#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour nettoyer les doublons de collections dans la base de données
- Normalise "abudawud" → "Sunan Abu Dawud"
- Normalise "ibnmajah" → "Sunan Ibn Majah"
"""

import sqlite3
import sys
from pathlib import Path

# Force UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def nettoyer_doublons():
    """Nettoie les doublons de collections"""
    
    db_path = Path("backend/mizan.db")
    if not db_path.exists():
        print("[ERREUR] Base de données non trouvée")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("[INFO] Analyse des doublons...")
    
    # Vérifier les doublons
    cursor.execute("""
        SELECT collection, COUNT(*) as count
        FROM hadiths
        WHERE collection IN ('abudawud', 'ibnmajah', 'Sunan Abu Dawud', 'Sunan Ibn Majah')
        GROUP BY collection
        ORDER BY collection
    """)
    
    doublons = cursor.fetchall()
    print("\n[ETAT] État actuel:")
    for nom, count in doublons:
        print(f"  - {nom}: {count:,} hadiths")
    
    # Normaliser abudawud → Sunan Abu Dawud
    print("\n[ACTION] Normalisation de 'abudawud' -> 'Sunan Abu Dawud'...")
    cursor.execute("""
        UPDATE hadiths
        SET collection = 'Sunan Abu Dawud'
        WHERE collection = 'abudawud'
    """)
    abudawud_updated = cursor.rowcount
    print(f"  [OK] {abudawud_updated:,} hadiths mis à jour")
    
    # Normaliser ibnmajah → Sunan Ibn Majah
    print("\n[ACTION] Normalisation de 'ibnmajah' -> 'Sunan Ibn Majah'...")
    cursor.execute("""
        UPDATE hadiths
        SET collection = 'Sunan Ibn Majah'
        WHERE collection = 'ibnmajah'
    """)
    ibnmajah_updated = cursor.rowcount
    print(f"  [OK] {ibnmajah_updated:,} hadiths mis à jour")
    
    # Commit les changements
    conn.commit()
    
    # Vérifier le résultat
    print("\n[ETAT] État après nettoyage:")
    cursor.execute("""
        SELECT collection, COUNT(*) as count
        FROM hadiths
        WHERE collection IN ('abudawud', 'ibnmajah', 'Sunan Abu Dawud', 'Sunan Ibn Majah')
        GROUP BY collection
        ORDER BY collection
    """)
    
    apres = cursor.fetchall()
    for nom, count in apres:
        print(f"  - {nom}: {count:,} hadiths")
    
    # Statistiques finales
    print("\n[STATS] Statistiques globales:")
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT collection) as collections
        FROM hadiths
    """)
    total, collections = cursor.fetchone()
    print(f"  - Total hadiths: {total:,}")
    print(f"  - Collections uniques: {collections}")
    
    conn.close()
    
    print("\n[SUCCESS] Nettoyage terminé !")
    print(f"\n[INFO] Total mis à jour: {abudawud_updated + ibnmajah_updated:,} hadiths")

if __name__ == "__main__":
    nettoyer_doublons()