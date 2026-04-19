"""
Applique la migration 001_verifier_schema_almizane.sql sur almizane.db
"""
import sqlite3
from pathlib import Path

DB = Path("backend/almizane.db")
MIGRATION = Path("backend/migrations/001_verifier_schema_almizane.sql")

def main():
    print(f"Application de la migration sur {DB}...")
    
    # Lire le fichier SQL
    sql = MIGRATION.read_text(encoding="utf-8")
    
    # Connexion et exécution
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL;")
    
    try:
        # Exécuter toutes les commandes SQL
        conn.executescript(sql)
        conn.commit()
        print("✅ Migration appliquée avec succès")
        
        # Vérifier les nouvelles tables
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cur.fetchall()]
        print(f"\nTables disponibles ({len(tables)}):")
        for t in tables:
            print(f"  - {t}")
            
        # Vérifier les nouvelles colonnes de hadiths
        print("\nNouvelles colonnes de 'hadiths':")
        cur.execute("PRAGMA table_info(hadiths)")
        for row in cur.fetchall():
            if row[1] in ['matn_ar_normalized', 'isnad_ar', 'sahabi_rawi', 
                          'type_rafa', 'type_tawatur', 'grade_synthese', 
                          'grade_confidence', 'verified_at']:
                print(f"  ✓ {row[1]}")
                
    except Exception as e:
        print(f"❌ Erreur lors de la migration : {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()