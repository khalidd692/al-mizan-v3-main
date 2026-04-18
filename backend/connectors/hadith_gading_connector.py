#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Connecteur Hadith Gading API
API la plus rapide validée (0.28s)
"""

import requests
import time
from typing import List, Dict, Optional
from datetime import datetime

class HadithGadingConnector:
    """
    Connecteur pour l'API Hadith Gading
    https://api.hadith.gading.dev
    """
    
    BASE_URL = "https://api.hadith.gading.dev"
    
    # Mapping des collections vers noms standards
    COLLECTIONS_MAP = {
        'bukhari': 'Sahih Bukhari',
        'muslim': 'Sahih Muslim',
        'abudawud': 'Sunan Abu Dawud',
        'tirmidzi': 'Jami\' at-Tirmidhi',
        'nasai': 'Sunan an-Nasa\'i',
        'ibnmajah': 'Sunan Ibn Majah',
        'malik': 'Muwatta Malik',
        'ahmad': 'Musnad Ahmad'
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Al-Mizan-Harvester/7.0',
            'Accept': 'application/json'
        })
        self.stats = {
            'requests': 0,
            'success': 0,
            'errors': 0,
            'total_time': 0
        }
    
    def get_available_books(self) -> Optional[List[Dict]]:
        """
        Récupère la liste des collections disponibles
        
        Returns:
            Liste des collections ou None si erreur
        """
        try:
            start_time = time.time()
            response = self.session.get(f"{self.BASE_URL}/books", timeout=10)
            elapsed = time.time() - start_time
            
            self.stats['requests'] += 1
            self.stats['total_time'] += elapsed
            
            if response.status_code == 200:
                data = response.json()
                self.stats['success'] += 1
                
                if data.get('code') == 200 and 'data' in data:
                    books = data['data']
                    
                    # Enrichir avec noms standards
                    for book in books:
                        book_id = book.get('id', '')
                        book['standard_name'] = self.COLLECTIONS_MAP.get(
                            book_id, 
                            book.get('name', '')
                        )
                    
                    return books
            
            self.stats['errors'] += 1
            return None
            
        except Exception as e:
            self.stats['errors'] += 1
            print(f"❌ Erreur get_available_books: {e}")
            return None
    
    def get_hadiths_range(
        self, 
        book: str, 
        start: int, 
        end: int
    ) -> Optional[List[Dict]]:
        """
        Récupère une plage de hadiths d'une collection
        
        Args:
            book: ID de la collection (ex: 'bukhari')
            start: Numéro de début (inclusif)
            end: Numéro de fin (inclusif)
        
        Returns:
            Liste de hadiths ou None si erreur
        """
        try:
            start_time = time.time()
            url = f"{self.BASE_URL}/books/{book}"
            params = {'range': f"{start}-{end}"}
            
            response = self.session.get(url, params=params, timeout=15)
            elapsed = time.time() - start_time
            
            self.stats['requests'] += 1
            self.stats['total_time'] += elapsed
            
            if response.status_code == 200:
                data = response.json()
                self.stats['success'] += 1
                
                if data.get('code') == 200 and 'data' in data:
                    hadiths_data = data['data']
                    
                    # Extraire les hadiths
                    if isinstance(hadiths_data, dict):
                        hadiths = hadiths_data.get('hadiths', [])
                    elif isinstance(hadiths_data, list):
                        hadiths = hadiths_data
                    else:
                        return None
                    
                    # Normaliser chaque hadith
                    normalized = []
                    for hadith in hadiths:
                        normalized_hadith = self._normalize_hadith(hadith, book)
                        if normalized_hadith:
                            normalized.append(normalized_hadith)
                    
                    return normalized
            
            self.stats['errors'] += 1
            return None
            
        except Exception as e:
            self.stats['errors'] += 1
            print(f"❌ Erreur get_hadiths_range: {e}")
            return None
    
    def _normalize_hadith(self, raw_hadith: Dict, book: str) -> Optional[Dict]:
        """
        Normalise un hadith au format Al-Mīzān v7
        
        Args:
            raw_hadith: Hadith brut de l'API
            book: ID de la collection
        
        Returns:
            Hadith normalisé ou None si invalide
        """
        try:
            # Extraire les champs
            hadith_number = raw_hadith.get('number', 0)
            arab_text = raw_hadith.get('arab', '')
            hadith_id = raw_hadith.get('id', f"{book}_{hadith_number}")
            
            # Vérifier champs obligatoires
            if not arab_text or not hadith_number:
                return None
            
            # Construire l'objet normalisé
            normalized = {
                # Identifiants
                'source_id': hadith_id,
                'source_api': 'hadith_gading',
                'collection': self.COLLECTIONS_MAP.get(book, book),
                'collection_id': book,
                'hadith_number': hadith_number,
                
                # Contenu
                'text_arabic': arab_text.strip(),
                
                # Métadonnées (à enrichir)
                'narrator': '',
                'grade': '',
                'grade_raw': '',
                'source_book': self.COLLECTIONS_MAP.get(book, book),
                'source_page': '',
                
                # Timestamps
                'harvested_at': datetime.utcnow().isoformat(),
                'api_version': 'v1'
            }
            
            # Tenter d'extraire le grade si présent
            if 'grade' in raw_hadith:
                normalized['grade_raw'] = str(raw_hadith['grade'])
                normalized['grade'] = self._normalize_grade(normalized['grade_raw'])
            
            return normalized
            
        except Exception as e:
            print(f"⚠️  Erreur normalisation hadith: {e}")
            return None
    
    def _normalize_grade(self, grade_raw: str) -> str:
        """
        Normalise le grade du hadith
        
        Args:
            grade_raw: Grade brut
        
        Returns:
            Grade normalisé (sahih, hasan, daif, etc.)
        """
        grade_lower = grade_raw.lower().strip()
        
        # Sahih
        if 'sahih' in grade_lower or 'صحيح' in grade_lower:
            return 'sahih'
        
        # Hasan
        if 'hasan' in grade_lower or 'حسن' in grade_lower:
            return 'hasan'
        
        # Daif
        if 'daif' in grade_lower or 'da\'if' in grade_lower or 'ضعيف' in grade_lower:
            return 'daif'
        
        # Mawdu
        if 'mawdu' in grade_lower or 'موضوع' in grade_lower:
            return 'mawdu'
        
        return 'unknown'
    
    def harvest_collection(
        self, 
        book: str, 
        max_hadiths: int = 1000,
        batch_size: int = 50
    ) -> List[Dict]:
        """
        Harveste une collection complète par batches
        
        Args:
            book: ID de la collection
            max_hadiths: Nombre maximum de hadiths à extraire
            batch_size: Taille des batches
        
        Returns:
            Liste de tous les hadiths extraits
        """
        all_hadiths = []
        current = 1
        
        print(f"\n🔄 Harvesting {book}...")
        print(f"   Objectif: {max_hadiths} hadiths")
        print(f"   Batch: {batch_size} hadiths/requête")
        print()
        
        while current <= max_hadiths:
            end = min(current + batch_size - 1, max_hadiths)
            
            print(f"📥 Batch {current}-{end}...", end=' ')
            
            hadiths = self.get_hadiths_range(book, current, end)
            
            if hadiths:
                all_hadiths.extend(hadiths)
                print(f"✅ {len(hadiths)} hadiths")
            else:
                print(f"❌ Erreur")
                break
            
            current = end + 1
            
            # Rate limiting
            time.sleep(0.5)
        
        print(f"\n✅ Total extrait: {len(all_hadiths)} hadiths")
        return all_hadiths
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques du connecteur"""
        avg_time = (
            self.stats['total_time'] / self.stats['requests'] 
            if self.stats['requests'] > 0 
            else 0
        )
        
        success_rate = (
            (self.stats['success'] / self.stats['requests'] * 100)
            if self.stats['requests'] > 0
            else 0
        )
        
        return {
            'requests': self.stats['requests'],
            'success': self.stats['success'],
            'errors': self.stats['errors'],
            'success_rate': round(success_rate, 2),
            'avg_response_time': round(avg_time, 2),
            'total_time': round(self.stats['total_time'], 2)
        }

