#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect("backend/almizane.db")
cursor = conn.cursor()

print("\n📊 HADITHS PAR RECUEIL\n")
print("-" * 50)

cursor.execute("""
    SELECT collection, COUNT(*) as nombre
    FROM hadiths
    GROUP BY collection
    ORDER BY nombre DESC
""")

total = 0
for collection, nombre in cursor.fetchall():
    print(f"{collection:<25} : {nombre:>6,} hadiths")
    total += nombre

print("-" * 50)
print(f"{'TOTAL':<25} : {total:>6,} hadiths")

conn.close()