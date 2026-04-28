#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('backend/almizane.db')

# Bukhari existants
cursor = conn.execute('SELECT COUNT(*) FROM hadiths WHERE source_api = "hadith_gading" AND collection = "bukhari"')
bukhari_count = cursor.fetchone()[0]

# Muslim existants
cursor = conn.execute('SELECT COUNT(*) FROM hadiths WHERE source_api = "hadith_gading" AND collection = "muslim"')
muslim_count = cursor.fetchone()[0]

# Tous les livres Hadith Gading
cursor = conn.execute('''
    SELECT collection, COUNT(*) 
    FROM hadiths 
    WHERE source_api = "hadith_gading"
    GROUP BY collection
    ORDER BY COUNT(*) DESC
''')
all_books = cursor.fetchall()

conn.close()

print("=" * 60)
print("📚 LIVRES HADITH GADING DANS LA BASE")
print("=" * 60)
print(f"Bukhari: {bukhari_count}")
print(f"Muslim: {muslim_count}")
print()
print("Tous les livres:")
for book, count in all_books:
    print(f"  - {book}: {count:,}")
print("=" * 60)