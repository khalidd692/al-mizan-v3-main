"""
Connecteur pour Hadith.Islam-db.com
Source brute du Jarḥ wa Taʿdīl

Ce connecteur récupère les évaluations EXACTES des imams
sans résumé ni interprétation.
"""

import aiohttp
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NarratorEvaluation:
    """Évaluation d'un narrateur par un imam"""
    imam: str
    verdict: str
    source_book: str
    raw_quote: str
    page: Optional[int] = None
    volume: Optional[int] = None

class IslamDBConnector:
    """
    Connecteur pour Hadith.Islam-db.com
    
    Récupère les évaluations des narrateurs selon TOUS les imams
    du Jarḥ wa Taʿdīl, sans résumé.
    
    Usage:
        connector = IslamDBConnector()
        evaluations = await connector.get_narrator_evaluations("أبو هريرة")
    """
    
    BASE_URL = "https://hadith.islam-db.com"
    
    # Imams majeurs du Jarḥ wa Taʿdīl
    MAJOR_IMAMS = [
        "ابن معين",           # Ibn Ma'in
        "أبو حاتم الرازي",    # Abu Hatim al-Razi
        "أبو زرعة الرازي",    # Abu Zur'ah al-Razi
        "الذهبي",             # Al-Dhahabi
        "ابن حجر العسقلاني",  # Ibn Hajar al-Asqalani
        "النسائي",            # Al-Nasa'i
        "البخاري",            # Al-Bukhari
        "أحمد بن حنبل",       # Ahmad ibn Hanbal
        "يحيى بن سعيد القطان", # Yahya ibn Sa'id al-Qattan
        "علي بن المديني"     # Ali ibn al-Madini
    ]
    
    # Verdicts possibles
    VERDICTS = {
        'thiqah': ['ثقة', 'ثقة ثقة', 'ثقة ثبت', 'ثقة حافظ'],
        'saduq': ['صدوق', 'صدوق حسن الحديث'],
        'daif': ['ضعيف', 'ضعيف الحديث', 'ليس بالقوي'],
        'matruk': ['متروك', 'متروك الحديث'],
        'kadhdhab': ['كذاب', 'وضاع']
    }
    
    def __init__(self, timeout: int = 30):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_narrator_evaluations(
        self, 
        narrator_name: str
    ) -> Dict[str, any]:
        """
        Récupère TOUTES les évaluations d'un narrateur
        
        Args:
            narrator_name: Nom du narrateur en arabe
            
        Returns:
            {
                'narrator': 'أبو هريرة',
                'evaluations': [
                    {
                        'imam': 'ابن معين',
                        'verdict': 'ثقة',
                        'source': 'تاريخ ابن معين',
                        'raw_quote': 'قال ابن معين: أبو هريرة ثقة',
                        'volume': 1,
                        'page': 234
                    },
                    ...
                ],
                'consensus': 'ثقة',
                'total_evaluations': 10
            }
        """
        if not self.session:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                return await self._fetch_evaluations(session, narrator_name)
        
        return await self._fetch_evaluations(self.session, narrator_name)
    
    async def _fetch_evaluations(
        self, 
        session: aiohttp.ClientSession,
        narrator_name: str
    ) -> Dict[str, any]:
        """Récupère les évaluations depuis l'API"""
        
        logger.info(f"Récupération des évaluations pour: {narrator_name}")
        
        # Endpoint de recherche
        search_url = f"{self.BASE_URL}/api/narrator/search"
        
        try:
            async with session.get(
                search_url,
                params={'name': narrator_name}
            ) as response:
                if response.status != 200:
                    logger.error(f"Erreur API: {response.status}")
                    return self._empty_result(narrator_name)
                
                data = await response.json()
                
                if not data or 'narrator' not in data:
                    logger.warning(f"Narrateur non trouvé: {narrator_name}")
                    return self._empty_result(narrator_name)
                
                narrator_id = data['narrator']['id']
                
                # Récupérer les évaluations détaillées
                evaluations_url = f"{self.BASE_URL}/api/narrator/{narrator_id}/evaluations"
                
                async with session.get(evaluations_url) as eval_response:
                    if eval_response.status != 200:
                        logger.error(f"Erreur récupération évaluations: {eval_response.status}")
                        return self._empty_result(narrator_name)
                    
                    eval_data = await eval_response.json()
                    
                    # Parser les évaluations
                    evaluations = self._parse_evaluations(eval_data)
                    
                    # Calculer le consensus
                    consensus = self._calculate_consensus(evaluations)
                    
                    return {
                        'narrator': narrator_name,
                        'narrator_id': narrator_id,
                        'evaluations': evaluations,
                        'consensus': consensus,
                        'total_evaluations': len(evaluations),
                        'source': 'hadith.islam-db.com'
                    }
        
        except aiohttp.ClientError as e:
            logger.error(f"Erreur réseau: {e}")
            return self._empty_result(narrator_name)
        except Exception as e:
            logger.error(f"Erreur inattendue: {e}")
            return self._empty_result(narrator_name)
    
    def _parse_evaluations(self, data: dict) -> List[dict]:
        """Parse les évaluations brutes"""
        evaluations = []
        
        for eval_item in data.get('evaluations', []):
            evaluations.append({
                'imam': eval_item.get('imam_name', ''),
                'verdict': eval_item.get('verdict', ''),
                'source': eval_item.get('source_book', ''),
                'raw_quote': eval_item.get('quote', ''),
                'volume': eval_item.get('volume'),
                'page': eval_item.get('page')
            })
        
        return evaluations
    
    def _calculate_consensus(self, evaluations: List[dict]) -> str:
        """
        Calcule le consensus des imams
        
        Logique:
        - Si majorité dit "Thiqah" → Thiqah
        - Si majorité dit "Da'if" → Da'if
        - Si mixte → "Mukhtalaf fih" (Controversé)
        """
        if not evaluations:
            return "غير معروف"  # Inconnu
        
        verdict_counts = {}
        
        for eval in evaluations:
            verdict = eval['verdict']
            
            # Normaliser le verdict
            normalized = self._normalize_verdict(verdict)
            verdict_counts[normalized] = verdict_counts.get(normalized, 0) + 1
        
        # Trouver le verdict majoritaire
        if not verdict_counts:
            return "غير معروف"
        
        max_count = max(verdict_counts.values())
        majority_verdicts = [v for v, c in verdict_counts.items() if c == max_count]
        
        if len(majority_verdicts) == 1:
            return majority_verdicts[0]
        else:
            return "مختلف فيه"  # Controversé
    
    def _normalize_verdict(self, verdict: str) -> str:
        """Normalise un verdict vers une catégorie standard"""
        verdict = verdict.strip()
        
        for category, variants in self.VERDICTS.items():
            if verdict in variants:
                return variants[0]  # Retourne la forme standard
        
        return verdict  # Si non reconnu, retourne tel quel
    
    def _empty_result(self, narrator_name: str) -> dict:
        """Résultat vide en cas d'erreur"""
        return {
            'narrator': narrator_name,
            'narrator_id': None,
            'evaluations': [],
            'consensus': 'غير معروف',
            'total_evaluations': 0,
            'source': 'hadith.islam-db.com',
            'error': True
        }
    
    async def get_raw_quotes(
        self, 
        narrator_name: str, 
        imam: str
    ) -> Optional[str]:
        """
        Récupère la citation EXACTE d'un imam sur un narrateur
        SANS résumé, SANS interprétation
        
        Args:
            narrator_name: Nom du narrateur
            imam: Nom de l'imam (ex: "ابن معين")
            
        Returns:
            Citation exacte ou None si non trouvée
        """
        evaluations = await self.get_narrator_evaluations(narrator_name)
        
        for eval in evaluations.get('evaluations', []):
            if eval['imam'] == imam:
                return eval['raw_quote']
        
        return None
    
    async def search_by_verdict(
        self, 
        verdict: str, 
        limit: int = 100
    ) -> List[dict]:
        """
        Recherche les narrateurs par verdict
        
        Args:
            verdict: Type de verdict (ex: "ثقة", "ضعيف")
            limit: Nombre maximum de résultats
            
        Returns:
            Liste de narrateurs avec ce verdict
        """
        if not self.session:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                return await self._search_by_verdict(session, verdict, limit)
        
        return await self._search_by_verdict(self.session, verdict, limit)
    
    async def _search_by_verdict(
        self,
        session: aiohttp.ClientSession,
        verdict: str,
        limit: int
    ) -> List[dict]:
        """Recherche interne par verdict"""
        
        search_url = f"{self.BASE_URL}/api/narrator/search-by-verdict"
        
        try:
            async with session.get(
                search_url,
                params={'verdict': verdict, 'limit': limit}
            ) as response:
                if response.status != 200:
                    logger.error(f"Erreur recherche: {response.status}")
                    return []
                
                data = await response.json()
                return data.get('narrators', [])
        
        except Exception as e:
            logger.error(f"Erreur recherche par verdict: {e}")
            return []

# Exemple d'utilisation
async def main():
    """Exemple d'utilisation du connecteur"""
    
    async with IslamDBConnector() as connector:
        # Récupérer les évaluations d'Abu Hurayrah
        result = await connector.get_narrator_evaluations("أبو هريرة")
        
        print(f"\n{'='*60}")
        print(f"Narrateur: {result['narrator']}")
        print(f"Consensus: {result['consensus']}")
        print(f"Total évaluations: {result['total_evaluations']}")
        print(f"{'='*60}\n")
        
        for eval in result['evaluations']:
            print(f"Imam: {eval['imam']}")
            print(f"Verdict: {eval['verdict']}")
            print(f"Source: {eval['source']}")
            print(f"Citation: {eval['raw_quote']}")
            print(f"-" * 60)
        
        # Récupérer une citation spécifique
        quote = await connector.get_raw_quotes("أبو هريرة", "ابن معين")
        if quote:
            print(f"\nCitation d'Ibn Ma'in:")
            print(quote)

if __name__ == "__main__":
    asyncio.run(main())
