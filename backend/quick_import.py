#!/usr/bin/env python3
"""
Import Rapide - API Hadith Gading directe
"""

import requests
import sqlite3
import logging
import hashlib
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QuickImporter:
    """Import rapide depuis Hadith Gading API"""
    
    def __init__(self, db_path: str = "backend/almizane.db"):
        self.db_path = db_path
        self.base_url = "https://api.hadith.gading.dev"
        self.stats = {'imported': 0, 'skipped': 0, 'errors': 0}
    
    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def import_book(self, book_name: str, limit: int = 1000):
        """Import un livre depuis Hadith Gading"""
        logger.info(f"📖 Import {book_name}...")
        
        conn = self.get_db_connection()
        imported = 0
        
        try:
            # Récupérer info livre avec range pour obtenir le total
            resp = requests.get(f"{self.base_url}/books/{book_name}?range=1-1", timeout=10)
            if resp.status_code != 200:
                logger.error(f"   ❌ Erreur API: {resp.status_code}")
                return 0
            
            data = resp.json()
            if data.get('code') != 200:
                logger.error(f"   ❌ Erreur: {data.get('message')}")
                return 0
            
            book_data = data.get('data', {})
            total = book_data.get('available', 0)
            logger.info(f"   📊 {total} hadiths disponibles (import limité à {limit})")
            
            # Import par hadith
            for num in range(1, min(total + 1, limit + 1)):
                try:
                    resp = requests.get(
                        f"{self.base_url}/books/{book_name}/{num}",
                        timeout=5
                    )
                    
                    if resp.status_code != 200:
                        continue
                    
                    data = resp.json()
                    if data.get('code') != 200:
                        continue
                    
                    hadith_data = data.get('data', {})
                    hadith = hadith_data.get('contents', {})
                    
                    # Vérifier doublon (utiliser le format existant)
                    cursor = conn.execute(
                        "SELECT 1 FROM hadiths WHERE source_api = ? AND collection = ? AND numero_hadith = ? LIMIT 1",
                        ("hadith_gading", book_name, str(num))
                    )
                    
                    if cursor.fetchone():
                        self.stats['skipped'] += 1
                        continue
                    
                    # Générer SHA256 pour déduplication
                    matn_ar = hadith.get('arab', '')
                    matn_fr = hadith.get('id', '')
                    hash_content = f"{matn_ar}|{book_name}|{num}"
                    sha256_hash = hashlib.sha256(hash_content.encode('utf-8')).hexdigest()
                    
                    # Insérer avec toutes les colonnes NOT NULL
                    conn.execute("""
                        INSERT INTO hadiths (
                            sha256, matn_ar, matn_fr, source_api, collection,
                            numero_hadith, grade_final, categorie, inserted_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        sha256_hash,
                        matn_ar,
                        matn_fr,
                        "hadith_gading",
                        book_name,
                        str(num),
                        "non_évalué",  # Grade par défaut
                        "MAQBUL",      # Catégorie par défaut (Kutub al-Sittah sont fiables)
                        datetime.now().isoformat()
                    ))
                    
                    imported += 1
                    self.stats['imported'] += 1
                    
                    if imported % 100 == 0:
                        conn.commit()
                        logger.info(f"   ✓ {imported}/{min(total, limit)} importés")
                    
                except Exception as e:
                    self.stats['errors'] += 1
                    # Log les 5 premières erreurs pour debug
                    if self.stats['errors'] <= 5:
                        logger.error(f"   ❌ Erreur hadith #{num}: {e}")
                    elif self.stats['errors'] % 50 == 0:
                        logger.warning(f"   ⚠️  {self.stats['errors']} erreurs")
            
            conn.commit()
            logger.info(f"✅ {book_name}: {imported} hadiths importés")
            
        except Exception as e:
            logger.error(f"❌ Erreur livre {book_name}: {e}")
        finally:
            conn.close()
        
        return imported
    
    def import_all(self, limit_per_book: int = 1000):
        """Import tous les livres"""
        logger.info("=" * 60)
        logger.info("🚀 IMPORT RAPIDE HADITH GADING")
        logger.info("=" * 60)
        
        books = ['bukhari', 'muslim', 'abudawud', 'tirmidzi', 'nasai', 'ibnmajah']
        
        for book in books:
            self.import_book(book, limit_per_book)
        
        logger.info("=" * 60)
        logger.info(f"✅ Total importé: {self.stats['imported']}")
        logger.info(f"⚠️  Doublons évités: {self.stats['skipped']}")
        logger.info(f"❌ Erreurs: {self.stats['errors']}")
        logger.info("=" * 60)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Import rapide Hadith Gading")
    parser.add_argument('--book', help="Livre spécifique (bukhari, muslim, etc.)")
    parser.add_argument('--limit', type=int, default=1000, help="Limite par livre (défaut: 1000)")
    parser.add_argument('--all', action='store_true', help="Importer tous les livres")
    
    args = parser.parse_args()
    
    importer = QuickImporter()
    
    if args.all:
        importer.import_all(args.limit)
    elif args.book:
        importer.import_book(args.book, args.limit)
    else:
        # Par défaut: import rapide Bukhari
        importer.import_book('bukhari', args.limit)

if __name__ == "__main__":
    main()