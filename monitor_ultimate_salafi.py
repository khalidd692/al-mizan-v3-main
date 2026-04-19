#!/usr/bin/env python3
"""
Monitoring en temps réel de l'Ultimate Salafi Harvester
"""

import sqlite3
import time
from datetime import datetime

def get_stats():
    """Récupère les statistiques de la base"""
    conn = sqlite3.connect('backend/almizane.db')
    cursor = conn.cursor()
    
    # Total hadiths
    cursor.execute("SELECT COUNT(*) FROM hadiths")
    total = cursor.fetchone()[0]
    
    # Par source
    cursor.execute("""
        SELECT import_source, COUNT(*) 
        FROM hadiths 
        GROUP BY import_source 
        ORDER BY COUNT(*) DESC
    """)
    by_source = cursor.fetchall()
    
    # Derniers imports
    cursor.execute("""
        SELECT import_source, COUNT(*) 
        FROM hadiths 
        WHERE import_date > datetime('now', '-1 hour')
        GROUP BY import_source
    """)
    last_hour = cursor.fetchall()
    
    conn.close()
    
    return {
        'total': total,
        'by_source': by_source,
        'last_hour': last_hour
    }

def print_dashboard():
    """Affiche le dashboard"""
    stats = get_stats()
    
    print("\n" + "=" * 80)
    print(f"🎯 ULTIMATE SALAFI HARVESTER - MONITORING")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    print(f"\n📊 TOTAL HADITHS: {stats['total']:,}")
    
    print("\n📚 PAR SOURCE:")
    for source, count in stats['by_source'][:15]:
        print(f"  {source:40} {count:>8,}")
    
    if stats['last_hour']:
        print("\n⚡ DERNIÈRE HEURE:")
        for source, count in stats['last_hour']:
            print(f"  {source:40} {count:>8,}")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    print("🚀 Démarrage du monitoring...")
    print("Appuyez sur Ctrl+C pour arrêter")
    
    try:
        while True:
            print_dashboard()
            time.sleep(30)  # Rafraîchir toutes les 30 secondes
    except KeyboardInterrupt:
        print("\n\n✅ Monitoring arrêté")