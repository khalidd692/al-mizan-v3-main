#!/usr/bin/env python3
"""
Test de l'API HadeethEnc v1 pour Al Mîzân
API: https://hadeethenc.com/api/v1
"""

import requests
import json

BASE_URL = "https://hadeethenc.com/api/v1"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

def test_endpoint(url, description, save_file=None):
    """Teste un endpoint API"""
    print(f"\n{'='*70}")
    print(f"TEST: {description}")
    print(f"URL: {url}")
    print(f"{'='*70}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ SUCCESS - JSON ({len(str(data))} caractères)")
            
            # Preview
            preview = json.dumps(data, ensure_ascii=False, indent=2)[:2500]
            print(preview)
            if len(str(data)) > 2500:
                print("\n... (tronqué)")
            
            # Sauvegarder
            if save_file:
                with open(save_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"\n💾 Sauvegardé: {save_file}")
            
            return data
        else:
            print(f"\n❌ Erreur {response.status_code}")
            print(response.text[:500])
    except Exception as e:
        print(f"\n❌ Exception: {e}")
    
    return None

print("="*70)
print("TEST API HADEETHENC v1")
print("="*70)

# 1. Test categories en français
print("\n📚 Test 1: Catégories racines en FR")
categories_fr = test_endpoint(
    f"{BASE_URL}/categories/roots/?language=fr",
    "Catégories racines FR",
    "hadeethenc_categories_fr.json"
)

# 2. Test catégories en anglais (pour comparaison)
print("\n📚 Test 2: Catégories racines en EN")
categories_en = test_endpoint(
    f"{BASE_URL}/categories/roots/?language=en",
    "Catégories racines EN",
    "hadeethenc_categories_en.json"
)

# 3. Si on a des catégories, chercher celle du hadith
hadith_category_id = None
if categories_fr:
    for cat in categories_fr:
        title = cat.get('title', '').lower()
        if 'hadith' in title or 'حديث' in title:
            hadith_category_id = cat.get('id')
            print(f"\n📍 Catégorie Hadith trouvée: ID {hadith_category_id} - {cat.get('title')}")
            print(f"   Hadiths count: {cat.get('hadeeths_count')}")
            break

# 4. Test liste des hadiths en FR
if hadith_category_id:
    print(f"\n📚 Test 3: Liste des hadiths (catégorie {hadith_category_id}) en FR")
    hadiths_fr = test_endpoint(
        f"{BASE_URL}/hadeeths/list/?language=fr&category_id={hadith_category_id}&page=1&per_page=20",
        f"Hadiths FR (cat {hadith_category_id})",
        "hadeethenc_hadiths_fr.json"
    )
    
    # 5. Test un hadith spécifique en FR
    if hadiths_fr and 'data' in hadiths_fr and hadiths_fr['data']:
        first_hadith = hadiths_fr['data'][0]
        hadith_id = first_hadith.get('id')
        print(f"\n📚 Test 4: Détails d'un hadith spécifique (ID {hadith_id}) en FR")
        hadith_detail = test_endpoint(
            f"{BASE_URL}/hadeeths/one/?id={hadith_id}&language=fr",
            f"Hadith détail FR (ID {hadith_id})",
            "hadeethenc_hadith_detail_fr.json"
        )
        
        # 6. Même hadith en AR pour comparer
        print(f"\n📚 Test 5: Détails du même hadith en AR")
        hadith_detail_ar = test_endpoint(
            f"{BASE_URL}/hadeeths/one/?id={hadith_id}&language=ar",
            f"Hadith détail AR (ID {hadith_id})",
            "hadeethenc_hadith_detail_ar.json"
        )

# Résumé
print("\n" + "="*70)
print("RÉSUMÉ DES TESTS")
print("="*70)
print(f"✅ API HadeethEnc v1 testée")
print(f"   • Catégories FR: {'OK' if categories_fr else 'FAILED'}")
print(f"   • Hadiths FR: {'OK' if 'hadiths_fr' in dir() and hadiths_fr else 'N/A'}")
print(f"\n💾 Fichiers générés:")
print(f"   - hadeethenc_categories_fr.json")
print(f"   - hadeethenc_categories_en.json")
if hadith_category_id:
    print(f"   - hadeethenc_hadiths_fr.json")
    print(f"   - hadeethenc_hadith_detail_fr.json")
    print(f"   - hadeethenc_hadith_detail_ar.json")
