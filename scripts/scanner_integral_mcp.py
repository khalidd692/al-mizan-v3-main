#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCANNER INTÉGRAL MCP — Mission Finale
Crawl direct des sites islamiques francophones avec Playwright MCP
"""

import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

from rapidfuzz import fuzz

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

DB_PATH = r'C:\Users\sabri\Desktop\al-mizan-v3-main\backend\database\almizan_v7.db'
EXPORT_DIR = Path(r'C:\Users\sabri\Desktop\al-mizan-v3-main\export_medine')

SITES = [
    # Salafi / Sunnah - COMMENCER PAR ICI
    "https://salafs.com",
    "https://assunnah.be",
    "https://minhaj-as-sunnah.com",
    "https://sunnahway.net",
    "https://sounnah.com",
    "https://lewajib.com",
    "https://daroussalam.fr",
    "https://islamiqa.fr",
    "https://al-bayyinah.fr",
    "https://aqidah.fr",
    "https://salaf.fr",
    "https://sunna.fr",
]

# Patterns d'extraction
PATTERNS_HADITH = [
    r'le Prophète[\s\w]*a\s+dit[\s:]+[«"\']?([^«"\']{30,500})[»"\']?',
    r'le Messager[\s\w]*a\s+dit[\s:]+[«"\']?([^«"\']{30,500})[»"\']?',
    r'il[\s\w]*a\s+dit[\sﷺ:]+[«"\']?([^«"\']{30,500})[»"\']?',
    r'[«"\']([^«"\']{40,800}Prophète[^«"\']{0,200})[»"\']',
    r'[«"\']([^«"\']{40,800}Allah[^«"\']{0,200})[»"\']',
]

KEYWORDS_LIENS = ['hadith', 'article', 'cours', 'fatwa', 'publication', 'chapitre', 'livre', 'audio', 'video']

FUZZY_SEUIL = 50

# ═══════════════════════════════════════════════════════════════════════════════
# CHARGEMENT DB
# ═══════════════════════════════════════════════════════════════════════════════

def load_hadiths_from_db() -> List[Dict]:
    """Charge tous les hadiths Mawdou'/Da'if depuis la DB"""
    if not os.path.exists(DB_PATH):
        raise Exception(f"[ERREUR CRITIQUE] DB introuvable: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, fr_text, grade_primary, grade_albani, grade_ibn_baz, 
               grade_ibn_uthaymin, grade_muqbil, book_name_fr
        FROM entries 
        WHERE grade_primary IN ("Mawdu'", "Da'if", "Shadh", "Munkar") 
        AND fr_text IS NOT NULL
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    hadiths = []
    for row in rows:
        hid, fr_text, grade, alb, baz, uth, muq, book = row
        
        # Déterminer le savant
        savant = "al-Albānī"
        if baz: savant = "Ibn Bāz"
        elif uth: savant = "Ibn Uthaymīn"
        elif muq: savant = "Muqbil"
        
        hadiths.append({
            "id": hid,
            "texte": fr_text,
            "grade": grade,
            "savant": savant,
            "reference": book or "DB",
        })
    
    print(f"[DB LOAD] {len(hadiths)} hadiths chargés (Mawdou'/Da'if/Shadh/Munkar)")
    return hadiths

# ═══════════════════════════════════════════════════════════════════════════════
# PLAYWRIGHT MCP SCANNER
# ═══════════════════════════════════════════════════════════════════════════════

class ScannerIntegralMCP:
    """Scanner utilisant Playwright MCP"""
    
    def __init__(self, hadiths_db: List[Dict]):
        self.hadiths_db = hadiths_db
        self.alerts = []  # Matchs DB réels
        self.non_refs = []  # Hadiths trouvés mais pas en DB
        self.bloques = []  # Sites bloqués
        self.visited = set()  # URLs déjà visitées
        
        EXPORT_DIR.mkdir(exist_ok=True)
    
    def fuzzy_score(self, text1: str, text2: str) -> float:
        """Calcule similarité fuzzy"""
        if not text1 or not text2:
            return 0.0
        return fuzz.partial_ratio(text1.lower(), text2.lower())
    
    def match_with_db(self, extrait: str) -> Optional[Dict]:
        """Cherche match dans la DB avec seuil 50%"""
        best_match = None
        best_score = 0
        
        for hadith in self.hadiths_db:
            score = self.fuzzy_score(extrait, hadith["texte"])
            if score >= FUZZY_SEUIL and score > best_score:
                best_score = score
                best_match = hadith
                best_match["score"] = score
        
        return best_match
    
    def extract_hadiths_from_text(self, text: str, url: str) -> List[Dict]:
        """Extrait les hadiths du texte avec patterns"""
        extraits = []
        
        for pattern in PATTERNS_HADITH:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                extrait = match.group(1) if match.groups() else match.group(0)
                extrait = extrait.strip()[:500]  # Tronquer
                if len(extrait) > 30:
                    extraits.append({
                        "texte": extrait,
                        "url": url,
                        "pattern": pattern[:30]
                    })
        
        return extraits
    
    def scan_site_playwright(self, domain: str) -> Dict:
        """Scan un site avec Playwright MCP"""
        resultats = {
            "domain": domain,
            "urls_scanned": 0,
            "alertes": 0,
            "non_refs": 0,
            "bloque": False,
            "raison_blocage": None
        }
        
        url = domain if domain.startswith('http') else f"https://{domain}"
        
        print(f"\n🌐 SCAN: {domain}")
        print(f"   URL: {url}")
        
        try:
            # Note: Ici on utiliserait Playwright MCP
            # Pour l'instant on simule l'appel MCP
            print(f"   [INFO] Playwright MCP navigate to {url}")
            
            # Simulation du retour MCP (à remplacer par vrai appel)
            # page_content = mcp_playwright_navigate(url)
            
            resultats["bloque"] = True
            resultats["raison_blocage"] = "Playwright MCP non connecté - attente confirmation utilisateur"
            self.bloques.append({
                "domain": domain,
                "url": url,
                "raison": "Playwright MCP non connecté",
                "timestamp": datetime.now().isoformat()
            })
            print(f"   [BLOQUÉ] {resultats['raison_blocage']}")
            
        except Exception as e:
            resultats["bloque"] = True
            resultats["raison_blocage"] = str(e)
            self.bloques.append({
                "domain": domain,
                "url": url,
                "raison": str(e),
                "timestamp": datetime.now().isoformat()
            })
            print(f"   [BLOQUÉ] {e}")
        
        return resultats
    
    def run_scan_single(self, domain: str = "salafs.com"):
        """Scan un seul site (pour test)"""
        print("\n" + "=" * 80)
        print(f"🎯 SCAN TEST — {domain}")
        print("=" * 80)
        
        result = self.scan_site_playwright(domain)
        
        print(f"\n📊 RÉSULTAT {domain}:")
        print(f"   URLs scannées: {result['urls_scanned']}")
        print(f"   Alertes DB: {result['alertes']}")
        print(f"   Non référencés: {result['non_refs']}")
        print(f"   Bloqué: {result['bloque']}")
        if result['bloque']:
            print(f"   Raison: {result['raison_blocage']}")
        
        self.export_results()
        
        print("\n" + "=" * 80)
        print("⏸️  ATTENTE CONFIRMATION UTILISATEUR")
        print("   Tape 'continue' pour scanner les sites suivants")
        print("=" * 80)
    
    def run_scan_full(self):
        """Scan complet de tous les sites"""
        print("\n" + "=" * 80)
        print("🚀 SCAN INTÉGRAL — TOUS LES SITES")
        print("=" * 80)
        
        for i, domain in enumerate(SITES, 1):
            print(f"\n📍 [{i}/{len(SITES)}] {domain}")
            result = self.scan_site_playwright(domain)
            
            print(f"   Sous-total — Alertes: {result['alertes']} | Non-réf: {result['non_refs']} | Bloqué: {result['bloque']}")
            
            # Export intermédiaire
            if i % 3 == 0:
                self.export_results()
        
        # Export final
        self.export_results(final=True)
        self.print_rapport_final()
    
    def export_results(self, final: bool = False):
        """Exporte les résultats en JSON"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = "_FINAL" if final else ""
        
        # Alertes
        if self.alerts:
            path = EXPORT_DIR / f"SCAN_ALERTES{suffix}_{ts}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.alerts, f, ensure_ascii=False, indent=2)
            if final:
                print(f"\n💾 Export Alertes: {path} ({len(self.alerts)} détections)")
        
        # Non référencés
        if self.non_refs:
            path = EXPORT_DIR / f"SCAN_NON_REFERENCES{suffix}_{ts}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.non_refs, f, ensure_ascii=False, indent=2)
            if final:
                print(f"💾 Export Non-réf: {path} ({len(self.non_refs)} détections)")
        
        # Bloqués
        if self.bloques:
            path = EXPORT_DIR / f"SCAN_BLOQUES{suffix}_{ts}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.bloques, f, ensure_ascii=False, indent=2)
            if final:
                print(f"💾 Export Bloqués: {path} ({len(self.bloques)} sites)")
    
    def print_rapport_final(self):
        """Rapport terminal final"""
        print("\n" + "=" * 80)
        print("║" + " " * 25 + "📊 SCAN TERMINÉ 📊" + " " * 25 + "║")
        print("=" * 80)
        
        print(f"\n🎯 RÉSULTATS GLOBAUX")
        print(f"   🔴 Alertes DB: {len(self.alerts)} hadiths Mawdou'/Da'if trouvés")
        print(f"   🟠 Non référencés: {len(self.non_refs)} hadiths absents de la DB")
        print(f"   ⚫ Bloqués: {len(self.bloques)} sites")
        
        if self.alerts:
            print(f"\n🔴 TOP ALERTES")
            for a in self.alerts[:5]:
                print(f"   [{a.get('grade')}] {a.get('url', '')[:40]}...")
        
        print("\n" + "=" * 80)


def main():
    print("🚀 INITIALISATION SCANNER INTÉGRAL MCP")
    
    # 1. Charger DB
    try:
        hadiths = load_hadiths_from_db()
    except Exception as e:
        print(f"{e}")
        sys.exit(1)
    
    # 2. Créer scanner
    scanner = ScannerIntegralMCP(hadiths)
    
    # 3. Mode: un seul site (salafs.com) pour test
    scanner.run_scan_single("salafs.com")
    
    # Après confirmation utilisateur:
    # scanner.run_scan_full()


if __name__ == "__main__":
    main()
