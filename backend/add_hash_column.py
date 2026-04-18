#!/usr/bin/env python3
"""
Script pour ajouter la colonne matn_ar_hash à la DB
"""

import sqlite3

def add_hash_column():
    """Ajoute les colonnes manquantes si elles n'existent pas"""
    conn = sqlite3.connect('backend/database/almizan_v7.db')
    cursor = conn.cursor()
    
    try:
        # Vérifie les colonnes existantes
        cursor.execute("PRAGMA table_info(entries)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Ajoute matn_ar_hash
        if 'matn_ar_hash' not in columns:
            print("[INFO] Ajout de la colonne matn_ar_hash...")
            cursor.execute("ALTER TABLE entries ADD COLUMN matn_ar_hash TEXT")
            conn.commit()
            print("[OK] Colonne matn_ar_hash ajoutée avec succès")
        else:
            print("[INFO] La colonne matn_ar_hash existe déjà")
        
        # Ajoute external_id
        if 'external_id' not in columns:
            print("[INFO] Ajout de la colonne external_id...")
            cursor.execute("ALTER TABLE entries ADD COLUMN external_id TEXT")
            conn.commit()
            print("[OK] Colonne external_id ajoutée avec succès")
        else:
            print("[INFO] La colonne external_id existe déjà")
        
        # Crée les index pour améliorer les performances
        print("[INFO] Création des index...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_matn_ar_hash 
            ON entries(matn_ar_hash)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_external_id 
            ON entries(external_id)
        """)
        conn.commit()
        print("[OK] Index créés avec succès")
        
    except Exception as e:
        print(f"[ERREUR] {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_hash_column()