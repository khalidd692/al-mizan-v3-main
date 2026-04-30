#!/usr/bin/env python3
"""
Test de l'API IslamHouse v3 - Essais avec différentes variantes de clés et endpoints
"""

import requests
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

BASE_URL = "https://api3.islamhouse.com/v3"

# Différentes variantes de clés à tester
API_KEYS = [
    "ISLAMHOUSE_API_KEY_REDACTED",    # Clé fournie par l'utilisateur
    "ISLAMHOUSE_API_KEY_REDACTEDy",   # Clé avec 'y' à la fin (vu dans la doc)
]

# Différents patterns d'endpoints à tester
ENDPOINT_PATTERNS = [
    # Pattern 1: Documentation officielle
    ("{base}/{key}/main/home/json", "Home/Stats"),
    ("{base}/{key}/main/categories/fr/json", "Catégories FR"),
    ("{base}/{key}/main/get-items/showall/fr/book/1/50/json", "Livres FR page 1"),
    ("{base}/{key}/main/get-items/ar/fr/book/1/50/json", "Livres AR→FR"),
    
    # Pattern 2: Sans /main
    ("{base}/{key}/categories/fr/json", "Catégories (sans main)"),
    ("{base}/{key}/get-items/showall/fr/book/1/50/json", "Livres (sans main)"),
    
    # Pattern 3: Alternative avec query params
    ("{base}/categories?key={key}&flang=fr&format=json", "Catégories (query)"),
    ("{base}/collections/books?key={key}&flang=fr&type=book&format=json&limit=50", "Livres (query)"),
]

def test_endpoint(url, description):
    """Teste un endpoint API"""
    print(f"\n{'='*70}")
    print(f"TEST: {description}")
    print(f"URL: {url}")
    print(f"{'='*70}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\n✅ SUCCESS - Réponse JSON ({len(str(data))} caractères)")
                preview = json.dumps(data, ensure_ascii=False, indent=2)[:2000]
                print(preview)
                if len(str(data)) > 2000:
                    print("\n... (tronqué)")
                return data
            except Exception as e:
                print(f"\n⚠️ Status 200 mais pas JSON: {e}")
                print(response.text[:300])
        else:
            print(f"\n❌ Erreur {response.status_code}")
            print(response.text[:300])
    except Exception as e:
        print(f"\n❌ Exception: {e}")
    return None

print("="*70)
print("TEST API ISLAMHOUSE v3 - MULTIPLES VARIANTES")
print("="*70)

results = {}

for key in API_KEYS:
    print(f"\n\n{'#'*70}")
    print(f"# TEST AVEC CLÉ: {key}")
    print(f"{'#'*70}")
    
    for pattern, desc in ENDPOINT_PATTERNS:
        url = pattern.format(base=BASE_URL, key=key)
        result = test_endpoint(url, f"[{key[:15]}...] {desc}")
        results[f"{key}_{desc}"] = result is not None
        
        if result and "Livres" in desc:
            # Sauvegarder si on trouve des livres
            filename = f"islamhouse_api_{key[:10]}_{desc.replace(' ', '_').replace('→','_')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Sauvegardé dans: {filename}")

print("\n\n" + "="*70)
print("RÉCAPITULATIF DES TESTS")
print("="*70)

success_count = sum(1 for v in results.values() if v)
total_count = len(results)

print(f"\nTests réussis: {success_count}/{total_count}")

if success_count > 0:
    print("\n✅ Endpoints fonctionnels trouvés:")
    for test_name, success in results.items():
        if success:
            print(f"   ✅ {test_name}")
else:
    print("\n❌ Aucun endpoint fonctionnel trouvé")
    print("\nRecommandations:")
    print("1. Vérifier la clé API avec IslamHouse")
    print("2. Essayer d'autres patterns d'URL")
    print("3. Utiliser le web scraping comme fallback")

# Essai direct avec les URLs exactes de la documentation
print("\n\n" + "="*70)
print("TEST AVEC URLS EXACTES DE LA DOCUMENTATION")
print("="*70)

doc_urls = [
    "https://api3.islamhouse.com/v3/ISLAMHOUSE_API_KEY_REDACTEDy/main/home/json",
    "https://api3.islamhouse.com/v3/ISLAMHOUSE_API_KEY_REDACTEDy/main/categories/fr/json",
]

for url in doc_urls:
    test_endpoint(url, f"DOC: {url.split('/')[-2]}")
