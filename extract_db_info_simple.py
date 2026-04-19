#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'extraction complète des informations de la base de données
Version simplifiée sans print Unicode
"""

import sqlite3
import json
import sys
from pathlib import Path

def connect_db(db_path):
    """Connexion à la base de données"""
    return sqlite3.connect(db_path)

def extract_all_info(conn):
    """Extrait toutes les informations nécessaires"""
    cursor = conn.cursor()
    info = {}
    
    # 1. Schéma complet
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' ORDER BY name")
    info['schema'] = [sql[0] for sql in cursor.fetchall() if sql[0]]
    
    # 2. Liste des tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    info['tables'] = [row[0] for row in cursor.fetchall()]
    
    # 3. Stats générales
    cursor.execute("SELECT COUNT(*) FROM hadiths")
    info['total_hadiths'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT collection) FROM hadiths")
    info['total_collections'] = cursor.fetchone()[0]
    
    # 4. Grades distincts
    cursor.execute("SELECT DISTINCT grade_final FROM hadiths WHERE grade_final IS NOT NULL ORDER BY grade_final")
    info['grades'] = [g[0] for g in cursor.fetchall()]
    
    # 5. Répartition par grade
    cursor.execute("SELECT grade_final, COUNT(*) FROM hadiths GROUP BY grade_final ORDER BY COUNT(*) DESC")
    info['grades_distribution'] = cursor.fetchall()
    
    # 6. Collections présentes
    cursor.execute("SELECT collection, COUNT(*) FROM hadiths GROUP BY collection ORDER BY COUNT(*) DESC")
    info['collections'] = cursor.fetchall()
    
    # 7. Exemples de hadiths (3 premiers)
    cursor.execute("""
        SELECT id, collection, numero_hadith, matn_ar, grade_final, 
               source_url, source_api, inserted_at
        FROM hadiths 
        LIMIT 3
    """)
    info['sample_hadiths'] = []
    for row in cursor.fetchall():
        info['sample_hadiths'].append({
            'id': row[0],
            'collection': row[1],
            'numero': row[2],
            'matn_ar': row[3][:100] + "..." if row[3] and len(row[3]) > 100 else row[3],
            'grade': row[4],
            'source_url': row[5],
            'source_api': row[6],
            'inserted_at': row[7]
        })
    
    return info

def main():
    # Chemins des bases de données
    mizan_path = Path("backend/mizan.db")
    almizane_path = Path("backend/almizane.db")
    
    output = {
        "timestamp": "2026-04-19T15:26:00+02:00",
        "databases": {}
    }
    
    # Vérifier quelle base existe
    for db_name, db_path in [("mizan", mizan_path), ("almizane", almizane_path)]:
        if db_path.exists():
            sys.stdout.write(f"Extraction de {db_name}...\n")
            conn = connect_db(db_path)
            output['databases'][db_name] = extract_all_info(conn)
            conn.close()
            sys.stdout.write(f"OK - {output['databases'][db_name]['total_hadiths']} hadiths\n")
    
    # Sauvegarder le rapport JSON
    output_file = Path("output/DB_EXTRACTION_COMPLETE.json")
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    sys.stdout.write(f"\nRapport JSON: {output_file}\n")
    
    # Créer le rapport markdown
    md_output = Path("output/DB_EXTRACTION_COMPLETE.md")
    with open(md_output, 'w', encoding='utf-8') as f:
        f.write("# EXTRACTION COMPLÈTE DES BASES DE DONNÉES\n\n")
        f.write(f"**Date**: {output['timestamp']}\n\n")
        
        for db_name, db_info in output['databases'].items():
            f.write(f"## BASE: {db_name.upper()}\n\n")
            
            f.write(f"### Statistiques\n\n")
            f.write(f"- **Total hadiths**: {db_info['total_hadiths']}\n")
            f.write(f"- **Collections**: {db_info['total_collections']}\n")
            f.write(f"- **Tables**: {len(db_info['tables'])}\n\n")
            
            f.write(f"### Tables présentes\n\n")
            for table in db_info['tables']:
                f.write(f"- `{table}`\n")
            f.write("\n")
            
            f.write(f"### Grades distincts ({len(db_info['grades'])})\n\n")
            for grade in db_info['grades']:
                f.write(f"- `{grade}`\n")
            f.write("\n")
            
            f.write(f"### Répartition par grade\n\n")
            for grade, count in db_info['grades_distribution']:
                f.write(f"- **{grade}**: {count} hadiths\n")
            f.write("\n")
            
            f.write(f"### Collections présentes\n\n")
            for collection, count in db_info['collections']:
                f.write(f"- **{collection}**: {count} hadiths\n")
            f.write("\n")
            
            f.write(f"### Exemples de hadiths\n\n")
            for i, hadith in enumerate(db_info['sample_hadiths'], 1):
                f.write(f"#### Hadith {i}\n\n")
                f.write(f"- **ID**: {hadith['id']}\n")
                f.write(f"- **Collection**: {hadith['collection']}\n")
                f.write(f"- **Numéro**: {hadith['numero']}\n")
                f.write(f"- **Grade**: {hadith['grade']}\n")
                f.write(f"- **Source API**: {hadith['source_api']}\n")
                f.write(f"- **Matn (extrait)**: {hadith['matn_ar']}\n\n")
            
            f.write(f"### Schéma complet\n\n")
            f.write("```sql\n")
            for sql in db_info['schema']:
                f.write(f"{sql};\n\n")
            f.write("```\n\n")
    
    sys.stdout.write(f"Rapport Markdown: {md_output}\n")
    sys.stdout.write("\nExtraction terminee!\n")

if __name__ == "__main__":
    main()