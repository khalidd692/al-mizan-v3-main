#!/usr/bin/env python3
"""
Test détaillé de la réponse API
"""

import requests
import json

def test_api_response():
    """Examiner la structure exacte de la réponse API"""
    
    print("=" * 60)
    print("🔍 TEST RÉPONSE API HADITH GADING")
    print("=" * 60)
    
    # Test 1: Récupérer un hadith
    print("\n1️⃣ Récupération hadith Bukhari #1...")
    try:
        resp = requests.get("https://api.hadith.gading.dev/books/bukhari/1", timeout=10)
        print(f"   Status: {resp.status_code}")
        
        data = resp.json()
        print(f"\n   📦 Structure complète de la réponse:")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
        
        print(f"\n   🔑 Clés disponibles:")
        print(f"      - Niveau racine: {list(data.keys())}")
        
        if 'data' in data:
            hadith_data = data['data']
            print(f"      - Niveau 'data': {list(hadith_data.keys())}")
            
            print(f"\n   📖 Contenu du hadith:")
            for key, value in hadith_data.items():
                if isinstance(value, str):
                    preview = value[:100] + "..." if len(value) > 100 else value
                    print(f"      - {key}: {preview}")
                else:
                    print(f"      - {key}: {value}")
        
        # Test 2: Vérifier si 'arab' et 'id' existent
        print(f"\n2️⃣ Vérification des champs requis:")
        hadith = data.get('data', {})
        
        has_arab = 'arab' in hadith
        has_id = 'id' in hadith
        
        print(f"   - Champ 'arab' présent: {has_arab}")
        print(f"   - Champ 'id' présent: {has_id}")
        
        if has_arab:
            print(f"   - Contenu 'arab': {hadith['arab'][:100]}...")
        
        if has_id:
            print(f"   - Contenu 'id': {hadith['id'][:100] if isinstance(hadith['id'], str) else hadith['id']}")
        
        # Test 3: Identifier le bon champ pour la traduction
        print(f"\n3️⃣ Recherche du champ de traduction:")
        for key in hadith.keys():
            if 'indo' in key.lower() or 'trans' in key.lower() or key == 'id':
                value = hadith[key]
                if isinstance(value, str):
                    print(f"   - Candidat '{key}': {value[:100]}...")
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_api_response()