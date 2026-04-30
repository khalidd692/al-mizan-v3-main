#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GRAND SCAN AL-MĪZĀN — DÉLUGE V2 🔥🔥
Scan massif avec extraction agressive et matching optimisé
"""

import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote

import requests
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════════
# BLACKLIST ULTRA MASSIVE — 50+ HADITHS INVENTÉS/FABLES
# ═══════════════════════════════════════════════════════════════════════════════

BLACKLIST_ULTRA = [
    # === AL-ALBĀNĪ ===
    {"id": 1, "texte_fr": "Cherche la science même en Chine", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 416", "courant": "Général", "keywords": ["science", "chine", "étudier"]},
    {"id": 2, "texte_fr": "Mes compagnons sont comme des étoiles suivez n'importe lequel", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 144", "courant": "Ikhwānī", "keywords": ["compagnons", "étoiles", "suivre"]},
    {"id": 3, "texte_fr": "La divergence de ma communauté est une miséricorde", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 57", "courant": "Ikhwānī", "keywords": ["divergence", "différence", "miséricorde"]},
    {"id": 4, "texte_fr": "L'amour de la patrie fait partie de la foi", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 36", "courant": "Ikhwānī", "keywords": ["patrie", "nation", "foi"]},
    {"id": 5, "texte_fr": "Travaillez pour votre vie comme si vous viviez éternellement", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 8", "courant": "Général", "keywords": ["travailler", "vie", "éternel"]},
    {"id": 6, "texte_fr": "Celui qui ne se soucie pas des affaires des musulmans n'en fait pas partie", "grade": "daif_jiddan", "savant": "al-Albānī", "ref": "SD 480", "courant": "Ikhwānī", "keywords": ["soucier", "affaires", "musulmans"]},
    {"id": 7, "texte_fr": "Soyez optimistes vous trouverez le bien", "grade": "la_asla_lahu", "savant": "al-Albānī", "ref": "SD 829", "courant": "Général", "keywords": ["optimiste", "bien", "positif"]},
    {"id": 8, "texte_fr": "Visitez les tombes car elles vous rappellent la mort", "grade": "daif", "savant": "al-Albānī", "ref": "SD 50", "courant": "Soufi", "keywords": ["tombe", "cimetière", "mort"]},
    {"id": 9, "texte_fr": "Les savants sont les héritiers des prophètes", "grade": "daif", "savant": "al-Albānī", "ref": "SD 629", "courant": "Ash'arī", "keywords": ["savants", "héritiers", "prophètes"]},
    {"id": 10, "texte_fr": "Le Prophète a pleuré pour les morts", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 182", "courant": "Soufi", "keywords": ["pleurer", "morts", "larmes"]},
    
    # === IBN BĀZ ===
    {"id": 11, "texte_fr": "La femme en Enfer suspendue par les cheveux", "grade": "mawdou", "savant": "Ibn Bāz", "ref": "FT 19493", "courant": "Général", "keywords": ["femme", "enfer", "cheveux"]},
    {"id": 12, "texte_fr": "Qui me voit a vu Allah", "grade": "mawdou", "savant": "Ibn Bāz", "ref": "FT", "courant": "Soufi", "keywords": ["voir", "Allah", "prophète"]},
    {"id": 13, "texte_fr": "Ne refuse pas le don d'eau", "grade": "mawdou", "savant": "Ibn Bāz", "ref": "", "courant": "Général", "keywords": ["eau", "don", "refuser"]},
    
    # === VIRAL HADITHS ===
    {"id": 14, "texte_fr": "La meilleure des femmes est celle qui ne voit pas les hommes", "grade": "mawdou", "savant": "al-Albānī", "ref": "", "courant": "Général", "keywords": ["femme", "meilleure", "voile"]},
    {"id": 15, "texte_fr": "Le Prophète a interdit de manger avec la main gauche", "grade": "saheeh", "savant": "Muslim", "ref": "", "courant": "Salafī", "keywords": ["manger", "gauche", "main"]},
    {"id": 16, "texte_fr": "Quand un mari regarde sa femme avec amour Allah le récompense", "grade": "mawdou", "savant": "al-Albānī", "ref": "", "courant": "Général", "keywords": ["mari", "femme", "amour", "regarder"]},
    {"id": 17, "texte_fr": "Les anges ne entrent pas dans une maison avec un chien", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī", "keywords": ["anges", "chien", "maison"]},
    {"id": 18, "texte_fr": "Le cœur rouille comme le fer", "grade": "daif", "savant": "al-Albānī", "ref": "", "courant": "Général", "keywords": ["cœur", "rouille", "fer"]},
    {"id": 19, "texte_fr": "Quand Allah aime un serviteur il l'afflige", "grade": "mawdou", "savant": "Ibn Taymiya", "ref": "", "courant": "Général", "keywords": ["aime", "affliger", "souffrance"]},
    {"id": 20, "texte_fr": "Ne voyagez pas seul car Satan sera votre compagnon", "grade": "mawdou", "savant": "al-Albānī", "ref": "", "courant": "Général", "keywords": ["voyage", "seul", "satan"]},
    {"id": 21, "texte_fr": "Le Prophète aurait embrassé les mains de Abu Bakr", "grade": "mawdou", "savant": "Multiple", "ref": "", "courant": "Ash'arī", "keywords": ["Abu Bakr", "embrasser", "mains"]},
    {"id": 22, "texte_fr": "La science sans pratique est comme un arbre sans fruit", "grade": "la_asla_lahu", "savant": "Ibn Hajar", "ref": "", "courant": "Soufi", "keywords": ["science", "pratique", "arbre"]},
    {"id": 23, "texte_fr": "La meilleure dhikr est celle faite en secret", "grade": "mawdou", "savant": "al-Albānī", "ref": "", "courant": "Soufi", "keywords": ["dhikr", "secret", "silencieux"]},
    {"id": 24, "texte_fr": "Quand tu as un appel à faire à Allah fais-le", "grade": "mawdou", "savant": "Multiple", "ref": "", "courant": "Général", "keywords": ["appel", "Allah", "demander"]},
    {"id": 25, "texte_fr": "Les trois choses sérieuses mariage chasse femme", "grade": "mawdou", "savant": "al-Albānī", "ref": "", "courant": "Général", "keywords": ["sérieux", "chasse", "jeu"]},
    {"id": 26, "texte_fr": "Quand vous priez ne regardez ni à droite ni à gauche", "grade": "daif", "savant": "al-Albānī", "ref": "", "courant": "Général", "keywords": ["prière", "regarder", "droite"]},
    {"id": 27, "texte_fr": "Le Prophète a dit au Companion qui voulait tuer un serpent", "grade": "mawdou", "savant": "al-Albānī", "ref": "", "courant": "Général", "keywords": ["serpent", "tuer", "compagnon"]},
    {"id": 28, "texte_fr": "Si tu as un appel à faire à Allah fais-le car il t'écoute", "grade": "mawdou", "savant": "Multiple", "ref": "", "courant": "Général", "keywords": ["appel", "écoute", "Allah"]},
    {"id": 29, "texte_fr": "Une femme ne doit pas voyager sans mahram", "grade": "saheeh", "savant": "Muqbil", "ref": "", "courant": "Salafī", "keywords": ["femme", "voyage", "mahram"]},
    {"id": 30, "texte_fr": "Le Prophète a interdit de fumer", "grade": "mawdou", "savant": "al-Albānī", "ref": "", "courant": "Général", "keywords": ["fumer", "cigarette", "interdit"]},
    {"id": 31, "texte_fr": "Le Prophète a dit de ne pas dormir sur le ventre", "grade": "daif", "savant": "al-Albānī", "ref": "", "courant": "Général", "keywords": ["dormir", "ventre", "position"]},
    {"id": 32, "texte_fr": "Le Prophète a dit de manger avec trois doigts", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī", "keywords": ["manger", "doigts", "trois"]},
    {"id": 33, "texte_fr": "Le Prophète a dit de boire en trois fois", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī", "keywords": ["boire", "trois", "gorgées"]},
    {"id": 34, "texte_fr": "Le Prophète a dit de ne pas s'allonger sur le côté gauche", "grade": "daif", "savant": "al-Albānī", "ref": "", "courant": "Général", "keywords": ["allonger", "gauche", "côté"]},
    {"id": 35, "texte_fr": "Le Prophète a dit que le mariage est la moitié de la foi", "grade": "mawdou", "savant": "al-Albānī", "ref": "", "courant": "Général", "keywords": ["mariage", "moitié", "foi"]},
    {"id": 36, "texte_fr": "Le Prophète a dit que le paradis est aux pieds des mères", "grade": "mawdou", "savant": "al-Albānī", "ref": "", "courant": "Général", "keywords": ["paradis", "pieds", "mère"]},
    {"id": 37, "texte_fr": "Le Prophète a dit que le temps est une épée", "grade": "mawdou", "savant": "al-Albānī", "ref": "", "courant": "Général", "keywords": ["temps", "épée", "coupe"]},
    {"id": 38, "texte_fr": "Le Prophète a dit que le monde est la prison du croyant", "grade": "saheeh", "savant": "Muslim", "ref": "", "courant": "Salafī", "keywords": ["monde", "prison", "croyant"]},
    {"id": 39, "texte_fr": "Le Prophète a dit que le fajr est meilleur que le monde", "grade": "saheeh", "savant": "Muslim", "ref": "", "courant": "Salafī", "keywords": ["fajr", "prière", "monde"]},
    {"id": 40, "texte_fr": "Le Prophète a dit que le sourire est sadaqa", "grade": "saheeh", "savant": "Tirmidhi", "ref": "", "courant": "Général", "keywords": ["sourire", "sadaqa", "charité"]},
    {"id": 41, "texte_fr": "Le Prophète a dit que le bon caractère est le meilleur", "grade": "saheeh", "savant": "Tirmidhi", "ref": "", "courant": "Général", "keywords": ["caractère", "meilleur", "vertu"]},
    {"id": 42, "texte_fr": "Le Prophète a dit que le musulman est le miroir du musulman", "grade": "saheeh", "savant": "Abu Dawud", "ref": "", "courant": "Général", "keywords": ["miroir", "musulman", "frère"]},
    {"id": 43, "texte_fr": "Le Prophète a dit que le calme est de Allah", "grade": "daif", "savant": "al-Albānī", "ref": "", "courant": "Général", "keywords": ["calme", "Allah", "hâte"]},
    {"id": 44, "texte_fr": "Le Prophète a dit que le mariage est ma sunna", "grade": "saheeh", "savant": "Ibn Majah", "ref": "", "courant": "Salafī", "keywords": ["mariage", "sounnah", "célibat"]},
    {"id": 45, "texte_fr": "Le Prophète a dit que le rêve du croyant est vrai", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Général", "keywords": ["rêve", "croyant", "vérité"]},
    {"id": 46, "texte_fr": "Le Prophète a dit que le riba a 70 portes", "grade": "saheeh", "savant": "Ibn Majah", "ref": "", "courant": "Salafī", "keywords": ["riba", "intérêt", "70"]},
    {"id": 47, "texte_fr": "Le Prophète a dit que le pauvre entre au paradis", "grade": "daif", "savant": "al-Albānī", "ref": "", "courant": "Général", "keywords": ["pauvre", "paradis", "riche"]},
    {"id": 48, "texte_fr": "Le Prophète a dit que le meilleur jihad parler vérité", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī", "keywords": ["jihad", "vérité", "parler"]},
    {"id": 49, "texte_fr": "Le Prophète a dit que le paradis est sous l'ombre des épées", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī", "keywords": ["paradis", "ombre", "épées"]},
    {"id": 50, "texte_fr": "Le Prophète a dit que la bonté vers parents est jihad", "grade": "mawdou", "savant": "al-Albānī", "ref": "", "courant": "Général", "keywords": ["parents", "bonté", "jihad"]},
]

# Requêtes ultra agressives
REQUETES_ULTRA = [
    # Hadiths viraux
    "hadith science Chine Prophète français",
    "hadith compagnons étoiles messager",
    "hadith divergence miséricorde communauté",
    "hadith patrie nationalisme islam",
    "hadith femme paradis enfer hadith",
    "hadith cœur rouille dhikr",
    "hadith voyage seul satan",
    "hadith mariage moitié foi",
    "hadith paradis pieds mères",
    "hadith meilleur femme voit pas hommes",
    "hadith anges chien maison",
    "hadith monde prison croyant",
    "hadith sourire sadaqa charité",
    "hadith pauvre entre paradis",
    "hadith jihad parler vérité tyran",
    "hadith temps épée coupe",
    "hadith optimisme bien trouver",
    "hadith savants héritiers prophètes",
    "hadith bon caractère meilleur",
    "hadith musulman miroir frère",
    
    # YouTube spécifique
    "site:youtube.com hadith authentique",
    "site:youtube.com rappel islamique",
    "site:youtube.com cours hadith",
    "site:youtube.com hadith du jour",
    "site:youtube.com explication hadith",
]

# ═══════════════════════════════════════════════════════════════════════════════
# SCANNER V2
# ═══════════════════════════════════════════════════════════════════════════════

class ScannerDelugeV2:
    """Scanner ultra agressif"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        self.stats = {
            "google_calls": 0, "youtube_calls": 0,
            "candidats_bruts": 0, "candidats_filtres": 0,
            "matches_confirmes": 0, "fiches_generees": 0,
            "courants": {"Ikhwānī": 0, "Tablīghī": 0, "Soufi": 0, "Ash'arī": 0, "Salafī": 0, "Général": 0}
        }
        
        self.fiches = []
        self.lock = threading.Lock()
        self.blacklist = BLACKLIST_ULTRA
        
        # API
        self.google_key = os.getenv("GOOGLE_API_KEY")
        self.google_cx = os.getenv("GOOGLE_CX")
        self.youtube_key = os.getenv("YOUTUBE_API_KEY")
    
    def fuzzy_score(self, s1: str, s2: str) -> float:
        """Score de similarité"""
        if not s1 or not s2:
            return 0.0
        return SequenceMatcher(None, s1.lower(), s2.lower()).ratio() * 100
    
    def extract_candidates_aggressive(self, text: str) -> List[str]:
        """Extraction ultra agressive"""
        if not text or len(text) < 20:
            return []
        
        candidates = []
        
        # Pattern 1: Citations entre guillemets avec mot Prophète
        for match in re.findall(r'[«"\']([^«"\']{30,500}?Proph[^«"\']{0,200})[»"\']', text, re.IGNORECASE):
            candidates.append(match.strip())
        
        # Pattern 2: Phrases avec "a dit" et contexte religieux
        for match in re.findall(r'(?:le |L\')(?:Prophète|Messager)[^.]{0,50}a dit[^.]{0,10}([^\n.]{25,400})', text, re.IGNORECASE):
            candidates.append(match.strip())
        
        # Pattern 3: Keywords hadiths viraux
        viral_keywords = ["science Chine", "compagnons étoiles", "divergence", "patrie", "cœur rouille", 
                         "paradis femme", "anges chien", "monde prison", "meilleur femme"]
        for keyword in viral_keywords:
            if keyword.lower() in text.lower():
                # Extraire la phrase contenant le keyword
                for match in re.findall(r'[^\n.]{0,50}' + re.escape(keyword) + r'[^\n.]{0,200}', text, re.IGNORECASE):
                    if len(match) > 30:
                        candidates.append(match.strip())
        
        # Filtrer doublons et courts
        seen = set()
        filtered = []
        for c in candidates:
            c = c[:500]  # Limite taille
            if len(c) >= 30 and c not in seen:
                seen.add(c)
                filtered.append(c)
        
        return filtered
    
    def scan_google_aggressive(self, query: str) -> List[Dict]:
        """Scan Google agressif"""
        results = []
        if not self.google_key or not self.google_cx:
            return results
        
        try:
            for start in range(1, 21, 10):  # 20 résultats
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    "key": self.google_key, "cx": self.google_cx,
                    "q": query, "start": start, "num": 10,
                    "lr": "lang_fr", "hl": "fr"
                }
                
                r = requests.get(url, params=params, timeout=20)
                with self.lock:
                    self.stats["google_calls"] += 1
                
                if r.status_code == 200:
                    for item in r.json().get("items", []):
                        snippet = f"{item.get('title', '')} {item.get('snippet', '')}"
                        cands = self.extract_candidates_aggressive(snippet)
                        
                        for cand in cands:
                            results.append({
                                "source": "google", "url": item.get("link"),
                                "title": item.get("title"), "texte": cand,
                                "requete": query
                            })
                time.sleep(0.3)
        except Exception as e:
            pass
        return results
    
    def scan_youtube_aggressive(self, query: str) -> List[Dict]:
        """Scan YouTube agressif"""
        results = []
        if not self.youtube_key:
            return results
        
        try:
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                "part": "snippet", "q": query, "type": "video",
                "maxResults": 25, "relevanceLanguage": "fr",
                "key": self.youtube_key
            }
            
            r = requests.get(url, params=params, timeout=20)
            with self.lock:
                self.stats["youtube_calls"] += 1
            
            if r.status_code == 200:
                for item in r.json().get("items", []):
                    vid = item.get("id", {}).get("videoId", "")
                    title = item.get("snippet", {}).get("title", "")
                    desc = item.get("snippet", {}).get("description", "")
                    channel = item.get("snippet", {}).get("channelTitle", "")
                    
                    # Transcription (sans bloquer)
                    transcript = ""
                    try:
                        from youtube_transcript_api import YouTubeTranscriptApi
                        t = YouTubeTranscriptApi.get_transcript(vid, languages=['fr'])
                        transcript = " ".join([x['text'] for x in t[:50]])  # Limite 50 segments
                    except:
                        pass
                    
                    search_text = f"{title} {desc} {transcript}"
                    cands = self.extract_candidates_aggressive(search_text)
                    
                    for cand in cands:
                        results.append({
                            "source": "youtube", "url": f"youtube.com/watch?v={vid}",
                            "title": title, "channel": channel,
                            "texte": cand, "requete": query
                        })
            time.sleep(0.2)
        except:
            pass
        return results
    
    def detect_courant(self, text: str) -> str:
        """Détection courant"""
        t = text.lower()
        if any(x in t for x in ['soufi', 'tariqa', 'dhikr', 'awliya']):
            return "Soufi"
        elif any(x in t for x in ['tabligh', 'tablighi']):
            return "Tablīghī"
        elif any(x in t for x in ['ikhwane', 'frere musulman']):
            return "Ikhwānī"
        elif any(x in t for x in ['ashari', 'matourid']):
            return "Ash'arī"
        elif any(x in t for x in ['salafi', 'albani', 'baz', 'uthaymin']):
            return "Salafī"
        return "Général"
    
    def generer_fiche(self, cand: Dict, ref: Dict, score: float) -> Dict:
        """Génère fiche anatomie"""
        courant = self.detect_courant(cand.get("texte", ""))
        
        fiche = {
            "id": f"FICHE_{len(self.fiches)+1:04d}",
            "timestamp": datetime.now().isoformat(),
            "detection": {
                "source": cand.get("source"),
                "plateforme": cand.get("source").upper(),
                "url": cand.get("url"),
                "titre": cand.get("title") or cand.get("channel", "N/A"),
                "score_match": f"{score:.1f}%",
            },
            "mensonge_detecte": {
                "texte_circulant": cand.get("texte"),
                "longueur": len(cand.get("texte", "")),
            },
            "verite_revelée": {
                "grade_authentique": ref.get("grade"),
                "savant_verificateur": ref.get("savant"),
                "reference": ref.get("ref"),
                "texte_reference": ref.get("texte_fr"),
            },
            "verdict_savants": {
                "couperet": f"{ref.get('grade').upper()} — {ref.get('savant')}",
                "reference_livre": ref.get("ref"),
            },
            "propagation_analysee": {
                "courant_identifie": courant,
                "pratique_justifiee": ref.get("keywords", []),
                "niveau_viralite": "ÉLEVÉ" if cand.get("source") == "youtube" else "MOYEN",
            }
        }
        
        with self.lock:
            self.stats["courants"][courant] = self.stats["courants"].get(courant, 0) + 1
        
        return fiche
    
    def matcher_ultra(self, candidats: List[Dict]):
        """Matching ultra avec seuil 65%"""
        print(f"\n🔎 MATCHING ULTRA — {len(candidats)} candidats vs {len(self.blacklist)} référencés...")
        
        matches = 0
        for cand in candidats:
            texte_cand = cand.get("texte", "").lower()
            if not texte_cand or len(texte_cand) < 25:
                continue
            
            with self.lock:
                self.stats["candidats_filtres"] += 1
            
            for ref in self.blacklist:
                texte_ref = ref.get("texte_fr", "").lower()
                if not texte_ref:
                    continue
                
                # Matching fuzzy
                score = self.fuzzy_score(texte_cand, texte_ref)
                
                # Matching par keywords
                keyword_match = any(kw.lower() in texte_cand for kw in ref.get("keywords", []))
                
                if score >= 65 or (keyword_match and score >= 40):
                    matches += 1
                    fiche = self.generer_fiche(cand, ref, score)
                    
                    with self.lock:
                        self.fiches.append(fiche)
                        self.stats["matches_confirmes"] += 1
                        self.stats["fiches_generees"] += 1
                    
                    print(f"  🎯 #{matches} [{score:.0f}%] {ref.get('grade')} | {ref.get('savant')} | {fiche['propagation_analysee']['courant_identifie']}")
                    break
        
        print(f"✅ {matches} MENSONGES CONFIRMÉS ET DOCUMENTÉS")
    
    def save_ultra(self):
        """Sauvegarde massive"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        fiches_path = self.data_dir / f"ANATOMIE_ULTRA_{ts}.json"
        with open(fiches_path, "w", encoding="utf-8") as f:
            json.dump(self.fiches, f, ensure_ascii=False, indent=2)
        
        rapport = {
            "scan": "DELUGE_V2", "timestamp": ts,
            "statistiques": self.stats,
            "courants_propagateurs": self.stats["courants"],
            "total_mensonges": len(self.fiches)
        }
        rapport_path = self.data_dir / f"RAPPORT_ULTRA_{ts}.json"
        with open(rapport_path, "w", encoding="utf-8") as f:
            json.dump(rapport, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 SAUVEGARDE:")
        print(f"   📁 Fiches: {fiches_path}")
        print(f"   📁 Rapport: {rapport_path}")
    
    def print_rapport_ultra(self):
        """Rapport final explosif"""
        print("\n" + "=" * 75)
        print("║" + " " * 25 + "🔥 DÉLUGE V2 TERMINÉ 🔥" + " " * 25 + "║")
        print("=" * 75)
        
        print(f"\n📊 STATISTIQUES EXPLOSIVES")
        print(f"   🔍 Appels Google API    : {self.stats['google_calls']}")
        print(f"   📺 Appels YouTube API   : {self.stats['youtube_calls']}")
        print(f"   📝 Candidats bruts      : {self.stats['candidats_bruts']}")
        print(f"   🎯 Candidats analysés   : {self.stats['candidats_filtres']}")
        print(f"   ✅ MATCHES CONFIRMÉS   : {self.stats['matches_confirmes']}")
        print(f"   📋 FICHES GÉNÉRÉES      : {self.stats['fiches_generees']}")
        
        print(f"\n🎯 MAPPING COURANTS DÉVIANTS")
        total = sum(self.stats["courants"].values())
        for c, n in sorted(self.stats["courants"].items(), key=lambda x: -x[1]):
            pct = (n / max(total, 1)) * 100
            bar = "█" * int(pct / 3)
            print(f"   {c:<12} : {n:>4} ({pct:>5.1f}%) {bar}")
        
        print("\n" + "=" * 75)
        print(f"✅ SCAN TERMINÉ — {len(self.fiches)} MENSONGES DOCUMENTÉS")
        print("=" * 75)
    
    def executer_ultra(self):
        """Exécution ultra"""
        print("\n🚀 DÉLUGE AL-MĪZĀN V2 — ARTILLERIE ULTRA LOURDE")
        print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Blacklist: {len(self.blacklist)} hadiths")
        print(f"   Seuil matching: 65% | Keywords: ACTIVÉ\n")
        
        # Threading
        all_cands = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures_g = {executor.submit(self.scan_google_aggressive, q): q for q in REQUETES_ULTRA[:10]}
            futures_y = {executor.submit(self.scan_youtube_aggressive, q): q for q in REQUETES_ULTRA[10:]}
            
            for f in futures_g:
                all_cands.extend(f.result())
            for f in futures_y:
                all_cands.extend(f.result())
        
        with self.lock:
            self.stats["candidats_bruts"] = len(all_cands)
        
        print(f"\n📊 EXTRACTION: {len(all_cands)} candidats bruts")
        
        # Matching
        if all_cands:
            self.matcher_ultra(all_cands)
        
        # Sauvegarde
        self.save_ultra()
        
        # Rapport
        self.print_rapport_ultra()
        
        return self.fiches


def main():
    scanner = ScannerDelugeV2()
    scanner.executer_ultra()


if __name__ == "__main__":
    main()
