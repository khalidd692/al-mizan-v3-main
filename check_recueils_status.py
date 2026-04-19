#!/usr/bin/env python3
"""
Script pour vérifier l'état des recueils de hadiths dans la base de données
"""

import sqlite3
import json
from collections import defaultdict

def check_database_status():
    """Vérifie l'état complet de la base de données"""
    
    conn = sqlite3.connect('backend/almizane.db')
    cursor = conn.cursor()
    
    print("=" * 80)
    print("📊 ÉTAT DES RECUEILS DE HADITHS")
    print("=" * 80)
    
    # 1. Compter les hadiths par collection
    cursor.execute("""
        SELECT collection, COUNT(*) as count
        FROM hadiths
        GROUP BY collection
        ORDER BY count DESC
    """)
    
    collections = cursor.fetchall()
    total_hadiths = sum(count for _, count in collections)
    
    print(f"\n✅ TOTAL HADITHS: {total_hadiths:,}")
    print("\n📚 RÉPARTITION PAR COLLECTION:")
    print("-" * 80)
    
    # Définir les recueils attendus
    kutub_sittah = {
        'sahih_bukhari': 'Sahih Bukhari',
        'sahih_muslim': 'Sahih Muslim',
        'sunan_abu_dawud': 'Sunan Abu Dawud',
        'sunan_tirmidhi': 'Sunan al-Tirmidhi',
        'sunan_nasai': "Sunan al-Nasa'i",
        'sunan_ibn_majah': 'Sunan Ibn Majah'
    }
    
    autres_recueils = {
        'musnad_ahmad': 'Musnad Ahmad',
        'sunan_darimi': 'Sunan al-Darimi',
        'muwatta_malik': 'Muwatta Malik',
        'sahih_ibn_hibban': 'Sahih Ibn Hibban',
        'sahih_ibn_khuzaymah': 'Sahih Ibn Khuzaymah',
        'sunan_kubra_bayhaqi': 'Sunan al-Kubra (Bayhaqi)',
        'musannaf_ibn_abi_shaybah': 'Musannaf Ibn Abi Shaybah',
        'musannaf_abd_razzaq': 'Musannaf Abd al-Razzaq',
        'sunan_daraqutni': 'Sunan al-Daraqutni',
        'adab_mufrad': 'Al-Adab al-Mufrad',
        'riyad_salihin': 'Riyad al-Salihin',
        'bulugh_maram': 'Bulugh al-Maram',
        'forty_hadith': '40 Hadiths (Nawawi)'
    }
    
    collections_dict = {coll: count for coll, count in collections}
    
    # Afficher les Kutub al-Sittah
    print("\n🌟 KUTUB AL-SITTAH (Les 6 Livres Authentiques):")
    kutub_total = 0
    for key, name in kutub_sittah.items():
        count = collections_dict.get(key, 0)
        kutub_total += count
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {name:30} {count:>8,} hadiths")
    
    print(f"\n  📊 Total Kutub al-Sittah: {kutub_total:,} hadiths")
    
    # Afficher les autres recueils
    print("\n📖 AUTRES RECUEILS MAJEURS:")
    autres_total = 0
    for key, name in autres_recueils.items():
        count = collections_dict.get(key, 0)
        autres_total += count
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {name:30} {count:>8,} hadiths")
    
    print(f"\n  📊 Total autres recueils: {autres_total:,} hadiths")
    
    # Afficher les collections non identifiées
    known_collections = set(kutub_sittah.keys()) | set(autres_recueils.keys())
    unknown_collections = [(c, cnt) for c, cnt in collections if c not in known_collections]
    
    if unknown_collections:
        print("\n❓ COLLECTIONS NON IDENTIFIÉES:")
        for coll, count in unknown_collections:
            print(f"  • {coll:30} {count:>8,} hadiths")
    
    # 2. Statistiques détaillées
    print("\n" + "=" * 80)
    print("📈 STATISTIQUES DÉTAILLÉES")
    print("=" * 80)
    
    # Compter les hadiths avec chaîne de transmission
    cursor.execute("SELECT COUNT(*) FROM hadiths WHERE isnad_brut IS NOT NULL AND isnad_brut != ''")
    with_chain = cursor.fetchone()[0]
    
    # Compter les hadiths avec grade
    cursor.execute("SELECT COUNT(*) FROM hadiths WHERE grade_final IS NOT NULL AND grade_final != ''")
    with_grade = cursor.fetchone()[0]
    
    # Compter les hadiths avec référence
    cursor.execute("SELECT COUNT(*) FROM hadiths WHERE numero_hadith IS NOT NULL AND numero_hadith != ''")
    with_ref = cursor.fetchone()[0]
    
    print(f"\n✅ Hadiths avec chaîne de transmission: {with_chain:,} ({with_chain*100/total_hadiths:.1f}%)")
    print(f"✅ Hadiths avec grade d'authenticité: {with_grade:,} ({with_grade*100/total_hadiths:.1f}%)")
    print(f"✅ Hadiths avec référence: {with_ref:,} ({with_ref*100/total_hadiths:.1f}%)")
    
    # 3. Recueils manquants prioritaires
    print("\n" + "=" * 80)
    print("🎯 RECUEILS MANQUANTS PRIORITAIRES")
    print("=" * 80)
    
    missing_priority = []
    
    # Vérifier Musnad Ahmad complet
    ahmad_count = collections_dict.get('musnad_ahmad', 0)
    if ahmad_count < 27000:
        missing_priority.append({
            'name': 'Musnad Ahmad (complet)',
            'current': ahmad_count,
            'target': 27000,
            'priority': 'HAUTE',
            'reason': 'Collection majeure, on n\'a que 16% du total'
        })
    
    # Vérifier les autres recueils manquants
    if 'sahih_ibn_hibban' not in collections_dict:
        missing_priority.append({
            'name': 'Sahih Ibn Hibban',
            'current': 0,
            'target': 7000,
            'priority': 'HAUTE',
            'reason': 'Recueil authentique important'
        })
    
    if 'sahih_ibn_khuzaymah' not in collections_dict:
        missing_priority.append({
            'name': 'Sahih Ibn Khuzaymah',
            'current': 0,
            'target': 3000,
            'priority': 'MOYENNE',
            'reason': 'Recueil authentique'
        })
    
    if 'sunan_kubra_bayhaqi' not in collections_dict:
        missing_priority.append({
            'name': 'Sunan al-Kubra (Bayhaqi)',
            'current': 0,
            'target': 20000,
            'priority': 'MOYENNE',
            'reason': 'Grande collection de jurisprudence'
        })
    
    if 'riyad_salihin' not in collections_dict:
        missing_priority.append({
            'name': 'Riyad al-Salihin',
            'current': 0,
            'target': 1900,
            'priority': 'HAUTE',
            'reason': 'Collection très populaire et accessible'
        })
    
    if 'forty_hadith' not in collections_dict:
        missing_priority.append({
            'name': '40 Hadiths (Nawawi)',
            'current': 0,
            'target': 42,
            'priority': 'HAUTE',
            'reason': 'Collection fondamentale, très courte'
        })
    
    for item in missing_priority:
        print(f"\n🔴 {item['name']}")
        print(f"   Actuel: {item['current']:,} / Cible: {item['target']:,}")
        print(f"   Priorité: {item['priority']}")
        print(f"   Raison: {item['reason']}")
    
    # 4. Recommandations
    print("\n" + "=" * 80)
    print("💡 RECOMMANDATIONS")
    print("=" * 80)
    
    print("""
1. ✅ EXCELLENT DÉPART: Les 6 Kutub al-Sittah sont complets
   → Ce sont les recueils les plus authentiques et importants

2. 🎯 PRIORITÉ IMMÉDIATE (facile à obtenir):
   → 40 Hadiths de Nawawi (42 hadiths seulement)
   → Riyad al-Salihin (~1,900 hadiths)
   → Ces deux sont très populaires et disponibles

3. 📈 EXPANSION RECOMMANDÉE:
   → Compléter Musnad Ahmad (manque ~22,700 hadiths)
   → Ajouter Sahih Ibn Hibban (~7,000 hadiths)
   → Ajouter Sahih Ibn Khuzaymah (~3,000 hadiths)

4. 📊 OBJECTIF RÉALISTE:
   → Atteindre 100,000 hadiths avec les recueils prioritaires
   → Cela couvrirait ~50% du corpus total
   → Excellente base pour l'analyse critique
""")
    
    # 5. Sauvegarder le rapport
    report = {
        'total_hadiths': total_hadiths,
        'kutub_sittah': {k: collections_dict.get(k, 0) for k in kutub_sittah.keys()},
        'autres_recueils': {k: collections_dict.get(k, 0) for k in autres_recueils.keys()},
        'missing_priority': missing_priority,
        'statistics': {
            'with_chain': with_chain,
            'with_grade': with_grade,
            'with_reference': with_ref
        }
    }
    
    with open('output/RECUEILS_STATUS.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n✅ Rapport sauvegardé dans: output/RECUEILS_STATUS.json")
    
    conn.close()

if __name__ == '__main__':
    check_database_status()