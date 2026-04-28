#!/usr/bin/env python3
"""
Script de monitoring en temps réel de l'import Bukhari
Affiche la progression et les statistiques
"""

import sqlite3
import time
import os
from datetime import datetime, timedelta

DB_PATH = "backend/almizane.db"

def get_stats():
    """Récupère les statistiques actuelles"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Compter les hadiths par livre
    cursor.execute("""
        SELECT livre, COUNT(*) 
        FROM hadiths 
        WHERE source = 'hadith_gading'
        GROUP BY livre
    """)
    
    stats = {}
    for livre, count in cursor.fetchall():
        stats[livre] = count
    
    conn.close()
    return stats

def estimate_completion(current, total, start_time):
    """Estime le temps restant"""
    if current == 0:
        return "Calcul en cours..."
    
    elapsed = time.time() - start_time
    rate = current / elapsed  # hadiths par seconde
    remaining = total - current
    
    if rate > 0:
        eta_seconds = remaining / rate
        eta = timedelta(seconds=int(eta_seconds))
        completion_time = datetime.now() + eta
        return f"{eta} (fin prévue: {completion_time.strftime('%H:%M:%S')})"
    
    return "Calcul en cours..."

def clear_screen():
    """Efface l'écran"""
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    """Boucle principale de monitoring"""
    print("🚀 Démarrage du monitoring...")
    print("Appuyez sur Ctrl+C pour arrêter\n")
    time.sleep(2)
    
    start_time = time.time()
    last_count = 0
    
    # Objectifs par livre
    targets = {
        'bukhari': 6638,
        'muslim': 5362,
        'abu-dawud': 4590,
        'tirmidhi': 3891,
        'nasai': 5662,
        'ibn-majah': 4331
    }
    
    try:
        while True:
            clear_screen()
            
            # En-tête
            print("=" * 70)
            print("📊 MONITORING IMPORT HADITH GADING - AL-MIZAN V3")
            print("=" * 70)
            print(f"⏰ {datetime.now().strftime('%H:%M:%S')} | Durée: {timedelta(seconds=int(time.time() - start_time))}")
            print("=" * 70)
            print()
            
            # Récupérer les stats
            stats = get_stats()
            
            # Calculer le total
            total_imported = sum(stats.values())
            total_target = sum(targets.values())
            
            # Afficher par livre
            print("📚 PROGRESSION PAR LIVRE:")
            print("-" * 70)
            
            for livre, target in targets.items():
                count = stats.get(livre, 0)
                percentage = (count / target * 100) if target > 0 else 0
                bar_length = 40
                filled = int(bar_length * count / target)
                bar = "█" * filled + "░" * (bar_length - filled)
                
                status = "🔄" if count > 0 and count < target else "⏳" if count == 0 else "✅"
                
                print(f"{status} {livre.upper():12} [{bar}] {count:5}/{target} ({percentage:5.1f}%)")
            
            print("-" * 70)
            
            # Total global
            global_percentage = (total_imported / total_target * 100) if total_target > 0 else 0
            print(f"\n📊 TOTAL GLOBAL: {total_imported:,} / {total_target:,} ({global_percentage:.1f}%)")
            
            # Vitesse d'import
            if total_imported > last_count:
                elapsed = time.time() - start_time
                rate_per_min = (total_imported / elapsed) * 60 if elapsed > 0 else 0
                print(f"⚡ Vitesse: {rate_per_min:.1f} hadiths/minute")
                
                # Estimation temps restant
                if total_imported > 0:
                    eta = estimate_completion(total_imported, total_target, start_time)
                    print(f"⏱️  Temps restant estimé: {eta}")
            
            last_count = total_imported
            
            # Détails Bukhari (livre en cours)
            bukhari_count = stats.get('bukhari', 0)
            if bukhari_count > 0:
                print("\n" + "=" * 70)
                print("🎯 FOCUS BUKHARI (en cours):")
                print("-" * 70)
                bukhari_target = targets['bukhari']
                bukhari_pct = (bukhari_count / bukhari_target * 100)
                print(f"   Importés: {bukhari_count:,} / {bukhari_target:,}")
                print(f"   Progression: {bukhari_pct:.2f}%")
                print(f"   Restants: {bukhari_target - bukhari_count:,}")
            
            print("\n" + "=" * 70)
            print("💡 Commandes utiles:")
            print("   • python check_bukhari.py  - Vérifier manuellement")
            print("   • tasklist | findstr python - Voir processus actifs")
            print("=" * 70)
            
            # Attendre avant la prochaine mise à jour
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\n✋ Monitoring arrêté par l'utilisateur")
        print(f"📊 Dernier décompte: {total_imported:,} hadiths importés")
        print("=" * 70)

if __name__ == "__main__":
    main()