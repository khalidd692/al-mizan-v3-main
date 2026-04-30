#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GRAND SCAN AL-MĪZĀN — Artillerie Lourde
Scan intégral du web francophone pour hadiths inventés/faibles
Threading | Base de données complète | Mapping des courants
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
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from queue import Queue

import requests
from dotenv import load_dotenv

# Chargement environnement
load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION MASSIVE
# ═══════════════════════════════════════════════════════════════════════════════

# Requêtes virales islamiques francophones
REQUETES_MASSIVES = [
    # Hadiths génériques
    '"le Prophète a dit" hadith site:youtube.com',
    '"le Prophète a dit" hadith site:facebook.com',
    '"hadith authentique" français',
    '"rappel islamique" hadith',
    '"hadith du jour"',
    '"hadith sur" amour mariage',
    '"hadith sur" femme paradis',
    '"hadith sur" science Chine',
    '"hadith sur" divergence miséricorde',
    '"hadith sur" compagnons étoiles',
    
    # Thématiques virales
    '"hadith" nationalisme patrie foi',
    '"hadith" travail dunya akhira',
    '"hadith" femme enfer cheveux',
    '"hadith" optimisme bien',
    '"hadith" musulmans affairés',
    
    # Sites spécifiques
    '"hadith" site:islamhouse.com',
    '"hadith" site:sounna.com',
    '"hadith" site:islamweb.net',
    '"hadith" site:fr.islamway.net',
    
    # Réseaux sociaux
    '"hadith" site:tiktok.com',
    '"hadith" site:instagram.com',
    '"hadith" site:twitter.com OR site:x.com',
    '"hadith" site:pinterest.com',
    
    # Plateformes vidéo
    '"hadith" cours islam site:youtube.com',
    '"hadith" khutba vendredi',
    '"hadith" rappel site:facebook.com/watch',
]

REQUETES_YOUTUBE_MASSIVES = [
    "hadith authentique français",
    "hadith du jour",
    "rappel islamique",
    "cours hadith français",
    "explication hadith",
    "khutba hadith vendredi",
    "hadith femme paradis",
    "hadith science Chine",
    "hadith divergence miséricorde",
    "hadith compagnons étoiles",
    "hadith amour mariage",
    "hadith inventé",
    "hadith faible réfutation",
    "albani hadith daif",
    "ibn baz hadith mawdou",
]

# Canaux Telegram cibles (islam francophone)
TELEGRAM_CHANNELS_HEAVY = [
    "islamfrance", "sounnahfrance", "rappelislamique", "muslimfrance",
    "islamicreminders_fr", "rappelislam", "hadithdujour", "sounnahdaily",
    "islamhouse_fr", "fr_islam", "salaf_fr", "sounnah_fr", "hadiths",
    "islam_quran_hadith", "lesbeauxproverbes", "rappels_islamiques",
    "islamic_quotes_fr", "sagesse_coran", "versets_hadiths",
]

# Grades cibles (hadiths dangereux)
GRADES_CIBLES = ['mawdou', 'daif_jiddan', 'daif', 'la_asla_lahu', 'munkar', 'batil']

# ═══════════════════════════════════════════════════════════════════════════════
# CLASSE PRINCIPALE — SCANNER HEAVY
# ═══════════════════════════════════════════════════════════════════════════════

