#!/usr/bin/env python3
"""Vérifie la progression des harvesters actifs"""

import sqlite3
import os
from datetime import datetime

def check_progress():
    db_path = 'backend/almizane.db'
    
    if not os.path.exists(db_path):
        print("Base de données introuvable")
        return
    
    conn = sqlite3.connect(db_path)
    
    # Total actuel
    total = conn.execute("SELECT COUNT(*) FROM hadiths").fetchone()[0]
    
    # Par source
    print(f"\n{'='*60}")
    print(f"PROGRESSION HARVESTING - {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")
    print(f"\nTOTAL: {total:,} hadiths\n")
    
    print("Par source:")
    sources = conn.execute("""
        SELECT source, COUNT(*) as count
        FROM hadiths
        GROUP BY source
        ORDER BY count DESC
    """).fetchall()
    
    for source, count in sources:
        print(f"  {source:30s}: {count:>8,}")
    
    # Par collection
    print("\nPar collection:")
    collections = conn.execute("""
        SELECT collection, COUNT(*) as count
        FROM hadiths
        WHERE collection IS NOT NULL AND collection != ''
        GROUP BY collection
        ORDER BY count DESC
        LIMIT 15
    """).fetchall()
    
    for coll, count in collections:
        print(f"  {coll:30s}: {count:>8,}")
    
    # Derniers imports
    print("\nDerniers imports:")
    recent = conn.execute("""
        SELECT source, COUNT(*) as count
        FROM hadiths
        WHERE id > (SELECT MAX(id) - 1000 FROM hadiths)
        GROUP BY source
    """).fetchall()
    
    if recent:
        for source, count in recent:
            print(f"  {source}: {count} hadiths (derniers 1000)")
    else:
        print("  Aucun import récent détecté")
    
    # Vérifier les logs actifs
    print("\nLogs actifs:")
    log_files = [
        'backend/harvest_v7.log',
        'backend/harvest_hadeethenc.log',
        'backend/mega_harvest_with_salaf.log',
        'backend/ultimate_harvest_v11.log'
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file) / 1024
            print(f"  {os.path.basename(log_file):40s}: {size:>8.1f} KB")
    
    print(f"\n{'='*60}")
    print(f"Objectif 200K: {(total/200000)*100:.1f}% atteint")
    print(f"Reste à importer: {200000-total:,} hadiths")
    print(f"{'='*60}\n")
    
    conn.close()

if __name__ == '__main__':
    check_progress()