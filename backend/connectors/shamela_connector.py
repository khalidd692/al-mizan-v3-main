#!/usr/bin/env python3
"""
Connecteur Shamela.ws - Bibliothèque islamique complète
Source: https://shamela.ws
Contenu: 10,000+ livres incluant collections majeures de hadiths
"""

import requests
import time
import hashlib
import json
from typing import Dict, List, Optional
from datetime import datetime

class ShamelaConnector:
    """
    Connecteur pour extraire hadiths depuis Shamela.ws
    
    Collections prioritaires:
    - Sahih Ibn Hibban
    - Sahih Ibn Khuzaymah
    - Musnad Ahmad (complet)
    - Œuvres Al-Albani
    - Sunan al-Darimi
    """
    
    BASE_URL = "https://shamela.ws"
    API_ENDPOINT = f"{BASE_URL}/api"
    
    # IDs des livres prioritaires sur Shamela
    PRIORITY_BOOKS = {
        'sahih_ibn_hibban': {
            'id': 1654,
            'name': 'Sahih Ibn Hibban',
            'author': 'Ibn Hibban',
            'estimated_hadiths': 7000
        },
        'sahih_ibn_khuzaymah': {
            'id': 1655,
            'name': 'Sahih Ibn Khuzaymah',
            'author': 'Ibn Khuzaymah',
            'estimated_hadiths': 3000
        },
        'musnad_ahmad': {
            'id': 1676,
            'name': 'Musnad Ahmad',
            'author': 'Ahmad ibn Hanbal',
            'estimated_hadiths': 27000
        },
        'sunan_darimi': {
            'id': 1658,
            'name': 'Sunan al-Darimi',
            'author': 'Al-Darimi',
            'estimated_hadiths': 3500
        },
        'silsilat_sahiha': {
            'id': 3232,
            'name': 'Silsilat al-Ahadith al-Sahiha',
            'author': 'Al-Albani',
            'estimated_hadiths': 3500
        }
    }
    
    def __init__(self, delay: float = 1.0):
        """
        Initialise le connecteur Shamela
        
        Args:
            delay: Délai entre requêtes (secondes) pour respecter le serveur
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/html',
            'Accept-Language': 'ar,en;q=0.9,fr;q=0.8'
        })
        
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Effectue une requête HTTP avec gestion d'erreurs
        
        Args:
            url: URL à requêter
            params: Paramètres de requête
            
        Returns:
            Réponse JSON ou None si erreur
        """
        try:
            time.sleep(self.delay)
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            # Shamela peut retourner HTML ou JSON
            if 'application/json' in response.headers.get('Content-Type', ''):
                return response.json()
            else:
                # Parser HTML si nécessaire
                return {'html': response.text}
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur requête {url}: {e}")
            return None
    
    def get_book_info(self, book_id: int) -> Optional[Dict]:
        """
        Récupère les métadonnées d'un livre
        
        Args:
            book_id: ID du livre sur Shamela
            
        Returns:
            Informations du livre
        """
        url = f"{self.BASE_URL}/book/{book_id}"
        return self._make_request(url)
    
    def get_book_content(self, book_id: int, page: int = 1) -> Optional[Dict]:
        """
        Récupère le contenu d'une page d'un livre
        
        Args:
            book_id: ID du livre
            page: Numéro de page
            
        Returns:
            Contenu de la page
        """
        url = f"{self.BASE_URL}/book/{book_id}/{page}"
        return self._make_request(url)
    
    def search_hadiths(self, query: str, book_id: Optional[int] = None) -> List[Dict]:
        """
        Recherche de hadiths par mots-clés
        
        Args:
            query: Termes de recherche
            book_id: Limiter à un livre spécifique
            
        Returns:
            Liste de hadiths trouvés
        """
        params = {
            'q': query,
            'type': 'hadith'
        }
        
        if book_id:
            params['book'] = book_id
        
        url = f"{self.BASE_URL}/search"
        result = self._make_request(url, params)
        
        if result:
            return self._parse_search_results(result)
        return []
    
    def _parse_search_results(self, data: Dict) -> List[Dict]:
        """
        Parse les résultats de recherche
        
        Args:
            data: Données brutes de Shamela
            
        Returns:
            Liste de hadiths formatés
        """
        hadiths = []
        
        # Structure à adapter selon réponse réelle de Shamela
        if 'results' in data:
            for item in data['results']:
                hadith = self._format_hadith(item)
                if hadith:
                    hadiths.append(hadith)
        
        return hadiths
    
    def _format_hadith(self, raw_data: Dict) -> Optional[Dict]:
        """
        Formate un hadith au format Al-Mizan
        
        Args:
            raw_data: Données brutes de Shamela
            
        Returns:
            Hadith formaté ou None
        """
        try:
            # Extraction des champs
            matn_ar = raw_data.get('text', '').strip()
            if not matn_ar:
                return None
            
            # Génération SHA256 pour déduplication
            sha256 = hashlib.sha256(matn_ar.encode('utf-8')).hexdigest()
            
            hadith = {
                'sha256': sha256,
                'collection': raw_data.get('book_name', 'Unknown'),
                'numero_hadith': str(raw_data.get('hadith_number', '')),
                'livre': raw_data.get('chapter', ''),
                'chapitre': raw_data.get('section', ''),
                'matn_ar': matn_ar,
                'matn_fr': '',  # À enrichir plus tard
                'isnad_brut': raw_data.get('chain', ''),
                'grade_final': raw_data.get('grade', ''),
                'categorie': self._determine_category(raw_data.get('grade', '')),
                'badge_alerte': 0,
                'source_url': f"{self.BASE_URL}/book/{raw_data.get('book_id')}/{raw_data.get('page')}",
                'source_api': 'shamela.ws',
                'inserted_at': datetime.now().isoformat()
            }
            
            return hadith
            
        except Exception as e:
            print(f"❌ Erreur formatage hadith: {e}")
            return None
    
    def _determine_category(self, grade: str) -> str:
        """
        Détermine la catégorie selon le grade
        
        Args:
            grade: Grade d'authenticité
            
        Returns:
            Catégorie (sahih, hassan, daif, etc.)
        """
        grade_lower = grade.lower()
        
        if 'صحيح' in grade or 'sahih' in grade_lower:
            return 'sahih'
        elif 'حسن' in grade or 'hassan' in grade_lower or 'hasan' in grade_lower:
            return 'hassan'
        elif 'ضعيف' in grade or 'daif' in grade_lower or 'weak' in grade_lower:
            return 'daif'
        elif 'موضوع' in grade or 'mawdu' in grade_lower or 'fabricated' in grade_lower:
            return 'mawdu'
        else:
            return 'non_classifie'
    
    def harvest_book(self, book_key: str, max_pages: Optional[int] = None) -> List[Dict]:
        """
        Récolte tous les hadiths d'un livre
        
        Args:
            book_key: Clé du livre dans PRIORITY_BOOKS
            max_pages: Limite de pages (None = toutes)
            
        Returns:
            Liste de hadiths extraits
        """
        if book_key not in self.PRIORITY_BOOKS:
            print(f"❌ Livre inconnu: {book_key}")
            return []
        
        book_info = self.PRIORITY_BOOKS[book_key]
        book_id = book_info['id']
        
        print(f"\n📚 Harvesting: {book_info['name']}")
        print(f"   Auteur: {book_info['author']}")
        print(f"   Estimation: {book_info['estimated_hadiths']:,} hadiths")
        
        hadiths = []
        page = 1
        
        while True:
            if max_pages and page > max_pages:
                break
            
            print(f"   Page {page}...", end=' ')
            
            content = self.get_book_content(book_id, page)
            if not content:
                print("❌ Erreur")
                break
            
            # Parser le contenu de la page
            page_hadiths = self._extract_hadiths_from_page(content, book_info)
            
            if not page_hadiths:
                print("✅ Fin")
                break
            
            hadiths.extend(page_hadiths)
            print(f"✅ {len(page_hadiths)} hadiths")
            
            page += 1
        
        print(f"\n✅ Total extrait: {len(hadiths):,} hadiths")
        return hadiths
    
    def _extract_hadiths_from_page(self, content: Dict, book_info: Dict) -> List[Dict]:
        """
        Extrait les hadiths d'une page
        
        Args:
            content: Contenu de la page
            book_info: Informations du livre
            
        Returns:
            Liste de hadiths
        """
        # À implémenter selon structure réelle de Shamela
        # Cette méthode nécessite l'analyse du HTML/JSON retourné
        
        hadiths = []
        
        # Exemple de structure (à adapter)
        if 'html' in content:
            # Parser HTML pour extraire hadiths
            # Utiliser BeautifulSoup si nécessaire
            pass
        elif 'hadiths' in content:
            for item in content['hadiths']:
                hadith = self._format_hadith(item)
                if hadith:
                    hadiths.append(hadith)
        
        return hadiths
    
    def harvest_all_priority_books(self, max_pages_per_book: Optional[int] = None) -> Dict[str, List[Dict]]:
        """
        Récolte tous les livres prioritaires
        
        Args:
            max_pages_per_book: Limite de pages par livre
            
        Returns:
            Dictionnaire {book_key: [hadiths]}
        """
        results = {}
        
        print("=" * 80)
        print("🚀 HARVESTING SHAMELA.WS - LIVRES PRIORITAIRES")
        print("=" * 80)
        
        for book_key in self.PRIORITY_BOOKS:
            hadiths = self.harvest_book(book_key, max_pages_per_book)
            results[book_key] = hadiths
            
            print(f"\n📊 Progression:")
            total = sum(len(h) for h in results.values())
            print(f"   Total hadiths: {total:,}")
        
        return results
    
    def save_to_json(self, hadiths: List[Dict], filename: str):
        """
        Sauvegarde les hadiths en JSON
        
        Args:
            hadiths: Liste de hadiths
            filename: Nom du fichier
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(hadiths, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Sauvegardé: {filename} ({len(hadiths):,} hadiths)")

def test_connector():
    """Test du connecteur Shamela"""
    print("🧪 Test du connecteur Shamela.ws\n")
    
    connector = ShamelaConnector(delay=2.0)
    
    # Test 1: Info d'un livre
    print("Test 1: Récupération info livre...")
    book_info = connector.get_book_info(1654)  # Sahih Ibn Hibban
    if book_info:
        print("✅ Info livre récupérée")
    else:
        print("❌ Échec récupération info")
    
    # Test 2: Recherche
    print("\nTest 2: Recherche hadiths...")
    results = connector.search_hadiths("الصلاة", book_id=1654)
    print(f"✅ {len(results)} résultats trouvés")
    
    # Test 3: Harvest limité
    print("\nTest 3: Harvest limité (5 pages)...")
    hadiths = connector.harvest_book('sahih_ibn_hibban', max_pages=5)
    print(f"✅ {len(hadiths)} hadiths extraits")
    
    if hadiths:
        connector.save_to_json(hadiths, 'backend/output/shamela_test.json')

if __name__ == '__main__':
    test_connector()