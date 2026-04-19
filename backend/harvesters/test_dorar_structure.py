"""
Test de l'API Dorar.net pour comprendre la structure des réponses
Avant de créer le harvester complet, on doit inspecter les données retournées
"""
import asyncio
import aiohttp
import json
from urllib.parse import quote

# Test avec un hadith célèbre
TEST_QUERIES = [
    "من كذب علي متعمدا",  # Hadith très connu
    "إنما الأعمال بالنيات",  # Premier hadith de Bukhari
    "بني الإسلام على خمس",  # Hadith des 5 piliers
]

DORAR_SEARCH = "https://dorar.net/dorar_api.json?skey={query}"
HEADERS = {
    "User-Agent": "Mizan-Research-Bot/1.0 (Salafi hadith verification; educational purpose)",
    "Accept": "application/json",
}

async def test_dorar_api():
    async with aiohttp.ClientSession() as session:
        for i, query in enumerate(TEST_QUERIES, 1):
            print(f"\n{'='*60}")
            print(f"TEST {i}/3 : {query[:30]}...")
            print('='*60)
            
            url = DORAR_SEARCH.format(query=quote(query))
            print(f"URL: {url}")
            
            try:
                async with session.get(url, headers=HEADERS, timeout=15) as r:
                    print(f"Status: {r.status}")
                    print(f"Content-Type: {r.headers.get('Content-Type')}")
                    
                    if r.status == 200:
                        try:
                            data = await r.json(content_type=None)
                            
                            # Sauvegarder la réponse brute
                            filename = f"dorar_test_{i}.json"
                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                            print(f"✅ Réponse sauvegardée dans {filename}")
                            
                            # Analyser la structure
                            print(f"\nStructure de la réponse:")
                            print(f"  Type: {type(data)}")
                            if isinstance(data, dict):
                                print(f"  Clés principales: {list(data.keys())}")
                                
                                # Explorer les résultats de hadiths
                                if 'ahadith' in data:
                                    ahadith = data['ahadith']
                                    print(f"\n  ahadith:")
                                    print(f"    Type: {type(ahadith)}")
                                    if isinstance(ahadith, dict):
                                        print(f"    Clés: {list(ahadith.keys())}")
                                        if 'result' in ahadith:
                                            results = ahadith['result']
                                            print(f"    Nombre de résultats: {len(results)}")
                                            if results:
                                                print(f"\n  Premier résultat:")
                                                first = results[0]
                                                for key, value in first.items():
                                                    val_preview = str(value)[:100] if value else "None"
                                                    print(f"    {key}: {val_preview}")
                        except json.JSONDecodeError as e:
                            print(f"❌ Erreur JSON: {e}")
                            text = await r.text()
                            print(f"Réponse brute (100 premiers chars): {text[:100]}")
                    else:
                        print(f"❌ Status non-200")
                        
            except Exception as e:
                print(f"❌ Erreur: {e}")
            
            # Pause entre requêtes
            if i < len(TEST_QUERIES):
                print("\nPause 2 secondes...")
                await asyncio.sleep(2)

if __name__ == "__main__":
    print("🔍 TEST DE L'API DORAR.NET")
    print("="*60)
    asyncio.run(test_dorar_api())
    print("\n✅ Tests terminés. Vérifiez les fichiers dorar_test_*.json")