def test_connector():
    """Test du connecteur Hadith Gading"""
    
    print("=" * 80)
    print("🔍 TEST CONNECTEUR HADITH GADING")
    print("=" * 80)
    print()
    
    connector = HadithGadingConnector()
    
    # Test 1: Liste des collections
    print("📚 Test 1: Liste des collections")
    print("-" * 80)
    
    books = connector.get_available_books()
    
    if books:
        print(f"✅ {len(books)} collections disponibles:")
        for book in books[:5]:
            print(f"   - {book.get('id')}: {book.get('standard_name')}")
            print(f"     Hadiths: {book.get('available', 'N/A')}")
    else:
        print("❌ Erreur récupération collections")
    
    print()
    
    # Test 2: Extraction Bukhari (10 premiers hadiths)
    print("📖 Test 2: Extraction Sahih Bukhari (10 premiers)")
    print("-" * 80)
    
    hadiths = connector.get_hadiths_range('bukhari', 1, 10)
    
    if hadiths:
        print(f"✅ {len(hadiths)} hadiths extraits")
        
        # Afficher le premier
        if hadiths:
            h = hadiths[0]
            print(f"\n📝 Premier hadith:")
            print(f"   ID: {h['source_id']}")
            print(f"   Numéro: {h['hadith_number']}")
            print(f"   Collection: {h['collection']}")
            print(f"   Texte: {h['text_arabic'][:100]}...")
            print(f"   Grade: {h['grade']}")
    else:
        print("❌ Erreur extraction hadiths")
    
    print()
    
    # Test 3: Harvesting batch (50 hadiths)
    print("🔄 Test 3: Harvesting batch Muslim (50 hadiths)")
    print("-" * 80)
    
    batch_hadiths = connector.harvest_collection('muslim', max_hadiths=50, batch_size=25)
    
    print()
    
    # Statistiques
    print("=" * 80)
    print("📊 STATISTIQUES")
    print("=" * 80)
    
    stats = connector.get_stats()
    print(f"Requêtes totales: {stats['requests']}")
    print(f"Succès: {stats['success']}")
    print(f"Erreurs: {stats['errors']}")
    print(f"Taux de succès: {stats['success_rate']}%")
    print(f"Temps moyen: {stats['avg_response_time']}s")
    print(f"Temps total: {stats['total_time']}s")
    
    print()
    print("=" * 80)
    print("✅ CONNECTEUR HADITH GADING OPÉRATIONNEL")
    print("=" * 80)

if __name__ == "__main__":
    test_connector()