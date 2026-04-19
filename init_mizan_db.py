#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'initialisation de la base de données Mîzân avec toutes les migrations v2
"""
import sqlite3
import sys
from pathlib import Path

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = Path("backend/mizan.db")
MIGRATIONS = [
    "backend/init_complete_schema.sql",  # Schéma complet (base + vérificateur + zones 33-40)
    "backend/migrations/003_seed_muhaddithin_complete.sql"  # Seed des ~80 muḥaddithīn
]

def run_migration(conn, migration_file):
    """Execute une migration SQL"""
    if not Path(migration_file).exists():
        print(f"[!] Migration introuvable : {migration_file}")
        return False
    
    print(f"[*] Application de {migration_file}...")
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    try:
        conn.executescript(sql)
        conn.commit()
        print(f"[OK] {migration_file} appliquee avec succes")
        return True
    except sqlite3.Error as e:
        print(f"[X] Erreur lors de l'application de {migration_file}: {e}")
        return False

def init_database():
    """Initialise la base de données complète"""
    print("=" * 60)
    print("INITIALISATION BASE DE DONNEES MIZAN v2")
    print("=" * 60)
    print()
    
    # Supprimer l'ancienne base si elle existe
    if DB_PATH.exists():
        print(f"[*] Suppression de l'ancienne base : {DB_PATH}")
        DB_PATH.unlink()
    
    # Créer la nouvelle base
    print(f"[*] Creation de la nouvelle base : {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    
    # Appliquer toutes les migrations
    success_count = 0
    for migration in MIGRATIONS:
        if run_migration(conn, migration):
            success_count += 1
        else:
            print(f"[X] Echec de la migration {migration}")
            conn.close()
            return False
    
    conn.close()
    
    print()
    print("=" * 60)
    print(f"[OK] Base de donnees initialisee avec succes !")
    print(f"[OK] {success_count}/{len(MIGRATIONS)} migrations appliquees")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)