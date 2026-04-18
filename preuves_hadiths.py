#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect("backend/almizane.db")
cursor = conn.cursor()

print("\n" + "="*80)
print("📚 PREUVE : EXEMPLES DE HADITHS PAR RECUEIL")
print("="*80)

# Pour chaque collection, afficher 2 exemples
cursor.execute("""
    SELECT DISTINCT collection
    FROM hadiths
    ORDER BY collection
""")

collections = [row[0] for row in cursor.fetchall()]

for collection in collections:
    cursor.execute("""
        SELECT id, numero_hadith, matn_ar, matn_fr
        FROM hadiths
        WHERE collection = ?
        LIMIT 2
    """, (collection,))
    
    hadiths = cursor.fetchall()
    
    if hadiths:
        print(f"\n{'='*80}")
        print(f"📖 {collection.upper()}")
        print(f"{'='*80}")
        
        for hadith_id, num, arabe, francais in hadiths:
            print(f"\n🔹 Hadith #{num} (ID: {hadith_id})")
            print(f"   Arabe : {arabe[:100]}..." if len(arabe) > 100 else f"   Arabe : {arabe}")
            print(f"   Français : {francais[:150]}..." if len(francais) > 150 else f"   Français : {francais}")

print(f"\n{'='*80}")
print("✅ Preuve établie : Les hadiths sont bien présents dans la base de données")
print("="*80)

conn.close()