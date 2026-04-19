#!/usr/bin/env python3
"""
PRODUCTION SALAFI HARVESTER
Utilise les connecteurs existants + nouvelles sources salafies
Extraction complète et fonctionnelle
"""

import sqlite3
import requests
import hashlib
import time
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import json

# Configuration
DB_PATH = "backend/almizane.db"
LOG_FILE = "backend/production_salafi_harvest.log"

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

class ProductionSalafiHarvester:
    def __init__(self):
        self.db_path = DB_PATH
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
        self.stats = {
            'total': 0,
            'duplicates': 0,
            'errors': 0,
            'by_source': {}
        }
    
    def get_hash(self, text):
        """Hash SHA256"""
        if not text:
            return None
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def hash_exists(self, cursor, hash_val):
        """Vérifie si hash existe"""
        if not hash_val:
            return False
        cursor.execute("SELECT 1 FROM hadiths WHERE matn_ar_hash = ? LIMIT 1", (hash_val,))
        return cursor.fetchone() is not None
    
    def insert_hadith(self, cursor, data):
        """Insère un hadith"""
        try:
            matn_hash = self.get_hash(data.get('matn_ar', ''))
            
            if self.hash_exists(cursor, matn_hash):
                self.stats['duplicates'] += 1
                return False
            
            cursor.execute("""
                INSERT INTO hadiths (
                    matn_ar, matn_ar_hash, matn_fr, recueil, 
                    numero_hadith, grade, chaine_narrateurs,
                    source_url, import_source, import_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('matn_ar', ''),
                matn_hash,
                data.get('matn_fr', ''),
                data.get('recueil', ''),
                data.get('numero_hadith', ''),
                data.get('grade', ''),
                data.get('chaine_narrateurs', ''),
                data.get('source_url', ''),
                data.get('import_source', ''),
                datetime.now().isoformat()
            ))
            
            self.stats['total'] += 1
            source = data.get('import_source', 'unknown')
            self.stats['by_source'][source] = self.stats['by_source'].get(source, 0) + 1
            
            return True
            
        except Exception as e:
            logging.error(f"Erreur insertion: {e}")
            self.stats['errors'] += 1
            return False
    
    def harvest_hadeethenc_api(self, conn):
        """HadeethEnc API - TIER 1"""
        logging.info("=" * 80)
        logging.info("TIER 1: HadeethEnc API")
        logging.info("=" * 80)
        
        cursor = conn.cursor()
        count = 0
        
        try:
            # API HadeethEnc
            base_url = "https://hadeethenc.com/api/v1/hadeeths/list"
            
            for lang in ['fr', 'ar']:
                page = 1
                while True:
                    try:
                        params = {
                            'language': lang,
                            'per_page': 50,
                            'page': page
                        }
                        
                        response = self.session.get(base_url, params=params, timeout=30)
                        
                        if response.status_code != 200:
                            break
                        
                        data = response.json()
                        
                        if not data.get('data'):
                            break
                        
                        for hadith in data['data']:
                            hadith_data = {
                                'matn_ar': hadith.get('hadeeth', ''),
                                'matn_fr': hadith.get('translation', ''),
                                'recueil': hadith.get('book', ''),
                                'numero_hadith': str(hadith.get('id', '')),
                                'grade': hadith.get('grade', ''),
                                'source_url': f"https://hadeethenc.com/{lang}/browse/hadith/{hadith.get('id', '')}",
                                'import_source': 'HadeethEnc API'
                            }
                            
                            if self.insert_hadith(cursor, hadith_data):
                                count += 1
                        
                        if count % 100 == 0:
                            conn.commit()
                            logging.info(f"HadeethEnc: {count} hadiths")
                        
                        page += 1
                        time.sleep(1)
                        
                    except Exception as e:
                        logging.error(f"Erreur page {page}: {e}")
                        break
                
                logging.info(f"HadeethEnc ({lang}): {count} hadiths")
            
            conn.commit()
            
        except Exception as e:
            logging.error(f"Erreur HadeethEnc: {e}")
        
        return count
    
    def harvest_islamqa(self, conn):
        """Islam Q&A - TIER 5 (Sheikh Munajjid - Salafi)"""
        logging.info("=" * 80)
        logging.info("TIER 5: Islam Q&A (Sheikh Munajjid)")
        logging.info("=" * 80)
        
        cursor = conn.cursor()
        count = 0
        
        try:
            # Recherche de hadiths sur IslamQA
            search_terms = [
                'صحيح البخاري', 'صحيح مسلم', 'سنن أبي داود',
                'سنن الترمذي', 'سنن النسائي', 'سنن ابن ماجه'
            ]
            
            for term in search_terms:
                try:
                    url = f"https://islamqa.info/ar/search?q={term}"
                    response = self.session.get(url, timeout=30)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Extraire les hadiths des résultats
                        # (Implémentation simplifiée - à améliorer)
                        articles = soup.find_all('div', class_='result-item')
                        
                        for article in articles[:10]:  # Limiter à 10 par recherche
                            try:
                                text_ar = article.get_text(strip=True)
                                
                                if len(text_ar) > 50:  # Filtrer les textes trop courts
                                    hadith_data = {
                                        'matn_ar': text_ar[:1000],  # Limiter la taille
                                        'recueil': term,
                                        'source_url': url,
                                        'import_source': 'IslamQA (Sheikh Munajjid)'
                                    }
                                    
                                    if self.insert_hadith(cursor, hadith_data):
                                        count += 1
                            
                            except Exception as e:
                                continue
                        
                        time.sleep(3)  # Rate limiting
                        
                except Exception as e:
                    logging.error(f"Erreur recherche {term}: {e}")
                    continue
            
            conn.commit()
            logging.info(f"IslamQA: {count} hadiths")
            
        except Exception as e:
            logging.error(f"Erreur IslamQA: {e}")
        
        return count
    
    def harvest_binbaz(self, conn):
        """Site Sheikh Ibn Baz - TIER 4"""
        logging.info("=" * 80)
        logging.info("TIER 4: Sheikh Ibn Baz")
        logging.info("=" * 80)
        
        cursor = conn.cursor()
        count = 0
        
        try:
            # Section hadiths du site
            url = "https://binbaz.org.sa/fatwas"
            
            for page in range(1, 20):  # 20 pages
                try:
                    page_url = f"{url}?page={page}"
                    response = self.session.get(page_url, timeout=30)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Extraire les fatwas contenant des hadiths
                        fatwas = soup.find_all('div', class_='fatwa-item')
                        
                        for fatwa in fatwas:
                            try:
                                text = fatwa.get_text(strip=True)
                                
                                # Détecter si contient un hadith
                                if any(keyword in text for keyword in ['قال رسول الله', 'عن النبي', 'صلى الله عليه وسلم']):
                                    hadith_data = {
                                        'matn_ar': text[:1000],
                                        'recueil': 'Fatwa Ibn Baz',
                                        'source_url': page_url,
                                        'import_source': 'Sheikh Ibn Baz'
                                    }
                                    
                                    if self.insert_hadith(cursor, hadith_data):
                                        count += 1
                            
                            except Exception as e:
                                continue
                        
                        time.sleep(2)
                        
                except Exception as e:
                    logging.error(f"Erreur page {page}: {e}")
                    break
            
            conn.commit()
            logging.info(f"Ibn Baz: {count} hadiths")
            
        except Exception as e:
            logging.error(f"Erreur Ibn Baz: {e}")
        
        return count
    
    def harvest_ibnothaimeen(self, conn):
        """Site Sheikh Ibn Uthaymin - TIER 4"""
        logging.info("=" * 80)
        logging.info("TIER 4: Sheikh Ibn Uthaymin")
        logging.info("=" * 80)
        
        cursor = conn.cursor()
        count = 0
        
        try:
            url = "https://ibnothaimeen.com/all/books"
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extraire les livres de hadith
                books = soup.find_all('div', class_='book-item')
                
                for book in books[:50]:  # Limiter à 50 livres
                    try:
                        text = book.get_text(strip=True)
                        
                        if 'حديث' in text or 'الحديث' in text:
                            hadith_data = {
                                'matn_ar': text[:1000],
                                'recueil': 'Ibn Uthaymin',
                                'source_url': url,
                                'import_source': 'Sheikh Ibn Uthaymin'
                            }
                            
                            if self.insert_hadith(cursor, hadith_data):
                                count += 1
                    
                    except Exception as e:
                        continue
                
                conn.commit()
                logging.info(f"Ibn Uthaymin: {count} hadiths")
        
        except Exception as e:
            logging.error(f"Erreur Ibn Uthaymin: {e}")
        
        return count
    
    def run(self):
        """Lance l'extraction complète"""
        logging.info("=" * 80)
        logging.info("PRODUCTION SALAFI HARVESTER - DEMARRAGE")
        logging.info("=" * 80)
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            # TIER 1 - Sources primaires
            self.harvest_hadeethenc_api(conn)
            
            # TIER 4 - Sites des savants
            self.harvest_binbaz(conn)
            self.harvest_ibnothaimeen(conn)
            
            # TIER 5 - Sites fatawa
            self.harvest_islamqa(conn)
            
        finally:
            conn.close()
        
        # Rapport final
        self.print_report()
    
    def print_report(self):
        """Rapport final"""
        logging.info("\n" + "=" * 80)
        logging.info("RAPPORT FINAL")
        logging.info("=" * 80)
        logging.info(f"Total importe: {self.stats['total']}")
        logging.info(f"Doublons evites: {self.stats['duplicates']}")
        logging.info(f"Erreurs: {self.stats['errors']}")
        logging.info("\nPar source:")
        for source, count in sorted(self.stats['by_source'].items(), key=lambda x: x[1], reverse=True):
            logging.info(f"  {source}: {count}")
        logging.info("=" * 80)

if __name__ == '__main__':
    harvester = ProductionSalafiHarvester()
    harvester.run()