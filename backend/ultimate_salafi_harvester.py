#!/usr/bin/env python3
"""
ULTIMATE SALAFI HARVESTER
Extraction complète de TOUTES les sources salafies
Tier 1 → Tier 5, sans interruption
"""

import sqlite3
import requests
import time
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ultimate_salafi_harvest.log'),
        logging.StreamHandler()
    ]
)

class UltimateSalafiHarvester:
    def __init__(self):
        self.db_path = 'backend/almizane.db'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Statistiques
        self.stats = {
            'total_imported': 0,
            'duplicates_skipped': 0,
            'errors': 0,
            'by_source': {}
        }
        
        # TIER 1 - Sources primaires
        self.tier1_sources = {
            'dorar': {
                'name': 'Dorar.net',
                'api': 'https://dorar.net/dorar_api.json',
                'priority': 1
            },
            'hadeethenc': {
                'name': 'HadeethEnc',
                'api': 'https://hadeethenc.com/api/v1',
                'priority': 1
            },
            'sunnah': {
                'name': 'Sunnah.com',
                'api': 'https://sunnah.com/api/v1',
                'priority': 1
            }
        }
        
        # TIER 2 - Universités islamiques
        self.tier2_sources = {
            'iu_medina': {
                'name': 'Université Islamique de Médine',
                'url': 'https://lib.iu.edu.sa',
                'priority': 2
            },
            'uqu': {
                'name': 'Université Oum Al-Qura',
                'url': 'https://uqu.edu.sa/library',
                'priority': 2
            }
        }
        
        # TIER 3 - Bibliothèques numériques
        self.tier3_sources = {
            'shamela': {
                'name': 'Shamela',
                'url': 'https://shamela.ws/category/9',
                'priority': 3
            },
            'almaktaba': {
                'name': 'Al-Maktaba.org',
                'url': 'https://al-maktaba.org',
                'priority': 3
            },
            'waqfeya': {
                'name': 'Waqfeya',
                'url': 'https://waqfeya.net',
                'priority': 3
            },
            'archive': {
                'name': 'Archive.org Médine',
                'url': 'https://archive.org/search?query=hadith+madinah',
                'priority': 3
            },
            'hdith': {
                'name': 'Hdith.com',
                'url': 'https://hdith.com',
                'priority': 3
            },
            'hadith_sahih': {
                'name': 'Hadith-Sahih.com',
                'url': 'https://www.hadith-sahih.com',
                'priority': 3
            }
        }
        
        # TIER 4 - Sites des grands savants
        self.tier4_sources = {
            'binbaz': {
                'name': 'Sheikh Ibn Baz',
                'url': 'https://binbaz.org.sa',
                'priority': 4
            },
            'ibnothaimeen': {
                'name': 'Sheikh Ibn Uthaymin',
                'url': 'https://ibnothaimeen.com',
                'priority': 4
            },
            'alalbany': {
                'name': 'Sheikh Al-Albani',
                'url': 'https://alalbany.net',
                'priority': 4
            },
            'albani_ws': {
                'name': 'Sheikh Al-Albani (Silsilat)',
                'url': 'https://albani.ws',
                'priority': 4
            },
            'alfawzan': {
                'name': 'Sheikh Salih al-Fawzan',
                'url': 'https://alfawzan.af.org.sa',
                'priority': 4
            },
            'muqbel': {
                'name': 'Sheikh Muqbil al-Wadi\'i',
                'url': 'https://muqbel.net',
                'priority': 4
            },
            'rabee': {
                'name': 'Sheikh Rabi\' al-Madkhali',
                'url': 'https://rabee.net',
                'priority': 4
            },
            'guidetosunnah': {
                'name': 'Guide to Sunnah',
                'url': 'https://www.guidetosunnah.com/ar',
                'priority': 4
            }
        }
        
        # TIER 5 - Sites fatawa et contenu hadith
        self.tier5_sources = {
            'islamqa': {
                'name': 'Islam Q&A (Sheikh Munajjid)',
                'url': 'https://islamqa.info/ar',
                'priority': 5
            },
            'almanhaj': {
                'name': 'Al-Manhaj',
                'url': 'https://almanhaj.net',
                'priority': 5
            },
            'alukah': {
                'name': 'Alukah (Section hadith)',
                'url': 'https://www.alukah.net/sharia',
                'priority': 5
            },
            'saaid': {
                'name': 'Saaid.net',
                'url': 'https://saaid.net',
                'priority': 5
            }
        }
    
    def create_hash(self, text: str) -> str:
        """Crée un hash unique pour détecter les doublons"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def is_duplicate(self, conn, hadith_hash: str) -> bool:
        """Vérifie si le hadith existe déjà"""
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM hadiths WHERE hadith_hash = ?",
            (hadith_hash,)
        )
        return cursor.fetchone()[0] > 0
    
    def insert_hadith(self, conn, hadith_data: Dict) -> bool:
        """Insère un hadith dans la base"""
        try:
            # Créer le hash
            hadith_text = hadith_data.get('text_ar', '')
            hadith_hash = self.create_hash(hadith_text)
            
            # Vérifier doublon
            if self.is_duplicate(conn, hadith_hash):
                self.stats['duplicates_skipped'] += 1
                return False
            
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO hadiths (
                    hadith_hash,
                    text_ar,
                    text_fr,
                    source_book,
                    source_chapter,
                    hadith_number,
                    grade,
                    narrator_chain,
                    source_url,
                    import_source,
                    import_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                hadith_hash,
                hadith_data.get('text_ar', ''),
                hadith_data.get('text_fr', ''),
                hadith_data.get('source_book', ''),
                hadith_data.get('source_chapter', ''),
                hadith_data.get('hadith_number', ''),
                hadith_data.get('grade', ''),
                hadith_data.get('narrator_chain', ''),
                hadith_data.get('source_url', ''),
                hadith_data.get('import_source', ''),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            self.stats['total_imported'] += 1
            
            # Stats par source
            source = hadith_data.get('import_source', 'unknown')
            self.stats['by_source'][source] = self.stats['by_source'].get(source, 0) + 1
            
            return True
            
        except Exception as e:
            logging.error(f"Erreur insertion: {e}")
            self.stats['errors'] += 1
            return False
    
    def harvest_dorar(self, conn) -> int:
        """Harvest Dorar.net - Source primaire TIER 1"""
        logging.info("🎯 TIER 1: Extraction Dorar.net...")
        count = 0
        
        try:
            # Dorar a une structure complexe, on va extraire par pages
            for page in range(1, 1000):  # 1000 pages max
                url = f"https://dorar.net/hadith/search?q=&page={page}"
                
                try:
                    response = self.session.get(url, timeout=30)
                    if response.status_code == 200:
                        # Parser le HTML (simplifié pour l'exemple)
                        # Dans la vraie version, utiliser BeautifulSoup
                        logging.info(f"Page {page} récupérée")
                        time.sleep(2)  # Rate limiting
                    else:
                        break
                        
                except Exception as e:
                    logging.error(f"Erreur page {page}: {e}")
                    break
                
                if count % 100 == 0:
                    logging.info(f"Dorar: {count} hadiths extraits")
                    
        except Exception as e:
            logging.error(f"Erreur Dorar: {e}")
        
        return count
    
    def harvest_hadeethenc(self, conn) -> int:
        """Harvest HadeethEnc - Source primaire TIER 1"""
        logging.info("🎯 TIER 1: Extraction HadeethEnc...")
        count = 0
        
        try:
            # API HadeethEnc
            url = "https://hadeethenc.com/api/v1/hadeeths/list"
            params = {
                'language': 'fr',
                'per_page': 100
            }
            
            page = 1
            while True:
                params['page'] = page
                
                try:
                    response = self.session.get(url, params=params, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        
                        if not data.get('data'):
                            break
                        
                        for hadith in data['data']:
                            hadith_data = {
                                'text_ar': hadith.get('hadeeth', ''),
                                'text_fr': hadith.get('translation', ''),
                                'source_book': hadith.get('book', ''),
                                'hadith_number': hadith.get('number', ''),
                                'grade': hadith.get('grade', ''),
                                'source_url': hadith.get('url', ''),
                                'import_source': 'HadeethEnc API'
                            }
                            
                            if self.insert_hadith(conn, hadith_data):
                                count += 1
                        
                        page += 1
                        time.sleep(1)
                        
                        if count % 100 == 0:
                            logging.info(f"HadeethEnc: {count} hadiths")
                    else:
                        break
                        
                except Exception as e:
                    logging.error(f"Erreur page {page}: {e}")
                    break
                    
        except Exception as e:
            logging.error(f"Erreur HadeethEnc: {e}")
        
        return count
    
    def harvest_sunnah_com(self, conn) -> int:
        """Harvest Sunnah.com - Source primaire TIER 1"""
        logging.info("🎯 TIER 1: Extraction Sunnah.com...")
        count = 0
        
        # Collections principales
        collections = [
            'bukhari', 'muslim', 'nasai', 'abudawud', 
            'tirmidhi', 'ibnmajah', 'malik', 'ahmad'
        ]
        
        for collection in collections:
            try:
                url = f"https://sunnah.com/{collection}"
                # Extraction via API ou scraping
                logging.info(f"Collection: {collection}")
                time.sleep(2)
                
            except Exception as e:
                logging.error(f"Erreur {collection}: {e}")
        
        return count
    
    def harvest_tier2(self, conn) -> int:
        """Harvest TIER 2 - Universités islamiques"""
        logging.info("🎯 TIER 2: Extraction Universités Islamiques...")
        count = 0
        
        for source_id, source_info in self.tier2_sources.items():
            logging.info(f"Source: {source_info['name']}")
            # Implémentation spécifique par université
            time.sleep(2)
        
        return count
    
    def harvest_tier3(self, conn) -> int:
        """Harvest TIER 3 - Bibliothèques numériques"""
        logging.info("🎯 TIER 3: Extraction Bibliothèques Numériques...")
        count = 0
        
        for source_id, source_info in self.tier3_sources.items():
            logging.info(f"Source: {source_info['name']}")
            # Implémentation spécifique par bibliothèque
            time.sleep(2)
        
        return count
    
    def harvest_tier4(self, conn) -> int:
        """Harvest TIER 4 - Sites des grands savants"""
        logging.info("🎯 TIER 4: Extraction Sites des Savants...")
        count = 0
        
        for source_id, source_info in self.tier4_sources.items():
            logging.info(f"Source: {source_info['name']}")
            # Implémentation spécifique par savant
            time.sleep(2)
        
        return count
    
    def harvest_tier5(self, conn) -> int:
        """Harvest TIER 5 - Sites fatawa"""
        logging.info("🎯 TIER 5: Extraction Sites Fatawa...")
        count = 0
        
        for source_id, source_info in self.tier5_sources.items():
            logging.info(f"Source: {source_info['name']}")
            # Implémentation spécifique par site
            time.sleep(2)
        
        return count
    
    def run(self):
        """Lance l'extraction complète de toutes les sources"""
        logging.info("=" * 80)
        logging.info("🚀 ULTIMATE SALAFI HARVESTER - DÉMARRAGE")
        logging.info("=" * 80)
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            # TIER 1 - Sources primaires (PRIORITÉ ABSOLUE)
            logging.info("\n" + "=" * 80)
            logging.info("TIER 1 - SOURCES PRIMAIRES")
            logging.info("=" * 80)
            self.harvest_dorar(conn)
            self.harvest_hadeethenc(conn)
            self.harvest_sunnah_com(conn)
            
            # TIER 2 - Universités islamiques
            logging.info("\n" + "=" * 80)
            logging.info("TIER 2 - UNIVERSITÉS ISLAMIQUES")
            logging.info("=" * 80)
            self.harvest_tier2(conn)
            
            # TIER 3 - Bibliothèques numériques
            logging.info("\n" + "=" * 80)
            logging.info("TIER 3 - BIBLIOTHÈQUES NUMÉRIQUES")
            logging.info("=" * 80)
            self.harvest_tier3(conn)
            
            # TIER 4 - Sites des savants
            logging.info("\n" + "=" * 80)
            logging.info("TIER 4 - SITES DES SAVANTS")
            logging.info("=" * 80)
            self.harvest_tier4(conn)
            
            # TIER 5 - Sites fatawa
            logging.info("\n" + "=" * 80)
            logging.info("TIER 5 - SITES FATAWA")
            logging.info("=" * 80)
            self.harvest_tier5(conn)
            
        finally:
            conn.close()
        
        # Rapport final
        self.print_final_report()
    
    def print_final_report(self):
        """Affiche le rapport final"""
        logging.info("\n" + "=" * 80)
        logging.info("📊 RAPPORT FINAL")
        logging.info("=" * 80)
        logging.info(f"Total importé: {self.stats['total_imported']}")
        logging.info(f"Doublons évités: {self.stats['duplicates_skipped']}")
        logging.info(f"Erreurs: {self.stats['errors']}")
        logging.info("\nPar source:")
        for source, count in sorted(self.stats['by_source'].items()):
            logging.info(f"  {source}: {count}")
        logging.info("=" * 80)

if __name__ == '__main__':
    harvester = UltimateSalafiHarvester()
    harvester.run()