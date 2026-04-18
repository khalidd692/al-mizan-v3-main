#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de l'API Dorar.net avec méthode JSONP
Documentation officielle: https://dorar.net/files/dorar_json_api.js.zip
"""

import requests
import json
import re
from typing import Optional, Dict

class DorarJSONPAPI:
    """Client pour l'API Dorar.net avec JSONP"""
    
    BASE_URL = "https://dorar.net/dorar_api.json"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Al-Mizan-Harvester/7.0',
            'Accept': '*/*',
            'Referer': 'https://dorar.net/'
        })
    
    def search_hadith(self, keyword: str) -> Optional[Dict]:
        """
        Recherche de hadiths avec mot-clé
        
        Args:
            keyword: Mot-clé de recherche en arabe
        
        Returns:
            Dict avec les résultats ou None si erreur
        """
        try:
            # Paramètres selon la documentation
            params = {
                'skey': keyword,
                'callback': 'jQuery'  # JSONP callback
            }
            
            print(f"🔍 Recherche: {keyword}")
            print(f"📡 URL: {self.BASE_URL}")
            print(f"📋 Params: {params}")
            
            response = self.session.get(
                self.BASE_URL, 
                params=params, 
                timeout=15
            )
            
            print(f"📊 Status: {response.status_code}")
            print(f"📄 Content-Type: {response.headers.get('Content-Type')}")
            
            response.raise_for_status()
            
            # Récupérer le contenu brut
            raw_content = response.text
            print(f"\n📝 Contenu brut (premiers 500 caractères):")
            print(raw_content[:500])
            print("...")
            
            # Extraire le JSON du JSONP
            # Format attendu: jQuery(...JSON...)
            jsonp_match = re.search(r'jQuery\((.*)\)', raw_content, re.DOTALL)
            
            if jsonp_match:
                json_str = jsonp_match.group(1)
                print(f"\n✅ JSON extrait du JSONP")
                
                # Parser le JSON
                data = json.loads(json_str)
                print(f"📦 Type de données: {type(data)}")
                
                if isinstance(data, dict):
                    print(f"🔑 Clés disponibles: {list(data.keys())}")
                
                return data
            else:
                print(f"\n❌ Impossible d'extraire le JSON du JSONP")
                print(f"Format reçu non conforme")
                return None
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur réseau: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Erreur parsing JSON: {e}")
            return None
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            return None

def test_dorar_jsonp():
    """Test de l'API Dorar avec JSONP"""
    
    print("=" * 80)
    print("🕋 TEST API DORAR.NET - MÉTHODE JSONP OFFICIELLE")
    print("=" * 80)
    
    api = DorarJSONPAPI()
    
    # Test 1: Recherche simple
    print("\n📖 Test 1: Recherche 'الصلاة' (la prière)")
    print("-" * 80)
    
    result = api.search_hadith("الصلاة")
    
    if result:
        print(f"\n✅ Résultat obtenu")
        print(f"📊 Structure:")
        print(json.dumps(result, indent=2, ensure_ascii=False)[:1000])
        
        # Analyser la structure
        if isinstance(result, dict):
            if 'ahadith' in result:
                ahadith = result['ahadith']
                print(f"\n📚 Clé 'ahadith' trouvée")
                print(f"   Type: {type(ahadith)}")
                
                if isinstance(ahadith, dict) and 'result' in ahadith:
                    print(f"   ⚠️  Format HTML détecté dans 'result'")
                    print(f"   Premiers caractères: {str(ahadith['result'])[:200]}")
                elif isinstance(ahadith, list):
                    print(f"   ✅ Liste de hadiths: {len(ahadith)} éléments")
                    if ahadith:
                        print(f"\n   Premier hadith:")
                        print(json.dumps(ahadith[0], indent=4, ensure_ascii=False))
            else:
                print(f"\n⚠️  Clé 'ahadith' non trouvée")
                print(f"   Clés disponibles: {list(result.keys())}")
    else:
        print(f"\n❌ Aucun résultat")
    
    # Test 2: Recherche avec terme différent
    print("\n\n📖 Test 2: Recherche 'الإيمان' (la foi)")
    print("-" * 80)
    
    result2 = api.search_hadith("الإيمان")
    
    if result2:
        print(f"\n✅ Résultat obtenu")
        if isinstance(result2, dict) and 'ahadith' in result2:
            ahadith = result2['ahadith']
            if isinstance(ahadith, list):
                print(f"📚 {len(ahadith)} hadiths trouvés")
            else:
                print(f"⚠️  Format: {type(ahadith)}")
    
    print("\n" + "=" * 80)
    print("📋 CONCLUSION")
    print("=" * 80)
    
    if result:
        print("✅ API accessible")
        if isinstance(result, dict) and 'ahadith' in result:
            ahadith = result['ahadith']
            if isinstance(ahadith, list):
                print("✅ Format JSON structuré exploitable")
                print("✅ Prêt pour harvesting")
            else:
                print("⚠️  Format HTML dans la réponse")
                print("❌ Nécessite parsing HTML ou API alternative")
        else:
            print("⚠️  Structure inattendue")
    else:
        print("❌ API non accessible ou erreur")
    
    print("\n💡 Recommandation:")
    if result and isinstance(result, dict) and 'ahadith' in result:
        ahadith = result['ahadith']
        if isinstance(ahadith, list):
            print("   → Utiliser cette méthode JSONP pour le harvesting")
        else:
            print("   → Utiliser API HadeethEnc (déjà testée et fonctionnelle)")
    else:
        print("   → Utiliser API HadeethEnc (alternative validée)")

if __name__ == "__main__":
    test_dorar_jsonp()