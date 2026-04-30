#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Radar de la Sunna - Al-Mīzān
Système de détection des hadiths inventés/faibles circulant sur internet francophone
"""

import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
REQUETES_GOOGLE = [
    '"le Prophète a dit" hadith',
    '"le Messager d\'Allah a dit" hadith',
    '"il est rapporté que" Prophète',
    '"le Prophète paix sur lui a dit"',
    '"sallallahu alayhi wa sallam a dit"',
    '"hadith" "le Prophète" site:facebook.com',
    '"hadith" "Prophète" site:tiktok.com',
    '"le Prophète a dit" site:telegram.me',
    '"hadith" "Messager" site:twitter.com',
    '"le Prophète a dit" site:youtube.com'
]

REQUETES_YOUTUBE = [
    "hadith du jour français",
    "rappel islamique hadith",
    "khutba vendredi français",
    "cours islam hadith français",
    "hadith inventé réfuté",
    "faux hadith islam",
    "hadith faible français"
]

SITES_CIBLES = [
    "https://alibaanahtt.wordpress.com/2020/06/30/les-hadiths-faibles-les-plus-repandus/",
    "https://bibliotheque-islamique.fr/hadith/hadiths-faibles/",
    "https://www.alnas.fr/actualite/religion/prenez-garde-aux-faux-hadiths-qui-circulent/",
    "https://www.convertistoislam.fr/2014/11/gare-aux-hadiths-mensongers.html",
    "https://islamhouse.com/fr/",
    "https://islamweb.net/fr/"
]

BLACKLIST_MANUELLE = [
    {
        "texte_fr": "Cherche la science même en Chine",
        "texte_ar": "اطلبوا العلم ولو في الصين",
        "grade": "mawdou",
        "savant": "al-Albānī",
        "reference": "Silsila Daifa n°416",
        "courants_concernes": ["Général"],
        "pratique_justifiee": "Justifier l'étude sans cadre méthodologique islamique",
        "refutation_savant": "al-Albānī : inventé — Silsila Daifa vol.1 n°416"
    },
    {
        "texte_fr": "Mes compagnons sont comme des étoiles suivez n'importe lequel",
        "texte_ar": "أصحابي كالنجوم بأيهم اقتديتم اهتديتم",
        "grade": "mawdou",
        "savant": "al-Albānī",
        "reference": "Silsila Daifa n°144",
        "courants_concernes": ["Ikhwānī", "Ash'arī"],
        "pratique_justifiee": "Justifier le taqlīd aveugle et légitimer tous les madhhabs sans critère",
        "refutation_savant": "al-Albānī : inventé — Ibn Ḥazm : faux et mensonge — Silsila Daifa n°144"
    },
    {
        "texte_fr": "La divergence de ma communauté est une miséricorde",
        "texte_ar": "اختلاف أمتي رحمة",
        "grade": "mawdou",
        "savant": "al-Albānī",
        "reference": "Silsila Daifa n°57",
        "courants_concernes": ["Ikhwānī", "Ash'arī", "Soufi"],
        "pratique_justifiee": "Légitimer toutes les divergences doctrinales et neutraliser le manhaj",
        "refutation_savant": "al-Albānī : inventé et sans fondement — Silsila Daifa n°57"
    },
    {
        "texte_fr": "L'amour de la patrie fait partie de la foi",
        "texte_ar": "حب الوطن من الإيمان",
        "grade": "mawdou",
        "savant": "al-Albānī",
        "reference": "Silsila Daifa n°36",
        "courants_concernes": ["Ikhwānī"],
        "pratique_justifiee": "Légitimer le nationalisme au sein de l'Islam",
        "refutation_savant": "al-Albānī : inventé — Silsila Daifa n°36"
    },
    {
        "texte_fr": "Travaillez pour votre vie comme si vous viviez éternellement",
        "texte_ar": "اعمل لدنياك كأنك تعيش أبداً",
        "grade": "mawdou",
        "savant": "al-Albānī",
        "reference": "Silsila Daifa n°8",
        "courants_concernes": ["Général"],
        "pratique_justifiee": "Fausse sagesse attribuée au Prophète pour justifier l'attachement au dunya",
        "refutation_savant": "al-Albānī : inventé — Silsila Daifa n°8"
    },
    {
        "texte_fr": "Celui qui ne se soucie pas des affaires des musulmans n'en fait pas partie",
        "texte_ar": "من لم يهتم بأمر المسلمين فليس منهم",
        "grade": "daif_jiddan",
        "savant": "al-Albānī",
        "reference": "Silsila Daifa n°480",
        "courants_concernes": ["Ikhwānī"],
        "pratique_justifiee": "Justifier l'activisme politique partisan au nom de l'Islam",
        "refutation_savant": "al-Albānī : très faible — Silsila Daifa vol.1 n°480"
    },
    {
        "texte_fr": "Hadith de la femme en Enfer suspendue par les cheveux",
        "texte_ar": None,
        "grade": "mawdou",
        "savant": "Ibn Bāz",
        "reference": "Fatwā Ibn Bāz n°19493",
        "courants_concernes": ["Général"],
        "pratique_justifiee": "Effrayer les femmes par des châtiments inventés",
        "refutation_savant": "Ibn Bāz : faux et inventé — mensonge envers le Prophète — Fatwā n°19493"
    },
    {
        "texte_fr": "Soyez optimistes vous trouverez le bien",
        "texte_ar": "تفاءلوا بالخير تجدوه",
        "grade": "la_asla_lahu",
        "savant": "al-Albānī",
        "reference": "Silsila Daifa n°829",
        "courants_concernes": ["Général"],
        "pratique_justifiee": "Citation pieuse sans fondement attribuée au Prophète",
        "refutation_savant": "al-Albānī : je n'en connais pas de source — Silsila Daifa n°829"
    },
    {
        "texte_fr": "Les Fadhail al-Amal utilisés par les Tablīghī",
        "texte_ar": None,
        "grade": "daif_jiddan",
        "savant": "al-Albānī",
        "reference": "Silsila Daifa — multiples entrées",
        "courants_concernes": ["Tablīghī"],
        "pratique_justifiee": "Justifier les pratiques du mouvement Tablīgh par des hadiths très faibles",
        "refutation_savant": "al-Albānī a réfuté systématiquement les hadiths du Fadhail al-Amal dans la Silsila Daifa"
    },
    {
        "texte_fr": "Visitez les tombes car elles vous rappellent la mort",
        "texte_ar": "زوروا القبور فإنها تذكركم الآخرة",
        "grade": "daif",
        "savant": "al-Albānī",
        "reference": "Silsila Daifa n°50",
        "courants_concernes": ["Soufi"],
        "pratique_justifiee": "Légitimer la visite des tombes des saints et le culte des morts",
        "refutation_savant": "al-Albānī : faible — utilisé abusivement pour légitimer le culte des tombes — Silsila Daifa n°50"
    }
]

# Pattern pour extraire les citations hadith
HADITH_PATTERNS = [
    r'le Prophète(?:\s+paix\s+sur\s+lui)?\s+a\s+dit\s*:?\s*["\']?([^"\']{20,500})["\']?',
    r'le Messager d\'Allah\s+a\s+dit\s*:?\s*["\']?([^"\']{20,500})["\']?',
    r'sallallahu\s+alayhi\s+wa\s+sallam\s+a\s+dit\s*:?\s*["\']?([^"\']{20,500})["\']?',
    r'il\s+est\s+rapporté\s+que\s+(?:le\s+)?Prophète[^"\']*["\']?([^"\']{20,500})["\']?',
    r'hadith[^"\']*["\']([^"\']{20,500})["\']',
    r'[«"\']([^"\']{30,500}?(?:Prophète|Messager|Allah|prière|sallallahu)[^"\']{0,200})[»"\']'
]


class ScannerInternet:
    """Scanner de détection des hadiths inventés/faibles"""

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.config_dir = self.base_dir / "config"
        self.db_path = self.base_dir / "backend" / "almizan_v7.db"

        self.data_dir.mkdir(exist_ok=True)

        # Stats
        self.stats = {
            "google_results": 0,
            "youtube_videos": 0,
            "telegram_messages": 0,
            "sites_pages": 0,
            "manual_entries": len(BLACKLIST_MANUELLE),
            "candidats_detectes": 0,
            "confirmes_dorar": 0,
            "non_trouves_dorar": 0,
            "deja_dans_base": 0,
            "absents_base": 0,
            "courants": {
                "Ikhwānī": 0,
                "Tablīghī": 0,
                "Soufi": 0,
                "Ash'arī": 0,
                "Général": 0
            }
        }

        # Results
        self.blacklist: List[Dict[str, Any]] = []
        self.candidats: List[Dict[str, Any]] = []

        # Load config
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Charge la configuration des sources"""
        config_path = self.config_dir / "sources.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "telegram_channels": [],
            "youtube_channels": [],
            "sites_islamiques": []
        }

    def extract_hadith_candidates(self, text: str) -> List[str]:
        """Extrait les candidats hadith d'un texte"""
        candidates = []
        if not text:
            return candidates

        for pattern in HADITH_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                candidate = match.strip()
                if len(candidate) >= 20:
                    candidates.append(candidate)

        # Nettoyer les doublons
        return list(set(candidates))

    def scan_google(self) -> List[Dict[str, Any]]:
        """Scan Google Custom Search API"""
        print("🔍 Scan Google Custom Search...")
        results = []

        api_key = os.getenv("GOOGLE_API_KEY")
        cx = os.getenv("GOOGLE_CX")

        if not api_key or not cx:
            print("⚠️  Clés Google API non configurées, skipping...")
            return results

        for query in REQUETES_GOOGLE:
            try:
                # 5 pages maximum = 50 résultats
                for start in range(1, 51, 10):
                    url = "https://www.googleapis.com/customsearch/v1"
                    params = {
                        "key": api_key,
                        "cx": cx,
                        "q": query,
                        "start": start,
                        "num": 10,
                        "lr": "lang_fr",
                        "hl": "fr"
                    }

                    response = requests.get(url, params=params, timeout=30)

                    if response.status_code == 200:
                        data = response.json()
                        items = data.get("items", [])

                        for item in items:
                            snippet = item.get("snippet", "")
                            candidates = self.extract_hadith_candidates(snippet)

                            for candidate in candidates:
                                results.append({
                                    "source": "google",
                                    "url": item.get("link", ""),
                                    "title": item.get("title", ""),
                                    "texte_candidat": candidate,
                                    "requete": query,
                                    "date_scan": datetime.now().isoformat()
                                })

                        self.stats["google_results"] += len(items)

                        if len(items) < 10:
                            break

                    time.sleep(1)

            except Exception as e:
                print(f"⚠️  Erreur Google scan ({query}): {e}")
                continue

        print(f"✅ Google: {len(results)} candidats extraits")
        return results

    def scan_youtube(self) -> List[Dict[str, Any]]:
        """Scan YouTube Data API avec transcripts"""
        print("📺 Scan YouTube...")
        results = []

        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            print("⚠️  Clé YouTube API non configurée, skipping...")
            return results

        try:
            from youtube_transcript_api import YouTubeTranscriptApi
        except ImportError:
            print("⚠️  youtube_transcript_api non installé, skipping transcripts...")
            YouTubeTranscriptApi = None

        for query in REQUETES_YOUTUBE:
            try:
                url = "https://www.googleapis.com/youtube/v3/search"
                params = {
                    "part": "snippet",
                    "q": query,
                    "type": "video",
                    "maxResults": 25,
                    "relevanceLanguage": "fr",
                    "key": api_key
                }

                response = requests.get(url, params=params, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])

                    for item in items:
                        video_id = item.get("id", {}).get("videoId", "")
                        title = item.get("snippet", {}).get("title", "")
                        channel = item.get("snippet", {}).get("channelTitle", "")
                        published_at = item.get("snippet", {}).get("publishedAt", "")

                        transcript_text = ""

                        if YouTubeTranscriptApi and video_id:
                            try:
                                transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['fr'])
                                transcript_text = " ".join([t['text'] for t in transcript_list])
                            except Exception:
                                pass

                        search_text = f"{title} {transcript_text}"
                        candidates = self.extract_hadith_candidates(search_text)

                        for candidate in candidates:
                            results.append({
                                "source": "youtube",
                                "url": f"https://youtube.com/watch?v={video_id}",
                                "title": title,
                                "channel": channel,
                                "date": published_at,
                                "texte_candidat": candidate,
                                "requete": query,
                                "date_scan": datetime.now().isoformat()
                            })

                    self.stats["youtube_videos"] += len(items)

                time.sleep(1)

            except Exception as e:
                print(f"⚠️  Erreur YouTube scan ({query}): {e}")
                continue

        print(f"✅ YouTube: {len(results)} candidats extraits")
        return results

    def scan_telegram(self) -> List[Dict[str, Any]]:
        """Scan Telegram channels publics"""
        print("📱 Scan Telegram...")
        results = []

        api_id = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")

        if not api_id or not api_hash:
            print("⚠️  Clés Telegram API non configurées, skipping...")
            return results

        try:
            from telethon import TelegramClient
            from telethon.tl.types import Channel
        except ImportError:
            print("⚠️  telethon non installé, skipping Telegram...")
            return results

        channels = self.config.get("telegram_channels", [])

        try:
            client = TelegramClient('session_scanner', int(api_id), api_hash)

            async def scan():
                await client.start()

                for channel_name in channels:
                    try:
                        entity = await client.get_entity(channel_name)
                        if isinstance(entity, Channel):
                            messages = await client.get_messages(entity, limit=1000)

                            for msg in messages:
                                if msg.text:
                                    text_lower = msg.text.lower()
                                    if any(kw in text_lower for kw in ["prophète", "hadith", "rapporté"]):
                                        candidates = self.extract_hadith_candidates(msg.text)

                                        for candidate in candidates:
                                            results.append({
                                                "source": "telegram",
                                                "url": f"https://t.me/{channel_name}/{msg.id}",
                                                "channel": channel_name,
                                                "date": msg.date.isoformat() if msg.date else None,
                                                "texte_complet": msg.text[:500],
                                                "texte_candidat": candidate,
                                                "date_scan": datetime.now().isoformat()
                                            })

                            self.stats["telegram_messages"] += len(messages)

                    except Exception as e:
                        print(f"⚠️  Erreur Telegram channel {channel_name}: {e}")
                        continue

                await client.disconnect()

            import asyncio
            asyncio.run(scan())

        except Exception as e:
            print(f"⚠️  Erreur Telegram scan: {e}")

        print(f"✅ Telegram: {len(results)} candidats extraits")
        return results

    def scan_sites(self) -> List[Dict[str, Any]]:
        """Scan sites islamiques cibles"""
        print("🌐 Scan sites islamiques...")
        results = []

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
        }

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            print("⚠️  beautifulsoup4 non installé, skipping sites...")
            return results

        for site_url in SITES_CIBLES:
            try:
                response = requests.get(site_url, headers=headers, timeout=30)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    for paragraph in soup.find_all(['p', 'article', 'div', 'blockquote']):
                        text = paragraph.get_text(strip=True)
                        if len(text) >= 50:
                            candidates = self.extract_hadith_candidates(text)

                            for candidate in candidates:
                                results.append({
                                    "source": "site",
                                    "url": site_url,
                                    "texte_candidat": candidate,
                                    "contexte": text[:300],
                                    "date_scan": datetime.now().isoformat()
                                })

                    self.stats["sites_pages"] += 1

                time.sleep(2)

            except Exception as e:
                print(f"⚠️  Erreur site {site_url}: {e}")
                continue

        print(f"✅ Sites: {len(results)} candidats extraits")
        return results

    def detect_hadith(self, texte_candidat: str, blacklist: List[Dict]) -> Dict[str, Any]:
        """Détection par fuzzy matching"""
        try:
            from rapidfuzz import fuzz
        except ImportError:
            print("⚠️  rapidfuzz non installé, fuzzy matching désactivé")
            return {"alerte": False}

        if not texte_candidat or len(texte_candidat) < 10:
            return {"alerte": False}

        for entree in blacklist:
            texte_fr = entree.get("texte_fr", "")
            if not texte_fr:
                continue

            score = fuzz.partial_ratio(
                texte_candidat.lower(),
                texte_fr.lower()
            )

            if score >= 85:
                return {
                    "match": entree,
                    "score": score,
                    "alerte": True
                }

        return {"alerte": False}

    def verify_dorar(self, texte_ar: Optional[str]) -> Dict[str, Any]:
        """Vérification API Dorar"""
        if not texte_ar:
            return {"statut": "EN_ATTENTE"}

        base_url = os.getenv("DORAR_BASE_URL", "https://dorar.net/dorar_api.json")

        try:
            url = f"{base_url}?skey={requests.utils.quote(texte_ar)}"
            response = requests.get(url, timeout=30)
            time.sleep(2)

            if response.status_code == 200:
                data = response.json()
                result = data.get("ahadith", {}).get("result", [])

                if result:
                    hadith = result[0]
                    return {
                        "statut": "CONFIRME",
                        "grade": hadith.get("grade"),
                        "url_dorar": f"https://dorar.net/hadith/{hadith.get('id')}"
                    }

            return {"statut": "NON_TROUVE"}

        except Exception as e:
            print(f"⚠️  Erreur Dorar API: {e}")
            return {"statut": "ERREUR"}

    def check_database(self, texte_fr: str) -> Dict[str, Any]:
        """Vérification base de données locale"""
        if not self.db_path.exists():
            return {"statut": "ABSENT"}

        try:
            conn = sqlite3.connect(str(self.db_path))
            mots_cles = " ".join(texte_fr.split()[:5])

            cursor = conn.execute(
                "SELECT id, zone_26 FROM hadiths WHERE zone_04 LIKE ?",
                (f"%{mots_cles}%",)
            )
            result = cursor.fetchone()

            conn.close()

            if result:
                hadith_id, grade = result
                if grade:
                    return {"statut": "EXISTANT", "id": hadith_id}
                return {"statut": "EXISTANT_SANS_GRADE", "id": hadith_id}

            return {"statut": "ABSENT"}

        except Exception as e:
            print(f"⚠️  Erreur base de données: {e}")
            return {"statut": "ERREUR"}

    def process_candidats(self, candidats: List[Dict[str, Any]]):
        """Traite les candidats détectés"""
        print(f"\n🔎 Analyse de {len(candidats)} candidats...")

        # Charger la blacklist existante
        blacklist_path = self.data_dir / "blacklist_hadiths_fr.json"
        existing_blacklist = []
        if blacklist_path.exists():
            with open(blacklist_path, "r", encoding="utf-8") as f:
                existing_blacklist = json.load(f)

        # Merge avec la blacklist manuelle
        all_blacklist = BLACKLIST_MANUELLE + existing_blacklist

        seen_texts = set()

        for candidat in candidats:
            texte = candidat.get("texte_candidat", "")
            if not texte or texte in seen_texts:
                continue

            seen_texts.add(texte)
            self.stats["candidats_detectes"] += 1

            # Vérification fuzzy matching
            detection = self.detect_hadith(texte, all_blacklist)

            if detection.get("alerte"):
                match = detection.get("match", {})

                # Vérification Dorar
                texte_ar = match.get("texte_ar")
                dorar_result = self.verify_dorar(texte_ar)

                if dorar_result.get("statut") == "CONFIRME":
                    self.stats["confirmes_dorar"] += 1
                elif dorar_result.get("statut") == "NON_TROUVE":
                    self.stats["non_trouves_dorar"] += 1

                # Vérification base
                db_result = self.check_database(texte)

                if db_result.get("statut") == "EXISTANT":
                    self.stats["deja_dans_base"] += 1
                elif db_result.get("statut") == "ABSENT":
                    self.stats["absents_base"] += 1

                # Compter par courant
                for courant in match.get("courants_concernes", ["Général"]):
                    if courant in self.stats["courants"]:
                        self.stats["courants"][courant] += 1

                entry = {
                    "id": len(self.blacklist) + 1,
                    "texte_fr": match.get("texte_fr", texte),
                    "texte_ar": texte_ar,
                    "grade": match.get("grade", "non_verifie"),
                    "savant": match.get("savant", "Non identifié"),
                    "reference": match.get("reference"),
                    "source_detection": candidat.get("source", "inconnu"),
                    "source_url": candidat.get("url"),
                    "frequence_detection": 1,
                    "statut_dorar": dorar_result.get("statut", "EN_ATTENTE"),
                    "url_dorar": dorar_result.get("url_dorar"),
                    "statut_base": db_result.get("statut", "ABSENT"),
                    "hadith_id_base": db_result.get("id"),
                    "courants_concernes": match.get("courants_concernes", ["Général"]),
                    "pratique_justifiee": match.get("pratique_justifiee"),
                    "refutation_savant": match.get("refutation_savant"),
                    "date_detection": datetime.now().isoformat()
                }

                self.blacklist.append(entry)

    def add_manual_blacklist(self):
        """Ajoute la blacklist manuelle"""
        print(f"\n📚 Intégration blacklist manuelle ({len(BLACKLIST_MANUELLE)} entrées)...")

        for i, entry in enumerate(BLACKLIST_MANUELLE):
            # Vérification Dorar
            texte_ar = entry.get("texte_ar")
            dorar_result = self.verify_dorar(texte_ar)

            if dorar_result.get("statut") == "CONFIRME":
                self.stats["confirmes_dorar"] += 1
            elif dorar_result.get("statut") == "NON_TROUVE":
                self.stats["non_trouves_dorar"] += 1

            # Vérification base
            db_result = self.check_database(entry.get("texte_fr", ""))

            if db_result.get("statut") == "EXISTANT":
                self.stats["deja_dans_base"] += 1
            elif db_result.get("statut") == "ABSENT":
                self.stats["absents_base"] += 1

            # Compter par courant
            for courant in entry.get("courants_concernes", ["Général"]):
                if courant in self.stats["courants"]:
                    self.stats["courants"][courant] += 1

            blacklist_entry = {
                "id": len(self.blacklist) + 1,
                "texte_fr": entry.get("texte_fr"),
                "texte_ar": entry.get("texte_ar"),
                "grade": entry.get("grade"),
                "savant": entry.get("savant"),
                "reference": entry.get("reference"),
                "source_detection": "manuel",
                "source_url": None,
                "frequence_detection": 1,
                "statut_dorar": dorar_result.get("statut", "EN_ATTENTE"),
                "url_dorar": dorar_result.get("url_dorar"),
                "statut_base": db_result.get("statut", "ABSENT"),
                "hadith_id_base": db_result.get("id"),
                "courants_concernes": entry.get("courants_concernes", ["Général"]),
                "pratique_justifiee": entry.get("pratique_justifiee"),
                "refutation_savant": entry.get("refutation_savant"),
                "date_detection": datetime.now().isoformat()
            }

            self.blacklist.append(blacklist_entry)

    def save_results(self):
        """Sauvegarde les résultats"""
        output_path = self.data_dir / "blacklist_hadiths_fr.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.blacklist, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Résultats sauvegardés: {output_path}")
        print(f"   Total entrées blacklist: {len(self.blacklist)}")

    def print_report(self):
        """Affiche le rapport terminal"""
        print("\n" + "=" * 50)
        print("║     RADAR DE LA SUNNA — AL-MĪZĀN        ║")
        print("=" * 50)
        print("SOURCES SCANNÉES")
        print(f"  Google Search API      : {self.stats['google_results']} résultats")
        print(f"  YouTube API            : {self.stats['youtube_videos']} vidéos")
        print(f"  Telegram               : {self.stats['telegram_messages']} messages")
        print(f"  Sites islamiques       : {self.stats['sites_pages']} pages")
        print(f"  Blacklist manuelle     : {self.stats['manual_entries']} entrées")
        print("-" * 50)
        print("RÉSULTATS")
        print(f"  Candidats détectés     : {self.stats['candidats_detectes']}")
        print(f"  Confirmés par Dorar    : {self.stats['confirmes_dorar']}")
        print(f"  Non trouvés sur Dorar  : {self.stats['non_trouves_dorar']}")
        print(f"  Déjà dans la base      : {self.stats['deja_dans_base']}")
        print(f"  Absents de la base     : {self.stats['absents_base']}")
        print("-" * 50)
        print("COURANTS IDENTIFIÉS")
        for courant, count in self.stats["courants"].items():
            print(f"  {courant:<20} : {count} hadiths")
        print("-" * 50)
        print(f"Fichier produit : data/blacklist_hadiths_fr.json")
        print("=" * 50)

    def run(self):
        """Exécute le scan complet"""
        print("\n🚀 Démarrage du Radar de la Sunna...")
        print(f"   Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 1. Ajouter la blacklist manuelle d'abord
        self.add_manual_blacklist()

        # 2. Scanner les sources
        all_candidats = []

        # Google
        candidats_google = self.scan_google()
        all_candidats.extend(candidats_google)

        # YouTube
        candidats_youtube = self.scan_youtube()
        all_candidats.extend(candidats_youtube)

        # Telegram
        candidats_telegram = self.scan_telegram()
        all_candidats.extend(candidats_telegram)

        # Sites
        candidats_sites = self.scan_sites()
        all_candidats.extend(candidats_sites)

        # 3. Traiter les candidats
        self.process_candidats(all_candidats)

        # 4. Sauvegarder
        self.save_results()

        # 5. Rapport
        self.print_report()

        return self.blacklist


def main():
    """Point d'entrée principal"""
    scanner = ScannerInternet()
    scanner.run()


if __name__ == "__main__":
    main()
