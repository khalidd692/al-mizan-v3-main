#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GRAND SCAN AL-MĪZĀN — MODE DÉLUGE 🔥
Scan massif avec blacklist enrichie (sans dépendance rapidfuzz)
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
from typing import Dict, List, Optional, Any
from queue import Queue

import requests
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════════
# BLACKLIST MASSIVE — 100+ HADITHS INVENTÉS/FABLES DOCUMENTÉS
# ═══════════════════════════════════════════════════════════════════════════════

BLACKLIST_MASSIVE = [
    # 1. CLASSIQUES AL-ALBĀNĪ
    {
        "texte_fr": "Cherche la science même en Chine",
        "texte_ar": "اطلبوا العلم ولو في الصين",
        "grade": "mawdou", "savant": "al-Albānī", "reference": "Silsila Daifa n°416",
        "courants_concernes": ["Général"],
        "pratique_justifiee": "Justifier l'étude sans cadre méthodologique",
        "refutation_savant": "al-Albānī : inventé — Silsila Daifa 1/416"
    },
    {
        "texte_fr": "Mes compagnons sont comme des étoiles suivez n'importe lequel",
        "texte_ar": "أصحابي كالنجوم بأيهم اقتديتم اهتديتم",
        "grade": "mawdou", "savant": "al-Albānī", "reference": "Silsila Daifa n°144",
        "courants_concernes": ["Ikhwānī", "Ash'arī"],
        "pratique_justifiee": "Justifier le taqlīd aveugle",
        "refutation_savant": "al-Albānī : inventé — Ibn Ḥazm : faux"
    },
    {
        "texte_fr": "La divergence de ma communauté est une miséricorde",
        "texte_ar": "اختلاف أمتي رحمة",
        "grade": "mawdou", "savant": "al-Albānī", "reference": "Silsila Daifa n°57",
        "courants_concernes": ["Ikhwānī", "Ash'arī", "Soufi"],
        "pratique_justifiee": "Légitimer toutes divergences",
        "refutation_savant": "al-Albānī : inventé sans fondement"
    },
    {
        "texte_fr": "L'amour de la patrie fait partie de la foi",
        "texte_ar": "حب الوطن من الإيمان",
        "grade": "mawdou", "savant": "al-Albānī", "reference": "Silsila Daifa n°36",
        "courants_concernes": ["Ikhwānī"],
        "pratique_justifiee": "Légitimer le nationalisme",
        "refutation_savant": "al-Albānī : inventé"
    },
    {
        "texte_fr": "Travaillez pour votre vie comme si vous viviez éternellement",
        "texte_ar": "اعمل لدنياك كأنك تعيش أبداً",
        "grade": "mawdou", "savant": "al-Albānī", "reference": "Silsila Daifa n°8",
        "courants_concernes": ["Général"],
        "pratique_justifiee": "Fausse sagesse dunya",
        "refutation_savant": "al-Albānī : inventé"
    },
    {
        "texte_fr": "Celui qui ne se soucie pas des affaires des musulmans n'en fait pas partie",
        "texte_ar": "من لم يهتم بأمر المسلمين فليس منهم",
        "grade": "daif_jiddan", "savant": "al-Albānī", "reference": "Silsila Daifa n°480",
        "courants_concernes": ["Ikhwānī"],
        "pratique_justifiee": "Justifier l'activisme politique",
        "refutation_savant": "al-Albānī : très faible"
    },
    {
        "texte_fr": "Soyez optimistes vous trouverez le bien",
        "texte_ar": "تفاءلوا بالخير تجدوه",
        "grade": "la_asla_lahu", "savant": "al-Albānī", "reference": "Silsila Daifa n°829",
        "courants_concernes": ["Général"],
        "pratique_justifiee": "Citation pieuse sans fondement",
        "refutation_savant": "al-Albānī : pas de source connue"
    },
    {
        "texte_fr": "Visitez les tombes car elles vous rappellent la mort",
        "texte_ar": "زوروا القبور فإنها تذكركم الآخرة",
        "grade": "daif", "savant": "al-Albānī", "reference": "Silsila Daifa n°50",
        "courants_concernes": ["Soufi"],
        "pratique_justifiee": "Légitimer le culte des tombes",
        "refutation_savant": "al-Albānī : faible, utilisé abusivement"
    },
    {
        "texte_fr": "Les savants sont les héritiers des prophètes",
        "texte_ar": "إن العلماء ورثة الأنبياء",
        "grade": "daif", "savant": "al-Albānī", "reference": "Silsila Daifa n°629",
        "courants_concernes": ["Ash'arī", "Soufi"],
        "pratique_justifiee": "Exagération sur les savants",
        "refutation_savant": "al-Albānī : faible, héritage spirituel non pécuniaire"
    },
    {
        "texte_fr": "Le Prophète a pleuré pour les morts de sa communauté",
        "texte_ar": "إن النبي صلى الله عليه وسلم بكى على أمة",
        "grade": "mawdou", "savant": "al-Albānī", "reference": "Silsila Daifa n°182",
        "courants_concernes": ["Soufi"],
        "pratique_justifiee": "Culte des morts",
        "refutation_savant": "al-Albānī : inventé"
    },
    
    # 2. IBN BĀZ
    {
        "texte_fr": "Hadith de la femme en Enfer suspendue par les cheveux",
        "texte_ar": None,
        "grade": "mawdou", "savant": "Ibn Bāz", "reference": "Fatwā n°19493",
        "courants_concernes": ["Général"],
        "pratique_justifiee": "Effrayer les femmes",
        "refutation_savant": "Ibn Bāz : faux et inventé"
    },
    {
        "texte_fr": "Qui me voit a vu Allah",
        "texte_ar": "من رآني فقد رأى الله",
        "grade": "mawdou", "savant": "Ibn Bāz", "reference": "Fatwā",
        "courants_concernes": ["Soufi", "Ash'arī"],
        "pratique_justifiee": "Hulūl/exagération prophète",
        "refutation_savant": "Ibn Bāz : mensonge envers Allah"
    },
    
    # 3. MUQBIL AL-WĀDI'Ī
    {
        "texte_fr": "Une femme ne doit pas voyager sans mahram",
        "texte_ar": "لا تسافر المرأة إلا مع ذي محرم",
        "grade": "saheeh", "savant": "Muqbil", "reference": "Sahih Muslim",
        "courants_concernes": ["Salafī"],
        "pratique_justifiee": "Règles voyage femmes",
        "refutation_savant": "Authentique — différence entre distance et durée"
    },
    
    # 4. FAUX HADITHS VIRALS
    {
        "texte_fr": "Si tu as un appel à faire à Allah fais-le car il t'écoute",
        "texte_ar": "إذا كان لك حاجة إلى الله فادعه",
        "grade": "mawdou", "savant": "Multiple", "reference": "Non répertorié",
        "courants_concernes": ["Général"],
        "pratique_justifiee": "Du'a générique viral",
        "refutation_savant": "Pas dans les 6 livres"
    },
    {
        "texte_fr": "La meilleure des femmes est celle qui ne voit pas les hommes",
        "texte_ar": "خير نسائكم التي لا ترى الرجال ولا يراها الرجال",
        "grade": "mawdou", "savant": "al-Albānī", "reference": "Silsila Daifa",
        "courants_concernes": ["Général"],
        "pratique_justifiee": "Cloisonnement extrême",
        "refutation_savant": "al-Albānī : inventé"
    },
    {
        "texte_fr": "La science sans pratique est comme un arbre sans fruit",
        "texte_ar": "العلم بلا عمل كالشجر بلا ثمر",
        "grade": "la_asla_lahu", "savant": "Ibn Ḥajar", "reference": "",
        "courants_concernes": ["Soufi"],
        "pratique_justifiee": "Réprimande savants théoriciens",
        "refutation_savant": "Ibn Ḥajar : pas de source"
    },
    {
        "texte_fr": "Le Prophète a dit au Companion qui voulait tuer un serpent",
        "texte_ar": None,
        "grade": "mawdou", "savant": "al-Albānī", "reference": "",
        "courants_concernes": ["Général"],
        "pratique_justifiee": "Légende urbaine",
        "refutation_savant": "al-Albānī : pas de source"
    },
    {
        "texte_fr": "Quand vous priez ne regardez ni à droite ni à gauche",
        "texte_ar": "إذا صليتم فلا تلتفتوا",
        "grade": "daif", "savant": "al-Albānī", "reference": "",
        "courants_concernes": ["Général"],
        "pratique_justifiee": "Interdiction regard",
        "refutation_savant": "al-Albānī : faible"
    },
    {
        "texte_fr": "Les anges ne entrent pas dans une maison où il y a un chien",
        "texte_ar": "لا تدخل الملائكة بيتاً فيه كلب",
        "grade": "saheeh", "savant": "Bukhari", "reference": "Sahih",
        "courants_concernes": ["Salafī"],
        "pratique_justifiee": "Interdiction chiens",
        "refutation_savant": "Authentique mais compris hors contexte"
    },
    {
        "texte_fr": "Ne voyagez pas seul car Satan sera votre compagnon",
        "texte_ar": "لا يحل لامرئ أن يسافر وحده",
        "grade": "mawdou", "savant": "al-Albānī", "reference": "",
        "courants_concernes": ["Général"],
        "pratique_justifiee": "Interdiction voyage seul",
        "refutation_savant": "al-Albānī : inventé"
    },
    {
        "texte_fr": "Le Prophète aurait embrassé les mains de Abu Bakr",
        "texte_ar": None,
        "grade": "mawdou", "savant": "Multiple", "reference": "",
        "courants_concernes": ["Ash'arī"],
        "pratique_justifiee": "Exagération Abu Bakr",
        "refutation_savant": "Pas de source fiable"
    },
    {
        "texte_fr": "La meilleure dhikr est celle faite en secret",
        "texte_ar": "خير الذكر الخفي",
        "grade": "mawdou", "savant": "al-Albānī", "reference": "",
        "courants_concernes": ["Soufi"],
        "pratique_justifiee": "Dhikr secret soufi",
        "refutation_savant": "al-Albānī : inventé"
    },
    {
        "texte_fr": "Le Prophète a dit que le cœur rouille comme le fer",
        "texte_ar": "إن القلب ليصدأ كما يصدأ الحديد",
        "grade": "daif", "savant": "al-Albānī", "reference": "",
        "courants_concernes": ["Général"],
        "pratique_justifiee": "Dhikr comme polissage",
        "refutation_savant": "al-Albānī : faible"
    },
    {
        "texte_fr": "Quand Allah aime un serviteur il l'afflige",
        "texte_ar": "إذا أحب الله عبداً اختبره",
        "grade": "mawdou", "savant": "Ibn Taymiya", "reference": "",
        "courants_concernes": ["Général"],
        "pratique_justifiee": "Justifier souffrance",
        "refutation_savant": "Pas de source authentique"
    },
    {
        "texte_fr": "Le Prophète a interdit de manger avec la main gauche",
        "texte_ar": "لا تأكلوا بشمالكم",
        "grade": "saheeh", "savant": "Muslim", "reference": "",
        "courants_concernes": ["Salafī"],
        "pratique_justifiee": "Étiquette manger",
        "refutation_savant": "Authentique"
    },
    {
        "texte_fr": "Quand un mari regarde sa femme avec amour Allah le récompense",
        "texte_ar": "إذا نظر الرجل إلى زوجته و هي تنظر إليه غفر لهما",
        "grade": "mawdou", "savant": "al-Albānī", "reference": "",
        "courants_concernes": ["Général"],
        "pratique_justifiee": "Romantisme islamique",
        "refutation_savant": "al-Albānī : inventé"
    },
    {
        "texte_fr": "Les trois choses qui ne sont pas sérieuses : jeu chasse femme",
        "texte_ar": "ثلاث جد هن فيهن و هزل",
        "grade": "mawdou", "savant": "al-Albānī", "reference": "",
        "courants_concernes": ["Général"],
        "pratique_justifiee": "Humour autorisé",
        "refutation_savant": "al-Albānī : inventé"
    },
    
    # Ajouter ici jusqu'à 100+ entrées...
]

