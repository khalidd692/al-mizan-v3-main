#!/usr/bin/env python3
"""
MEGA HARVESTER V9 - EXTRACTION MASSIVE MULTI-SOURCES
Objectif : 150,000+ hadiths TOUS GRADES confondus
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

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend/mega_harvest_v9.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MegaHarvesterV9:
    """Harvester massif multi-sources avec TOUS les grades"""
    
    def __init__(self, db_path: str = "backend/database/almizan_v7.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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
            
            # Hasan
            'حسن': 'Hasan',
            'hasan': 'Hasan',
            'حسن لغيره': 'Hasan li-Ghayrihi',
            'حسن صحيح': 'Hasan Sahih',
            
            # Da'if (TOUS)
            'ضعيف': 'Da\'if',
            'da\'if': 'Da\'if',
            'daif': 'Da\'if',
            'ضعيف جدا': 'Da\'if Jiddan',
            'ضعيف جداً': 'Da\'if Jiddan',
            
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
        
        # Sources API prioritaires
        self.api_sources = [
            {
                'name': 'sunnah.com',
                'base_url': 'https://api.sunnah.com/v1',
                'collections': [
                    'bukhari', 'muslim', 'nasai', 'abudawud', 'tirmidhi', 'ibnmajah',
                    'malik', 'ahmad', 'darimi', 'adab', 'bulugh', 'qudsi40', 'nawawi40'
                ]
            },
            {
                'name': 'hadeethenc.com',
                'base_url': 'https://hadeethenc.com/api/v1',
                'endpoint': '/hadeeths/list/'
            },
            {
                'name': 'dorar.net',
                'base_url': 'https://dorar.net/hadith/search',
                'method': 'scraping'
            },
            {
                'name': 'hadithgading.com',
                'base_url': 'https://hadithgading.com/api',
                'endpoint': '/hadiths'
            },
            {
                'name': 'jsdelivr-hadith-api',
                'base_url': 'https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1',
                'editions': ['ara-abudawud', 'ara-bukhari', 'ara-muslim', 'ara-nasai', 
                            'ara-tirmidhi', 'ara-ibnmajah', 'ara-malik', 'ara-ahmad']
            }
        ]
        
        self._init_db()
    
    def _init_db(self):
        """Initialise la connexion DB"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logger.info(f"✅ Connexion DB établie: {self.db_path}")
        except Exception as e:
            logger.error(f"❌ Erreur connexion DB: {e}")
            raise
    
    def _compute_sha256(self, text: str) -> str:
        """Calcule SHA256 pour détecter doublons"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def _is_fabricated(self, grade: str) -> bool:
        """Détecte si le hadith est forgé (badge_alerte=1)"""
        fabricated_keywords = ['موضوع', 'mawdu', 'باطل', 'batil', 'موضوع بلا شك']
        return any(kw in grade.lower() for kw in fabricated_keywords)
    
    def _normalize_grade(self, raw_grade: str) -> Tuple[str, str]:
        """
        Normalise le grade et retourne (grade_primaire, grade_albani)
        """
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
        """
        Insère un hadith dans la DB
        Retourne True si insertion réussie, False si doublon
        """
        try:
            # Calcul SHA256 sur matn_ar
            matn_ar = hadith_data.get('matn_ar', '')
            if not matn_ar:
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
            logger.error(f"❌ Erreur insertion: {e}")
            self.stats['errors'] += 1
            return False
    
    def harvest_sunnah_com(self):
        """Extrait TOUS les hadiths de sunnah.com API"""
        logger.info("🔄 Démarrage extraction sunnah.com...")
        source_name = 'sunnah.com'
        
        if source_name not in self.stats['by_source']:
            self.stats['by_source'][source_name] = 0
        
        for collection in self.api_sources[0]['collections']:
            try:
                logger.info(f"  📖 Collection: {collection}")
                
                # Récupère tous les livres de la collection
                url = f"https://api.sunnah.com/v1/collections/{collection}/books"
                response = self.session.get(url, timeout=30)
                
                if response.status_code != 200:
                    logger.warning(f"  ⚠️  Échec {collection}: {response.status_code}")
                    continue
                
                books = response.json().get('data', [])
                
                for book in books:
                    book_number = book.get('bookNumber')
                    logger.info(f"    📚 Livre {book_number}")
                    
                    # Récupère tous les hadiths du livre
                    hadith_url = f"https://api.sunnah.com/v1/collections/{collection}/books/{book_number}/hadiths"
                    hadith_response = self.session.get(hadith_url, timeout=30)
                    
                    if hadith_response.status_code != 200:
                        continue
                    
                    hadiths = hadith_response.json().get('data', [])
                    
                    for hadith in hadiths:
                        self.stats['total_processed'] += 1
                        
                        hadith_data = {
                            'external_id': f"sunnah_{collection}_{hadith.get('hadithNumber', '')}",
                            'source': source_name,
                            'livre': f"{collection} - Book {book_number}",
                            'numero': str(hadith.get('hadithNumber', '')),
                            'matn_ar': hadith.get('hadithArabic', ''),
                            'matn_fr': '',  # À compléter avec HadeethEnc
                            'grade': hadith.get('grade', '')
                        }
                        
                        if self._insert_hadith(hadith_data):
                            self.stats['by_source'][source_name] += 1
                        
                        # Rapport tous les 500
                        if self.stats['total_processed'] % 500 == 0:
                            self._log_progress()
                    
                    time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.error(f"❌ Erreur {collection}: {e}")
                continue
    
    def harvest_hadeethenc(self):
        """Extrait hadiths de HadeethEnc (arabe + français)"""
        logger.info("🔄 Démarrage extraction HadeethEnc...")
        source_name = 'hadeethenc.com'
        
        if source_name not in self.stats['by_source']:
            self.stats['by_source'][source_name] = 0
        
        try:
            # Arabe
            url_ar = "https://hadeethenc.com/api/v1/hadeeths/list/?language=ar&per_page=100"
            page = 1
            
            while True:
                response = self.session.get(f"{url_ar}&page={page}", timeout=30)
                if response.status_code != 200:
                    break
                
                data = response.json()
                hadiths = data.get('data', [])
                
                if not hadiths:
                    break
                
                for hadith in hadiths:
                    self.stats['total_processed'] += 1
                    
                    hadith_data = {
                        'external_id': f"hadeethenc_{hadith.get('id', '')}",
                        'source': source_name,
                        'livre': hadith.get('attribution', ''),
                        'numero': str(hadith.get('id', '')),
                        'matn_ar': hadith.get('hadeeth', ''),
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
            logger.error(f"❌ Erreur HadeethEnc: {e}")
    
    def harvest_jsdelivr_api(self):
        """Extrait hadiths de jsdelivr hadith-api"""
        logger.info("🔄 Démarrage extraction jsdelivr...")
        source_name = 'jsdelivr-hadith-api'
        
        if source_name not in self.stats['by_source']:
            self.stats['by_source'][source_name] = 0
        
        base_url = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1"
        editions = ['ara-abudawud', 'ara-bukhari', 'ara-muslim', 'ara-nasai',
                   'ara-tirmidhi', 'ara-ibnmajah', 'ara-malik', 'ara-ahmad']
        
        for edition in editions:
            try:
                logger.info(f"  📖 Édition: {edition}")
                
                # Récupère sections
                sections_url = f"{base_url}/editions/{edition}/sections.json"
                response = self.session.get(sections_url, timeout=30)
                
                if response.status_code != 200:
                    continue
                
                sections = response.json().get('data', [])
                
                for section in sections:
                    section_num = section.get('number')
                    
                    # Récupère hadiths de la section
                    hadith_url = f"{base_url}/editions/{edition}/sections/{section_num}.json"
                    hadith_response = self.session.get(hadith_url, timeout=30)
                    
                    if hadith_response.status_code != 200:
                        continue
                    
                    hadiths = hadith_response.json().get('hadiths', [])
                    
                    for hadith in hadiths:
                        self.stats['total_processed'] += 1
                        
                        hadith_data = {
                            'external_id': f"jsdelivr_{edition}_{hadith.get('hadithnumber', '')}",
                            'source': source_name,
                            'livre': edition.replace('ara-', '').title(),
                            'numero': str(hadith.get('hadithnumber', '')),
                            'matn_ar': hadith.get('text', ''),
                            'matn_fr': '',
                            'grade': hadith.get('grades', [{}])[0].get('grade', '') if hadith.get('grades') else ''
                        }
                        
                        if self._insert_hadith(hadith_data):
                            self.stats['by_source'][source_name] += 1
                        
                        if self.stats['total_processed'] % 500 == 0:
                            self._log_progress()
                    
                    time.sleep(0.3)
                
            except Exception as e:
                logger.error(f"❌ Erreur {edition}: {e}")
                continue
    
    def _log_progress(self):
        """Log progression tous les 500 hadiths"""
        logger.info(f"""
