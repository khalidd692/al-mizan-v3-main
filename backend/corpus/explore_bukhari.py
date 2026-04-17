#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Explorer la structure de Sahih al-Bukhari dans mhashim6
"""

import requests
import json

def explore_bukhari():
    """Explorer Sahih al-Bukhari"""
    url = "https://api.github.com/repos/mhashim6/Open-Hadith-Data/contents/Sahih_Al-Bukhari"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        contents = response.json()
        
        print("=== STRUCTURE SAHIH AL-BUKHARI ===\n")
        print(f"Nombre de fichiers/dossiers: {len(contents)}\n")
        
        # Afficher les premiers éléments
        for i, item in enumerate(contents[:15]):
            icon = "📁" if item['type'] == 'dir' else "📄"
            size = f" ({item.get('size', 0)} bytes)" if item['type'] == 'file' else ""
            print(f"{icon} {item['name']}{size}")
            
            # Si c'est un fichier JSON, télécharger un exemple
            if i == 0 and item['type'] == 'file' and item['name'].endswith('.json'):
                print(f"\n📥 Téléchargement exemple: {item['name']}")
                file_response = requests.get(item['download_url'], timeout=10)
                if file_response.status_code == 200:
                    data = file_response.json()
                    print(f"Structure du fichier:")
                    print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
                    print("...\n")
        
        if len(contents) > 15:
            print(f"\n... et {len(contents) - 15} autres fichiers")
        
        return contents
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

if __name__ == '__main__':
    explore_bukhari()