#!/usr/bin/env python3
"""
Monitoring en temps réel de l'import des Kutub al-Sittah
"""

import sqlite3
import time
from datetime import datetime

def get_stats():
    """Récupère les statistiques actuelles"""
    conn = sqlite3.connect("backend/almizane.db")
    cursor = conn.cursor()
    
    # Stats par collection
    cursor.execute("""
        SELECT collection, COUNT(*) as count
        FROM hadiths
        WHERE source_api = 'hadith_gading'
        GROUP BY collection
        ORDER BY collection
    """)
    
    collections = cursor.fetchall()
    conn.close()
    
    return collections

def display_progress():
    """Affiche la progression en temps réel"""
    
    # Objectifs par livre
    targets = {
        'bukhari': 6638,
        'muslim': 4930,
        'abudawud': 4590,
        'tirmidzi': 3891,
        'nasai': 5662,
        'ibnmajah': 4331
    }
    
    total_target = sum(targets.values())
    
    print("\n" + "="*70)
    print("🚀 IMPORT KUTUB AL-SITTAH - MONITORING EN TEMPS RÉEL")
    print("="*70)
    print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    stats = get_stats()
    stats_dict = {row[0]: row[1] for row in stats}
    
    total_imported = 0
    
    for book, target in targets.items():
        count = stats_dict.get(book, 0)
        total_imported += count
        percent = (count * 100) // target if target > 0 else 0
        
        # Barre de progression
        bar_length = 40
        filled = (count * bar_length) // target if target > 0 else 0
        bar = "█" * filled + "░" * (bar_length - filled)
        
        status = "✅" if count >= target else "⏳"
        
        print(f"{status} {book.upper():12} [{bar}] {count:5}/{target} ({percent:3}%)")
    
    print()
    print("="*70)
    
    overall_percent = (total_imported * 100) // total_target
    overall_bar_length = 60
    overall_filled = (total_imported * overall_bar_length) // total_target
    overall_bar = "█" * overall_filled + "░" * (overall_bar_length - overall_filled)
    
    print(f"📊 TOTAL: [{overall_bar}]")
    print(f"   {total_imported:,} / {total_target:,} hadiths ({overall_percent}%)")
    print("="*70)
    
    return total_imported >= total_target

if __name__ == "__main__":
    print("\n🔄 Monitoring démarré... (Ctrl+C pour arrêter)")
    
    try:
        while True:
            completed = display_progress()
            
            if completed:
                print("\n🎉 IMPORT COMPLET TERMINÉ !")
                break
            
            time.sleep(5)  # Rafraîchir toutes les 5 secondes
            
    except KeyboardInterrupt:
        print("\n\n⏸️  Monitoring arrêté par l'utilisateur")