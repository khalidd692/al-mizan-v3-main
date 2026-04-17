#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Télécharger et analyser un échantillon de Sahih al-Bukhari
"""

import requests
import csv
from io import StringIO

def download_bukhari_sample():
    """Télécharger les premières lignes de Sahih al-Bukhari"""
    url = "https://raw.githubusercontent.com/mhashim6/Open-Hadith-Data/master/Sahih_Al-Bukhari/sahih_al-bukhari_ahadith.utf8.csv"
    
    print("=== TÉLÉCHARGEMENT SAHIH AL-BUKHARI ===\n")
    print(f"URL: {url}\n")
    
    try:
        # Télécharger avec streaming pour limiter la taille
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Lire les premières lignes
        lines = []
        for i, line in enumerate(response.iter_lines()):
            if i < 10:  # Limiter à 10 lignes
                if isinstance(line, bytes):
                    lines.append(line.decode('utf-8'))
                else:
                    lines.append(line)
            else:
                break
        
        # Analyser le CSV
        csv_data = StringIO('\n'.join(lines))
        reader = csv.reader(csv_data)
        
        print("📊 STRUCTURE DU CSV:\n")
        for i, row in enumerate(reader):
            if i == 0:
                print(f"En-têtes ({len(row)} colonnes):")
                for j, header in enumerate(row):
                    print(f"  {j+1}. {header}")
                print()
            else:
                print(f"Ligne {i}:")
                for j, value in enumerate(row[:5]):  # Limiter à 5 colonnes
                    print(f"  {value[:100]}..." if len(value) > 100 else f"  {value}")
                if len(row) > 5:
                    print(f"  ... et {len(row) - 5} autres colonnes")
                print()
        
        print("✅ Échantillon téléchargé avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == '__main__':
    download_bukhari_sample()