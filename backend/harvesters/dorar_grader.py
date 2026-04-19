"""
Dorar.net Grader — Phase 3 du Vérificateur 32 Zones
Objectif : récupérer les verdicts (ahkam) pour les 72 446 hadiths sans grade
Méthode : Scraping éthique avec parsing HTML de l'API Dorar
"""
import asyncio
import aiohttp
import sqlite3
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import quote
from bs4 import BeautifulSoup
from datetime import datetime

DB = Path("backend/almizane.db")
CACHE_DIR = Path("backend/cache/dorar")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = Path("backend/harvesters/dorar_grading.log")

# API Dorar
DORAR_SEARCH = "https://dorar.net/dorar_api.json?skey={query}"
HEADERS = {
    "User-Agent": "Mizan-Research-Bot/1.0 (Salafi hadith verification; educational; contact: research@mizan.edu)",
    "Accept": "application/json, text/html",
}
RATE_LIMIT_SEC = 1.5  # Respect du serveur

# Mapping enrichi des verdicts arabes → codes normalisés
# Ordre important : patterns spécifiques avant génériques
HUKM_MAP = {
    # Authentique (sahih)
    "صحيح لذاته": "sahih_li_dhatihi",
    "صحيح لغيره": "sahih_li_ghayrihi",
    "حسن صحيح": "hasan_sahih",
    "إسناده صحيح": "sahih",
    "أصح": "sahih",  # "plus authentique"
    "صحيح": "sahih",
    "أخرجه البخاري": "sahih",
    "أخرجه مسلم": "sahih",
    "أورده البخاري": "sahih",
    "أورده مسلم": "sahih",
    "في الصحيحين": "sahih",
    "متفق عليه": "sahih",
    
    # Bon (hasan)
    "حسن لذاته": "hasan_li_dhatihi",
    "حسن لغيره": "hasan_li_ghayrihi",
    "إسناده حسن": "hasan",
    "حسن": "hasan",
    
    # Faible (daif)
    "ضعيف جداً": "daif_jiddan",
    "ضعيف جدا": "daif_jiddan",
    "إسناده ضعيف": "daif",
    "ضعيف": "daif",
    "أضعف": "daif",  # "plus faible"
    
    # Inventé/Rejeté
    "موضوع": "mawduʿ",
    "منكر": "munkar",
    "شاذ": "shadhdh",
    "لا أصل له": "la_asla_lah",
    "لا يصح": "la_yasihh",
    "لا يثبت": "la_yathbut",
    "باطل": "batil",
    "كذب": "kadhib",
    
    # Autres
    "متواتر": "mutawatir",
    "مشهور": "mashhur",
    "غريب": "gharib",
}

# Patterns regex pour détecter des nuances dans les commentaires
import re
HUKM_PATTERNS = [
    (re.compile(r"أصح|الصحيح"), "sahih"),
    (re.compile(r"لا يصح|لا يثبت|لا أصل"), "la_yasihh"),
    (re.compile(r"منكر"), "munkar"),
    (re.compile(r"ضعيف جد"), "daif_jiddan"),
    (re.compile(r"ضعيف|أضعف"), "daif"),
    (re.compile(r"موضوع|باطل|كذب"), "mawduʿ"),
    (re.compile(r"حسن"), "hasan"),
    (re.compile(r"صحيح"), "sahih"),
]

