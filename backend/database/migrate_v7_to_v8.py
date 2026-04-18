#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
AL-MĪZĀN V8.0 — MIGRATION SCRIPT
Migration de v7 à v8 : Chain of Trust + Historique + Quarantaine
═══════════════════════════════════════════════════════════════
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime
import json

# Chemins
DB_PATH = Path(__file__).parent / "almizan_v7.db"
MIGRATION_SQL = Path(__file__).parent / "migrations" / "001_chain_of_trust.sql"
BACKUP_PATH = Path(__file__).parent / f"almizan_v7.db.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def print_banner():
    print("═" * 70)
    print("🕋 AL-MĪZĀN V8.0 — MIGRATION VERS CHAIN OF TRUST")
    print("═" * 70)
    print()

def create_backup():
    """Crée un backup de la base avant migration"""
    print(f"📦 Création du backup : {BACKUP_PATH.name}")
    try:
        import shutil
        shutil.copy2(DB_PATH, BACKUP_PATH)
        print(f"✅ Backup créé avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur lors du backup : {e}")
        return False

def check_db_integrity():
    """Vérifie l'intégrité de la base avant migration"""
    print("\n🔍 Vérification de l'intégrité de la base...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Vérifier l'intégrité
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        
        if result != "ok":
            print(f"❌ Problème d'intégrité détecté : {result}")
            conn.close()
            return False
        
        # Compter les entrées
        cursor.execute("SELECT COUNT(*) FROM entries")
        count = cursor.fetchone()[0]
        print(f"✅ Base intègre : {count} entrées trouvées")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la vérification : {e}")
        return False

def run_migration():
    """Exécute la migration SQL"""
    print("\n🚀 Exécution de la migration...")
    
    if not MIGRATION_SQL.exists():
        print(f"❌ Fichier de migration introuvable : {MIGRATION_SQL}")
        return False
    
    try:
        # Lire le script SQL
        with open(MIGRATION_SQL, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Connexion et exécution
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Activer les foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Exécuter le script
        cursor.executescript(sql_script)
        conn.commit()
        
        print("✅ Migration SQL exécutée avec succès")
        
        # Vérifier les nouvelles colonnes
        cursor.execute("PRAGMA table_info(entries)")
        columns = [row[1] for row in cursor.fetchall()]
        
        expected_cols = ['content_hash', 'source_fetch_sha', 'merkle_parent', 
                        'lexique_version', 'needs_human_review']
        
        missing = [col for col in expected_cols if col not in columns]
        if missing:
            print(f"⚠️  Colonnes manquantes : {missing}")
            conn.close()
            return False
        
        print(f"✅ Toutes les colonnes ajoutées : {', '.join(expected_cols)}")
        
        # Vérifier les nouvelles tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('entries_history', 'quarantine')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        if len(tables) != 2:
            print(f"⚠️  Tables manquantes. Trouvées : {tables}")
            conn.close()
            return False
        
        print(f"✅ Tables créées : {', '.join(tables)}")
        
        # Vérifier les vues
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='view' AND name IN ('v_quality_stats', 'v_needs_review')
        """)
        views = [row[0] for row in cursor.fetchall()]
        
        if len(views) != 2:
            print(f"⚠️  Vues manquantes. Trouvées : {views}")
        else:
            print(f"✅ Vues créées : {', '.join(views)}")
        
        # Vérifier le trigger
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='trigger' AND name='trg_entries_audit_before_update'
        """)
        trigger = cursor.fetchone()
        
        if not trigger:
            print("⚠️  Trigger d'audit non trouvé")
        else:
            print(f"✅ Trigger créé : {trigger[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration : {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_migration():
    """Vérifie que la migration s'est bien passée"""
    print("\n🔍 Vérification post-migration...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Vérifier que les données existantes sont intactes
        cursor.execute("SELECT COUNT(*) FROM entries")
        count = cursor.fetchone()[0]
        print(f"✅ {count} entrées préservées")
        
        # Tester la vue de stats
        cursor.execute("SELECT * FROM v_quality_stats")
        stats = cursor.fetchone()
        print(f"✅ Statistiques : {stats[0]} total, {stats[1]} avec hash, {stats[2]} à revoir")
        
        # Vérifier que les nouvelles colonnes sont NULL pour les anciennes entrées
        cursor.execute("""
            SELECT COUNT(*) FROM entries 
            WHERE content_hash IS NULL
        """)
        null_count = cursor.fetchone()[0]
        print(f"✅ {null_count} entrées avec content_hash NULL (normal pour migration)")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification : {e}")
        return False

def main():
    print_banner()
    
    # Vérifier que la base existe
    if not DB_PATH.exists():
        print(f"❌ Base de données introuvable : {DB_PATH}")
        sys.exit(1)
    
    # Étape 1 : Backup
    if not create_backup():
        print("\n❌ Migration annulée : impossible de créer le backup")
        sys.exit(1)
    
    # Étape 2 : Vérification intégrité
    if not check_db_integrity():
        print("\n❌ Migration annulée : problème d'intégrité détecté")
        sys.exit(1)
    
    # Étape 3 : Migration
    if not run_migration():
        print("\n❌ Migration échouée")
        print(f"💾 Restaurez le backup : {BACKUP_PATH}")
        sys.exit(1)
    
    # Étape 4 : Vérification
    if not verify_migration():
        print("\n⚠️  Migration terminée mais vérification échouée")
        print(f"💾 Backup disponible : {BACKUP_PATH}")
        sys.exit(1)
    
    # Succès
    print("\n" + "═" * 70)
    print("✅ MIGRATION V7 → V8 RÉUSSIE")
    print("═" * 70)
    print(f"\n💾 Backup conservé : {BACKUP_PATH}")
    print("\n📊 Prochaines étapes :")
    print("   1. Tester avec : python -m backend.database.test_migration")
    print("   2. Calculer les content_hash pour les entrées existantes")
    print("   3. Activer le nouveau pipeline avec Lexique de Fer")
    print()

if __name__ == "__main__":
    main()