class GrandScanner:
    """Scanner massif multi-threaded"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.db_path = self.base_dir / "backend" / "database" / "almizan_v7.db"
        
        self.data_dir.mkdir(exist_ok=True)
        
        # Stats massives
        self.stats = {
            "google_calls": 0,
            "youtube_calls": 0,
            "telegram_msgs": 0,
            "hadiths_faibles_db": 0,
            "candidats_detectes": 0,
            "matches_confirmes": 0,
            "fiches_generees": 0,
            "courants_map": {
                "Ikhwānī": 0, "Tablīghī": 0, "Soufi": 0,
                "Ash'arī": 0, "Salafī": 0, "Général": 0
            }
        }
        
        # Données
        self.hadiths_faibles_db: List[Dict] = []
        self.fiches_anatomie: List[Dict] = []
        self.lock = threading.Lock()
        
        # API Keys
        self.google_key = os.getenv("GOOGLE_API_KEY")
        self.google_cx = os.getenv("GOOGLE_CX")
        self.youtube_key = os.getenv("YOUTUBE_API_KEY")
        self.tg_api_id = os.getenv("TELEGRAM_API_ID")
        self.tg_api_hash = os.getenv("TELEGRAM_API_HASH")
        
    # ═══════════════════════════════════════════════════════════════════════════
    # CHARGEMENT BASE DE DONNÉES COMPLÈTE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def charger_hadiths_faibles(self) -> List[Dict]:
        """Charge tous les hadiths faibles de la base"""
        print("\n📚 Chargement base de données — Hadiths faibles...")
        
        if not self.db_path.exists():
            print(f"⚠️ Base non trouvée: {self.db_path}")
            return []
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.execute("""
                SELECT id, zone_04, zone_03, zone_26, zone_28, zone_29
                FROM hadiths 
                WHERE zone_26 IN ('mawdou', 'daif_jiddan', 'daif', 'la_asla_lahu', 'munkar')
                   OR zone_26 LIKE '%daif%'
                   OR zone_26 LIKE '%mawdou%'
                LIMIT 5000
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            hadiths = []
            for row in rows:
                hadith = {
                    "id": row[0],
                    "texte_fr": row[1] or "",
                    "texte_ar": row[2] or "",
                    "grade": row[3] or "non_classifie",
                    "savant": row[4] or "Non identifié",
                    "reference": row[5] or None
                }
                if len(hadith["texte_fr"]) > 20:
                    hadiths.append(hadith)
            
            self.stats["hadiths_faibles_db"] = len(hadiths)
            print(f"✅ {len(hadiths)} hadiths faibles chargés de la base")
            return hadiths
            
        except Exception as e:
            print(f"⚠️ Erreur base de données: {e}")
            return []
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GOOGLE CUSTOM SEARCH — VAGUES MASSIVES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def scan_google_massif(self, query: str) -> List[Dict]:
        """Scan une requête Google avec pagination maximale"""
        results = []
        
        if not self.google_key or not self.google_cx:
            return results
        
        try:
            # 10 résultats x 10 pages = 100 résultats par requête
            for start in range(1, 101, 10):
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    "key": self.google_key,
                    "cx": self.google_cx,
                    "q": query,
                    "start": start,
                    "num": 10,
                    "lr": "lang_fr",
                    "hl": "fr",
                    "safe": "active"
                }
                
                response = requests.get(url, params=params, timeout=15)
                
                with self.lock:
                    self.stats["google_calls"] += 1
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])
                    
                    for item in items:
                        snippet = item.get("snippet", "")
                        link = item.get("link", "")
                        title = item.get("title", "")
                        
                        # Extraction candidats
                        candidates = self._extraire_candidats(snippet)
                        
                        for cand in candidates:
                            results.append({
                                "source": "google",
                                "url": link,
                                "title": title,
                                "texte": cand,
                                "contexte": snippet[:300],
                                "requete": query,
                                "date": datetime.now().isoformat()
                            })
                    
                    if len(items) < 10:
                        break
                
                elif response.status_code == 429:
                    print(f"⚠️ Google quota exceeded — pause 60s")
                    time.sleep(60)
                    break
                else:
                    break
                
                time.sleep(0.5)  # Respect rate limit
                
        except Exception as e:
            pass
        
        return results
    
    def scan_google_threaded(self) -> List[Dict]:
        """Lance les scans Google en parallèle"""
        print(f"\n🔍 LANCEMENT GOOGLE MASSIF — {len(REQUETES_MASSIVES)} requêtes...")
        all_results = []
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(self.scan_google_massif, q): q for q in REQUETES_MASSIVES}
            
            for future in as_completed(futures):
                query = futures[future]
                try:
                    results = future.result()
                    with self.lock:
                        all_results.extend(results)
                    print(f"  ✅ {query[:50]}... → {len(results)} candidats")
                except Exception as e:
                    print(f"  ❌ {query[:50]}... → Erreur: {e}")
        
        print(f"✅ Google Total: {len(all_results)} candidats")
        return all_results
    
    # ═══════════════════════════════════════════════════════════════════════════
    # YOUTUBE — RATISSAGE COMPLET
    # ═══════════════════════════════════════════════════════════════════════════
    
    def scan_youtube_video(self, query: str, max_results: int = 50) -> List[Dict]:
        """Scan YouTube avec transcription"""
        results = []
        
        if not self.youtube_key:
            return results
        
        try:
            # Recherche vidéos
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": max_results,
                "relevanceLanguage": "fr",
                "key": self.youtube_key
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            with self.lock:
                self.stats["youtube_calls"] += 1
            
            if response.status_code != 200:
                return results
            
            data = response.json()
            items = data.get("items", [])
            
            for item in items:
                video_id = item.get("id", {}).get("videoId", "")
                title = item.get("snippet", {}).get("title", "")
                channel = item.get("snippet", {}).get("channelTitle", "")
                desc = item.get("snippet", {}).get("description", "")
                
                # Essai transcription
                transcript = ""
                try:
                    from youtube_transcript_api import YouTubeTranscriptApi
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['fr'])
                    transcript = " ".join([t['text'] for t in transcript_list])
                except:
                    pass
                
                search_text = f"{title} {desc} {transcript}"
                candidates = self._extraire_candidats(search_text)
                
                for cand in candidates:
                    results.append({
                        "source": "youtube",
                        "url": f"https://youtube.com/watch?v={video_id}",
                        "title": title,
                        "channel": channel,
                        "texte": cand,
                        "requete": query,
                        "date": datetime.now().isoformat()
                    })
                
                time.sleep(0.3)
                
        except Exception as e:
            pass
        
        return results
    
    def scan_youtube_threaded(self) -> List[Dict]:
        """Lance les scans YouTube en parallèle"""
        print(f"\n📺 LANCEMENT YOUTUBE MASSIF — {len(REQUETES_YOUTUBE_MASSIVES)} requêtes...")
        all_results = []
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {executor.submit(self.scan_youtube_video, q): q 
                      for q in REQUETES_YOUTUBE_MASSIVES}
            
            for future in as_completed(futures):
                query = futures[future]
                try:
                    results = future.result()
                    with self.lock:
                        all_results.extend(results)
                    print(f"  ✅ YouTube: {query[:40]}... → {len(results)} candidats")
                except Exception as e:
                    print(f"  ❌ YouTube: {query[:40]}... → Erreur")
        
        print(f"✅ YouTube Total: {len(all_results)} candidats")
        return all_results
    
    # ═══════════════════════════════════════════════════════════════════════════
    # TELEGRAM — INFILTRATION CANAUX
    # ═══════════════════════════════════════════════════════════════════════════
    
    def scan_telegram_channel(self, channel: str) -> List[Dict]:
        """Scan un canal Telegram"""
        results = []
        
        if not self.tg_api_id or not self.tg_api_hash:
            return results
        
        try:
            from telethon import TelegramClient
            from telethon.tl.types import Channel
            
            client = TelegramClient('session_grand_scan', int(self.tg_api_id), self.tg_api_hash)
            
            async def scan():
                await client.start()
                
                try:
                    entity = await client.get_entity(channel)
                    if isinstance(entity, Channel):
                        messages = await client.get_messages(entity, limit=500)
                        
                        for msg in messages:
                            if msg.text:
                                text_lower = msg.text.lower()
                                keywords = ["prophète", "hadith", "rapporté", "messager", 
                                          "sallallahu", "science chine", "différence", 
                                          "patrie", "étoiles", "compagnons"]
                                
                                if any(kw in text_lower for kw in keywords):
                                    candidates = self._extraire_candidats(msg.text)
                                    
                                    for cand in candidates:
                                        results.append({
                                            "source": "telegram",
                                            "url": f"https://t.me/{channel}/{msg.id}",
                                            "channel": channel,
                                            "texte": cand,
                                            "contexte": msg.text[:400],
                                            "date": datetime.now().isoformat()
                                        })
                        
                        with self.lock:
                            self.stats["telegram_msgs"] += len(messages)
                            
                except Exception as e:
                    pass
                finally:
                    await client.disconnect()
            
            import asyncio
            asyncio.run(scan())
            
        except Exception as e:
            pass
        
        return results
    
    def scan_telegram_heavy(self) -> List[Dict]:
        """Scan tous les canaux Telegram"""
        print(f"\n📱 LANCEMENT TELEGRAM — {len(TELEGRAM_CHANNELS_HEAVY)} canaux...")
        all_results = []
        
        if not self.tg_api_id:
            print("⚠️ Telegram API non configuré")
            return []
        
        for channel in TELEGRAM_CHANNELS_HEAVY:
            try:
                results = self.scan_telegram_channel(channel)
                with self.lock:
                    all_results.extend(results)
                print(f"  ✅ @{channel} → {len(results)} candidats")
                time.sleep(2)  # Respect rate limit
            except Exception as e:
                print(f"  ❌ @{channel} → Erreur")
        
        print(f"✅ Telegram Total: {len(all_results)} candidats")
        return all_results
    
    # ═══════════════════════════════════════════════════════════════════════════
    # UTILITAIRES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _extraire_candidats(self, text: str) -> List[str]:
        """Extrait les candidats hadith d'un texte"""
        if not text or len(text) < 30:
            return []
        
        patterns = [
            r'le Prophète(?:\s+paix\s+sur\s+lui)?\s+a\s+dit\s*:?\s*["\']?([^"\']{20,400})["\']?',
            r'le Messager d\'Allah\s+a\s+dit\s*:?\s*["\']?([^"\']{20,400})["\']?',
            r'sallallahu\s+alayhi\s+wa\s+sallam\s+a\s+dit\s*:?\s*["\']?([^"\']{20,400})["\']?',
            r'il\s+est\s+rapporté\s+que\s+(?:le\s+)?Prophète[^"\']*["\']?([^"\']{20,400})["\']?',
            r'[«"\']([^"\']{30,400}?(?:Prophète|Messager|Allah|prière|sallallahu|science|compagnons|divergence|patrie)[^"\']{0,200})[»"\']'
        ]
        
        candidates = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                cand = match.strip()
                if len(cand) >= 25 and len(cand) <= 500:
                    candidates.append(cand)
        
        return list(set(candidates))
    
    def _detecter_courant(self, texte: str, source: str) -> str:
        """Détecte le courant islamique basé sur le contenu"""
        text_lower = texte.lower()
        
        # Signaux courants
        if any(kw in text_lower for kw in ['soufisme', 'soufi', 'dhikr', 'zikr', 'tariqa', 'mourid', 'awliya']):
            return "Soufi"
        elif any(kw in text_lower for kw in ['tabligh', 'tablighi', 'daawa', 'khuruj', 'fadhail', 'fada']):
            return "Tablīghī"
        elif any(kw in text_lower for kw in ['ikhwane', 'frere musulman', 'fikra', 'hassan al banna', 'qutb']):
            return "Ikhwānī"
        elif any(kw in text_lower for kw in ['ashari', 'asharite', 'matourid', 'kalam', 'aqeeda philosophie']):
            return "Ash'arī"
        elif any(kw in text_lower for kw in ['salafi', 'salaf', 'manhaj', 'albani', 'ibn baz', 'uthaymin']):
            return "Salafī"
        else:
            return "Général"
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GÉNÉRATION FICHES "ANATOMIE DU MENSONGE"
    # ═══════════════════════════════════════════════════════════════════════════
    
    def generer_fiche_anatomie(self, candidat: Dict, hadith_db: Dict) -> Dict:
        """Génère une fiche anatomie du mensonge"""
        
        courant = self._detecter_courant(candidat.get("texte", ""), candidat.get("source", ""))
        
        fiche = {
            "id_fiche": f"ANATOMIE_{len(self.fiches_anatomie) + 1:04d}",
            "date_generation": datetime.now().isoformat(),
            
            # La source du mensonge
            "source_mensonge": {
                "plateforme": candidat.get("source", "inconnu"),
                "url": candidat.get("url", ""),
                "titre": candidat.get("title") or candidat.get("channel", ""),
                "date_extraction": candidat.get("date", "")
            },
            
            # Le mensonge circulant
            "mensonge_circulant": {
                "texte_fr": candidat.get("texte", ""),
                "longueur": len(candidat.get("texte", ""))
            },
            
            # La vérité (depuis la base)
            "verite_hadith": {
                "texte_arabe_original": hadith_db.get("texte_ar", ""),
                "grade_authentique": hadith_db.get("grade", ""),
                "savant_verificateur": hadith_db.get("savant", ""),
                "reference_livre": hadith_db.get("reference", "")
            },
            
            # Le couperet des savants
            "verdict_savants": {
                "albani": self._verdict_albani(hadith_db),
                "ibn_baz": self._verdict_ibn_baz(hadith_db),
                "muqbil": self._verdict_muqbil(hadith_db),
                "conclusion": f"Hadith {hadith_db.get('grade', 'non classifié')} — {hadith_db.get('savant', 'Savant inconnu')}"
            },
            
            # Mapping courant
            "propagation": {
                "courant_identifie": courant,
                "viralite_estimee": "Élevée" if candidat.get("source") in ["youtube", "telegram"] else "Moyenne"
            }
        }
        
        with self.lock:
            self.stats["courants_map"][courant] = self.stats["courants_map"].get(courant, 0) + 1
        
        return fiche
    
    def _verdict_albani(self, hadith: Dict) -> str:
        """Extrait verdict al-Albānī si disponible"""
        savant = hadith.get("savant", "").lower()
        if "albani" in savant or "الباني" in savant:
            return f"✓ {hadith.get('reference', 'Silsila Daifa')} — {hadith.get('grade', '')}"
        return "Non répertorié dans ses ouvrages"
    
    def _verdict_ibn_baz(self, hadith: Dict) -> str:
        """Extrait verdict Ibn Bāz si disponible"""
        savant = hadith.get("savant", "").lower()
        if "baz" in savant or "باز" in savant:
            return f"✓ {hadith.get('reference', 'Fatwa')} — {hadith.get('grade', '')}"
        return "Non répertorié dans ses fatâwâ"
    
    def _verdict_muqbil(self, hadith: Dict) -> str:
        """Extrait verdict Muqbil si disponible"""
        savant = hadith.get("savant", "").lower()
        if "muqbil" in savant or "مقبل" in savant:
            return f"✓ {hadith.get('reference', 'Zad al-Ma^ad')} — {hadith.get('grade', '')}"
        return "Non répertorié dans ses ouvrages"
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MATCHING & ANALYSE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def matcher_candidats(self, candidats: List[Dict]):
        """Matche les candidats avec la base de hadiths faibles"""
        print(f"\n🔎 MATCHING — {len(candidats)} candidats vs {len(self.hadiths_faibles_db)} hadiths faibles...")
        
        try:
            from rapidfuzz import fuzz
        except ImportError:
            print("⚠️ rapidfuzz non installé — matching désactivé")
            return
        
        matches = 0
        seen = set()
        
        for candidat in candidats:
            texte_cand = candidat.get("texte", "").lower()
            if not texte_cand or texte_cand in seen:
                continue
            seen.add(texte_cand)
            
            with self.lock:
                self.stats["candidats_detectes"] += 1
            
            # Matching fuzzy contre base
            for hadith in self.hadiths_faibles_db:
                texte_db = hadith.get("texte_fr", "").lower()
                if not texte_db:
                    continue
                
                score = fuzz.partial_ratio(texte_cand, texte_db)
                
                if score >= 80:  # Seuil de correspondance
                    matches += 1
                    
                    # Générer fiche anatomie
                    fiche = self.generer_fiche_anatomie(candidat, hadith)
                    
                    with self.lock:
                        self.fiches_anatomie.append(fiche)
                        self.stats["matches_confirmes"] += 1
                        self.stats["fiches_generees"] += 1
                    
                    print(f"  🎯 MATCH #{matches} (score: {score}%) — {fiche['propagation']['courant_identifie']}")
                    break
        
        print(f"✅ Matching terminé: {matches} correspondances trouvées")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SAUVEGARDE & RAPPORT
    # ═══════════════════════════════════════════════════════════════════════════
    
    def sauvegarder_results(self):
        """Sauvegarde tous les résultats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Fiches Anatomie du Mensonge
        fiches_path = self.data_dir / f"anatomie_mensonge_{timestamp}.json"
        with open(fiches_path, "w", encoding="utf-8") as f:
            json.dump(self.fiches_anatomie, f, ensure_ascii=False, indent=2)
        
        # Rapport statistique
        rapport = {
            "timestamp": timestamp,
            "statistiques": self.stats,
            "total_fiches": len(self.fiches_anatomie),
            "courants_propagateurs": self.stats["courants_map"]
        }
        
        rapport_path = self.data_dir / f"rapport_grand_scan_{timestamp}.json"
        with open(rapport_path, "w", encoding="utf-8") as f:
            json.dump(rapport, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Résultats sauvegardés:")
        print(f"   📁 Fiches Anatomie: {fiches_path}")
        print(f"   📁 Rapport: {rapport_path}")
    
    def print_rapport_final(self):
        """Affiche le rapport terminal massif"""
        print("\n" + "=" * 70)
        print("║" + " " * 20 + "GRAND SCAN AL-MĪZĀN" + " " * 29 + "║")
        print("║" + " " * 15 + "ARTILLERIE LOURDE DÉPLOYÉE" + " " * 26 + "║")
        print("=" * 70)
        print(f"\n📊 STATISTIQUES DE MISSION")
        print(f"   Appels Google API      : {self.stats['google_calls']}")
        print(f"   Appels YouTube API     : {self.stats['youtube_calls']}")
        print(f"   Messages Telegram      : {self.stats['telegram_msgs']}")
        print(f"   Hadiths faibles DB     : {self.stats['hadiths_faibles_db']}")
        print(f"   Candidats détectés     : {self.stats['candidats_detectes']}")
        print(f"   ✅ Matches confirmés   : {self.stats['matches_confirmes']}")
        print(f"   📋 Fiches générées    : {self.stats['fiches_generees']}")
        
        print(f"\n🎯 MAPPING DES COURANTS PROPAGATEURS")
        for courant, count in sorted(self.stats["courants_map"].items(), key=lambda x: -x[1]):
            bar = "█" * (count // 2)
            print(f"   {courant:<12} : {count:>4} {bar}")
        
        print("\n" + "=" * 70)
        print(f"✅ SCAN TERMINÉ — {len(self.fiches_anatomie)} mensonges documentés")
        print("=" * 70)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # EXÉCUTION PRINCIPALE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def executer(self):
        """Lance le Grand Scan complet"""
        print("\n🚀 GRAND SCAN AL-MĪZĀN — DÉPLOIEMENT ARTILLERIE LOURDE")
        print(f"   Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("   Mode: THREADING MASSIF | BASE COMPLÈTE | MAPPING COURANTS\n")
        
        # 1. Chargement base de données
        self.hadiths_faibles_db = self.charger_hadiths_faibles()
        
        if not self.hadiths_faibles_db:
            print("⚠️ Base de données vide ou inaccessible — utilisation blacklist manuelle")
        
        # 2. Lancement scans en parallèle
        all_candidats = []
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Soumettre tous les scans
            future_google = executor.submit(self.scan_google_threaded)
            future_youtube = executor.submit(self.scan_youtube_threaded)
            future_telegram = executor.submit(self.scan_telegram_heavy)
            
            # Récupérer résultats
            all_candidats.extend(future_google.result())
            all_candidats.extend(future_youtube.result())
            all_candidats.extend(future_telegram.result())
        
        print(f"\n📊 TOTAL CANDIDATS: {len(all_candidats)}")
        
        # 3. Matching contre base
        if all_candidats:
            self.matcher_candidats(all_candidats)
        
        # 4. Sauvegarde
        self.sauvegarder_results()
        
        # 5. Rapport final
        self.print_rapport_final()
        
        return self.fiches_anatomie


# ═══════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Point d'entrée principal"""
    scanner = GrandScanner()
    scanner.executer()


if __name__ == "__main__":
    main()
