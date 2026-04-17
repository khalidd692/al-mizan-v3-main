#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetcher HadeethEnc.com API pour AL-MĪZĀN V7.0
Récupère les hadiths avec explications savantes en français
"""

import aiohttp
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class HadeethEncFetcher:
    """Fetcher pour HadeethEnc.com API officielle"""
    
    BASE_URL = "https://hadeethenc.com/api/v1"
    
    # Mapping des catégories vers les zones Al-Mīzān
    CATEGORY_TO_ZONE = {
        3: 21,   # Al-'Aqîdah → Zone 21 (Aqîdah)
        4: 22,   # Fiqh → Zone 22 (Fiqh al-'Ibâdât)
        5: 31,   # Sîrah → Zone 31 (Manâqib et Sîrah)
        6: 27,   # Fadâ'il → Zone 27 (Fadâ'il)
        7: 28,   # Dhikr → Zone 28 (Dhikr et Du'â')
        8: 29,   # Zuhd → Zone 29 (Zuhd et Raqâ'iq)
    }
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.session:
            await self.session.close()
    
    async def fetch_languages(self) -> Optional[List[Dict[str, Any]]]:
        """Récupérer la liste des langues disponibles"""
        url = f"{self.BASE_URL}/languages/"
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            logger.error(f"Erreur fetch languages: {e}")
            return None
    
    async def fetch_categories_roots(self, language: str = 'fr') -> Optional[List[Dict[str, Any]]]:
        """Récupérer les catégories racines"""
        url = f"{self.BASE_URL}/categories/roots/?language={language}"
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            logger.error(f"Erreur fetch categories roots: {e}")
            return None
    
    async def fetch_categories_list(self, language: str = 'fr') -> Optional[List[Dict[str, Any]]]:
        """Récupérer toutes les catégories (hiérarchiques)"""
        url = f"{self.BASE_URL}/categories/list/?language={language}"
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            logger.error(f"Erreur fetch categories list: {e}")
            return None
    
    async def fetch_hadeeths_by_category(
        self, 
        category_id: int, 
        language: str = 'fr',
        page: int = 1,
        per_page: int = 20
    ) -> Optional[Dict[str, Any]]:
        """
        Récupérer les hadiths d'une catégorie
        
        Args:
            category_id: ID de la catégorie
            language: Code langue (fr, ar, en, etc.)
            page: Numéro de page
            per_page: Hadiths par page
            
        Returns:
            Dict avec metadata et data (liste de hadiths)
        """
        url = f"{self.BASE_URL}/hadeeths/list/?language={language}&category_id={category_id}&page={page}&per_page={per_page}"
        try:
            async with self.session.get(url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                return None
        except Exception as e:
            logger.error(f"Erreur fetch hadeeths category {category_id}: {e}")
            return None
    
    async def fetch_hadith_by_id(self, hadith_id: int, language: str = 'fr') -> Optional[Dict[str, Any]]:
        """
        Récupérer un hadith par son ID
        
        Args:
            hadith_id: ID du hadith
            language: Code langue
            
        Returns:
            Dict avec le hadith complet + explication
        """
        url = f"{self.BASE_URL}/hadeeths/one/?id={hadith_id}&language={language}"
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._normalize_hadith(data, hadith_id)
                elif response.status == 404:
                    logger.warning(f"Hadith non trouvé: ID {hadith_id}")
                    return None
                else:
                    logger.error(f"Erreur HTTP {response.status}: {url}")
                    return None
        except Exception as e:
            logger.error(f"Erreur fetch hadith {hadith_id}: {e}")
            return None
    
    async def fetch_all_hadeeths_from_category(
        self, 
        category_id: int, 
        language: str = 'fr',
        max_pages: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Récupérer tous les hadiths d'une catégorie (pagination automatique)
        
        Args:
            category_id: ID de la catégorie
            language: Code langue
            max_pages: Nombre maximum de pages à récupérer
            
        Returns:
            Liste complète de hadiths
        """
        all_hadeeths = []
        page = 1
        
        while page <= max_pages:
            result = await self.fetch_hadeeths_by_category(category_id, language, page)
            if not result or 'data' not in result:
                break
            
            hadeeths = result['data']
            if not hadeeths:
                break
            
            all_hadeeths.extend([self._normalize_hadith(h, h.get('id')) for h in hadeeths])
            
            # Vérifier s'il y a d'autres pages
            metadata = result.get('metadata', {})
            if page >= metadata.get('last_page', 1):
                break
            
            page += 1
            await asyncio.sleep(0.5)  # Rate limiting respectueux
        
        logger.info(f"✅ {len(all_hadeeths)} hadiths récupérés de la catégorie {category_id}")
        return all_hadeeths
    
    def _normalize_hadith(self, data: Dict, hadith_id: int) -> Dict[str, Any]:
        """Normaliser un hadith HadeethEnc vers le schéma V7"""
        
        # Déterminer la zone Al-Mīzān depuis les catégories
        categories = data.get('categories', [])
        zone_id = 11  # Grading par défaut
        for cat_id in categories:
            if cat_id in self.CATEGORY_TO_ZONE:
                zone_id = self.CATEGORY_TO_ZONE[cat_id]
                break
        
        return {
            'id': f"hadeethenc-{hadith_id}",
            'hadeethenc_id': hadith_id,
            'zone_id': zone_id,
            'fr_text': data.get('hadeeth', ''),
            'fr_explanation': data.get('explanation', ''),
            'fr_source': 'hadeethenc',
            'fr_summary': data.get('title', ''),
            'source_api': 'hadeethenc',
            'source_url': f"https://hadeethenc.com/fr/browse/hadith/{hadith_id}",
            'source_data_license': 'conditions',
            'attribution': data.get('attribution', ''),
            'hints': data.get('hints', []),
            'categories': categories,
            'translations': data.get('translations', []),
            'fetched_at': datetime.now().isoformat(),
            'conditions': [
                'Aucune modification du contenu',
                'Référence obligatoire à HadeethEnc.com',
                'Usage commercial interdit sans autorisation'
            ]
        }
    
    def get_zone_for_category(self, category_id: int) -> int:
        """Obtenir la zone Al-Mīzān correspondant à une catégorie HadeethEnc"""
        return self.CATEGORY_TO_ZONE.get(category_id, 11)

