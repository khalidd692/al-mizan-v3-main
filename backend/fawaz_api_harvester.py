#!/usr/bin/env python3
"""
FAWAZ API HARVESTER
Utilise l'API hadith de fawazahmed0 (GitHub)
https://github.com/fawazahmed0/hadith-api
"""

import sqlite3
import requests
import hashlib
import logging
import time
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('backend/fawaz_harvest.log'),
        logging.StreamHandler()
    ]
)

class FawazAPIHarvester:
    def __init__(self):
        self.db_path = 'backend/almizane.db'
        self.api_base = 'https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1'
        
        self.stats = {
            'total_processed': 0,
            'total_imported': 0,
            'duplicates': 0,
            'errors': 0
        }
        
        # Éditions disponibles (collections)
        self.editions = [
            'ara-abudawud', 'ara-bukhari', 'ara-darimi',
            'ara-ibnmajah', 'ara-malik', 'ara-muslim',
            'ara-nasai', 'ara-tirmidhi', 'ara-ahmad'
        ]
    
    def get_edition_metadata(self, edition):
        """Récupère les métadonnées d'une édition"""
        try:
            url = f"{self.api_base}/editions/{edition}.json"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logging.error(f"Erreur metadata {edition}: {e}")
            return None
    
    def get_hadith(self, edition, number):
        """Récupère un hadith spécifique"""
        try:
            url = f"{self.api_base}/editions/{edition}/{number}.json"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            return None
    
    def generate_hash(self, text_ar):
        """Génère hash SHA-256"""
        if not text_ar:
            return None
        normalized = text_ar.strip().replace(' ', '').replace('\n', '')
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    
    def hash_exists(self, conn, hash_value):
        """Vérifie si hash existe"""
        cursor = conn.execute(
            "SELECT 1 FROM hadiths WHERE content_hash = ? LIMIT 1",
            (hash_value,)
        )
        return cursor.fetchone() is not None
    
    def import_hadith(self, conn, hadith_data, edition):
        """Importe un hadith"""
        try:
            # Extraire le texte arabe
            text_ar = hadith_data.get('text', hadith_data.get('hadith', ''))
            if not text_ar:
                return False
            
            content_hash = self.generate_hash(text_ar)
            if not content_hash:
                return False
            
            if self.hash_exists(conn, content_hash):
                self.stats['duplicates'] += 1
                return False
            
            # Mapper le nom de collection
            collection_map = {
                'bukhari': 'Sahih Bukhari',
                'muslim': 'Sahih Muslim',
                'abudawud': 'Sunan Abu Dawud',
                'tirmidhi': 'Jami at-Tirmidhi',
                'nasai': 'Sunan an-Nasa\'i',
                'ibnmajah': 'Sunan Ibn Majah',
                'malik': 'Muwatta Malik',
                'ahmad': 'Musnad Ahmad',
                'darimi': 'Sunan ad-Darimi'
            }
            
            collection_name = edition.replace('ara-', '')
            collection = collection_map.get(collection_name, collection_name)
            
            conn.execute("""
                INSERT INTO hadiths (
                    text_ar, text_en, collection, book, chapter,
                    hadith_number, grade, narrator, source, content_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                text_ar,
                hadith_data.get('english', ''),
                collection,
                hadith_data.get('book', ''),
                hadith_data.get('chapter', ''),
                str(hadith_data.get('hadithnumber', '')),
                hadith_data.get('grade', ''),
                hadith_data.get('narrator', ''),
                'fawaz_api',
                content_hash
            ))
            
            self.stats['total_imported'] += 1
            return True
        
        except Exception as e:
            self.stats['errors'] += 1
            logging.error(f"Erreur import: {e}")
            return False
    
    def harvest_edition(self, conn, edition):
        """Harveste une édition complète"""
        logging.info(f"\n{'='*60}")
        logging.info(f"EDITION: {edition}")
        logging.info(f"{'='*60}")
        
        # Récupérer métadonnées
        metadata = self.get_edition_metadata(edition)
        if not metadata:
            logging.error(f"Impossible de récupérer metadata pour {edition}")
            return
        
        total_hadiths = metadata.get('metadata', {}).get('total_hadiths', 0)
        logging.info(f"Total hadiths dans cette edition: {total_hadiths}")
        
        if total_hadiths == 0:
            # Essayer de deviner le nombre
            total_hadiths = 7000  # Maximum estimé
        
        imported_count = 0
        
        for i in range(1, total_hadiths + 1):
            self.stats['total_processed'] += 1
            
            hadith_data = self.get_hadith(edition, i)
            if hadith_data:
                if self.import_hadith(conn, hadith_data, edition):
                    imported_count += 1
                
                # Commit tous les 100
                if imported_count % 100 == 0:
                    conn.commit()
                    logging.info(f"  [{i}/{total_hadiths}] {imported_count} importes, {self.stats['duplicates']} doublons")
            
            # Pause légère
            if i % 50 == 0:
                time.sleep(0.5)
        
        conn.commit()
        logging.info(f"TERMINE: {imported_count} hadiths importes pour {edition}")
    
    def run(self):
        """Lance le harvesting"""
        logging.info("DEMARRAGE FAWAZ API HARVESTER")
        logging.info(f"Base actuelle: {self.get_current_count():,} hadiths")
        logging.info(f"{len(self.editions)} editions a harvester")
        
        conn = sqlite3.connect(self.db_path)
        
        for edition in self.editions:
            self.harvest_edition(conn, edition)
            
            # Stats intermédiaires
            logging.info(f"\nSTATS CUMULEES:")
            logging.info(f"  Traites: {self.stats['total_processed']:,}")
            logging.info(f"  Importes: {self.stats['total_imported']:,}")
            logging.info(f"  Doublons: {self.stats['duplicates']:,}")
            logging.info(f"  Base totale: {self.get_current_count():,}")
        
        conn.close()
        self.print_final_report()
    
    def get_current_count(self):
        """Compte hadiths actuels"""
        conn = sqlite3.connect(self.db_path)
        count = conn.execute("SELECT COUNT(*) FROM hadiths").fetchone()[0]
        conn.close()
        return count
    
    def print_final_report(self):
        """Rapport final"""
        logging.info(f"\n{'='*60}")
        logging.info("RAPPORT FINAL FAWAZ API")
        logging.info(f"{'='*60}")
        logging.info(f"Hadiths traites: {self.stats['total_processed']:,}")
        logging.info(f"Hadiths importes: {self.stats['total_imported']:,}")
        logging.info(f"Doublons evites: {self.stats['duplicates']:,}")
        logging.info(f"Erreurs: {self.stats['errors']:,}")
        logging.info(f"Base totale: {self.get_current_count():,} hadiths")
        logging.info(f"{'='*60}")

if __name__ == '__main__':
    harvester = FawazAPIHarvester()
    harvester.run()