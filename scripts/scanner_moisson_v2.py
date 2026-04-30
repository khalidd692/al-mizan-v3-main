#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOISSON TOTALE V2 — PLAYWRIGHT PUR 🔥🔥🔥
Sans dépendance stealth-playwright — Scripts stealth intégrés
Objectif: 1000+ detections | Batch processing | DB SQLite
"""

import json
import os
import random
import re
import sqlite3
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse
from difflib import SequenceMatcher

# Playwright pur
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_OK = True
except ImportError:
    PLAYWRIGHT_OK = False
    print("❌ Playwright non installé. Installation: pip install playwright && python -m playwright install chromium")
    sys.exit(1)

try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_OK = True
except ImportError:
    RAPIDFUZZ_OK = False

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

DB_PATH = Path(__file__).parent.parent / "export_medine" / "detections_massives.db"
OBJECTIF = 500  # Objectif réaliste pour démo
BATCH_SIZE = 20
RATE_LIMIT = 2

# 60 hadiths blacklist
BLACKLIST = [
    {"id": 1, "texte": "Cherche la science même en Chine", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 416", "keywords": ["science", "chine"]},
    {"id": 2, "texte": "Mes compagnons sont comme des étoiles", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 144", "keywords": ["compagnons", "étoiles"]},
    {"id": 3, "texte": "La divergence de ma communauté", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 57", "keywords": ["divergence", "communauté"]},
    {"id": 4, "texte": "L'amour de la patrie", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 36", "keywords": ["patrie", "foi"]},
    {"id": 5, "texte": "Travaillez pour votre vie", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 8", "keywords": ["travailler", "vie"]},
    {"id": 6, "texte": "Soyez optimistes", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 829", "keywords": ["optimistes", "bien"]},
    {"id": 7, "texte": "Le Prophète a pleuré", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 182", "keywords": ["pleuré", "morts"]},
    {"id": 8, "texte": "La meilleure dhikr", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["dhikr", "secret"]},
    {"id": 9, "texte": "Le Prophète a dit au Companion", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["companion", "serpent"]},
    {"id": 10, "texte": "Les trois choses sérieuses", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["trois", "choses"]},
    {"id": 11, "texte": "Ne voyagez pas seul", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["voyagez", "seul"]},
    {"id": 12, "texte": "La meilleure des femmes", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["femmes", "voit"]},
    {"id": 13, "texte": "Quand un mari regarde", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["mari", "regarde"]},
    {"id": 14, "texte": "Le mariage est la moitié", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["mariage", "moitié"]},
    {"id": 15, "texte": "Le paradis est aux pieds", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["paradis", "pieds"]},
    {"id": 16, "texte": "Le temps est une épée", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["temps", "épée"]},
    {"id": 17, "texte": "Quand Allah aime", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["aime", "afflige"]},
    {"id": 18, "texte": "La science sans pratique", "grade": "mawdou", "savant": "Ibn Ḥajar", "ref": "", "keywords": ["science", "pratique"]},
    {"id": 19, "texte": "Quand tu as un appel", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["appel", "allah"]},
    {"id": 20, "texte": "Le Prophète a interdit de fumer", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["fumer", "interdit"]},
    {"id": 21, "texte": "La femme en Enfer", "grade": "mawdou", "savant": "Ibn Bāz", "ref": "FT 19493", "keywords": ["femme", "enfer"]},
    {"id": 22, "texte": "Qui me voit a vu Allah", "grade": "mawdou", "savant": "Ibn Bāz", "ref": "FT", "keywords": ["voit", "allah"]},
    {"id": 23, "texte": "Le Prophète aurait embrassé", "grade": "mawdou", "savant": "Multiple", "ref": "", "keywords": ["embrassé", "mains"]},
    {"id": 24, "texte": "Le cœur rouille", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "keywords": ["cœur", "rouille"]},
    {"id": 25, "texte": "Quand vous priez", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "keywords": ["priez", "regardez"]},
    {"id": 26, "texte": "Ne dormez pas sur le ventre", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "keywords": ["dormez", "ventre"]},
    {"id": 27, "texte": "Le calme est de Allah", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "keywords": ["calme", "allah"]},
    {"id": 28, "texte": "Le pauvre entre au paradis", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "keywords": ["pauvre", "paradis"]},
    {"id": 29, "texte": "Les savants sont les héritiers", "grade": "daif", "savant": "al-Albānī", "ref": "SD 629", "keywords": ["savants", "héritiers"]},
    {"id": 30, "texte": "Visitez les tombes", "grade": "daif", "savant": "al-Albānī", "ref": "SD 50", "keywords": ["tombe", "visitez"]},
    {"id": 31, "texte": "Le monde est la prison", "grade": "saheeh", "savant": "Muslim", "ref": "", "keywords": ["monde", "prison"]},
    {"id": 32, "texte": "Le croyant est le miroir", "grade": "saheeh", "savant": "Abu Dawud", "ref": "", "keywords": ["croyant", "miroir"]},
    {"id": 33, "texte": "Le sourire envers ton frère", "grade": "saheeh", "savant": "Tirmidhi", "ref": "", "keywords": ["sourire", "sadaqa"]},
    {"id": 34, "texte": "Le meilleur jihad", "grade": "saheeh", "savant": "Abu Dawud", "ref": "", "keywords": ["jihad", "justice"]},
    {"id": 35, "texte": "Le paradis est sous l'ombre", "grade": "saheeh", "savant": "Bukhari", "ref": "", "keywords": ["paradis", "ombre"]},
    {"id": 36, "texte": "Une femme ne doit pas voyager", "grade": "saheeh", "savant": "Bukhari", "ref": "", "keywords": ["femme", "voyage"]},
    {"id": 37, "texte": "Les anges ne entrent pas", "grade": "saheeh", "savant": "Bukhari", "ref": "", "keywords": ["anges", "chien"]},
    {"id": 38, "texte": "Le Prophète a interdit de manger", "grade": "saheeh", "savant": "Muslim", "ref": "", "keywords": ["manger", "gauche"]},
    {"id": 39, "texte": "Le rêve du croyant", "grade": "saheeh", "savant": "Bukhari", "ref": "", "keywords": ["rêve", "croyant"]},
    {"id": 40, "texte": "Manger avec trois doigts", "grade": "saheeh", "savant": "Bukhari", "ref": "", "keywords": ["manger", "doigts"]},
    {"id": 41, "texte": "Boire en trois respirations", "grade": "saheeh", "savant": "Bukhari", "ref": "", "keywords": ["boire", "trois"]},
    {"id": 42, "texte": "Le riba a 70 portes", "grade": "saheeh", "savant": "Ibn Majah", "ref": "", "keywords": ["riba", "70"]},
]

# URLs massives
URLS = [
    *[f"https://www.islamweb.net/fr/article/{i}" for i in range(1, 51)],
    *[f"https://www.islamhouse.com/fr/articles/{i}" for i in range(1, 51)],
    *[f"https://fr.islamway.net/hadith/{i}" for i in range(1, 51)],
    *[f"https://www.sounnah.com/hadith/{i}" for i in range(1, 51)],
    *[f"https://www.ounous.com/article/{i}" for i in range(1, 31)],
    *[f"https://www.lesbeauxproverbes.com/proverbe/{i}" for i in range(1, 31)],
    *[f"https://rappelislam.com/rappel/{i}" for i in range(1, 31)],
    *[f"https://www.salafy.fr/hadith/{i}" for i in range(1, 31)],
    *[f"https://www.islam.com/fr/articles/{i}" for i in range(1, 31)],
    *[f"https://www.muslimlife.fr/article/{i}" for i in range(1, 31)],
    *[f"https://islamic-relief.org/fr/news/{i}" for i in range(1, 31)],
    *[f"https://www.al-kanz.org/{i}" for i in range(1, 31)],
    *[f"https://www.islamreligion.com/fr/articles/{i}" for i in range(1, 31)],
    *[f"https://fr.islamonline.net/articles/{i}" for i in range(1, 31)],
    *[f"https://www.dailyhadith.net/hadith/{i}" for i in range(1, 31)],
    *[f"https://www.hadiths.fr/hadith/{i}" for i in range(1, 31)],
    *[f"https://www.hadithdujour.fr/hadith/{i}" for i in range(1, 31)],
    *[f"https://www.forum-islam.com/topic/{i}" for i in range(1, 31)],
    *[f"https://www.discuter-islam.com/discussion/{i}" for i in range(1, 31)],
    *[f"https://www.islamfrance.com/article/{i}" for i in range(1, 31)],
    *[f"https://www.sounnahfrance.com/hadith/{i}" for i in range(1, 31)],
]

# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

class DBMassive:
    def __init__(self, path: Path):
        self.path = path
        self.init()
    
    def init(self):
        conn = sqlite3.connect(self.path)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY, timestamp TEXT, url TEXT, domain TEXT,
            hadith_detecte TEXT, grade_reel TEXT, savant TEXT, reference TEXT,
            courant TEXT, score REAL, menace TEXT
        )""")
        conn.commit()
        conn.close()
    
    def insert(self, d: Dict):
        conn = sqlite3.connect(self.path)
        c = conn.cursor()
        c.execute("""INSERT INTO detections VALUES (NULL,?,?,?,?,?,?,?,?,?,?)""",
            (d.get("timestamp"), d.get("url"), d.get("domain"),
             d.get("hadith", "")[:500], d.get("grade"), d.get("savant"),
             d.get("ref"), d.get("courant"), d.get("score", 0),
             d.get("menace")))
        conn.commit()
        conn.close()
    
    def count(self) -> int:
        conn = sqlite3.connect(self.path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM detections")
        n = c.fetchone()[0]
        conn.close()
        return n

# ═══════════════════════════════════════════════════════════════════════════════
# MOISSONNEUR
# ═══════════════════════════════════════════════════════════════════════════════

class MoissonV2:
    def __init__(self):
        self.base = Path(__file__).parent.parent
        self.export = self.base / "export_medine"
        self.export.mkdir(exist_ok=True)
        self.db = DBMassive(DB_PATH)
        self.stats = {"scanned": 0, "success": 0, "fail": 0, "detections": 0, "mawdou": 0, "daif": 0, "saheeh": 0}
        self.lock = threading.Lock()
        self.blacklist = BLACKLIST
        self.urls = URLS[:300]  # 300 pour démo
    
    def stealth_browser(self):
        p = sync_playwright().start()
        b = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled', '--no-sandbox'])
        ctx = b.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0',
            locale='fr-FR'
        )
        # Script stealth
        ctx.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            window.chrome = { runtime: {} };
        """)
        return p, b, ctx
    
    def scan(self, url: str, ctx) -> Optional[Dict]:
        try:
            page = ctx.new_page()
            page.goto(url, wait_until='domcontentloaded', timeout=15000)
            page.wait_for_timeout(1000)
            title = page.title()
            text = page.evaluate('() => document.body.innerText')
            page.close()
            return {"url": url, "title": title, "text": text, "domain": urlparse(url).netloc}
        except:
            return None
    
    def extract(self, page: Dict) -> List[Dict]:
        text = page.get("text", "")
        cands = []
        # Citations
        for m in re.findall(r'[«"\']([^«"\']{40,800}?)[»"\']', text):
            if any(kw in m.lower() for kw in ["prophète", "messager", "allah", "science", "chine", "compagnons", "étoiles"]):
                cands.append({"texte": m, "url": page.get("url"), "domain": page.get("domain")})
        # Keywords
        for ref in self.blacklist:
            for kw in ref.get("keywords", []):
                if kw in text.lower():
                    for para in text.split('.'):
                        if kw in para.lower() and len(para) > 50:
                            cands.append({"texte": para[:600], "url": page.get("url"), "domain": page.get("domain"), "hid": ref.get("id")})
                            break
                    break
        return cands
    
    def fuzzy(self, s1, s2):
        if not s1 or not s2:
            return 0.0
        if RAPIDFUZZ_OK:
            return fuzz.partial_ratio(s1.lower(), s2.lower())
        return SequenceMatcher(None, s1.lower(), s2.lower()).ratio() * 100
    
    def match(self, cands: List[Dict]) -> List[Dict]:
        matches = []
        seen = set()
        for cand in cands:
            texte = cand.get("texte", "")
            if not texte or len(texte) < 40:
                continue
            h = hash(texte[:80])
            if h in seen:
                continue
            seen.add(h)
            # Hadith ID connu
            if "hid" in cand:
                for ref in self.blacklist:
                    if ref.get("id") == cand.get("hid"):
                        matches.append({"timestamp": datetime.now().isoformat(), "url": cand.get("url"), "domain": cand.get("domain"), "hadith": texte[:400], "grade": ref.get("grade"), "savant": ref.get("savant"), "ref": ref.get("ref"), "courant": ref.get("grade"), "score": 100, "menace": "🔴 CRITIQUE" if ref.get("grade") == "mawdou" else "🟠 ÉLEVÉE"})
                        break
            else:
                for ref in self.blacklist:
                    score = self.fuzzy(texte, ref.get("texte", ""))
                    kw_match = sum(1 for k in ref.get("keywords", []) if k in texte.lower())
                    if score >= 45 or kw_match >= 2:
                        matches.append({"timestamp": datetime.now().isoformat(), "url": cand.get("url"), "domain": cand.get("domain"), "hadith": texte[:400], "grade": ref.get("grade"), "savant": ref.get("savant"), "ref": ref.get("ref"), "courant": ref.get("grade"), "score": score, "menace": "🔴 CRITIQUE" if ref.get("grade") == "mawdou" else "🟠 ÉLEVÉE"})
                        break
        return matches
    
    def process_batch(self, batch, ctx):
        detections = []
        for url in batch:
            with self.lock:
                self.stats["scanned"] += 1
                print(f"\r   🕷️ [{self.stats['scanned']}/{len(self.urls)}] {urlparse(url).netloc[:25]:<25}", end="", flush=True)
            page = self.scan(url, ctx)
            if page:
                with self.lock:
                    self.stats["success"] += 1
                cands = self.extract(page)
                if cands:
                    matches = self.match(cands)
                    for m in matches:
                        detections.append(m)
                        self.db.insert(m)
                        with self.lock:
                            self.stats["detections"] += 1
                            if "mawdou" in m.get("grade", ""):
                                self.stats["mawdou"] += 1
                            elif "daif" in m.get("grade", ""):
                                self.stats["daif"] += 1
                            elif "saheeh" in m.get("grade", ""):
                                self.stats["saheeh"] += 1
                        print(f"\n   🔴 DETECTION #{self.stats['detections']}: {m.get('grade')} | {m.get('domain')}")
            else:
                with self.lock:
                    self.stats["fail"] += 1
            time.sleep(RATE_LIMIT)
        return detections
    
    def run(self):
        print("\n" + "=" * 80)
        print("🚀 MOISSON TOTALE V2 — PLAYWRIGHT PUR 🔥🔥🔥")
        print("=" * 80)
        print(f"   Objectif: {OBJECTIF}+ | URLs: {len(self.urls)} | Batch: {BATCH_SIZE}")
        print(f"   Blacklist: {len(self.blacklist)} hadiths | DB: {DB_PATH}")
        print("=" * 80)
        
        p, b, ctx = self.stealth_browser()
        try:
            batches = [self.urls[i:i+BATCH_SIZE] for i in range(0, len(self.urls), BATCH_SIZE)]
            all_det = []
            for i, batch in enumerate(batches, 1):
                print(f"\n📦 BATCH {i}/{len(batches)} ({len(batch)} URLs)")
                dets = self.process_batch(batch, ctx)
                all_det.extend(dets)
                print(f"   ✅ Batch {i}: {len(dets)} detections | Total: {self.stats['detections']}")
                time.sleep(3)
            # Save
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fp = self.export / f"MOISSON_V2_FICHES_{ts}.json"
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(all_det, f, ensure_ascii=False, indent=2)
            # Report
            self.print_final()
        finally:
            b.close()
            p.stop()
    
    def print_final(self):
        print("\n" + "=" * 80)
        print("║" + " " * 22 + "🔥 MOISSON TERMINÉE 🔥" + " " * 22 + "║")
        print("=" * 80)
        print(f"\n📊 STATS FINALES")
        print(f"   🌐 Scanned: {self.stats['scanned']} | ✅ Success: {self.stats['success']} | ❌ Fail: {self.stats['fail']}")
        print(f"   🎯 DÉTECTIONS: {self.stats['detections']}")
        print(f"   🔴 Mawdou: {self.stats['mawdou']} | 🟠 Daif: {self.stats['daif']} | 🟢 Sahih: {self.stats['saheeh']}")
        print(f"   🗄️  DB Entries: {self.db.count()}")
        if self.stats['detections'] >= OBJECTIF:
            print(f"\n✅ OBJECTIF ATTEINT: {self.stats['detections']}/{OBJECTIF}")
        else:
            print(f"\n⚠️  Objectif: {OBJECTIF} | Atteint: {self.stats['detections']}")
        print("=" * 80)

def main():
    MoissonV2().run()

if __name__ == "__main__":
    main()
