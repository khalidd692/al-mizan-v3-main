#!/usr/bin/env python3
"""
MEGA HARVESTER 100K
Objectif: Atteindre 100 000 hadiths en exploitant TOUTES les sources
"""

import sqlite3
import requests
import hashlib
import logging
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('backend/mega_harvest_100k.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class MegaHarvester100K:
    def __init__(self):
        self.db_path = 'backend/almizane.db'
        self.stats = {
            'total_imported': 0,
            'duplicates': 0,
            'errors': 0,
            'by_source': {}
        }
        
        # TOUTES LES SOURCES DISPONIBLES
        self.sources = {
            'hadith_gading': self.harvest_hadith_gading,
            'jsdelivr_fawaz': self.harvest_jsdelivr_fawaz,
            'github_datasets': self.harvest_github_datasets,
            'sunnah_com_api': self.harvest_sunnah_com,
            'hadith_one': self.harvest_hadith_one,
            'hadith_api_dev': self.harvest_hadith_api_dev,
        }
    
    def generate_hash(self, text_ar):
        if not text_ar:
            return None
        normalized = text_ar.strip().replace(' ', '').replace('\n', '')
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    
    def hash_exists(self, conn, hash_value):
        cursor = conn.execute(
            "SELECT 1 FROM hadiths WHERE sha256 = ? LIMIT 1",
            (hash_value,)
        )
        return cursor.fetchone() is not None
    
    def insert_hadith(self, conn, text_ar, grade, collection, source_name):
        """Insert avec gestion des doublons"""
        sha256_hash = self.generate_hash(text_ar)
        if not sha256_hash or self.hash_exists(conn, sha256_hash):
            self.stats['duplicates'] += 1
            return False
        
        try:
            conn.execute("""
                INSERT INTO hadiths (
                    matn_ar, grade_final, collection, sha256, source_api, categorie
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (text_ar, grade, collection, sha256_hash, source_name, 'hadith'))
            
            self.stats['total_imported'] += 1
            self.stats['by_source'][source_name] = self.stats['by_source'].get(source_name, 0) + 1
            return True
        
        except Exception as e:
            logging.error(f"Erreur insertion: {e}")
            self.stats['errors'] += 1
            return False
    
    def harvest_hadith_gading(self, conn):
        """API Hadith Gading - TOUTES les collections"""
        logging.info("=== HADITH GADING API ===")
        
        collections = [
            'bukhari', 'muslim', 'abudawud', 'tirmidhi', 
            'nasai', 'ibnmajah', 'malik', 'ahmad'
        ]
        
        for coll in collections:
            try:
                url = f'https://api.hadith.gading.dev/books/{coll}?range=1-1000'
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    hadiths = data.get('data', {}).get('hadiths', [])
                    
                    for h in hadiths:
                        text_ar = h.get('arab', '')
                        grade = h.get('grade', {}).get('arab', '')
                        
                        if text_ar:
                            self.insert_hadith(conn, text_ar, grade, coll, 'hadith_gading')
                    
                    conn.commit()
                    logging.info(f"  {coll}: {len(hadiths)} hadiths traités")
                
                time.sleep(1)
            
            except Exception as e:
                logging.error(f"Erreur {coll}: {e}")
    
    def harvest_jsdelivr_fawaz(self, conn):
        """jsDelivr CDN - Repository Fawaz"""
        logging.info("=== JSDELIVR FAWAZ ===")
        
        collections = [
            'bukhari', 'muslim', 'abudawud', 'tirmidhi',
            'nasai', 'ibnmajah', 'malik', 'ahmad', 'darimi'
        ]
        
        for coll in collections:
            try:
                url = f'https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/ara-{coll}.json'
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    hadiths = data.get('hadiths', [])
                    
                    for h in hadiths:
                        text_ar = h.get('text', '')
                        
                        if text_ar:
                            self.insert_hadith(conn, text_ar, '', coll, 'jsdelivr_fawaz')
                    
                    conn.commit()
                    logging.info(f"  {coll}: {len(hadiths)} hadiths traités")
                
                time.sleep(1)
            
            except Exception as e:
                logging.error(f"Erreur {coll}: {e}")
    
    def harvest_github_datasets(self, conn):
        """Datasets GitHub publics"""
        logging.info("=== GITHUB DATASETS ===")
        
        repos = [
            'https://raw.githubusercontent.com/A-Hussien96/hadith/master/data/bukhari.json',
            'https://raw.githubusercontent.com/A-Hussien96/hadith/master/data/muslim.json',
            'https://raw.githubusercontent.com/suhailgupta03/hadith-api/master/data/bukhari.json',
            'https://raw.githubusercontent.com/suhailgupta03/hadith-api/master/data/muslim.json',
        ]
        
        for url in repos:
            try:
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Adapter selon la structure
                    if isinstance(data, list):
                        hadiths = data
                    elif isinstance(data, dict):
                        hadiths = data.get('hadiths', data.get('data', []))
                    else:
                        continue
                    
                    for h in hadiths:
                        text_ar = h.get('text_ar', h.get('arab', h.get('arabic', '')))
                        grade = h.get('grade', '')
                        collection = h.get('collection', 'unknown')
                        
                        if text_ar:
                            self.insert_hadith(conn, text_ar, grade, collection, 'github')
                    
                    conn.commit()
                    logging.info(f"  {url.split('/')[-1]}: {len(hadiths)} hadiths traités")
                
                time.sleep(1)
            
            except Exception as e:
                logging.error(f"Erreur {url}: {e}")
    
    def harvest_sunnah_com(self, conn):
        """Sunnah.com API"""
        logging.info("=== SUNNAH.COM API ===")
        
        collections = ['bukhari', 'muslim', 'abudawud', 'tirmidhi', 'nasai', 'ibnmajah']
        
        for coll in collections:
            try:
                url = f'https://api.sunnah.com/v1/collections/{coll}/hadiths'
                headers = {'X-API-Key': 'SqD712P3E82xnwOAEOkGd5JZH8s9wRR24TqNFzjk'}
                
                response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    hadiths = data.get('data', [])
                    
                    for h in hadiths:
                        text_ar = h.get('hadith', [{}])[0].get('body', '')
                        grade = h.get('grades', [{}])[0].get('grade', '')
                        
                        if text_ar:
                            self.insert_hadith(conn, text_ar, grade, coll, 'sunnah_com')
                    
                    conn.commit()
                    logging.info(f"  {coll}: {len(hadiths)} hadiths traités")
                
                time.sleep(1)
            
            except Exception as e:
                logging.error(f"Erreur {coll}: {e}")
    
    def harvest_hadith_one(self, conn):
        """Hadith.one API"""
        logging.info("=== HADITH.ONE ===")
        
        try:
            url = 'https://hadith.one/api/hadiths'
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                hadiths = data.get('data', [])
                
                for h in hadiths:
                    text_ar = h.get('text_ar', '')
                    grade = h.get('grade', '')
                    collection = h.get('collection', '')
                    
                    if text_ar:
                        self.insert_hadith(conn, text_ar, grade, collection, 'hadith_one')
                
                conn.commit()
                logging.info(f"  {len(hadiths)} hadiths traités")
        
        except Exception as e:
            logging.error(f"Erreur hadith.one: {e}")
    
    def harvest_hadith_api_dev(self, conn):
        """Hadith-API.dev"""
        logging.info("=== HADITH-API.DEV ===")
        
        collections = ['bukhari', 'muslim', 'tirmidhi', 'abudawud', 'nasai', 'ibnmajah']
        
        for coll in collections:
            try:
                url = f'https://hadith-api.dev/api/{coll}/all'
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    hadiths = data.get('hadiths', [])
                    
                    for h in hadiths:
                        text_ar = h.get('arabic', '')
                        grade = h.get('grade', '')
                        
                        if text_ar:
                            self.insert_hadith(conn, text_ar, grade, coll, 'hadith_api_dev')
                    
                    conn.commit()
                    logging.info(f"  {coll}: {len(hadiths)} hadiths traités")
                
                time.sleep(1)
            
            except Exception as e:
                logging.error(f"Erreur {coll}: {e}")
    
    def run(self):
        """Lance le mega harvesting"""
        logging.info("="*60)
        logging.info("MEGA HARVESTER 100K - DEMARRAGE")
        logging.info("="*60)
        
        start_count = self.get_current_count()
        logging.info(f"Base actuelle: {start_count:,} hadiths")
        logging.info(f"Objectif: 100 000 hadiths")
        logging.info(f"Manquant: {100000 - start_count:,} hadiths")
        
        conn = sqlite3.connect(self.db_path)
        
        # Exécuter toutes les sources
        for source_name, harvest_func in self.sources.items():
            logging.info(f"\n{'='*60}")
            logging.info(f"SOURCE: {source_name.upper()}")
            logging.info(f"{'='*60}")
            
            try:
                harvest_func(conn)
            except Exception as e:
                logging.error(f"Erreur source {source_name}: {e}")
            
            current = self.get_current_count()
            logging.info(f"Total actuel: {current:,} hadiths")
            
            if current >= 100000:
                logging.info("🎯 OBJECTIF 100K ATTEINT!")
                break
        
        conn.close()
        self.print_final_report()
    
    def get_current_count(self):
        conn = sqlite3.connect(self.db_path)
        count = conn.execute("SELECT COUNT(*) FROM hadiths").fetchone()[0]
        conn.close()
        return count
    
    def print_final_report(self):
        final_count = self.get_current_count()
        
        logging.info(f"\n{'='*60}")
        logging.info("RAPPORT FINAL MEGA HARVESTER 100K")
        logging.info(f"{'='*60}")
        logging.info(f"Hadiths importés: {self.stats['total_imported']:,}")
        logging.info(f"Doublons évités: {self.stats['duplicates']:,}")
        logging.info(f"Erreurs: {self.stats['errors']:,}")
        logging.info(f"\nBase finale: {final_count:,} hadiths")
        
        if final_count >= 100000:
            logging.info("🎯 OBJECTIF 100 000 ATTEINT! ✅")
        else:
            logging.info(f"Manquant: {100000 - final_count:,} hadiths")
        
        logging.info(f"\nPar source:")
        for source, count in self.stats['by_source'].items():
            logging.info(f"  {source}: {count:,}")
        
        logging.info(f"{'='*60}")

if __name__ == '__main__':
    harvester = MegaHarvester100K()
    harvester.run()