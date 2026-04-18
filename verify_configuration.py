#!/usr/bin/env python3
"""
🔍 VÉRIFICATION CONFIGURATION AL-MIZAN V7
Analyse Lead Dev - Points critiques
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = "backend/database/almizan_v7.db"

def check_database_structure():
    """Vérifie la structure de la base de données"""
    print("=" * 80)
    print("🔍 VÉRIFICATION CONFIGURATION AL-MIZAN V7")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. VÉRIFICATION DU SANAD NUMÉRIQUE (SHA256)
    print("\n📜 1. SANAD NUMÉRIQUE (SHA256)")
    print("-" * 80)
    
    cursor.execute("PRAGMA table_info(entries)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    
    if 'content_hash' in columns:
        print("✅ Colonne 'content_hash' existe")
        cursor.execute("SELECT COUNT(*) FROM entries WHERE content_hash IS NOT NULL")
        count_with_hash = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM entries")
        total = cursor.fetchone()[0]
        print(f"   📊 {count_with_hash}/{total} entries avec empreinte SHA256")
        
        if count_with_hash > 0:
            cursor.execute("SELECT id, content_hash, arabic_text FROM entries WHERE content_hash IS NOT NULL LIMIT 3")
            print("\n   🔍 Exemples d'empreintes:")
            for row in cursor.fetchall():
                print(f"      Entry #{row[0]}: {row[1][:16]}...")
    else:
        print("❌ Colonne 'content_hash' MANQUANTE")
        print("   ⚠️  CRITIQUE: Le Sanad Numérique n'est pas implémenté!")
    
    # 2. TABLE DES AUTORITÉS
    print("\n\n👥 2. TABLE DES AUTORITÉS")
    print("-" * 80)
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    if 'authorities' in tables:
        print("✅ Table 'authorities' existe")
        cursor.execute("SELECT COUNT(*) FROM authorities")
        auth_count = cursor.fetchone()[0]
        print(f"   📊 {auth_count} autorités enregistrées")
        
        cursor.execute("PRAGMA table_info(authorities)")
        auth_columns = [row[1] for row in cursor.fetchall()]
        print(f"   📋 Colonnes: {', '.join(auth_columns)}")
        
        if auth_count > 0:
            cursor.execute("SELECT name_transliterated, century, school FROM authorities LIMIT 5")
            print("\n   🔍 Exemples d'autorités:")
            for row in cursor.fetchall():
                print(f"      • {row[0]} ({row[1]}ème s.H) - École: {row[2]}")
    else:
        print("❌ Table 'authorities' MANQUANTE")
        print("   ⚠️  CRITIQUE: Impossible de tracer les jugements!")
    
    # Vérifier les grades/jugements
    if 'entry_grades' in tables or 'hadith_grades' in tables:
        grade_table = 'entry_grades' if 'entry_grades' in tables else 'hadith_grades'
        print(f"\n✅ Table de grades '{grade_table}' existe")
        cursor.execute(f"SELECT COUNT(*) FROM {grade_table}")
        grade_count = cursor.fetchone()[0]
        print(f"   📊 {grade_count} jugements enregistrés")
        
        cursor.execute(f"PRAGMA table_info({grade_table})")
        grade_columns = [row[1] for row in cursor.fetchall()]
        print(f"   📋 Colonnes: {', '.join(grade_columns)}")
    else:
        print("❌ Table de grades MANQUANTE")
    
    # 3. GESTION DU "NEEDS HUMAN REVIEW"
    print("\n\n⚖️  3. GESTION DU 'NEEDS HUMAN REVIEW'")
    print("-" * 80)
    
    if 'quarantine' in tables:
        print("✅ Table 'quarantine' existe")
        cursor.execute("SELECT COUNT(*) FROM quarantine")
        quarantine_count = cursor.fetchone()[0]
        print(f"   📊 {quarantine_count} cas en quarantaine")
        
        cursor.execute("PRAGMA table_info(quarantine)")
        quar_columns = [row[1] for row in cursor.fetchall()]
        print(f"   📋 Colonnes: {', '.join(quar_columns)}")
        
        if quarantine_count > 0:
            cursor.execute("SELECT reason, COUNT(*) FROM quarantine GROUP BY reason")
            print("\n   🔍 Raisons de quarantaine:")
            for row in cursor.fetchall():
                print(f"      • {row[0]}: {row[1]} cas")
    else:
        print("❌ Table 'quarantine' MANQUANTE")
        print("   ⚠️  CRITIQUE: Pas de système de révision humaine!")
    
    # 4. VÉRIFICATION DES SOURCES
    print("\n\n📚 4. SOURCES ET TRAÇABILITÉ")
    print("-" * 80)
    
    if 'sources' in tables:
        print("✅ Table 'sources' existe")
        cursor.execute("SELECT COUNT(*) FROM sources")
        source_count = cursor.fetchone()[0]
        print(f"   📊 {source_count} sources enregistrées")
        
        cursor.execute("SELECT name, COUNT(*) as cnt FROM sources GROUP BY name ORDER BY cnt DESC LIMIT 5")
        print("\n   🔍 Top 5 sources:")
        for row in cursor.fetchall():
            print(f"      • {row[0]}: {row[1]} références")
    
    # 5. STATISTIQUES GLOBALES
    print("\n\n📈 5. STATISTIQUES GLOBALES")
    print("-" * 80)
    
    cursor.execute("SELECT COUNT(*) FROM entries")
    total_entries = cursor.fetchone()[0]
    print(f"   📊 Total entries: {total_entries}")
    
    if 'rijal' in tables:
        cursor.execute("SELECT COUNT(*) FROM rijal")
        total_rijal = cursor.fetchone()[0]
        print(f"   👥 Total rijal: {total_rijal}")
    
    # 6. VÉRIFICATION DES MIGRATIONS
    print("\n\n🔄 6. MIGRATIONS APPLIQUÉES")
    print("-" * 80)
    
    migration_files = list(Path("backend/database/migrations").glob("*.sql"))
    print(f"   📁 {len(migration_files)} fichiers de migration trouvés:")
    for mig in sorted(migration_files):
        print(f"      • {mig.name}")
    
    conn.close()
    
    # RÉSUMÉ FINAL
    print("\n" + "=" * 80)
    print("📋 RÉSUMÉ DE LA VÉRIFICATION")
    print("=" * 80)
    
    issues = []
    if 'content_hash' not in columns:
        issues.append("❌ Sanad Numérique (SHA256) non implémenté")
    if 'authorities' not in tables:
        issues.append("❌ Table des autorités manquante")
    if 'quarantine' not in tables:
        issues.append("❌ Système de révision humaine manquant")
    
    if issues:
        print("\n⚠️  PROBLÈMES CRITIQUES DÉTECTÉS:")
        for issue in issues:
            print(f"   {issue}")
        print("\n🔧 ACTION REQUISE: Appliquer les migrations manquantes")
    else:
        print("\n✅ CONFIGURATION VALIDÉE")
        print("   Tous les systèmes critiques sont en place")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_database_structure()