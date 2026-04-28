#!/usr/bin/env python3
"""
Importeur Simple - Utilise les harvesters existants validés
"""

import sys
import sqlite3
from pathlib import Path

# Ajouter le répertoire backend au path
sys.path.insert(0, str(Path(__file__).parent))

from connectors.hadith_gading_connector import HadithGadingConnector
from connectors.jsdelivr_connector import JSDelivrConnector
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleImporter:
    """Import depuis connecteurs validés"""
    
    def __init__(self, db_path: str = "backend/almizane.db"):
        self.db_path = db_path
        self.stats = {
            'imported': 0,
            'skipped': 0,
            'errors': 0
        }
    
    def get_db_connection(self):
        """Connexion SQLite"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def import_from_gading(self):
        """Import depuis Hadith Gading (validé)"""
        logger.info("=" * 60)
        logger.info("📦 IMPORT HADITH GADING API")
        logger.info("=" * 60)
        
        connector = HadithGadingConnector()
        conn = self.get_db_connection()
        
        # Collections disponibles
        books = ['bukhari', 'muslim', 'abudawud', 'tirmidzi', 'nasai', 'ibnmajah']
        
        for book in books:
            logger.info(f"📖 Import {book}...")
            
            try:
                # Récupérer info livre
                book_info = connector.get_book_info(book)
                if not book_info:
                    logger.warning(f"   ⚠️  Livre {book} non trouvé")
                    continue
                
                total = book_info.get('available', 0)
                logger.info(f"   📊 {total} hadiths disponibles")
                
                # Import par batch
                batch_size = 100
                imported = 0
                
                for start in range(1, total + 1, batch_size):
                    end = min(start + batch_size - 1, total)
                    
                    # Récupérer batch
                    hadiths = connector.get_hadiths_range(book, start, end)
                    
                    if not hadiths:
                        continue
                    
                    # Insérer dans DB
                    for hadith in hadiths:
                        try:
                            # Vérifier si existe déjà
                            cursor = conn.execute(
                                "SELECT 1 FROM hadiths WHERE source = ? AND hadith_number = ? LIMIT 1",
                                (f"hadith.gading.dev/{book}", str(hadith.get('number', '')))
                            )
                            
                            if cursor.fetchone():
                                self.stats['skipped'] += 1
                                continue
                            
                            # Insérer
                            conn.execute("""
                                INSERT INTO hadiths (
                                    text_ar, text_fr, source, book, 
                                    hadith_number, created_at
                                ) VALUES (?, ?, ?, ?, ?, datetime('now'))
                            """, (
                                hadith.get('arab', ''),
                                hadith.get('id', ''),  # Texte indonésien
                                f"hadith.gading.dev/{book}",
                                book,
                                str(hadith.get('number', ''))
                            ))
                            
                            imported += 1
                            self.stats['imported'] += 1
                            
                        except Exception as e:
                            logger.error(f"Erreur insert hadith: {e}")
                            self.stats['errors'] += 1
                    
                    conn.commit()
                    
                    if start % 500 == 1:
                        logger.info(f"   ✓ {imported}/{total} importés")
                
                logger.info(f"✅ {book}: {imported} hadiths importés")
                
            except Exception as e:
                logger.error(f"❌ Erreur livre {book}: {e}")
                self.stats['errors'] += 1
        
        conn.close()
        
        logger.info("=" * 60)
        logger.info(f"✅ Total importé: {self.stats['imported']}")
        logger.info(f"⚠️  Doublons évités: {self.stats['skipped']}")
        logger.info(f"❌ Erreurs: {self.stats['errors']}")
        logger.info("=" * 60)
    
    def import_from_jsdelivr(self):
        """Import depuis jsDelivr (validé)"""
        logger.info("=" * 60)
        logger.info("📦 IMPORT JSDELIVR CDN")
        logger.info("=" * 60)
        
        connector = JSDelivrConnector()
        conn = self.get_db_connection()
        
        # Collections disponibles
        collections = ['bukhari', 'muslim', 'abudawud', 'tirmidhi', 'nasai', 'ibnmajah']
        
        for collection in collections:
            logger.info(f"📖 Import {collection}...")
            
            try:
                hadiths = connector.fetch_collection(collection)
                
                if not hadiths:
                    logger.warning(f"   ⚠️  Aucun hadith trouvé")
                    continue
                
                logger.info(f"   📊 {len(hadiths)} hadiths récupérés")
                
                imported = 0
                
                for hadith in hadiths:
                    try:
                        # Vérifier doublon
                        cursor = conn.execute(
                            "SELECT 1 FROM hadiths WHERE source = ? AND hadith_number = ? LIMIT 1",
                            (f"jsdelivr/{collection}", str(hadith.get('number', '')))
                        )
                        
                        if cursor.fetchone():
                            self.stats['skipped'] += 1
                            continue
                        
                        # Insérer
                        conn.execute("""
                            INSERT INTO hadiths (
                                text_ar, text_fr, source, book,
                                hadith_number, narrator, grade, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                        """, (
                            hadith.get('arabic', ''),
                            hadith.get('text', ''),
                            f"jsdelivr/{collection}",
                            collection,
                            str(hadith.get('number', '')),
                            hadith.get('narrator', ''),
                            hadith.get('grade', '')
                        ))
                        
                        imported += 1
                        self.stats['imported'] += 1
                        
                    except Exception as e:
                        logger.error(f"Erreur insert: {e}")
                        self.stats['errors'] += 1
                
                conn.commit()
                logger.info(f"✅ {collection}: {imported} hadiths importés")
                
            except Exception as e:
                logger.error(f"❌ Erreur collection {collection}: {e}")
                self.stats['errors'] += 1
        
        conn.close()
        
        logger.info("=" * 60)
        logger.info(f"✅ Total importé: {self.stats['imported']}")
        logger.info(f"⚠️  Doublons évités: {self.stats['skipped']}")
        logger.info(f"❌ Erreurs: {self.stats['errors']}")
        logger.info("=" * 60)

def main():
    """Point d'entrée"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Import simple depuis connecteurs validés")
    parser.add_argument(
        '--source',
        choices=['gading', 'jsdelivr', 'all'],
        default='all',
        help="Source à importer"
    )
    
    args = parser.parse_args()
    
    importer = SimpleImporter()
    
    if args.source in ['gading', 'all']:
        importer.import_from_gading()
    
    if args.source in ['jsdelivr', 'all']:
        importer.import_from_jsdelivr()

if __name__ == "__main__":
    main()