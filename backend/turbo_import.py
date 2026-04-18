#!/usr/bin/env python3
"""
TURBO IMPORT - Import par lots de 1000 hadiths
Utilise l'API range pour importer massivement
"""

import requests
import sqlite3
import logging
import hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TurboImporter:
    """Import ultra-rapide par lots de 1000"""
    
    def __init__(self, db_path: str = "backend/almizane.db"):
        self.db_path = db_path
        self.base_url = "https://api.hadith.gading.dev"
        self.stats = {'imported': 0, 'skipped': 0, 'errors': 0}
        self.batch_size = 100  # Taille des lots (API limite à 100)
    
    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def fetch_batch(self, book_name: str, start: int, end: int):
        """Récupère un lot de hadiths via l'API range"""
        try:
            url = f"{self.base_url}/books/{book_name}?range={start}-{end}"
            resp = requests.get(url, timeout=30)
            
            if resp.status_code != 200:
                logger.error(f"❌ Erreur API {resp.status_code} pour {book_name} {start}-{end}")
                return []
            
            data = resp.json()
            if data.get('code') != 200:
                logger.error(f"❌ Erreur: {data.get('message')}")
                return []
            
            hadiths_data = data.get('data', {}).get('hadiths', [])
            logger.info(f"✓ Récupéré lot {start}-{end} ({len(hadiths_data)} hadiths)")
            return hadiths_data
            
        except Exception as e:
            logger.error(f"❌ Erreur fetch {book_name} {start}-{end}: {e}")
            return []
    
    def import_batch(self, book_name: str, hadiths_data: list):
        """Importe un lot de hadiths en base"""
        conn = self.get_db_connection()
        imported = 0
        
        try:
            for hadith_item in hadiths_data:
                try:
                    num = hadith_item.get('number', 0)
                    hadith = hadith_item.get('contents', {})
                    
                    # Vérifier doublon
                    cursor = conn.execute(
                        "SELECT 1 FROM hadiths WHERE source_api = ? AND collection = ? AND numero_hadith = ? LIMIT 1",
                        ("hadith_gading", book_name, str(num))
                    )
                    
                    if cursor.fetchone():
                        self.stats['skipped'] += 1
                        continue
                    
                    # Générer SHA256
                    matn_ar = hadith.get('arab', '')
                    matn_fr = hadith.get('id', '')
                    hash_content = f"{matn_ar}|{book_name}|{num}"
                    sha256_hash = hashlib.sha256(hash_content.encode('utf-8')).hexdigest()
                    
                    # Insérer
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
                        "non_évalué",
                        "MAQBUL",
                        datetime.now().isoformat()
                    ))
                    
                    imported += 1
                    self.stats['imported'] += 1
                    
                except Exception as e:
                    self.stats['errors'] += 1
                    if self.stats['errors'] <= 5:
                        logger.error(f"❌ Erreur hadith: {e}")
            
            conn.commit()
            logger.info(f"✅ Lot importé: {imported} hadiths")
            
        except Exception as e:
            logger.error(f"❌ Erreur import lot: {e}")
        finally:
            conn.close()
        
        return imported
    
    def import_book_turbo(self, book_name: str, limit: int = 10000):
        """Import ultra-rapide d'un livre par lots de 1000"""
        logger.info(f"🚀 TURBO IMPORT {book_name.upper()}")
        logger.info("=" * 60)
        
        # Récupérer le total disponible
        try:
            resp = requests.get(f"{self.base_url}/books/{book_name}?range=1-1", timeout=10)
            data = resp.json()
            total = data.get('data', {}).get('available', 0)
            logger.info(f"📊 {total} hadiths disponibles")
            logger.info(f"🎯 Import limité à {limit} hadiths")
            logger.info(f"📦 Taille des lots: {self.batch_size}")
            logger.info("=" * 60)
        except Exception as e:
            logger.error(f"❌ Erreur récupération total: {e}")
            return 0
        
        # Calculer les lots
        max_import = min(total, limit)
        batches = []
        for start in range(1, max_import + 1, self.batch_size):
            end = min(start + self.batch_size - 1, max_import)
            batches.append((start, end))
        
        logger.info(f"📦 {len(batches)} lots à importer")
        
        # Import séquentiel des lots (plus stable que parallèle)
        total_imported = 0
        for i, (start, end) in enumerate(batches, 1):
            logger.info(f"\n📦 LOT {i}/{len(batches)}: {start}-{end}")
            
            # Fetch
            hadiths_data = self.fetch_batch(book_name, start, end)
            
            if hadiths_data:
                # Import
                imported = self.import_batch(book_name, hadiths_data)
                total_imported += imported
                
                logger.info(f"✅ Progression: {total_imported}/{max_import} ({total_imported*100//max_import}%)")
            else:
                logger.warning(f"⚠️  Lot vide ou erreur")
        
        logger.info("=" * 60)
        logger.info(f"✅ {book_name.upper()} TERMINÉ: {total_imported} hadiths")
        logger.info("=" * 60)
        
        return total_imported
    
    def import_all_turbo(self, limit_per_book: int = 10000):
        """Import tous les livres en mode turbo"""
        logger.info("=" * 60)
        logger.info("🚀 TURBO IMPORT - TOUS LES LIVRES")
        logger.info("=" * 60)
        
        books = [
            ('bukhari', 6638),
            ('muslim', 5362),
            ('abudawud', 4590),
            ('tirmidzi', 3891),
            ('nasai', 5662),
            ('ibnmajah', 4331)
        ]
        
        for book_name, expected in books:
            logger.info(f"\n📖 {book_name.upper()} ({expected} hadiths attendus)")
            self.import_book_turbo(book_name, limit_per_book)
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 IMPORT COMPLET TERMINÉ")
        logger.info("=" * 60)
        logger.info(f"✅ Total importé: {self.stats['imported']}")
        logger.info(f"⚠️  Doublons évités: {self.stats['skipped']}")
        logger.info(f"❌ Erreurs: {self.stats['errors']}")
        logger.info("=" * 60)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="TURBO Import Hadith Gading")
    parser.add_argument('--book', help="Livre spécifique (bukhari, muslim, etc.)")
    parser.add_argument('--limit', type=int, default=10000, help="Limite par livre (défaut: 10000)")
    parser.add_argument('--all', action='store_true', help="Importer tous les livres")
    
    args = parser.parse_args()
    
    importer = TurboImporter()
    
    if args.all:
        importer.import_all_turbo(args.limit)
    elif args.book:
        importer.import_book_turbo(args.book, args.limit)
    else:
        # Par défaut: Bukhari complet
        importer.import_book_turbo('bukhari', 7000)

if __name__ == "__main__":
    main()