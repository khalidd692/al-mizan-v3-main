#!/usr/bin/env python3
"""
Moniteur en temps réel du Mega Harvester 100K
"""

import sqlite3
import time
import os
from datetime import datetime

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_stats():
    conn = sqlite3.connect('backend/almizane.db')
    
    # Total
    total = conn.execute("SELECT COUNT(*) FROM hadiths").fetchone()[0]
    
    # Par collection
    collections = conn.execute("""
        SELECT collection, COUNT(*) as count 
        FROM hadiths 
        GROUP BY collection 
        ORDER BY count DESC
    """).fetchall()
    
    # Par source
    sources = conn.execute("""
        SELECT source_api, COUNT(*) as count 
        FROM hadiths 
        WHERE source_api IS NOT NULL
        GROUP BY source_api 
        ORDER BY count DESC
    """).fetchall()
    
    conn.close()
    
    return {
        'total': total,
        'collections': collections,
        'sources': sources
    }

def display_dashboard():
    while True:
        clear_screen()
        stats = get_stats()
        
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 20 + "🚀 MEGA HARVESTER 100K - LIVE" + " " * 29 + "║")
        print("╚" + "═" * 78 + "╝")
        print()
        
        # Progression
        total = stats['total']
        target = 100000
        progress = (total / target) * 100
        remaining = target - total
        
        print(f"📊 PROGRESSION GLOBALE")
        print(f"   Total actuel: {total:,} hadiths")
        print(f"   Objectif:     {target:,} hadiths")
        print(f"   Progression:  {progress:.1f}%")
        print(f"   Manquant:     {remaining:,} hadiths")
        print()
        
        # Barre de progression
        bar_length = 50
        filled = int(bar_length * progress / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"   [{bar}] {progress:.1f}%")
        print()
        
        # Collections
        print("📚 PAR COLLECTION (Top 10)")
        for i, (coll, count) in enumerate(stats['collections'][:10], 1):
            print(f"   {i:2d}. {coll:15s} : {count:>6,} hadiths")
        print()
        
        # Sources
        print("🌐 PAR SOURCE")
        for source, count in stats['sources']:
            if source:
                print(f"   • {source:20s} : {count:>6,} hadiths")
        print()
        
        print(f"⏰ Dernière mise à jour: {datetime.now().strftime('%H:%M:%S')}")
        print()
        print("Appuyez sur Ctrl+C pour quitter...")
        
        time.sleep(5)

if __name__ == '__main__':
    try:
        display_dashboard()
    except KeyboardInterrupt:
        print("\n\n✅ Monitoring arrêté.")