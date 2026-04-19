"""
Connecteur IslamWeb Maktaba
Accès aux commentaires classiques (Sharh)

Ce connecteur récupère les commentaires des grands savants
comme Fath al-Bari, Sharh Muslim, etc.
"""

import aiohttp
import asyncio
from typing import Dict, List, Optional
import re
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IslamWebConnector:
    """
    Connecteur pour IslamWeb Maktaba
    
    Accès aux commentaires (Sharh) des hadiths:
    - Fath al-Bari (Ibn Hajar)
    - Sharh Muslim (Al-Nawawi)
    - Autres commentaires classiques
    
    Usage:
        connector = IslamWebConnector()
        sharh = await connector.get_sharh("bukhari", 1, "fath_al_bari")
    """
    
    BASE_URL = "https://islamweb.net"
    LIBRARY_ENDPOINT = "/ar/library"
    
    # Livres de commentaires disponibles
    SHARH_BOOKS = {
        'fath_al_bari': {
            'name': 'فتح الباري شرح صحيح البخاري',
            'author': 'ابن حجر العسقلاني',
            'book_id': 1673,
            'edition': {
                'publisher': 'دار المعرفة',
                'year_hijri': 1379,
                'editor': 'محمد فؤاد عبد الباقي',
                'volumes': 13
            }
        },
        'sharh_muslim': {
            'name': 'المنهاج شرح صحيح مسلم بن الحجاج',
            'author': 'النووي',
            'book_id': 1679,
            'edition': {
                'publisher': 'دار إحياء التراث العربي',
                'year_hijri': 1392,
                'editor': None,
                'volumes': 18
            }
        },
        'awn_al_mabud': {
            'name': 'عون المعبود شرح سنن أبي داود',
            'author': 'العظيم آبادي',
            'book_id': 1681,
            'edition': {
                'publisher': 'دار الكتب العلمية',
                'year_hijri': 1415,
                'editor': 'عبد الرحمن محمد عثمان',
                'volumes': 14
            }
        },
        'tuhfat_al_ahwadhi': {
            'name': 'تحفة الأحوذي بشرح جامع الترمذي',
            'author': 'المباركفوري',
            'book_id': 1682,
            'edition': {
                'publisher': 'دار الكتب العلمية',
                'year_hijri': None,
                'editor': None,
                'volumes': 10
            }
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
    
    async def get_sharh(
        self,
        book: str,
        hadith_number: int,
        sharh_book: str = 'fath_al_bari'
    ) -> Optional[Dict]:
        """
        Récupère le commentaire d'un hadith
        
        Args:
            book: Livre source ('bukhari', 'muslim', etc.)
            hadith_number: Numéro du hadith
            sharh_book: Livre de commentaire à utiliser
            
        Returns:
            {
                'book': 'فتح الباري',
                'author': 'ابن حجر العسقلاني',
                'edition': {...},
                'volume': 1,
                'page': 45,
                'commentary': '...',
                'key_points': [...]
            }
        """
        if not self.session:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                return await self._get_sharh(session, book, hadith_number, sharh_book)
        
        return await self._get_sharh(self.session, book, hadith_number, sharh_book)
    
    async def _get_sharh(
        self,
        session: aiohttp.ClientSession,
        book: str,
        hadith_number: int,
        sharh_book: str
    ) -> Optional[Dict]:
        """Récupération interne du Sharh"""
        
        if sharh_book not in self.SHARH_BOOKS:
            logger.error(f"Livre de Sharh inconnu: {sharh_book}")
            return None
        
        sharh_info = self.SHARH_BOOKS[sharh_book]
        logger.info(f"Récupération Sharh: {sharh_info['name']} pour {book} #{hadith_number}")
        
        # Construire l'URL de recherche
        search_url = f"{self.BASE_URL}{self.LIBRARY_ENDPOINT}/book/{sharh_info['book_id']}"
        
        try:
            # Rechercher le hadith dans le livre de commentaire
            async with session.get(
                search_url,
                params={'q': f'{book} {hadith_number}'}
            ) as response:
                if response.status != 200:
                    logger.error(f"Erreur IslamWeb: {response.status}")
                    return None
                
                html = await response.text()
                
                # Parser le commentaire
                commentary_data = self._parse_commentary(html, sharh_info)
                
                if not commentary_data:
                    logger.warning(f"Commentaire non trouvé pour {book} #{hadith_number}")
                    return None
                
                return {
                    'book': sharh_info['name'],
                    'author': sharh_info['author'],
                    'edition': sharh_info['edition'],
                    'volume': commentary_data.get('volume'),
                    'page': commentary_data.get('page'),
                    'commentary': commentary_data.get('text'),
                    'key_points': commentary_data.get('key_points', []),
                    'source': 'islamweb.net',
                    'url': commentary_data.get('url')
                }
        
        except Exception as e:
            logger.error(f"Erreur récupération Sharh: {e}")
            return None
    
    def _parse_commentary(
        self,
        html: str,
        sharh_info: Dict
    ) -> Optional[Dict]:
        """Parse le commentaire depuis le HTML"""
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Trouver le contenu du commentaire
        content_div = soup.find('div', class_='article-content')
        if not content_div:
            return None
        
        # Extraire le texte complet
        commentary_text = content_div.get_text(separator='\n', strip=True)
        
        # Extraire le volume et la page
        volume, page = self._extract_volume_page(soup)
        
        # Extraire les points clés
        key_points = self._extract_key_points(commentary_text)
        
        # Extraire l'URL
        url = self._extract_url(soup)
        
        return {
            'text': commentary_text,
            'volume': volume,
            'page': page,
            'key_points': key_points,
            'url': url
        }
    
    def _extract_volume_page(self, soup: BeautifulSoup) -> tuple:
        """Extrait le volume et la page"""
        
        # Chercher dans les métadonnées
        meta_div = soup.find('div', class_='book-meta')
        if meta_div:
            text = meta_div.get_text()
            
            # Pattern pour volume: ج1, الجزء 1, etc.
            volume_match = re.search(r'(?:ج|الجزء)\s*(\d+)', text)
            volume = int(volume_match.group(1)) if volume_match else None
            
            # Pattern pour page: ص45, الصفحة 45, etc.
            page_match = re.search(r'(?:ص|الصفحة)\s*(\d+)', text)
            page = int(page_match.group(1)) if page_match else None
            
            return volume, page
        
        return None, None
    
    def _extract_key_points(self, text: str) -> List[str]:
        """
        Extrait les points clés du commentaire
        
        Cherche les sections importantes comme:
        - شرح الكلمات (Explication des mots)
        - المعنى الإجمالي (Sens global)
        - الفوائد (Bénéfices)
        """
        key_points = []
        
        # Patterns pour identifier les sections importantes
        patterns = [
            r'شرح الكلمات:(.+?)(?=\n\n|\Z)',
            r'المعنى الإجمالي:(.+?)(?=\n\n|\Z)',
            r'الفوائد:(.+?)(?=\n\n|\Z)',
            r'ما يستفاد من الحديث:(.+?)(?=\n\n|\Z)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                # Nettoyer et ajouter
                point = match.strip()
                if point and len(point) > 20:  # Ignorer les points trop courts
                    key_points.append(point[:500])  # Limiter la longueur
        
        return key_points
    
    def _extract_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrait l'URL de la page"""
        
        canonical = soup.find('link', rel='canonical')
        if canonical and canonical.get('href'):
            return canonical['href']
        
        return None
    
    async def search_in_sharh(
        self,
        keyword: str,
        sharh_book: str = 'fath_al_bari',
        limit: int = 10
    ) -> List[Dict]:
        """
        Recherche dans un livre de commentaire
        
        Args:
            keyword: Mot-clé à rechercher
            sharh_book: Livre de commentaire
            limit: Nombre maximum de résultats
            
        Returns:
            Liste de résultats avec contexte
        """
        if not self.session:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                return await self._search_in_sharh(session, keyword, sharh_book, limit)
        
        return await self._search_in_sharh(self.session, keyword, sharh_book, limit)
    
    async def _search_in_sharh(
        self,
        session: aiohttp.ClientSession,
        keyword: str,
        sharh_book: str,
        limit: int
    ) -> List[Dict]:
        """Recherche interne dans le Sharh"""
        
        if sharh_book not in self.SHARH_BOOKS:
            logger.error(f"Livre de Sharh inconnu: {sharh_book}")
            return []
        
        sharh_info = self.SHARH_BOOKS[sharh_book]
        search_url = f"{self.BASE_URL}{self.LIBRARY_ENDPOINT}/search"
        
        try:
            async with session.get(
                search_url,
                params={
                    'q': keyword,
                    'book': sharh_info['book_id'],
                    'limit': limit
                }
            ) as response:
                if response.status != 200:
                    logger.error(f"Erreur recherche: {response.status}")
                    return []
                
                html = await response.text()
                
                # Parser les résultats
                results = self._parse_search_results(html, sharh_info)
                
                return results[:limit]
        
        except Exception as e:
            logger.error(f"Erreur recherche dans Sharh: {e}")
            return []
    
    def _parse_search_results(
        self,
        html: str,
        sharh_info: Dict
    ) -> List[Dict]:
        """Parse les résultats de recherche"""
        
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Trouver tous les résultats
        result_divs = soup.find_all('div', class_='search-result')
        
        for div in result_divs:
            # Extraire le titre
            title_elem = div.find('h3')
            title = title_elem.get_text(strip=True) if title_elem else ''
            
            # Extraire l'extrait
            excerpt_elem = div.find('div', class_='excerpt')
            excerpt = excerpt_elem.get_text(strip=True) if excerpt_elem else ''
            
            # Extraire l'URL
            link_elem = div.find('a')
            url = link_elem.get('href') if link_elem else None
            
            # Extraire volume/page si disponible
            meta_elem = div.find('div', class_='meta')
            volume, page = None, None
            if meta_elem:
                meta_text = meta_elem.get_text()
                volume_match = re.search(r'ج(\d+)', meta_text)
                page_match = re.search(r'ص(\d+)', meta_text)
                volume = int(volume_match.group(1)) if volume_match else None
                page = int(page_match.group(1)) if page_match else None
            
            results.append({
                'title': title,
                'excerpt': excerpt,
                'url': url,
                'volume': volume,
                'page': page,
                'book': sharh_info['name'],
                'author': sharh_info['author']
            })
        
        return results
    
    async def get_available_sharh_books(self) -> List[Dict]:
        """
        Retourne la liste des livres de Sharh disponibles
        
        Returns:
            Liste des livres avec leurs métadonnées
        """
        return [
            {
                'key': key,
                'name': info['name'],
                'author': info['author'],
                'edition': info['edition']
            }
            for key, info in self.SHARH_BOOKS.items()
        ]

# Exemple d'utilisation
async def main():
    """Exemple d'utilisation du connecteur"""
    
    async with IslamWebConnector() as connector:
        # Récupérer le commentaire du premier hadith de Bukhari
        print("Récupération du Sharh de Bukhari #1 (Fath al-Bari):")
        sharh = await connector.get_sharh('bukhari', 1, 'fath_al_bari')
        
        if sharh:
            print(f"\n{'='*60}")
            print(f"Livre: {sharh['book']}")
            print(f"Auteur: {sharh['author']}")
            print(f"Édition: {sharh['edition']['publisher']} ({sharh['edition']['year_hijri']}هـ)")
            print(f"Volume: {sharh['volume']}, Page: {sharh['page']}")
            print(f"{'='*60}\n")
            print(f"Commentaire (extrait):")
            print(sharh['commentary'][:500] + "...")
            print(f"\nPoints clés:")
            for i, point in enumerate(sharh['key_points'][:3], 1):
                print(f"{i}. {point[:200]}...")
        
        # Rechercher dans Fath al-Bari
        print("\n\nRecherche du mot 'النية' dans Fath al-Bari:")
        results = await connector.search_in_sharh('النية', 'fath_al_bari', limit=3)
        
        for i, result in enumerate(results, 1):
            print(f"\nRésultat {i}:")
            print(f"  Titre: {result['title']}")
            print(f"  Extrait: {result['excerpt'][:150]}...")
            print(f"  Volume: {result['volume']}, Page: {result['page']}")
        
        # Lister les livres disponibles
        print("\n\nLivres de Sharh disponibles:")
        books = await connector.get_available_sharh_books()
        for book in books:
            print(f"- {book['name']} ({book['author']})")

if __name__ == "__main__":
    asyncio.run(main())