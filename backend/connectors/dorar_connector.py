"""
Connecteur API Dorar.net pour Al-Mīzān v7.0
Utilise les extensions MCP (Tavily + Browser) pour extraction
"""

import asyncio
import json
import re
from typing import Dict, List, Optional
from datetime import datetime

class DorarConnector:
    """Connecteur pour l'API Dorar.net"""
    
    BASE_URL = "https://dorar.net"
    API_ENDPOINT = "/api/hadith"
    
    # Mapping des livres vers leurs IDs Dorar
    BOOK_IDS = {
        "bukhari": 6216,
        "muslim": 3088,
        "abu_dawud": 1666,
        "tirmidhi": 1669,
        "nasai": 1694,
        "ibn_majah": 1670,
        "musnad_ahmad": 1668
    }
    
    def __init__(self):
        self.session_stats = {
            "requests": 0,
            "success": 0,
            "errors": 0,
            "start_time": None
        }
    
    async def fetch_hadith_by_id(self, hadith_id: int) -> Optional[Dict]:
        """
        Récupère un hadith par son ID Dorar
        En production, utiliser use_mcp_tool avec browser_navigate
        """
        self.session_stats["requests"] += 1
        
        try:
            # URL du hadith
            url = f"{self.BASE_URL}/hadith/{hadith_id}"
            
            # Ici, en production, utiliser:
            # result = await use_mcp_tool("browser_navigate", {"url": url})
            # puis browser_snapshot pour extraire le contenu
            
            # Pour l'instant, simulation avec structure réelle Dorar
            hadith_data = await self._simulate_dorar_response(hadith_id)
            
            if hadith_data:
                self.session_stats["success"] += 1
                return self._parse_dorar_hadith(hadith_data)
            
            return None
            
        except Exception as e:
            self.session_stats["errors"] += 1
            print(f"❌ Erreur fetch hadith {hadith_id}: {e}")
            return None
    
    async def fetch_book_hadiths(self, book_key: str, start: int = 1, count: int = 100) -> List[Dict]:
        """
        Récupère une série de hadiths d'un livre spécifique
        """
        book_id = self.BOOK_IDS.get(book_key)
        if not book_id:
            raise ValueError(f"Livre inconnu: {book_key}")
        
        print(f"\n📖 Extraction {book_key} (ID Dorar: {book_id})")
        print(f"   Range: {start} → {start + count}")
        
        hadiths = []
        for i in range(count):
            hadith_num = start + i
            
            # Construire l'URL de recherche Dorar
            # Format: /hadith/search?skey=<book_id>&page=<num>
            hadith = await self.fetch_hadith_by_id(hadith_num)
            
            if hadith:
                hadith["book_key"] = book_key
                hadith["book_id_dorar"] = book_id
                hadiths.append(hadith)
            
            # Progress
            if (i + 1) % 20 == 0:
                print(f"   ✓ {i+1}/{count} hadiths extraits")
            
            # Rate limiting
            await asyncio.sleep(2.0)
        
        return hadiths
    
    async def _simulate_dorar_response(self, hadith_id: int) -> Dict:
        """
        Simule une réponse Dorar (à remplacer par vraie extraction MCP)
        Structure basée sur l'API réelle de Dorar
        """
        # Simulation de données réalistes
        grades = ["Sahih", "Hasan", "Da'if"]
        grade = grades[hadith_id % 3]
        
        muhaddithin = [
            {"name": "الألباني", "id": 1420},
            {"name": "ابن باز", "id": 1421},
            {"name": "ابن عثيمين", "id": 1422}
        ]
        muhaddith = muhaddithin[hadith_id % 3]
        
        return {
            "id": hadith_id,
            "matn": f"متن الحديث رقم {hadith_id} - هذا نص تجريبي للحديث",
            "rawi": "أبو هريرة رضي الله عنه",
            "grade": grade,
            "graded_by": muhaddith["name"],
            "graded_by_id": muhaddith["id"],
            "grade_explanation": f"حكم {muhaddith['name']} على هذا الحديث بأنه {grade}",
            "book_name": "صحيح البخاري",
            "hadith_number": str(hadith_id),
            "takhrij": f"رواه البخاري في كتاب الإيمان، باب {hadith_id}",
            "has_similar": hadith_id % 5 == 0,
            "has_sharh": hadith_id % 3 == 0
        }
    
    def _parse_dorar_hadith(self, raw_data: Dict) -> Dict:
        """
        Parse les données brutes de Dorar vers le format Al-Mīzān
        """
        return {
            "hadith_id_dorar": str(raw_data.get("id", "")),
            "ar_text": raw_data.get("matn", ""),
            "ar_narrator": raw_data.get("rawi", ""),
            "grade_primary": raw_data.get("grade", "unknown"),
            "grade_by_mohdith": raw_data.get("graded_by", ""),
            "grade_by_mohdith_id": raw_data.get("graded_by_id"),
            "grade_explanation": raw_data.get("grade_explanation", ""),
            "book_name_ar": raw_data.get("book_name", ""),
            "hadith_number": raw_data.get("hadith_number", ""),
            "takhrij": raw_data.get("takhrij", ""),
            "has_similar": 1 if raw_data.get("has_similar") else 0,
            "has_sharh": 1 if raw_data.get("has_sharh") else 0,
            "source_api": "dorar",
            "source_url": f"{self.BASE_URL}/hadith/{raw_data.get('id', '')}",
            "source_data_license": "conditions",
            "zone_id": 2,  # Zone Matn par défaut
            "zone_label": "Matn"
        }
    
    async def search_by_text(self, query: str, max_results: int = 50) -> List[Dict]:
        """
        Recherche de hadiths par texte
        Utilise Tavily MCP pour recherche intelligente
        """
        print(f"\n🔍 Recherche Dorar: '{query}'")
        
        # En production, utiliser:
        # results = await use_mcp_tool("tavily_search", {
        #     "query": f"site:dorar.net {query}",
        #     "max_results": max_results
        # })
        
        # Simulation
        await asyncio.sleep(1)
        return []
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques de session"""
        duration = None
        if self.session_stats["start_time"]:
            duration = (datetime.now() - self.session_stats["start_time"]).total_seconds()
        
        return {
            **self.session_stats,
            "duration_seconds": duration,
            "success_rate": (
                self.session_stats["success"] / max(self.session_stats["requests"], 1) * 100
            )
        }

async def test_connector():
    """Test du connecteur"""
    print("="*70)
    print("🧪 TEST CONNECTEUR DORAR.NET")
    print("="*70)
    
    connector = DorarConnector()
    connector.session_stats["start_time"] = datetime.now()
    
    # Test 1: Fetch hadith unique
    print("\n📝 Test 1: Extraction hadith unique")
    hadith = await connector.fetch_hadith_by_id(1)
    if hadith:
        print(f"✅ Hadith extrait: {hadith['hadith_id_dorar']}")
        print(f"   Grade: {hadith['grade_primary']}")
        print(f"   Livre: {hadith['book_name_ar']}")
    
    # Test 2: Extraction série
    print("\n📚 Test 2: Extraction série (20 hadiths)")
    hadiths = await connector.fetch_book_hadiths("bukhari", start=1, count=20)
    print(f"✅ {len(hadiths)} hadiths extraits")
    
    # Stats
    print("\n📊 STATISTIQUES")
    stats = connector.get_stats()
    print(f"   Requêtes: {stats['requests']}")
    print(f"   Succès: {stats['success']}")
    print(f"   Erreurs: {stats['errors']}")
    print(f"   Taux de succès: {stats['success_rate']:.1f}%")
    print(f"   Durée: {stats['duration_seconds']:.2f}s")

if __name__ == "__main__":
    asyncio.run(test_connector())