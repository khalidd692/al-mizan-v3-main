"""
Vérification complète des migrations v2
"""
import sqlite3
import sys
from pathlib import Path

# Force UTF-8 pour Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

DB = Path("backend/almizane.db")

def main():
    print("="*70)
    print("VERIFICATION DES MIGRATIONS V2")
    print("="*70)
    
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # Vérifier les nouvelles tables (zones 33-40)
    expected_tables = [
        'ziyadat_thiqah',
        'taʿarud_wasl_irsal',
        'taʿarud_waqf_rafʿ',
        'mubham_muhmal',
        'mazid_muttasil',
        'tafarrud',
        'ʿamal_salaf',
        'mukhtalif_hadith'
    ]
    
    print("\n[1] Verification des nouvelles tables (zones 33-40):")
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {row[0] for row in cur.fetchall()}
    
    for table in expected_tables:
        if table in existing_tables:
            print(f"  [OK] {table}")
        else:
            print(f"  [MANQUANT] {table}")
    
    # Vérifier les nouvelles colonnes de hukm_sources
    print("\n[2] Verification des colonnes de hukm_sources:")
    cur.execute("PRAGMA table_info(hukm_sources)")
    columns = {row[1] for row in cur.fetchall()}
    
    expected_columns = ['tabaqah', 'death_hijri', 'specialty']
    for col in expected_columns:
        if col in columns:
            print(f"  [OK] {col}")
        else:
            print(f"  [MANQUANT] {col}")
    
    # Vérifier le seed des muḥaddithīn
    print("\n[3] Verification du seed des muhaddithin:")
    cur.execute("SELECT COUNT(*) FROM hukm_sources")
    count = cur.fetchone()[0]
    print(f"  Total muhaddithin: {count}")
    
    if count >= 80:
        print(f"  [OK] Seed complet (attendu: ~80)")
    else:
        print(f"  [ATTENTION] Seed incomplet (attendu: ~80, trouve: {count})")
    
    # Statistiques par ṭabaqah
    print("\n[4] Repartition par tabaqah:")
    cur.execute("""
        SELECT tabaqah, COUNT(*) 
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
    
    # Exemples de muḥaddithīn
    print("\n[5] Exemples de muhaddithin (5 premiers):")
    cur.execute("""
        SELECT name_ar, name_fr, tabaqah, death_hijri, specialty
        FROM hukm_sources
        LIMIT 5
    """)
    
    for row in cur.fetchall():
        name_ar, name_fr, tabaqah, death_h, specialty = row
        print(f"  - {name_fr} ({name_ar})")
        print(f"    Tabaqah: {tabaqah}, Deces: {death_h}H, Specialite: {specialty}")
    
    conn.close()
    
    print("\n" + "="*70)
    print("[SUCCESS] Verification terminee !")
    print("="*70)

if __name__ == "__main__":
    main()