#!/usr/bin/env python3
"""Script pour vérifier l'état de la base de données al-mizan v7"""

import sqlite3
import os

db_path = 'backend/database/almizan_v7.db'

if not os.path.exists(db_path):
    print(f"❌ Base de données non trouvée: {db_path}")
    exit(1)

print(f"✅ Base de données trouvée: {db_path}")
print()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Lister les tables
print("📋 TABLES DISPONIBLES:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"  - {table[0]}")
print()

# Vérifier si la table hadiths existe
if ('hadiths',) in tables or ('hadith',) in tables:
    table_name = 'hadiths' if ('hadiths',) in tables else 'hadith'
    
    # Compter les hadiths
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    total = cursor.fetchone()[0]
    print(f"📚 TOTAL HADITHS: {total}")
    print()
    
    # Répartition par grade
    print("📊 RÉPARTITION PAR GRADE:")
    cursor.execute(f"SELECT grade, COUNT(*) FROM {table_name} GROUP BY grade ORDER BY COUNT(*) DESC")
    grades = cursor.fetchall()
    for grade, count in grades:
        percentage = (count / total * 100) if total > 0 else 0
        print(f"  • {grade:15s}: {count:5d} ({percentage:5.1f}%)")
    print()
    
    # Répartition par livre
    print("📖 RÉPARTITION PAR LIVRE:")
    cursor.execute(f"SELECT book, COUNT(*) FROM {table_name} GROUP BY book ORDER BY COUNT(*) DESC")
    books = cursor.fetchall()
    for book, count in books:
        print(f"  • {book:30s}: {count:5d}")
    print()
    
    # Derniers hadiths insérés
    print("🆕 DERNIERS 5 HADITHS INSÉRÉS:")
    cursor.execute(f"SELECT id, grade, book FROM {table_name} ORDER BY id DESC LIMIT 5")
    recent = cursor.fetchall()
    for hadith_id, grade, book in recent:
        print(f"  • ID {hadith_id:5d} | {grade:10s} | {book}")
else:
    print("⚠️  Aucune table 'hadiths' ou 'hadith' trouvée")
    print("Tables disponibles:", [t[0] for t in tables])

conn.close()