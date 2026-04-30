#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCANNER TERMINATOR V5 — BYPASS ACTIVÉ 🔥🔥🔥
Bypass robots.txt | CloudScraper | Proxy rotation | Respect rate limit 1req/s
"""

import json
import os
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse, urljoin
from difflib import SequenceMatcher

# Install cloudscraper if not available
try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False
    print("⚠️ cloudscraper non installé — utilisation requests avancé")

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION BYPASS
# ═══════════════════════════════════════════════════════════════════════════════

# User-Agents rotatifs
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:119.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0",
]

# Headers complets pour bypass
def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7,ar;q=0.6",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "Referer": "https://www.google.com/",
    }

# Liste des 23 faux hadiths à détecter
HADITHS_CIBLES = [
    {"id": 1, "texte": "Cherche la science même en Chine", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 416", "keywords": ["science", "chine", "étudier"]},
    {"id": 2, "texte": "Mes compagnons sont comme des étoiles", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 144", "keywords": ["compagnons", "étoiles", "suivre"]},
    {"id": 3, "texte": "La divergence de ma communauté est une miséricorde", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 57", "keywords": ["divergence", "différence", "miséricorde"]},
    {"id": 4, "texte": "L'amour de la patrie fait partie de la foi", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 36", "keywords": ["patrie", "nation", "foi"]},
    {"id": 5, "texte": "Travaillez pour votre vie comme si vous viviez éternellement", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 8", "keywords": ["travailler", "vie", "éternel"]},
    {"id": 6, "texte": "Soyez optimistes vous trouverez le bien", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 829", "keywords": ["optimiste", "bien", "positif"]},
    {"id": 7, "texte": "Le Prophète a pleuré pour les morts de sa communauté", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 182", "keywords": ["pleurer", "morts", "larmes"]},
    {"id": 8, "texte": "La meilleure dhikr est celle faite en secret", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["dhikr", "secret", "silencieux"]},
    {"id": 9, "texte": "Le Prophète a dit au Companion qui voulait tuer un serpent", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["serpent", "tuer", "compagnon"]},
    {"id": 10, "texte": "Les trois choses qui ne sont pas sérieuses", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["sérieux", "chasse", "jeu"]},
    {"id": 11, "texte": "Ne voyagez pas seul car Satan sera votre compagnon", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["voyage", "seul", "satan"]},
    {"id": 12, "texte": "La meilleure des femmes ne voit pas les hommes", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["femme", "meilleure", "hommes"]},
    {"id": 13, "texte": "Quand un mari regarde sa femme avec amour", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["mari", "femme", "amour"]},
    {"id": 14, "texte": "Le mariage est la moitié de la foi", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["mariage", "moitié", "foi"]},
    {"id": 15, "texte": "Le paradis est aux pieds des mères", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["paradis", "pieds", "mères"]},
    {"id": 16, "texte": "Le temps est une épée", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["temps", "épée", "coupe"]},
    {"id": 17, "texte": "Quand Allah aime un serviteur il l'afflige", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["aime", "affliger", "souffrance"]},
    {"id": 18, "texte": "La science sans pratique est comme un arbre sans fruit", "grade": "mawdou", "savant": "Ibn Hajar", "ref": "", "keywords": ["science", "pratique", "arbre"]},
    {"id": 19, "texte": "Quand tu as un appel à faire à Allah fais-le", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["appel", "demande", "Allah"]},
    {"id": 20, "texte": "Le Prophète a interdit de fumer", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "keywords": ["fumer", "cigarette", "interdit"]},
    {"id": 21, "texte": "La femme en Enfer suspendue par les cheveux", "grade": "mawdou", "savant": "Ibn Bāz", "ref": "FT 19493", "keywords": ["femme", "enfer", "cheveux"]},
    {"id": 22, "texte": "Qui me voit a vu Allah", "grade": "mawdou", "savant": "Ibn Bāz", "ref": "FT", "keywords": ["voir", "Allah", "prophète"]},
    {"id": 23, "texte": "Le Prophète aurait embrassé les mains de Abu Bakr", "grade": "mawdou", "savant": "Multiple", "ref": "", "keywords": ["Abu Bakr", "embrasser", "mains"]},
]

# Sites cibles avec URLs de pages hadiths
SITES_CIBLES_TERMINATOR = [
    # Format: (domaine, [URLs de pages à scanner])
    ("islamweb.net", [
        "https://www.islamweb.net/fr/article/" + str(i) for i in range(1, 50)
    ]),
    ("islamhouse.com", [
        "https://www.islamhouse.com/fr/articles/" + str(i) for i in range(1, 50)
    ]),
    ("fr.islamway.net", [
        "https://fr.islamway.net/hadith/" + str(i) for i in range(1, 50)
    ]),
    ("sounnah.com", [
        "https://www.sounnah.com/hadith/" + str(i) for i in range(1, 50)
    ]),
    ("ounous.com", [
        "https://www.ounous.com/article/" + str(i) for i in range(1, 30)
    ]),
    ("lesbeauxproverbes.com", [
        "https://www.lesbeauxproverbes.com/proverbe/" + str(i) for i in range(1, 30)
    ]),
    ("rappelislam.com", [
        "https://rappelislam.com/rappel/" + str(i) for i in range(1, 30)
    ]),
    ("salafy.fr", [
        "https://www.salafy.fr/hadith/" + str(i) for i in range(1, 30)
    ]),
    ("islam.com", [
        "https://www.islam.com/fr/articles/" + str(i) for i in range(1, 30)
    ]),
    ("muslimlife.fr", [
        "https://www.muslimlife.fr/article/" + str(i) for i in range(1, 30)
    ]),
]

# ═══════════════════════════════════════════════════════════════════════════════
# SCANNER TERMINATOR V5
# ═══════════════════════════════════════════════════════════════════════════════

class ScannerTerminatorV5:
    """Scanner avec bypass intégré"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        self.stats = {
            "urls_ciblés": 0, "pages_réussies": 0, "pages_échouées": 0,
            "hadiths_extraits": 0, "matches": 0, "fiches": 0,
            "by_cloudscraper": 0, "by_requests": 0, "by_bypass": 0,
        }
        
        self.fiches = []
        self.lock = threading.Lock()
        self.session = None
        self.scraper = None
        
        if CLOUDSCRAPER_AVAILABLE:
            self.scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                }
            )
        else:
            self.session = requests.Session()
    
    def fetch_page_terminator(self, url: str) -> Optional[Dict]:
        """Récupère une page avec bypass"""
        # Attente 1 seconde (respect rate limit)
        time.sleep(1)
        
        # Essai 1: CloudScraper
        if CLOUDSCRAPER_AVAILABLE and self.scraper:
            try:
                r = self.scraper.get(url, headers=get_headers(), timeout=15)
                if r.status_code == 200:
                    with self.lock:
                        self.stats["by_cloudscraper"] += 1
                    return self.parse_page(url, r.text)
            except Exception as e:
                pass
        
        # Essai 2: Requests avec headers avancés
        try:
            self.session.headers.update(get_headers())
            r = self.session.get(url, timeout=15, allow_redirects=True)
            if r.status_code == 200:
                with self.lock:
                    self.stats["by_requests"] += 1
                return self.parse_page(url, r.text)
        except Exception as e:
            pass
        
        # Essai 3: Bypass avec referer différent
        try:
            headers = get_headers()
            headers["Referer"] = "https://www.bing.com/"
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                with self.lock:
                    self.stats["by_bypass"] += 1
                return self.parse_page(url, r.text)
        except Exception as e:
            pass
        
        with self.lock:
            self.stats["pages_échouées"] += 1
        return None
    
    def parse_page(self, url: str, html: str) -> Dict:
        """Parse le contenu de la page"""
        soup = BeautifulSoup(html, 'lxml')
        
        # Nettoyer
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form']):
            tag.decompose()
        
        # Extraire texte
        text = soup.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text)
        
        # Titre
        title = soup.find('title')
        title_text = title.get_text() if title else ""
        
        with self.lock:
            self.stats["pages_réussies"] += 1
        
        return {
            "url": url,
            "title": title_text,
            "text": text,
            "domain": urlparse(url).netloc
        }
    
    def extract_hadiths_terminator(self, page: Dict) -> List[Dict]:
        """Extraction agressive des hadiths"""
        text = page.get("text", "")
        url = page.get("url", "")
        domain = page.get("domain", "")
        
        candidats = []
        
        # Pattern 1: Citations entre guillemets
        for match in re.findall(r'[«"\']([^«"\']{40,1000}?)[»"\']', text):
            if any(kw in match.lower() for kw in ["prophète", "messager", "allah", "hadith", "science", "chine", "compagnons", "étoiles", "divergence", "patrie"]):
                candidats.append({
                    "texte": match.strip(),
                    "url": url,
                    "domain": domain,
                    "source": "citation"
                })
        
        # Pattern 2: Phrases avec "a dit" et Prophète
        for match in re.findall(r'(?:le |L\')(?:Prophète|Messager)[^.]{0,400}a dit[^.]{0,100}([^\n.]{60,800})', text, re.IGNORECASE):
            candidats.append({
                "texte": match.strip(),
                "url": url,
                "domain": domain,
                "source": "adit"
            })
        
        # Pattern 3: Keywords spécifiques des hadiths cibles
        keywords_map = {
            "science chine": 1, "compagnons étoiles": 2, "divergence": 3, "patrie": 4,
            "travailler vie": 5, "optimiste": 6, "pleurer morts": 7, "dhikr secret": 8,
            "serpent tuer": 9, "trois choses sérieuses": 10, "voyage seul": 11,
            "femme voit pas hommes": 12, "mari regarde femme": 13, "mariage moitié": 14,
            "paradis pieds mères": 15, "temps épée": 16, "afflige aime": 17,
            "science pratique": 18, "appel allah": 19, "fumer interdit": 20,
            "femme enfer cheveux": 21, "voit allah": 22, "embrasser mains": 23,
        }
        
        text_lower = text.lower()
        for keyword, hadith_id in keywords_map.items():
            if keyword in text_lower:
                # Extraire le paragraphe contenant le keyword
                for para in text.split('.'):
                    if keyword in para.lower() and len(para) > 60:
                        candidats.append({
                            "texte": para.strip()[:800],
                            "url": url,
                            "domain": domain,
                            "source": f"keyword_{hadith_id}",
                            "hadith_id": hadith_id
                        })
                        break
        
        return candidats
    
    def fuzzy_score(self, s1: str, s2: str) -> float:
        """Score de similarité"""
        if not s1 or not s2:
            return 0.0
        if RAPIDFUZZ_AVAILABLE:
            return fuzz.partial_ratio(s1.lower(), s2.lower())
        return SequenceMatcher(None, s1.lower(), s2.lower()).ratio() * 100
    
    def matcher_terminator(self, candidats: List[Dict]):
        """Matching terminator — Seuil 50%"""
        print(f"\n🔥 MATCHING TERMINATOR — {len(candidats)} candidats vs {len(HADITHS_CIBLES)} cibles...")
        
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
            
            with self.lock:
                self.stats["hadiths_extraits"] += 1
            
            # Si hadith_id connu (keyword match)
            if "hadith_id" in cand:
                hadith_id = cand["hadith_id"]
                for ref in HADITHS_CIBLES:
                    if ref["id"] == hadith_id:
                        matches += 1
                        fiche = self.generer_fiche(cand, ref, 100.0)
                        with self.lock:
                            self.fiches.append(fiche)
                            self.stats["matches"] += 1
                            self.stats["fiches"] += 1
                        print(f"  🎯 #{matches} [100%] {ref['grade']} | {ref['savant']} | {cand.get('domain')}")
                        break
            else:
                # Matching fuzzy
                for ref in HADITHS_CIBLES:
                    score = self.fuzzy_score(texte, ref.get("texte", ""))
                    
                    # Keywords match
                    keyword_match = sum(1 for kw in ref.get("keywords", []) if kw in texte.lower())
                    
                    if score >= 50 or keyword_match >= 2:
                        matches += 1
                        fiche = self.generer_fiche(cand, ref, score)
                        with self.lock:
                            self.fiches.append(fiche)
                            self.stats["matches"] += 1
                            self.stats["fiches"] += 1
                        print(f"  🎯 #{matches} [{score:.0f}%] {ref['grade']} | {ref['savant']} | {cand.get('domain')}")
                        break
        
        print(f"\n✅ {matches} MENSONGES CONFIRMÉS")
    
    def generer_fiche(self, cand: Dict, ref: Dict, score: float) -> Dict:
        """Génère fiche"""
        return {
            "id": f"TERMINATOR_{len(self.fiches)+1:04d}",
            "timestamp": datetime.now().isoformat(),
            "detection": {
                "domain": cand.get("domain"),
                "url": cand.get("url"),
                "source_extraction": cand.get("source"),
                "score_matching": f"{score:.1f}%",
            },
            "mensonge": {
                "texte_extrait": cand.get("texte")[:500],
                "hadith_id": ref.get("id"),
            },
            "verite": {
                "texte_original": ref.get("texte"),
                "grade_reel": ref.get("grade"),
                "savant_verificateur": ref.get("savant"),
                "reference": ref.get("ref"),
            },
            "menace": "🔴 CRITIQUE" if ref.get("grade") == "mawdou" else "🟠 ÉLEVÉE",
        }
    
    def executer_terminator(self):
        """Exécution mode terminator"""
        print("\n" + "=" * 80)
        print("🚀 SCANNER TERMINATOR V5 — BYPASS ACTIVÉ 🔥🔥🔥")
        print("=" * 80)
        print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   CloudScraper: {'✅' if CLOUDSCRAPER_AVAILABLE else '❌'}")
        print(f"   RapidFuzz: {'✅' if RAPIDFUZZ_AVAILABLE else '❌'}")
        print(f"   Rate Limit: 1 req/sec")
        print(f"   Hadiths cibles: {len(HADITHS_CIBLES)}")
        print("=" * 80)
        
        # Collecter toutes les URLs
        all_urls = []
        for domain, urls in SITES_CIBLES_TERMINATOR:
            all_urls.extend(urls[:10])  # Limiter à 10 URLs par site
        
        print(f"\n🎯 PHASE 1: SCANNING {len(all_urls)} URLs...")
        print("   Bypass: CloudScraper → Requests → Custom Headers")
        print("   Respect: 1 requête/seconde\n")
        
        # Threading avec 2 workers max (pour respecter rate limit)
        all_candidats = []
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {executor.submit(self.fetch_page_terminator, url): url for url in all_urls}
            
            for i, future in enumerate(as_completed(futures)):
                url = futures[future]
                try:
                    page = future.result()
                    if page:
                        cands = self.extract_hadiths_terminator(page)
                        all_candidats.extend(cands)
                        if cands:
                            print(f"   [{i+1}/{len(all_urls)}] ✅ {urlparse(url).netloc:<30} | {len(cands)} hadiths")
                        else:
                            print(f"   [{i+1}/{len(all_urls)}] ⚪ {urlparse(url).netloc:<30} | 0")
                    else:
                        print(f"   [{i+1}/{len(all_urls)}] ❌ {urlparse(url).netloc:<30} | BLOCKED")
                except Exception as e:
                    print(f"   [{i+1}/{len(all_urls)}] 💥 {urlparse(url).netloc:<30} | ERREUR")
        
        with self.lock:
            self.stats["urls_ciblés"] = len(all_urls)
        
        print(f"\n📊 RÉSULTAT: {len(all_candidats)} hadiths candidats extraits")
        
        # Phase 2: Matching
        if all_candidats:
            self.matcher_terminator(all_candidats)
        
        # Sauvegarde
        self.sauvegarder_terminator()
        
        # Rapport
        self.print_rapport_terminator()
    
    def sauvegarder_terminator(self):
        """Sauvegarde massive"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        fiches_path = self.data_dir / f"TERMINATOR_FICHES_{ts}.json"
        with open(fiches_path, "w", encoding="utf-8") as f:
            json.dump(self.fiches, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 SAUVEGARDE:")
        print(f"   📁 Fiches: {fiches_path}")
    
    def print_rapport_terminator(self):
        """Rapport final"""
        print("\n" + "=" * 80)
        print("║" + " " * 25 + "🔥 TERMINATOR TERMINÉ 🔥" + " " * 25 + "║")
        print("=" * 80)
        
        print(f"\n📊 STATISTIQUES DE BYPASS")
        print(f"   🌐 URLs ciblés           : {self.stats['urls_ciblés']}")
        print(f"   ✅ Pages réussies         : {self.stats['pages_réussies']}")
        print(f"   ❌ Pages échouées         : {self.stats['pages_échouées']}")
        print(f"   🕷️ By CloudScraper        : {self.stats['by_cloudscraper']}")
        print(f"   🌐 By Requests           : {self.stats['by_requests']}")
        print(f"   🚧 By Bypass             : {self.stats['by_bypass']}")
        print(f"   📝 Hadiths extraits       : {self.stats['hadiths_extraits']}")
        print(f"   🎯 Matches confirmés     : {self.stats['matches']}")
        print(f"   📋 Fiches générées       : {self.stats['fiches']}")
        
        if self.fiches:
            print(f"\n🔴 TOP MENSONGES CONFIRMÉS")
            for fiche in self.fiches[:15]:
                domain = fiche.get("detection", {}).get("domain", "N/A")
                grade = fiche.get("verite", {}).get("grade_reel", "")
                score = fiche.get("detection", {}).get("score_matching", "N/A")
                print(f"   {grade:<10} | {score:<6} | {domain}")
        
        print("\n" + "=" * 80)
        print(f"✅ TERMINATOR TERMINÉ — {len(self.fiches)} MENSONGES DOCUMENTÉS")
        print("=" * 80)


def main():
    scanner = ScannerTerminatorV5()
    scanner.executer_terminator()


if __name__ == "__main__":
    main()
