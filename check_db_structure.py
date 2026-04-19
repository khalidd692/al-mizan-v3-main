#!/usr/bin/env python3
"""Script pour analyser la structure de la base de données."""

import sqlite3
import sys

def main():
    db_path = "backend/almizane.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Statistiques générales
        cursor.execute("SELECT COUNT(*) FROM hadiths")
        total = cursor.fetchone()[0]
        print(f"📊 Total hadiths: {total:,}")
        
        cursor.execute("SELECT COUNT(DISTINCT collection) FROM hadiths")
        collections = cursor.fetchone()[0]
        print(f"📚 Collections distinctes: {collections}")
        
        # Top 10 collections
        print("\n🔝 Top 10 collections:")
        cursor.execute("""
            SELECT collection, COUNT(*) as count 
            FROM hadiths 
            GROUP BY collection 
            ORDER BY count DESC 
            LIMIT 10
        """)
        for row in cursor.fetchall():
            print(f"  • {row[0]}: {row[1]:,}")
        
        # Catégories
        print("\n📋 Répartition par catégorie:")
        cursor.execute("""
            SELECT categorie, COUNT(*) as count 
            FROM hadiths 
            GROUP BY categorie 
            ORDER BY count DESC
        """)
        for row in cursor.fetchall():
            print(f"  • {row[0]}: {row[1]:,}")
        
        # Grades
        print("\n⭐ Répartition par grade:")
        cursor.execute("""
            SELECT grade_final, COUNT(*) as count 
            FROM hadiths 
            GROUP BY grade_final 
            ORDER BY count DESC 
            LIMIT 10
        """)
        for row in cursor.fetchall():
            print(f"  • {row[0]}: {row[1]:,}")
        
        # Sources API
        print("\n🌐 Sources API:")
        cursor.execute("""
            SELECT source_api, COUNT(*) as count 
            FROM hadiths 
            GROUP BY source_api 
            ORDER BY count DESC
        """)
        for row in cursor.fetchall():
            source = row[0] if row[0] else "Non spécifié"
            print(f"  • {source}: {row[1]:,}")
        
        # Schéma de la table
        print("\n🗂️  Schéma de la table 'hadiths':")
        cursor.execute("PRAGMA table_info(hadiths)")
        for row in cursor.fetchall():
            print(f"  • {row[1]} ({row[2]})")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Erreur SQLite: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()