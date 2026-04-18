#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de l'API HadeethEnc.com
Documentation: https://documenter.getpostman.com/view/5211979/TVev3j7q
Alternative à Dorar.net pour le harvesting de hadiths
"""

import requests
import json
from typing import Dict, List, Optional

class HadeethEncAPI:
    """Client pour l'API HadeethEnc.com"""
    
    BASE_URL = "https://hadeethenc.com/api/v1"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'Al-Mizan-Harvester/7.0'
        })
    
    def get_categories(self, lang: str = "ar") -> Optional[Dict]:
        """
        Récupère toutes les catégories de hadiths
        
        Args:
            lang: Code langue (ar, en, fr, etc.)
        
        Returns:
            Dict avec les catégories ou None si erreur
        """
        try:
            url = f"{self.BASE_URL}/categories/list"
            params = {"language": lang}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"❌ Erreur get_categories: {e}")
            return None
    
    def get_hadiths_by_category(
        self, 
        category_id: int, 
        lang: str = "ar",
        page: int = 1,
        per_page: int = 20
    ) -> Optional[Dict]:
        """
        Récupère les hadiths d'une catégorie
        
        Args:
            category_id: ID de la catégorie
            lang: Code langue
            page: Numéro de page
            per_page: Hadiths par page (max 50)
        
        Returns:
            Dict avec les hadiths ou None si erreur
        """
        try:
            url = f"{self.BASE_URL}/hadeeths/list"
            params = {
                "language": lang,
                "category_id": category_id,
                "page": page,
                "per_page": min(per_page, 50)
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"❌ Erreur get_hadiths_by_category: {e}")
            return None
    
    def get_hadith_by_id(self, hadith_id: int, lang: str = "ar") -> Optional[Dict]:
        """
        Récupère un hadith spécifique par son ID
        
        Args:
            hadith_id: ID du hadith
            lang: Code langue
        
        Returns:
            Dict avec le hadith ou None si erreur
        """
        try:
            url = f"{self.BASE_URL}/hadeeths/one"
            params = {
                "language": lang,
                "id": hadith_id
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"❌ Erreur get_hadith_by_id: {e}")
            return None

def test_api():
    """Fonction de test de l'API"""
    
    print("🔍 Test API HadeethEnc.com")
    print("=" * 70)
    
    api = HadeethEncAPI()
    
    # Test 1: Récupérer les catégories
    print("\n📚 Test 1: Récupération des catégories")
    print("-" * 70)
    categories = api.get_categories(lang="ar")
    
    if categories:
        print(f"✅ Catégories récupérées avec succès")
        print(f"   Type: {type(categories)}")
        print(f"   Clés: {list(categories.keys()) if isinstance(categories, dict) else 'Liste'}")
        
        # Afficher quelques catégories
        if isinstance(categories, dict) and 'data' in categories:
            cats = categories['data'][:3]
            print(f"\n   Exemples de catégories:")
            for cat in cats:
                print(f"   - ID: {cat.get('id')}, Titre: {cat.get('title', 'N/A')}")
        elif isinstance(categories, list):
            print(f"\n   Première catégorie:")
            print(f"   {json.dumps(categories[0], indent=2, ensure_ascii=False)}")
    else:
        print("❌ Échec de récupération des catégories")
    
    # Test 2: Récupérer des hadiths d'une catégorie
    print("\n📖 Test 2: Récupération de hadiths (catégorie 1)")
    print("-" * 70)
    hadiths = api.get_hadiths_by_category(category_id=1, lang="ar", per_page=3)
    
    if hadiths:
        print(f"✅ Hadiths récupérés avec succès")
        print(f"   Type: {type(hadiths)}")
        print(f"   Clés: {list(hadiths.keys()) if isinstance(hadiths, dict) else 'Liste'}")
        
        # Afficher structure d'un hadith
        if isinstance(hadiths, dict) and 'data' in hadiths:
            hadith_list = hadiths['data']
            if hadith_list:
                print(f"\n   Nombre de hadiths: {len(hadith_list)}")
                print(f"\n   Structure du premier hadith:")
                first_hadith = hadith_list[0]
                print(f"   Clés disponibles: {list(first_hadith.keys())}")
                
                # Afficher les champs importants
                print(f"\n   📝 Exemple de hadith:")
                print(f"   - ID: {first_hadith.get('id')}")
                print(f"   - Titre: {first_hadith.get('title', 'N/A')[:100]}...")
                print(f"   - Texte: {first_hadith.get('hadeeth', 'N/A')[:150]}...")
                print(f"   - Grade: {first_hadith.get('grade', 'N/A')}")
                print(f"   - Attribution: {first_hadith.get('attribution', 'N/A')}")
                
                # Afficher la structure complète du premier hadith
                print(f"\n   Structure JSON complète:")
                print(json.dumps(first_hadith, indent=2, ensure_ascii=False))
        elif isinstance(hadiths, list) and hadiths:
            print(f"\n   Premier hadith:")
            print(json.dumps(hadiths[0], indent=2, ensure_ascii=False))
    else:
        print("❌ Échec de récupération des hadiths")
    
    # Test 3: Récupérer un hadith spécifique (utiliser un ID valide du test 2)
    print("\n🔍 Test 3: Récupération d'un hadith spécifique (ID: 5907)")
    print("-" * 70)
    hadith = api.get_hadith_by_id(hadith_id=5907, lang="ar")
    
    if hadith:
        print(f"✅ Hadith récupéré avec succès")
        print(f"   Type: {type(hadith)}")
        if isinstance(hadith, dict):
            print(f"   Clés: {list(hadith.keys())}")
            print(f"\n   Détails:")
            print(json.dumps(hadith, indent=2, ensure_ascii=False)[:500])
    else:
        print("❌ Échec de récupération du hadith")
    
    print("\n" + "=" * 70)
    print("✅ Tests terminés")
    print("\n💡 Analyse:")
    print("   - API fonctionnelle: ✅" if categories or hadiths else "   - API fonctionnelle: ❌")
    print("   - Structure JSON: ✅" if hadiths else "   - Structure JSON: ❌")
    print("   - Données exploitables: ✅" if hadiths else "   - Données exploitables: ❌")
    print("\n📋 Prochaine étape:")
    print("   → Créer harvester_hadeethenc.py pour extraction massive")

if __name__ == "__main__":
    test_api()