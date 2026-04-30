#!/usr/bin/env python3
"""
Test de l'API IslamHouse v3 - Structure correcte selon documentation
Syntaxe: {endpoint}/{key}/.../{format}
"""

import requests
import json
import sys

# Configuration
API_KEY = "ISLAMHOUSE_API_KEY_REDACTED"
BASE_URL = "https://api3.islamhouse.com/v3"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

# Stockage des résultats
all_results = {
    "test_date": "",
    "categories": None,
    "books_fr": None,
    "books_ar_source": None,
    "target_books_found": []
}

def test_endpoint(url, description, save_file=None):
    """Teste un endpoint API"""
    print(f"\n{'='*70}")
    print(f"TEST: {description}")
    print(f"URL: {url}")
    print('='*70)
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\n✅ Réponse JSON ({len(str(data))} caractères)")
                
                # Afficher un extrait
                preview = json.dumps(data, ensure_ascii=False, indent=2)[:3000]
                print(preview)
                if len(str(data)) > 3000:
                    print("\n... (tronqué)")
                
                # Sauvegarder si demandé
                if save_file:
                    with open(save_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f"\n💾 Sauvegardé dans: {save_file}")
                
                return data
            except Exception as e:
                print(f"\n⚠️ Réponse non-JSON: {e}")
                print(response.text[:500])
        else:
            print(f"\n❌ Erreur {response.status_code}")
            print(response.text[:500])
    except Exception as e:
        print(f"\n❌ Exception: {e}")
    return None

# Tests
print("="*70)
print("TEST API ISLAMHOUSE v3 - STRUCTURE CORRECTE")
print("="*70)

# 1. API Home - Statistiques
endpoint_home = f"{BASE_URL}/{API_KEY}/main/home/json"
data_home = test_endpoint(endpoint_home, "1. API Home - Statistiques globales", 
                          "islamhouse_api_home.json")

# 2. Liste des catégories en français
endpoint_categories = f"{BASE_URL}/{API_KEY}/main/categories/fr/json"
data_categories = test_endpoint(endpoint_categories, "2. Liste des catégories (français)",
                                "islamhouse_api_categories_fr.json")

# 3. Livres en français - page 1
# Format: get-items/{slang}/{flang}/{type}/{pageNum}/{limit}/json
endpoint_books = f"{BASE_URL}/{API_KEY}/main/get-items/showall/fr/book/1/50/json"
data_books = test_endpoint(endpoint_books, "3. Livres en français (page 1)",
                           "islamhouse_api_books_fr_page1.json")

# 4. Livres avec source arabe
endpoint_books_ar = f"{BASE_URL}/{API_KEY}/main/get-items/ar/fr/book/1/50/json"
data_books_ar = test_endpoint(endpoint_books_ar, "4. Livres source arabe traduits en FR",
                              "islamhouse_api_books_ar_fr.json")

# 5. Pagination - page 2
endpoint_books_p2 = f"{BASE_URL}/{API_KEY}/main/get-items/showall/fr/book/2/50/json"
data_books_p2 = test_endpoint(endpoint_books_p2, "5. Pagination - Page 2")

print("\n" + "="*70)
print("RECHERCHE DES LIVRES SPÉCIFIQUES")
print("="*70)

# Livres recherchés
TARGET_BOOKS = [
    "Nukhbat Al-Fikar",
    "Mustalah Al-Hadith", 
    "Taysir Al-Hadith",
    "Al-Muqiza",
    "Al-Baïqouniyya"
]
TARGET_KEYWORDS = ["nukhbat", "mustalah", "taysir", "muqiza", "baïqoun", "beyqoun", 
                   "نخبة", "مصطلح", "تيسير", "مقيزة", "البيقونية"]

found_books = []
all_books_data = []

# Collecter tous les livres des différentes requêtes
for data in [data_books, data_books_ar, data_books_p2]:
    if data and isinstance(data, dict):
        if 'data' in data:
            all_books_data.extend(data['data'])
        elif 'items' in data:
            all_books_data.extend(data['items'])
    elif data and isinstance(data, list):
        all_books_data.extend(data)

print(f"\n📚 Total livres analysés: {len(all_books_data)}")

# Chercher les livres cibles
for book in all_books_data:
    title = str(book.get('title', '') or book.get('name', '') or '')
    description = str(book.get('description', '') or book.get('desc', '') or '')
    full_text = f"{title} {description}".lower()
    
    for keyword in TARGET_KEYWORDS:
        if keyword.lower() in full_text:
            found_books.append({
                'title': title,
                'id': book.get('id', 'N/A'),
                'url': book.get('url', ''),
                'description': description[:200] if description else ''
            })
            break

# Supprimer les doublons
seen = set()
unique_found = []
for book in found_books:
    if book['id'] not in seen:
        seen.add(book['id'])
        unique_found.append(book)

print(f"\n✅ Livres spécifiques trouvés: {len(unique_found)}")
for book in unique_found:
    print(f"\n   📖 {book['title']}")
    print(f"      ID: {book['id']}")
    if book['description']:
        print(f"      Desc: {book['description'][:100]}...")

if not unique_found:
    print("\n❌ Aucun livre spécifique trouvé dans les résultats")
    print("   Les livres recherchés:")
    for tb in TARGET_BOOKS:
        print(f"      - {tb}")

print("\n" + "="*70)
print("RÉSULTAT FINAL")
print("="*70)

success = data_books is not None

if success:
    print("\n✅ API ISLAMHOUSE v3 FONCTIONNELLE")
    print(f"   • Home/Stats: {'✅' if data_home else '❌'}")
    print(f"   • Catégories FR: {'✅' if data_categories else '❌'}")
    print(f"   • Livres FR: {'✅' if data_books else '❌'}")
    print(f"   • Livres AR→FR: {'✅' if data_books_ar else '❌'}")
    print(f"\n📊 Livres trouvés: {len(unique_found)}/{len(TARGET_BOOKS)} cibles")
    
    # Sauvegarder les résultats
    all_results.update({
        "test_date": "2026-04-30",
        "categories": data_categories is not None,
        "books_fr": data_books is not None,
        "books_ar_source": data_books_ar is not None,
        "target_books_found": unique_found,
        "total_books_analyzed": len(all_books_data)
    })
    
    with open("islamhouse_api_test_results.json", 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print("\n� Résultats sauvegardés dans: islamhouse_api_test_results.json")
    
    sys.exit(0)  # Success
else:
    print("\n❌ API ISLAMHOUSE v3 NON FONCTIONNELLE")
    print("   Impossible de récupérer les livres")
    sys.exit(1)  # Failure
