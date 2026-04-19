#!/usr/bin/env python3
"""
GITHUB MASS IMPORTER
Importe massivement les hadiths depuis les repos GitHub découverts
"""

import sqlite3
import json
import hashlib
import os
import sys
from pathlib import Path
import logging
from datetime import datetime
import subprocess

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend/github_import.log'),
        logging.StreamHandler()
    ]
)

class GitHubMassImporter:
    def __init__(self):
        self.db_path = 'backend/almizane.db'
        self.corpus_dir = Path('backend/corpus')
        self.corpus_dir.mkdir(exist_ok=True)
        
        self.stats = {
            'total_processed': 0,
            'total_imported': 0,
            'duplicates': 0,
            'errors': 0
        }
        
        # Sources GitHub prioritaires
        self.github_sources = [
            {
                'name': 'AhmedBaset/hadith-json',
                'url': 'https://github.com/AhmedBaset/hadith-json.git',
                'path': 'hadith-json',
                'parser': 'parse_ahmedbaset',
                'priority': 1
            },
            {
                'name': 'abdelrahmaan/Hadith-Data-Sets',
                'url': 'https://github.com/abdelrahmaan/Hadith-Data-Sets.git',
                'path': 'Hadith-Data-Sets',
                'parser': 'parse_abdelrahmaan',
                'priority': 2
            },
            {
                'name': 'mhashim6/Open-Hadith-Data',
                'url': 'https://github.com/mhashim6/Open-Hadith-Data.git',
                'path': 'Open-Hadith-Data',
                'parser': 'parse_open_hadith',
                'priority': 3
            }
        ]
    
    def clone_repo(self, source):
        """Clone un repo GitHub"""
        repo_path = self.corpus_dir / source['path']
        
        if repo_path.exists():
            logging.info(f"✅ Repo déjà cloné: {source['name']}")
            return True
        
        try:
            logging.info(f"📥 Clonage de {source['name']}...")
            subprocess.run(
                ['git', 'clone', '--depth', '1', source['url'], str(repo_path)],
                check=True,
                capture_output=True
            )
            logging.info(f"✅ Repo cloné: {source['name']}")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"❌ Erreur clonage {source['name']}: {e}")
            return False
    
    def generate_hash(self, text_ar):
        """Génère un hash SHA-256 pour déduplication"""
        if not text_ar:
            return None
        normalized = text_ar.strip().replace(' ', '').replace('\n', '')
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    
    def hash_exists(self, conn, hash_value):
        """Vérifie si un hash existe déjà"""
        cursor = conn.execute(
            "SELECT 1 FROM hadiths WHERE content_hash = ? LIMIT 1",
            (hash_value,)
        )
        return cursor.fetchone() is not None
    
    def parse_ahmedbaset(self, repo_path):
        """Parse AhmedBaset/hadith-json (50,884 hadiths)"""
        hadiths = []
        db_path = repo_path / 'db' / 'by_book'
        
        if not db_path.exists():
            logging.warning(f"⚠️ Dossier db/by_book introuvable dans {repo_path}")
            return hadiths
        
        for book_file in db_path.glob('*.json'):
            try:
                with open(book_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    book_name = data.get('metadata', {}).get('name', book_file.stem)
                    
                    for hadith in data.get('hadiths', []):
                        hadiths.append({
                            'text_ar': hadith.get('arab', ''),
                            'text_en': hadith.get('english', ''),
                            'collection': book_name,
                            'book': hadith.get('book', ''),
                            'chapter': hadith.get('chapter', ''),
                            'hadith_number': hadith.get('id', ''),
                            'grade': hadith.get('grade', ''),
                            'narrator': hadith.get('narrator', ''),
                            'source': 'github_ahmedbaset'
                        })
                
                logging.info(f"✅ {book_file.name}: {len(data.get('hadiths', []))} hadiths")
            
            except Exception as e:
                logging.error(f"❌ Erreur parsing {book_file}: {e}")
        
        return hadiths
    
    def parse_abdelrahmaan(self, repo_path):
        """Parse abdelrahmaan/Hadith-Data-Sets (62,169 hadiths)"""
        hadiths = []
        
        # Chercher les fichiers JSON
        for json_file in repo_path.rglob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if isinstance(data, list):
                        for item in data:
                            hadiths.append({
                                'text_ar': item.get('text', item.get('arabic', '')),
                                'text_en': item.get('english', ''),
                                'collection': item.get('collection', json_file.stem),
                                'book': item.get('book', ''),
                                'chapter': item.get('chapter', ''),
                                'hadith_number': item.get('number', item.get('id', '')),
                                'grade': item.get('grade', ''),
                                'narrator': item.get('narrator', ''),
                                'source': 'github_abdelrahmaan'
                            })
                    
                    elif isinstance(data, dict):
                        for key, value in data.items():
                            if isinstance(value, list):
                                for item in value:
                                    hadiths.append({
                                        'text_ar': item.get('text', item.get('arabic', '')),
                                        'text_en': item.get('english', ''),
                                        'collection': key,
                                        'book': item.get('book', ''),
                                        'chapter': item.get('chapter', ''),
                                        'hadith_number': item.get('number', item.get('id', '')),
                                        'grade': item.get('grade', ''),
                                        'narrator': item.get('narrator', ''),
                                        'source': 'github_abdelrahmaan'
                                    })
                
                logging.info(f"✅ {json_file.name}: {len(hadiths)} hadiths")
            
            except Exception as e:
                logging.error(f"❌ Erreur parsing {json_file}: {e}")
        
        return hadiths
    
    def parse_open_hadith(self, repo_path):
        """Parse mhashim6/Open-Hadith-Data"""
        hadiths = []
        
        for json_file in repo_path.rglob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if isinstance(data, list):
                        for item in data:
                            hadiths.append({
                                'text_ar': item.get('text', item.get('arabic', item.get('hadith', ''))),
                                'text_en': item.get('english', ''),
                                'collection': item.get('collection', json_file.stem),
                                'book': item.get('book', ''),
                                'chapter': item.get('chapter', ''),
                                'hadith_number': item.get('number', item.get('id', '')),
                                'grade': item.get('grade', ''),
                                'narrator': item.get('narrator', ''),
                                'source': 'github_open_hadith'
                            })
                
                logging.info(f"✅ {json_file.name}: {len(hadiths)} hadiths")
            
            except Exception as e:
                logging.error(f"❌ Erreur parsing {json_file}: {e}")
        
        return hadiths
    
    def import_hadiths(self, hadiths):
        """Importe les hadiths dans la base"""
        conn = sqlite3.connect(self.db_path)
        imported = 0
        duplicates = 0
        
        for hadith in hadiths:
            self.stats['total_processed'] += 1
            
            try:
                # Génération hash
                content_hash = self.generate_hash(hadith['text_ar'])
                if not content_hash:
                    continue
                
                # Vérification doublon
                if self.hash_exists(conn, content_hash):
                    duplicates += 1
                    self.stats['duplicates'] += 1
                    continue
                
                # Insertion
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
                
                imported += 1
                self.stats['total_imported'] += 1
                
                # Commit tous les 100
                if imported % 100 == 0:
                    conn.commit()
                    logging.info(f"💾 {imported} hadiths importés, {duplicates} doublons")
            
            except Exception as e:
                self.stats['errors'] += 1
                logging.error(f"❌ Erreur import: {e}")
        
        conn.commit()
        conn.close()
        
        logging.info(f"✅ Import terminé: {imported} hadiths, {duplicates} doublons")
        return imported
    
    def run(self):
        """Lance l'import massif"""
        logging.info("🚀 DÉMARRAGE GITHUB MASS IMPORTER")
        logging.info(f"📊 Base actuelle: {self.get_current_count()} hadiths")
        
        for source in sorted(self.github_sources, key=lambda x: x['priority']):
            logging.info(f"\n{'='*60}")
            logging.info(f"📦 SOURCE: {source['name']}")
            logging.info(f"{'='*60}")
            
            # Clonage
            if not self.clone_repo(source):
                continue
            
            # Parsing
            repo_path = self.corpus_dir / source['path']
            parser_method = getattr(self, source['parser'])
            hadiths = parser_method(repo_path)
            
            logging.info(f"📊 {len(hadiths)} hadiths extraits")
            
            # Import
            if hadiths:
                self.import_hadiths(hadiths)
            
            # Rapport intermédiaire
            logging.info(f"\n📊 STATS CUMULÉES:")
            logging.info(f"   Traités: {self.stats['total_processed']:,}")
            logging.info(f"   Importés: {self.stats['total_imported']:,}")
            logging.info(f"   Doublons: {self.stats['duplicates']:,}")
            logging.info(f"   Erreurs: {self.stats['errors']:,}")
            logging.info(f"   Base totale: {self.get_current_count():,} hadiths")
        
        # Rapport final
        self.print_final_report()
    
    def get_current_count(self):
        """Compte les hadiths actuels"""
        conn = sqlite3.connect(self.db_path)
        count = conn.execute("SELECT COUNT(*) FROM hadiths").fetchone()[0]
        conn.close()
        return count
    
    def print_final_report(self):
        """Affiche le rapport final"""
        logging.info(f"\n{'='*60}")
        logging.info("📊 RAPPORT FINAL GITHUB MASS IMPORTER")
        logging.info(f"{'='*60}")
        logging.info(f"✅ Hadiths traités: {self.stats['total_processed']:,}")
        logging.info(f"✅ Hadiths importés: {self.stats['total_imported']:,}")
        logging.info(f"⚠️  Doublons évités: {self.stats['duplicates']:,}")
        logging.info(f"❌ Erreurs: {self.stats['errors']:,}")
        logging.info(f"📊 Base totale: {self.get_current_count():,} hadiths")
        logging.info(f"{'='*60}")

if __name__ == '__main__':
    importer = GitHubMassImporter()
    importer.run()