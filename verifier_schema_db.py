#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script pour vérifier la structure de la base de données"""

import sqlite3
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def verifier_schema():
    db_path = Path("backend/mizan.db")
    if not db_path.exists():
        print("[ERREUR] Base de données non trouvée")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Lister les tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("[INFO] Tables dans la base de données:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Vérifier la structure de la table hadiths
    print("\n[INFO] Structure de la table 'hadiths':")
    cursor.execute("PRAGMA table_info(hadiths)")
    columns = cursor.fetchall()
    
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Compter les hadiths par source
    print("\n[INFO] Statistiques par source:")
    cursor.execute("""
        SELECT source, COUNT(*) as count
        FROM hadiths
        GROUP BY source
        ORDER BY count DESC
        LIMIT 10
    """)
    
    sources = cursor.fetchall()
    for source, count in sources:
        print(f"  - {source}: {count:,} hadiths")
    
    conn.close()

if __name__ == "__main__":
    verifier_schema()