#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyse complète de la chaîne Naqil
Vérifie la connexion salafi_authorities.json ↔ muhaddithin ↔ verdicts
"""

import sqlite3
import json
import sys
import io

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def analyser_echantillon_sans_grade():
    """Analyse 20 hadiths sans grade pour voir leur provenance"""
    conn = sqlite3.connect('backend/mizan.db')
    cursor = conn.cursor()
    
    print("=" * 80)
    print("ÉCHANTILLON DE 20 HADITHS SANS GRADE")
    print("=" * 80)
    
    cursor.execute("""
        SELECT id, collection, numero_hadith, source_api, 
               substr(matn_ar, 1, 50) as matn_preview
        FROM hadiths 
        WHERE grade_final IS NULL OR grade_final = ''
        LIMIT 20
    """)
    
    hadiths = cursor.fetchall()
    
    # Compter par source
    sources = {}
    collections = {}
    
    for h in hadiths:
        id_h, coll, num, src, matn = h
        sources[src] = sources.get(src, 0) + 1
        collections[coll] = collections.get(coll, 0) + 1
        print(f"\nID: {id_h}")
        print(f"  Collection: {coll}")
        print(f"  Numéro: {num}")
        print(f"  Source API: {src}")
        print(f"  Matn: [texte arabe]")
    
    print("\n" + "=" * 80)
    print("RÉPARTITION PAR SOURCE_API")
    print("=" * 80)
    for src, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        print(f"{src}: {count} hadiths")
    
    print("\n" + "=" * 80)
    print("RÉPARTITION PAR COLLECTION")
    print("=" * 80)
    for coll, count in sorted(collections.items(), key=lambda x: x[1], reverse=True):
        print(f"{coll}: {count} hadiths")
    
    conn.close()

def verifier_table_muhaddithin():
    """Vérifie si la table muhaddithin existe et contient des données"""
    conn = sqlite3.connect('backend/mizan.db')
    cursor = conn.cursor()
    
    print("\n" + "=" * 80)
    print("VÉRIFICATION TABLE MUHADDITHIN")
    print("=" * 80)
    
    # Vérifier si la table existe
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='muhaddithin'
    """)
    
    if not cursor.fetchone():
        print("❌ La table 'muhaddithin' N'EXISTE PAS dans la base")
        conn.close()
        return False
    
    print("✅ La table 'muhaddithin' existe")
    
    # Compter les entrées
    cursor.execute("SELECT COUNT(*) FROM muhaddithin")
    count = cursor.fetchone()[0]
    print(f"\nNombre d'entrées: {count}")
    
    if count == 0:
        print("❌ La table est VIDE - aucun muhaddith enregistré")
        conn.close()
        return False
    
    # Afficher les entrées
    cursor.execute("""
        SELECT id, nom_ar, nom_latin, naissance, deces, tier, trust_level
        FROM muhaddithin
        LIMIT 10
    """)
    
    print("\n10 premières entrées:")
    for row in cursor.fetchall():
        print(f"  ID {row[0]}: {row[1]} ({row[2]}) - {row[3]}-{row[4]} - Tier {row[5]}, Trust: {row[6]}")
    
    conn.close()
    return True

