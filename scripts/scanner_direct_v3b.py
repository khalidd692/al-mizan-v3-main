#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCANNER DIRECT V3b — MODE INVASION 🔥🔥🔥
Crawling direct des sites islamiques francophones — PAS DE LIMITES API
"""

import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

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
# CIBLE MASSIVE — 50+ SITES ISLAMIQUES FRANCOPHONES
# ═══════════════════════════════════════════════════════════════════════════════

SITES_CIBLES_DIRECT = [
    # Rappels et blogs
    "https://rappelislam.com/",
    "https://www.islamweb.net/fr/",
    "https://www.islamhouse.com/fr/",
    "https://fr.islamway.net/",
    "https://www.sounna.com/",
    "https://www.ounous.com/",
    "https://www.islamsobhanallah.com/",
    "https://www.lesbeauxproverbes.com/",
    "https://www.al-kanz.org/",
    "https://www.muslimlife.fr/",
    "https://www.salafy.fr/",
    "https://www.islam.com/fr/",
    "https://www.islamreligion.com/fr/",
    "https://fr.islamonline.net/",
    "https://www.islamic-relief.org/fr/",
    "https://www.islamic-relief.fr/",
    "https://www.hadiths.fr/",
    "https://www.hadithdujour.fr/",
    "https://www.dailyhadith.net/",
    "https://www.islam-guide.com/fr/",
    
    # Forums
    "https://www.forum-islam.com/",
    "https://www.discuter-islam.com/",
    
    # Institutions
    "https://www.uoif.fr/",
    "https://www.cfcms.fr/",
    "https://www.mosqueedeparis.net/",
    
    # Médias
    "https://www.saphirnews.com/",
    "https://www.islametinfo.fr/",
    "https://www.al-kanz.org/",
    
    # Chaînes YouTube (via scraping si possible)
]

# Blacklist complète
BLACKLIST_DIRECT = [
    {"texte": "Cherche la science même en Chine", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 416", "courant": "Général"},
    {"texte": "Mes compagnons sont comme des étoiles suivez n'importe lequel", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 144", "courant": "Ikhwānī"},
    {"texte": "La divergence de ma communauté est une miséricorde", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 57", "courant": "Ikhwānī"},
    {"texte": "L'amour de la patrie fait partie de la foi", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 36", "courant": "Ikhwānī"},
    {"texte": "Travaillez pour votre vie comme si vous viviez éternellement", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 8", "courant": "Général"},
    {"texte": "Celui qui ne se soucie pas des affaires des musulmans n'en fait pas partie", "grade": "daif_jiddan", "savant": "al-Albānī", "ref": "SD 480", "courant": "Ikhwānī"},
    {"texte": "Soyez optimistes vous trouverez le bien", "grade": "la_asla_lahu", "savant": "al-Albānī", "ref": "SD 829", "courant": "Général"},
    {"texte": "Visitez les tombes car elles vous rappellent la mort", "grade": "daif", "savant": "al-Albānī", "ref": "SD 50", "courant": "Soufi"},
    {"texte": "Les savants sont les héritiers des prophètes", "grade": "daif", "savant": "al-Albānī", "ref": "SD 629", "courant": "Ash'arī"},
    {"texte": "Le Prophète a pleuré pour les morts de sa communauté", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 182", "courant": "Soufi"},
    {"texte": "La meilleure dhikr est celle faite en secret", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Soufi"},
    {"texte": "Le Prophète a dit au Companion qui voulait tuer un serpent", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Les trois choses qui ne sont pas sérieuses jeu chasse femme", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Ne voyagez pas seul car Satan sera votre compagnon", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "La meilleure des femmes est celle qui ne voit pas les hommes", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Quand un mari regarde sa femme avec amour Allah le récompense", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Le mariage est la moitié de la foi", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Le paradis est aux pieds des mères", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Le temps est une épée", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Quand Allah aime un serviteur il l'afflige", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "La science sans pratique est comme un arbre sans fruit", "grade": "la_asla_lahu", "savant": "Ibn Ḥajar", "ref": "", "courant": "Soufi"},
    {"texte": "Le cœur rouille comme le fer", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Quand tu as un appel à faire à Allah fais-le", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Quand vous priez ne regardez ni à droite ni à gauche", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Ne dormez pas sur le ventre car c'est la position de l'Enfer", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Le Prophète a interdit de manger avec la main gauche", "grade": "saheeh", "savant": "Muslim", "ref": "", "courant": "Salafī"},
    {"texte": "Le Prophète a interdit de boire debout", "grade": "saheeh", "savant": "Muslim", "ref": "", "courant": "Salafī"},
    {"texte": "Le Prophète a dit de boire en trois respirations", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī"},
    {"texte": "Le Prophète a dit de manger avec trois doigts", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī"},
    {"texte": "Le Prophète a interdit de fumer", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Le Prophète a interdit le tabac", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Une femme ne doit pas voyager sans mahram", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī"},
    {"texte": "Les anges ne entrent pas dans une maison où il y a un chien", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī"},
    {"texte": "Les anges ne entrent pas dans une maison avec une image", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī"},
    {"texte": "Le monde est la prison du croyant et le paradis du mécréant", "grade": "saheeh", "savant": "Muslim", "ref": "", "courant": "Salafī"},
    {"texte": "Le croyant est le miroir de son frère", "grade": "saheeh", "savant": "Abu Dawud", "ref": "", "courant": "Général"},
    {"texte": "Le sourire envers ton frère est une sadaqa", "grade": "saheeh", "savant": "Tirmidhi", "ref": "", "courant": "Général"},
    {"texte": "Le meilleur jihad parler une parole de justice", "grade": "saheeh", "savant": "Abu Dawud", "ref": "", "courant": "Salafī"},
    {"texte": "Le paradis est sous l'ombre des épées", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī"},
    {"texte": "La femme en Enfer suspendue par les cheveux", "grade": "mawdou", "savant": "Ibn Bāz", "ref": "FT 19493", "courant": "Général"},
    {"texte": "Qui me voit a vu Allah", "grade": "mawdou", "savant": "Ibn Bāz", "ref": "FT", "courant": "Soufi"},
    {"texte": "Ne refuse pas le don d'eau", "grade": "mawdou", "savant": "Ibn Bāz", "ref": "", "courant": "Général"},
    {"texte": "Le Prophète aurait embrassé les mains de Abu Bakr", "grade": "mawdou", "savant": "Multiple", "ref": "", "courant": "Ash'arī"},
    {"texte": "Le Prophète a dit que le calme est de Allah", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Le Prophète a dit que le pauvre entre au paradis", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Le Prophète a dit que la bonté vers parents est jihad", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Le Prophète a dit que le rêve du croyant est vrai", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Général"},
    {"texte": "Le Prophète a dit que le riba a 70 portes", "grade": "saheeh", "savant": "Ibn Majah", "ref": "", "courant": "Salafī"},
]

HEADERS_DIRECT = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
}

# ═══════════════════════════════════════════════════════════════════════════════
# SCANNER DIRECT V3b
# ═══════════════════════════════════════════════════════════════════════════════

class ScannerDirectV3b:
    """Scanner invasion direct — Pas besoin d'API"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        self.stats = {
            "sites_ciblés": 0, "pages_crawlées": 0, "pages_réussies": 0,
            "pages_échouées": 0, "hadiths_extraits": 0,
            "mawdou_trouvés": 0, "daif_trouvés": 0, "saheeh_trouvés": 0,
            "matches_total": 0, "fiches_générées": 0,
            "courants": {"Ikhwānī": 0, "Tablīghī": 0, "Soufi": 0, "Ash'arī": 0, "Salafī": 0, "Général": 0}
        }
        
        self.fiches = []
        self.sites_infectés = {}
        self.lock = threading.Lock()
        self.session = requests.Session()
        self.session.headers.update(HEADERS_DIRECT)
        
        self.blacklist = BLACKLIST_DIRECT
        self.youtube_key = os.getenv("YOUTUBE_API_KEY")
    
    def crawl_site_direct(self, base_url: str, max_pages: int = 10) -> List[Dict]:
        """Crawl un site directement"""
        pages = []
        crawled = set()
        to_crawl = [base_url]
        
        try:
            for _ in range(max_pages):
                if not to_crawl:
                    break
                
                url = to_crawl.pop(0)
                if url in crawled:
                    continue
                crawled.add(url)
                
                r = self.session.get(url, timeout=15)
                
                with self.lock:
                    self.stats["pages_crawlées"] += 1
                
                if r.status_code != 200:
                    continue
                
                with self.lock:
                    self.stats["pages_réussies"] += 1
                
                soup = BeautifulSoup(r.content, 'lxml')
                
                # Nettoyer
                for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                    tag.decompose()
                
                text = soup.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text)
                
                if len(text) > 300:
                    pages.append({
                        "url": url,
                        "text": text,
                        "site": urlparse(base_url).netloc
                    })
                
                # Trouver liens internes
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('/'):
                        full_url = urljoin(base_url, href)
                        if full_url not in crawled and len(to_crawl) < max_pages:
                            to_crawl.append(full_url)
                
                time.sleep(0.5)
                
        except Exception as e:
            with self.lock:
                self.stats["pages_échouées"] += 1
        
        return pages
    
    def extract_hadiths_massif(self, page: Dict) -> List[Dict]:
        """Extraction massive des hadiths"""
        text = page.get("text", "")
        url = page.get("url", "")
        site = page.get("site", "")
        
        candidats = []
        
        # Pattern 1: Hadiths entre guillemets avec contexte
        for match in re.findall(r'[«"\']([^«"\']{50,800}?)[»"\']', text):
            if any(kw in match.lower() for kw in ["prophète", "messager", "allah", "sallallahu", "science", "chine", "compagnon", "étoile"]):
                candidats.append({"texte": match.strip(), "url": url, "site": site, "source": "guillemets"})
        
        # Pattern 2: Phrases clés
        phrases_cles = [
            r'le Prophète[^.]{0,200}a dit[^.]{0,50}([^\n.]{50,500})',
            r'le Messager[^.]{0,200}a dit[^.]{0,50}([^\n.]{50,500})',
            r'il est rapporté[^.]{0,300}([^\n.]{50,500})',
        ]
        
        for pattern in phrases_cles:
            for match in re.findall(pattern, text, re.IGNORECASE):
                candidats.append({"texte": match.strip(), "url": url, "site": site, "source": "pattern"})
        
        # Pattern 3: Paragraphes avec keywords
        keywords_viraux = ["science chine", "compagnons étoiles", "divergence", "patrie", "cœur rouille",
                          "paradis pieds mères", "anges chien", "monde prison", "meilleur femme",
                          "savants héritiers", "femme enfer cheveux"]
        
        for para in text.split('.'):
            para = para.strip()
            for kw in keywords_viraux:
                if kw in para.lower() and len(para) > 50:
                    candidats.append({"texte": para[:500], "url": url, "site": site, "source": f"keyword:{kw}"})
        
        return candidats
    
    def fuzzy_match(self, s1: str, s2: str) -> float:
        """Matching fuzzy"""
        if not s1 or not s2:
            return 0.0
        if RAPIDFUZZ_AVAILABLE:
            return fuzz.partial_ratio(s1.lower(), s2.lower())
        return 0.0
    
    def matcher_invasion(self, candidats: List[Dict]):
        """Matching mode invasion"""
        print(f"\n🔎 MATCHING INVASION — {len(candidats)} candidats vs {len(self.blacklist)} référencés...")
        
        matches = 0
        seen_texts = set()
        
        for cand in candidats:
            texte_cand = cand.get("texte", "")
            if not texte_cand or len(texte_cand) < 40:
                continue
            
            # Éviter doublons
            text_hash = hash(texte_cand[:100])
            if text_hash in seen_texts:
                continue
            seen_texts.add(text_hash)
            
            url = cand.get("url", "")
            site = cand.get("site", "")
            
            for ref in self.blacklist:
                score = self.fuzzy_match(texte_cand, ref.get("texte", ""))
                
                if score >= 65:
                    matches += 1
                    grade = ref.get("grade", "")
                    
                    # Stats par grade
                    with self.lock:
                        if "mawdou" in grade:
                            self.stats["mawdou_trouvés"] += 1
                        elif "daif" in grade:
                            self.stats["daif_trouvés"] += 1
                        elif "saheeh" in grade:
                            self.stats["saheeh_trouvés"] += 1
                        self.stats["matches_total"] += 1
                    
                    # Site infecté
                    if site not in self.sites_infectés:
                        self.sites_infectés[site] = []
                    self.sites_infectés[site].append(ref.get("texte", "")[:50])
                    
                    # Fiche
                    fiche = {
                        "id": f"INVASION_{len(self.fiches)+1:04d}",
                        "timestamp": datetime.now().isoformat(),
                        "site_infecté": site,
                        "url": url,
                        "hadith_circulant": texte_cand[:300],
                        "grade_réel": grade,
                        "savant_vérificateur": ref.get("savant"),
                        "référence": ref.get("ref"),
                        "score_matching": f"{score:.1f}%",
                        "courant": ref.get("courant"),
                        "menace": "CRITIQUE" if "mawdou" in grade else "ÉLEVÉE" if "daif" in grade else "MOYENNE"
                    }
                    
                    with self.lock:
                        self.fiches.append(fiche)
                        self.stats["fiches_générées"] += 1
                        self.stats["courants"][ref.get("courant", "Général")] = self.stats["courants"].get(ref.get("courant", "Général"), 0) + 1
                    
                    print(f"  🎯 #{matches} [{score:.0f}%] | {grade} | {ref.get('savant')} | {site}")
                    break
        
        print(f"✅ {matches} MENSONGES CONFIRMÉS SUR {len(self.sites_infectés)} SITES")
    
    def executer_invasion(self):
        """Exécution mode invasion"""
        print("\n" + "=" * 80)
        print("🚀 SCANNER DIRECT V3b — MODE INVASION 🔥")
        print("=" * 80)
        print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Sites ciblés: {len(SITES_CIBLES_DIRECT)}")
        print(f"   Blacklist: {len(self.blacklist)} hadiths")
        print(f"   RapidFuzz: {'✅' if RAPIDFUZZ_AVAILABLE else '❌'}")
        print("=" * 80)
        
        # Phase 1: Crawling massif
        print("\n🕷️ PHASE 1: CRAWLING INVASION...")
        all_candidats = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.crawl_site_direct, site, 5): site for site in SITES_CIBLES_DIRECT[:15]}
            
            for i, future in enumerate(as_completed(futures)):
                site = futures[future]
                try:
                    pages = future.result()
                    for page in pages:
                        cands = self.extract_hadiths_massif(page)
                        all_candidats.extend(cands)
                    print(f"   [{i+1}/15] {urlparse(site).netloc:<30} | {len(pages)} pages | {len(all_candidats)} candidats")
                except Exception as e:
                    print(f"   [{i+1}/15] {urlparse(site).netloc:<30} | ❌ ERREUR")
        
        with self.lock:
            self.stats["sites_ciblés"] = len(SITES_CIBLES_DIRECT)
            self.stats["hadiths_extraits"] = len(all_candidats)
        
        print(f"\n✅ {len(all_candidats)} HADITHS CANDIDATS EXTRAITS")
        
        # Phase 2: Matching
        if all_candidats:
            self.matcher_invasion(all_candidats)
        
        # Phase 3: Sauvegarde
        self.sauvegarder_invasion()
        
        # Phase 4: Rapport
        self.print_rapport_invasion()
    
    def sauvegarder_invasion(self):
        """Sauvegarde"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        fiches_path = self.data_dir / f"INVASION_FICHES_{ts}.json"
        with open(fiches_path, "w", encoding="utf-8") as f:
            json.dump(self.fiches, f, ensure_ascii=False, indent=2)
        
        sites_path = self.data_dir / f"INVASION_SITES_{ts}.json"
        with open(sites_path, "w", encoding="utf-8") as f:
            json.dump(self.sites_infectés, f, ensure_ascii=False, indent=2)
        
        rapport_path = self.data_dir / f"INVASION_RAPPORT_{ts}.json"
        with open(rapport_path, "w", encoding="utf-8") as f:
            json.dump({"stats": self.stats, "fiches": len(self.fiches)}, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 SAUVEGARDE:")
        print(f"   📁 Fiches: {fiches_path}")
        print(f"   📁 Sites infectés: {sites_path}")
    
    def print_rapport_invasion(self):
        """Rapport final"""
        print("\n" + "=" * 80)
        print("║" + " " * 25 + "🔥 INVASION TERMINÉE 🔥" + " " * 25 + "║")
        print("=" * 80)
        
        print(f"\n📊 STATISTIQUES D'INVASION")
        print(f"   🌐 Sites ciblés         : {self.stats['sites_ciblés']}")
        print(f"   📄 Pages crawlées        : {self.stats['pages_crawlées']}")
        print(f"   ✅ Pages réussies         : {self.stats['pages_réussies']}")
        print(f"   ❌ Pages échouées         : {self.stats['pages_échouées']}")
        print(f"   📝 Hadiths extraits       : {self.stats['hadiths_extraits']}")
        print(f"   🔥 MAWDOU (inventés)      : {self.stats['mawdou_trouvés']}")
        print(f"   ⚠️ DAIF (faibles)         : {self.stats['daif_trouvés']}")
        print(f"   ✓ SAHEEH (authentiques)   : {self.stats['saheeh_trouvés']}")
        print(f"   🎯 Matches total          : {self.stats['matches_total']}")
        print(f"   📋 Fiches générées        : {self.stats['fiches_générées']}")
        print(f"   🦠 Sites infectés        : {len(self.sites_infectés)}")
        
        print(f"\n🎯 MAPPING COURANTS")
        for c, n in sorted(self.stats["courants"].items(), key=lambda x: -x[1]):
            if n > 0:
                print(f"   {c:<12} : {n:>3}")
        
        if self.sites_infectés:
            print(f"\n🦠 TOP SITES INFECTÉS")
            for site, hadiths in sorted(self.sites_infectés.items(), key=lambda x: -len(x[1]))[:10]:
                print(f"   {site:<40} | {len(hadiths)} détections")
        
        print("\n" + "=" * 80)
        print(f"✅ INVASION TERMINÉE — {len(self.fiches)} MENSONGES DOCUMENTÉS")
        print("=" * 80)


def main():
    scanner = ScannerDirectV3b()
    scanner.executer_invasion()


if __name__ == "__main__":
    main()
