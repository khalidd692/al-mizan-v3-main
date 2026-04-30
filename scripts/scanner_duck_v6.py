#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCANNER DUCKDUCKGO V6 — PAS D'API KEY 🔥
DuckDuckGo HTML Scraping + Playwright Stealth
Pas de quota, pas de clé, déluge de résultats
"""

import json
import random
import re
import sys
import threading
import time
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse, urljoin, quote_plus

import os
import sqlite3
import requests
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_OK = True
except ImportError:
    PLAYWRIGHT_OK = False

# ═══════════════════════════════════════════════════════════════════════════════
# CHARGEMENT DEPUIS LA BASE DE DONNÉES RÉELLE
# ═══════════════════════════════════════════════════════════════════════════════

def load_from_db():
    """Charge les hadiths Mawdou' et Da'if depuis almizan_v7.db"""
    db_path = r'C:\Users\sabri\Desktop\al-mizan-v3-main\backend\database\almizan_v7.db'
    
    if not os.path.exists(db_path):
        raise Exception(f"[ERREUR CRITIQUE] Base de données introuvable: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Vérifier que la table existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entries'")
    if not cursor.fetchone():
        conn.close()
        raise Exception("[ERREUR CRITIQUE] Table 'entries' inexistante dans la DB")
    
    # Charger les hadiths Mawdou' et Da'if
    cursor.execute("""
        SELECT id, fr_text, grade_primary, grade_albani, grade_ibn_baz, grade_ibn_uthaymin, grade_muqbil
        FROM entries 
        WHERE grade_primary IN ("Mawdu'", "Da'if", "Shadh", "Munkar") 
        AND fr_text IS NOT NULL
        ORDER BY grade_primary
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        raise Exception("[ERREUR CRITIQUE] Aucun hadith Mawdou'/Da'if trouvé dans la DB")
    
    hadiths = []
    for row in rows:
        hadith_id, fr_text, grade, alb, baz, uth, muq = row
        # Déterminer le savant vérificateur
        savant = "al-Albānī"
        if baz:
            savant = "Ibn Bāz"
        elif uth:
            savant = "Ibn Uthaymīn"
        elif muq:
            savant = "Muqbil"
        elif alb:
            savant = "al-Albānī"
        
        # Extraire keywords simples (3 premiers mots significatifs)
        words = [w.lower() for w in fr_text.split() if len(w) > 3][:5]
        keywords = words[:3] if len(words) >= 3 else words
        
        hadiths.append({
            "id": hadith_id,
            "texte": fr_text[:300],  # Tronquer pour le matching
            "grade": grade.lower().replace("'", ""),
            "savant": savant,
            "reference": f"DB:{hadith_id}",
            "courant": "Inconnu",
            "keywords": keywords
        })
    
    print(f"[DB LOAD] {len(hadiths)} hadiths chargés (Mawdou'/Da'if)")
    return hadiths

# Charger depuis la DB au lieu de la liste codée en dur
try:
    HADITHS_CIBLES = load_from_db()
except Exception as e:
    print(f"{e}")
    print("[ABANDON] Arrêt du scan - DB inaccessible")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════════
# DUCKDUCKGO SCRAPER — PAS DE CLÉ API
# ═══════════════════════════════════════════════════════════════════════════════