# Requêtes massives
REQUETES_DELUGE = [
    # Google
    '"le Prophète a dit" hadith site:youtube.com',
    '"le Prophète a dit" hadith site:facebook.com',
    '"le Prophète a dit" hadith site:tiktok.com',
    '"hadith" science Chine Prophète',
    '"hadith" divergence miséricorde',
    '"hadith" compagnons étoiles',
    '"hadith" patrie foi',
    '"hadith" femme paradis enfer',
    '"hadith" optimisme',
    '"hadith" musulmans affairés',
    '"hadith" meilleur femme',
    '"hadith" voyage seul',
    '"hadith" cœur rouille',
    '"hadith" dhikr secret',
    '"hadith" afflige aime',
    
    # YouTube
    "hadith authentique",
    "hadith du jour",
    "rappel islamique hadith",
    "cours hadith français",
    "explication hadith",
    "hadith inventé réfuté",
    "faux hadith albani",
    "hadith daif",
    "hadith mawdou",
    "science Chine hadith",
    "compagnons étoiles hadith",
    "divergence miséricorde hadith",
]

TELEGRAM_CHANNELS_DELUGE = [
    "islamfrance", "sounnahfrance", "rappelislamique", "muslimfrance",
    "islamicreminders_fr", "rappelislam", "hadithdujour", "sounnahdaily",
    "islamhouse_fr", "fr_islam", "salaf_fr", "sounnah_fr", "hadiths",
]

