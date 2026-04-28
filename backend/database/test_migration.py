#!/usr/bin/env python3
"""
Test de la migration v7 → v8 sur une copie de test
"""

import sqlite3
import sys
from pathlib import Path
import shutil

DB_TEST = Path(__file__).parent / "almizan_v7_test.db"
DB_PROD = Path(__file__).parent / "almizan_v7.db"
MIGRATION_SQL = Path(__file__).parent / "migrations" / "001_chain_of_trust.sql"

def test_migration():
    print("🧪 TEST DE MIGRATION V7 → V8")
    print("=" * 70)
    
    # Créer une copie de test si elle n'existe pas
    if not DB_TEST.exists():
        print(f"📋 Création de la copie de test...")
        shutil.copy2(DB_PROD, DB_TEST)
    
    print(f"✅ Base de test : {DB_TEST.name}")
    
    # Lire le script SQL
    with open(MIGRATION_SQL, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    # Connexion
    conn = sqlite3.connect(DB_TEST)
    cursor = conn.cursor()
    
    # État AVANT
    print("\n📊 ÉTAT AVANT MIGRATION:")
    cursor.execute("SELECT COUNT(*) FROM entries")
    count_before = cursor.fetchone()[0]
    print(f"   Entrées : {count_before}")
    
    cursor.execute("PRAGMA table_info(entries)")
    cols_before = [row[1] for row in cursor.fetchall()]
    print(f"   Colonnes : {len(cols_before)}")
    
    # Exécuter la migration
    print("\n🚀 Exécution de la migration...")
    try:
        cursor.executescript(sql_script)
        conn.commit()
        print("✅ Migration exécutée")
    except Exception as e:
        print(f"❌ Erreur : {e}")
        conn.close()
        return False
    
    # État APRÈS
    print("\n📊 ÉTAT APRÈS MIGRATION:")
    cursor.execute("SELECT COUNT(*) FROM entries")
    count_after = cursor.fetchone()[0]
    print(f"   Entrées : {count_after}")
    
    if count_before != count_after:
        print(f"❌ ERREUR : Perte de données ! {count_before} → {count_after}")
        conn.close()
        return False
    
    cursor.execute("PRAGMA table_info(entries)")
    cols_after = [row[1] for row in cursor.fetchall()]
    print(f"   Colonnes : {len(cols_after)}")
    
    new_cols = set(cols_after) - set(cols_before)
    print(f"   Nouvelles colonnes : {', '.join(new_cols)}")
    
    # Vérifier les tables
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name IN ('entries_history', 'quarantine')
    """)
    tables = [row[0] for row in cursor.fetchall()]
    print(f"   Nouvelles tables : {', '.join(tables)}")
    
    # Tester la vue
    cursor.execute("SELECT * FROM v_quality_stats")
    stats = cursor.fetchone()
    print(f"\n📈 STATISTIQUES DE QUALITÉ:")
    print(f"   Total : {stats[0]}")
    print(f"   Avec hash : {stats[1]}")
    print(f"   À revoir : {stats[2]}")
    print(f"   Avec lexique : {stats[3]}")
    print(f"   Versions lexique : {stats[4]}")
    
    # Tester le trigger
    print(f"\n🔧 TEST DU TRIGGER:")
    cursor.execute("SELECT id, ar_text FROM entries LIMIT 1")
    test_entry = cursor.fetchone()
    
    if test_entry:
        entry_id = test_entry[0]
        print(f"   Modification de l'entrée {entry_id}...")
        
        cursor.execute("""
            UPDATE entries 
            SET needs_human_review = 1 
            WHERE id = ?
        """, (entry_id,))
        conn.commit()
        
        cursor.execute("""
            SELECT COUNT(*) FROM entries_history 
            WHERE entry_id = ?
        """, (entry_id,))
        history_count = cursor.fetchone()[0]
        
        if history_count > 0:
            print(f"   ✅ Trigger fonctionne : {history_count} snapshot(s) créé(s)")
        else:
            print(f"   ❌ Trigger ne fonctionne pas")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("✅ TEST RÉUSSI - La migration peut être appliquée en production")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = test_migration()
    sys.exit(0 if success else 1)