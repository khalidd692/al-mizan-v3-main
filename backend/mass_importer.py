#!/usr/bin/env python3
"""
Mass Hadith Importer - Solution 100% GRATUITE
Importe 125K+ hadiths depuis 5 sources gratuites vérifiées
"""

import asyncio
import aiohttp
import sqlite3
import json
import hashlib
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import logging
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FreeHadithImporter:
    """Import massif depuis sources 100% gratuites"""
    
    def __init__(self, db_path: str = "backend/almizane.db"):
        self.db_path = db_path
        self.corpus_dir = Path("corpus")
        self.corpus_dir.mkdir(exist_ok=True)
        
        self.stats = {
            "total_imported": 0,
            "duplicates_skipped": 0,
            "errors": 0,
            "sources": {}
        }
    
    def get_db_connection(self):
        """Connexion SQLite"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def compute_hash(self, text_ar: str, source: str) -> str:
        """Hash pour déduplication"""
        content = f"{text_ar}:{source}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def check_duplicate(self, hadith_hash: str) -> bool:
        """Vérifie si hadith existe"""
        conn = self.get_db_connection()
        cursor = conn.execute(
            "SELECT 1 FROM hadiths WHERE hash = ? LIMIT 1",
            (hadith_hash,)
        )
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    
    def bulk_insert(self, hadiths: List[Dict], batch_size: int = 1000):
        """Insert par batch"""
        conn = self.get_db_connection()
        
        inserted = 0
        skipped = 0
        
        for i in range(0, len(hadiths), batch_size):
            batch = hadiths[i:i+batch_size]
            
            for hadith in batch:
                try:
                    hadith_hash = self.compute_hash(
                        hadith['text_ar'],
                        hadith['source']
                    )
                    
                    if self.check_duplicate(hadith_hash):
                        skipped += 1
                        continue
                    
                    conn.execute("""
                        INSERT INTO hadiths (
                            text_ar, text_fr, source, book, chapter,
                            hadith_number, grade, narrator, chain,
                            hash, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        hadith.get('text_ar'),
                        hadith.get('text_fr'),
                        hadith.get('source'),
                        hadith.get('book'),
                        hadith.get('chapter'),
                        hadith.get('hadith_number'),
                        hadith.get('grade'),
                        hadith.get('narrator'),
                        hadith.get('chain'),
                        hadith_hash,
                        datetime.now().isoformat()
                    ))
                    
                    inserted += 1
                    
                except Exception as e:
                    logger.error(f"Erreur insert: {e}")
                    self.stats['errors'] += 1
            
            conn.commit()
            logger.info(f"✓ Batch {i//batch_size + 1}: {inserted} insérés, {skipped} doublons")
        
        conn.close()
        return inserted, skipped
    
    # ==================== SOURCE 1: SUNNAH.COM API (50K) ====================
    
    async def import_sunnah_com(self) -> int:
        """Import Sunnah.com API - 50K hadiths GRATUIT"""
        logger.info("=" * 60)
        logger.info("📦 SOURCE 1: SUNNAH.COM API (50K hadiths)")
        logger.info("=" * 60)
        
        all_hadiths = []
        
        # Collections principales
        collections = [
            'bukhari', 'muslim', 'nasai', 'abudawud', 
            'tirmidhi', 'ibnmajah', 'malik', 'ahmad'
        ]
        
        async with aiohttp.ClientSession() as session:
            for collection in collections:
                logger.info(f"📖 Récupération {collection}...")
                
                try:
                    # API Sunnah.com
                    url = f"https://api.sunnah.com/v1/collections/{collection}/hadiths"
                    headers = {'X-API-Key': 'SqD712P3E82xnwOAEOkGd5JZH8s9wRR24TqNFzjk'}
                    
                    async with session.get(url, headers=headers, timeout=30) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            hadiths = self.parse_sunnah_api(data, collection)
                            all_hadiths.extend(hadiths)
                            logger.info(f"   ✓ {len(hadiths)} hadiths extraits")
                        else:
                            logger.warning(f"   ⚠️  Status {resp.status}")
                    
                    await asyncio.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"   ❌ Erreur: {e}")
        
        # Insert
        logger.info(f"💾 Insertion de {len(all_hadiths)} hadiths...")
        inserted, skipped = self.bulk_insert(all_hadiths)
        
        self.stats['sources']['sunnah_com'] = {
            'imported': inserted,
            'skipped': skipped
        }
        
        logger.info(f"✅ Sunnah.com: {inserted} hadiths importés")
        return inserted
    
    def parse_sunnah_api(self, data: Dict, collection: str) -> List[Dict]:
        """Parse réponse API Sunnah.com"""
        hadiths = []
        
        raw_hadiths = data.get('data', [])
        
        for h in raw_hadiths:
            hadith = {
                'text_ar': h.get('hadithArabic', ''),
                'text_fr': h.get('hadithEnglish', ''),
                'source': f"sunnah.com/{collection}",
                'book': h.get('bookSlug', collection),
                'chapter': h.get('chapterTitle', ''),
                'hadith_number': str(h.get('hadithNumber', '')),
                'grade': ', '.join([g.get('grade', '') for g in h.get('grades', [])]),
                'narrator': h.get('narrator', ''),
                'chain': ''
            }
            
            if hadith['text_ar']:
                hadiths.append(hadith)
        
        return hadiths
    
    # ==================== SOURCE 2: HADITH API (30K) ====================
    
    async def import_hadith_api(self) -> int:
        """Import Hadith API GitHub - 30K hadiths GRATUIT"""
        logger.info("=" * 60)
        logger.info("📦 SOURCE 2: HADITH API (30K hadiths)")
        logger.info("=" * 60)
        
        repo_path = self.corpus_dir / "hadith-api"
        
        if not repo_path.exists():
            logger.info("⬇️  Clonage du repo GitHub...")
            try:
                subprocess.run([
                    'git', 'clone',
                    'https://github.com/fawazahmed0/hadith-api',
                    str(repo_path)
                ], check=True)
                logger.info("✅ Repo cloné")
            except Exception as e:
                logger.error(f"❌ Erreur clone: {e}")
                return 0
        
        # Parse editions
        editions_dir = repo_path / "editions"
        if not editions_dir.exists():
            logger.error("❌ Dossier editions introuvable")
            return 0
        
        all_hadiths = []
        
        for json_file in editions_dir.glob("**/*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                hadiths = self.parse_hadith_api_json(data)
                all_hadiths.extend(hadiths)
                
            except Exception as e:
                logger.error(f"Erreur {json_file}: {e}")
        
        logger.info(f"💾 Insertion de {len(all_hadiths)} hadiths...")
        inserted, skipped = self.bulk_insert(all_hadiths)
        
        self.stats['sources']['hadith_api'] = {
            'imported': inserted,
            'skipped': skipped
        }
        
        logger.info(f"✅ Hadith API: {inserted} hadiths importés")
        return inserted
    
    def parse_hadith_api_json(self, data: Dict) -> List[Dict]:
        """Parse JSON Hadith API"""
        hadiths = []
        
        for h in data.get('hadiths', []):
            hadith = {
                'text_ar': h.get('arab', ''),
                'text_fr': h.get('text', ''),
                'source': 'hadith-api',
                'book': data.get('metadata', {}).get('name', ''),
                'chapter': h.get('chapterName', ''),
                'hadith_number': str(h.get('hadithnumber', '')),
                'grade': h.get('grades', [{}])[0].get('grade', ''),
                'narrator': '',
                'chain': ''
            }
            
            if hadith['text_ar']:
                hadiths.append(hadith)
        
        return hadiths
    
    # ==================== SOURCE 3: HADITH GADING (20K) ====================
    
    async def import_hadith_gading(self) -> int:
        """Import Hadith Gading API - 20K hadiths GRATUIT"""
        logger.info("=" * 60)
        logger.info("📦 SOURCE 3: HADITH GADING (20K hadiths)")
        logger.info("=" * 60)
        
        base_url = "https://api.hadith.gading.dev"
        books = ['bukhari', 'muslim', 'tirmidzi', 'abudaud', 'nasai', 'ibnumajah']
        
        all_hadiths = []
        
        async with aiohttp.ClientSession() as session:
            for book in books:
                logger.info(f"📖 Récupération {book}...")
                
                try:
                    # Get total
                    async with session.get(f"{base_url}/books/{book}") as resp:
                        data = await resp.json()
                        total = data.get('data', {}).get('available', 0)
                    
                    # Fetch hadiths
                    for i in range(1, min(total + 1, 5000)):  # Limite 5000/livre
                        try:
                            async with session.get(
                                f"{base_url}/books/{book}/{i}"
                            ) as resp:
                                data = await resp.json()
                                
                                if data.get('data'):
                                    h = data['data']
                                    hadith = {
                                        'text_ar': h.get('arab', ''),
                                        'text_fr': h.get('id', ''),  # Indonésien
                                        'source': f"hadith.gading.dev/{book}",
                                        'book': book,
                                        'chapter': '',
                                        'hadith_number': str(h.get('number', '')),
                                        'grade': '',
                                        'narrator': '',
                                        'chain': ''
                                    }
                                    
                                    if hadith['text_ar']:
                                        all_hadiths.append(hadith)
                            
                            if i % 100 == 0:
                                logger.info(f"   ✓ {i}/{total}")
                            
                            await asyncio.sleep(0.1)  # Rate limit
                            
                        except Exception as e:
                            logger.error(f"Erreur hadith {i}: {e}")
                            continue
                    
                except Exception as e:
                    logger.error(f"Erreur livre {book}: {e}")
        
        logger.info(f"💾 Insertion de {len(all_hadiths)} hadiths...")
        inserted, skipped = self.bulk_insert(all_hadiths)
        
        self.stats['sources']['hadith_gading'] = {
            'imported': inserted,
            'skipped': skipped
        }
        
        logger.info(f"✅ Hadith Gading: {inserted} hadiths importés")
        return inserted
    
    # ==================== SOURCE 4: DORAR.NET (15K) ====================
    
    async def import_dorar(self) -> int:
        """Import Dorar.net - 15K hadiths GRATUIT"""
        logger.info("=" * 60)
        logger.info("📦 SOURCE 4: DORAR.NET (15K hadiths)")
        logger.info("=" * 60)
        
        # Utilise le connecteur existant
        from connectors.dorar_connector import DorarConnector
        
        connector = DorarConnector()
        all_hadiths = []
        
        # Livres principaux
        books = [1, 2, 3, 4, 5, 6]  # IDs Bukhari, Muslim, etc.
        
        for book_id in books:
            logger.info(f"📖 Récupération livre {book_id}...")
            
            try:
                hadiths = await connector.fetch_book(book_id)
                all_hadiths.extend(hadiths)
                logger.info(f"   ✓ {len(hadiths)} hadiths")
                
            except Exception as e:
                logger.error(f"Erreur livre {book_id}: {e}")
        
        logger.info(f"💾 Insertion de {len(all_hadiths)} hadiths...")
        inserted, skipped = self.bulk_insert(all_hadiths)
        
        self.stats['sources']['dorar'] = {
            'imported': inserted,
            'skipped': skipped
        }
        
        logger.info(f"✅ Dorar.net: {inserted} hadiths importés")
        return inserted
    
    # ==================== SOURCE 5: HADEETHENC (10K) ====================
    
    async def import_hadeethenc(self) -> int:
        """Import HadeethEnc API - 10K hadiths GRATUIT"""
        logger.info("=" * 60)
        logger.info("📦 SOURCE 5: HADEETHENC (10K hadiths)")
        logger.info("=" * 60)
        
        base_url = "https://hadeethenc.com/api/v1"
        all_hadiths = []
        
        async with aiohttp.ClientSession() as session:
            # Categories
            categories = [1, 2, 3, 4, 5]  # IDs principales
            
            for cat_id in categories:
                logger.info(f"📖 Catégorie {cat_id}...")
                
                try:
                    async with session.get(
                        f"{base_url}/hadeeths/list",
                        params={'language': 'ar', 'category_id': cat_id}
                    ) as resp:
                        data = await resp.json()
                        
                        for h in data.get('data', []):
                            hadith = {
                                'text_ar': h.get('hadeeth', ''),
                                'text_fr': h.get('translation', ''),
                                'source': 'hadeethenc.com',
                                'book': h.get('attribution', ''),
                                'chapter': h.get('category', ''),
                                'hadith_number': str(h.get('id', '')),
                                'grade': h.get('grade', ''),
                                'narrator': '',
                                'chain': ''
                            }
                            
                            if hadith['text_ar']:
                                all_hadiths.append(hadith)
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Erreur catégorie {cat_id}: {e}")
        
        logger.info(f"💾 Insertion de {len(all_hadiths)} hadiths...")
        inserted, skipped = self.bulk_insert(all_hadiths)
        
        self.stats['sources']['hadeethenc'] = {
            'imported': inserted,
            'skipped': skipped
        }
        
        logger.info(f"✅ HadeethEnc: {inserted} hadiths importés")
        return inserted
    
    # ==================== ORCHESTRATION ====================
    
    async def import_all(self):
        """Import toutes les sources gratuites"""
        logger.info("=" * 60)
        logger.info("🚀 IMPORT MASSIF - SOLUTION 100% GRATUITE")
        logger.info("=" * 60)
        logger.info("5 sources gratuites identifiées")
        logger.info("Objectif: 125K+ hadiths, 0€")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        # Source 1: Sunnah.com (50K)
        await self.import_sunnah_com()
        
        # Source 2: Hadith API (30K)
        await self.import_hadith_api()
        
        # Source 3: Hadith Gading (20K)
        await self.import_hadith_gading()
        
        # Source 4: Dorar.net (15K)
        await self.import_dorar()
        
        # Source 5: HadeethEnc (10K)
        await self.import_hadeethenc()
        
        # Stats finales
        duration = (datetime.now() - start_time).total_seconds()
        total_imported = sum(s['imported'] for s in self.stats['sources'].values())
        total_skipped = sum(s['skipped'] for s in self.stats['sources'].values())
        
        logger.info("=" * 60)
        logger.info("📊 STATISTIQUES FINALES")
        logger.info("=" * 60)
        logger.info(f"⏱️  Durée: {duration/60:.1f} minutes")
        logger.info(f"✅ Total importé: {total_imported:,} hadiths")
        logger.info(f"⚠️  Doublons évités: {total_skipped:,}")
        logger.info(f"❌ Erreurs: {self.stats['errors']}")
        logger.info(f"💰 Coût: 0€")
        logger.info("")
        logger.info("Détail par source:")
        
        for source, stats in self.stats['sources'].items():
            logger.info(f"  • {source}: {stats['imported']:,} hadiths")
        
        logger.info("=" * 60)
        logger.info("✅ IMPORT TERMINÉ - 100% GRATUIT")
        logger.info("=" * 60)

async def main():
    """Point d'entrée"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Import massif de hadiths - Solution 100% GRATUITE"
    )
    parser.add_argument(
        '--source',
        choices=[
            'sunnah_com',
            'hadith_api', 
            'hadith_gading',
            'dorar',
            'hadeethenc',
            'all'
        ],
        default='all',
        help="Source à importer (défaut: all)"
    )
    parser.add_argument(
        '--db',
        default='backend/almizane.db',
        help="Chemin base de données"
    )
    
    args = parser.parse_args()
    
    importer = FreeHadithImporter(db_path=args.db)
    
    if args.source == 'all':
        await importer.import_all()
    elif args.source == 'sunnah_com':
        await importer.import_sunnah_com()
    elif args.source == 'hadith_api':
        await importer.import_hadith_api()
    elif args.source == 'hadith_gading':
        await importer.import_hadith_gading()
    elif args.source == 'dorar':
        await importer.import_dorar()
    elif args.source == 'hadeethenc':
        await importer.import_hadeethenc()

if __name__ == "__main__":
    asyncio.run(main())