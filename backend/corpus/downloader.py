#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de téléchargement des sources AL-MĪZĀN V6.0
Téléchargement depuis GitHub, Hugging Face et sites officiels
"""

import os
import json
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import time

from .sources_registry import (
    get_downloadable_sources,
    get_source_by_id,
    format_source_for_db
)

logger = logging.getLogger(__name__)

class SourceDownloader:
    """Gestionnaire de téléchargement des sources"""
    
    def __init__(self, output_dir: str = "corpus/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Al-Mizan-V6-Academic-Corpus/1.0'
        })
    
    def download_file(self, url: str, output_path: Path, timeout: int = 30) -> bool:
        """Télécharger un fichier depuis une URL"""
        try:
            logger.info(f"Téléchargement: {url}")
            response = self.session.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"✅ Téléchargé: {output_path}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur téléchargement {url}: {e}")
            return False
    
    def download_json(self, url: str, timeout: int = 30) -> Optional[Dict]:
        """Télécharger et parser un fichier JSON"""
        try:
            logger.info(f"Téléchargement JSON: {url}")
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Erreur JSON {url}: {e}")
            return None
    
    def download_ahmedbaset_hadith_json(self) -> Dict[str, Any]:
        """Télécharger AhmedBaset/hadith-json"""
        source = get_source_by_id('hadith-json-ahmedbaset')
        source_dir = self.output_dir / 'ahmedbaset'
        source_dir.mkdir(exist_ok=True)
        
        results = {
            'source_id': source['id'],
            'source_name': source['name'],
            'timestamp': datetime.now().isoformat(),
            'books_downloaded': [],
            'total_hadiths': 0,
            'errors': []
        }
        
        # Liste des livres à télécharger
        books_to_download = [
            ('bukhari', 'bukhari.json'),
            ('muslim', 'muslim.json'),
            ('tirmidhi', 'tirmidhi.json'),
            ('abudawud', 'abudawud.json'),
            ('nasai', 'nasai.json'),
            ('ibnmajah', 'ibnmajah.json')
        ]
        
        for book_id, filename in books_to_download:
            url = f"{source['raw_data_url']}/{filename}"
            output_path = source_dir / filename
            
            # Télécharger
            if self.download_file(url, output_path):
                # Compter les hadiths
                try:
                    with open(output_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        hadith_count = len(data) if isinstance(data, list) else len(data.get('hadiths', []))
                        results['books_downloaded'].append({
                            'book': book_id,
                            'file': str(output_path),
                            'hadith_count': hadith_count
                        })
                        results['total_hadiths'] += hadith_count
                except Exception as e:
                    results['errors'].append(f"Erreur lecture {filename}: {e}")
            else:
                results['errors'].append(f"Échec téléchargement {filename}")
            
            # Pause pour éviter rate limiting
            time.sleep(1)
        
        return results
    
    def download_mhashim_open_hadith(self) -> Dict[str, Any]:
        """Télécharger mhashim6/Open-Hadith-Data"""
        source = get_source_by_id('open-hadith-data-mhashim')
        source_dir = self.output_dir / 'mhashim'
        source_dir.mkdir(exist_ok=True)
        
        results = {
            'source_id': source['id'],
            'source_name': source['name'],
            'timestamp': datetime.now().isoformat(),
            'books_downloaded': [],
            'total_hadiths': 0,
            'errors': []
        }
        
        # Tenter de télécharger les fichiers principaux
        books = ['bukhari', 'muslim', 'tirmidhi', 'abudawud', 'nasai', 'ibnmajah']
        
        for book in books:
            # Essayer différents formats de noms de fichiers
            possible_filenames = [
                f"{book}.json",
                f"{book}_data.json",
                f"sahih_{book}.json"
            ]
            
            downloaded = False
            for filename in possible_filenames:
                url = f"{source['raw_data_url']}/{filename}"
                output_path = source_dir / filename
                
                if self.download_file(url, output_path):
                    try:
                        with open(output_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            hadith_count = len(data) if isinstance(data, list) else len(data.get('hadiths', []))
                            results['books_downloaded'].append({
                                'book': book,
                                'file': str(output_path),
                                'hadith_count': hadith_count
                            })
                            results['total_hadiths'] += hadith_count
                            downloaded = True
                            break
                    except Exception as e:
                        results['errors'].append(f"Erreur lecture {filename}: {e}")
            
            if not downloaded:
                results['errors'].append(f"Aucun fichier trouvé pour {book}")
            
            time.sleep(1)
        
        return results
    
    def download_all_sources(self) -> Dict[str, Any]:
        """Télécharger toutes les sources disponibles"""
        logger.info("=== DÉBUT TÉLÉCHARGEMENT SOURCES ===")
        
        overall_results = {
            'timestamp': datetime.now().isoformat(),
            'sources': [],
            'total_hadiths': 0,
            'total_errors': 0
        }
        
        # AhmedBaset/hadith-json (priorité 1)
        logger.info("\n📥 Téléchargement AhmedBaset/hadith-json...")
        result1 = self.download_ahmedbaset_hadith_json()
        overall_results['sources'].append(result1)
        overall_results['total_hadiths'] += result1['total_hadiths']
        overall_results['total_errors'] += len(result1['errors'])
        
        # mhashim6/Open-Hadith-Data (priorité 2)
        logger.info("\n📥 Téléchargement mhashim6/Open-Hadith-Data...")
        result2 = self.download_mhashim_open_hadith()
        overall_results['sources'].append(result2)
        overall_results['total_hadiths'] += result2['total_hadiths']
        overall_results['total_errors'] += len(result2['errors'])
        
        # Sauvegarder le rapport
        report_path = self.output_dir / 'download_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(overall_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✅ Rapport sauvegardé: {report_path}")
        logger.info(f"📊 Total hadiths téléchargés: {overall_results['total_hadiths']}")
        logger.info(f"⚠️  Total erreurs: {overall_results['total_errors']}")
        
        return overall_results

def main():
    """Point d'entrée principal"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    downloader = SourceDownloader()
    results = downloader.download_all_sources()
    
    print("\n" + "="*60)
    print("RÉSUMÉ TÉLÉCHARGEMENT")
    print("="*60)
    print(f"Total hadiths: {results['total_hadiths']}")
    print(f"Sources traitées: {len(results['sources'])}")
    print(f"Erreurs: {results['total_errors']}")
    
    for source_result in results['sources']:
        print(f"\n{source_result['source_name']}:")
        print(f"  Livres: {len(source_result['books_downloaded'])}")
        print(f"  Hadiths: {source_result['total_hadiths']}")
        if source_result['errors']:
            print(f"  Erreurs: {len(source_result['errors'])}")

if __name__ == '__main__':
    main()