#!/usr/bin/env python3
"""
Import intelligent - Évite les doublons
N'importe que les collections manquantes
"""

import sqlite3
import requests
import time
from datetime import datetime

# Configuration
DB_PATH = "backend/almizane.db"
API_BASE = "https://api.hadith.gading.dev"

# Collections disponibles dans l'API
AVAILABLE_COLLECTIONS = {
    'bukhari': 'Sahih al-Bukhari',
    'muslim': 'Sahih Muslim',
    'abudawud': 'Sunan Abu Dawud',
    'tirmidzi': "Jami' at-Tirmidhi",
    'nasai': "Sunan an-Nasa'i",
    'ibnmajah': 'Sunan Ibn Majah',
    'malik': 'Muwatta Malik',
    'ahmad': 'Musnad Ahmad',
    'darimi': 'Sunan ad-Darimi'
}

def get_existing_collections():
    """Récupère les collections déjà présentes dans la base"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT collection, COUNT(*) as count
        FROM hadiths
        GROUP BY collection
        ORDER BY count DESC
    """)
    
    existing = {}
    for row in cursor.fetchall():
        collection_name = row[0].lower() if row[0] else ''
        count = row[1]
        existing[collection_name] = count
    
    conn.close()
    return existing

def get_api_collection_info(collection_id):
    """Récupère les infos d'une collection depuis l'API"""
    try:
        url = f"{API_BASE}/books/{collection_id}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200 and 'data' in data:
                return data['data']
        return None
    except Exception as e:
        print(f"   ❌ Erreur API pour {collection_id}: {e}")
        return None

def analyze_collections():
    """Analyse les collections existantes vs disponibles"""
    print("=" * 70)
    print("🔍 ANALYSE DES COLLECTIONS")
    print("=" * 70)
    
    existing = get_existing_collections()
    
    print("\n📊 Collections existantes dans la base:")
    for name, count in existing.items():
        print(f"   ✅ {name}: {count:,} hadiths")
    
    print(f"\n   Total: {sum(existing.values()):,} hadiths")
    
    print("\n" + "=" * 70)
    print("🆕 Collections disponibles dans l'API:")
    print("=" * 70)
    
    to_import = []
    already_have = []
    
    for api_id, full_name in AVAILABLE_COLLECTIONS.items():
        print(f"\n📚 {full_name} ({api_id})")
        
        # Vérifier si déjà présent
        has_collection = False
        for existing_name in existing.keys():
            if api_id in existing_name or existing_name in api_id.lower():
                has_collection = True
                already_have.append({
                    'api_id': api_id,
                    'name': full_name,
                    'existing_name': existing_name,
                    'count': existing[existing_name]
                })
                print(f"   ✅ Déjà présent: {existing[existing_name]:,} hadiths")
                break
        
        if not has_collection:
            # Récupérer les infos de l'API
            info = get_api_collection_info(api_id)
            if info:
                available_count = info.get('available', 0)
                to_import.append({
                    'api_id': api_id,
                    'name': full_name,
                    'count': available_count
                })
                print(f"   🆕 À importer: {available_count:,} hadiths disponibles")
            else:
                print(f"   ⚠️  Impossible de récupérer les infos")
            
            time.sleep(0.5)  # Rate limiting
    
    return to_import, already_have

def import_collection(api_id, collection_name, total_hadiths):
    """Importe une collection complète"""
    print(f"\n{'=' * 70}")
    print(f"📥 IMPORT: {collection_name}")
    print(f"{'=' * 70}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    imported = 0
    errors = 0
    
    # Importer par lots de 50
    batch_size = 50
    for start in range(1, total_hadiths + 1, batch_size):
        end = min(start + batch_size - 1, total_hadiths)
        
        try:
            url = f"{API_BASE}/books/{api_id}?range={start}-{end}"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('code') == 200 and 'data' in data:
                    hadiths = data['data'].get('hadiths', [])
                    
                    for hadith in hadiths:
                        try:
                            cursor.execute("""
                                INSERT INTO hadiths (
                                    collection,
                                    numero_hadith,
                                    livre,
                                    matn_ar,
                                    matn_fr,
                                    grade_final,
                                    source_api
                                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                collection_name,
                                str(hadith.get('number', start + imported)),
                                hadith.get('id', '').split(':')[0] if ':' in str(hadith.get('id', '')) else '1',
                                hadith.get('arab', ''),
                                hadith.get('id', ''),  # ID comme référence
                                'Unknown',
                                'hadith_gading'
                            ))
                            imported += 1
                        except sqlite3.IntegrityError:
                            # Doublon détecté, on ignore
                            pass
                        except Exception as e:
                            errors += 1
                    
                    conn.commit()
                    
                    # Afficher progression
                    progress = (end / total_hadiths) * 100
                    print(f"   [{progress:5.1f}%] {imported:,}/{total_hadiths:,} hadiths importés", end='\r')
            
            time.sleep(0.3)  # Rate limiting
            
        except Exception as e:
            print(f"\n   ⚠️  Erreur lot {start}-{end}: {e}")
            errors += 1
            time.sleep(1)
    
    conn.close()
    
    print(f"\n   ✅ Import terminé: {imported:,} hadiths")
    if errors > 0:
        print(f"   ⚠️  Erreurs: {errors}")
    
    return imported, errors

def main():
    print("\n" + "=" * 70)
    print("🚀 IMPORT INTELLIGENT - SANS DOUBLONS")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Analyser les collections
    to_import, already_have = analyze_collections()
    
    # Résumé
    print("\n" + "=" * 70)
    print("📋 RÉSUMÉ")
    print("=" * 70)
    
    print(f"\n✅ Collections déjà présentes: {len(already_have)}")
    for item in already_have:
        print(f"   • {item['name']}: {item['count']:,} hadiths")
    
    print(f"\n🆕 Collections à importer: {len(to_import)}")
    total_to_import = 0
    for item in to_import:
        print(f"   • {item['name']}: {item['count']:,} hadiths")
        total_to_import += item['count']
    
    if len(to_import) == 0:
        print("\n✅ Aucune nouvelle collection à importer !")
        print("   Votre base de données est déjà complète.")
        return
    
    print(f"\n📊 Total à importer: {total_to_import:,} hadiths")
    print(f"⏱️  Temps estimé: {(total_to_import / 1000):.1f} minutes")
    
    # Demander confirmation
    print("\n" + "=" * 70)
    response = input("Voulez-vous continuer l'import ? (oui/non): ").lower()
    
    if response not in ['oui', 'o', 'yes', 'y']:
        print("\n❌ Import annulé")
        return
    
    # Importer les collections manquantes
    print("\n" + "=" * 70)
    print("🚀 DÉBUT DE L'IMPORT")
    print("=" * 70)
    
    total_imported = 0
    total_errors = 0
    
    for item in to_import:
        imported, errors = import_collection(
            item['api_id'],
            item['name'],
            item['count']
        )
        total_imported += imported
        total_errors += errors
        time.sleep(1)
    
    # Rapport final
    print("\n" + "=" * 70)
    print("✅ IMPORT TERMINÉ")
    print("=" * 70)
    print(f"\n📊 Statistiques:")
    print(f"   • Collections importées: {len(to_import)}")
    print(f"   • Hadiths importés: {total_imported:,}")
    print(f"   • Erreurs: {total_errors}")
    
    # Vérifier le total final
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM hadiths")
    final_count = cursor.fetchone()[0]
    conn.close()
    
    print(f"\n📈 Total dans la base: {final_count:,} hadiths")
    print(f"\n✅ Mission accomplie !")

if __name__ == "__main__":
    main()