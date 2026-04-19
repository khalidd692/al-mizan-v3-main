"""
Script de test pour l'API des Outils de Médine
Valide tous les endpoints créés
"""

import asyncio
import aiohttp
from typing import Dict
import json

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1/medine"

class MedineAPITester:
    """Testeur pour l'API des Outils de Médine"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.results = []
    
    async def test_health_check(self):
        """Test 1: Health Check"""
        print("\n" + "="*60)
        print("TEST 1: Health Check")
        print("="*60)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.base_url}/health") as response:
                    data = await response.json()
                    
                    print(f"Status: {response.status}")
                    print(f"Résultat: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    
                    self.results.append({
                        "test": "Health Check",
                        "status": "✅ PASS" if data.get("success") else "❌ FAIL",
                        "details": data
                    })
            except Exception as e:
                print(f"❌ Erreur: {e}")
                self.results.append({
                    "test": "Health Check",
                    "status": "❌ FAIL",
                    "error": str(e)
                })
    
    async def test_narrator_analysis(self):
        """Test 2: Analyse d'un narrateur"""
        print("\n" + "="*60)
        print("TEST 2: Analyse d'un Narrateur (Abu Hurayra)")
        print("="*60)
        
        narrator = "أبو هريرة"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/narrator/{narrator}",
                    params={"include_salafi_opinions": True}
                ) as response:
                    data = await response.json()
                    
                    print(f"Status: {response.status}")
                    print(f"Narrateur: {narrator}")
                    
                    if data.get("success"):
                        narrator_data = data.get("data", {})
                        print(f"Nom complet: {narrator_data.get('full_name', 'N/A')}")
                        print(f"Nombre d'avis Jarh wa Ta'dil: {len(narrator_data.get('jarh_tadil_opinions', []))}")
                        print(f"Score de fiabilité: {narrator_data.get('reliability_score', 'N/A')}")
                    
                    self.results.append({
                        "test": "Narrator Analysis",
                        "status": "✅ PASS" if data.get("success") else "❌ FAIL",
                        "details": data
                    })
            except Exception as e:
                print(f"❌ Erreur: {e}")
                self.results.append({
                    "test": "Narrator Analysis",
                    "status": "❌ FAIL",
                    "error": str(e)
                })
    
    async def test_matn_verification(self):
        """Test 3: Vérification du Matn"""
        print("\n" + "="*60)
        print("TEST 3: Vérification du Matn")
        print("="*60)
        
        hadith_text = "إنما الأعمال بالنيات"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_url}/verify-matn",
                    params={
                        "hadith_text": hadith_text,
                        "detect_variants": True
                    }
                ) as response:
                    data = await response.json()
                    
                    print(f"Status: {response.status}")
                    print(f"Texte recherché: {hadith_text}")
                    
                    if data.get("success"):
                        matn_data = data.get("data", {})
                        print(f"Texte normalisé: {matn_data.get('normalized_text', 'N/A')[:100]}...")
                        print(f"Nombre de variantes: {len(matn_data.get('variants', []))}")
                        print(f"Confiance: {matn_data.get('confidence', 'N/A')}")
                    
                    self.results.append({
                        "test": "Matn Verification",
                        "status": "✅ PASS" if data.get("success") else "❌ FAIL",
                        "details": data
                    })
            except Exception as e:
                print(f"❌ Erreur: {e}")
                self.results.append({
                    "test": "Matn Verification",
                    "status": "❌ FAIL",
                    "error": str(e)
                })
    
    async def test_get_hadith(self):
        """Test 4: Récupération d'un hadith"""
        print("\n" + "="*60)
        print("TEST 4: Récupération Hadith (Bukhari #1)")
        print("="*60)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/hadith/bukhari/1",
                    params={"include_edition": True}
                ) as response:
                    data = await response.json()
                    
                    print(f"Status: {response.status}")
                    
                    if data.get("success"):
                        hadith_data = data.get("data", {})
                        print(f"Texte: {hadith_data.get('text', 'N/A')[:100]}...")
                        edition = hadith_data.get('edition', {})
                        print(f"Édition: {edition.get('publisher', 'N/A')}")
                        print(f"Année: {edition.get('year_hijri', 'N/A')}هـ")
                    
                    self.results.append({
                        "test": "Get Hadith",
                        "status": "✅ PASS" if data.get("success") else "❌ FAIL",
                        "details": data
                    })
            except Exception as e:
                print(f"❌ Erreur: {e}")
                self.results.append({
                    "test": "Get Hadith",
                    "status": "❌ FAIL",
                    "error": str(e)
                })
    
    async def test_get_sharh(self):
        """Test 5: Récupération d'un commentaire"""
        print("\n" + "="*60)
        print("TEST 5: Récupération Sharh (Fath al-Bari)")
        print("="*60)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/sharh/bukhari/1",
                    params={
                        "sharh_book": "fath_al_bari",
                        "include_key_points": True
                    }
                ) as response:
                    data = await response.json()
                    
                    print(f"Status: {response.status}")
                    
                    if data.get("success"):
                        sharh_data = data.get("data", {})
                        print(f"Livre: {sharh_data.get('book', 'N/A')}")
                        print(f"Auteur: {sharh_data.get('author', 'N/A')}")
                        print(f"Volume: {sharh_data.get('volume', 'N/A')}, Page: {sharh_data.get('page', 'N/A')}")
                        print(f"Points clés: {len(sharh_data.get('key_points', []))}")
                    
                    self.results.append({
                        "test": "Get Sharh",
                        "status": "✅ PASS" if data.get("success") else "❌ FAIL",
                        "details": data
                    })
            except Exception as e:
                print(f"❌ Erreur: {e}")
                self.results.append({
                    "test": "Get Sharh",
                    "status": "❌ FAIL",
                    "error": str(e)
                })
    
    async def test_available_sharh_books(self):
        """Test 6: Liste des livres de Sharh"""
        print("\n" + "="*60)
        print("TEST 6: Liste des Livres de Sharh Disponibles")
        print("="*60)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.base_url}/sharh/available-books") as response:
                    data = await response.json()
                    
                    print(f"Status: {response.status}")
                    
                    if data.get("success"):
                        books = data.get("data", [])
                        print(f"Nombre de livres: {len(books)}")
                        for book in books:
                            print(f"  - {book.get('name')} ({book.get('author')})")
                    
                    self.results.append({
                        "test": "Available Sharh Books",
                        "status": "✅ PASS" if data.get("success") else "❌ FAIL",
                        "details": data
                    })
            except Exception as e:
                print(f"❌ Erreur: {e}")
                self.results.append({
                    "test": "Available Sharh Books",
                    "status": "❌ FAIL",
                    "error": str(e)
                })
    
    async def test_search_sharh(self):
        """Test 7: Recherche dans un livre de Sharh"""
        print("\n" + "="*60)
        print("TEST 7: Recherche dans Fath al-Bari")
        print("="*60)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/sharh/search",
                    params={
                        "keyword": "النية",
                        "sharh_book": "fath_al_bari",
                        "limit": 5
                    }
                ) as response:
                    data = await response.json()
                    
                    print(f"Status: {response.status}")
                    
                    if data.get("success"):
                        results = data.get("data", [])
                        print(f"Résultats trouvés: {len(results)}")
                        for i, result in enumerate(results[:3], 1):
                            print(f"\n  Résultat {i}:")
                            print(f"    Titre: {result.get('title', 'N/A')}")
                            print(f"    Volume: {result.get('volume', 'N/A')}, Page: {result.get('page', 'N/A')}")
                    
                    self.results.append({
                        "test": "Search Sharh",
                        "status": "✅ PASS" if data.get("success") else "❌ FAIL",
                        "details": data
                    })
            except Exception as e:
                print(f"❌ Erreur: {e}")
                self.results.append({
                    "test": "Search Sharh",
                    "status": "❌ FAIL",
                    "error": str(e)
                })
    
    async def test_extract_aqidah(self):
        """Test 8: Extraction Aqidah"""
        print("\n" + "="*60)
        print("TEST 8: Extraction Points de Aqidah")
        print("="*60)
        
        hadith_text = "حديث الجارية"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_url}/aqidah/extract",
                    params={
                        "hadith_text": hadith_text,
                        "include_salaf_positions": True
                    }
                ) as response:
                    data = await response.json()
                    
                    print(f"Status: {response.status}")
                    
                    if data.get("success"):
                        aqidah_data = data.get("data", {})
                        print(f"Points de Aqidah: {len(aqidah_data.get('aqidah_points', []))}")
                        print(f"Positions des Salaf: {len(aqidah_data.get('salaf_positions', []))}")
                    
                    self.results.append({
                        "test": "Extract Aqidah",
                        "status": "✅ PASS" if data.get("success") else "❌ FAIL",
                        "details": data
                    })
            except Exception as e:
                print(f"❌ Erreur: {e}")
                self.results.append({
                    "test": "Extract Aqidah",
                    "status": "❌ FAIL",
                    "error": str(e)
                })
    
    async def test_complete_analysis(self):
        """Test 9: Analyse complète"""
        print("\n" + "="*60)
        print("TEST 9: Analyse Complète d'un Hadith")
        print("="*60)
        
        hadith_text = "إنما الأعمال بالنيات"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_url}/analyze-complete",
                    params={
                        "hadith_text": hadith_text,
                        "book": "bukhari",
                        "hadith_number": 1
                    }
                ) as response:
                    data = await response.json()
                    
                    print(f"Status: {response.status}")
                    
                    if data.get("success"):
                        analysis = data.get("data", {})
                        print(f"Vérification Matn: {'✅' if analysis.get('matn_verification') else '❌'}")
                        print(f"Sharh: {'✅' if analysis.get('sharh') else '❌'}")
                        print(f"Aqidah: {'✅' if analysis.get('aqidah') else '❌'}")
                    
                    self.results.append({
                        "test": "Complete Analysis",
                        "status": "✅ PASS" if data.get("success") else "❌ FAIL",
                        "details": data
                    })
            except Exception as e:
                print(f"❌ Erreur: {e}")
                self.results.append({
                    "test": "Complete Analysis",
                    "status": "❌ FAIL",
                    "error": str(e)
                })
    
    def print_summary(self):
        """Affiche le résumé des tests"""
        print("\n" + "="*60)
        print("RÉSUMÉ DES TESTS")
        print("="*60)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if "✅" in r["status"])
        failed = total - passed
        
        print(f"\nTotal: {total} tests")
        print(f"✅ Réussis: {passed}")
        print(f"❌ Échoués: {failed}")
        print(f"Taux de réussite: {(passed/total*100):.1f}%")
        
        print("\nDétails:")
        for result in self.results:
            print(f"  {result['status']} - {result['test']}")
    
    async def run_all_tests(self):
        """Lance tous les tests"""
        print("\n🚀 DÉMARRAGE DES TESTS DE L'API OUTILS DE MÉDINE")
        print("="*60)
        
        await self.test_health_check()
        await self.test_narrator_analysis()
        await self.test_matn_verification()
        await self.test_get_hadith()
        await self.test_get_sharh()
        await self.test_available_sharh_books()
        await self.test_search_sharh()
        await self.test_extract_aqidah()
        await self.test_complete_analysis()
        
        self.print_summary()

async def main():
    """Point d'entrée principal"""
    tester = MedineAPITester()
    await tester.run_all_tests()
    
    print("\n✅ Tests terminés!")
    print("\nPour lancer l'API:")
    print("  cd backend")
    print("  uvicorn main:app --reload")

if __name__ == "__main__":
    asyncio.run(main())