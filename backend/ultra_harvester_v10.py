#!/usr/bin/env python3
"""
ULTRA HARVESTER V10 - EXTRACTION MASSIVE MULTI-SOURCES
Objectif : 150,000+ hadiths TOUS GRADES confondus
Version corrigée sans emojis, avec sources alternatives
"""

import sqlite3
import requests
import hashlib
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import re
from bs4 import BeautifulSoup

# Configuration logging (sans emojis pour Windows)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend/ultra_harvest_v10.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltraHarvesterV10:
    """Harvester massif multi-sources avec TOUS les grades"""
    
    def __init__(self, db_path: str = "backend/database/almizan_v7.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'ar,en;q=0.9',
            'Referer': 'https://dorar.net/'
        })
        
        # Compteurs
        self.stats = {
            'total_processed': 0,
            'total_inserted': 0,
            'total_duplicates': 0,
            'by_source': {},
            'by_grade': {},
            'errors': 0
        }
        
        # Mapping des grades COMPLETS
        self.grade_mapping = {
            # Sahih
            'صحيح': 'Sahih',
            'sahih': 'Sahih',
            'صحيح لغيره': 'Sahih li-Ghayrihi',
            'صحيح الإسناد': 'Sahih al-Isnad',
            
            # Hasan
            'حسن': 'Hasan',
            'hasan': 'Hasan',
            'حسن لغيره': 'Hasan li-Ghayrihi',
            'حسن صحيح': 'Hasan Sahih',
            'حسن الإسناد': 'Hasan al-Isnad',
            
            # Da'if (TOUS)
            'ضعيف': 'Da\'if',
            'da\'if': 'Da\'if',
            'daif': 'Da\'if',
            'ضعيف جدا': 'Da\'if Jiddan',
            'ضعيف جداً': 'Da\'if Jiddan',
            'ضعيف الإسناد': 'Da\'if al-Isnad',
            
            # Très faibles
            'منكر': 'Munkar',
            'munkar': 'Munkar',
            'شاذ': 'Shaadh',
            'متروك': 'Matruk',
            'matruk': 'Matruk',
            
            # Forgés (badge_alerte=1)
            'موضوع': 'Mawdu\'',
            'mawdu': 'Mawdu\'',
            'باطل': 'Batil',
            'batil': 'Batil',
            'موضوع بلا شك': 'Mawdu\'',
            
            # Autres
            'لا أصل له': 'La Asl Lahu',
            'لا يصح': 'La Yasihh',
            'غير محفوظ': 'Ghayr Mahfudh'
        }
        
        self._init_db()
    
    def _init_db(self):
        """Initialise la connexion DB"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logger.info(f"[OK] Connexion DB etablie: {self.db_path}")
        except Exception as e:
            logger.error(f"[ERREUR] Connexion DB: {e}")
            raise
    
    def _compute_sha256(self, text: str) -> str:
        """Calcule SHA256 pour détecter doublons"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def _is_fabricated(self, grade: str) -> bool:
        """Détecte si le hadith est forgé (badge_alerte=1)"""
        if not grade:
            return False
        fabricated_keywords = ['موضوع', 'mawdu', 'باطل', 'batil']
        return any(kw in grade.lower() for kw in fabricated_keywords)
    
    def _normalize_grade(self, raw_grade: str) -> Tuple[str, str]:
        """Normalise le grade et retourne (grade_primaire, grade_albani)"""
        if not raw_grade:
            return 'Non classé', ''
        
        raw_lower = raw_grade.lower().strip()
        
        # Cherche correspondance exacte
        for ar_grade, en_grade in self.grade_mapping.items():
            if ar_grade in raw_lower:
                return en_grade, raw_grade
        
        # Si pas de correspondance, garde tel quel
        return raw_grade, raw_grade
    
    def _insert_hadith(self, hadith_data: Dict) -> bool:
        """Insère un hadith dans la DB"""
        try:
            matn_ar = hadith_data.get('matn_ar', '')
            if not matn_ar or len(matn_ar) < 10:
                return False
            
            sha256_hash = self._compute_sha256(matn_ar)
            
            # Vérification doublon
            self.cursor.execute(
                "SELECT id FROM entries WHERE matn_ar_hash = ?",
                (sha256_hash,)
            )
            if self.cursor.fetchone():
                self.stats['total_duplicates'] += 1
                return False
            
            # Normalisation grade
            raw_grade = hadith_data.get('grade', '')
            grade_primaire, grade_albani = self._normalize_grade(raw_grade)
            
            # Badge alerte si forgé
            badge_alerte = 1 if self._is_fabricated(raw_grade) else 0
            
            # Insertion
            self.cursor.execute("""
                INSERT INTO entries (
                    external_id, source, livre, numero,
                    matn_ar, matn_fr, matn_ar_hash,
                    grade_primaire, grade_albani, badge_alerte,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                hadith_data.get('external_id', ''),
                hadith_data.get('source', ''),
                hadith_data.get('livre', ''),
                hadith_data.get('numero', ''),
                matn_ar,
                hadith_data.get('matn_fr', ''),
                sha256_hash,
                grade_primaire,
                grade_albani,
                badge_alerte,
                datetime.now().isoformat()
            ))
            
            self.conn.commit()
            self.stats['total_inserted'] += 1
            
            # Stats par grade
            if grade_primaire not in self.stats['by_grade']:
                self.stats['by_grade'][grade_primaire] = 0
            self.stats['by_grade'][grade_primaire] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"[ERREUR] Insertion: {e}")
            self.stats['errors'] += 1
            return False
    
    def harvest_dorar_scraping(self):
        """Scraping direct de Dorar.net (toutes pages)"""
        logger.info("[DEBUT] Extraction Dorar.net par scraping...")
        source_name = 'dorar.net'
        
        if source_name not in self.stats['by_source']:
            self.stats['by_source'][source_name] = 0
        
        # Recherche générique pour obtenir tous les hadiths
        base_url = "https://dorar.net/hadith/search"
        
        # Différentes requêtes pour couvrir tous les grades
        search_queries = [
            {'q': 'صحيح', 'st': 'p'},  # Sahih
            {'q': 'حسن', 'st': 'p'},   # Hasan
            {'q': 'ضعيف', 'st': 'p'},  # Da'if
            {'q': 'منكر', 'st': 'p'},  # Munkar
            {'q': 'موضوع', 'st': 'p'}, # Mawdu'
        ]
        
        for query in search_queries:
            try:
                page = 1
                while page <= 100:  # Limite à 100 pages par requête
                    params = {**query, 'page': page}
                    response = self.session.get(base_url, params=params, timeout=30)
                    
                    if response.status_code != 200:
                        logger.warning(f"[WARN] Dorar page {page}: {response.status_code}")
                        break
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    hadith_cards = soup.find_all('div', class_='hadith-card')
                    
                    if not hadith_cards:
                        break
                    
                    for card in hadith_cards:
                        try:
                            self.stats['total_processed'] += 1
                            
                            # Extraction texte arabe
                            matn_div = card.find('div', class_='hadith-text')
                            if not matn_div:
                                continue
                            
                            matn_ar = matn_div.get_text(strip=True)
                            
                            # Extraction grade
                            grade_div = card.find('div', class_='grade')
                            grade = grade_div.get_text(strip=True) if grade_div else ''
                            
                            # Extraction source/livre
                            source_div = card.find('div', class_='source')
                            livre = source_div.get_text(strip=True) if source_div else ''
                            
                            # ID unique
                            hadith_id = card.get('data-id', f"dorar_{self.stats['total_processed']}")
                            
                            hadith_data = {
                                'external_id': f"dorar_{hadith_id}",
                                'source': source_name,
                                'livre': livre,
                                'numero': '',
                                'matn_ar': matn_ar,
                                'matn_fr': '',
                                'grade': grade
                            }
                            
                            if self._insert_hadith(hadith_data):
                                self.stats['by_source'][source_name] += 1
                            
                            if self.stats['total_processed'] % 500 == 0:
                                self._log_progress()
                        
                        except Exception as e:
                            logger.error(f"[ERREUR] Parsing hadith: {e}")
                            continue
                    
                    page += 1
                    time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"[ERREUR] Dorar query {query}: {e}")
                continue
    
    def harvest_hadithgading(self):
        """Extraction depuis hadithgading.com API"""
        logger.info("[DEBUT] Extraction hadithgading.com...")
        source_name = 'hadithgading.com'
        
        if source_name not in self.stats['by_source']:
            self.stats['by_source'][source_name] = 0
        
        try:
            # API endpoint
            base_url = "https://hadithgading.com/api/hadiths"
            page = 1
            
            while page <= 200:  # Limite à 200 pages
                params = {'page': page, 'per_page': 100}
                response = self.session.get(base_url, params=params, timeout=30)
                
                if response.status_code != 200:
                    break
                
                data = response.json()
                hadiths = data.get('data', [])
                
                if not hadiths:
                    break
                
                for hadith in hadiths:
                    self.stats['total_processed'] += 1
                    
                    hadith_data = {
                        'external_id': f"hadithgading_{hadith.get('id', '')}",
                        'source': source_name,
                        'livre': hadith.get('book', ''),
                        'numero': str(hadith.get('number', '')),
                        'matn_ar': hadith.get('arab', ''),
                        'matn_fr': '',
                        'grade': hadith.get('grade', '')
                    }
                    
                    if self._insert_hadith(hadith_data):
                        self.stats['by_source'][source_name] += 1
                    
                    if self.stats['total_processed'] % 500 == 0:
                        self._log_progress()
                
                page += 1
                time.sleep(0.5)
                
        except Exception as e:
            logger.error(f"[ERREUR] HadithGading: {e}")
    
    def harvest_sunnah_alternative(self):
        """Extraction alternative de sunnah.com (sans API key)"""
        logger.info("[DEBUT] Extraction sunnah.com (scraping)...")
        source_name = 'sunnah.com'
        
        if source_name not in self.stats['by_source']:
            self.stats['by_source'][source_name] = 0
        
        collections = ['bukhari', 'muslim', 'nasai', 'abudawud', 'tirmidhi', 'ibnmajah']
        
        for collection in collections:
            try:
                logger.info(f"  [INFO] Collection: {collection}")
                
                # Scraping des pages HTML
                for book_num in range(1, 100):  # Jusqu'à 100 livres par collection
                    url = f"https://sunnah.com/{collection}/{book_num}"
                    response = self.session.get(url, timeout=30)
                    
                    if response.status_code != 200:
                        break
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    hadith_divs = soup.find_all('div', class_='actualHadithContainer')
                    
                    for hadith_div in hadith_divs:
                        try:
                            self.stats['total_processed'] += 1
                            
                            # Texte arabe
                            arabic_div = hadith_div.find('div', class_='arabic_hadith_full')
                            if not arabic_div:
                                continue
                            
                            matn_ar = arabic_div.get_text(strip=True)
                            
                            # Numéro
                            hadith_num = hadith_div.get('id', '').replace('hadith', '')
                            
                            hadith_data = {
                                'external_id': f"sunnah_{collection}_{hadith_num}",
                                'source': source_name,
                                'livre': f"{collection} - Book {book_num}",
                                'numero': hadith_num,
                                'matn_ar': matn_ar,
                                'matn_fr': '',
                                'grade': 'Sahih'  # Collections Sahih par défaut
                            }
                            
                            if self._insert_hadith(hadith_data):
                                self.stats['by_source'][source_name] += 1
                            
                            if self.stats['total_processed'] % 500 == 0:
                                self._log_progress()
                        
                        except Exception as e:
                            continue
                    
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"[ERREUR] Sunnah {collection}: {e}")
                continue
    
    def _log_progress(self):
        """Log progression tous les 500 hadiths"""
        logger.info(f"""
========================================
PROGRESSION ULTRA HARVESTER V10
========================================
Traites    : {self.stats['total_processed']:>8}
Inseres    : {self.stats['total_inserted']:>8}
Doublons   : {self.stats['total_duplicates']:>8}
Erreurs    : {self.stats['errors']:>8}
========================================
PAR SOURCE:
""")
        for source, count in self.stats['by_source'].items():
            logger.info(f"  {source:<30} : {count:>8}")
        
        logger.info(f"""========================================
PAR GRADE (Top 10):
""")
        for grade, count in sorted(self.stats['by_grade'].items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"  {grade:<30} : {count:>8}")
        
        logger.info("========================================")
    
    def run(self):
        """Lance l'extraction massive"""
        logger.info("""
========================================
ULTRA HARVESTER V10 - DEMARRAGE
========================================
Objectif : 150,000+ hadiths TOUS GRADES
Mode     : EXTRACTION CONTINUE
========================================
""")
        
        start_time = time.time()
        
        try:
            # Source 1: Dorar.net (scraping)
            self.harvest_dorar_scraping()
            
            # Source 2: HadithGading
            self.harvest_hadithgading()
            
            # Source 3: Sunnah.com (scraping)
            self.harvest_sunnah_alternative()
            
            # Rapport final
            elapsed = time.time() - start_time
            logger.info(f"""
========================================
ULTRA HARVESTER V10 - RAPPORT FINAL
========================================
Duree totale : {elapsed/3600:.2f} heures
Traites      : {self.stats['total_processed']:>8}
Inseres      : {self.stats['total_inserted']:>8}
Doublons     : {self.stats['total_duplicates']:>8}
Erreurs      : {self.stats['errors']:>8}
========================================
SOURCES EXPLOITEES:
""")
            for source, count in self.stats['by_source'].items():
                logger.info(f"  {source:<30} : {count:>8}")
            
            logger.info(f"""========================================
GRADES COLLECTES:
""")
            for grade, count in sorted(self.stats['by_grade'].items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  {grade:<30} : {count:>8}")
            
            logger.info("========================================")
            
        except KeyboardInterrupt:
            logger.warning("\n[WARN] Interruption utilisateur - Sauvegarde en cours...")
            self._log_progress()
        except Exception as e:
            logger.error(f"[ERREUR] Fatale: {e}")
        finally:
            self.conn.close()
            logger.info("[OK] Connexion DB fermee")

if __name__ == "__main__":
    harvester = UltraHarvesterV10()
    harvester.run()