#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCANNER COMPLET — MISSION FINALE
Google Search → Crawl → DB Match → Sources Externes → Export
"""

import json
import os
import re
import sqlite3
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

DB_PATH = r'C:\Users\sabri\Desktop\al-mizan-v3-main\backend\database\almizan_v7.db'
EXPORT_DIR = Path(r'C:\Users\sabri\Desktop\al-mizan-v3-main\export_medine')

QUERIES_GOOGLE = [
    'hadith "le prophète a dit" islam france',
    'hadith mawdou faible inventé islam français',
    '"قال رسول الله" français islam',
    'rappel hadith prophète islam france',
    'hadiths inventés propagés france islam',
    'hadith faible sunna islam francophone',
]

# Patterns d'extraction de hadiths
PATTERNS_HADITH = [
    r'le\s+Proph[èe]te[\s\w]*a\s+dit[\s:]+[«"\']?([^«"\']{30,500})[»"\']?',
    r'le\s+Messager[\s\w]*a\s+dit[\s:]+[«"\']?([^«"\']{30,500})[»"\']?',
    r'il\s+a\s+dit[\sﷺ:]+[«"\']?([^«"\']{30,500})[»"\']?',
    r'rapport[ée]\s+que[\s\w]*Proph[èe]te[\s:]+[«"\']?([^«"\']{30,500})[»"\']?',
    r'[«"\']([^«"\']{40,500}Proph[èe]te[^«"\']{0,200})[»"\']',
    r'[«"\']([^«"\']{40,500}Allah[^«"\']{0,200}disait[^«"\']{0,100})[»"\']',
]

KEYWORDS_LIENS = ['hadith', 'article', 'cours', 'fatwa', 'sunna', 'prophète', 'rappel', 'science', 'foi']
FUZZY_SEUIL = 50
MAX_PAGES_PAR_DOMAINE = 15

# ═══════════════════════════════════════════════════════════════════════════════
# CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

class ScannerComplet:
    def __init__(self):
        self.hadiths_db = []
        self.alertes_db = []  # Matchs avec almizan_v7.db
        self.alertes_externes = []  # Matchs avec sources externes
        self.non_references = []  # Non trouvés nulle part
        self.bloques = []  # Sites bloqués
        self.visited_urls = set()
        self.domain_pages_count = {}  # Compteur pages par domaine
        
        EXPORT_DIR.mkdir(exist_ok=True)
        
        # Headers pour requêtes
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def log(self, msg: str):
        """Log temps réel"""
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] {msg}")
        sys.stdout.flush()
    
    def load_db(self):
        """Étape 0: Charge hadiths depuis almizan_v7.db"""
        self.log("📚 ÉTAPE 0: Chargement DB almizan_v7.db")
        
        if not os.path.exists(DB_PATH):
            raise Exception(f"[ERREUR CRITIQUE] DB introuvable: {DB_PATH}")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, fr_text, grade_primary, grade_albani, grade_ibn_baz, 
                   grade_ibn_uthaymin, grade_muqbil, book_name_fr
            FROM entries 
            WHERE grade_primary IN ("Mawdu'", "Da'if", "Shadh", "Munkar", "Matruk", "Hasan Da'if")
            AND fr_text IS NOT NULL
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            hid, fr_text, grade, alb, baz, uth, muq, book = row
            savant = "al-Albānī"
            if baz: savant = "Ibn Bāz"
            elif uth: savant = "Ibn Uthaymīn"
            elif muq: savant = "Muqbil"
            
            self.hadiths_db.append({
                "id": hid,
                "texte": fr_text,
                "grade": grade,
                "savant": savant,
                "reference": book or "DB",
            })
        
        self.log(f"✅ DB chargée: {len(self.hadiths_db)} hadiths faibles/inventés")
    
    def google_search_playwright(self, query: str) -> List[str]:
        """Étape 1: Recherche Google via Playwright MCP — À implémenter avec MCP"""
        # Pour l'instant on simule — le vrai appel MCP sera fait manuellement
        self.log(f"🔍 Google search (MCP): '{query[:50]}...'")
        return []  # Retournera les vraies URLs quand MCP sera appelé
    
    def fetch_url(self, url: str) -> Optional[Dict]:
        """Récupère contenu d'une URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            return {
                "url": url,
                "html": response.text,
                "status": response.status_code
            }
        except Exception as e:
            self.log(f"   [BLOQUÉ] {url[:60]}... | {str(e)[:50]}")
            self.bloques.append({
                "url": url,
                "raison": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return None
    
    def extract_hadiths_from_page(self, page: Dict) -> List[Dict]:
        """Extrait les passages hadith du contenu"""
        html = page.get("html", "")
        url = page.get("url", "")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extraire tout le texte visible
        texts = []
        for tag in soup.find_all(['p', 'div', 'article', 'section', 'span']):
            text = tag.get_text(strip=True)
            if len(text) > 50:
                texts.append(text)
        
        full_text = ' '.join(texts)
        
        # Chercher patterns hadith
        extraits = []
        for pattern in PATTERNS_HADITH:
            for match in re.finditer(pattern, full_text, re.IGNORECASE):
                extrait = match.group(1) if match.groups() else match.group(0)
                extrait = extrait.strip()[:600]
                if len(extrait) > 40:
                    extraits.append({
                        "texte": extrait,
                        "url": url,
                        "pattern": pattern[:30],
                        "timestamp": datetime.now().isoformat()
                    })
        
        return extraits
    
    def extract_links(self, page: Dict) -> List[str]:
        """Extrait les liens internes pertinents"""
        html = page.get("html", "")
        base_url = page.get("url", "")
        domain = urlparse(base_url).netloc
        
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True).lower()
            
            # Lien complet
            full_url = urljoin(base_url, href)
            link_domain = urlparse(full_url).netloc
            
            # Filtrer: même domaine + keywords
            if link_domain == domain or link_domain.endswith('.' + domain):
                if any(kw in (text + href).lower() for kw in KEYWORDS_LIENS):
                    if full_url not in self.visited_urls:
                        links.append(full_url)
        
        return list(set(links))[:10]  # Max 10 liens par page
    
    def match_with_db(self, extrait: str) -> Optional[Dict]:
        """Matching niveau 1: DB locale avec seuil 50%"""
        best_match = None
        best_score = 0
        
        for hadith in self.hadiths_db:
            score = fuzz.partial_ratio(extrait.lower(), hadith["texte"].lower())
            if score >= FUZZY_SEUIL and score > best_score:
                best_score = score
                best_match = hadith.copy()
                best_match["score_fuzzy"] = score
        
        return best_match
    
    def check_external_sources(self, extrait: str) -> Optional[Dict]:
        """Matching niveau 2: Vérification sources externes"""
        # Note: Simplifié pour l'instant — les vrais appels API nécessitent clés/config
        return None
    
    def crawl_domain(self, start_url: str):
        """Crawl un domaine (max 15 pages)"""
        domain = urlparse(start_url).netloc
        
        if domain in self.domain_pages_count and self.domain_pages_count[domain] >= MAX_PAGES_PAR_DOMAINE:
            return
        
        urls_to_visit = [start_url]
        
        while urls_to_visit and self.domain_pages_count.get(domain, 0) < MAX_PAGES_PAR_DOMAINE:
            url = urls_to_visit.pop(0)
            
            if url in self.visited_urls:
                continue
            
            self.visited_urls.add(url)
            self.domain_pages_count[domain] = self.domain_pages_count.get(domain, 0) + 1
            
            self.log(f"🕷️ [{self.domain_pages_count[domain]}/{MAX_PAGES_PAR_DOMAINE}] {domain} | {url[:70]}...")
            
            # Fetch page
            page = self.fetch_url(url)
            if not page:
                continue
            
            # Extraire hadiths
            hadiths = self.extract_hadiths_from_page(page)
            self.log(f"   📄 {len(hadiths)} passages hadith extraits")
            
            # Matcher chaque passage
            for h in hadiths:
                match_db = self.match_with_db(h["texte"])
                
                if match_db:
                    # Match DB trouvé
                    alerte = {
                        "type": "ALERTE_CRITIQUE_DB" if "mawdu" in match_db["grade"].lower() else "ALERTE_MODEREE_DB",
                        "url": h["url"],
                        "extrait": h["texte"][:200],
                        "hadith_id": match_db["id"],
                        "grade": match_db["grade"],
                        "savant": match_db["savant"],
                        "score_fuzzy": match_db["score_fuzzy"],
                        "timestamp": datetime.now().isoformat()
                    }
                    self.alertes_db.append(alerte)
                    self.log(f"   🔴 {alerte['type']} | {match_db['grade']} | Score: {match_db['score_fuzzy']}%")
                else:
                    # Pas de match DB — vérifier sources externes
                    match_ext = self.check_external_sources(h["texte"])
                    if match_ext:
                        self.alertes_externes.append({
                            "type": "ALERTE_EXTERNE",
                            "url": h["url"],
                            "extrait": h["texte"][:200],
                            "source": match_ext.get("source"),
                            "grade": match_ext.get("grade"),
                            "timestamp": datetime.now().isoformat()
                        })
                        self.log(f"   🟡 ALERTE_EXTERNE | {match_ext.get('grade')}")
                    else:
                        # Non référencé
                        self.non_references.append({
                            "type": "NON_REFERENCé",
                            "url": h["url"],
                            "extrait": h["texte"],
                            "timestamp": datetime.now().isoformat()
                        })
            
            # Extraire liens pour suite
            new_links = self.extract_links(page)
            for link in new_links:
                if link not in self.visited_urls and link not in urls_to_visit:
                    urls_to_visit.append(link)
    
    def export_results(self):
        """Exporte tous les résultats"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # ALERTES_DB.json
        if self.alertes_db:
            path = EXPORT_DIR / f"ALERTES_DB_{ts}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.alertes_db, f, ensure_ascii=False, indent=2)
            self.log(f"💾 ALERTES_DB: {path} ({len(self.alertes_db)} alertes)")
        
        # ALERTES_EXTERNES.json
        if self.alertes_externes:
            path = EXPORT_DIR / f"ALERTES_EXTERNES_{ts}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.alertes_externes, f, ensure_ascii=False, indent=2)
            self.log(f"💾 ALERTES_EXTERNES: {path} ({len(self.alertes_externes)} alertes)")
        
        # NON_REFERENCES.json
        if self.non_references:
            path = EXPORT_DIR / f"NON_REFERENCES_{ts}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.non_references, f, ensure_ascii=False, indent=2)
            self.log(f"💾 NON_REFERENCES: {path} ({len(self.non_references)} passages)")
        
        # BLOQUES.json
        if self.bloques:
            path = EXPORT_DIR / f"BLOQUES_{ts}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.bloques, f, ensure_ascii=False, indent=2)
            self.log(f"💾 BLOQUES: {path} ({len(self.bloques)} sites)")
        
        # RAPPORT_FINAL.md
        self.generate_rapport_md(ts)
    
    def generate_rapport_md(self, ts: str):
        """Génère le rapport Markdown final"""
        path = EXPORT_DIR / f"RAPPORT_FINAL_{ts}.md"
        
        with open(path, "w", encoding="utf-8") as f:
            f.write("# 📊 RAPPORT FINAL — SCAN HADITHS FRANCOPHONES\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Stats globales
            f.write("## 🎯 Statistiques Globales\n\n")
            f.write(f"- **URLs visitées:** {len(self.visited_urls)}\n")
            f.write(f"- **🔴 Alertes DB (faibles/inventés):** {len(self.alertes_db)}\n")
            f.write(f"- **🟡 Alertes Externes:** {len(self.alertes_externes)}\n")
            f.write(f"- **⚪ Non référencés:** {len(self.non_references)}\n")
            f.write(f"- **⚫ Sites bloqués:** {len(self.bloques)}\n\n")
            
            # Top alertes par fréquence
            if self.alertes_db:
                f.write("## 🔴 Top Alertes par Hadith (DB)\n\n")
                from collections import Counter
                hadith_counts = Counter([a["hadith_id"] for a in self.alertes_db])
                for hid, count in hadith_counts.most_common(10):
                    alert = next(a for a in self.alertes_db if a["hadith_id"] == hid)
                    f.write(f"### {hid}\n")
                    f.write(f"- **Grade:** {alert['grade']}\n")
                    f.write(f"- **Savant:** {alert['savant']}\n")
                    f.write(f"- **Occurrences:** {count}\n")
                    f.write(f"- **Exemple URL:** {alert['url']}\n")
                    f.write(f"- **Extrait:** {alert['extrait'][:150]}...\n\n")
            
            # Liste complète alertes
            if self.alertes_db:
                f.write("## 📋 Liste Complète Alertes DB\n\n")
                for i, a in enumerate(self.alertes_db, 1):
                    f.write(f"{i}. **[{a['type']}]** `{a['grade']}` | {a['url']}\n")
                    f.write(f"   - Hadith ID: `{a['hadith_id']}`\n")
                    f.write(f"   - Score: {a['score_fuzzy']}% | Savant: {a['savant']}\n\n")
        
        self.log(f"💾 RAPPORT_FINAL: {path}")
    
    def run(self):
        """Exécution complète"""
        self.log("=" * 80)
        self.log("🚀 SCAN COMPLET — MISSION FINALE")
        self.log("=" * 80)
        
        # Étape 0: Charger DB
        self.load_db()
        
        # Étape 1-2: Google Search + Crawl (à faire avec MCP manuellement)
        self.log("\n📡 ÉTAPE 1-2: Google Search + Crawl")
        self.log("[INFO] Les recherches Google nécessitent Playwright MCP")
        self.log("[INFO] Exécution manuelle requise pour éviter les blocages")
        
        # Pour test: on peut crawler des URLs connues directement
        test_urls = [
            "https://islamhouse.com/fr",
            "https://islamweb.net",
        ]
        
        for url in test_urls:
            self.crawl_domain(url)
        
        # Export final
        self.log("\n" + "=" * 80)
        self.log("📤 EXPORT DES RÉSULTATS")
        self.export_results()
        
        # Résumé
        self.log("\n" + "=" * 80)
        self.log("✅ SCAN TERMINÉ")
        self.log(f"   🔴 Alertes DB: {len(self.alertes_db)}")
        self.log(f"   🟡 Alertes Externes: {len(self.alertes_externes)}")
        self.log(f"   ⚪ Non référencés: {len(self.non_references)}")
        self.log(f"   ⚫ Bloqués: {len(self.bloques)}")
        self.log("=" * 80)


if __name__ == "__main__":
    scanner = ScannerComplet()
    scanner.run()
