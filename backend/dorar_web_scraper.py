#!/usr/bin/env python3
"""
DORAR.NET WEB SCRAPER
Extrait les hadiths directement depuis le HTML de dorar.net
"""

import sqlite3
import requests
import hashlib
import logging
import time
import re
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('backend/dorar_scraping.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class DorarWebScraper:
    def __init__(self):
        self.db_path = 'backend/almizane.db'
        self.base_url = 'https://dorar.net/hadith/search'
        self.stats = {
            'total_imported': 0,
            'duplicates': 0,
            'errors': 0
        }
        
        # Termes de recherche pour couvrir différents recueils
        self.search_terms = [
            'البخاري',  # Bukhari
            'مسلم',     # Muslim
            'الترمذي',  # Tirmidhi
            'أبو داود', # Abu Dawud
            'النسائي',  # Nasa'i
            'ابن ماجه', # Ibn Majah
            'أحمد',     # Ahmad
            'مالك',     # Malik
        ]
    
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
    
    def extract_hadith_from_html(self, html_content):
        """Extrait les hadiths depuis le HTML de dorar.net"""
        soup = BeautifulSoup(html_content, 'html.parser')
        hadiths = []
        
        # Chercher les divs de hadiths (structure observée dans le HTML)
        hadith_blocks = soup.find_all('div', class_=re.compile('hadith|result'))
        
        if not hadith_blocks:
            # Essayer une autre structure
            hadith_blocks = soup.find_all(['article', 'section'], class_=re.compile('hadith'))
        
        for block in hadith_blocks:
            try:
                # Extraire le texte arabe
                text_ar = ''
                
                # Chercher le texte principal
                text_elem = block.find(['p', 'div', 'span'], class_=re.compile('text|content|hadith'))
                if text_elem:
                    text_ar = text_elem.get_text(strip=True)
                else:
                    # Fallback: prendre tout le texte du bloc
                    text_ar = block.get_text(strip=True)
                
                if not text_ar or len(text_ar) < 20:
                    continue
                
                # Extraire le grade
                grade = ''
                grade_elem = block.find(['span', 'div'], class_=re.compile('grade|degree|حكم'))
                if grade_elem:
                    grade = grade_elem.get_text(strip=True)
                
                # Extraire la source
                source = ''
                source_elem = block.find(['span', 'div'], class_=re.compile('source|المصدر'))
                if source_elem:
                    source = source_elem.get_text(strip=True)
                
                hadiths.append({
                    'text_ar': text_ar,
                    'grade': grade,
                    'source': source
                })
            
            except Exception as e:
                logging.error(f"Erreur extraction hadith: {e}")
                continue
        
        return hadiths
    
    def scrape_search_page(self, term, page=1):
        """Scrape une page de résultats de recherche"""
        try:
            params = {
                'q': term,
                'st': 'p',  # Recherche par phrase
                'd[]': '1',  # Hadiths sahih
                'page': page
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return self.extract_hadith_from_html(response.text)
            else:
                logging.error(f"Erreur HTTP {response.status_code} pour {term}")
                return []
        
        except Exception as e:
            logging.error(f"Erreur scraping {term}: {e}")
            return []
    
    def run(self):
        """Lance le scraping"""
        logging.info("DEMARRAGE DORAR WEB SCRAPER")
        logging.info(f"Base actuelle: {self.get_current_count():,} hadiths")
        
        conn = sqlite3.connect(self.db_path)
        
        for term in self.search_terms:
            logging.info(f"\n=== Scraping: {term} ===")
            
            # Scraper plusieurs pages
            for page in range(1, 11):  # 10 pages par terme
                hadiths = self.scrape_search_page(term, page)
                
                if not hadiths:
                    break
                
                for h in hadiths:
                    text_ar = h['text_ar']
                    
                    content_hash = self.generate_hash(text_ar)
                    if not content_hash or self.hash_exists(conn, content_hash):
                        self.stats['duplicates'] += 1
                        continue
                    
                    try:
                        conn.execute("""
                            INSERT INTO hadiths (
                                text_ar, grade, collection, content_hash
                            ) VALUES (?, ?, ?, ?)
                        """, (
                            text_ar,
                            h['grade'],
                            h['source'],
                            content_hash
                        ))
                        
                        self.stats['total_imported'] += 1
                        
                        if self.stats['total_imported'] % 100 == 0:
                            conn.commit()
                            logging.info(f"  {term} page {page}: {self.stats['total_imported']} importes")
                    
                    except Exception as e:
                        logging.error(f"Erreur insertion: {e}")
                        self.stats['errors'] += 1
                
                time.sleep(2)  # Respecter le serveur
            
            conn.commit()
        
        conn.close()
        self.print_final_report()
    
    def get_current_count(self):
        conn = sqlite3.connect(self.db_path)
        count = conn.execute("SELECT COUNT(*) FROM hadiths").fetchone()[0]
        conn.close()
        return count
    
    def print_final_report(self):
        logging.info(f"\n{'='*60}")
        logging.info("RAPPORT FINAL DORAR SCRAPING")
        logging.info(f"{'='*60}")
        logging.info(f"Hadiths importes: {self.stats['total_imported']:,}")
        logging.info(f"Doublons evites: {self.stats['duplicates']:,}")
        logging.info(f"Erreurs: {self.stats['errors']:,}")
        logging.info(f"Base totale: {self.get_current_count():,} hadiths")
        logging.info(f"{'='*60}")

if __name__ == '__main__':
    scraper = DorarWebScraper()
    scraper.run()