class DuckDuckGoSearcher:
    """Recherche DuckDuckGo sans API key"""
    
    BASE_URL = "https://html.duckduckgo.com/html/"
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def search(self, query: str, lang: str = "fr-fr", max_results: int = 30) -> List[str]:
        """Recherche DuckDuckGo et retourne les URLs"""
        urls = []
        
        try:
            params = {
                "q": query,
                "kl": lang,
                "api": "d.js"
            }
            
            response = self.session.post(self.BASE_URL, data=params, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extraction des résultats
            for result in soup.select(".result"):
                link = result.select_one(".result__a")
                if link and link.get("href"):
                    url = link["href"]
                    if url.startswith("http"):
                        urls.append(url)
            
            # Alternative selectors
            if not urls:
                for a in soup.select("a[href]"):
                    href = a.get("href", "")
                    if href.startswith("http") and "duckduckgo" not in href:
                        urls.append(href)
            
            return urls[:max_results]
            
        except Exception as e:
            print(f"   ⚠️ DuckDuckGo error: {e}")
            return []
    
    def search_hadith_french(self, hadith_text: str, max_results: int = 20) -> List[str]:
        """Recherche spécifique pour hadiths en français"""
        # Extraire mots-clés
        keywords = hadith_text.lower().split()[:8]
        query = " ".join(keywords) + " hadith prophète"
        return self.search(query, max_results=max_results)


# ═══════════════════════════════════════════════════════════════════════════════
# SCANNER DUCK V6 — PLAYWRIGHT + DUCKDUCKGO
# ═══════════════════════════════════════════════════════════════════════════════

class ScannerDuckV6:
    """Scanner ultime: DuckDuckGo + Playwright Stealth"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.export_dir = self.base_dir / "export_medine"
        self.export_dir.mkdir(exist_ok=True)
        
        self.ddg = DuckDuckGoSearcher()
        self.cibles = HADITHS_CIBLES
        
        self.stats = {
            "searches": 0, "urls_found": 0, "pages_scan": 0,
            "hadiths_extraits": 0, "matches": 0, "fiches": 0,
            "mawdou": 0, "daif": 0, "saheeh": 0
        }
        
        self.fiches = []
        self.lock = threading.Lock()
    
    def create_stealth_browser(self):
        """Crée navigateur Playwright stealth"""
        p = sync_playwright().start()
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
            ]
        )
        ctx = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='fr-FR',
            timezone_id='Europe/Paris',
        )
        # Script anti-détection
        ctx.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            window.chrome = { runtime: {} };
        """)
        return p, browser, ctx
    
    def scan_page(self, url: str, context) -> Optional[Dict]:
        """Scan une page avec Playwright"""
        try:
            page = context.new_page()
            page.goto(url, wait_until='domcontentloaded', timeout=15000)
            page.wait_for_timeout(1000)
            
            title = page.title()
            text = page.evaluate('() => document.body.innerText')
            html = page.content()
            
            page.close()
            return {"url": url, "title": title, "text": text, "html": html}
        except Exception as e:
            return None
    
    def extract_hadiths(self, page: Dict) -> List[Dict]:
        """Extraction massive"""
        text = page.get("text", "")
        url = page.get("url", "")
        
        candidats = []
        
        # Pattern 1: Citations entre guillemets
        for match in re.findall(r'[«"\']([^«"\']{50,1000}?)[»"\']', text):
            if any(kw in match.lower() for kw in ["prophète", "messager", "allah", "science", "chine", "compagnons", "étoiles", "divergence", "patrie", "mariage", "paradis", "femme", "mères", "sourire", "croyant", "miroir"]):
                candidats.append({
                    "texte": match.strip(),
                    "url": url,
                    "source": "citation"
                })
        
        # Pattern 2: Keywords hadith
        for ref in self.cibles:
            for kw in ref.get("keywords", []):
                if kw in text.lower():
                    # Extraire phrase contexte
                    for para in text.split('.'):
                        if kw in para.lower() and len(para) > 60:
                            candidats.append({
                                "texte": para.strip()[:800],
                                "url": url,
                                "source": "keyword",
                                "hadith_id": ref.get("id"),
                                "keyword": kw
                            })
                            break
                    break
        
        return candidats
    
    def fuzzy_match(self, text1: str, text2: str) -> float:
        """Score fuzzy"""
        return fuzz.partial_ratio(text1.lower(), text2.lower())
    
    def matcher(self, candidats: List[Dict]) -> List[Dict]:
        """Matching avec seuil 45%"""
        matches = []
        seen = set()
        
        for cand in candidats:
            texte = cand.get("texte", "")
            if not texte or len(texte) < 40:
                continue
            
            # Dédoublonnage
            h = hash(texte[:100])
            if h in seen:
                continue
            seen.add(h)
            
            # Si hadith_id connu
            if "hadith_id" in cand:
                for ref in self.cibles:
                    if ref.get("id") == cand.get("hadith_id"):
                        matches.append({
                            "timestamp": datetime.now().isoformat(),
                            "url": cand.get("url"),
                            "hadith_detecte": texte[:500],
                            "grade_reel": ref.get("grade"),
                            "savant": ref.get("savant"),
                            "reference": ref.get("ref"),
                            "courant": ref.get("courant"),
                            "score": "100%",
                            "keywords_match": True,
                            "menace": "🔴 CRITIQUE" if ref.get("grade") == "mawdou" else "🟠 ÉLEVÉE"
                        })
                        break
            else:
                # Fuzzy matching
                for ref in self.cibles:
                    score = self.fuzzy_match(texte, ref.get("texte", ""))
                    kw_match = sum(1 for k in ref.get("keywords", []) if k in texte.lower())
                    
                    if score >= 45 or kw_match >= 2:
                        matches.append({
                            "timestamp": datetime.now().isoformat(),
                            "url": cand.get("url"),
                            "hadith_detecte": texte[:500],
                            "grade_reel": ref.get("grade"),
                            "savant": ref.get("savant"),
                            "reference": ref.get("ref"),
                            "courant": ref.get("courant"),
                            "score": f"{score:.0f}%",
                            "keywords_match": kw_match >= 2,
                            "menace": "🔴 CRITIQUE" if ref.get("grade") == "mawdou" else "🟠 ÉLEVÉE"
                        })
                        break
        
        return matches
    
    def process_url(self, url: str, context):
        """Traite une URL"""
        page = self.scan_page(url, context)
        if page:
            with self.lock:
                self.stats["pages_scan"] += 1
            
            cands = self.extract_hadiths(page)
            if cands:
                with self.lock:
                    self.stats["hadiths_extraits"] += len(cands)
                
                matches = self.matcher(cands)
                for match in matches:
                    self.fiches.append(match)
                    with self.lock:
                        self.stats["matches"] += 1
                        self.stats["fiches"] += 1
                        if "mawdou" in match.get("grade_reel", ""):
                            self.stats["mawdou"] += 1
                        elif "daif" in match.get("grade_reel", ""):
                            self.stats["daif"] += 1
                    
                    print(f"\n   🔴 DETECTION #{self.stats['fiches']}: {match.get('grade_reel')} | {urlparse(match.get('url', '')).netloc}")
    
    def executer_duck_scan(self):
        """Exécution scan DuckDuckGo + Playwright"""
        print("\n" + "=" * 80)
        print("🦆 DUCKDUCKGO V6 — PAS D'API KEY, PAS DE QUOTA 🔥")
        print("=" * 80)
        print(f"   🎯 Hadiths cibles: {len(self.cibles)}")
        print(f"   🔍 Moteur: DuckDuckGo HTML Scraping")
        print(f"   🕷️  Crawler: Playwright Stealth")
        print("=" * 80)
        
        # Phase 1: Discovery via DuckDuckGo
        print("\n📡 PHASE 1: DÉCOUVERTE DUCKDUCKGO")
        all_urls = set()
        
        # Recherches par hadith phare
        queries = [
            "science chine hadith prophète",
            "compagnons étoiles hadith",
            "divergence communauté miséricorde hadith",
            "patrie foi hadith",
            "mariage moitié foi hadith",
            "paradis pieds mères hadith",
        ]
        
        for query in queries:
            with self.lock:
                self.stats["searches"] += 1
                print(f"\n   🔍 [{self.stats['searches']}/{len(queries)}] Recherche: '{query}'")
            
            urls = self.ddg.search(query, max_results=20)
            for url in urls:
                if any(domain in url for domain in ["islam", "sounnah", "hadith", "muslim", "coran", "fr"]):
                    all_urls.add(url)
            
            with self.lock:
                self.stats["urls_found"] = len(all_urls)
            
            print(f"   ✅ {len(urls)} URLs | Total uniques: {len(all_urls)}")
            time.sleep(2)
        
        # Phase 2: Crawling avec Playwright
        print(f"\n🕷️  PHASE 2: CRAWLING PLAYWRIGHT ({len(all_urls)} URLs)")
        
        if not PLAYWRIGHT_OK:
            print("   ❌ Playwright non disponible")
            return
        
        p, browser, context = self.create_stealth_browser()
        
        try:
            urls_list = list(all_urls)[:100]  # Limiter pour démo
            
            for i, url in enumerate(urls_list, 1):
                print(f"\r   🕷️ [{i}/{len(urls_list)}] {urlparse(url).netloc[:35]:<35}", end="", flush=True)
                self.process_url(url, context)
                time.sleep(1.5)
            
        finally:
            browser.close()
            p.stop()
        
        # Sauvegarde
        self.sauvegarder()
        self.print_rapport()
    
    def sauvegarder(self):
        """Sauvegarde"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        fiches_path = self.export_dir / f"DUCK_V6_FICHES_{ts}.json"
        with open(fiches_path, "w", encoding="utf-8") as f:
            json.dump(self.fiches, f, ensure_ascii=False, indent=2)
        
        rapport = {
            "scanner": "DuckDuckGo V6",
            "timestamp": ts,
            "stats": self.stats,
            "total_detections": len(self.fiches)
        }
        
        rapport_path = self.export_dir / f"DUCK_V6_RAPPORT_{ts}.json"
        with open(rapport_path, "w", encoding="utf-8") as f:
            json.dump(rapport, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 SAUVEGARDE:")
        print(f"   📄 Fiches: {fiches_path}")
        print(f"   📊 Rapport: {rapport_path}")
    
    def print_rapport(self):
        """Rapport final"""
        print("\n" + "=" * 80)
        print("║" + " " * 28 + "🦆 DUCK V6 TERMINÉ 🦆" + " " * 28 + "║")
        print("=" * 80)
        
        print(f"\n📊 STATS")
        print(f"   🔍 Recherches DDG     : {self.stats['searches']}")
        print(f"   🌐 URLs découvertes   : {self.stats['urls_found']}")
        print(f"   📄 Pages scannées     : {self.stats['pages_scan']}")
        print(f"   🎯 DÉTECTIONS        : {self.stats['fiches']}")
        
        print(f"\n🎯 PAR GRADE")
        print(f"   🔴 MAWDOU : {self.stats['mawdou']}")
        print(f"   🟠 DAIF   : {self.stats['daif']}")
        
        if self.fiches:
            print(f"\n📋 TOP DÉTECTIONS")
            for f in self.fiches[:5]:
                print(f"   {f.get('menace')} {f.get('grade_reel')} | {urlparse(f.get('url','')).netloc[:25]}")
        
        print("=" * 80)


def main():
    scanner = ScannerDuckV6()
    scanner.executer_duck_scan()


if __name__ == "__main__":
    main()
