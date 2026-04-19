#!/usr/bin/env python3
"""
Détection et analyse des doublons dans la base de données
"""

import sqlite3
from collections import defaultdict

conn = sqlite3.connect("backend/almizane.db")
cursor = conn.cursor()

print("\n" + "="*80)
print("🔍 ANALYSE DES DOUBLONS DANS LA BASE DE DONNÉES")
print("="*80)

# 1. Vérifier les doublons par SHA256 (hash du contenu)
print("\n📊 1. DOUBLONS PAR HASH SHA256 (contenu identique)")
print("-" * 80)

cursor.execute("""
    SELECT sha256, COUNT(*) as count
    FROM hadiths
    GROUP BY sha256
    HAVING count > 1
    ORDER BY count DESC
    LIMIT 10
""")

doublons_hash = cursor.fetchall()
if doublons_hash:
    print(f"⚠️  {len(doublons_hash)} hashs avec doublons détectés")
    for hash_val, count in doublons_hash[:5]:
        print(f"   Hash {hash_val[:16]}... : {count} occurrences")
else:
    print("✅ Aucun doublon par hash détecté")

# 2. Vérifier les doublons par collection + numéro
print("\n📊 2. DOUBLONS PAR COLLECTION + NUMÉRO")
print("-" * 80)

cursor.execute("""
    SELECT collection, numero_hadith, COUNT(*) as count
    FROM hadiths
    WHERE numero_hadith IS NOT NULL
    GROUP BY collection, numero_hadith
    HAVING count > 1
    ORDER BY count DESC
    LIMIT 10
""")

doublons_numero = cursor.fetchall()
if doublons_numero:
    print(f"⚠️  {len(doublons_numero)} combinaisons collection+numéro en doublon")
    for collection, numero, count in doublons_numero[:5]:
        print(f"   {collection} #{numero} : {count} occurrences")
else:
    print("✅ Aucun doublon par collection+numéro détecté")

# 3. Analyser les collections en doublon (Bukhari/Sahih Bukhari, etc.)
print("\n📊 3. COLLECTIONS SIMILAIRES (possibles doublons)")
print("-" * 80)

cursor.execute("""
    SELECT collection, COUNT(*) as count, source_api
    FROM hadiths
    GROUP BY collection, source_api
    ORDER BY collection, count DESC
""")

collections_data = defaultdict(list)
for collection, count, source in cursor.fetchall():
    collections_data[collection.lower().replace(' ', '').replace('-', '')].append({
        'nom': collection,
        'count': count,
        'source': source or 'inconnu'
    })

print("\nCollections potentiellement en doublon :")
for key, items in collections_data.items():
    if len(items) > 1:
        print(f"\n🔸 Groupe '{key}' :")
        for item in items:
            print(f"   - {item['nom']:<25} : {item['count']:>6,} hadiths (source: {item['source']})")

# 4. Statistiques globales
print("\n" + "="*80)
print("📈 STATISTIQUES GLOBALES")
print("-" * 80)

cursor.execute("SELECT COUNT(*) FROM hadiths")
total = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(DISTINCT sha256) FROM hadiths")
unique_hash = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(DISTINCT collection || '-' || numero_hadith) 
    FROM hadiths 
    WHERE numero_hadith IS NOT NULL
""")
unique_collection_numero = cursor.fetchone()[0]

print(f"Total hadiths en base      : {total:>8,}")
print(f"Hadiths uniques (par hash) : {unique_hash:>8,}")
print(f"Doublons potentiels        : {total - unique_hash:>8,}")
print(f"Taux de duplication        : {((total - unique_hash) * 100 / total):.1f}%")

# 5. Recommandations
print("\n" + "="*80)
print("💡 RECOMMANDATIONS")
print("-" * 80)

if total - unique_hash > 0:
    print("""
⚠️  Des doublons ont été détectés. Causes possibles :
   1. Même recueil importé de sources différentes (ex: Bukhari + Sahih Bukhari)
   2. Hadiths identiques dans différents recueils (normal)
   3. Erreurs d'import

✅ Solutions :
   1. Garder une seule version par recueil (priorité à la source la plus complète)
   2. Utiliser le champ sha256 pour déduplication
   3. Créer une vue SQL qui élimine les doublons
""")
else:
    print("✅ Aucun doublon détecté. La base de données est propre.")

print("="*80)

conn.close()