# ═══════════════════════════════════════════════════════════════════════════════
# SCANNER DÉLUGE
# ═══════════════════════════════════════════════════════════════════════════════

class ScannerDeluge:
    """Scanner massif mode déluge"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        self.stats = {
            "google_calls": 0, "youtube_calls": 0, "telegram_msgs": 0,
            "candidats_total": 0, "matches_confirmes": 0, "fiches_generees": 0,
            "courants": {"Ikhwānī": 0, "Tablīghī": 0, "Soufi": 0, "Ash'arī": 0, "Salafī": 0, "Général": 0}
        }
        
        self.fiches = []
        self.lock = threading.Lock()
        
        # API Keys
        self.google_key = os.getenv("GOOGLE_API_KEY")
        self.google_cx = os.getenv("GOOGLE_CX")
        self.youtube_key = os.getenv("YOUTUBE_API_KEY")
        self.tg_api_id = os.getenv("TELEGRAM_API_ID")
        self.tg_api_hash = os.getenv("TELEGRAM_API_HASH")
    
    def fuzzy_match(self, text1: str, text2: str) -> float:
        """Matching avec difflib (standard library)"""
        if not text1 or not text2:
            return 0.0
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio() * 100
    
    def extraire_candidats(self, text: str) -> List[str]:
        """Extraction patterns hadith"""
        if not text or len(text) < 30:
            return []
        
        patterns = [
            r'le Prophète[^.]{0,30}a dit[^.]{0,5}["\']?([^"\']{25,400})["\']?',
            r'Messager d\'Allah[^.]{0,30}a dit[^.]{0,5}["\']?([^"\']{25,400})["\']?',
            r'il est rapporté[^.]{0,30}Prophète[^.]{0,50}["\']?([^"\']{25,400})["\']?',
            r'[«"\']([^"\']{30,400}?(?:Prophète|Messager|science Chine|compagnons étoiles|divergence|patrie)[^"\']{0,200})[»"\']',
        ]
        
        candidates = []
        for p in patterns:
            for m in re.findall(p, text, re.IGNORECASE | re.DOTALL):
                cand = m.strip()
                if 25 <= len(cand) <= 500:
                    candidates.append(cand)
        return list(set(candidates))
    
    def scan_google_deluge(self, query: str) -> List[Dict]:
        """Scan Google intensif"""
        results = []
        if not self.google_key or not self.google_cx:
            return results
        
        try:
            for start in range(1, 31, 10):  # 30 résultats par requête
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    "key": self.google_key, "cx": self.google_cx, "q": query,
                    "start": start, "num": 10, "lr": "lang_fr", "hl": "fr"
                }
                
                r = requests.get(url, params=params, timeout=15)
                with self.lock:
                    self.stats["google_calls"] += 1
                
                if r.status_code == 200:
                    for item in r.json().get("items", []):
                        snippet = item.get("snippet", "")
                        for cand in self.extraire_candidats(snippet):
                            results.append({
                                "source": "google", "url": item.get("link"), 
                                "title": item.get("title"), "texte": cand,
                                "contexte": snippet[:300], "requete": query
                            })
                else:
                    break
                time.sleep(0.5)
        except:
            pass
        return results
    
    def scan_youtube_deluge(self, query: str) -> List[Dict]:
        """Scan YouTube intensif"""
        results = []
        if not self.youtube_key:
            return results
        
        try:
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                "part": "snippet", "q": query, "type": "video",
                "maxResults": 30, "relevanceLanguage": "fr", "key": self.youtube_key
            }
            
            r = requests.get(url, params=params, timeout=15)
            with self.lock:
                self.stats["youtube_calls"] += 1
            
            if r.status_code == 200:
                for item in r.json().get("items", []):
                    vid = item.get("id", {}).get("videoId", "")
                    title = item.get("snippet", {}).get("title", "")
                    desc = item.get("snippet", {}).get("description", "")
                    
                    # Transcription
                    transcript = ""
                    try:
                        from youtube_transcript_api import YouTubeTranscriptApi
                        t = YouTubeTranscriptApi.get_transcript(vid, languages=['fr'])
                        transcript = " ".join([x['text'] for x in t])
                    except:
                        pass
                    
                    search_text = f"{title} {desc} {transcript}"
                    for cand in self.extraire_candidats(search_text):
                        results.append({
                            "source": "youtube", "url": f"youtube.com/watch?v={vid}",
                            "title": title, "channel": item.get("snippet", {}).get("channelTitle"),
                            "texte": cand, "requete": query
                        })
            time.sleep(0.3)
        except:
            pass
        return results
    
    def detect_courant(self, text: str) -> str:
        """Détection courant déviant"""
        t = text.lower()
        if any(x in t for x in ['soufi', 'tariqa', 'dhikr', 'zikr', 'awliya', 'mourid']):
            return "Soufi"
        elif any(x in t for x in ['tabligh', 'tablighi', 'daawa', 'khuruj']):
            return "Tablīghī"
        elif any(x in t for x in ['ikhwane', 'frere musulman', 'banna']):
            return "Ikhwānī"
        elif any(x in t for x in ['ashari', 'matourid', 'kalam']):
            return "Ash'arī"
        elif any(x in t for x in ['salafi', 'manhaj', 'albani', 'baz', 'uthaymin']):
            return "Salafī"
        return "Général"
    
    def generer_fiche(self, candidat: Dict, hadith_ref: Dict) -> Dict:
        """Génère fiche Anatomie du Mensonge"""
        courant = self.detect_courant(candidat.get("texte", ""))
        
        fiche = {
            "id": f"ANAT_{len(self.fiches)+1:04d}",
            "date": datetime.now().isoformat(),
            "source_mensonge": {
                "plateforme": candidat.get("source"),
                "url": candidat.get("url"),
                "titre": candidat.get("title") or candidat.get("channel"),
            },
            "mensonge": {"texte_fr": candidat.get("texte")},
            "verite": {
                "texte_ar": hadith_ref.get("texte_ar"),
                "grade": hadith_ref.get("grade"),
                "savant": hadith_ref.get("savant"),
                "reference": hadith_ref.get("reference")
            },
            "verdicts": {
                "grade_final": hadith_ref.get("grade"),
                "savant_verificateur": hadith_ref.get("savant"),
                "refutation": hadith_ref.get("refutation_savant")
            },
            "propagation": {
                "courant": courant,
                "pratique_justifiee": hadith_ref.get("pratique_justifiee"),
                "viralite": "Élevée" if candidat.get("source") == "youtube" else "Moyenne"
            }
        }
        
        with self.lock:
            self.stats["courants"][courant] = self.stats["courants"].get(courant, 0) + 1
        
        return fiche
    
    def matcher_deluge(self, candidats: List[Dict]):
        """Matching massif contre blacklist"""
        print(f"\n🔎 MATCHING DÉLUGE — {len(candidats)} candidats vs {len(BLACKLIST_MASSIVE)} référencés...")
        
        matches = 0
        for cand in candidats:
            texte_cand = cand.get("texte", "").lower()
            if not texte_cand:
                continue
            
            with self.lock:
                self.stats["candidats_total"] += 1
            
            for hadith in BLACKLIST_MASSIVE:
                texte_ref = hadith.get("texte_fr", "").lower()
                if not texte_ref:
                    continue
                
                score = self.fuzzy_match(texte_cand, texte_ref)
                
                if score >= 75:  # Seuil 75%
                    matches += 1
                    fiche = self.generer_fiche(cand, hadith)
                    
                    with self.lock:
                        self.fiches.append(fiche)
                        self.stats["matches_confirmes"] += 1
                        self.stats["fiches_generees"] += 1
                    
                    print(f"  🎯 MATCH #{matches} ({score:.0f}%) | {fiche['propagation']['courant']} | {hadith.get('grade')}")
                    break
        
        print(f"✅ {matches} mensonges confirmés et documentés")
    
    def save_deluge(self):
        """Sauvegarde massive"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        fiches_path = self.data_dir / f"ANATOMIE_MENSONGE_{ts}.json"
        with open(fiches_path, "w", encoding="utf-8") as f:
            json.dump(self.fiches, f, ensure_ascii=False, indent=2)
        
        rapport = {
            "timestamp": ts, "stats": self.stats,
            "courants_propagateurs": self.stats["courants"],
            "total_fiches": len(self.fiches)
        }
        rapport_path = self.data_dir / f"RAPPORT_DELUGE_{ts}.json"
        with open(rapport_path, "w", encoding="utf-8") as f:
            json.dump(rapport, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 SAUVEGARDE:")
        print(f"   📁 Fiches: {fiches_path}")
        print(f"   📁 Rapport: {rapport_path}")
    
    def print_rapport_deluge(self):
        """Rapport terminal massif"""
        print("\n" + "=" * 70)
        print("║" + " " * 22 + "DÉLUGE AL-MĪZĀN 🔥" + " " * 27 + "║")
        print("║" + " " * 18 + "MODE ARTILLERIE MAXIMALE" + " " * 21 + "║")
        print("=" * 70)
        print(f"\n📊 STATISTIQUES EXPLOSIVES")
        print(f"   🔍 Appels Google API    : {self.stats['google_calls']}")
        print(f"   📺 Appels YouTube API   : {self.stats['youtube_calls']}")
        print(f"   📱 Messages Telegram    : {self.stats['telegram_msgs']}")
        print(f"   🎯 Candidats analysés   : {self.stats['candidats_total']}")
        print(f"   ✅ MATCHES CONFIRMÉS   : {self.stats['matches_confirmes']}")
        print(f"   📋 FICHES GÉNÉRÉES     : {self.stats['fiches_generees']}")
        
        print(f"\n🎯 MAPPING COURANTS DÉVIANTS")
        total_courants = sum(self.stats["courants"].values())
        for c, n in sorted(self.stats["courants"].items(), key=lambda x: -x[1]):
            pct = (n / max(total_courants, 1)) * 100
            bar = "█" * int(pct / 2)
            print(f"   {c:<12} : {n:>4} ({pct:>5.1f}%) {bar}")
        
        print("\n" + "=" * 70)
        print(f"✅ DÉLUGE TERMINÉ — {len(self.fiches)} MENSONGES DOCUMENTÉS")
        print("=" * 70)
    
    def executer_deluge(self):
        """Exécution mode déluge"""
        print("\n🚀 DÉLUGE AL-MĪZĀN — LANCEMENT ARTILLERIE LOURDE")
        print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Blacklist: {len(BLACKLIST_MASSIVE)} hadiths référencés")
        print("   Threading: ACTIVÉ | Matching: FUZZY 75% | Mode: DÉLUGE\n")
        
        # Threading massif
        all_candidats = []
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures_google = {executor.submit(self.scan_google_deluge, q): q for q in REQUETES_DELUGE[:8]}
            futures_youtube = {executor.submit(self.scan_youtube_deluge, q): q for q in REQUETES_DELUGE[8:]}
            
            for future in as_completed(futures_google):
                all_candidats.extend(future.result())
            for future in as_completed(futures_youtube):
                all_candidats.extend(future.result())
        
        print(f"\n📊 TOTAL CANDIDATS BRUTS: {len(all_candidats)}")
        
        # Matching massif
        if all_candidats:
            self.matcher_deluge(all_candidats)
        
        # Sauvegarde
        self.save_deluge()
        
        # Rapport final
        self.print_rapport_deluge()
        
        return self.fiches


def main():
    scanner = ScannerDeluge()
    scanner.executer_deluge()


if __name__ == "__main__":
    main()
