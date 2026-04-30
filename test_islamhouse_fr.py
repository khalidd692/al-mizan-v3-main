#!/usr/bin/env python3
"""
Test des endpoints Français IslamHouse API v3
"""

import requests
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

BASE_URL = "https://api3.islamhouse.com/v3"
API_KEY = "ISLAMHOUSE_API_KEY_REDACTED"  # Clé sans 'y' qui fonctionne pour /home

def test_endpoint(url, description, save_file=None):
    """Teste un endpoint API"""
    print(f"\n{'='*70}")
    print(f"TEST: {description}")
    print(f"URL: {url}")
    print(f"{'='*70}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ SUCCESS - JSON ({len(str(data))} caractères)")
                
                # Sauvegarder
                if save_file:
                    with open(save_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f"💾 Sauvegardé: {save_file}")
                
                return data
            except:
                print("⚠️ Réponse 200 mais pas JSON")
        else:
            print(f"❌ Erreur {response.status_code}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    return None

print("="*70)
print("TEST ENDPOINTS FRANÇAIS ISLAMHOUSE API v3")
print("="*70)

# 1. Récupérer le home pour trouver l'URL du contenu FR
print("\n🔄 Récupération des infos depuis /home...")
home_data = test_endpoint(f"{BASE_URL}/{API_KEY}/main/home/json", "API Home")

fr_site_url = None
if home_data and 'data' in home_data:
    for lang in home_data['data']:
        if lang.get('language_code') == 'fr':
            fr_site_url = lang.get('site_contents')
            print(f"\n📍 URL contenu FR trouvée: {fr_site_url}")
            break

# 2. Tester l'URL du contenu français
if fr_site_url:
    fr_content = test_endpoint(fr_site_url, "Contenu FR (sitecontent)", 
                               "islamhouse_fr_sitecontent.json")

# 3. Essayer différents patterns pour récupérer les livres FR
print("\n" + "="*70)
print("TEST PATTERNS LIVRES FRANÇAIS")
print("="*70)

book_patterns = [
    # Pattern vu dans la doc pour récupérer les items
    (f"{BASE_URL}/{API_KEY}/main/get-items/showall/fr/all/1/50/json", "Tous types FR"),
    (f"{BASE_URL}/{API_KEY}/main/get-items/showall/fr/book/1/50/json", "Livres FR"),
    (f"{BASE_URL}/{API_KEY}/main/get-items/ar/fr/book/1/50/json", "Livres AR→FR"),
    
    # Alternatives
    (f"{BASE_URL}/{API_KEY}/main/items/fr/book/1/50/json", "Items pattern alternatif"),
    (f"{BASE_URL}/{API_KEY}/main/books/fr/1/50/json", "Books pattern"),
]

books_data = None
for url, desc in book_patterns:
    result = test_endpoint(url, desc)
    if result:
        books_data = result
        break

# 4. Si on a des livres, chercher les cibles
print("\n" + "="*70)
print("RECHERCHE LIVRES SPÉCIFIQUES")
print("="*70)

if books_data:
    print(f"\n📚 Données reçues: {type(books_data)}")
    if isinstance(books_data, dict):
        print(f"   Clés: {list(books_data.keys())}")
        if 'data' in books_data:
            items = books_data['data']
        elif 'items' in books_data:
            items = books_data['items']
        else:
            items = []
    elif isinstance(books_data, list):
        items = books_data
    else:
        items = []
    
    print(f"\n📖 Nombre d'items: {len(items)}")
    
    if items:
        print("\nPremiers items:")
        for item in items[:3]:
            title = item.get('title', item.get('name', 'N/A'))
            print(f"   - {title}")
        
        # Recherche des livres cibles
        TARGETS = ["nukhbat", "mustalah", "taysir", "muqiza", "baïqoun", 
                   "نخبة", "مصطلح", "تيسير", "مقيزة", "البيقونية"]
        
        found = []
        for item in items:
            text = f"{item.get('title','')} {item.get('description','')}".lower()
            for target in TARGETS:
                if target.lower() in text:
                    found.append(item)
                    break
        
        print(f"\n✅ Livres cibles trouvés: {len(found)}")
        for book in found[:5]:
            print(f"   📖 {book.get('title', 'N/A')}")
else:
    print("\n❌ Aucune donnée de livres récupérée")

print("\n" + "="*70)
print("RÉSULTAT FINAL")
print("="*70)

if books_data:
    print("\n✅ API ISLAMHOUSE v3 FONCTIONNELLE pour les livres FR")
else:
    print("\n⚠️ API partiellement fonctionnelle - home OK mais pas les livres")
    print("   Recommandation: Explorer les endpoints via le sitecontent FR")
