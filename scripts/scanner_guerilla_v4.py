#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCANNER GUÉRILLA V4 — MODE TERMINATOR 🔥🔥🔥
Extraction massive sans merci — Seuil 45% — Keywords full power
"""

import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse
from difflib import SequenceMatcher

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
# BLACKLIST ULTRA-COMPLÈTE — 60+ HADITHS
# ═══════════════════════════════════════════════════════════════════════════════

BLACKLIST_GUERILLA = [
    # === HADITHS MAWDOU (INVENTÉS) — Priorité CRITIQUE ===
    {"id": 1, "texte": "Cherche la science même en Chine", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 416", "courant": "Général", "keywords": ["science", "chine", "étudier", "apprendre"]},
    {"id": 2, "texte": "Mes compagnons sont comme des étoiles", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 144", "courant": "Ikhwānī", "keywords": ["compagnons", "étoiles", "suivre", "étoile"]},
    {"id": 3, "texte": "La divergence de ma communauté est une miséricorde", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 57", "courant": "Ikhwānī", "keywords": ["divergence", "différence", "miséricorde", "communauté"]},
    {"id": 4, "texte": "L'amour de la patrie fait partie de la foi", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 36", "courant": "Ikhwānī", "keywords": ["patrie", "nation", "pays", "foi", "amour"]},
    {"id": 5, "texte": "Travaillez pour votre vie comme si vous viviez éternellement", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 8", "courant": "Général", "keywords": ["travailler", "vie", "éternel", "akhira"]},
    {"id": 6, "texte": "Soyez optimistes vous trouverez le bien", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 829", "courant": "Général", "keywords": ["optimiste", "bien", "positif", "trouver"]},
    {"id": 7, "texte": "Le Prophète a pleuré pour les morts de sa communauté", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 182", "courant": "Soufi", "keywords": ["pleurer", "morts", "larmes", "pleuré"]},
    {"id": 8, "texte": "La meilleure dhikr est celle faite en secret", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Soufi", "keywords": ["dhikr", "secret", "silencieux", "meilleure"]},
    {"id": 9, "texte": "Le Prophète a dit au Companion qui voulait tuer un serpent", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["serpent", "tuer", "compagnon"]},
    {"id": 10, "texte": "Les trois choses qui ne sont pas sérieuses", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["sérieux", "chasse", "jeu", "femme"]},
    {"id": 11, "texte": "Ne voyagez pas seul car Satan sera votre compagnon", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["voyage", "seul", "satan", "compagnon"]},
    {"id": 12, "texte": "La meilleure des femmes ne voit pas les hommes", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["femme", "meilleure", "hommes", "voir"]},
    {"id": 13, "texte": "Quand un mari regarde sa femme avec amour", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["mari", "femme", "amour", "regarder"]},
    {"id": 14, "texte": "Le mariage est la moitié de la foi", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["mariage", "moitié", "foi", "religion"]},
    {"id": 15, "texte": "Le paradis est aux pieds des mères", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["paradis", "pieds", "mère", "mères"]},
    {"id": 16, "texte": "Le temps est une épée", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["temps", "épée", "coupe"]},
    {"id": 17, "texte": "Quand Allah aime un serviteur il l'afflige", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["aime", "affliger", "souffrance", "serviteur"]},
    {"id": 18, "texte": "La science sans pratique est comme un arbre sans fruit", "grade": "mawdou", "savant": "Ibn Hajar", "ref": "", "courant": "Soufi", "keywords": ["science", "pratique", "arbre", "fruit"]},
    {"id": 19, "texte": "Quand tu as un appel à faire à Allah fais-le", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["appel", "demande", "Allah", "fais-le"]},
    {"id": 20, "texte": "Le Prophète a interdit de fumer", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["fumer", "cigarette", "tabac", "interdit"]},
    {"id": 21, "texte": "La femme en Enfer suspendue par les cheveux", "grade": "mawdou", "savant": "Ibn Bāz", "ref": "FT 19493", "courant": "Général", "keywords": ["femme", "enfer", "cheveux", "suspendue"]},
    {"id": 22, "texte": "Qui me voit a vu Allah", "grade": "mawdou", "savant": "Ibn Bāz", "ref": "FT", "courant": "Soufi", "keywords": ["voir", "Allah", "prophète", "vu"]},
    {"id": 23, "texte": "Le Prophète aurait embrassé les mains de Abu Bakr", "grade": "mawdou", "savant": "Multiple", "ref": "", "courant": "Ash'arī", "keywords": ["Abu Bakr", "embrasser", "mains"]},
    {"id": 24, "texte": "La bonté vers parents est jihad", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["parents", "bonté", "jihad", "bienfaisance"]},
    {"id": 25, "texte": "Celui qui ne se soucie pas des affaires des musulmans", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 480", "courant": "Ikhwānī", "keywords": ["soucier", "affaires", "musulmans", "partie"]},
    
    # === HADITHS DAIF (FAIBLES) ===
    {"id": 26, "texte": "Le cœur rouille comme le fer", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["cœur", "rouille", "fer", "dhikr"]},
    {"id": 27, "texte": "Quand vous priez ne regardez ni à droite", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["prière", "regarder", "droite", "gauche"]},
    {"id": 28, "texte": "Ne dormez pas sur le ventre", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["dormir", "ventre", "position", "enfer"]},
    {"id": 29, "texte": "Le calme est de Allah", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["calme", "Allah", "hâte", "diable"]},
    {"id": 30, "texte": "Le pauvre entre au paradis avant le riche", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["pauvre", "paradis", "riche", "entrer"]},
    {"id": 31, "texte": "Les savants sont les héritiers des prophètes", "grade": "daif", "savant": "al-Albānī", "ref": "SD 629", "courant": "Ash'arī", "keywords": ["savants", "héritiers", "prophètes", "science"]},
    {"id": 32, "texte": "Visitez les tombes", "grade": "daif", "savant": "al-Albānī", "ref": "SD 50", "courant": "Soufi", "keywords": ["tombe", "cimetière", "visiter", "mort"]},
    
    # === HADITHS SAHEEH (AUTENTIQUES — Pour comparaison) ===
    {"id": 33, "texte": "Le monde est la prison du croyant", "grade": "saheeh", "savant": "Muslim", "ref": "", "courant": "Salafī", "keywords": ["monde", "prison", "croyant", "paradis"]},
    {"id": 34, "texte": "Le croyant est le miroir de son frère", "grade": "saheeh", "savant": "Abu Dawud", "ref": "", "courant": "Général", "keywords": ["miroir", "frère", "croyant", "musulman"]},
    {"id": 35, "texte": "Le sourire envers ton frère est une sadaqa", "grade": "saheeh", "savant": "Tirmidhi", "ref": "", "courant": "Général", "keywords": ["sourire", "frère", "sadaqa", "charité"]},
    {"id": 36, "texte": "Le meilleur jihad parler une parole de justice", "grade": "saheeh", "savant": "Abu Dawud", "ref": "", "courant": "Salafī", "keywords": ["jihad", "justice", "parole", "tyran"]},
    {"id": 37, "texte": "Le paradis est sous l'ombre des épées", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī", "keywords": ["paradis", "ombre", "épées", "jihad"]},
    {"id": 38, "texte": "Une femme ne doit pas voyager sans mahram", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī", "keywords": ["femme", "voyage", "mahram", "jour"]},
    {"id": 39, "texte": "Les anges ne entrent pas dans une maison avec un chien", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī", "keywords": ["anges", "chien", "maison", "image"]},
    {"id": 40, "texte": "Le Prophète a interdit de manger avec la main gauche", "grade": "saheeh", "savant": "Muslim", "ref": "", "courant": "Salafī", "keywords": ["manger", "gauche", "main", "shaytan"]},
    {"id": 41, "texte": "Le rêve du croyant est vrai", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Général", "keywords": ["rêve", "croyant", "vérité", "étonnant"]},
    {"id": 42, "texte": "Manger avec trois doigts", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī", "keywords": ["manger", "doigts", "trois", "main"]},
    {"id": 43, "texte": "Boire en trois respirations", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī", "keywords": ["boire", "trois", "respiration", "gorgées"]},
    {"id": 44, "texte": "Le riba a 70 portes", "grade": "saheeh", "savant": "Ibn Majah", "ref": "", "courant": "Salafī", "keywords": ["riba", "intérêt", "70", "portes"]},
]

# ═══════════════════════════════════════════════════════════════════════════════
# SCANNER GUÉRILLA V4
# ═══════════════════════════════════════════════════════════════════════════════

class ScannerGuerillaV4:
    """Scanner mode terminator — Aucune pitié"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        self.stats = {
            "pages_scan": 0, "hadiths_extraits": 0,
            "mawdou": 0, "daif": 0, "saheeh": 0,
            "matches": 0, "fiches": 0,
            "courants": {}
        }
        
        self.fiches = []
        self.lock = threading.Lock()
        self.blacklist = BLACKLIST_GUERILLA
    
    def extract_all_hadiths(self, text: str, url: str) -> List[Dict]:
        """Extraction TOTALE — Tout ce qui ressemble à un hadith"""
        candidats = []
        
        # Pattern 1: Guillemets avec mots clés religieux
        for match in re.findall(r'[«"\']([^«"\']{30,800}?)[»"\']', text):
            if any(kw in match.lower() for kw in ["prophète", "messager", "allah", "islam", "prière", "coran", "paradis", "enfer"]):
                candidats.append({"texte": match, "url": url, "source": "guillemets"})
        
        # Pattern 2: Phrases avec "a dit" et Prophète
        for match in re.findall(r'(?:le |L\')(?:Prophète|Messager)[^.]{0,300}a dit[^.]{0,100}([^\n.]{50,600})', text, re.IGNORECASE):
            candidats.append({"texte": match, "url": url, "source": "a_dit"})
        
        # Pattern 3: Paragraphes avec keywords hadiths viraux
        for para in text.split('\n'):
            para = para.strip()
            if len(para) < 80:
                continue
            
            viral_keywords = [
                "science chine", "compagnons étoiles", "divergence", "patrie", "cœur rouille",
                "paradis mères", "anges chien", "monde prison", "miroir frère", "sourire sadaqa",
                "jihad justice", "ombre épées", "femme voyage", "manger gauche", "rêve croyant",
                "meilleur femme", "savants héritiers", "femme enfer", "mariage moitié", "temps épée",
                "afflige aime", "science pratique", "appel allah", "fumer interdit", "embrasser mains",
                "parents jihad", "dormir ventre", "prière regarder", "pauvre paradis", "calme allah",
                "dhikr secret", "serpent tuer", "trois choses", "voyage seul", "satan compagnon"
            ]
            
            for kw in viral_keywords:
                if kw in para.lower():
                    candidats.append({"texte": para[:800], "url": url, "source": f"keyword:{kw}"})
                    break
        
        return candidats
    
    def fuzzy_score(self, s1: str, s2: str) -> float:
        """Score de similarité"""
        if not s1 or not s2:
            return 0.0
        if RAPIDFUZZ_AVAILABLE:
            return fuzz.partial_ratio(s1.lower(), s2.lower())
        return SequenceMatcher(None, s1.lower(), s2.lower()).ratio() * 100
    
    def match_keywords(self, text: str, ref: Dict) -> bool:
        """Matching par keywords"""
        text_lower = text.lower()
        keywords = ref.get("keywords", [])
        
        matches = sum(1 for kw in keywords if kw in text_lower)
        return matches >= 2  # Au moins 2 keywords
    
    def matcher_guerilla(self, candidats: List[Dict]):
        """Matching ultra-agressif — Seuil 45%"""
        print(f"\n🔥 MATCHING GUÉRILLA — {len(candidats)} candidats vs {len(self.blacklist)} référencés...")
        print("   Seuil: 45% | Keywords: 2+ | Mode: TERMINATOR")
        
        matches = 0
        seen = set()
        
        for cand in candidats:
            texte = cand.get("texte", "")
            if not texte or len(texte) < 40:
                continue
            
            text_hash = hash(texte[:80])
            if text_hash in seen:
                continue
            seen.add(text_hash)
            
            with self.lock:
                self.stats["hadiths_extraits"] += 1
            
            for ref in self.blacklist:
                # Matching fuzzy
                score = self.fuzzy_score(texte, ref.get("texte", ""))
                
                # Matching keywords
                keyword_match = self.match_keywords(texte, ref)
                
                # Seuil: 45% OU 2+ keywords
                if score >= 45 or keyword_match:
                    matches += 1
                    grade = ref.get("grade", "")
                    
                    with self.lock:
                        if "mawdou" in grade:
                            self.stats["mawdou"] += 1
                        elif "daif" in grade:
                            self.stats["daif"] += 1
                        elif "saheeh" in grade:
                            self.stats["saheeh"] += 1
                        self.stats["matches"] += 1
                    
                    fiche = {
                        "id": f"GUERILLA_{len(self.fiches)+1:04d}",
                        "timestamp": datetime.now().isoformat(),
                        "url": cand.get("url"),
                        "hadith_detecte": texte[:400],
                        "grade_reel": grade,
                        "savant": ref.get("savant"),
                        "reference": ref.get("ref"),
                        "score": f"{score:.0f}%",
                        "keywords_match": keyword_match,
                        "courant": ref.get("courant"),
                        "menace": "🔴 CRITIQUE" if "mawdou" in grade else "🟠 ÉLEVÉE" if "daif" in grade else "🟢 VÉRIFIÉ"
                    }
                    
                    with self.lock:
                        self.fiches.append(fiche)
                        self.stats["fiches"] += 1
                    
                    emoji = "🔴" if "mawdou" in grade else "🟠" if "daif" in grade else "🟢"
                    print(f"  {emoji} #{matches} [{score:.0f}%] {grade} | {ref.get('savant')} | {cand.get('url', '')[:50]}...")
                    break
        
        print(f"\n✅ {matches} MENSONGES CONFIRMÉS")
    
    def simuler_scan_massif(self):
        """Simulation avec données réalistes (pour démonstration)"""
        print("\n🔥 SIMULATION MODE GUÉRILLA — Injection données test...")
        
        # Simuler des candidats trouvés sur le web
        candidats_simules = [
            {
                "texte": "Le Prophète a dit: Cherche la science même en Chine, car la science est la vie du cœur et la lumière des yeux",
                "url": "https://islamweb.net/fr/hadith-science",
                "source": "simulation"
            },
            {
                "texte": "Mes compagnons sont comme des étoiles, suivez n'importe lequel d'entre eux et vous serez guidés",
                "url": "https://islamhouse.com/fr/companions",
                "source": "simulation"
            },
            {
                "texte": "La divergence de ma communauté est une miséricorde, c'est pourquoi nous devons respecter toutes les écoles",
                "url": "https://fr.islamway.net/divergence",
                "source": "simulation"
            },
            {
                "texte": "Le Prophète a dit: Le monde est la prison du croyant et le paradis du mécréant. Ne vous attachez pas à ce monde",
                "url": "https://sounnah.com/dunya",
                "source": "simulation"
            },
            {
                "texte": "L'amour de la patrie fait partie de la foi, celui qui meurt pour sa patrie meurt en martyr",
                "url": "https://ounous.com/patrie",
                "source": "simulation"
            },
            {
                "texte": "Le Prophète a dit: Soyez optimistes en cette vie, car Allah aime les cœurs optimistes",
                "url": "https://lesbeauxproverbes.com/optimisme",
                "source": "simulation"
            },
            {
                "texte": "Le croyant est le miroir de son frère croyant, quand il le voit en défaut il le corrige",
                "url": "https://rappelislam.com/miroir",
                "source": "simulation"
            },
            {
                "texte": "Le Prophète a dit: Le sourire envers ton frère musulman est une sadaqa pour toi",
                "url": "https://islamic-relief.org/fr/sourire",
                "source": "simulation"
            },
            {
                "texte": "Les savants sont les héritiers des prophètes, ils ont hérité leur science et leur lumière",
                "url": "https://salafy.fr/savants",
                "source": "simulation"
            },
            {
                "texte": "Le Prophète a dit: Visitez les tombes car elles vous rappellent la vie après la mort",
                "url": "https://islam.com/tombes",
                "source": "simulation"
            },
            {
                "texte": "Quand Allah aime un serviteur, Il l'afflige. Si tu souffres c'est que Allah t'aime",
                "url": "https://muslimlife.fr/souffrance",
                "source": "simulation"
            },
            {
                "texte": "La science sans pratique est comme un arbre sans fruit, inutile et morte",
                "url": "https://islamreligion.com/science",
                "source": "simulation"
            },
            {
                "texte": "Le meilleur jihad c'est dire une parole de justice devant un tyran injuste",
                "url": "https://islamonline.net/jihad",
                "source": "simulation"
            },
            {
                "texte": "Le Prophète a interdit de fumer car c'est une saleté et une dépense inutile",
                "url": "https://al-kanz.org/fumer",
                "source": "simulation"
            },
            {
                "texte": "Le mariage est la moitié de la foi, c'est pourquoi tout jeune doit se marier vite",
                "url": "https://hadiths.fr/mariage",
                "source": "simulation"
            },
            {
                "texte": "Le paradis est aux pieds des mères, servez vos mères pour entrer au paradis",
                "url": "https://hadithdujour.fr/meres",
                "source": "simulation"
            },
            {
                "texte": "Le cœur rouille comme le fer rouille, et le dhikr est son polissage",
                "url": "https://forum-islam.com/coeur",
                "source": "simulation"
            },
            {
                "texte": "Le temps est une épée tranchante, si tu ne la tranches elle te tranchera",
                "url": "https://discuter-islam.com/temps",
                "source": "simulation"
            },
            {
                "texte": "Le rêve du croyant est étonnant, c'est une partie de la prophétie",
                "url": "https://islam-guide.com/reve",
                "source": "simulation"
            },
            {
                "texte": "La meilleure des femmes est celle qui ne voit pas les hommes et que les hommes ne voient pas",
                "url": "https://dailyhadith.net/femme",
                "source": "simulation"
            },
            {
                "texte": "Le Prophète a dit: Ne voyagez pas seul car Satan sera votre compagnon de voyage",
                "url": "https://sounnah.com/voyage",
                "source": "simulation"
            },
            {
                "texte": "Quand un mari regarde sa femme avec amour et qu'elle lui rend son regard, Allah les regarde avec amour",
                "url": "https://islamfrance.com/regard",
                "source": "simulation"
            },
            {
                "texte": "Le Prophète a dit: Celui qui ne se soucie pas des affaires des musulmans n'en fait pas partie",
                "url": "https://sounnahfrance.com/musulmans",
                "source": "simulation"
            },
        ]
        
        with self.lock:
            self.stats["pages_scan"] = 25
        
        return candidats_simules
    
    def executer_guerilla(self):
        """Exécution mode terminator"""
        print("\n" + "=" * 80)
        print("🚀 SCANNER GUÉRILLA V4 — MODE TERMINATOR 🔥🔥🔥")
        print("=" * 80)
        print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Blacklist: {len(self.blacklist)} hadiths")
        print(f"   RapidFuzz: {'✅' if RAPIDFUZZ_AVAILABLE else '❌'}")
        print(f"   Seuil: 45% | Keywords: 2+")
        print("=" * 80)
        
        # Simulation (en attendant vrai crawling)
        candidats = self.simuler_scan_massif()
        
        # Matching
        self.matcher_guerilla(candidats)
        
        # Sauvegarde
        self.sauvegarder_guerilla()
        
        # Rapport
        self.print_rapport_guerilla()
    
    def sauvegarder_guerilla(self):
        """Sauvegarde massive"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        fiches_path = self.data_dir / f"GUERILLA_FICHES_{ts}.json"
        with open(fiches_path, "w", encoding="utf-8") as f:
            json.dump(self.fiches, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 SAUVEGARDE:")
        print(f"   📁 Fiches: {fiches_path}")
    
    def print_rapport_guerilla(self):
        """Rapport terminal massif"""
        print("\n" + "=" * 80)
        print("║" + " " * 25 + "🔥 GUÉRILLA TERMINÉE 🔥" + " " * 25 + "║")
        print("=" * 80)
        
        print(f"\n📊 STATISTIQUES DE GUERRE")
        print(f"   📄 Pages scannées       : {self.stats['pages_scan']}")
        print(f"   📝 Hadiths extraits     : {self.stats['hadiths_extraits']}")
        print(f"   🎯 Matches confirmés   : {self.stats['matches']}")
        print(f"   📋 Fiches générées      : {self.stats['fiches']}")
        
        print(f"\n🎯 RÉPARTITION PAR GRADE")
        print(f"   🔴 MAWDOU (Inventés)    : {self.stats['mawdou']}")
        print(f"   🟠 DAIF (Faibles)        : {self.stats['daif']}")
        print(f"   🟢 SAHEEH (Authentiques): {self.stats['saheeh']}")
        
        if self.fiches:
            print(f"\n📋 TOP 10 MENSONGES DÉTECTÉS")
            for fiche in self.fiches[:10]:
                grade = fiche.get("grade_reel", "")
                emoji = "🔴" if "mawdou" in grade else "🟠" if "daif" in grade else "🟢"
                url = urlparse(fiche.get("url", "")).netloc
                print(f"   {emoji} [{fiche.get('score', 'N/A')}] {grade} | {fiche.get('savant')} | {url}")
        
        print("\n" + "=" * 80)
        print(f"✅ GUÉRILLA TERMINÉE — {len(self.fiches)} MENSONGES DOCUMENTÉS")
        print("=" * 80)


def main():
    scanner = ScannerGuerillaV4()
    scanner.executer_guerilla()


if __name__ == "__main__":
    main()
