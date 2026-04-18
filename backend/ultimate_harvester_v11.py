#!/usr/bin/env python3
"""
ULTIMATE HARVESTER V11 - EXTRACTION MASSIVE SANS LIMITE
Objectif : 150,000+ hadiths TOUS GRADES confondus
"""

import sqlite3
import requests
import hashlib
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import re

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend/ultimate_harvest_v11.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltimateHarvester:
    """Harvester massif multi-sources sans filtrage"""
    
    def __init__(self):
        self.db_path = "backend/database/almizan_v7.db"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.stats = {
            'total_inserted': 0,
            'duplicates': 0,
            'errors': 0,
            'by_source': {},
            'by_grade': {}
        }
        
    def get_sha256(self, text: str) -> str:
        """Génère hash SHA256 pour détecter doublons"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def insert_hadith(self, data: Dict) -> bool:
        """Insert hadith avec gestion doublons via SHA256"""
        conn = None
        try:
            # Timeout plus long pour éviter locks
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()
            
            # Calcul hash
            matn_hash = self.get_sha256(data['matn_ar'])
            
            # Vérif doublon
            cursor.execute("SELECT id FROM entries WHERE matn_ar_hash = ?", (matn_hash,))
            if cursor.fetchone():
                self.stats['duplicates'] += 1
                return False
            
            # Insertion avec TOUTES les colonnes obligatoires
            cursor.execute("""
                INSERT INTO entries (
                    external_id, source_api, book_name_ar, hadith_number,
                    ar_text, fr_text, grade_primary, grade_albani,
                    matn_ar_hash, created_at, zone_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('external_id', f"harvest_{int(time.time())}"),
                data.get('source', 'unknown'),
                data.get('livre', 'Non défini'),
                data.get('numero_hadith', '0'),
                data['matn_ar'],
                data.get('matn_fr'),
                data.get('grade_primaire', 'Non classé'),
                data.get('grade_albani'),
                matn_hash,
                datetime.now().isoformat(),
                1  # zone_id par défaut
            ))
            
            conn.commit()
            
            self.stats['total_inserted'] += 1
            source = data.get('source', 'unknown')
            grade = data.get('grade_primaire', 'Non classé')
            self.stats['by_source'][source] = self.stats['by_source'].get(source, 0) + 1
            self.stats['by_grade'][grade] = self.stats['by_grade'].get(grade, 0) + 1
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur insertion: {e}")
            self.stats['errors'] += 1
            return False
        finally:
            if conn:
                conn.close()
    
    def normalize_grade(self, grade_raw: str) -> Tuple[str, int, Optional[str]]:
        """Normalise grade et détermine badge_alerte"""
        if not grade_raw:
            return "Non classé", 0, None
        
        grade_lower = grade_raw.lower()
        
        # Grades authentiques
        if any(x in grade_lower for x in ['صحيح', 'sahih', 'authentic']):
            return "Sahih", 0, None
        if any(x in grade_lower for x in ['حسن', 'hasan', 'good']):
            return "Hasan", 0, None
        
        # Grades faibles (ACCEPTÉS)
        if any(x in grade_lower for x in ['ضعيف', 'da\'if', 'daif', 'weak']):
            if 'جدا' in grade_lower or 'jiddan' in grade_lower:
                return "Da'if Jiddan", 0, "Très faible"
            return "Da'if", 0, "Faible"
        
        # Grades problématiques (badge alerte)
        if any(x in grade_lower for x in ['منكر', 'munkar', 'rejected']):
            return "Munkar", 1, "Rejeté par consensus"
        if any(x in grade_lower for x in ['شاذ', 'shaadh', 'irregular']):
            return "Shaadh", 1, "Irrégulier"
        if any(x in grade_lower for x in ['متروك', 'matruk', 'abandoned']):
            return "Matruk", 1, "Abandonné"
        if any(x in grade_lower for x in ['موضوع', 'mawdu', 'fabricated', 'forged']):
            return "Mawdu'", 1, "FABRICATION - Ne pas utiliser"
        if any(x in grade_lower for x in ['باطل', 'batil', 'false']):
            return "Batil", 1, "FAUX - Rejeté"
        
        return grade_raw, 0, None
    
    # ========== SOURCES TIER 1 : APIs OFFICIELLES ==========
    
    def harvest_sunnah_com(self):
        """Sunnah.com API - TOUTES collections"""
        logger.info("🔄 Sunnah.com - Extraction complète...")
        
        collections = [
            'bukhari', 'muslim', 'nasai', 'abudawud', 'tirmidhi', 'ibnmajah',
            'malik', 'ahmad', 'darimi', 'adab', 'bulugh', 'qudsi40', 'nawawi40',
            'riyadussalihin', 'shamail', 'mishkat'
        ]
        
        for collection in collections:
            try:
                logger.info(f"  📖 {collection}...")
                url = f"https://api.sunnah.com/v1/collections/{collection}/hadiths"
                
                page = 1
                while True:
                    resp = self.session.get(f"{url}?page={page}", timeout=30)
                    if resp.status_code != 200:
                        break
                    
                    data = resp.json()
                    hadiths = data.get('data', [])
                    if not hadiths:
                        break
                    
                    for h in hadiths:
                        grade_raw = h.get('grade', {}).get('name', '')
                        grade, badge, raison = self.normalize_grade(grade_raw)
                        
                        self.insert_hadith({
                            'external_id': f"sunnah_{collection}_{h.get('hadithNumber', '')}",
                            'source': f'sunnah.com/{collection}',
                            'livre': collection.title(),
                            'numero_hadith': h.get('hadithNumber', 0),
                            'matn_ar': h.get('hadithArabic', ''),
                            'matn_fr': None,
                            'grade_primaire': grade,
                            'grade_albani': grade_raw,
                            'badge_alerte': badge,
                            'raison_alerte': raison
                        })
                    
                    if self.stats['total_inserted'] % 500 == 0:
                        logger.info(f"  ✅ {self.stats['total_inserted']} hadiths insérés")
                    
                    page += 1
                    time.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Erreur {collection}: {e}")
    
    def harvest_hadeethenc(self):
        """HadeethEnc - Traductions françaises"""
        logger.info("🔄 HadeethEnc - Extraction avec traductions FR...")
        
        try:
            url = "https://hadeethenc.com/api/v1/hadeeths/list/"
            params = {'language': 'ar', 'per_page': 100, 'page': 1}
            
            while True:
                resp = self.session.get(url, params=params, timeout=30)
                if resp.status_code != 200:
                    break
                
                data = resp.json()
                hadiths = data.get('data', [])
                if not hadiths:
                    break
                
                for h in hadiths:
                    # Récupération traduction FR
                    matn_fr = None
                    try:
                        fr_resp = self.session.get(
                            f"https://hadeethenc.com/api/v1/hadeeths/one/",
                            params={'id': h.get('id'), 'language': 'fr'},
                            timeout=10
                        )
                        if fr_resp.status_code == 200:
                            fr_data = fr_resp.json()
                            matn_fr = fr_data.get('data', {}).get('hadeeth', '')
                    except:
                        pass
                    
                    grade_raw = h.get('grade', '')
                    grade, badge, raison = self.normalize_grade(grade_raw)
                    
                    self.insert_hadith({
                        'external_id': f"hadeethenc_{h.get('id', '')}",
                        'source': 'hadeethenc.com',
                        'livre': h.get('book', 'Non défini'),
                        'numero_hadith': h.get('number', 0),
                        'matn_ar': h.get('hadeeth', ''),
                        'matn_fr': matn_fr,
                        'grade_primaire': grade,
                        'grade_albani': grade_raw,
                        'badge_alerte': badge,
                        'raison_alerte': raison
                    })
                
                if self.stats['total_inserted'] % 500 == 0:
                    logger.info(f"  ✅ {self.stats['total_inserted']} hadiths insérés")
                
                params['page'] += 1
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Erreur HadeethEnc: {e}")
    
    def harvest_dorar(self):
        """Dorar.net - Extraction HTML"""
        logger.info("🔄 Dorar.net - Extraction HTML...")
        
        try:
            # Extraction via recherche générique
            base_url = "https://dorar.net/hadith/search"
            
            for page in range(1, 1000):  # Max 1000 pages
                try:
                    resp = self.session.get(
                        base_url,
                        params={'page': page, 'q': ''},
                        timeout=30
                    )
                    
                    if resp.status_code != 200:
                        break
                    
                    # Parse HTML (simplifié)
                    html = resp.text
                    
                    # Extraction basique via regex
                    hadiths = re.findall(
                        r'<div class="hadith-text">(.*?)</div>.*?<div class="grade">(.*?)</div>',
                        html,
                        re.DOTALL
                    )
                    
                    if not hadiths:
                        break
                    
                    for matn, grade_raw in hadiths:
                        matn_clean = re.sub(r'<[^>]+>', '', matn).strip()
                        grade_clean = re.sub(r'<[^>]+>', '', grade_raw).strip()
                        
                        if not matn_clean:
                            continue
                        
                        grade, badge, raison = self.normalize_grade(grade_clean)
                        
                        self.insert_hadith({
                            'external_id': f"dorar_{self.get_sha256(matn_clean)[:16]}",
                            'source': 'dorar.net',
                            'livre': 'Non défini',
                            'numero_hadith': 0,
                            'matn_ar': matn_clean,
                            'matn_fr': None,
                            'grade_primaire': grade,
                            'grade_albani': grade_clean,
                            'badge_alerte': badge,
                            'raison_alerte': raison
                        })
                    
                    if self.stats['total_inserted'] % 500 == 0:
                        logger.info(f"  ✅ {self.stats['total_inserted']} hadiths insérés")
                    
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Erreur page {page}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Erreur Dorar: {e}")
    
    def harvest_jsdelivr(self):
        """jsDelivr CDN - hadith-api"""
        logger.info("🔄 jsDelivr - hadith-api...")
        
        collections = [
            'bukhari', 'muslim', 'nasai', 'abudawud', 'tirmidhi', 'ibnmajah',
            'malik', 'ahmad', 'darimi'
        ]
        
        for collection in collections:
            try:
                logger.info(f"  📖 {collection}...")
                base_url = f"https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/ara-{collection}.json"
                
                resp = self.session.get(base_url, timeout=30)
                if resp.status_code != 200:
                    continue
                
                data = resp.json()
                hadiths = data.get('hadiths', [])
                
                for h in hadiths:
                    grade_raw = h.get('grade', '')
                    grade, badge, raison = self.normalize_grade(grade_raw)
                    
                    self.insert_hadith({
                        'external_id': f"jsdelivr_{collection}_{h.get('hadithnumber', '')}",
                        'source': f'jsdelivr/{collection}',
                        'livre': collection.title(),
                        'numero_hadith': h.get('hadithnumber', 0),
                        'matn_ar': h.get('text', ''),
                        'matn_fr': None,
                        'grade_primaire': grade,
                        'grade_albani': grade_raw,
                        'badge_alerte': badge,
                        'raison_alerte': raison
                    })
                
                if self.stats['total_inserted'] % 500 == 0:
                    logger.info(f"  ✅ {self.stats['total_inserted']} hadiths insérés")
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Erreur {collection}: {e}")
    
    # ========== SOURCES TIER 2 : BIBLIOTHÈQUES NUMÉRIQUES ==========
    
    def harvest_shamela(self):
        """Shamela.ws - Tentative extraction"""
        logger.info("🔄 Shamela.ws - Tentative...")
        
        # Note: Shamela nécessite scraping complexe ou API non documentée
        # Implémentation basique pour test
        try:
            # URLs connues de collections hadith
            book_ids = [
                '1', '2', '3', '4', '5', '6',  # Kutub Sittah
                '7', '8', '9', '10'  # Autres collections
            ]
            
            for book_id in book_ids:
                try:
                    url = f"https://shamela.ws/book/{book_id}"
                    resp = self.session.get(url, timeout=30)
                    
                    if resp.status_code == 200:
                        # Parse basique (à améliorer)
                        html = resp.text
                        # Extraction simplifiée
                        logger.info(f"  📖 Book {book_id} - Parsing...")
                    
                    time.sleep(3)
                    
                except Exception as e:
                    logger.error(f"Erreur book {book_id}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Erreur Shamela: {e}")
    
    def harvest_albani_silsila(self):
        """Al-Albani Silsila Sahiha + Da'ifa"""
        logger.info("🔄 Al-Albani Silsila...")
        
        # Sources potentielles
        sources = [
            'https://albani.ws/silsila-sahiha',
            'https://albani.ws/silsila-daifa'
        ]
        
        for source_url in sources:
            try:
                resp = self.session.get(source_url, timeout=30)
                if resp.status_code == 200:
                    logger.info(f"  ✅ {source_url} accessible")
                    # Parse HTML (à implémenter)
                
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Erreur {source_url}: {e}")
    
    # ========== RAPPORT ==========
    
    def generate_report(self):
        """Génère rapport final"""
        report = f"""
# RAPPORT ULTIMATE HARVESTER V11
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## STATISTIQUES GLOBALES
- **Total hadiths insérés**: {self.stats['total_inserted']:,}
- **Doublons évités**: {self.stats['duplicates']:,}
- **Erreurs**: {self.stats['errors']:,}

## RÉPARTITION PAR SOURCE
"""
        for source, count in sorted(self.stats['by_source'].items(), key=lambda x: x[1], reverse=True):
            report += f"- {source}: {count:,}\n"
        
        report += "\n## RÉPARTITION PAR GRADE\n"
        for grade, count in sorted(self.stats['by_grade'].items(), key=lambda x: x[1], reverse=True):
            report += f"- {grade}: {count:,}\n"
        
        # Sauvegarde
        Path('output').mkdir(exist_ok=True)
        with open('output/ULTIMATE_HARVEST_V11_REPORT.md', 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(report)
    
    # ========== ORCHESTRATION ==========
    
    def run(self):
        """Lance harvesting complet"""
        logger.info("=" * 80)
        logger.info("🚀 ULTIMATE HARVESTER V11 - DÉMARRAGE")
        logger.info("Objectif: 150,000+ hadiths TOUS GRADES")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # TIER 1: APIs officielles
        self.harvest_sunnah_com()
        self.harvest_hadeethenc()
        self.harvest_jsdelivr()
        
        # TIER 2: Scraping
        self.harvest_dorar()
        
        # TIER 3: Bibliothèques (expérimental)
        self.harvest_shamela()
        self.harvest_albani_silsila()
        
        # Rapport final
        elapsed = time.time() - start_time
        logger.info("=" * 80)
        logger.info(f"✅ HARVESTING TERMINÉ en {elapsed/3600:.2f}h")
        logger.info(f"📊 Total: {self.stats['total_inserted']:,} hadiths")
        logger.info("=" * 80)
        
        self.generate_report()

if __name__ == "__main__":
    harvester = UltimateHarvester()
    harvester.run()