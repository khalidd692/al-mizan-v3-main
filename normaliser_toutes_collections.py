#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Normalise tous les noms de collections vers les noms standards"""

import sqlite3
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def normaliser_collections():
    """Normalise tous les noms de collections"""
    
    db_path = Path("backend/mizan.db")
    if not db_path.exists():
        print("[ERREUR] Base de données non trouvée")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Mapping des normalisations à effectuer
    normalisations = {
        'bukhari': 'Sahih al-Bukhari',
        'Sahih Bukhari': 'Sahih al-Bukhari',
        'muslim': 'Sahih Muslim',
        'nasai': "Sunan an-Nasa'i",
        'tirmidhi': 'Jami at-Tirmidhi',
        'tirmidzi': 'Jami at-Tirmidhi',
        "Jami' at-Tirmidhi": 'Jami at-Tirmidhi',
        'malik': 'Muwatta Malik',
        'darimi': 'Sunan ad-Darimi'
    }
    
    print("=" * 80)
    print("NORMALISATION DES COLLECTIONS")
    print("=" * 80)
    print()
    
    total_updated = 0
    
    for ancien_nom, nouveau_nom in normalisations.items():
        # Vérifier combien de hadiths ont cet ancien nom
        cursor.execute("""
            SELECT COUNT(*) FROM hadiths WHERE collection = ?
        """, (ancien_nom,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"[ACTION] '{ancien_nom}' -> '{nouveau_nom}': {count:,} hadiths")
            
            # Effectuer la normalisation
            cursor.execute("""
                UPDATE hadiths
                SET collection = ?
                WHERE collection = ?
            """, (nouveau_nom, ancien_nom))
            
            total_updated += count
    
    # Commit les changements
    conn.commit()
    
    print()
    print("=" * 80)
    print("RÉSULTAT")
    print("=" * 80)
    print(f"Total hadiths mis à jour: {total_updated:,}")
    
    # Afficher l'état final
    print()
    print("Collections après normalisation:")
    cursor.execute("""
        SELECT collection, COUNT(*) as count
        FROM hadiths
        GROUP BY collection
        ORDER BY count DESC
    """)
    
    for collection, count in cursor.fetchall():
        print(f"  - {collection}: {count:,} hadiths")
    
    conn.close()
    print()
    print("[SUCCESS] Normalisation terminée !")

if __name__ == "__main__":
    normaliser_collections()