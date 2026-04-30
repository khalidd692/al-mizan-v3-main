#!/usr/bin/env python3
"""
Intégration API IslamHouse v3 pour Al Mîzân
Récupère les livres de hadith en français et les intègre dans les zones
"""

import requests
import json
import os
from datetime import datetime

# Configuration
API_KEY = "ISLAMHOUSE_API_KEY_REDACTED"
BASE_URL = "https://api3.islamhouse.com/v3"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

# Livres cibles à rechercher
TARGET_BOOKS = {
    "Nukhbat Al-Fikar": ["nukhbat", "نخبة", "fikar", "الفكر"],
    "Mustalah Al-Hadith": ["mustalah", "مصطلح", "حديث"],
    "Taysir Al-Hadith": ["taysir", "تيسير"],
    "Al-Muqiza": ["muqiza", "مقيزة"],
    "Al-Baïqouniyya": ["baïqoun", "beyqoun", "baeqoun", "البيقونية", "beyquniyyah"],
}

def api_request(url, description=""):
    """Effectue une requête API"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  ❌ {description}: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"  ❌ {description}: {e}")
        return None

def get_french_books(max_pages=15):
    """Récupère tous les livres en français avec pagination"""
    all_books = []
    
    print(f"\n📚 Récupération des livres en français...")
    print(f"   Endpoint: /main/books/fr/fr/{{page}}/50/json")
    
    for page in range(1, max_pages + 1):
        url = f"{BASE_URL}/{API_KEY}/main/books/fr/fr/{page}/50/json"
        print(f"   Page {page}...", end=" ")
        
        data = api_request(url, f"Livres page {page}")
        
        # La réponse est un dict avec 'data' et 'links'
        books_list = []
        if data and isinstance(data, dict) and 'data' in data:
            books_list = data['data']
        elif data and isinstance(data, list):
            books_list = data
        
        if books_list and len(books_list) > 0:
            all_books.extend(books_list)
            print(f"✅ {len(books_list)} livres")
            
            # Si moins de 50 résultats, on a atteint la fin
            if len(books_list) < 50:
                print(f"   Dernière page atteinte.")
                break
        else:
            print(f"⚠️ Pas de données")
            break
    
    print(f"\n📊 Total livres récupérés: {len(all_books)}")
    return all_books

def search_target_books(books):
    """Recherche les livres cibles dans la liste"""
    found = {}
    
    for book in books:
        title = str(book.get('title', '')).lower()
        desc = str(book.get('description', '')).lower()
        full_text = f"{title} {desc}"
        
        for target_name, keywords in TARGET_BOOKS.items():
            for keyword in keywords:
                if keyword.lower() in full_text:
                    if target_name not in found:
                        found[target_name] = []
                    found[target_name].append({
                        'id': book.get('id'),
                        'title': book.get('title'),
                        'description': book.get('description', '')[:200],
                        'pdf_url': extract_pdf_url(book),
                        'source_url': f"https://islamhouse.com/fr/books/{book.get('id', '')}",
                        'matched_keyword': keyword
                    })
                    break
    
    return found

def extract_pdf_url(book):
    """Extrait l'URL PDF d'un livre"""
    attachments = book.get('attachments', [])
    for att in attachments:
        if att.get('extension') == 'pdf' or 'pdf' in att.get('mimetype', ''):
            url = att.get('url', '')
            if url and not url.startswith('http'):
                url = f"https://d1.islamhouse.com/{url}"
            return url
    return None

def categorize_for_zones(found_books):
    """Catégorise les livres trouvés par zone Al Mîzân"""
    zones = {
        "zone_10_sabab_al_wurud": [],
        "zone_11_shuruh": [],
        "zone_14_positions_imams": [],
        "zone_19_masadir_thanawiyyah": [],
        "zone_22_fawaid_tarhawiyyah": [],
        "zone_30_takhrij_mawsuu": [],
        "zone_38_takhrij_wa_tahqiq": [],
        "general_hadith": []
    }
    
    for book_name, books in found_books.items():
        for book in books:
            entry = {
                "contenu_fr": f"{book['title']} - {book['description'][:150]}...",
                "source": "islamhouse_api",
                "titre_ouvrage": book['title'],
                "url": book['source_url'],
                "pdf_url": book['pdf_url'],
                "statut": "PENDING_FR",
                "id_islamhouse": book['id']
            }
            
            # Catégorisation selon le titre
            title_lower = book['title'].lower()
            
            if any(k in title_lower for k in ['sharh', 'شرح', 'explication']):
                zones["zone_11_shuruh"].append(entry)
            elif any(k in title_lower for k in ['nukhbat', 'mustalah', 'beyqoun', 'baïqoun']):
                zones["zone_19_masadir_thanawiyyah"].append(entry)
            elif any(k in title_lower for k in ['takhrij', 'tahqiq', 'تحقيق']):
                zones["zone_38_takhrij_wa_tahqiq"].append(entry)
            elif any(k in title_lower for k in ['mawsuu', 'encyclopedie', ' موسوع']):
                zones["zone_30_takhrij_mawsuu"].append(entry)
            else:
                zones["general_hadith"].append(entry)
    
    return zones

def update_zone_files(zones_data):
    """Met à jour les fichiers JSON des zones"""
    updated_zones = []
    
    for zone_file, entries in zones_data.items():
        if not entries:
            continue
            
        zone_path = f"sources_fr/{zone_file}.json"
        
        try:
            # Lire le fichier existant
            if os.path.exists(zone_path):
                with open(zone_path, 'r', encoding='utf-8') as f:
                    zone_data = json.load(f)
            else:
                # Créer une structure par défaut
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
            
            # Ajouter les nouvelles entrées
            existing_count = len(zone_data.get('entrees', []))
            zone_data['entrees'] = zone_data.get('entrees', []) + entries
            zone_data['count_entrees'] = len(zone_data['entrees'])
            
            # Mettre à jour le statut
            if zone_data['count_entrees'] > 0:
                zone_data['statut_global'] = "PARTIEL" if zone_data['count_entrees'] < 5 else "REMPLI"
            
            # Ajouter islamhouse aux sources utilisées
            sources = zone_data.get('sources_utilisees', [])
            if 'islamhouse_api' not in sources:
                sources.append('islamhouse_api')
            zone_data['sources_utilisees'] = sources
            
            # Sauvegarder
            with open(zone_path, 'w', encoding='utf-8') as f:
                json.dump(zone_data, f, ensure_ascii=False, indent=2)
            
            new_entries = len(entries)
            print(f"   ✅ {zone_file}: +{new_entries} entrées (total: {zone_data['count_entrees']})")
            updated_zones.append(zone_file)
            
        except Exception as e:
            print(f"   ❌ Erreur {zone_file}: {e}")
    
    return updated_zones

def generate_report(books, found_books, updated_zones):
    """Génère le rapport d'intégration"""
    report = {
        "date": datetime.now().isoformat(),
        "source": "IslamHouse API v3",
        "total_books_api": len(books),
        "target_books_found": {k: len(v) for k, v in found_books.items()},
        "zones_updated": updated_zones,
        "details": found_books
    }
    
    with open("islamhouse_integration_report.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return report

def main():
    print("="*70)
    print("INTÉGRATION API ISLAMHOUSE v3 - AL MÎZÂN")
    print("="*70)
    
    # 1. Récupérer tous les livres
    books = get_french_books(max_pages=8)  # 8 pages = ~400 livres max
    
    if not books:
        print("\n❌ Impossible de récupérer les livres depuis l'API")
        return False
    
    # Sauvegarder tous les livres
    with open("islamhouse_all_books_fr.json", 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=2)
    print(f"💾 Sauvegardé: islamhouse_all_books_fr.json")
    
    # 2. Rechercher les livres cibles
    print(f"\n🔍 Recherche des livres cibles...")
    for name in TARGET_BOOKS.keys():
        print(f"   - {name}")
    
    found_books = search_target_books(books)
    
    print(f"\n📚 Résultats de la recherche:")
    total_found = 0
    for name, items in found_books.items():
        count = len(items)
        total_found += count
        status = "✅" if count > 0 else "❌"
        print(f"   {status} {name}: {count} trouvé(s)")
        for item in items[:2]:  # Afficher max 2 par livre
            print(f"      → {item['title'][:60]}...")
    
    print(f"\n📊 Total livres cibles trouvés: {total_found}")
    
    # 3. Catégoriser par zones
    print(f"\n📁 Catégorisation par zones Al Mîzân...")
    zones_data = categorize_for_zones(found_books)
    
    # 4. Mettre à jour les fichiers de zones
    print(f"\n📝 Mise à jour des fichiers sources_fr/...")
    updated_zones = update_zone_files(zones_data)
    
    # 5. Générer le rapport
    report = generate_report(books, found_books, updated_zones)
    
    # 6. Résumé final
    print("\n" + "="*70)
    print("RÉSULTAT FINAL")
    print("="*70)
    print(f"✅ API IslamHouse v3 intégrée avec succès")
    print(f"   • Livres FR récupérés: {len(books)}")
    print(f"   • Livres cibles trouvés: {total_found}/{len(TARGET_BOOKS)}")
    print(f"   • Zones mises à jour: {len(updated_zones)}")
    print(f"\n📄 Rapport: islamhouse_integration_report.json")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
