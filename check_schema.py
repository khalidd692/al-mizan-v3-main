#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('backend/almizane.db')
cursor = conn.execute('PRAGMA table_info(hadiths)')

print("Colonnes de la table hadiths:")
for row in cursor.fetchall():
    print(f"  - {row[1]} ({row[2]})")

conn.close()