#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour vérifier les statistiques de la base de données mizan.db
"""
import sqlite3
import sys
from pathlib import Path

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = Path("backend/mizan.db")

def check_stats():
    if not DB_PATH.exists():
        print(f"❌ Base de données introuvable : {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    tables = [
        'hadiths',
        'ahkam',
        'hukm_sources',
        'rijal',
        'rijal_verdicts',
        'sanad_chains',
        'sanad_links',
        'takhrij',
        'ilal',
        'ziyadat_thiqah',
        'taʿarud_wasl_irsal',
        'taʿarud_waqf_rafʿ',
        'mubham_muhmal',
        'mazid_muttasil',
        'tafarrud',
        'ʿamal_salaf',
        'mukhtalif_hadith',
        'matn_analysis',
        'fiqh_hadith'
    ]
    
    print("=" * 60)
    print("STATISTIQUES BASE DE DONNEES MIZAN")
    print("=" * 60)
    print()
    
    for table in tables:
        try:
            cur.execute(f'SELECT COUNT(*) FROM "{table}"')
            count = cur.fetchone()[0]
            status = "[OK]" if count > 0 else "[ ]"
            print(f"{status} {table:30} : {count:>10,} entrées")
        except sqlite3.OperationalError as e:
            print(f"[X] {table:30} : Table inexistante")
    
    print()
    print("-" * 60)
    
    # Hadiths avec grade_synthese
    try:
        cur.execute('SELECT COUNT(*) FROM hadiths WHERE grade_synthese IS NOT NULL')
        graded = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM hadiths')
        total = cur.fetchone()[0]
        pct = (graded / total * 100) if total > 0 else 0
        print(f"[OK] Hadiths avec grade_synthese : {graded:>10,} / {total:,} ({pct:.1f}%)")
    except:
        print("[X] Impossible de verifier les grades")
    
    print()
    print("=" * 60)
    
    conn.close()

if __name__ == "__main__":
    check_stats()