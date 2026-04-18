#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Affichage de hadiths lisibles depuis la base de données
"""
import sqlite3

conn = sqlite3.connect('backend/almizane.db')
cursor = conn.cursor()

print("\n" + "="*80)
print("📖 HADITHS À LIRE AVANT DE DORMIR")
print("="*80)

# Récupérer 10 hadiths variés avec leur texte arabe
cursor.execute("""
    SELECT 
        collection,
        numero_hadith,
        matn_ar,
        grade_final,
        badge_alerte
    FROM hadiths 
    WHERE matn_ar IS NOT NULL 
    AND matn_ar != ''
    ORDER BY RANDOM()
    LIMIT 10
""")

for i, row in enumerate(cursor.fetchall(), 1):
    collection, number, matn_ar, grade, alerte = row
    
    print(f"\n{'─'*80}")
    print(f"📚 Hadith #{i} - {collection} #{number}")
    print(f"{'─'*80}")
    
    # Grade
    if grade:
        print(f"🏅 Grade: {grade}")
    else:
        print(f"🏅 Grade: Non évalué")
    
    # Alerte si inventé
    if alerte == 1:
        print(f"⚠️  ATTENTION: Ce hadith est marqué comme INVENTÉ (Mawdu)")
    
    # Texte arabe
    print(f"\n📝 Texte arabe:")
    print(f"{matn_ar}")
    
    print()

print("="*80)
print("✅ Lecture terminée - Bonne nuit !")
print("="*80)

# Statistiques finales
cursor.execute("SELECT COUNT(*) FROM hadiths")
total = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM hadiths WHERE badge_alerte = 1")
mawdu = cursor.fetchone()[0]

print(f"\n📊 STATISTIQUES:")
print(f"   • Total: {total:,} hadiths")
print(f"   • Inventés détectés: {mawdu:,}")
print(f"   • Authentiques: {total - mawdu:,}")

conn.close()