async def test_fetcher():
    """Test du fetcher"""
    print("=== TEST HADEETHENC FETCHER ===\n")
    
    async with HadeethEncFetcher() as fetcher:
        # Test 1: Langues disponibles
        print("Test 1: Langues disponibles")
        languages = await fetcher.fetch_languages()
        if languages:
            fr_lang = next((l for l in languages if l.get('code') == 'fr'), None)
            if fr_lang:
                print(f"✅ Français disponible: {fr_lang.get('native')}")
        
        # Test 2: Catégories racines
        print("\nTest 2: Catégories racines en français")
        categories = await fetcher.fetch_categories_roots('fr')
        if categories:
            print(f"✅ {len(categories)} catégories racines")
            for cat in categories[:3]:
                print(f"   - {cat.get('title')}")
        
        # Test 3: Hadith individuel
        print("\nTest 3: Hadith ID 1")
        hadith = await fetcher.fetch_hadith_by_id(1, 'fr')
        if hadith:
            print(f"✅ Récupéré: {hadith['fr_summary']}")
            print(f"   Zone Al-Mīzān: {hadith['zone_id']}")
            print(f"   Explication: {hadith['fr_explanation'][:100]}...")
        
        # Test 4: Hadiths d'une catégorie
        print("\nTest 4: Hadiths de la catégorie Aqîdah (ID 3)")
        result = await fetcher.fetch_hadeeths_by_category(3, 'fr', page=1, per_page=5)
        if result and 'data' in result:
            print(f"✅ {len(result['data'])} hadiths récupérés")
            print(f"   Metadata: {result.get('metadata')}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_fetcher())