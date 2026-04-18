#!/usr/bin/env python3
"""
Vérification finale de l'import Kutub al-Sittah
"""

import sqlite3
from datetime import datetime

def check_final_status():
    """Vérifie l'état final de l'import"""
    conn = sqlite3.connect("backend/almizane.db")
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("📊 RAPPORT FINAL - IMPORT KUTUB AL-SITTAH")
    print("="*70)
    print(f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Stats par collection
    cursor.execute("""
        SELECT collection, COUNT(*) as count
        FROM hadiths
        WHERE source_api = 'hadith_gading'
        GROUP BY collection
        ORDER BY collection
    """)
    
    collections = cursor.fetchall()
    
    # Objectifs
    targets = {
        'bukhari': 6638,
        'muslim': 4930,
        'abudawud': 4590,
        'tirmidzi': 3891,
        'nasai': 5662,
        'ibnmajah': 4331
    }
    
    print("📚 RÉSULTATS PAR LIVRE")
    print("-" * 70)
    
    total_imported = 0
    total_target = sum(targets.values())
    completed = 0
    
    for book, target in targets.items():
        count = next((c[1] for c in collections if c[0] == book), 0)
        total_imported += count
        percent = (count * 100) // target if target > 0 else 0
        
        status = "✅" if count >= target else "⚠️" if count > 0 else "❌"
        if count >= target:
            completed += 1
        
        print(f"{status} {book.upper():12} : {count:5,} / {target:,} ({percent:3}%)")
    
    print()
    print("="*70)
    print(f"📊 TOTAL GÉNÉRAL")
    print("-" * 70)
    print(f"Hadiths importés  : {total_imported:,}")
    print(f"Objectif total    : {total_target:,}")
    print(f"Progression       : {(total_imported * 100) // total_target}%")
    print(f"Livres complétés  : {completed} / 6")
    print()
    
    print()
    
    # Analyse des manquants
    print("="*70)
    print("🔍 ANALYSE DES LIVRES INCOMPLETS")
    print("-" * 70)
    
    for book, target in targets.items():
        count = next((c[1] for c in collections if c[0] == book), 0)
        if count < target:
            missing = target - count
            print(f"⚠️ {book.upper():12} : {missing:,} hadiths manquants")
            if count == 0:
                print(f"   → Livre non disponible dans l'API")
            else:
                print(f"   → Import partiel ({(count * 100) // target}%)")
    
    print()
    print("="*70)
    
    conn.close()
    
    return {
        'total_imported': total_imported,
        'total_target': total_target,
        'completed': completed
    }

if __name__ == "__main__":
    stats = check_final_status()
    
    print("\n✅ Vérification terminée")
    print(f"📊 {stats['total_imported']:,} hadiths importés sur {stats['total_target']:,} attendus")