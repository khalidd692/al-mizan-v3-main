#!/usr/bin/env python3
"""
Analyse complète de l'état actuel du harvesting
"""

import sqlite3
from datetime import datetime
from collections import defaultdict

def analyze_database():
    conn = sqlite3.connect('backend/almizane.db')
    cursor = conn.cursor()
    
    print("=" * 80)
    print("📊 ANALYSE COMPLÈTE DU HARVESTING AL-MIZAN")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. Statistiques globales
    cursor.execute('SELECT COUNT(*) FROM hadiths')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT collection) FROM hadiths')
    collections_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT source_api) FROM hadiths')
    sources_count = cursor.fetchone()[0]
    
    print("📈 STATISTIQUES GLOBALES")
    print("-" * 80)
    print(f"Total hadiths en base: {total:,}")
    print(f"Collections distinctes: {collections_count}")
    print(f"Sources API distinctes: {sources_count}")
    print(f"Progression vers objectif 150K: {(total/150000)*100:.1f}%")
    print()
    
    # 2. Répartition par collection
    cursor.execute('''
        SELECT collection, COUNT(*) as count 
        FROM hadiths 
        GROUP BY collection 
        ORDER BY count DESC
    ''')
    collections = cursor.fetchall()
    
    print("📚 RÉPARTITION PAR COLLECTION")
    print("-" * 80)
    for collection, count in collections:
        print(f"  {collection:40s} : {count:>6,} hadiths")
    print()
    
    # 3. Répartition par source API
    cursor.execute('''
        SELECT source_api, COUNT(*) as count 
        FROM hadiths 
        GROUP BY source_api 
        ORDER BY count DESC
    ''')
    sources = cursor.fetchall()
    
    print("🌐 RÉPARTITION PAR SOURCE API")
    print("-" * 80)
    for source, count in sources:
        source_name = source if source else "Non spécifié"
        print(f"  {source_name:40s} : {count:>6,} hadiths")
    print()
    
    # 4. Analyse temporelle
    cursor.execute('''
        SELECT 
            DATE(inserted_at) as date,
            COUNT(*) as count
        FROM hadiths
        WHERE inserted_at IS NOT NULL
        GROUP BY DATE(inserted_at)
        ORDER BY date DESC
        LIMIT 7
    ''')
    timeline = cursor.fetchall()
    
    print("📅 ACTIVITÉ DES 7 DERNIERS JOURS")
    print("-" * 80)
    for date, count in timeline:
        print(f"  {date} : {count:>6,} hadiths importés")
    print()
    
    # 5. Qualité des données
    cursor.execute('SELECT COUNT(*) FROM hadiths WHERE matn_ar IS NOT NULL AND matn_ar != ""')
    with_arabic = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM hadiths WHERE matn_fr IS NOT NULL AND matn_fr != ""')
    with_french = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM hadiths WHERE isnad_brut IS NOT NULL AND isnad_brut != ""')
    with_isnad = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM hadiths WHERE grade_final IS NOT NULL AND grade_final != ""')
    with_grade = cursor.fetchone()[0]
    
    print("✅ QUALITÉ DES DONNÉES")
    print("-" * 80)
    print(f"  Avec texte arabe    : {with_arabic:>6,} ({(with_arabic/total)*100:.1f}%)")
    print(f"  Avec traduction FR  : {with_french:>6,} ({(with_french/total)*100:.1f}%)")
    print(f"  Avec chaîne (isnad) : {with_isnad:>6,} ({(with_isnad/total)*100:.1f}%)")
    print(f"  Avec grade          : {with_grade:>6,} ({(with_grade/total)*100:.1f}%)")
    print()
    
    # 6. Kutub al-Sittah - Analyse détaillée
    kutub_sittah = [
        'Sahih al-Bukhari',
        'Sahih Muslim', 
        'Sunan Abu Dawud',
        'Jami` at-Tirmidhi',
        'Sunan an-Nasa\'i',
        'Sunan Ibn Majah'
    ]
    
    print("📖 KUTUB AL-SITTAH (Les Six Livres)")
    print("-" * 80)
    total_kutub = 0
    for book in kutub_sittah:
        cursor.execute('SELECT COUNT(*) FROM hadiths WHERE collection = ?', (book,))
        count = cursor.fetchone()[0]
        total_kutub += count
        status = "✅" if count > 0 else "⏳"
        print(f"  {status} {book:40s} : {count:>6,} hadiths")
    print(f"\n  Total Kutub al-Sittah: {total_kutub:,} hadiths")
    print()
    
    # 7. Projections
    print("🎯 PROJECTIONS ET OBJECTIFS")
    print("-" * 80)
    remaining = 150000 - total
    print(f"  Objectif final      : 150,000 hadiths")
    print(f"  Actuellement en base: {total:,} hadiths")
    print(f"  Restant à importer  : {remaining:,} hadiths")
    print()
    
    # Sources potentielles
    print("  Sources identifiées pour compléter:")
    print("    • hadith-gading.com  : ~30,000 hadiths (EN COURS)")
    print("    • Shamela.ws         : ~40,000 hadiths")
    print("    • Univ. Médine       : ~20,000 hadiths")
    print("    • Islamweb.net       : ~10,000 hadiths")
    print("    • Autres sources     : ~10,000 hadiths")
    print("  ────────────────────────────────────")
    print("  Total projeté        : ~110,000 hadiths supplémentaires")
    print(f"  Total final estimé   : ~{total + 110000:,} hadiths (107% de l'objectif)")
    print()
    
    # 8. Recommandations
    print("💡 RECOMMANDATIONS")
    print("-" * 80)
    
    if total < 60000:
        print("  🔴 PRIORITÉ HAUTE: Continuer l'import hadith-gading.com")
        print("     → Kutub al-Sittah en cours")
        print("     → Musnad Ahmad à venir")
    elif total < 100000:
        print("  🟡 PRIORITÉ MOYENNE: Diversifier les sources")
        print("     → Activer Shamela.ws")
        print("     → Préparer Université Médine")
    else:
        print("  🟢 PRIORITÉ BASSE: Finalisation")
        print("     → Compléter les recueils manquants")
        print("     → Vérifier la qualité des données")
    
    print()
    print("=" * 80)
    
    conn.close()

if __name__ == '__main__':
    analyze_database()