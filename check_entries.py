#!/usr/bin/env python3
"""Vérifier la table entries (hadiths)"""

import sqlite3

conn = sqlite3.connect('backend/database/almizan_v7.db')
cursor = conn.cursor()

# Compter les entrées
cursor.execute("SELECT COUNT(*) FROM entries")
total = cursor.fetchone()[0]
print(f"📚 TOTAL ENTRIES (HADITHS): {total}")
print()

# Répartition par grade primaire
print("📊 RÉPARTITION PAR GRADE PRIMAIRE:")
cursor.execute("SELECT grade_primary, COUNT(*) FROM entries GROUP BY grade_primary ORDER BY COUNT(*) DESC")
grades = cursor.fetchall()
for grade, count in grades:
    percentage = (count / total * 100) if total > 0 else 0
    grade_display = grade if grade else "Non défini"
    print(f"  • {grade_display:20s}: {count:5d} ({percentage:5.1f}%)")
print()

# Répartition par grade Albani
print("📊 RÉPARTITION PAR GRADE ALBANI:")
cursor.execute("SELECT grade_albani, COUNT(*) FROM entries WHERE grade_albani IS NOT NULL GROUP BY grade_albani ORDER BY COUNT(*) DESC")
albani_grades = cursor.fetchall()
for grade, count in albani_grades:
    percentage = (count / total * 100) if total > 0 else 0
    print(f"  • {grade:20s}: {count:5d} ({percentage:5.1f}%)")
print()

# Répartition par source (livre)
print("📖 RÉPARTITION PAR LIVRE:")
cursor.execute("SELECT book_name_fr, COUNT(*) FROM entries GROUP BY book_name_fr ORDER BY COUNT(*) DESC LIMIT 10")
sources = cursor.fetchall()
for source, count in sources:
    source_display = source if source else "Non défini"
    print(f"  • {source_display:40s}: {count:5d}")
print()

# Dernières entrées
print("🆕 DERNIÈRES 5 ENTRÉES:")
cursor.execute("SELECT id, grade_primary, book_name_fr, hadith_number FROM entries ORDER BY created_at DESC LIMIT 5")
recent = cursor.fetchall()
for entry_id, grade, book, number in recent:
    grade_display = grade if grade else "N/A"
    book_display = book if book else "N/A"
    number_display = number if number else "N/A"
    print(f"  • ID {entry_id[:8]}... | {grade_display:15s} | {book_display:30s} | #{number_display}")

conn.close()