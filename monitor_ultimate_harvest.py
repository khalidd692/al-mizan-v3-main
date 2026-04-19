#!/usr/bin/env python3
"""
📊 MONITORING EN TEMPS RÉEL - ULTIMATE HARVESTER
Suit la progression vers 200K+ hadiths
"""

import sqlite3
import time
import os
from datetime import datetime
from collections import defaultdict

DB_PATH = "backend/almizane.db"
LOG_FILE = "backend/ultimate_harvest.log"
TARGET = 200000

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_stats():
    """Récupère statistiques complètes"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total
    cursor.execute("SELECT COUNT(*) FROM hadiths")
    total = cursor.fetchone()[0]
    
    # Par source
    cursor.execute("""
        SELECT source_api, COUNT(*) 
        FROM hadiths 
        GROUP BY source_api 
        ORDER BY COUNT(*) DESC
    """)
    by_source = cursor.fetchall()
    
    # Par collection (top 15)
    cursor.execute("""
        SELECT collection, COUNT(*) 
        FROM hadiths 
        GROUP BY collection 
        ORDER BY COUNT(*) DESC
        LIMIT 15
    """)
    by_collection = cursor.fetchall()
    
    # Qualité
    cursor.execute("SELECT COUNT(*) FROM hadiths WHERE matn_fr IS NOT NULL AND matn_fr != ''")
    with_fr = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM hadiths WHERE grade_final IS NOT NULL AND grade_final != ''")
    with_grade = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM hadiths WHERE badge_alerte = 1")
    with_alert = cursor.fetchone()[0]
    
    # Derniers imports
    cursor.execute("""
        SELECT collection, COUNT(*) 
        FROM hadiths 
        WHERE inserted_at >= datetime('now', '-1 hour')
        GROUP BY collection
        ORDER BY COUNT(*) DESC
        LIMIT 5
    """)
    recent = cursor.fetchall()
    
    conn.close()
    
    return {
        'total': total,
        'by_source': by_source,
        'by_collection': by_collection,
        'with_fr': with_fr,
        'with_grade': with_grade,
        'with_alert': with_alert,
        'recent': recent
    }

def read_last_log_lines(n=10):
    """Lit les dernières lignes du log"""
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return lines[-n:] if len(lines) >= n else lines
    except:
        return []

def display_dashboard():
    """Affiche dashboard complet"""
    clear_screen()
    
    stats = get_stats()
    total = stats['total']
    progress = (total / TARGET) * 100
    remaining = TARGET - total
    
    print("=" * 100)
    print("🚀 ULTIMATE AUTONOMOUS HARVESTER - MONITORING EN TEMPS RÉEL")
    print("=" * 100)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Progression globale
    print("📊 PROGRESSION GLOBALE")
    print("-" * 100)
    print(f"Total hadiths:     {total:>10,}")
    print(f"Objectif:          {TARGET:>10,}")
    print(f"Restant:           {remaining:>10,}")
    print(f"Progression:       {progress:>9.2f}%")
    
    # Barre de progression
    bar_length = 50
    filled = int(bar_length * progress / 100)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"\n[{bar}] {progress:.1f}%")
    print()
    
    # Par source API
    print("🌐 RÉPARTITION PAR SOURCE API")
    print("-" * 100)
    for source, count in stats['by_source'][:10]:
        source_name = source if source else "Non spécifié"
        pct = (count / total) * 100 if total > 0 else 0
        print(f"  {source_name:30s} : {count:>8,} hadiths ({pct:>5.1f}%)")
    print()
    
    # Top collections
    print("📚 TOP 15 COLLECTIONS")
    print("-" * 100)
    for collection, count in stats['by_collection']:
        pct = (count / total) * 100 if total > 0 else 0
        print(f"  {collection:45s} : {count:>7,} ({pct:>5.1f}%)")
    print()
    
    # Qualité des données
    print("✅ QUALITÉ DES DONNÉES")
    print("-" * 100)
    fr_pct = (stats['with_fr'] / total) * 100 if total > 0 else 0
    grade_pct = (stats['with_grade'] / total) * 100 if total > 0 else 0
    alert_pct = (stats['with_alert'] / total) * 100 if total > 0 else 0
    
    print(f"  Avec traduction FR : {stats['with_fr']:>8,} ({fr_pct:>5.1f}%)")
    print(f"  Avec grade         : {stats['with_grade']:>8,} ({grade_pct:>5.1f}%)")
    print(f"  Avec badge alerte  : {stats['with_alert']:>8,} ({alert_pct:>5.1f}%)")
    print()
    
    # Activité récente
    if stats['recent']:
        print("🔥 ACTIVITÉ DERNIÈRE HEURE")
        print("-" * 100)
        for collection, count in stats['recent']:
            print(f"  {collection:45s} : +{count:>6,} hadiths")
        print()
    
    # Dernières lignes du log
    print("📝 DERNIÈRES ACTIVITÉS (LOG)")
    print("-" * 100)
    log_lines = read_last_log_lines(8)
    for line in log_lines:
        line = line.strip()
        if line:
            # Coloriser selon le type
            if "✅" in line or "Phase" in line:
                print(f"  {line}")
            elif "ERROR" in line or "Erreur" in line:
                print(f"  ⚠️  {line}")
            else:
                print(f"  {line}")
    
    print()
    print("=" * 100)
    print("🔄 Actualisation automatique toutes les 10 secondes... (Ctrl+C pour arrêter)")
    print("=" * 100)

def main():
    """Boucle principale de monitoring"""
    print("🚀 Démarrage du monitoring...")
    print("📊 Actualisation toutes les 10 secondes")
    print()
    
    try:
        while True:
            display_dashboard()
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n\n✅ Monitoring arrêté par l'utilisateur")
        print("📊 Dernières statistiques:")
        stats = get_stats()
        print(f"   Total: {stats['total']:,} hadiths")
        print(f"   Progression: {(stats['total']/TARGET)*100:.1f}%")

if __name__ == "__main__":
    main()