def verifier_connexion_json_db():
    """Vérifie si les 29 autorités du JSON sont dans la table muhaddithin"""
    
    # Charger le JSON
    with open('backend/data/salafi_authorities.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extraire toutes les autorités
    autorites_json = []
    for category in data['categories'].values():
        for auth in category['authorities']:
            autorites_json.append({
                'nom_ar': auth['name_ar'],
                'nom_latin': auth['name_latin'],
                'tier': auth['tier'],
                'trust': auth['trust_level']
            })
    
    print("\n" + "=" * 80)
    print("CONNEXION salafi_authorities.json ↔ muhaddithin")
    print("=" * 80)
    print(f"\nNombre d'autorités dans le JSON: {len(autorites_json)}")
    
    # Vérifier dans la DB
    conn = sqlite3.connect('backend/mizan.db')
    cursor = conn.cursor()
    
    # Vérifier si la table existe
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='muhaddithin'
    """)
    
    if not cursor.fetchone():
        print("\n❌ ÉCHEC: La table 'muhaddithin' n'existe pas")
        print("   → Les 29 autorités du JSON ne peuvent pas être liées")
        conn.close()
        return
    
    cursor.execute("SELECT COUNT(*) FROM muhaddithin")
    count_db = cursor.fetchone()[0]
    print(f"Nombre d'entrées dans muhaddithin: {count_db}")
    
    if count_db == 0:
        print("\n❌ ÉCHEC: La table 'muhaddithin' est VIDE")
        print("   → Les 29 autorités du JSON ne sont PAS dans la base")
        print("   → La chaîne Naqil est CASSÉE")
        conn.close()
        return
    
    # Vérifier correspondance
    matches = 0
    missing = []
    
    for auth in autorites_json:
        cursor.execute("""
            SELECT id, tier, trust_level 
            FROM muhaddithin 
            WHERE nom_ar = ? OR nom_latin = ?
        """, (auth['nom_ar'], auth['nom_latin']))
        
        result = cursor.fetchone()
        if result:
            matches += 1
            db_id, db_tier, db_trust = result
            if db_tier != auth['tier'] or db_trust != auth['trust']:
                print(f"⚠️  {auth['nom_latin']}: Trouvé mais données différentes")
                print(f"    JSON: tier={auth['tier']}, trust={auth['trust']}")
                print(f"    DB:   tier={db_tier}, trust={db_trust}")
        else:
            missing.append(auth['nom_latin'])
    
    print(f"\n✅ Autorités trouvées: {matches}/{len(autorites_json)}")
    
    if missing:
        print(f"\n❌ Autorités MANQUANTES ({len(missing)}):")
        for name in missing[:10]:
            print(f"   - {name}")
        if len(missing) > 10:
            print(f"   ... et {len(missing) - 10} autres")
    
    conn.close()

def verifier_table_verdicts():
    """Vérifie la table verdicts et sa liaison avec muhaddithin"""
    conn = sqlite3.connect('backend/mizan.db')
    cursor = conn.cursor()
    
    print("\n" + "=" * 80)
    print("VÉRIFICATION TABLE VERDICTS")
    print("=" * 80)
    
    # Vérifier si la table existe
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='verdicts'
    """)
    
    if not cursor.fetchone():
        print("❌ La table 'verdicts' N'EXISTE PAS")
        conn.close()
        return
    
    print("✅ La table 'verdicts' existe")
    
    # Compter les entrées
    cursor.execute("SELECT COUNT(*) FROM verdicts")
    count = cursor.fetchone()[0]
    print(f"\nNombre de verdicts: {count}")
    
    if count == 0:
        print("❌ La table est VIDE - aucun verdict enregistré")
        print("   → Aucune traçabilité Naqil disponible")
        conn.close()
        return
    
    # Vérifier les liaisons
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT hadith_id) as hadiths_avec_verdict,
            COUNT(DISTINCT muhaddith_id) as muhaddithin_actifs
        FROM verdicts
    """)
    
    total, hadiths, muhaddithin = cursor.fetchone()
    print(f"\nStatistiques:")
    print(f"  - Total verdicts: {total}")
    print(f"  - Hadiths avec verdict: {hadiths}")
    print(f"  - Muhaddithin actifs: {muhaddithin}")
    
    # Exemples de verdicts
    cursor.execute("""
        SELECT v.id, v.hadith_id, v.muhaddith_id, v.verdict, 
               m.nom_latin, h.collection
        FROM verdicts v
        LEFT JOIN muhaddithin m ON v.muhaddith_id = m.id
        LEFT JOIN hadiths h ON v.hadith_id = h.id
        LIMIT 5
    """)
    
    print("\n5 premiers verdicts:")
    for row in cursor.fetchall():
        v_id, h_id, m_id, verdict, m_nom, coll = row
        if m_nom:
            print(f"  Verdict #{v_id}: Hadith #{h_id} ({coll}) → {verdict} par {m_nom}")
        else:
            print(f"  Verdict #{v_id}: Hadith #{h_id} → {verdict} par muhaddith_id={m_id} (NON TROUVÉ)")
    
    conn.close()

def diagnostic_complet():
    """Diagnostic complet de la chaîne Naqil"""
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLET DE LA CHAÎNE NAQIL")
    print("=" * 80)
    
    # 1. Échantillon hadiths sans grade
    analyser_echantillon_sans_grade()
    
    # 2. Table muhaddithin
    table_ok = verifier_table_muhaddithin()
    
    # 3. Connexion JSON ↔ DB
    verifier_connexion_json_db()
    
    # 4. Table verdicts
    verifier_table_verdicts()
    
    # Conclusion
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    
    conn = sqlite3.connect('backend/mizan.db')
    cursor = conn.cursor()
    
    # Vérifier tables
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name IN ('muhaddithin', 'verdicts')
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    if 'muhaddithin' not in tables:
        print("\n🔴 CHAÎNE NAQIL CASSÉE: Table 'muhaddithin' manquante")
    elif 'verdicts' not in tables:
        print("\n🔴 CHAÎNE NAQIL CASSÉE: Table 'verdicts' manquante")
    else:
        cursor.execute("SELECT COUNT(*) FROM muhaddithin")
        m_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM verdicts")
        v_count = cursor.fetchone()[0]
        
        if m_count == 0:
            print("\n🔴 CHAÎNE NAQIL CASSÉE: Table 'muhaddithin' vide")
            print("   → Les 29 autorités de salafi_authorities.json ne sont PAS dans la DB")
        elif v_count == 0:
            print("\n🟡 CHAÎNE NAQIL INCOMPLÈTE: Table 'verdicts' vide")
            print("   → Les muhaddithin existent mais aucun verdict n'est enregistré")
        else:
            print("\n🟢 CHAÎNE NAQIL PARTIELLEMENT FONCTIONNELLE")
            print(f"   → {m_count} muhaddithin enregistrés")
            print(f"   → {v_count} verdicts enregistrés")
            print("   → Vérifier la qualité des liaisons ci-dessus")
    
    conn.close()

if __name__ == "__main__":
    diagnostic_complet()