#!/usr/bin/env python3
"""
DORAR OFFICIAL API HARVESTER
Utilise l'API officielle de Dorar.net pour extraction massive
"""

import sqlite3
import requests
import hashlib
import logging
import time
from datetime import datetime
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend/dorar_api_harvest.log'),
        logging.StreamHandler()
    ]
)

class DorarOfficialAPIHarvester:
    def __init__(self):
        self.db_path = 'backend/almizane.db'
        self.api_base = 'https://dorar.net/dorar_api.json'
        
        self.stats = {
            'total_processed': 0,
            'total_imported': 0,
            'duplicates': 0,
            'errors': 0,
            'api_calls': 0
        }
        
        # Termes de recherche prioritaires (salafi)
        self.search_terms = [
            # Collections majeures
            "البخاري", "مسلم", "الترمذي", "أبو داود", 
            "النسائي", "ابن ماجه", "أحمد", "الدارمي",
            
            # Grades
            "صحيح", "حسن", "ضعيف", "موضوع",
            
            # Savants salafi
            "الألباني", "ابن باز", "ابن عثيمين", "الفوزان",
            
            # Thèmes importants
            "التوحيد", "العقيدة", "الصلاة", "الزكاة",
            "الصيام", "الحج", "الجهاد", "الأمر بالمعروف",
            
            # Narrateurs
            "أبو هريرة", "عائشة", "ابن عمر", "أنس",
            "جابر", "أبو سعيد", "ابن عباس",
            
            # Livres spécifiques
            "صحيح البخاري", "صحيح مسلم", "سنن الترمذي",
            "سنن أبي داود", "سنن النسائي", "سنن ابن ماجه",
            "مسند أحمد", "موطأ مالك"
        ]
    
    def search_dorar_api(self, term):
        """Recherche via API officielle Dorar"""
        try:
            url = f"{self.api_base}?skey={term}"
            response = requests.get(url, timeout=30)
            self.stats['api_calls'] += 1
            
            if response.status_code == 200:
                # L'API retourne du JSONP, on doit extraire le JSON
                content = response.text
                
                # Si c'est du JSONP, extraire le JSON
                if content.startswith('(') and content.endswith(')'):
                    content = content[1:-1]
                
                data = json.loads(content)
                return data if isinstance(data, list) else []
            
            return []
        
        except Exception as e:
            logging.error(f"Erreur API Dorar pour '{term}': {e}")
            self.stats['errors'] += 1
            return []
    
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
    
    def parse_dorar_result(self, item):
        """Parse un résultat de l'API Dorar"""
        return {
            'text_ar': item.get('th', item.get('text', '')),
            'text_en': '',  # Dorar API ne fournit pas de traduction
            'collection': item.get('book', ''),
            'book': item.get('book', ''),
            'chapter': item.get('chapter', ''),
            'hadith_number': item.get('number', item.get('id', '')),
            'grade': item.get('grade', item.get('hukm', '')),
            'narrator': item.get('narrator', item.get('rawi', '')),
            'source': 'dorar_official_api'
        }
    
    def import_hadith(self, conn, hadith):
        """Importe un hadith"""
        try:
            content_hash = self.generate_hash(hadith['text_ar'])
            if not content_hash:
                return False
            
            if self.hash_exists(conn, content_hash):
                self.stats['duplicates'] += 1
                return False
            
            conn.execute("""
                INSERT INTO hadiths (
                    text_ar, text_en, collection, book, chapter,
                    hadith_number, grade, narrator, source, content_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                hadith['text_ar'],
                hadith['text_en'],
                hadith['collection'],
                hadith['book'],
                hadith['chapter'],
                hadith['hadith_number'],
                hadith['grade'],
                hadith['narrator'],
                hadith['source'],
                content_hash
            ))
            
            self.stats['total_imported'] += 1
            return True
        
        except Exception as e:
            self.stats['errors'] += 1
            logging.error(f"Erreur import: {e}")
            return False
    
    def run(self):
        """Lance le harvesting"""
        logging.info("DEMARRAGE DORAR OFFICIAL API HARVESTER")
        logging.info(f"Base actuelle: {self.get_current_count():,} hadiths")
        logging.info(f"{len(self.search_terms)} termes de recherche")
        
        conn = sqlite3.connect(self.db_path)
        
        for i, term in enumerate(self.search_terms, 1):
            logging.info(f"\n[{i}/{len(self.search_terms)}] Recherche: {term}")
            
            # Recherche API
            results = self.search_dorar_api(term)
            logging.info(f"  {len(results)} resultats")
            
            # Import
            imported_count = 0
            for result in results:
                self.stats['total_processed'] += 1
                hadith = self.parse_dorar_result(result)
                
                if self.import_hadith(conn, hadith):
                    imported_count += 1
                
                # Commit tous les 50
                if imported_count % 50 == 0:
                    conn.commit()
            
            conn.commit()
            logging.info(f"  {imported_count} importes, {self.stats['duplicates']} doublons")
            
            # Stats intermédiaires tous les 10 termes
            if i % 10 == 0:
                logging.info(f"\nSTATS INTERMEDIAIRES:")
                logging.info(f"  Appels API: {self.stats['api_calls']}")
                logging.info(f"  Traites: {self.stats['total_processed']:,}")
                logging.info(f"  Importes: {self.stats['total_imported']:,}")
                logging.info(f"  Doublons: {self.stats['duplicates']:,}")
                logging.info(f"  Base totale: {self.get_current_count():,}")
            
            # Pause entre requêtes
            time.sleep(1)
        
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
        logging.info("RAPPORT FINAL DORAR OFFICIAL API")
        logging.info(f"{'='*60}")
        logging.info(f"Appels API: {self.stats['api_calls']}")
        logging.info(f"Hadiths traites: {self.stats['total_processed']:,}")
        logging.info(f"Hadiths importes: {self.stats['total_imported']:,}")
        logging.info(f"Doublons evites: {self.stats['duplicates']:,}")
        logging.info(f"Erreurs: {self.stats['errors']:,}")
        logging.info(f"Base totale: {self.get_current_count():,} hadiths")
        logging.info(f"{'='*60}")

if __name__ == '__main__':
    harvester = DorarOfficialAPIHarvester()
    harvester.run()