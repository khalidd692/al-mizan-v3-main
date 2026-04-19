"""
Connecteur Dorar.net Enhanced
Vérification et normalisation du Matn (texte du hadith)

Ce connecteur récupère le texte exact du hadith avec ses variantes
selon les différentes sources et éditions.
"""

import aiohttp
import asyncio
from typing import Dict, List, Optional
import re
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DorarConnectorEnhanced:
    """
    Connecteur Dorar.net amélioré pour vérification du Matn
    
    Fonctionnalités:
    - Vérification du texte exact du hadith
    - Détection des variantes textuelles
    - Identification de l'édition de référence
    - Normalisation du texte arabe
    
    Usage:
        connector = DorarConnectorEnhanced()
        result = await connector.verify_matn("إنما الأعمال بالنيات")
    """
    
    BASE_URL = "https://dorar.net"
    SEARCH_ENDPOINT = "/hadith/search"
    
    # Éditions de référence connues
    REFERENCE_EDITIONS = {
        'bukhari': {
            'name': 'صحيح البخاري',
            'editions': [
                {
                    'publisher': 'دار المعرفة',
                    'editor': 'محمد فؤاد عبد الباقي',
                    'year_hijri': 1379,
                    'volumes': 9
                },
                {
                    'publisher': 'دار طوق النجاة',
                    'editor': 'محمد زهير بن ناصر الناصر',
                    'year_hijri': 1422,
                    'volumes': 9
                }
            ]
        },
        'muslim': {
            'name': 'صحيح مسلم',
            'editions': [
                {
                    'publisher': 'دار إحياء التراث العربي',
                    'editor': 'محمد فؤاد عبد الباقي',
                    'year_hijri': None,
                    'volumes': 5
                }
            ]
        },
        'abu_dawud': {
            'name': 'سنن أبي داود',
            'editions': [
                {
                    'publisher': 'المكتبة العصرية',
                    'editor': 'محمد محيي الدين عبد الحميد',
                    'year_hijri': None,
                    'volumes': 4
                }
            ]
        }
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
    
    async def verify_matn(self, hadith_text: str) -> Dict[str, any]:
        """
        Vérifie et normalise le texte du hadith
        
        Args:
            hadith_text: Texte du hadith à vérifier
            
        Returns:
            {
                'normalized_text': 'إنما الأعمال بالنيات',
                'original_text': '...',
                'variants': [
                    {
                        'source': 'صحيح البخاري',
                        'text': '...',
                        'edition': {...},
                        'differences': ['word1', 'word2']
                    }
                ],
                'reference_edition': {...},
                'confidence': 0.95
            }
        """
        if not self.session:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                return await self._verify_matn(session, hadith_text)
        
        return await self._verify_matn(self.session, hadith_text)
    
    async def _verify_matn(
        self,
        session: aiohttp.ClientSession,
        hadith_text: str
    ) -> Dict[str, any]:
        """Vérification interne du Matn"""
        
        logger.info(f"Vérification du Matn: {hadith_text[:50]}...")
        
        # Normaliser le texte pour la recherche
        normalized_search = self._normalize_arabic(hadith_text)
        
        # Rechercher sur Dorar
        search_url = f"{self.BASE_URL}{self.SEARCH_ENDPOINT}"
        
        try:
            async with session.get(
                search_url,
                params={
                    'q': normalized_search,
                    'st': 'p',  # Recherche précise
                    'xclude': '',
                    'fillopts': '',
                    'page': 1
                }
            ) as response:
                if response.status != 200:
                    logger.error(f"Erreur Dorar: {response.status}")
                    return self._empty_result(hadith_text)
                
                html = await response.text()
                
                # Parser les résultats
                variants = self._parse_search_results(html, hadith_text)
                
                if not variants:
                    logger.warning("Aucune variante trouvée")
                    return self._empty_result(hadith_text)
                
                # Sélectionner le texte de référence
                reference_text = variants[0]['text']
                reference_edition = variants[0].get('edition')
                
                # Calculer les différences
                for variant in variants:
                    variant['differences'] = self._find_differences(
                        reference_text,
                        variant['text']
                    )
                
                # Calculer la confiance
                confidence = self._calculate_confidence(variants)
                
                return {
                    'normalized_text': reference_text,
                    'original_text': hadith_text,
                    'variants': variants,
                    'reference_edition': reference_edition,
                    'confidence': confidence,
                    'total_variants': len(variants),
                    'source': 'dorar.net'
                }
        
        except Exception as e:
            logger.error(f"Erreur vérification Matn: {e}")
            return self._empty_result(hadith_text)
    
    def _parse_search_results(
        self,
        html: str,
        original_text: str
    ) -> List[Dict]:
        """Parse les résultats de recherche Dorar"""
        
        soup = BeautifulSoup(html, 'html.parser')
        variants = []
        
        # Trouver tous les hadiths dans les résultats
        hadith_divs = soup.find_all('div', class_='hadith')
        
        for div in hadith_divs:
            # Extraire le texte du hadith
            text_elem = div.find('div', class_='hadith_text')
            if not text_elem:
                continue
            
            text = text_elem.get_text(strip=True)
            
            # Extraire la source
            source_elem = div.find('div', class_='hadith_source')
            source = source_elem.get_text(strip=True) if source_elem else 'غير معروف'
            
            # Identifier l'édition
            edition = self._identify_edition(source)
            
            # Extraire le numéro du hadith
            hadith_number = self._extract_hadith_number(div)
            
            variants.append({
                'text': text,
                'source': source,
                'edition': edition,
                'hadith_number': hadith_number,
                'similarity': self._calculate_similarity(original_text, text)
            })
        
        # Trier par similarité
        variants.sort(key=lambda x: x['similarity'], reverse=True)
        
        return variants
    
    def _identify_edition(self, source: str) -> Optional[Dict]:
        """Identifie l'édition à partir de la source"""
        
        for book_key, book_data in self.REFERENCE_EDITIONS.items():
            if book_data['name'] in source:
                # Retourner la première édition par défaut
                if book_data['editions']:
                    return book_data['editions'][0]
        
        return None
    
    def _extract_hadith_number(self, div) -> Optional[int]:
        """Extrait le numéro du hadith"""
        
        # Chercher dans le texte de la source
        source_elem = div.find('div', class_='hadith_source')
        if source_elem:
            text = source_elem.get_text()
            # Chercher un pattern comme "رقم 123" ou "حديث 123"
            match = re.search(r'(?:رقم|حديث)\s*(\d+)', text)
            if match:
                return int(match.group(1))
        
        return None
    
    def _normalize_arabic(self, text: str) -> str:
        """
        Normalise le texte arabe pour la recherche
        
        - Supprime les diacritiques (tashkeel)
        - Normalise les hamzas
        - Normalise les alifs
        """
        # Supprimer les diacritiques
        text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
        
        # Normaliser les hamzas
        text = re.sub(r'[إأآا]', 'ا', text)
        text = re.sub(r'[ؤئ]', 'ء', text)
        
        # Normaliser les ya
        text = re.sub(r'[ىي]', 'ي', text)
        
        # Normaliser les ta marbuta
        text = re.sub(r'ة', 'ه', text)
        
        return text.strip()
    
    def _find_differences(self, text1: str, text2: str) -> List[str]:
        """Trouve les différences entre deux textes"""
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        # Mots présents dans text1 mais pas dans text2
        diff1 = words1 - words2
        # Mots présents dans text2 mais pas dans text1
        diff2 = words2 - words1
        
        return list(diff1.union(diff2))
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcule la similarité entre deux textes (0-1)"""
        
        words1 = set(self._normalize_arabic(text1).split())
        words2 = set(self._normalize_arabic(text2).split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_confidence(self, variants: List[Dict]) -> float:
        """
        Calcule le niveau de confiance basé sur les variantes
        
        - Plus de variantes similaires = plus de confiance
        - Présence dans sources majeures = plus de confiance
        """
        if not variants:
            return 0.0
        
        # Confiance de base sur la similarité
        avg_similarity = sum(v['similarity'] for v in variants) / len(variants)
        
        # Bonus si présent dans Bukhari ou Muslim
        major_sources_bonus = 0.0
        for variant in variants:
            source = variant['source']
            if 'البخاري' in source or 'مسلم' in source:
                major_sources_bonus = 0.1
                break
        
        confidence = min(avg_similarity + major_sources_bonus, 1.0)
        
        return round(confidence, 2)
    
    def _empty_result(self, hadith_text: str) -> Dict:
        """Résultat vide en cas d'erreur"""
        return {
            'normalized_text': hadith_text,
            'original_text': hadith_text,
            'variants': [],
            'reference_edition': None,
            'confidence': 0.0,
            'total_variants': 0,
            'source': 'dorar.net',
            'error': True
        }
    
    async def get_hadith_by_number(
        self,
        book: str,
        hadith_number: int
    ) -> Optional[Dict]:
        """
        Récupère un hadith par son numéro dans un livre
        
        Args:
            book: Nom du livre (ex: 'bukhari', 'muslim')
            hadith_number: Numéro du hadith
            
        Returns:
            Informations complètes sur le hadith
        """
        if not self.session:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                return await self._get_hadith_by_number(session, book, hadith_number)
        
        return await self._get_hadith_by_number(self.session, book, hadith_number)
    
    async def _get_hadith_by_number(
        self,
        session: aiohttp.ClientSession,
        book: str,
        hadith_number: int
    ) -> Optional[Dict]:
        """Récupération interne par numéro"""
        
        # Construire l'URL directe
        url = f"{self.BASE_URL}/hadith/{book}/{hadith_number}"
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extraire les informations
                hadith_div = soup.find('div', class_='hadith')
                if not hadith_div:
                    return None
                
                text_elem = hadith_div.find('div', class_='hadith_text')
                text = text_elem.get_text(strip=True) if text_elem else ''
                
                source_elem = hadith_div.find('div', class_='hadith_source')
                source = source_elem.get_text(strip=True) if source_elem else ''
                
                return {
                    'text': text,
                    'source': source,
                    'book': book,
                    'hadith_number': hadith_number,
                    'edition': self._identify_edition(source),
                    'url': url
                }
        
        except Exception as e:
            logger.error(f"Erreur récupération hadith {book}/{hadith_number}: {e}")
            return None

# Exemple d'utilisation
async def main():
    """Exemple d'utilisation du connecteur"""
    
    async with DorarConnectorEnhanced() as connector:
        # Vérifier un hadith célèbre
        hadith_text = "إنما الأعمال بالنيات"
        
        result = await connector.verify_matn(hadith_text)
        
        print(f"\n{'='*60}")
        print(f"Texte original: {result['original_text']}")
        print(f"Texte normalisé: {result['normalized_text']}")
        print(f"Confiance: {result['confidence']}")
        print(f"Nombre de variantes: {result['total_variants']}")
        print(f"{'='*60}\n")
        
        for i, variant in enumerate(result['variants'][:3], 1):
            print(f"Variante {i}:")
            print(f"  Source: {variant['source']}")
            print(f"  Texte: {variant['text'][:100]}...")
            print(f"  Similarité: {variant['similarity']:.2f}")
            if variant.get('edition'):
                ed = variant['edition']
                print(f"  Édition: {ed['publisher']} ({ed.get('year_hijri', 'N/A')}هـ)")
            print(f"  Différences: {variant.get('differences', [])}")
            print(f"-" * 60)
        
        # Récupérer un hadith spécifique
        print("\nRécupération du hadith Bukhari #1:")
        hadith = await connector.get_hadith_by_number('bukhari', 1)
        if hadith:
            print(f"Texte: {hadith['text']}")
            print(f"Source: {hadith['source']}")

if __name__ == "__main__":
    asyncio.run(main())