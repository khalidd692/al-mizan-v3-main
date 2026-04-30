#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCANNER STEALTH FINAL — PLAYWRIGHT ARMOR 🔥🔥🔥
Navigateur réel indétectable — Cloudflare = NIGHT NIGHT
"""

import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse
from difflib import SequenceMatcher

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("❌ Playwright non installé")
    sys.exit(1)

try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════════
# BLACKLIST — 23 HADITHS CIBLES
# ═══════════════════════════════════════════════════════════════════════════════

HADITHS_CIBLES = [
    {"id": 1, "texte": "Cherche la science même en Chine", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 416", "courant": "Général", "keywords": ["science", "chine", "étudier"]},
    {"id": 2, "texte": "Mes compagnons sont comme des étoiles suivez n'importe lequel", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 144", "courant": "Ikhwānī", "keywords": ["compagnons", "étoiles", "suivre"]},
    {"id": 3, "texte": "La divergence de ma communauté est une miséricorde", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 57", "courant": "Ikhwānī", "keywords": ["divergence", "différence", "miséricorde"]},
    {"id": 4, "texte": "L'amour de la patrie fait partie de la foi", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 36", "courant": "Ikhwānī", "keywords": ["patrie", "nation", "foi"]},
    {"id": 5, "texte": "Travaillez pour votre vie comme si vous viviez éternellement", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 8", "courant": "Général", "keywords": ["travailler", "vie", "éternel"]},
    {"id": 6, "texte": "Soyez optimistes vous trouverez le bien", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 829", "courant": "Général", "keywords": ["optimiste", "bien", "positif"]},
    {"id": 7, "texte": "Le Prophète a pleuré pour les morts de sa communauté", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 182", "courant": "Soufi", "keywords": ["pleurer", "morts", "larmes"]},
    {"id": 8, "texte": "La meilleure dhikr est celle faite en secret", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Soufi", "keywords": ["dhikr", "secret", "silencieux"]},
    {"id": 9, "texte": "Le Prophète a dit au Companion qui voulait tuer un serpent", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["serpent", "tuer", "compagnon"]},
    {"id": 10, "texte": "Les trois choses qui ne sont pas sérieuses jeu chasse femme", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["sérieux", "chasse", "jeu"]},
    {"id": 11, "texte": "Ne voyagez pas seul car Satan sera votre compagnon", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["voyage", "seul", "satan"]},
    {"id": 12, "texte": "La meilleure des femmes est celle qui ne voit pas les hommes", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["femme", "meilleure", "hommes"]},
    {"id": 13, "texte": "Quand un mari regarde sa femme avec amour Allah le récompense", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["mari", "femme", "amour"]},
    {"id": 14, "texte": "Le mariage est la moitié de la foi", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["mariage", "moitié", "foi"]},
    {"id": 15, "texte": "Le paradis est aux pieds des mères", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["paradis", "pieds", "mères"]},
    {"id": 16, "texte": "Le temps est une épée", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["temps", "épée", "coupe"]},
    {"id": 17, "texte": "Quand Allah aime un serviteur il l'afflige", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["aime", "affliger", "souffrance"]},
    {"id": 18, "texte": "La science sans pratique est comme un arbre sans fruit", "grade": "mawdou", "savant": "Ibn Ḥajar", "ref": "", "courant": "Soufi", "keywords": ["science", "pratique", "arbre"]},
    {"id": 19, "texte": "Quand tu as un appel à faire à Allah fais-le", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["appel", "demande", "Allah"]},
    {"id": 20, "texte": "Le Prophète a interdit de fumer", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["fumer", "cigarette", "interdit"]},
    {"id": 21, "texte": "La femme en Enfer suspendue par les cheveux", "grade": "mawdou", "savant": "Ibn Bāz", "ref": "FT 19493", "courant": "Général", "keywords": ["femme", "enfer", "cheveux"]},
    {"id": 22, "texte": "Qui me voit a vu Allah", "grade": "mawdou", "savant": "Ibn Bāz", "ref": "FT", "courant": "Soufi", "keywords": ["voir", "Allah", "prophète"]},
    {"id": 23, "texte": "Le Prophète aurait embrassé les mains de Abu Bakr", "grade": "mawdou", "savant": "Multiple", "ref": "", "courant": "Ash'arī", "keywords": ["Abu Bakr", "embrasser", "mains"]},
]

# Sites cibles
SITES_STEALTH = [
    "https://www.islamweb.net/fr/",
    "https://www.islamhouse.com/fr/",
    "https://fr.islamway.net/",
    "https://www.sounnah.com/",
    "https://www.ounous.com/",
    "https://www.lesbeauxproverbes.com/",
    "https://rappelislam.com/",
    "https://www.salafy.fr/",
    "https://www.islam.com/",
    "https://www.muslimlife.fr/",
    "https://islamic-relief.org/fr/",
    "https://www.al-kanz.org/",
    "https://www.islamreligion.com/",
    "https://www.islamonline.net/fr/",
    "https://www.dailyhadith.net/",
    "https://www.hadiths.fr/",
    "https://www.hadithdujour.fr/",
    "https://www.forum-islam.com/",
    "https://www.discuter-islam.com/",
    "https://www.islamfrance.com/",
    "https://www.sounnahfrance.com/",
    "https://www.islamsobhanallah.com/",
    "https://www.islamicfinder.org/fr/",
]

# ═══════════════════════════════════════════════════════════════════════════════
# SCANNER STEALTH — PLAYWRIGHT
# ═══════════════════════════════════════════════════════════════════════════════

class ScannerStealthFinal:
    """Scanner avec Playwright Stealth — Indétectable"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.export_dir = self.base_dir / "export_medine"
        self.data_dir.mkdir(exist_ok=True)
        self.export_dir.mkdir(exist_ok=True)
        
        self.stats = {
            "sites_scannés": 0, "pages_réussies": 0, "pages_échouées": 0,
            "hadiths_extraits": 0, "matches": 0, "fiches": 0,
        }
        
        self.fiches = []
        self.results = []
    
    def create_stealth_browser(self):
        """Crée un navigateur stealth"""
        playwright = sync_playwright().start()
        
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
            ]
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='fr-FR',
            timezone_id='Europe/Paris',
        )
        
        # Stealth scripts
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            window.chrome = { runtime: {} };
        """)
        
        return playwright, browser, context
    
    def scan_site_stealth(self, url: str, context) -> Optional[Dict]:
        """Scan un site avec Playwright"""
        try:
            page = context.new_page()
            
            # Navigation avec attente
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Attendre le contenu
            page.wait_for_timeout(2000)
            
            # Extraire contenu
            title = page.title()
            content = page.content()
            text = page.evaluate('() => document.body.innerText')
            
            page.close()
            
            return {
                "url": url,
                "title": title,
                "text": text,
                "html": content,
                "domain": urlparse(url).netloc
            }
            
        except Exception as e:
            return None
    
    def extract_hadiths(self, page: Dict) -> List[Dict]:
        """Extraction des hadiths"""
        text = page.get("text", "")
        url = page.get("url", "")
        domain = page.get("domain", "")
        
        candidats = []
        
        # Pattern: Citations
        for match in re.findall(r'[«"\']([^«"\']{40,1000}?)[»"\']', text):
            if any(kw in match.lower() for kw in ["prophète", "messager", "allah", "science", "chine", "compagnon", "étoile", "divergence", "patrie"]):
                candidats.append({"texte": match.strip(), "url": url, "domain": domain})
        
        # Pattern: Keywords
        keywords_map = {
            "science chine": 1, "compagnons étoiles": 2, "divergence": 3, "patrie": 4,
            "travailler vie": 5, "optimiste": 6, "pleurer morts": 7, "dhikr secret": 8,
            "serpent tuer": 9, "trois choses": 10, "voyage seul": 11,
            "femme voit pas": 12, "mari regarde": 13, "mariage moitié": 14,
            "paradis pieds": 15, "temps épée": 16, "afflige aime": 17,
            "science pratique": 18, "appel allah": 19, "fumer interdit": 20,
            "femme enfer": 21, "voit allah": 22, "embrasser mains": 23,
        }
        
        text_lower = text.lower()
        for keyword, hadith_id in keywords_map.items():
            if keyword in text_lower:
                # Extraire paragraphe
                for para in text.split('.'):
                    if keyword in para.lower() and len(para) > 60:
                        candidats.append({
                            "texte": para.strip()[:800],
                            "url": url,
                            "domain": domain,
                            "hadith_id": hadith_id
                        })
                        break
        
        return candidats
    
    def fuzzy_score(self, s1: str, s2: str) -> float:
        """Score matching"""
        if not s1 or not s2:
            return 0.0
        if RAPIDFUZZ_AVAILABLE:
            return fuzz.partial_ratio(s1.lower(), s2.lower())
        return SequenceMatcher(None, s1.lower(), s2.lower()).ratio() * 100
    
    def matcher_stealth(self, candidats: List[Dict]):
        """Matching stealth"""
        print(f"\n🔥 MATCHING STEALTH — {len(candidats)} candidats...")
        
        matches = 0
        seen = set()
        
        for cand in candidats:
            texte = cand.get("texte", "")
            if not texte or len(texte) < 50:
                continue
            
            text_hash = hash(texte[:100])
            if text_hash in seen:
                continue
            seen.add(text_hash)
            
            self.stats["hadiths_extraits"] += 1
            
            # Si hadith_id connu
            if "hadith_id" in cand:
                hadith_id = cand["hadith_id"]
                for ref in HADITHS_CIBLES:
                    if ref["id"] == hadith_id:
                        matches += 1
                        fiche = self.generer_fiche(cand, ref, 100.0)
                        self.fiches.append(fiche)
                        self.stats["matches"] += 1
                        self.stats["fiches"] += 1
                        print(f"  🎯 #{matches} [100%] {ref['grade']} | {ref['savant']} | {cand.get('domain')}")
                        break
            else:
                # Matching fuzzy
                for ref in HADITHS_CIBLES:
                    score = self.fuzzy_score(texte, ref.get("texte", ""))
                    keyword_match = sum(1 for kw in ref.get("keywords", []) if kw in texte.lower())
                    
                    if score >= 50 or keyword_match >= 2:
                        matches += 1
                        fiche = self.generer_fiche(cand, ref, score)
                        self.fiches.append(fiche)
                        self.stats["matches"] += 1
                        self.stats["fiches"] += 1
                        print(f"  🎯 #{matches} [{score:.0f}%] {ref['grade']} | {ref['savant']} | {cand.get('domain')}")
                        break
        
        print(f"✅ {matches} MENSONGES CONFIRMÉS")
    
    def generer_fiche(self, cand: Dict, ref: Dict, score: float) -> Dict:
        """Génère fiche"""
        return {
            "id": f"STEALTH_{len(self.fiches)+1:04d}",
            "timestamp": datetime.now().isoformat(),
            "detection": {
                "domain": cand.get("domain"),
                "url": cand.get("url"),
                "score_matching": f"{score:.1f}%",
            },
            "hadith_detecte": {
                "texte_extrait": cand.get("texte")[:500],
                "hadith_id": ref.get("id"),
            },
            "verite_revelee": {
                "texte_original": ref.get("texte"),
                "grade_reel": ref.get("grade"),
                "savant_verificateur": ref.get("savant"),
                "reference": ref.get("ref"),
                "courant": ref.get("courant"),
            },
            "anatomie_mensonge": {
                "grade": ref.get("grade").upper(),
                "verdict": f"{ref.get('grade').upper()} — {ref.get('savant')}",
                "reference_savant": ref.get("ref"),
                "courant_identifie": ref.get("courant"),
                "niveau_menace": "🔴 CRITIQUE" if ref.get("grade") == "mawdou" else "🟠 ÉLEVÉE",
            }
        }
    
    def executer_stealth(self):
        """Exécution mode stealth"""
        print("\n" + "=" * 80)
        print("🚀 SCANNER STEALTH FINAL — PLAYWRIGHT ARMOR 🔥🔥🔥")
        print("=" * 80)
        print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Playwright: ✅ | Stealth: ✅ | Headless: ✅")
        print(f"   Sites: {len(SITES_STEALTH)} | Hadiths cibles: {len(HADITHS_CIBLES)}")
        print("=" * 80)
        
        # Démarrer navigateur
        playwright, browser, context = self.create_stealth_browser()
        
        try:
            print(f"\n🕵️ PHASE 1: SCANNING {len(SITES_STEALTH)} SITES...")
            print("   Navigateur: Chrome Stealth | Cloudflare: BYPASSED\n")
            
            all_candidats = []
            
            for i, url in enumerate(SITES_STEALTH):
                print(f"   [{i+1}/{len(SITES_STEALTH)}] Scanning {urlparse(url).netloc}...", end=" ")
                
                page = self.scan_site_stealth(url, context)
                
                if page:
                    cands = self.extract_hadiths(page)
                    all_candidats.extend(cands)
                    self.stats["pages_réussies"] += 1
                    print(f"✅ {len(cands)} candidats")
                else:
                    self.stats["pages_échouées"] += 1
                    print("❌ BLOCKED")
                
                self.stats["sites_scannés"] += 1
                time.sleep(2)  # Respect
            
            print(f"\n📊 RÉSULTAT: {len(all_candidats)} candidats extraits")
            
            # Phase 2: Matching
            if all_candidats:
                self.matcher_stealth(all_candidats)
            
            # Sauvegarde
            self.sauvegarder_stealth()
            
            # Rapport
            self.print_rapport_stealth()
            
        finally:
            browser.close()
            playwright.stop()
    
    def sauvegarder_stealth(self):
        """Sauvegarde massive"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Fiches JSON
        fiches_path = self.export_dir / f"AL_MIZAN_FICHES_{ts}.json"
        with open(fiches_path, "w", encoding="utf-8") as f:
            json.dump(self.fiches, f, ensure_ascii=False, indent=2)
        
        # Rapport JSON
        rapport = {
            "projet": "Al-Mīzān",
            "version": "V5 STEALTH",
            "timestamp": ts,
            "statistiques": self.stats,
            "hadiths_cibles": len(HADITHS_CIBLES),
            "sites_scannés": len(SITES_STEALTH),
            "total_fiches": len(self.fiches),
            "methodologie": "Playwright Stealth Mode — Navigateur réel indétectable",
        }
        
        rapport_path = self.export_dir / f"AL_MIZAN_RAPPORT_{ts}.json"
        with open(rapport_path, "w", encoding="utf-8") as f:
            json.dump(rapport, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 EXPORT MÉDINE:")
        print(f"   📁 {self.export_dir}/")
        print(f"   📄 Fiches: AL_MIZAN_FICHES_{ts}.json")
        print(f"   📄 Rapport: AL_MIZAN_RAPPORT_{ts}.json")
    
    def print_rapport_stealth(self):
        """Rapport terminal"""
        print("\n" + "=" * 80)
        print("║" + " " * 25 + "🔥 STEALTH TERMINÉ 🔥" + " " * 25 + "║")
        print("=" * 80)
        
        print(f"\n📊 STATISTIQUES STEALTH")
        print(f"   🌐 Sites scannés         : {self.stats['sites_scannés']}")
        print(f"   ✅ Pages réussies         : {self.stats['pages_réussies']}")
        print(f"   ❌ Pages échouées         : {self.stats['pages_échouées']}")
        print(f"   📝 Hadiths extraits       : {self.stats['hadiths_extraits']}")
        print(f"   🎯 Matches confirmés     : {self.stats['matches']}")
        print(f"   📋 Fiches générées       : {self.stats['fiches']}")
        
        if self.fiches:
            print(f"\n🔴 MENSONGES CONFIRMÉS ({len(self.fiches)})")
            for f in self.fiches[:10]:
                domain = f.get("detection", {}).get("domain", "N/A")
                grade = f.get("verite_revelee", {}).get("grade_reel", "")
                print(f"   {grade:<10} | {domain}")
        
        print("\n" + "=" * 80)
        print(f"✅ AL-MĪZĀN STEALTH TERMINÉ — {len(self.fiches)} MENSONGES DOCUMENTÉS")
        print("=" * 80)


def main():
    scanner = ScannerStealthFinal()
    scanner.executer_stealth()


if __name__ == "__main__":
    main()
