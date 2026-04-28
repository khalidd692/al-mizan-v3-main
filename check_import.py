#!/usr/bin/env python3
"""Vérifier l'état de l'import"""

import sqlite3

conn = sqlite3.connect('backend/almizane.db')

# Total hadiths
cursor = conn.execute('SELECT COUNT(*) FROM hadiths')
total = cursor.fetchone()[0]

# Hadiths Gading
cursor = conn.execute('SELECT COUNT(*) FROM hadiths WHERE source_api = "hadith_gading"')
gading = cursor.fetchone()[0]

# Par livre
cursor = conn.execute('''
    SELECT collection, COUNT(*) 
    FROM hadiths 
    WHERE source_api = "hadith_gading"
    GROUP BY collection
''')
books = cursor.fetchall()

conn.close()

print("=" * 60)
print("📊 ÉTAT DE L'IMPORT")
print("=" * 60)
print(f"Total hadiths dans la DB: {total:,}")
print(f"Hadiths Hadith Gading: {gading:,}")
print()
print("Par livre:")
for book, count in books:
    print(f"  - {book}: {count:,} hadiths")
print("=" * 60)