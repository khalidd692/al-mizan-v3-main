#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test de l'API Dorar pour comprendre sa structure"""

import requests
import json

DORAR_API = "https://dorar.net/dorar_api.json"

print("="*70)
print("🧪 TEST API DORAR.NET")
print("="*70)

# Test 1: Requête simple
print("\n📡 Test 1: Requête Sahih al-Bukhari, page 1")
print("-"*70)

try:
    response = requests.get(
        DORAR_API,
        params={
            "skey": "صحيح البخاري",
            "lang": "ar",
            "page": 1
        },
        timeout=15
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
    print(f"Response Length: {len(response.text)} chars")
    
    # Afficher les premiers 500 caractères
    print(f"\nPremiers 500 caractères de la réponse:")
    print("-"*70)
    print(response.text[:500])
    print("-"*70)
    
    # Tenter de parser en JSON
    print("\n🔍 Tentative de parsing JSON...")
    try:
        data = response.json()
        print(f"✅ JSON valide!")
        print(f"Type: {type(data)}")
        
        if isinstance(data, dict):
            print(f"Clés disponibles: {list(data.keys())}")
            
            # Vérifier la clé 'ahadith'
            if 'ahadith' in data:
                ahadith = data['ahadith']
                print(f"\n📚 Clé 'ahadith' trouvée")
                print(f"Type: {type(ahadith)}")
                print(f"Nombre d'éléments: {len(ahadith) if isinstance(ahadith, list) else 'N/A'}")
                
                if isinstance(ahadith, list) and len(ahadith) > 0:
                    print(f"\n🔍 Premier élément:")
                    print(f"Type: {type(ahadith[0])}")
                    
                    if isinstance(ahadith[0], dict):
                        print(f"Clés: {list(ahadith[0].keys())}")
                        print(f"\nContenu complet du premier hadith:")
                        print(json.dumps(ahadith[0], ensure_ascii=False, indent=2))
                    else:
                        print(f"Contenu: {ahadith[0][:200]}...")
        else:
            print(f"⚠️  Réponse n'est pas un dict: {type(data)}")
            print(f"Contenu: {str(data)[:200]}...")
            
    except json.JSONDecodeError as e:
        print(f"❌ Erreur JSON: {e}")
        print(f"La réponse n'est pas du JSON valide")
        
except requests.RequestException as e:
    print(f"❌ Erreur requête: {e}")

print("\n" + "="*70)
print("✅ TEST TERMINÉ")
print("="*70)