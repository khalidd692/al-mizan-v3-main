#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de vérification de la base de données Mîzân v2
Vérifie que toutes les tables et données sont présentes
"""
import sqlite3
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = Path("backend/mizan.db")

def verify_database():
    """Vérifie l'intégrité de la base de données"""
    print("=" * 70)
    print("VERIFICATION BASE DE DONNEES MIZAN v2")
    print("=" * 70)
    print()
    
    if not DB_PATH.exists():
        print(f"[X] Base de donnees introuvable : {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Vérifier les tables principales
    print("[*] Verification des tables...")
    expected_tables = [
        # Tables de base
        'hadiths', 'avis_savants',
        # Tables vérificateur (zones 1-32)
        'hukm_sources', 'ahkam', 'rijal', 'rijal_verdicts',
        'sanad_chains', 'sanad_links', 'takhrij', 'ilal',
        'matn_analysis', 'fiqh_hadith',
        # Tables zones 33-40
        'ziyadat_thiqah', 'taʿarud_wasl_irsal', 'taʿarud_waqf_rafʿ',
        'mubham_muhmal', 'mazid_muttasil', 'tafarrud',
        'ʿamal_salaf', 'mukhtalif_hadith'
    ]
    
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {row[0] for row in cur.fetchall()}
    
    missing_tables = []
    for table in expected_tables:
        if table in existing_tables:
            print(f"  [OK] Table '{table}' presente")
        else:
            print(f"  [X] Table '{table}' MANQUANTE")
            missing_tables.append(table)
    
    if missing_tables:
        print(f"\n[X] {len(missing_tables)} tables manquantes !")
        conn.close()
        return False
    
    print(f"\n[OK] Toutes les {len(expected_tables)} tables sont presentes")
    
    # Vérifier le seed des muḥaddithīn
    print("\n[*] Verification du seed des muhaddithin...")
    cur.execute("SELECT COUNT(*) FROM hukm_sources")
    count = cur.fetchone()[0]
    
    if count == 0:
        print("[X] Aucun muhaddith dans hukm_sources !")
        conn.close()
        return False
    
    print(f"[OK] {count} muhaddithin charges dans hukm_sources")
    
    # Afficher quelques exemples
    print("\n[*] Exemples de muhaddithin (premiers 10):")
    cur.execute("""
        SELECT name_ar, name_fr, tabaqah, death_hijri, reliability_weight
        FROM hukm_sources
        ORDER BY death_hijri
        LIMIT 10
    """)
    
    for row in cur.fetchall():
        name_ar, name_fr, tabaqah, death_h, weight = row
        print(f"  - {name_ar} ({name_fr}) | {tabaqah} | †{death_h}H | poids={weight}")
    
    # Vérifier les index
    print("\n[*] Verification des index...")
    cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = cur.fetchall()
    print(f"[OK] {len(indexes)} index crees")
    
    # Statistiques par ṭabaqah
    print("\n[*] Repartition par tabaqah:")
    cur.execute("""
        SELECT tabaqah, COUNT(*) as count
        FROM hukm_sources
        WHERE tabaqah IS NOT NULL
        GROUP BY tabaqah
        ORDER BY 
            CASE tabaqah
                WHEN 'mutaqaddim' THEN 1
                WHEN 'mutawassit' THEN 2
                WHEN 'mutaakhkhir' THEN 3
                WHEN 'muʿasir' THEN 4
                ELSE 5
            END
    """)
    
    for tabaqah, count in cur.fetchall():
        print(f"  - {tabaqah}: {count} imams")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("[OK] VERIFICATION COMPLETE - Base de donnees prete !")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    success = verify_database()
    sys.exit(0 if success else 1)