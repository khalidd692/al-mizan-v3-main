#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Liste toutes les collections distinctes présentes dans la base"""

import sqlite3
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def lister_collections():
    db_path = Path("backend/mizan.db")
    if not db_path.exists():
        print("[ERREUR] Base de données non trouvée")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=" * 60)
    print("LISTE DES COLLECTIONS DISTINCTES")
    print("=" * 60)
    cursor.execute("""
        SELECT collection, COUNT(*) as count
        FROM hadiths
        GROUP BY collection
        ORDER BY count DESC
    """)
    for collection, count in cursor.fetchall():
        print(f"- {collection} : {count:,} hadiths")

    conn.close()

if __name__ == "__main__":
    lister_collections()