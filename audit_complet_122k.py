#!/usr/bin/env python3
"""
AUDIT COMPLET - BASE 122K HADITHS
Analyse exhaustive de la base après import
"""

import sqlite3
import json
from collections import Counter
from datetime import datetime

def audit_complet():
    conn = sqlite3.connect('backend/almizane.db')
    cursor = conn.cursor()
    
    rapport = {
        'date_audit': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'statistiques_globales': {},
        'par_collection': {},
        'par_source': {},
        'qualite_donnees': {},
        'integrite': {},
        'exemples': {}
    }
    
    print("="*80)
    print("🔍 AUDIT COMPLET - BASE AL-MIZAN")
    print("="*80)
    print()
    
    # 1. STATISTIQUES GLOBALES
    print("📊 STATISTIQUES GLOBALES")
    print("-" * 80)
    
    total = cursor.execute("SELECT COUNT(*) FROM hadiths").fetchone()[0]
    rapport['statistiques_globales']['total_hadiths'] = total
    print(f"Total hadiths: {total:,}")
    
    # Avec texte arabe
    avec_arabe = cursor.execute("SELECT COUNT(*) FROM hadiths WHERE matn_ar IS NOT NULL AND matn_ar != ''").fetchone()[0]
    rapport['statistiques_globales']['avec_texte_arabe'] = avec_arabe
    print(f"Avec texte arabe: {avec_arabe:,} ({avec_arabe/total*100:.1f}%)")
    
    # Avec traduction française
    avec_fr = cursor.execute("SELECT COUNT(*) FROM hadiths WHERE matn_fr IS NOT NULL AND matn_fr != ''").fetchone()[0]
    rapport['statistiques_globales']['avec_traduction_fr'] = avec_fr
    print(f"Avec traduction FR: {avec_fr:,} ({avec_fr/total*100:.1f}%)")
    
    # Avec grade
    avec_grade = cursor.execute("SELECT COUNT(*) FROM hadiths WHERE grade_final IS NOT NULL AND grade_final != ''").fetchone()[0]
    rapport['statistiques_globales']['avec_grade'] = avec_grade
    print(f"Avec grade: {avec_grade:,} ({avec_grade/total*100:.1f}%)")
    
    # Avec isnad
    avec_isnad = cursor.execute("SELECT COUNT(*) FROM hadiths WHERE isnad_brut IS NOT NULL AND isnad_brut != ''").fetchone()[0]
    rapport['statistiques_globales']['avec_isnad'] = avec_isnad
    print(f"Avec isnad: {avec_isnad:,} ({avec_isnad/total*100:.1f}%)")
    
    print()
    
    # 2. PAR COLLECTION
    print("📚 RÉPARTITION PAR COLLECTION")
    print("-" * 80)
    
    collections = cursor.execute("""
        SELECT collection, COUNT(*) as count 
        FROM hadiths 
        GROUP BY collection 
        ORDER BY count DESC
    """).fetchall()
    
    rapport['par_collection'] = {}
    for i, (coll, count) in enumerate(collections, 1):
        pct = count/total*100
        rapport['par_collection'][coll] = {
            'count': count,
            'pourcentage': round(pct, 2)
        }
        print(f"{i:2d}. {coll:20s} : {count:>7,} hadiths ({pct:5.2f}%)")
    
    print()
    
    # 3. PAR SOURCE API
    print("🌐 RÉPARTITION PAR SOURCE")
    print("-" * 80)
    
    sources = cursor.execute("""
        SELECT source_api, COUNT(*) as count 
        FROM hadiths 
        WHERE source_api IS NOT NULL
        GROUP BY source_api 
        ORDER BY count DESC
    """).fetchall()
    
    rapport['par_source'] = {}
    for source, count in sources:
        pct = count/total*100
        rapport['par_source'][source] = {
            'count': count,
            'pourcentage': round(pct, 2)
        }
        print(f"• {source:25s} : {count:>7,} hadiths ({pct:5.2f}%)")
    
    print()
    
    # 4. QUALITÉ DES DONNÉES
    print("✅ QUALITÉ DES DONNÉES")
    print("-" * 80)
    
    # Longueur moyenne texte arabe
    avg_len = cursor.execute("""
        SELECT AVG(LENGTH(matn_ar)) 
        FROM hadiths 
        WHERE matn_ar IS NOT NULL
    """).fetchone()[0]
    rapport['qualite_donnees']['longueur_moyenne_arabe'] = round(avg_len, 0) if avg_len else 0
    print(f"Longueur moyenne texte arabe: {avg_len:.0f} caractères")
    
    # Hadiths courts (< 50 car)
    courts = cursor.execute("""
        SELECT COUNT(*) 
        FROM hadiths 
        WHERE LENGTH(matn_ar) < 50
    """).fetchone()[0]
    rapport['qualite_donnees']['hadiths_courts'] = courts
    print(f"Hadiths courts (< 50 car): {courts:,}")
    
    # Hadiths longs (> 1000 car)
    longs = cursor.execute("""
        SELECT COUNT(*) 
        FROM hadiths 
        WHERE LENGTH(matn_ar) > 1000
    """).fetchone()[0]
    rapport['qualite_donnees']['hadiths_longs'] = longs
    print(f"Hadiths longs (> 1000 car): {longs:,}")
    
    print()
    
    # 5. INTÉGRITÉ
    print("🔒 INTÉGRITÉ")
    print("-" * 80)
    
    # Hash uniques
    hash_uniques = cursor.execute("SELECT COUNT(DISTINCT sha256) FROM hadiths WHERE sha256 IS NOT NULL").fetchone()[0]
    rapport['integrite']['hash_uniques'] = hash_uniques
    print(f"Hash SHA256 uniques: {hash_uniques:,}")
    
    # Doublons potentiels
    doublons = total - hash_uniques
    rapport['integrite']['doublons_potentiels'] = doublons
    print(f"Doublons potentiels: {doublons:,}")
    
    # Entrées sans hash
    sans_hash = cursor.execute("SELECT COUNT(*) FROM hadiths WHERE sha256 IS NULL OR sha256 = ''").fetchone()[0]
    rapport['integrite']['sans_hash'] = sans_hash
    print(f"Entrées sans hash: {sans_hash:,}")
    
    print()
    
    # 6. TOP COLLECTIONS DÉTAILLÉES
    print("🏆 TOP 5 COLLECTIONS - DÉTAILS")
    print("-" * 80)
    
    for coll, count in collections[:5]:
        print(f"\n{coll.upper()} ({count:,} hadiths)")
        
        # Avec grade
        avec_grade_coll = cursor.execute("""
            SELECT COUNT(*) 
            FROM hadiths 
            WHERE collection = ? AND grade_final IS NOT NULL AND grade_final != ''
        """, (coll,)).fetchone()[0]
        print(f"  • Avec grade: {avec_grade_coll:,} ({avec_grade_coll/count*100:.1f}%)")
        
        # Avec traduction
        avec_fr_coll = cursor.execute("""
            SELECT COUNT(*) 
            FROM hadiths 
            WHERE collection = ? AND matn_fr IS NOT NULL AND matn_fr != ''
        """, (coll,)).fetchone()[0]
        print(f"  • Avec traduction FR: {avec_fr_coll:,} ({avec_fr_coll/count*100:.1f}%)")
        
        # Sources
        sources_coll = cursor.execute("""
            SELECT source_api, COUNT(*) 
            FROM hadiths 
            WHERE collection = ? AND source_api IS NOT NULL
            GROUP BY source_api
        """, (coll,)).fetchall()
        
        if sources_coll:
            print(f"  • Sources:")
            for src, cnt in sources_coll:
                print(f"    - {src}: {cnt:,}")
    
    print()
    
    # 7. EXEMPLES
    print("📝 EXEMPLES DE HADITHS")
    print("-" * 80)
    
    exemples = cursor.execute("""
        SELECT collection, matn_ar, grade_final, source_api
        FROM hadiths 
        WHERE matn_ar IS NOT NULL 
        LIMIT 3
    """).fetchall()
    
    rapport['exemples'] = []
    for i, (coll, texte, grade, source) in enumerate(exemples, 1):
        print(f"\nExemple {i} - {coll}")
        print(f"Source: {source}")
        print(f"Grade: {grade or 'N/A'}")
        print(f"Texte: {texte[:100]}...")
        
        rapport['exemples'].append({
            'collection': coll,
            'source': source,
            'grade': grade,
            'extrait': texte[:200]
        })
    
    print()
    
    # 8. RECOMMANDATIONS
    print("💡 RECOMMANDATIONS")
    print("-" * 80)
    
    recommandations = []
    
    if avec_fr < total * 0.5:
        rec = f"⚠️  Seulement {avec_fr/total*100:.1f}% des hadiths ont une traduction française"
        print(rec)
        recommandations.append(rec)
    
    if avec_grade < total * 0.3:
        rec = f"⚠️  Seulement {avec_grade/total*100:.1f}% des hadiths ont un grade d'authenticité"
        print(rec)
        recommandations.append(rec)
    
    if doublons > 0:
        rec = f"ℹ️  {doublons:,} doublons potentiels détectés (normal si imports multiples)"
        print(rec)
        recommandations.append(rec)
    
    if sans_hash > 0:
        rec = f"⚠️  {sans_hash:,} entrées sans hash SHA256 (risque de doublons)"
        print(rec)
        recommandations.append(rec)
    
    rapport['recommandations'] = recommandations
    
    print()
    print("="*80)
    print("✅ AUDIT TERMINÉ")
    print("="*80)
    
    conn.close()
    
    # Sauvegarder le rapport JSON
    with open('output/audit_122k.json', 'w', encoding='utf-8') as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 Rapport JSON sauvegardé: output/audit_122k.json")
    
    return rapport

if __name__ == '__main__':
    audit_complet()