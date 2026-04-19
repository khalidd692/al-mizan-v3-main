#!/usr/bin/env python3
"""
📊 MONITORING TEMPS RÉEL - HARVESTING 200K
Affiche la progression en continu
"""

import sqlite3
import time
from datetime import datetime

DB_PATH = "backend/almizane.db"
TARGET = 200000

def get_stats():
    """Récupère statistiques complètes"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total hadiths
    cursor.execute("SELECT COUNT(*) FROM hadiths")
    total = cursor.fetchone()[0]
    
    # Par source API
    cursor.execute("""
        SELECT source_api, COUNT(*) 
        FROM hadiths 
        GROUP BY source_api 
        ORDER BY COUNT(*) DESC
    """)
    by_source = cursor.fetchall()
    
    # Hadiths avec badge alerte
    cursor.execute("SELECT COUNT(*) FROM hadiths WHERE badge_alerte = 1")
    alertes = cursor.fetchone()[0]
    
    # Hadiths avec traduction française
    cursor.execute("SELECT COUNT(*) FROM hadiths WHERE matn_fr IS NOT NULL")
    traduits = cursor.fetchone()[0]
    
    # Derniers ajouts
    cursor.execute("""
        SELECT collection, COUNT(*) 
        FROM hadiths 
        WHERE id > (SELECT MAX(id) - 1000 FROM hadiths)
        GROUP BY collection
        ORDER BY COUNT(*) DESC
        LIMIT 5
    """)
    recent = cursor.fetchall()
    
    conn.close()
    
    return {
        'total': total,
        'by_source': by_source,
        'alertes': alertes,
        'traduits': traduits,
        'recent': recent
    }

def display_progress(stats, start_total):
    """Affiche progression formatée"""
    total = stats['total']
    progress = (total / TARGET) * 100
    added = total - start_total
    remaining = TARGET - total
    
    print("\n" + "="*80)
    print(f"🚀 HARVESTING AUTONOME 200K - {datetime.now().strftime('%H:%M:%S')}")
    print("="*80)
    
    print(f"\n📊 PROGRESSION GLOBALE")
    print(f"   Total actuel: {total:,} hadiths")
    print(f"   Objectif: {TARGET:,} hadiths")
    print(f"   Progression: {progress:.2f}%")
    print(f"   Ajoutés depuis démarrage: +{added:,}")
    print(f"   Restant: {remaining:,} hadiths")
    
    # Barre de progression
    bar_length = 50
    filled = int(bar_length * progress / 100)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"   [{bar}] {progress:.1f}%")
    
    print(f"\n📡 PAR SOURCE API")
    for source, count in stats['by_source']:
        print(f"   {source}: {count:,} hadiths")
    
    print(f"\n⚠️  HADITHS AVEC ALERTE")
    print(f"   Badge alerte (Mawdu'/Batil): {stats['alertes']:,}")
    
    print(f"\n🌍 TRADUCTIONS")
    print(f"   Hadiths traduits en français: {stats['traduits']:,}")
    
    if stats['recent']:
        print(f"\n🔥 DERNIERS AJOUTS (1000 derniers)")
        for collection, count in stats['recent']:
            print(f"   {collection}: {count:,}")
    
    print("\n" + "="*80)

def main():
    """Monitoring en boucle"""
    print("🚀 DÉMARRAGE MONITORING HARVESTING 200K")
    print("Appuyez sur Ctrl+C pour arrêter\n")
    
    start_stats = get_stats()
    start_total = start_stats['total']
    
    try:
        while True:
            stats = get_stats()
            display_progress(stats, start_total)
            
            if stats['total'] >= TARGET:
                print("\n🎉 OBJECTIF 200K ATTEINT!")
                break
            
            time.sleep(30)  # Rafraîchir toutes les 30 secondes
            
    except KeyboardInterrupt:
        print("\n\n⏸️  Monitoring arrêté")
        final_stats = get_stats()
        print(f"\nTotal final: {final_stats['total']:,} hadiths")

if __name__ == "__main__":
    main()