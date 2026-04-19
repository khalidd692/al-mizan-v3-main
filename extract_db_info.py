#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'extraction complète des informations de la base de données
pour audit et vérification du système Naqil
"""

import sqlite3
import json
from pathlib import Path

def connect_db(db_path):
    """Connexion à la base de données"""
    return sqlite3.connect(db_path)

def extract_schema(conn):
    """Extrait le schéma complet de la base"""
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' ORDER BY name")
    return cursor.fetchall()

def extract_sample_hadiths(conn):
    """Extrait 3 exemples de hadiths avec leurs verdicts"""
    cursor = conn.cursor()
    query = """
    SELECT 
        h.id,
        h.collection,
        h.numero_hadith,
        h.matn_ar,
        h.grade_final,
        h.source_url,
        h.source_api,
        h.inserted_at
    FROM hadiths h
    LIMIT 3
    """
    cursor.execute(query)
    return cursor.fetchall()

def extract_grades(conn):
    """Extrait les valeurs distinctes des grades"""
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT grade_final FROM hadiths WHERE grade_final IS NOT NULL ORDER BY grade_final")
    return cursor.fetchall()

def extract_db_stats(conn):
    """Statistiques générales de la base"""
    cursor = conn.cursor()
    stats = {}
    
    # Nombre total de hadiths
    cursor.execute("SELECT COUNT(*) FROM hadiths")
    stats['total_hadiths'] = cursor.fetchone()[0]
    
    # Nombre de collections distinctes
    cursor.execute("SELECT COUNT(DISTINCT collection) FROM hadiths")
    stats['total_collections'] = cursor.fetchone()[0]
    
    # Répartition par grade
    cursor.execute("SELECT grade_final, COUNT(*) FROM hadiths GROUP BY grade_final ORDER BY COUNT(*) DESC")
    stats['grades_distribution'] = cursor.fetchall()
    
    # Collections présentes
    cursor.execute("SELECT collection, COUNT(*) FROM hadiths GROUP BY collection ORDER BY COUNT(*) DESC")
    stats['collections'] = cursor.fetchall()
    
    return stats

def check_tables_exist(conn):
    """Vérifie quelles tables existent"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return [row[0] for row in cursor.fetchall()]

def main():
    # Chemins des bases de données
    mizan_path = Path("backend/mizan.db")
    almizane_path = Path("backend/almizane.db")
    
    output = {
        "timestamp": "2026-04-19T15:25:00+02:00",
        "databases": {}
    }
    
    # Vérifier quelle base existe
    for db_name, db_path in [("mizan", mizan_path), ("almizane", almizane_path)]:
        if db_path.exists():
            print(f"\n{'='*80}")
            print(f"ANALYSE DE LA BASE: {db_name.upper()}")
            print(f"{'='*80}\n")
            
            conn = connect_db(db_path)
            db_info = {}
            
            # 1. SCHÉMA
            print("1. EXTRACTION DU SCHÉMA...")
            schema = extract_schema(conn)
            db_info['schema'] = [sql[0] for sql in schema if sql[0]]
            print(f"   OK {len(db_info['schema'])} tables trouvees")
            
            # 2. TABLES EXISTANTES
            print("\n2. LISTE DES TABLES...")
            tables = check_tables_exist(conn)
            db_info['tables'] = tables
            print(f"   OK Tables: {', '.join(tables)}")
            
            # 3. STATISTIQUES
            print("\n3. STATISTIQUES GÉNÉRALES...")
            stats = extract_db_stats(conn)
            db_info['stats'] = stats
            print(f"   OK Total hadiths: {stats['total_hadiths']}")
            print(f"   OK Collections: {stats['total_collections']}")
            
            # 4. GRADES DISTINCTS
            print("\n4. GRADES DISTINCTS...")
            grades = extract_grades(conn)
            db_info['grades'] = [g[0] for g in grades]
            print(f"   OK Grades trouves: {len(db_info['grades'])}")
            for grade in db_info['grades']:
                print(f"      - {grade}")
            
            # 5. EXEMPLES DE HADITHS
            print("\n5. EXTRACTION D'EXEMPLES DE HADITHS...")
            samples = extract_sample_hadiths(conn)
            db_info['sample_hadiths'] = []
            for i, sample in enumerate(samples, 1):
                hadith_info = {
                    'id': sample[0],
                    'collection': sample[1],
                    'numero': sample[2],
                    'matn_ar': sample[3][:100] + "..." if sample[3] and len(sample[3]) > 100 else sample[3],
                    'grade': sample[4],
                    'source_url': sample[5],
                    'source_api': sample[6],
                    'inserted_at': sample[7]
                }
                db_info['sample_hadiths'].append(hadith_info)
                print(f"   OK Hadith {i}: {sample[1]} #{sample[2]} - Grade: {sample[4]}")
            
            conn.close()
            output['databases'][db_name] = db_info
    
    # Sauvegarder le rapport
    output_file = Path("output/DB_EXTRACTION_COMPLETE.json")
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*80}")
    print(f"RAPPORT SAUVEGARDÉ: {output_file}")
    print(f"{'='*80}\n")
    
    # Créer aussi un rapport markdown lisible
    md_output = Path("output/DB_EXTRACTION_COMPLETE.md")
    with open(md_output, 'w', encoding='utf-8') as f:
        f.write("# EXTRACTION COMPLÈTE DES BASES DE DONNÉES\n\n")
        f.write(f"**Date**: {output['timestamp']}\n\n")
        
        for db_name, db_info in output['databases'].items():
            f.write(f"## BASE: {db_name.upper()}\n\n")
            
            f.write(f"### Statistiques\n\n")
            f.write(f"- **Total hadiths**: {db_info['stats']['total_hadiths']}\n")
            f.write(f"- **Collections**: {db_info['stats']['total_collections']}\n\n")
            
            f.write(f"### Tables présentes\n\n")
            for table in db_info['tables']:
                f.write(f"- `{table}`\n")
            f.write("\n")
            
            f.write(f"### Grades distincts\n\n")
            for grade in db_info['grades']:
                f.write(f"- `{grade}`\n")
            f.write("\n")
            
            f.write(f"### Répartition par grade\n\n")
            for grade, count in db_info['stats']['grades_distribution']:
                f.write(f"- **{grade}**: {count} hadiths\n")
            f.write("\n")
            
            f.write(f"### Collections présentes\n\n")
            for collection, count in db_info['stats']['collections']:
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
    
    print(f"RAPPORT MARKDOWN: {md_output}\n")

if __name__ == "__main__":
    main()