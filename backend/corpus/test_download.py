#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de téléchargement limité - AL-MĪZĀN V6.0
Télécharge uniquement Sahih al-Bukhari pour test
"""

import sys
import os
import json
import logging

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.corpus.downloader import SourceDownloader
from backend.corpus.sources_registry import get_source_by_id

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_download_sample():
    """Test de téléchargement d'un échantillon"""
    print("=== TEST TÉLÉCHARGEMENT ÉCHANTILLON ===\n")
    
    downloader = SourceDownloader(output_dir="corpus/raw_test")
    source = get_source_by_id('hadith-json-ahmedbaset')
    
    print(f"Source: {source['name']}")
    print(f"URL: {source['url']}")
    print(f"Fiabilité: {source['reliability_score']}/100\n")
    
    # Télécharger uniquement Sahih al-Bukhari
    from pathlib import Path
    
    source_dir = Path("corpus/raw_test/ahmedbaset")
    source_dir.mkdir(parents=True, exist_ok=True)
    
    url = f"{source['raw_data_url']}/bukhari.json"
    output_path = source_dir / "bukhari.json"
    
    print(f"📥 Téléchargement de Sahih al-Bukhari...")
    print(f"URL: {url}")
    
    if downloader.download_file(url, output_path):
        print(f"✅ Téléchargement réussi: {output_path}")
        
        # Analyser le fichier
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if isinstance(data, dict):
            print(f"\n📊 Structure du fichier:")
            print(f"  Clés: {list(data.keys())}")
            
            if 'hadiths' in data:
                hadiths = data['hadiths']
                print(f"  Total hadiths: {len(hadiths)}")
                
                if hadiths:
                    print(f"\n📖 Premier hadith (échantillon):")
                    first = hadiths[0]
                    for key, value in list(first.items())[:5]:
                        if isinstance(value, str) and len(value) > 100:
                            print(f"  {key}: {value[:100]}...")
                        else:
                            print(f"  {key}: {value}")
        elif isinstance(data, list):
            print(f"\n📊 Liste de {len(data)} éléments")
            if data:
                print(f"\n📖 Premier élément (échantillon):")
                first = data[0]
                for key, value in list(first.items())[:5]:
                    if isinstance(value, str) and len(value) > 100:
                        print(f"  {key}: {value[:100]}...")
                    else:
                        print(f"  {key}: {value}")
        
        print(f"\n✅ TEST RÉUSSI")
        return True
    else:
        print(f"❌ Échec du téléchargement")
        return False

if __name__ == '__main__':
    success = test_download_sample()
    sys.exit(0 if success else 1)