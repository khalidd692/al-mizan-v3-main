#!/usr/bin/env python3
"""Ajoute la colonne content_hash à mizan.db"""
import sqlite3
from pathlib import Path

DB = Path("backend/mizan.db")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Vérifier si la colonne existe déjà
columns = [row[1] for row in cur.execute("PRAGMA table_info(hadiths)").fetchall()]

if 'content_hash' not in columns:
    print("Ajout de la colonne content_hash...")
    cur.execute("ALTER TABLE hadiths ADD COLUMN content_hash TEXT")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_hadiths_content_hash ON hadiths(content_hash)")
    conn.commit()
    print("✅ Colonne content_hash ajoutée")
else:
    print("✅ Colonne content_hash existe déjà")

conn.close()