#!/usr/bin/env python3
"""Vérification rapide de l'état de l'import"""

import sqlite3
import os

DB_PATH = 'backend/almizane.db'

if not os.path.exists(DB_PATH):
    print("❌ Base de données introuvable!")
    exit(1)

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total
    cursor.execute('SELECT COUNT(*) FROM hadiths')
    total = cursor.fetchone()[0]
    
    # Par collection
    cursor.execute('''
        SELECT collection, COUNT(*) as count 
        FROM hadiths 
        GROUP BY collection 
        ORDER BY count DESC
    ''')
    sources = cursor.fetchall()
    
    conn.close()
    
    print(f"📊 ÉTAT DE LA BASE DE DONNÉES")
    print("=" * 50)
    print(f"Total hadiths: {total:,}")
    print("\nRépartition par collection:")
    for collection, count in sources:
        print(f"  • {collection}: {count:,} hadiths")
    print("=" * 50)
    
    # Vérifier si les nouvelles collections sont présentes
    new_collections = ['Riyad al-Salihin', '40 Hadiths Nawawi', 
                       'Bulugh al-Maram', 'Al-Adab al-Mufrad']
    
    found = [s[0] for s in sources if s[0] in new_collections]
    
    if found:
        print(f"\n✅ Collections Option A détectées: {len(found)}/4")
        for coll in found:
            print(f"  ✓ {coll}")
    else:
        print("\n⚠️  Aucune collection Option A détectée")
        print("L'import n'a peut-être pas encore commencé ou a échoué")
        
except Exception as e:
    print(f"❌ Erreur: {e}")