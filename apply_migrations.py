#!/usr/bin/env python3
"""
🔧 APPLICATION DES MIGRATIONS AL-MIZAN V7 → V8
Applique les migrations critiques pour le Sanad Numérique et les Autorités
"""

import sqlite3
from pathlib import Path

DB_PATH = "backend/database/almizan_v7.db"
MIGRATIONS_DIR = Path("backend/database/migrations")

def apply_migration(conn, migration_file):
    """Applique une migration SQL"""
    print(f"\n📄 Application de {migration_file.name}...")
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    try:
        # Exécuter le SQL
        cursor = conn.cursor()
        cursor.executescript(sql)
        conn.commit()
        print(f"   ✅ Migration {migration_file.name} appliquée avec succès")
        return True
    except sqlite3.Error as e:
        print(f"   ⚠️  Erreur lors de l'application: {e}")
        # Certaines erreurs sont acceptables (colonnes déjà existantes, etc.)
        if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
            print(f"   ℹ️  Élément déjà existant, on continue...")
            return True
        return False

def main():
    print("=" * 80)
    print("🔧 APPLICATION DES MIGRATIONS AL-MIZAN V7 → V8")
    print("=" * 80)
    
    # Connexion à la base
    print(f"\n📂 Connexion à {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    
    # Lister les migrations
    migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))
    print(f"\n📋 {len(migrations)} migrations trouvées:")
    for mig in migrations:
        print(f"   • {mig.name}")
    
    # Appliquer chaque migration
    print("\n" + "=" * 80)
    print("🚀 DÉBUT DE L'APPLICATION")
    print("=" * 80)
    
    success_count = 0
    for migration in migrations:
        if apply_migration(conn, migration):
            success_count += 1
    
    # Vérification post-migration
    print("\n" + "=" * 80)
    print("🔍 VÉRIFICATION POST-MIGRATION")
    print("=" * 80)
    
    cursor = conn.cursor()
    
    # Vérifier les nouvelles tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("\n📊 Tables disponibles:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   • {table}: {count} entrées")
    
    # Vérifier les colonnes de entries
    cursor.execute("PRAGMA table_info(entries)")
    columns = [row[1] for row in cursor.fetchall()]
    
    print("\n📋 Colonnes de la table 'entries':")
    critical_columns = ['content_hash', 'source_fetch_sha', 'merkle_parent', 'lexique_version', 'needs_human_review']
    for col in critical_columns:
        status = "✅" if col in columns else "❌"
        print(f"   {status} {col}")
    
    # Vérifier la table authorities
    if 'authorities' in tables:
        print("\n👥 Table 'authorities':")
        cursor.execute("PRAGMA table_info(authorities)")
        auth_cols = [row[1] for row in cursor.fetchall()]
        print(f"   ✅ {len(auth_cols)} colonnes créées")
        
        cursor.execute("SELECT COUNT(*) FROM authorities")
        auth_count = cursor.fetchone()[0]
        print(f"   📊 {auth_count} autorités (prêt pour l'import)")
    
    # Vérifier la table hadith_gradings
    if 'hadith_gradings' in tables:
        print("\n⚖️  Table 'hadith_gradings':")
        cursor.execute("SELECT COUNT(*) FROM hadith_gradings")
        grading_count = cursor.fetchone()[0]
        print(f"   📊 {grading_count} jugements (prêt pour l'import)")
    
    conn.close()
    
    # Résumé final
    print("\n" + "=" * 80)
    print("📋 RÉSUMÉ")
    print("=" * 80)
    print(f"\n✅ {success_count}/{len(migrations)} migrations appliquées avec succès")
    
    if success_count == len(migrations):
        print("\n🎉 MIGRATION COMPLÈTE !")
        print("   La base de données est maintenant prête pour:")
        print("   • Le Sanad Numérique (SHA256)")
        print("   • La Timeline des Autorités")
        print("   • Le système de révision humaine")
    else:
        print("\n⚠️  Certaines migrations ont échoué")
        print("   Vérifiez les erreurs ci-dessus")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()