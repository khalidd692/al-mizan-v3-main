#!/usr/bin/env python3
"""
Intégration API HadeethEnc v1 pour Al Mîzân
Récupère les hadiths en français avec explications détaillées
"""

import requests
import json
import os
import time
from datetime import datetime

BASE_URL = "https://hadeethenc.com/api/v1"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

def api_request(url, description=""):
    """Effectue une requête API avec retry"""
    for attempt in range(3):
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"  ⚠️ {description}: HTTP {response.status_code} (tentative {attempt+1})")
        except Exception as e:
            print(f"  ⚠️ {description}: {e} (tentative {attempt+1})")
        time.sleep(1)
    return None

def get_all_categories(language="fr"):
    """Récupère toutes les catégories"""
    url = f"{BASE_URL}/categories/roots/?language={language}"
    print(f"\n📚 Récupération des catégories ({language})...")
    data = api_request(url, "Catégories")
    if data:
        print(f"   ✅ {len(data)} catégories trouvées")
    return data

def get_hadeeths_by_category(category_id, language="fr", max_pages=10):
    """Récupère tous les hadiths d'une catégorie avec pagination"""
    all_hadeeths = []
    page = 1
    
    print(f"\n📖 Récupération des hadiths (catégorie {category_id})...")
    
    while page <= max_pages:
        url = f"{BASE_URL}/hadeeths/list/?language={language}&category_id={category_id}&page={page}&per_page=50"
        print(f"   Page {page}...", end=" ")
        
        data = api_request(url, f"Hadiths page {page}")
        
        if data and 'data' in data:
            hadeeths = data['data']
            all_hadeeths.extend(hadeeths)
            print(f"✅ {len(hadeeths)} hadiths")
            
            # Vérifier si c'est la dernière page
            meta = data.get('meta', {})
            if page >= int(meta.get('last_page', 1)):
                break
            page += 1
        else:
            print("⚠️ Pas de données")
            break
    
    print(f"   Total: {len(all_hadeeths)} hadiths")
    return all_hadeeths

def get_hadeeth_detail(hadeeth_id, language="fr"):
    """Récupère les détails d'un hadith"""
    url = f"{BASE_URL}/hadeeths/one/?id={hadeeth_id}&language={language}"
    return api_request(url, f"Hadith {hadeeth_id}")

def categorize_for_zones(hadeeths_with_details):
    """Catégorise les hadiths par zone Al Mîzân"""
    zones = {
        "zone_22_fawaid_tarhawiyyah": [],  # Fawa'id éducatives
        "zone_03_corpus_core": [],          # Hadiths de base
        "zone_21_fawaaid_aqadiyyah": [],    # Aqida
        "zone_20_fawaaid_fiqhiyyah": [],     # Fiqh
        "zone_10_sabab_al_wurud": [],       # Contexte
    }
    
    for hadeeth in hadeeths_with_details:
        if not hadeeth:
            continue
            
        detail_fr = hadeeth.get('fr', {})
        detail_ar = hadeeth.get('ar', {})
        
        # Créer l'entrée
        entry = {
            "id_hadeethenc": hadeeth.get('id'),
            "titre_fr": detail_fr.get('title', ''),
            "texte_ar": detail_ar.get('hadeeth', '')[:500] if detail_ar else '',
            "explication_fr": detail_fr.get('explanation', '')[:300] if detail_fr else '',
            "hints_fr": detail_fr.get('hints', [])[:3] if detail_fr else [],
            "grade": detail_ar.get('grade', '') if detail_ar else '',
            "attribution": detail_ar.get('attribution', '') if detail_ar else '',
            "categories": hadeeth.get('categories', []),
            "source": "hadeethenc_api",
            "url": f"https://hadeethenc.com/ar/hadeeth/{hadeeth.get('id')}",
            "statut": "PENDING_FR"
        }
        
        # Déterminer la catégorie primaire
        categories = hadeeth.get('categories', [])
        cat_id = str(categories[0]) if categories else '0'
        
        # Catégorisation selon l'ID de catégorie HadeethEnc
        # 1 = Coran, 2 = Hadith, 3 = Aqida, 4 = Fiqh, 5 = Vertus, 6 = Da'wah, 7 = Biographie
        if cat_id == '2':  # Hadith sciences
            zones["zone_03_corpus_core"].append(entry)
        elif cat_id == '3':  # Aqida
            zones["zone_21_fawaaid_aqadiyyah"].append(entry)
        elif cat_id == '4':  # Fiqh
            zones["zone_20_fawaaid_fiqhiyyah"].append(entry)
        elif cat_id == '5':  # Vertus/Manners
            zones["zone_22_fawaid_tarhawiyyah"].append(entry)
        elif cat_id in ['6', '7']:  # Da'wah, Biographie
            zones["zone_10_sabab_al_wurud"].append(entry)
        else:
            # Par défaut -> fawaid éducatives
            zones["zone_22_fawaid_tarhawiyyah"].append(entry)
    
    return zones

