"""
Script d'application des migrations v2 pour le Vérificateur Mîzân
Applique les zones 33-40 et le seed complet des muḥaddithīn
"""
import sqlite3
from pathlib import Path

DB = Path("backend/almizane.db")
MIGRATIONS_DIR = Path("backend/migrations")

MIGRATIONS = [
    "002_zones_33_40_extension.sql",
    "002b_add_muhaddithin_columns.sql",
    "003_seed_muhaddithin_complete.sql",
]

def apply_migration(conn, migration_file):
    """Applique une migration SQL"""
    print(f"\n>> Application de {migration_file}...")
    
    migration_path = MIGRATIONS_DIR / migration_file
    
    if not migration_path.exists():
        print(f"[ERREUR] Fichier introuvable : {migration_path}")
        return False
    
    try:
        with open(migration_path, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # Exécuter le SQL
        conn.executescript(sql)
        conn.commit()
        
        print(f"[OK] Migration appliquee avec succes")
        return True
        
    except Exception as e:
        print(f"[ERREUR] Erreur lors de l'application : {e}")
        conn.rollback()
        return False

def main():
    print("="*70)
    print("APPLICATION DES MIGRATIONS v2 - VERIFICATEUR MIZAN")
    print("="*70)
    
    if not DB.exists():
        print(f"\n[ERREUR] Base de donnees introuvable : {DB}")
        print("Veuillez d'abord creer la base avec init_db.py")
        return
    
    conn = sqlite3.connect(DB)
    
    success_count = 0
    
    for migration in MIGRATIONS:
        if apply_migration(conn, migration):
            success_count += 1
    
    conn.close()
    
    print(f"\n{'='*70}")
    print(f"[OK] {success_count}/{len(MIGRATIONS)} migrations appliquees avec succes")
    
    if success_count == len(MIGRATIONS):
        print("\n[SUCCESS] Toutes les migrations v2 ont ete appliquees !")
        print("\nProchaines etapes :")
        print("1. Verifier les nouvelles tables avec check_almizane_schema.py")
        print("2. Lancer les harvesters pour peupler les zones 33-40")
        print("3. Executer consolidate_grades_v2.py pour appliquer les nouvelles regles")
    else:
        print("\n[ATTENTION] Certaines migrations ont echoue. Verifiez les erreurs ci-dessus.")
    
    print("="*70)

if __name__ == "__main__":
    main()