#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Initialisation de la base de données AL-MĪZĀN v5.0
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "almizane.db"
SCHEMA_PATH = Path(__file__).parent / "init_schema_v5.sql"

def init_database():
    """Initialise la base de données avec le schéma v5.0"""
    print("🕌 Initialisation de la base de données AL-MĪZĀN v5.0")
    print(f"   Chemin: {DB_PATH}")
    
    # Lire le schéma SQL
    if not SCHEMA_PATH.exists():
        print(f"❌ Fichier schéma introuvable: {SCHEMA_PATH}")
        return False
    
    schema_sql = SCHEMA_PATH.read_text(encoding='utf-8')
    
    # Créer/ouvrir la base de données
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    
    try:
        # Exécuter le schéma
        conn.executescript(schema_sql)
        conn.commit()
        
        # Vérifier les tables créées
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\n✅ Base de données initialisée avec succès")
        print(f"   Tables créées: {', '.join(tables)}")
        
        # Vérifier le Lexique de Fer
        cursor.execute("SELECT COUNT(*) FROM lexique_fer")
        count = cursor.fetchone()[0]
        print(f"   Lexique de Fer: {count} entrées")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = init_database()
    exit(0 if success else 1)