╔══════════════════════════════════════════════════════════════╗
║  PROGRESSION MEGA HARVESTER V9                               ║
╠══════════════════════════════════════════════════════════════╣
║  Traités    : {self.stats['total_processed']:>8}                                  ║
║  Insérés    : {self.stats['total_inserted']:>8}                                  ║
║  Doublons   : {self.stats['total_duplicates']:>8}                                  ║
║  Erreurs    : {self.stats['errors']:>8}                                  ║
╠══════════════════════════════════════════════════════════════╣
║  PAR SOURCE:                                                 ║
""")
        for source, count in self.stats['by_source'].items():
            logger.info(f"║    {source:<30} : {count:>8}              ║")
        
        logger.info(f"""╠══════════════════════════════════════════════════════════════╣
║  PAR GRADE:                                                  ║
""")
        for grade, count in sorted(self.stats['by_grade'].items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"║    {grade:<30} : {count:>8}              ║")
        
        logger.info("╚══════════════════════════════════════════════════════════════╝")
    
    def run(self):
        """Lance l'extraction massive"""
        logger.info("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           MEGA HARVESTER V9 - DÉMARRAGE                      ║
║                                                              ║
║  Objectif : 150,000+ hadiths TOUS GRADES                     ║
║  Mode     : EXTRACTION CONTINUE SANS ARRÊT                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
        
        start_time = time.time()
        
        try:
            # Source 1: sunnah.com (toutes collections)
            self.harvest_sunnah_com()
            
            # Source 2: HadeethEnc
            self.harvest_hadeethenc()
            
            # Source 3: jsdelivr
            self.harvest_jsdelivr_api()
            
            # Rapport final
            elapsed = time.time() - start_time
            logger.info(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           MEGA HARVESTER V9 - RAPPORT FINAL                  ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  Durée totale : {elapsed/3600:.2f} heures                              ║
║  Traités      : {self.stats['total_processed']:>8}                                  ║
║  Insérés      : {self.stats['total_inserted']:>8}                                  ║
║  Doublons     : {self.stats['total_duplicates']:>8}                                  ║
║  Erreurs      : {self.stats['errors']:>8}                                  ║
╠══════════════════════════════════════════════════════════════╣
║  SOURCES EXPLOITÉES:                                         ║
""")
            for source, count in self.stats['by_source'].items():
                logger.info(f"║    {source:<30} : {count:>8}              ║")
            
            logger.info(f"""╠══════════════════════════════════════════════════════════════╣
║  GRADES COLLECTÉS:                                           ║
""")
            for grade, count in sorted(self.stats['by_grade'].items(), key=lambda x: x[1], reverse=True):
                logger.info(f"║    {grade:<30} : {count:>8}              ║")
            
            logger.info("╚══════════════════════════════════════════════════════════════╝")
            
        except KeyboardInterrupt:
            logger.warning("\n⚠️  Interruption utilisateur - Sauvegarde en cours...")
            self._log_progress()
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}")
        finally:
            self.conn.close()
            logger.info("✅ Connexion DB fermée")

if __name__ == "__main__":
    harvester = MegaHarvesterV9()
    harvester.run()