def update_zone_files(zones_data):
    """Met à jour les fichiers JSON des zones"""
    updated_zones = []
    
    for zone_file, entries in zones_data.items():
        if not entries:
            continue
        
        zone_path = f"sources_fr/{zone_file}.json"
        
        try:
            # Lire ou créer
            if os.path.exists(zone_path):
                with open(zone_path, 'r', encoding='utf-8') as f:
                    zone_data = json.load(f)
            else:
                zone_num = zone_file.split('_')[1]
                zone_data = {
                    "zone": int(zone_num),
                    "nom": zone_file.replace('zone_', '').replace('_', ' ').upper(),
                    "description": "",
                    "entrees": [],
                    "statut_global": "VIDE",
                    "sources_utilisees": [],
                    "count_entrees": 0
                }
            
            # Ajouter les entrées
            for entry in entries:
                zone_entry = {
                    "contenu_fr": f"{entry['titre_fr']} - {entry['explication_fr']}...",
                    "source": entry['source'],
                    "titre_ouvrage": entry['titre_fr'],
                    "url": entry['url'],
                    "grade_hadeeth": entry['grade'],
                    "attribution": entry['attribution'],
                    "statut": entry['statut'],
                    "id_hadeethenc": entry['id_hadeethenc'],
                    "hints": entry['hints_fr']
                }
                zone_data['entrees'].append(zone_entry)
            
            zone_data['count_entrees'] = len(zone_data['entrees'])
            if zone_data['count_entrees'] > 0:
                zone_data['statut_global'] = "PARTIEL" if zone_data['count_entrees'] < 5 else "REMPLI"
            
            sources = zone_data.get('sources_utilisees', [])
            if 'hadeethenc_api' not in sources:
                sources.append('hadeethenc_api')
            zone_data['sources_utilisees'] = sources
            
            with open(zone_path, 'w', encoding='utf-8') as f:
                json.dump(zone_data, f, ensure_ascii=False, indent=2)
            
            print(f"   ✅ {zone_file}: +{len(entries)} entrées (total: {zone_data['count_entrees']})")
            updated_zones.append(zone_file)
            
        except Exception as e:
            print(f"   ❌ Erreur {zone_file}: {e}")
    
    return updated_zones

def main():
    print("="*70)
    print("INTÉGRATION API HADEETHENC v1 - AL MÎZÂN")
    print("="*70)
    
    # 1. Récupérer les catégories
    categories = get_all_categories("fr")
    
    if not categories:
        print("\n❌ Impossible de récupérer les catégories")
        return False
    
    # Sauvegarder les catégories
    with open("hadeethenc_categories_all.json", 'w', encoding='utf-8') as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)
    
    # 2. Récupérer les hadiths de toutes les catégories pertinentes
    all_hadeeths = []
    target_categories = [cat for cat in categories if cat['id'] in ['2', '3', '4', '5', '6']]
    
    print(f"\n📚 Catégories cibles: {len(target_categories)}")
    for cat in target_categories:
        print(f"   - {cat['title']} (ID: {cat['id']}, {cat['hadeeths_count']} hadiths)")
    
    for cat in target_categories:
        cat_id = cat['id']
        hadeeths = get_hadeeths_by_category(cat_id, "fr")
        
        # Ajouter l'info de catégorie à chaque hadith
        for h in hadeeths:
            h['category_id'] = cat_id
            h['category_title'] = cat['title']
        
        all_hadeeths.extend(hadeeths)
        time.sleep(0.5)  # Rate limiting
    
    print(f"\n📊 Total hadiths récupérés: {len(all_hadeeths)}")
    
    # 3. Récupérer les détails de chaque hadith (FR et AR)
    print(f"\n🔍 Récupération des détails pour {len(all_hadeeths)} hadiths...")
    hadeeths_with_details = []
    
    for i, h in enumerate(all_hadeeths, 1):
        h_id = h.get('id')
        print(f"   [{i}/{len(all_hadeeths)}] Hadith {h_id}...", end=" ")
        
        detail_fr = get_hadeeth_detail(h_id, "fr")
        detail_ar = get_hadeeth_detail(h_id, "ar")
        
        if detail_fr or detail_ar:
            hadeeths_with_details.append({
                'id': h_id,
                'fr': detail_fr,
                'ar': detail_ar,
                'categories': h.get('categories', []),
                'category_id': h.get('category_id'),
                'category_title': h.get('category_title')
            })
            print("✅")
        else:
            print("❌")
        
        time.sleep(0.3)  # Rate limiting
    
    print(f"\n✅ Détails récupérés: {len(hadeeths_with_details)}/{len(all_hadeeths)}")
    
    # Sauvegarder tous les détails
    with open("hadeethenc_all_hadeeths_details.json", 'w', encoding='utf-8') as f:
        json.dump(hadeeths_with_details, f, ensure_ascii=False, indent=2)
    
    # 4. Catégoriser par zones
    print(f"\n📁 Catégorisation par zones Al Mîzân...")
    zones_data = categorize_for_zones(hadeeths_with_details)
    
    # 5. Mettre à jour les fichiers de zones
    print(f"\n📝 Mise à jour des fichiers sources_fr/...")
    updated_zones = update_zone_files(zones_data)
    
    # 6. Générer le rapport
    report = {
        "date": datetime.now().isoformat(),
        "api": "HadeethEnc v1",
        "endpoint": "https://hadeethenc.com/api/v1",
        "categories_fetched": len(categories),
        "total_hadeeths": len(all_hadeeths),
        "details_fetched": len(hadeeths_with_details),
        "zones_updated": updated_zones,
        "by_category": {
            cat['title']: len([h for h in all_hadeeths if h.get('category_id') == cat['id']])
            for cat in target_categories
        }
    }
    
    with open("hadeethenc_integration_report.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 7. Résumé final
    print("\n" + "="*70)
    print("RÉSULTAT FINAL")
    print("="*70)
    print(f"✅ API HadeethEnc v1 intégrée avec succès")
    print(f"   • Catégories: {len(categories)}")
    print(f"   • Hadiths récupérés: {len(all_hadeeths)}")
    print(f"   • Détails complets: {len(hadeeths_with_details)}")
    print(f"   • Zones mises à jour: {len(updated_zones)}")
    for zone in updated_zones:
        count = len(zones_data.get(zone, []))
        print(f"      - {zone}: {count} entrées")
    print(f"\n📄 Rapport: hadeethenc_integration_report.json")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
