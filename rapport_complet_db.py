#!/usr/bin/env python3
"""
Rapport complet de la base de données Al-Mizan
"""

import sqlite3
from datetime import datetime

def rapport_complet():
    """Génère un rapport complet de la base de données"""
    conn = sqlite3.connect("backend/almizane.db")
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("📊 RAPPORT COMPLET - BASE DE DONNÉES AL-MIZAN")
    print("="*80)
    print(f"📅 Date : {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
    print()
    
    # 1. Total général
    print("="*80)
    print("📈 STATISTIQUES GÉNÉRALES")
    print("-" * 80)
    
    cursor.execute("SELECT COUNT(*) FROM hadiths")
    total = cursor.fetchone()[0]
    print(f"Total de hadiths en base : {total:,}")
    
    cursor.execute("SELECT COUNT(*) FROM hadiths WHERE matn_fr IS NOT NULL")
    avec_trad = cursor.fetchone()[0]
    print(f"Avec traduction française : {avec_trad:,} ({(avec_trad*100)//total if total > 0 else 0}%)")
    
    cursor.execute("SELECT COUNT(*) FROM hadiths WHERE matn_fr IS NULL")
    sans_trad = cursor.fetchone()[0]
    print(f"Sans traduction française : {sans_trad:,} ({(sans_trad*100)//total if total > 0 else 0}%)")
    print()
    
    # 2. Statistiques par collection
    print("="*80)
    print("📚 STATISTIQUES PAR COLLECTION")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            collection,
            COUNT(*) as nombre,
            COUNT(CASE WHEN grade_final = 'Sahih' THEN 1 END) as sahih,
            COUNT(CASE WHEN grade_final = 'Hasan' THEN 1 END) as hasan,
            COUNT(CASE WHEN grade_final LIKE 'Da%' THEN 1 END) as daif,
            COUNT(CASE WHEN badge_alerte = 1 THEN 1 END) as mawduu
        FROM hadiths
        GROUP BY collection
        ORDER BY nombre DESC
    """)
    
    collections = cursor.fetchall()
    
    # En-tête du tableau
    print(f"{'Collection':<15} | {'Total':>8} | {'Sahih':>8} | {'Hasan':>8} | {'Daif':>8} | {'Mawduu':>8}")
    print("-" * 80)
    
    total_sahih = 0
    total_hasan = 0
    total_daif = 0
    total_mawduu = 0
    
    for row in collections:
        collection, nombre, sahih, hasan, daif, mawduu = row
        total_sahih += sahih
        total_hasan += hasan
        total_daif += daif
        total_mawduu += mawduu
        
        print(f"{collection.upper():<15} | {nombre:>8,} | {sahih:>8,} | {hasan:>8,} | {daif:>8,} | {mawduu:>8,}")
    
    print("-" * 80)
    print(f"{'TOTAL':<15} | {total:>8,} | {total_sahih:>8,} | {total_hasan:>8,} | {total_daif:>8,} | {total_mawduu:>8,}")
    print()
    
    # 3. Répartition par authenticité
    print("="*80)
    print("🎯 RÉPARTITION PAR AUTHENTICITÉ")
    print("-" * 80)
    
    if total > 0:
        pct_sahih = (total_sahih * 100) // total
        pct_hasan = (total_hasan * 100) // total
        pct_daif = (total_daif * 100) // total
        pct_mawduu = (total_mawduu * 100) // total
        
        print(f"✅ Sahih (Authentique)     : {total_sahih:>8,} hadiths ({pct_sahih:>3}%)")
        print(f"✅ Hasan (Bon)             : {total_hasan:>8,} hadiths ({pct_hasan:>3}%)")
        print(f"⚠️  Daif (Faible)          : {total_daif:>8,} hadiths ({pct_daif:>3}%)")
        print(f"❌ Mawduu (Forgé/Alerte)   : {total_mawduu:>8,} hadiths ({pct_mawduu:>3}%)")
    print()
    
    # 4. Sources des données
    print("="*80)
    print("🌐 SOURCES DES DONNÉES")
    print("-" * 80)
    
    cursor.execute("""
        SELECT source_api, COUNT(*) as nombre
        FROM hadiths
        GROUP BY source_api
        ORDER BY nombre DESC
    """)
    
    sources = cursor.fetchall()
    for source, nombre in sources:
        source_name = source if source else "Non spécifié"
        pct = (nombre * 100) // total if total > 0 else 0
        print(f"{source_name:<30} : {nombre:>8,} hadiths ({pct:>3}%)")
    print()
    
    # 5. Top 10 des livres les plus fournis
    print("="*80)
    print("📖 TOP 10 DES LIVRES LES PLUS FOURNIS")
    print("-" * 80)
    
    cursor.execute("""
        SELECT collection, book_number, COUNT(*) as nombre
        FROM hadiths
        WHERE book_number IS NOT NULL
        GROUP BY collection, book_number
        ORDER BY nombre DESC
        LIMIT 10
    """)
    
    top_books = cursor.fetchall()
    for i, (collection, book_num, nombre) in enumerate(top_books, 1):
        print(f"{i:>2}. {collection.upper():<12} - Livre {book_num:<3} : {nombre:>5,} hadiths")
    print()
    
    print("="*80)
    
    conn.close()
    
    return {
        'total': total,
        'avec_traduction': avec_trad,
        'sans_traduction': sans_trad,
        'sahih': total_sahih,
        'hasan': total_hasan,
        'daif': total_daif,
        'mawduu': total_mawduu
    }

if __name__ == "__main__":
    stats = rapport_complet()
    print("\n✅ Rapport généré avec succès")
    print(f"📊 {stats['total']:,} hadiths analysés")