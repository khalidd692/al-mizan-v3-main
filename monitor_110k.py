#!/usr/bin/env python3
"""
📊 Moniteur de progression vers 110K hadiths
"""

import sqlite3
import time
from datetime import datetime

def monitor():
    db_path = "backend/almizane.db"
    target = 110000
    
    print("\n" + "="*80)
    print("📊 MONITEUR DE PROGRESSION - OBJECTIF 110K HADITHS")
    print("="*80)
    
    while True:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Total hadiths
            cursor.execute("SELECT COUNT(*) FROM hadiths")
            total = cursor.fetchone()[0]
            
            # Par collection
            cursor.execute("""
                SELECT collection, COUNT(*) 
                FROM hadiths 
                GROUP BY collection 
                ORDER BY COUNT(*) DESC
            """)
            collections = cursor.fetchall()
            
            conn.close()
            
            # Affichage
            progress = (total / target) * 100
            remaining = target - total
            
            print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')}")
            print(f"📊 Total: {total:,} / {target:,} hadiths ({progress:.1f}%)")
            print(f"📈 Reste: {remaining:,} hadiths")
            
            print(f"\n📚 Top 10 collections:")
            for i, (coll, count) in enumerate(collections[:10], 1):
                print(f"   {i:2d}. {coll:30s} {count:>6,} hadiths")
            
            if total >= target:
                print("\n🎉 OBJECTIF ATTEINT ! 110,000 hadiths ✅")
                break
            
            time.sleep(30)  # Mise à jour toutes les 30 secondes
            
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring arrêté")
            break
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor()