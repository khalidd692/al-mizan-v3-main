#!/usr/bin/env python3
"""
ULTIMATE MULTI-SOURCE HARVESTER
Combine TOUTES les sources salafi en parallèle
"""

import sqlite3
import requests
import hashlib
import logging
import time
import concurrent.futures
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('backend/ultimate_multi_harvest.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class UltimateMultiSourceHarvester:
    def __init__(self):
        self.db_path = 'backend/almizane.db'
        self.stats = {
            'total_processed': 0,
            'total_imported': 0,
            'duplicates': 0,
            'errors': 0
        }
        
        # TOUTES les sources fonctionnelles
        self.sources = {
            'hadith_gading': 'https://api.hadith.gading.dev',
            'jsdelivr_bukhari': 'https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/ara-bukhari',
            'sunnah_com': 'https://api.sunnah.com/v1',
            'hadeethenc': 'https://hadeethenc.com/api/v1'
        }
    
    def generate_hash(self, text_ar):
        if not text_ar:
            return None
        normalized = text_ar.strip().replace(' ', '').replace('\n', '')
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    
    def hash_exists(self, conn, hash_value):
        cursor = conn.execute(
            "SELECT 1 FROM hadiths WHERE content_hash = ? LIMIT 1",
            (hash_value,)
        )
        return cursor.fetchone() is not None
    
    def harvest_hadith_gading(self, conn):
        """Harveste hadith.gading.dev"""
        logging.info("\n=== HADITH GADING ===")
        
        books = ['bukhari', 'muslim', 'tirmidhi', 'abudawud', 'nasai', 'ibnmajah', 'malik', 'ahmad']
        imported = 0
        
        for book in books:
            try:
                url = f"{self.sources['hadith_gading']}/books/{book}?range=1-500"
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    hadiths = data.get('data', {}).get('hadiths', [])
                    
                    for h in hadiths:
                        text_ar = h.get('arab', '')
                        if not text_ar:
                            continue
                        
                        content_hash = self.generate_hash(text_ar)
                        if not content_hash or self.hash_exists(conn, content_hash):
                            self.stats['duplicates'] += 1
                            continue
                        
                        conn.execute("""
                            INSERT INTO hadiths (
                                text_ar, text_en, collection, hadith_number,
                                source, content_hash
                            ) VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            text_ar,
                            h.get('id', ''),
                            book.title(),
                            str(h.get('number', '')),
                            'hadith_gading',
                            content_hash
                        ))
                        
                        imported += 1
                        self.stats['total_imported'] += 1
                        
                        if imported % 100 == 0:
                            conn.commit()
                            logging.info(f"  {book}: {imported} importes")
                
                time.sleep(1)
            
            except Exception as e:
                logging.error(f"Erreur {book}: {e}")
                self.stats['errors'] += 1
        
        conn.commit()
        logging.info(f"HADITH GADING: {imported} hadiths")
        return imported
    
    def harvest_sunnah_com(self, conn):
        """Harveste sunnah.com"""
        logging.info("\n=== SUNNAH.COM ===")
        
        collections = ['bukhari', 'muslim', 'tirmidhi', 'abudawud', 'nasai', 'ibnmajah']
        imported = 0
        
        for coll in collections:
            try:
                # Essayer différents endpoints
                for i in range(1, 100):
                    url = f"{self.sources['sunnah_com']}/collections/{coll}/hadith/{i}"
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code != 200:
                        break
                    
                    data = response.json()
                    text_ar = data.get('hadith', {}).get('body', '')
                    
                    if not text_ar:
                        continue
                    
                    content_hash = self.generate_hash(text_ar)
                    if not content_hash or self.hash_exists(conn, content_hash):
                        self.stats['duplicates'] += 1
                        continue
                    
                    conn.execute("""
                        INSERT INTO hadiths (
                            text_ar, collection, hadith_number,
                            source, content_hash
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        text_ar,
                        coll.title(),
                        str(i),
                        'sunnah_com',
                        content_hash
                    ))
                    
                    imported += 1
                    self.stats['total_imported'] += 1
                    
                    if imported % 50 == 0:
                        conn.commit()
                        logging.info(f"  {coll}: {imported} importes")
                    
                    time.sleep(0.5)
            
            except Exception as e:
                logging.error(f"Erreur {coll}: {e}")
                self.stats['errors'] += 1
        
        conn.commit()
        logging.info(f"SUNNAH.COM: {imported} hadiths")
        return imported
    
    def harvest_hadeethenc(self, conn):
        """Harveste hadeethenc.com"""
        logging.info("\n=== HADEETHENC ===")
        
        imported = 0
        
        try:
            # Recherches par termes
            terms = ['صحيح', 'البخاري', 'مسلم', 'الترمذي', 'أبو داود']
            
            for term in terms:
                url = f"{self.sources['hadeethenc']}/hadiths?language=ar&search={term}&per_page=100"
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    hadiths = data.get('data', [])
                    
                    for h in hadiths:
                        text_ar = h.get('hadeeth', '')
                        if not text_ar:
                            continue
                        
                        content_hash = self.generate_hash(text_ar)
                        if not content_hash or self.hash_exists(conn, content_hash):
                            self.stats['duplicates'] += 1
                            continue
                        
                        conn.execute("""
                            INSERT INTO hadiths (
                                text_ar, text_en, grade, source, content_hash
                            ) VALUES (?, ?, ?, ?, ?)
                        """, (
                            text_ar,
                            h.get('hadeeth_english', ''),
                            h.get('grade', ''),
                            'hadeethenc',
                            content_hash
                        ))
                        
                        imported += 1
                        self.stats['total_imported'] += 1
                
                time.sleep(2)
        
        except Exception as e:
            logging.error(f"Erreur hadeethenc: {e}")
            self.stats['errors'] += 1
        
        conn.commit()
        logging.info(f"HADEETHENC: {imported} hadiths")
        return imported
    
    def run(self):
        """Lance le harvesting multi-sources"""
        logging.info("DEMARRAGE ULTIMATE MULTI-SOURCE HARVESTER")
        logging.info(f"Base actuelle: {self.get_current_count():,} hadiths")
        
        conn = sqlite3.connect(self.db_path)
        
        # Harvester chaque source
        self.harvest_hadith_gading(conn)
        self.harvest_sunnah_com(conn)
        self.harvest_hadeethenc(conn)
        
        conn.close()
        self.print_final_report()
    
    def get_current_count(self):
        conn = sqlite3.connect(self.db_path)
        count = conn.execute("SELECT COUNT(*) FROM hadiths").fetchone()[0]
        conn.close()
        return count
    
    def print_final_report(self):
        logging.info(f"\n{'='*60}")
        logging.info("RAPPORT FINAL MULTI-SOURCE")
        logging.info(f"{'='*60}")
        logging.info(f"Hadiths importes: {self.stats['total_imported']:,}")
        logging.info(f"Doublons evites: {self.stats['duplicates']:,}")
        logging.info(f"Erreurs: {self.stats['errors']:,}")
        logging.info(f"Base totale: {self.get_current_count():,} hadiths")
        logging.info(f"{'='*60}")

if __name__ == '__main__':
    harvester = UltimateMultiSourceHarvester()
    harvester.run()