#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetcher fawazahmed0/hadith-api pour AL-MĪZĀN V7.0
Récupère les hadiths en français depuis le CDN JSDelivr
"""

import aiohttp
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class FawazahmedFetcher:
    """Fetcher pour fawazahmed0/hadith-api via CDN JSDelivr"""
    
    # Pin de version OBLIGATOIRE
    CDN_BASE = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1"
    
    # Mapping des livres français
    BOOKS_FR = {
        'bukhari': 'fra-bukhari',
        'muslim': 'fra-muslim',
        'abudawud': 'fra-abudawud',
        'ibnmajah': 'fra-ibnmajah',
        'malik': 'fra-malik',
        'dehlawi': 'fra-dehlawi',
        'nawawi': 'fra-nawawi'
    }
    
    # Mapping des livres arabes
    BOOKS_AR = {
        'bukhari': 'ara-bukhari',
        'muslim': 'ara-muslim',
        'abudawud': 'ara-abudawud',
        'nasai': 'ara-nasai',
        'tirmidhi': 'ara-tirmidhi',
        'ibnmajah': 'ara-ibnmajah',
        'malik': 'ara-malik',
        'ahmad': 'ara-ahmad'
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
    
    async def fetch_hadith_fr(self, book: str, hadith_number: int) -> Optional[Dict[str, Any]]:
        """
        Récupérer un hadith en français
        
        Args:
            book: Nom du livre ('bukhari', 'muslim', etc.)
            hadith_number: Numéro du hadith
            
        Returns:
            Dict avec le hadith ou None si erreur
        """
        if book not in self.BOOKS_FR:
            logger.error(f"Livre non supporté: {book}")
            return None
        
        book_code = self.BOOKS_FR[book]
        url = f"{self.CDN_BASE}/editions/{book_code}/{hadith_number}.json"
        
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._normalize_hadith_fr(data, book, hadith_number)
                elif response.status == 404:
                    logger.warning(f"Hadith non trouvé: {book} #{hadith_number}")
                    return None
                else:
                    logger.error(f"Erreur HTTP {response.status}: {url}")
                    return None
        except asyncio.TimeoutError:
            logger.error(f"Timeout: {url}")
            return None
        except Exception as e:
            logger.error(f"Erreur fetch {url}: {e}")
            return None
    
    async def fetch_hadith_ar(self, book: str, hadith_number: int) -> Optional[Dict[str, Any]]:
        """
        Récupérer un hadith en arabe
        
        Args:
            book: Nom du livre ('bukhari', 'muslim', etc.)
            hadith_number: Numéro du hadith
            
        Returns:
            Dict avec le hadith ou None si erreur
        """
        if book not in self.BOOKS_AR:
            logger.error(f"Livre arabe non supporté: {book}")
            return None
        
        book_code = self.BOOKS_AR[book]
        url = f"{self.CDN_BASE}/editions/{book_code}/{hadith_number}.json"
        
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._normalize_hadith_ar(data, book, hadith_number)
                elif response.status == 404:
                    logger.warning(f"Hadith arabe non trouvé: {book} #{hadith_number}")
                    return None
                else:
                    logger.error(f"Erreur HTTP {response.status}: {url}")
                    return None
        except Exception as e:
            logger.error(f"Erreur fetch arabe {url}: {e}")
            return None
    
    async def fetch_book_section_fr(self, book: str, section: int) -> Optional[List[Dict[str, Any]]]:
        """
        Récupérer une section complète d'un livre en français
        
        Args:
            book: Nom du livre
            section: Numéro de section
            
        Returns:
            Liste de hadiths ou None
        """
        if book not in self.BOOKS_FR:
            return None
        
        book_code = self.BOOKS_FR[book]
        url = f"{self.CDN_BASE}/editions/{book_code}/sections/{section}.json"
        
        try:
            async with self.session.get(url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    return [self._normalize_hadith_fr(h, book, h.get('hadithnumber', 0)) 
                            for h in data.get('hadiths', [])]
                else:
                    return None
        except Exception as e:
            logger.error(f"Erreur fetch section {url}: {e}")
            return None
    
    async def fetch_complete_book_fr(self, book: str) -> Optional[List[Dict[str, Any]]]:
        """
        Récupérer un livre complet en français
        
        Args:
            book: Nom du livre
            
        Returns:
            Liste complète de hadiths ou None
        """
        if book not in self.BOOKS_FR:
            return None
        
        book_code = self.BOOKS_FR[book]
        url = f"{self.CDN_BASE}/editions/{book_code}.json"
        
        try:
            logger.info(f"Téléchargement livre complet: {book_code}")
            async with self.session.get(url, timeout=60) as response:
                if response.status == 200:
                    data = await response.json()
                    hadiths = data.get('hadiths', [])
                    logger.info(f"✅ {len(hadiths)} hadiths récupérés pour {book}")
                    return [self._normalize_hadith_fr(h, book, h.get('hadithnumber', idx+1)) 
                            for idx, h in enumerate(hadiths)]
                else:
                    logger.error(f"Erreur HTTP {response.status}: {url}")
                    return None
        except Exception as e:
            logger.error(f"Erreur fetch livre complet {url}: {e}")
            return None
    
    def _normalize_hadith_fr(self, data: Dict, book: str, hadith_number: int) -> Dict[str, Any]:
        """Normaliser un hadith français vers le schéma V7"""
        return {
            'id': f"fawaz-{book}-{hadith_number}",
            'book': book,
            'book_name_fr': self._get_book_name_fr(book),
            'hadith_number': str(hadith_number),
            'fr_text': data.get('text', data.get('hadith', '')),
            'fr_source': 'fawazahmed0',
            'source_api': 'fawazahmed0',
            'source_url': f"{self.CDN_BASE}/editions/{self.BOOKS_FR[book]}/{hadith_number}.json",
            'source_version_pin': '@1',
            'source_data_license': 'unknown',
            'grades': data.get('grades', []),
            'reference': data.get('reference', {}),
            'fetched_at': datetime.now().isoformat()
        }
    
    def _normalize_hadith_ar(self, data: Dict, book: str, hadith_number: int) -> Dict[str, Any]:
        """Normaliser un hadith arabe vers le schéma V7"""
        return {
            'id': f"fawaz-ar-{book}-{hadith_number}",
            'book': book,
            'book_name_ar': self._get_book_name_ar(book),
            'hadith_number': str(hadith_number),
            'ar_text': data.get('text', data.get('hadith', '')),
            'source_api': 'fawazahmed0',
            'source_url': f"{self.CDN_BASE}/editions/{self.BOOKS_AR[book]}/{hadith_number}.json",
            'source_version_pin': '@1',
            'grades': data.get('grades', []),
            'reference': data.get('reference', {}),
            'fetched_at': datetime.now().isoformat()
        }
    
    def _get_book_name_fr(self, book: str) -> str:
        """Obtenir le nom français du livre"""
        names = {
            'bukhari': 'Sahih al-Bukhâri',
            'muslim': 'Sahih Muslim',
            'abudawud': 'Sunan Abû Dâwûd',
            'ibnmajah': 'Sunan Ibn Mâjah',
            'malik': 'Muwatta\' Mâlik',
            'dehlawi': '40 Hadith Dehlawî',
            'nawawi': '40 Hadith An-Nawawî'
        }
        return names.get(book, book)
    
    def _get_book_name_ar(self, book: str) -> str:
        """Obtenir le nom arabe du livre"""
        names = {
            'bukhari': 'صحيح البخاري',
            'muslim': 'صحيح مسلم',
            'abudawud': 'سنن أبي داود',
            'nasai': 'سنن النسائي',
            'tirmidhi': 'سنن الترمذي',
            'ibnmajah': 'سنن ابن ماجه',
            'malik': 'موطأ مالك',
            'ahmad': 'مسند أحمد'
        }
        return names.get(book, book)

async def test_fetcher():
    """Test du fetcher"""
    print("=== TEST FAWAZAHMED0 FETCHER ===\n")
    
    async with FawazahmedFetcher() as fetcher:
        # Test 1: Hadith individuel en français
        print("Test 1: Hadith Bukhâri #1 (français)")
        hadith_fr = await fetcher.fetch_hadith_fr('bukhari', 1)
        if hadith_fr:
            print(f"✅ Récupéré: {hadith_fr['book_name_fr']}")
            print(f"   Texte: {hadith_fr['fr_text'][:100]}...")
        else:
            print("❌ Échec")
        
        # Test 2: Hadith individuel en arabe
        print("\nTest 2: Hadith Bukhâri #1 (arabe)")
        hadith_ar = await fetcher.fetch_hadith_ar('bukhari', 1)
        if hadith_ar:
            print(f"✅ Récupéré: {hadith_ar['book_name_ar']}")
            print(f"   Texte: {hadith_ar['ar_text'][:100]}...")
        else:
            print("❌ Échec")
        
        # Test 3: Hadith inexistant
        print("\nTest 3: Hadith inexistant")
        hadith_404 = await fetcher.fetch_hadith_fr('bukhari', 999999)
        if hadith_404 is None:
            print("✅ Gestion 404 correcte")
        else:
            print("❌ Devrait retourner None")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_fetcher())