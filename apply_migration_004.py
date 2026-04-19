#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Applique la migration 004 - Taxonomie complète des ḥukm"""
import sqlite3
import sys
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

DB = Path("backend/mizan.db")
MIGRATION = Path("backend/migrations/004_complete_hukm_enum.sql")

def main():
    print("[*] Application de la migration 004...")
    
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # Lire et exécuter la migration
    sql = MIGRATION.read_text(encoding='utf-8')
    conn.executescript(sql)
    conn.commit()
    
    print("[OK] Migration 004 appliquee avec succes")
    
    # Vérification
    total = cur.execute("SELECT COUNT(*) FROM hukm_classes").fetchone()[0]
    print(f"\n[INFO] Total classes de hukm: {total}")
    
    print("\n[INFO] Distribution par categorie:")
    for row in cur.execute("""
        SELECT category, COUNT(*) as count 
        FROM hukm_classes 
        GROUP BY category 
        ORDER BY category
    """):
        print(f"  - {row[0]:<15} {row[1]:>3} classes")
    
    print("\n[INFO] Exemples de classes:")
    for row in cur.execute("""
        SELECT code, name_ar, name_fr, severity 
        FROM hukm_classes 
        ORDER BY severity DESC 
        LIMIT 10
    """):
        print(f"  - {row[0]:<25} {row[1]:<20} (severite: {row[3]})")
    
    conn.close()
    print("\n[OK] Migration 004 terminee")

if __name__ == "__main__":
    main()