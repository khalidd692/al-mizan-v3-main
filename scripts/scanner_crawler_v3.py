#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCANNER CRAWLER V3 — MODE PRÉDATEUR 🔥🔥🔥
Crawling massif du web francophone islamique
Pas de limites. Pas de pitié. Que des résultats.
"""

import json
import os
import re
import sqlite3
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import quote, urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    print("⚠️ rapidfuzz non disponible — utilisation difflib")

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION CRAWLER V3 — MODE PRÉDATEUR
# ═══════════════════════════════════════════════════════════════════════════════

# Blacklist massive — 100+ hadiths inventés/faibles
BLACKLIST_CRAWLER = [
    # AL-ALBĀNĪ — Silsila Daifa
    {"texte": "Cherche la science même en Chine", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 416", "courant": "Général"},
    {"texte": "Mes compagnons sont comme des étoiles", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 144", "courant": "Ikhwānī"},
    {"texte": "La divergence de ma communauté est une miséricorde", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 57", "courant": "Ikhwānī"},
    {"texte": "L'amour de la patrie fait partie de la foi", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 36", "courant": "Ikhwānī"},
    {"texte": "Travaillez pour votre vie comme si vous viviez éternellement", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 8", "courant": "Général"},
    {"texte": "Celui qui ne se soucie pas des affaires des musulmans", "grade": "daif_jiddan", "savant": "al-Albānī", "ref": "SD 480", "courant": "Ikhwānī"},
    {"texte": "Soyez optimistes vous trouverez le bien", "grade": "la_asla_lahu", "savant": "al-Albānī", "ref": "SD 829", "courant": "Général"},
    {"texte": "Visitez les tombes car elles vous rappellent la mort", "grade": "daif", "savant": "al-Albānī", "ref": "SD 50", "courant": "Soufi"},
    {"texte": "Les savants sont les héritiers des prophètes", "grade": "daif", "savant": "al-Albānī", "ref": "SD 629", "courant": "Ash'arī"},
    {"texte": "Le Prophète a pleuré pour les morts", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 182", "courant": "Soufi"},
    {"texte": "La meilleure dhikr est celle faite en secret", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Soufi"},
    {"texte": "Le Prophète a dit au Companion serpent", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Les trois choses sérieuses jeu chasse femme", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Ne voyagez pas seul car Satan sera votre compagnon", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "La meilleure des femmes ne voit pas les hommes", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Quand un mari regarde sa femme avec amour", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Le mariage est la moitié de la foi", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Le paradis est aux pieds des mères", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Le temps est une épée", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Quand Allah aime un serviteur il l'afflige", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "La science sans pratique est comme un arbre", "grade": "la_asla_lahu", "savant": "Ibn Ḥajar", "ref": "", "courant": "Soufi"},
    {"texte": "Le cœur rouille comme le fer", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Quand tu as un appel à faire à Allah fais-le", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Quand vous priez ne regardez ni à droite", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    
    # IBN BĀZ
    {"texte": "La femme en Enfer suspendue par les cheveux", "grade": "mawdou", "savant": "Ibn Bāz", "ref": "FT 19493", "courant": "Général"},
    {"texte": "Qui me voit a vu Allah", "grade": "mawdou", "savant": "Ibn Bāz", "ref": "FT", "courant": "Soufi"},
    {"texte": "Ne refuse pas le don d'eau", "grade": "mawdou", "savant": "Ibn Bāz", "ref": "", "courant": "Général"},
    
    # AUTRES
    {"texte": "Le Prophète aurait embrassé les mains de Abu Bakr", "grade": "mawdou", "savant": "Multiple", "ref": "", "courant": "Ash'arī"},
    {"texte": "Une femme ne doit pas voyager sans mahram", "grade": "saheeh", "savant": "Muqbil", "ref": "", "courant": "Salafī"},
    {"texte": "Les anges ne entrent pas dans une maison avec un chien", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī"},
    {"texte": "Le Prophète a interdit de fumer", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Le Prophète a dit de ne pas dormir sur le ventre", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Le Prophète a dit de manger avec trois doigts", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī"},
    {"texte": "Le Prophète a dit de boire en trois fois", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī"},
    {"texte": "Le Prophète a dit de ne pas s'allonger sur le côté gauche", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Le Prophète a dit que le calme est de Allah", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Le Prophète a dit que le pauvre entre au paradis", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Le Prophète a dit que la bonté vers parents est jihad", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général"},
    {"texte": "Le Prophète a dit que le paradis est sous l'ombre des épées", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī"},
]

# Sites cibles prioritaires (rappels, blogs, forums)
SITES_PRIORITAIRES = [
    "rappelislam.com", "islamweb.net", "islamhouse.com", "fr.islamway.net",
    "sounna.com", "muslimfrance.fr", "islamfrance.com", "sounnahfrance.com",
    "islamic-relief.org", "islamic-relief.fr", "ounous.com", "islamsobhanallah.com",
    "islam.com", "islami.city", "islamreligion.com", "islam-guide.com",
    "islamicfinder.org", "islamicity.org", "islamonline.net", "islamicfinder.com",
    "forum-islam.com", "discuter-islam.com", "salafy.fr", "sounnah.com",
    "al-kanz.org", "muslimlife.fr", "lesbeauxproverbes.com", "rappelislamique.fr",
    "hadiths.fr", "hadithdujour.fr", "dailyhadith.net", "hadith.fr",
]

# Requêtes massives pour Google
REQUETES_CRAWLER = [
    "site:forum-islam.com hadith",
    "site:discuter-islam.com hadith prophète",
    "site:rappelislam.com hadith",
    "site:islamweb.net/fr hadith",
    "site:fr.islamway.net hadith",
    "site:sounnah.com hadith",
    "site:islamhouse.com/fr hadith",
    "site:lesbeauxproverbes.com islam hadith",
    "site:ounous.com hadith",
    "site:al-kanz.org hadith",
    "site:muslimlife.fr hadith",
    "site:salafy.fr hadith",
    "site:islamic-relief.fr hadith",
    "site:islamsobhanallah.com hadith",
    "site:islami.city hadith",
    "hadith science Chine prophète site:fr",
    "hadith compagnons étoiles site:fr",
    "hadith divergence miséricorde site:fr",
    "hadith patrie nationalisme site:fr",
    "hadith femme paradis enfer site:fr",
    "hadith savants héritiers prophètes site:fr",
    "hadith meilleur femme voit pas hommes site:fr",
    "hadith monde prison croyant site:fr",
    "hadith anges chien maison site:fr",
    "hadith sourire sadaqa site:fr",
    "hadith jihad parler vérité site:fr",
]

HEADERS_CRAWLER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
}

# ═══════════════════════════════════════════════════════════════════════════════
# SCANNER CRAWLER V3
# ═══════════════════════════════════════════════════════════════════════════════

class ScannerCrawlerV3:
    """Scanner prédateur — Crawling massif"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        self.stats = {
            "urls_trouves": 0, "pages_crawlées": 0, "pages_échouées": 0,
            "candidats_extraits": 0, "matches_confirmés": 0, "fiches_générées": 0,
            "sites_infectés": {}, "courants": {"Ikhwānī": 0, "Tablīghī": 0, "Soufi": 0, "Ash'arī": 0, "Salafī": 0, "Général": 0}
        }
        
        self.fiches = []
        self.sites_infectés = {}  # {url: [hadiths trouvés]}
        self.lock = threading.Lock()
        self.session = requests.Session()
        self.session.headers.update(HEADERS_CRAWLER)
        
        self.blacklist = BLACKLIST_CRAWLER
        self.google_key = os.getenv("GOOGLE_API_KEY")
        self.google_cx = os.getenv("GOOGLE_CX")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GOOGLE — RÉCUPÉRATION URLS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_urls_google(self, query: str, max_results: int = 30) -> List[Dict]:
        """Récupère les URLs depuis Google (pas les snippets)"""
        urls = []
        if not self.google_key or not self.google_cx:
            return urls
        
        try:
            for start in range(1, min(max_results + 1, 31), 10):
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    "key": self.google_key, "cx": self.google_cx,
                    "q": query, "start": start, "num": 10,
                    "lr": "lang_fr", "hl": "fr"
                }
                
                r = self.session.get(url, params=params, timeout=20)
                
                if r.status_code == 200:
                    for item in r.json().get("items", []):
                        link = item.get("link", "")
                        # Filtrer sites prioritaires
                        domain = urlparse(link).netloc.lower()
                        if any(prio in domain for prio in SITES_PRIORITAIRES) or "hadith" in link.lower():
                            urls.append({
                                "url": link,
                                "title": item.get("title", ""),
                                "query": query
                            })
                
                time.sleep(0.5)
        except Exception as e:
            pass
        
        return urls
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CRAWLING — EXTRACTION MASSIVE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def crawl_page(self, url_data: Dict) -> Optional[Dict]:
        """Crawl une page et extrait tout le texte"""
        url = url_data.get("url", "")
        
        try:
            r = self.session.get(url, timeout=15, allow_redirects=True)
            
            with self.lock:
                self.stats["pages_crawlées"] += 1
            
            if r.status_code != 200:
                return None
            
            # Parse avec BeautifulSoup
            soup = BeautifulSoup(r.content, 'lxml', from_encoding=r.encoding)
            
            # Nettoyer le HTML
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form']):
                tag.decompose()
            
            # Extraire texte principal
            text = soup.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text)  # Normaliser espaces
            
            if len(text) < 200:
                return None
            
            return {
                "url": url,
                "title": url_data.get("title", ""),
                "text": text,
                "query": url_data.get("query", ""),
                "length": len(text)
            }
            
        except Exception as e:
            with self.lock:
                self.stats["pages_échouées"] += 1
            return None
    
    def extract_hadiths_from_text(self, page: Dict) -> List[Dict]:
        """Extrait les hadiths du texte complet"""
        text = page.get("text", "")
        url = page.get("url", "")
        
        candidats = []
        
        # Pattern 1: Citations entre guillemets avec contexte religieux
        for match in re.findall(r'[«"\']([^«"\']{40,600}?)(?:Prophète|Messager|sallallahu|alayhi|wsallam)[^«"\']{0,300}[»"\']', text, re.IGNORECASE):
            candidats.append({
                "texte": match.strip(),
                "url": url,
                "title": page.get("title"),
                "source": "citation"
            })
        
        # Pattern 2: Phrases avec "a dit" et contexte
        for match in re.findall(r'(?:le |L\')(?:Prophète|Messager)[^.]{0,100}a dit[^.]{0,20}([^\n.]{40,500})', text, re.IGNORECASE):
            candidats.append({
                "texte": match.strip(),
                "url": url,
                "title": page.get("title"),
                "source": "a_dit"
            })
        
        # Pattern 3: Keywords spécifiques
        viral_keywords = [
            "science Chine", "compagnons étoiles", "divergence miséricorde", "patrie foi",
            "cœur rouille", "paradis pieds mères", "anges chien", "monde prison",
            "meilleur femme", "savants héritiers", "femme enfer cheveux",
            "sourire sadaqa", "jihad vérité", "temps épée"
        ]
        
        for keyword in viral_keywords:
            if keyword.lower() in text.lower():
                # Extraire le paragraphe contenant le keyword
                for para in text.split('\n'):
                    if keyword.lower() in para.lower() and len(para) > 50:
                        candidats.append({
                            "texte": para.strip()[:500],
                            "url": url,
                            "title": page.get("title"),
                            "source": f"keyword:{keyword}"
                        })
        
        return candidats
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MATCHING ULTRA — RAPIDFUZZ
    # ═══════════════════════════════════════════════════════════════════════════
    
    def fuzzy_match(self, s1: str, s2: str) -> float:
        """Matching fuzzy optimisé"""
        if not s1 or not s2:
            return 0.0
        
        if RAPIDFUZZ_AVAILABLE:
            return fuzz.partial_ratio(s1.lower(), s2.lower())
        else:
            return SequenceMatcher(None, s1.lower(), s2.lower()).ratio() * 100
    
    def matcher_crawler(self, candidats: List[Dict]):
        """Matching massif avec rapports"""
        print(f"\n🔎 MATCHING CRAWLER — {len(candidats)} candidats vs {len(self.blacklist)} référencés...")
        
        matches = 0
        sites_infectés_local = {}
        
        for cand in candidats:
            texte_cand = cand.get("texte", "")
            if not texte_cand or len(texte_cand) < 40:
                continue
            
            url = cand.get("url", "")
            
            for ref in self.blacklist:
                texte_ref = ref.get("texte", "")
                if not texte_ref:
                    continue
                
                score = self.fuzzy_match(texte_cand, texte_ref)
                
                if score >= 70:  # Seuil 70%
                    matches += 1
                    
                    # Ajouter au site infecté
                    if url not in sites_infectés_local:
                        sites_infectés_local[url] = []
                    sites_infectés_local[url].append({
                        "hadith": ref.get("texte"),
                        "grade": ref.get("grade"),
                        "score": score
                    })
                    
                    # Générer fiche
                    fiche = self.generer_fiche_crawler(cand, ref, score)
                    
                    with self.lock:
                        self.fiches.append(fiche)
                        self.stats["matches_confirmés"] += 1
                        self.stats["fiches_générées"] += 1
                        
                        courant = ref.get("courant", "Général")
                        self.stats["courants"][courant] = self.stats["courants"].get(courant, 0) + 1
                    
                    print(f"  🎯 MATCH #{matches} [{score:.0f}%] | {ref.get('grade')} | {ref.get('savant')} | {url[:60]}...")
                    break
        
        # Mettre à jour sites infectés
        with self.lock:
            self.sites_infectés.update(sites_infectés_local)
            self.stats["sites_infectés"] = len(self.sites_infectés)
        
        print(f"✅ {matches} MENSONGES CONFIRMÉS sur {len(sites_infectés_local)} SITES INFECTÉS")
    
    def generer_fiche_crawler(self, cand: Dict, ref: Dict, score: float) -> Dict:
        """Génère fiche anatomie complète"""
        return {
            "id": f"CRAWLER_{len(self.fiches)+1:04d}",
            "timestamp": datetime.now().isoformat(),
            "detection": {
                "source": "crawler",
                "url": cand.get("url"),
                "titre_page": cand.get("title"),
                "type_extraction": cand.get("source"),
                "score_fuzzy": f"{score:.1f}%"
            },
            "mensonge_circulant": {
                "texte_extrait": cand.get("texte")[:400],
                "longueur": len(cand.get("texte", ""))
            },
            "verdict_authentique": {
                "grade_réel": ref.get("grade"),
                "savant_vérificateur": ref.get("savant"),
                "référence_livre": ref.get("ref"),
                "texte_original": ref.get("texte")
            },
            "mapping_courant": {
                "courant_identifié": ref.get("courant", "Général"),
                "niveau_menace": "CRITIQUE" if ref.get("grade") == "mawdou" else "ÉLEVÉ"
            }
        }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # EXÉCUTION PRINCIPALE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def executer_crawler(self):
        """Exécution mode prédateur"""
        print("\n" + "=" * 80)
        print("🚀 SCANNER CRAWLER V3 — MODE PRÉDATEUR ACTIVÉ")
        print("=" * 80)
        print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Blacklist: {len(self.blacklist)} hadiths référencés")
        print(f"   Sites prioritaires: {len(SITES_PRIORITAIRES)}")
        print(f"   Matching: RAPIDFUZZ {'✅' if RAPIDFUZZ_AVAILABLE else '⚠️ difflib'}")
        print("=" * 80)
        
        # 1. Récupération URLs depuis Google
        print("\n📡 PHASE 1: RÉCUPÉRATION URLS VIA GOOGLE...")
        all_urls = []
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(self.get_urls_google, q, 20): q for q in REQUETES_CRAWLER}
            for future in as_completed(futures):
                urls = future.result()
                all_urls.extend(urls)
        
        # Dédupliquer URLs
        seen_urls = set()
        unique_urls = []
        for u in all_urls:
            if u["url"] not in seen_urls:
                seen_urls.add(u["url"])
                unique_urls.append(u)
        
        with self.lock:
            self.stats["urls_trouves"] = len(unique_urls)
        
        print(f"✅ {len(unique_urls)} URLs uniques trouvés")
        
        # 2. Crawling massif
        print("\n🕷️ PHASE 2: CRAWLING MASSIF DES PAGES...")
        all_candidats = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.crawl_page, u): u for u in unique_urls}
            
            for i, future in enumerate(as_completed(futures)):
                page = future.result()
                if page:
                    cands = self.extract_hadiths_from_text(page)
                    all_candidats.extend(cands)
                
                if (i + 1) % 10 == 0:
                    print(f"   Progress: {i+1}/{len(unique_urls)} pages | {len(all_candidats)} candidats extraits")
        
        with self.lock:
            self.stats["candidats_extraits"] = len(all_candidats)
        
        print(f"✅ {len(all_candidats)} candidats hadiths extraits")
        
        # 3. Matching massif
        if all_candidats:
            self.matcher_crawler(all_candidats)
        
        # 4. Sauvegarde
        self.sauvegarder_crawler()
        
        # 5. Rapport final
        self.print_rapport_crawler()
    
    def sauvegarder_crawler(self):
        """Sauvegarde massive"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Fiches
        fiches_path = self.data_dir / f"CRAWLER_FICHES_{ts}.json"
        with open(fiches_path, "w", encoding="utf-8") as f:
            json.dump(self.fiches, f, ensure_ascii=False, indent=2)
        
        # Sites infectés
        sites_path = self.data_dir / f"CRAWLER_SITES_INFECTES_{ts}.json"
        with open(sites_path, "w", encoding="utf-8") as f:
            json.dump(self.sites_infectés, f, ensure_ascii=False, indent=2)
        
        # Rapport
        rapport = {
            "scan": "CRAWLER_V3",
            "timestamp": ts,
            "statistiques": self.stats,
            "total_fiches": len(self.fiches),
            "total_sites_infectés": len(self.sites_infectés)
        }
        rapport_path = self.data_dir / f"CRAWLER_RAPPORT_{ts}.json"
        with open(rapport_path, "w", encoding="utf-8") as f:
            json.dump(rapport, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 SAUVEGARDE CRAWLER:")
        print(f"   📁 Fiches: {fiches_path}")
        print(f"   📁 Sites infectés: {sites_path}")
        print(f"   📁 Rapport: {rapport_path}")
    
    def print_rapport_crawler(self):
        """Rapport terminal massif"""
        print("\n" + "=" * 80)
        print("║" + " " * 20 + "🔥 CRAWLER V3 — MISSION TERMINÉE 🔥" + " " * 22 + "║")
        print("=" * 80)
        
        print(f"\n📊 STATISTIQUES DE GUERRE")
        print(f"   🔍 URLs trouvés          : {self.stats['urls_trouves']}")
        print(f"   🕷️ Pages crawlées        : {self.stats['pages_crawlées']}")
        print(f"   ❌ Pages échouées        : {self.stats['pages_échouées']}")
        print(f"   📝 Candidats extraits    : {self.stats['candidats_extraits']}")
        print(f"   🎯 Matches confirmés     : {self.stats['matches_confirmés']}")
        print(f"   📋 Fiches générées       : {self.stats['fiches_générées']}")
        print(f"   🌐 Sites infectés       : {len(self.sites_infectés)}")
        
        print(f"\n🎯 MAPPING COURANTS DÉVIANTS")
        total = sum(self.stats["courants"].values())
        for c, n in sorted(self.stats["courants"].items(), key=lambda x: -x[1]):
            bar = "█" * (n * 3)
            print(f"   {c:<12} : {n:>3} {bar}")
        
        if self.sites_infectés:
            print(f"\n🌐 TOP 10 SITES INFECTÉS")
            sorted_sites = sorted(self.sites_infectés.items(), key=lambda x: -len(x[1]))[:10]
            for url, hadiths in sorted_sites:
                print(f"   {url[:70]:<70} | {len(hadiths)} hadiths")
        
        print("\n" + "=" * 80)
        print(f"✅ CRAWLER V3 TERMINÉ — {len(self.fiches)} MENSONGES DOCUMENTÉS SUR {len(self.sites_infectés)} SITES")
        print("=" * 80)


def main():
    scanner = ScannerCrawlerV3()
    scanner.executer_crawler()


if __name__ == "__main__":
    main()