def log(msg):
    """Log avec timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}\n"
    print(line.strip())
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line)

def cache_key(query: str) -> Path:
    """Génère un nom de fichier cache basé sur le hash de la requête"""
    h = hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]
    return CACHE_DIR / f"{h}.html"

def parse_dorar_html(html: str):
    """
    Parse le HTML retourné par Dorar pour extraire les verdicts
    Retourne une liste de dicts avec les informations structurées
    """
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    
    # Trouver tous les blocs de hadith
    hadith_divs = soup.find_all('div', class_='hadith')
    info_divs = soup.find_all('div', class_='hadith-info')
    
    for hadith_div, info_div in zip(hadith_divs, info_divs):
        try:
            # Extraire les métadonnées - méthode plus robuste
            data = {}
            
            # Extraire le texte complet et le parser ligne par ligne
            info_text = info_div.get_text(separator='|', strip=True)
            lines = [l.strip() for l in info_text.split('|') if l.strip()]
            
            for i, line in enumerate(lines):
                # IMPORTANT: vérifier "خلاصة حكم المحدث:" AVANT "المحدث:" 
                # car "المحدث:" est contenu dans "خلاصة حكم المحدث:"
                if 'خلاصة حكم المحدث:' in line:
                    if i+1 < len(lines):
                        hukm_raw = lines[i+1]
                        data['hukm_raw'] = hukm_raw
                        
                        # Mapper vers code normalisé - essayer d'abord le mapping exact
                        hukm_class = "unknown"
                        for ar_key, code in HUKM_MAP.items():
                            if ar_key in hukm_raw:
                                hukm_class = code
                                break
                        
                        # Si toujours unknown, essayer les patterns regex
                        if hukm_class == "unknown":
                            for pattern, code in HUKM_PATTERNS:
                                if pattern.search(hukm_raw):
                                    hukm_class = code
                                    break
                        
                        data['hukm_class'] = hukm_class
                elif 'الراوي:' in line:
                    if i+1 < len(lines):
                        data['rawi'] = lines[i+1]
                elif 'المحدث:' in line:
                    if i+1 < len(lines):
                        data['muhaddith'] = lines[i+1]
                elif 'المصدر:' in line:
                    if i+1 < len(lines):
                        data['source_book'] = lines[i+1]
                elif 'الصفحة أو الرقم:' in line:
                    if i+1 < len(lines):
                        data['source_page'] = lines[i+1]
            
            if data.get('muhaddith') and data.get('hukm_raw'):
                results.append(data)
                
        except Exception as e:
            log(f"  ⚠️ Erreur parsing bloc: {e}")
            continue
    
    return results

async def fetch_dorar(session, matn_ar: str):
    """Récupère les verdicts depuis Dorar avec cache"""
    # Utiliser les 10-12 premiers mots significatifs
    words = matn_ar.split()
    query = " ".join(words[:12])
    
    cache = cache_key(query)
    if cache.exists():
        html = cache.read_text(encoding='utf-8')
        return parse_dorar_html(html)
    
    url = DORAR_SEARCH.format(query=quote(query))
    
    try:
        async with session.get(url, headers=HEADERS, timeout=20) as r:
            if r.status != 200:
                log(f"  ✗ Status {r.status}")
                return []
            
            data = await r.json(content_type=None)
            
            # Extraire le HTML du champ result
            if isinstance(data, dict) and 'ahadith' in data:
                html = data['ahadith'].get('result', '')
                if html:
                    cache.write_text(html, encoding='utf-8')
                    await asyncio.sleep(RATE_LIMIT_SEC)
                    return parse_dorar_html(html)
            
            return []
            
    except Exception as e:
        log(f"  ✗ Erreur fetch: {e}")
        return []

async def process_batch(batch_size=100, offset=0):
    """Traite un lot de hadiths sans grade"""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Hadiths sans verdicts dans ahkam
    cur.execute("""
      SELECT h.id, h.matn_ar, h.collection, h.numero_hadith
      FROM hadiths h
      LEFT JOIN ahkam a ON a.hadith_id = h.id
      WHERE a.id IS NULL 
        AND h.matn_ar IS NOT NULL 
        AND length(h.matn_ar) > 30
      LIMIT ? OFFSET ?
    """, (batch_size, offset))
    
    targets = cur.fetchall()
    
    if not targets:
        log(f"✅ Aucun hadith à traiter (offset {offset})")
        conn.close()
        return 0
    
    log(f"📦 Lot de {len(targets)} hadiths (offset {offset})")
    
    # Charger le mapping nom_ar → hukm_sources.id
    cur.execute("SELECT id, name_ar FROM hukm_sources")
    source_map = {row["name_ar"]: row["id"] for row in cur.fetchall()}
    
    processed = 0
    verdicts_added = 0
    
    async with aiohttp.ClientSession() as session:
        for row in targets:
            try:
                verdicts = await fetch_dorar(session, row["matn_ar"])
                
                if not verdicts:
                    log(f"  ⊘ #{row['id']} ({row['collection']} {row['numero_hadith']}) : aucun verdict")
                    processed += 1
                    continue
                
                # Insérer les verdicts
                for v in verdicts:
                    muhaddith = v.get('muhaddith', '').strip()
                    if not muhaddith:
                        continue
                    
                    # Trouver ou créer la source
                    src_id = source_map.get(muhaddith)
                    if not src_id:
                        cur.execute(
                            "INSERT OR IGNORE INTO hukm_sources (name_ar, era, manhaj) VALUES (?, 'unknown', 'unknown')",
                            (muhaddith,),
                        )
                        cur.execute("SELECT id FROM hukm_sources WHERE name_ar = ?", (muhaddith,))
                        result = cur.fetchone()
                        if result:
                            src_id = result[0]
                            source_map[muhaddith] = src_id
                    
                    if src_id:
                        cur.execute("""
                          INSERT OR IGNORE INTO ahkam 
                          (hadith_id, source_id, hukm_class, hukm_raw_ar, source_book, source_page, scraped_from)
                          VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            row["id"], 
                            src_id, 
                            v.get('hukm_class', 'unknown'),
                            v.get('hukm_raw', ''),
                            v.get('source_book', ''),
                            v.get('source_page', ''),
                            'dorar.net'
                        ))
                        verdicts_added += 1
                
                conn.commit()
                log(f"  ✓ #{row['id']} : {len(verdicts)} verdict(s)")
                processed += 1
                
            except Exception as e:
                log(f"  ✗ #{row['id']} : {e}")
                processed += 1
    
    conn.close()
    log(f"✅ Lot terminé : {processed} traités, {verdicts_added} verdicts ajoutés")
    return processed

async def main():
    """Point d'entrée principal"""
    log("="*60)
    log("🚀 DORAR GRADER — Phase 3")
    log("="*60)
    
    # Compter le total à traiter
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
      SELECT COUNT(*) FROM hadiths h
      LEFT JOIN ahkam a ON a.hadith_id = h.id
      WHERE a.id IS NULL AND h.matn_ar IS NOT NULL AND length(h.matn_ar) > 30
    """)
    total = cur.fetchone()[0]
    conn.close()
    
    log(f"📊 Total à traiter : {total:,} hadiths")
    
    # Traiter par lots
    batch_size = 100
    offset = 0
    total_processed = 0
    
    while offset < total:
        processed = await process_batch(batch_size, offset)
        if processed == 0:
            break
        total_processed += processed
        offset += batch_size
        
        # Pause entre lots
        log(f"⏸️  Pause 3 secondes... ({total_processed}/{total})")
        await asyncio.sleep(3)
    
    log("="*60)
    log(f"✅ TERMINÉ : {total_processed:,} hadiths traités")
    log("="*60)

if __name__ == "__main__":
    asyncio.run(main())