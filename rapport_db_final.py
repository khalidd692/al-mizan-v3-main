#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rapport final de la base de données Al-Mizan
"""
import sqlite3
import os

def analyze_database(db_path):
    """Analyse complète d'une base de données"""
    if not os.path.exists(db_path):
        print(f"❌ Base de données introuvable: {db_path}\n")
        return
    
    print(f"\n{'='*60}")
    print(f"📊 ANALYSE DE: {db_path}")
    print(f"{'='*60}")
    
    # Taille du fichier
    size_mb = os.path.getsize(db_path) / (1024 * 1024)
    print(f"\n3. TAILLE PHYSIQUE DU FICHIER:")
    print(f"   {size_mb:.2f} MB ({os.path.getsize(db_path):,} octets)")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Liste des tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\n📋 TABLES DISPONIBLES: {', '.join(tables)}")
    
    # Vérifier si table hadiths existe
    if 'hadiths' in tables:
        # 1. Compte total
        cursor.execute("SELECT COUNT(*) FROM hadiths")
        total = cursor.fetchone()[0]
        print(f"\n1. COMPTE TOTAL:")
        print(f"   ✅ {total:,} hadiths en base de données")
        
        # 2. Détail par collection
        cursor.execute("""
            SELECT collection, COUNT(*) as nombre 
            FROM hadiths 
            GROUP BY collection 
            ORDER BY COUNT(*) DESC
        """)
        print(f"\n2. DÉTAIL PAR COLLECTION:")
        for row in cursor.fetchall():
            print(f"   • {row[0]}: {row[1]:,} hadiths")
        
        # 5. Traductions françaises
        cursor.execute("SELECT COUNT(*) FROM hadiths WHERE matn_fr IS NOT NULL AND matn_fr != ''")
        total_fr = cursor.fetchone()[0]
        print(f"\n5. HADITHS AVEC TRADUCTION FRANÇAISE:")
        print(f"   ✅ {total_fr:,} hadiths traduits ({total_fr/total*100:.1f}%)")
        
        # 6. Hadiths inventés
        cursor.execute("SELECT COUNT(*) FROM hadiths WHERE badge_alerte = 1")
        total_mawdu = cursor.fetchone()[0]
        print(f"\n6. HADITHS INVENTÉS DÉTECTÉS:")
        print(f"   ⚠️  {total_mawdu:,} hadiths marqués comme inventés")
        
        # 4. Exemples de hadiths en français
        cursor.execute("""
            SELECT collection, matn_fr, grade_final 
            FROM hadiths 
            WHERE matn_fr IS NOT NULL AND matn_fr != ''
            LIMIT 5
        """)
        print(f"\n4. EXEMPLES DE HADITHS EN FRANÇAIS:")
        print("="*60)
        for i, row in enumerate(cursor.fetchall(), 1):
            collection, matn, grade = row
            print(f"\n📖 Hadith #{i}")
            print(f"   Collection: {collection}")
            print(f"   Grade: {grade or 'Non évalué'}")
            print(f"   Texte:")
            # Afficher le texte complet, limité à 300 caractères pour la lisibilité
            if len(matn) > 300:
                print(f"   {matn[:300]}...")
            else:
                print(f"   {matn}")
            print("-"*60)
    
    elif 'entries' in tables:
        # Base de données v7 avec table entries
        cursor.execute("SELECT COUNT(*) FROM entries")
        total = cursor.fetchone()[0]
        print(f"\n⚠️  Cette base utilise la table 'entries' (v7)")
        print(f"   Total d'entrées: {total:,}")
        
        # Vérifier les colonnes disponibles
        cursor.execute("PRAGMA table_info(entries)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"   Colonnes: {', '.join(columns[:10])}...")
    
    else:
        print("\n❌ Aucune table 'hadiths' ou 'entries' trouvée")
    
    conn.close()
    print(f"\n{'='*60}\n")

# Analyser les deux bases de données possibles
print("\n🔍 RAPPORT DE PREUVE FINAL - AL-MIZAN")
print("="*60)

databases = [
    'backend/almizane.db',
    'backend/database/almizan_v7.db'
]

for db in databases:
    analyze_database(db)

print("\n✅ ANALYSE TERMINÉE")