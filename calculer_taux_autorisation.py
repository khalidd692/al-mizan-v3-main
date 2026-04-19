#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Calcule le taux d'autorisation des hadiths"""

import sqlite3
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def calculer_taux():
    db_path = Path("backend/mizan.db")
    if not db_path.exists():
        print("[ERREUR] Base de données non trouvée")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Total hadiths
    cursor.execute("SELECT COUNT(*) FROM hadiths")
    total = cursor.fetchone()[0]
    
    # Hadiths par collection
    cursor.execute("""
        SELECT collection, COUNT(*) as count
        FROM hadiths
        GROUP BY collection
        ORDER BY count DESC
    """)
    collections = cursor.fetchall()
    
    # Collections autorisées (celles qui matchent avec salafi_authorities.json)
    collections_autorisees = {
        'Sahih al-Bukhari',
        'Sahih Muslim', 
        'Sunan Abu Dawud',
        'Jami at-Tirmidhi',
        'Sunan an-Nasa\'i',
        'Sunan Ibn Majah',
        'Muwatta Malik',
        'Musnad Ahmad',
        'Sunan ad-Darimi',
        'forty_hadith_nawawi'
    }
    
    hadiths_autorises = 0
    hadiths_non_autorises = 0
    
    print("=" * 80)
    print("CALCUL DU TAUX D'AUTORISATION")
    print("=" * 80)
    print()
    
    for collection, count in collections:
        if collection in collections_autorisees:
            hadiths_autorises += count
            print(f"[OK] {collection}: {count:,} hadiths")
        else:
            hadiths_non_autorises += count
            print(f"[??] {collection}: {count:,} hadiths (non autorisé)")
    
    taux = (hadiths_autorises / total * 100) if total > 0 else 0
    
    print()
    print("=" * 80)
    print("RÉSULTATS")
    print("=" * 80)
    print(f"Total hadiths: {total:,}")
    print(f"Hadiths autorisés: {hadiths_autorises:,}")
    print(f"Hadiths non autorisés: {hadiths_non_autorises:,}")
    print(f"Taux d'autorisation: {taux:.2f}%")
    print()
    
    if taux >= 95:
        print("[SUCCESS] Objectif atteint ! (>= 95%)")
    else:
        print(f"[INFO] Objectif non atteint. Manque {95 - taux:.2f}% pour atteindre 95%")
    
    conn.close()

if __name__ == "__main__":
    calculer_taux()