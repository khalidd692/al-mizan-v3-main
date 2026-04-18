#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test des APIs Tier 3 pour sélection sources primaires
"""

import requests
import json
import time
from typing import Dict, List, Optional

class APITester:
    """Testeur d'APIs hadith"""
    
    def __init__(self):
        self.results = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Al-Mizan-Harvester/7.0',
            'Accept': 'application/json'
        })
    
    def test_api(self, name: str, url: str, timeout: int = 10) -> Dict:
        """
        Test une API et retourne les résultats
        
        Args:
            name: Nom de l'API
            url: URL de test
            timeout: Timeout en secondes
        
        Returns:
            Dict avec résultats du test
        """
        result = {
            'name': name,
            'url': url,
            'accessible': False,
            'response_time': None,
            'status_code': None,
            'format': None,
            'sample_data': None,
            'error': None
        }
        
        try:
            start_time = time.time()
            response = self.session.get(url, timeout=timeout)
            response_time = time.time() - start_time
            
            result['accessible'] = True
            result['response_time'] = round(response_time, 2)
            result['status_code'] = response.status_code
            
            if response.status_code == 200:
                # Tenter de parser le JSON
                try:
                    data = response.json()
                    result['format'] = 'JSON'
                    result['sample_data'] = self._extract_sample(data)
                except:
                    result['format'] = 'HTML/Text'
                    result['sample_data'] = response.text[:200]
            else:
                result['error'] = f"HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            result['error'] = "Timeout"
        except requests.exceptions.ConnectionError:
            result['error'] = "Connection Error"
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _extract_sample(self, data: any) -> Dict:
        """Extrait un échantillon des données"""
        sample = {
            'type': type(data).__name__,
            'keys': None,
            'count': None,
            'first_item': None
        }
        
        if isinstance(data, dict):
            sample['keys'] = list(data.keys())[:5]
            if data:
                first_key = list(data.keys())[0]
                sample['first_item'] = {first_key: data[first_key]}
        elif isinstance(data, list):
            sample['count'] = len(data)
            if data:
                sample['first_item'] = data[0]
        
        return sample
    
    def test_all_apis(self):
        """Test toutes les APIs Tier 3"""
        
        apis = [
            # Sunnah.com
            {
                'name': 'Sunnah.com - Collections',
                'url': 'https://api.sunnah.com/v1/collections'
            },
            {
                'name': 'Sunnah.com - Hadith',
                'url': 'https://api.sunnah.com/v1/hadiths/bukhari/1'
            },
            
            # Hadith Gading
            {
                'name': 'Hadith Gading - Books',
                'url': 'https://api.hadith.gading.dev/books'
            },
            {
                'name': 'Hadith Gading - Bukhari',
                'url': 'https://api.hadith.gading.dev/books/bukhari?range=1-5'
            },
            
            # CDN JSDelivr
            {
                'name': 'JSDelivr - Editions',
                'url': 'https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions.json'
            },
            {
                'name': 'JSDelivr - Bukhari',
                'url': 'https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/ara-bukhari.json'
            },
            
            # QuranHadith
            {
                'name': 'QuranHadith - API',
                'url': 'https://quranhadith.com/api/hadith'
            },
            
            # Random Hadith
            {
                'name': 'Random Hadith - API',
                'url': 'https://random-hadith-generator.vercel.app/api/hadiths'
            },
            
            # Sunnah Intranet (peut nécessiter auth)
            {
                'name': 'Sunnah Intranet',
                'url': 'https://hadith.intranet.sunnah.com/api'
            }
        ]
        
        print("=" * 80)
        print("🔍 TEST DES APIs TIER 3")
        print("=" * 80)
        print()
        
        for api in apis:
            print(f"📡 Test: {api['name']}")
            print(f"   URL: {api['url']}")
            
            result = self.test_api(api['name'], api['url'])
            self.results[api['name']] = result
            
            if result['accessible']:
                print(f"   ✅ Accessible")
                print(f"   ⏱️  Temps: {result['response_time']}s")
                print(f"   📄 Format: {result['format']}")
                
                if result['sample_data']:
                    print(f"   📊 Échantillon:")
                    print(f"      Type: {result['sample_data'].get('type')}")
                    if result['sample_data'].get('keys'):
                        print(f"      Clés: {result['sample_data']['keys']}")
                    if result['sample_data'].get('count'):
                        print(f"      Nombre: {result['sample_data']['count']}")
            else:
                print(f"   ❌ Erreur: {result['error']}")
            
            print()
            time.sleep(1)  # Rate limiting
        
        self._print_summary()
    
    def _print_summary(self):
        """Affiche le résumé des tests"""
        print("=" * 80)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 80)
        print()
        
        accessible = [r for r in self.results.values() if r['accessible']]
        json_apis = [r for r in accessible if r['format'] == 'JSON']
        fast_apis = [r for r in accessible if r['response_time'] and r['response_time'] < 2]
        
        print(f"✅ APIs accessibles: {len(accessible)}/{len(self.results)}")
        print(f"📄 Format JSON: {len(json_apis)}/{len(accessible)}")
        print(f"⚡ Rapides (<2s): {len(fast_apis)}/{len(accessible)}")
        print()
        
        if json_apis:
            print("🎯 APIs RECOMMANDÉES (JSON + Rapides):")
            for result in json_apis:
                if result['response_time'] and result['response_time'] < 2:
                    print(f"   ✅ {result['name']}")
                    print(f"      Temps: {result['response_time']}s")
                    print(f"      URL: {result['url']}")
                    print()
        
        print("=" * 80)
        print("💡 RECOMMANDATIONS")
        print("=" * 80)
        
        if len(json_apis) >= 3:
            print("✅ Suffisamment d'APIs validées pour harvesting massif")
            print("📋 Prochaine étape:")
            print("   1. Analyser structure détaillée des APIs validées")
            print("   2. Créer connecteurs pour top 3 APIs")
            print("   3. Lancer extraction test (100 hadiths)")
        else:
            print("⚠️  Peu d'APIs validées")
            print("💡 Options:")
            print("   1. Utiliser HadeethEnc comme source principale")
            print("   2. Explorer APIs Tier 2 (Shamela, IslamWeb)")
            print("   3. Développer scraper pour sources web")
        
        # Sauvegarder résultats
        self._save_results()
    
    def _save_results(self):
        """Sauvegarde les résultats en JSON"""
        output_file = 'output/api_tier3_test_results.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 Résultats sauvegardés: {output_file}")

def main():
    """Point d'entrée principal"""
    tester = APITester()
    tester.test_all_apis()

if __name__ == "__main__":
    main()