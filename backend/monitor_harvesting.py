"""
Script de monitoring en temps réel du harvesting
Affiche les statistiques de la base de données pendant l'exécution
"""

import sqlite3
import time
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "database" / "almizan_v7.db"

def get_stats():
    """Récupère les statistiques actuelles"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total hadiths
    cursor.execute("SELECT COUNT(*) FROM entries")
    total = cursor.fetchone()[0]
    
    # Par grade
    cursor.execute("""
        SELECT grade_primary, COUNT(*) 
        FROM entries 
        GROUP BY grade_primary
        ORDER BY COUNT(*) DESC
    """)
    by_grade = cursor.fetchall()
    
    # Par livre
    cursor.execute("""
        SELECT book_name_ar, COUNT(*) 
        FROM entries 
        WHERE book_name_ar IS NOT NULL AND book_name_ar != ''
        GROUP BY book_name_ar
        ORDER BY COUNT(*) DESC
        LIMIT 10
    """)
    by_book = cursor.fetchall()
    
    # Derniers insérés
    cursor.execute("""
        SELECT hadith_id_dorar, grade_primary, book_name_ar
        FROM entries
        ORDER BY rowid DESC
        LIMIT 5
    """)
    recent = cursor.fetchall()
    
    conn.close()
    
    return {
        "total": total,
        "by_grade": by_grade,
        "by_book": by_book,
        "recent": recent
    }

def print_stats(stats, iteration):
    """Affiche les statistiques"""
    print("\n" + "="*70)
    print(f"📊 MONITORING AL-MĪZĀN — Refresh #{iteration}")
    print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
    print("="*70)
    
    print(f"\n📚 TOTAL HADITHS: {stats['total']}")
    
    if stats['by_grade']:
        print(f"\n📊 PAR GRADE:")
        for grade, count in stats['by_grade']:
            pct = count / max(stats['total'], 1) * 100
            print(f"   • {grade:15s}: {count:5d} ({pct:5.1f}%)")
    
    if stats['by_book']:
        print(f"\n📖 PAR LIVRE:")
        for book, count in stats['by_book']:
            print(f"   • {book[:30]:30s}: {count:5d}")
    
    if stats['recent']:
        print(f"\n🆕 DERNIERS INSÉRÉS:")
        for hadith_id, grade, book in stats['recent']:
            book_display = book[:25] if book else "N/A"
            print(f"   • ID {hadith_id:6s} | {grade:10s} | {book_display}")
    
    print("\n" + "="*70)

def monitor(interval=5, max_iterations=None):
    """
    Monitore la base de données en temps réel
    
    Args:
        interval: Intervalle en secondes entre chaque refresh
        max_iterations: Nombre max d'itérations (None = infini)
    """
    print("\n🕋 AL-MĪZĀN V7.0 — MONITORING HARVESTING")
    print(f"📊 Refresh toutes les {interval} secondes")
    print("⌨️  Ctrl+C pour arrêter\n")
    
    iteration = 0
    try:
        while True:
            iteration += 1
            
            try:
                stats = get_stats()
                print_stats(stats, iteration)
            except Exception as e:
                print(f"❌ Erreur: {e}")
            
            if max_iterations and iteration >= max_iterations:
                break
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n✅ Monitoring arrêté")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitorer le harvesting")
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Intervalle en secondes (défaut: 5)"
    )
    parser.add_argument(
        "--max",
        type=int,
        help="Nombre max d'itérations"
    )
    
    args = parser.parse_args()
    
    monitor(interval=args.interval, max_iterations=args.max)