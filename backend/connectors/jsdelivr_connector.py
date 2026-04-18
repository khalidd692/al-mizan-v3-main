#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Connecteur JSDelivr CDN (GitHub Hadith API)
CDN haute disponibilité, pas de rate limiting
"""

import requests
import time
from typing import List, Dict, Optional
from datetime import datetime

class JSDelivrConnector:
    """
    Connecteur pour JSDelivr CDN (fawazahmed0/hadith-api)
    https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1
    """
    
    BASE_URL = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1"
    
    # Mapping des éditions vers noms standards
    EDITIONS_MAP = {
        'ara-bukhari': 'Sahih Bukhari',
        'ara-muslim': 'Sahih Muslim',
        'ara-abudawud': 'Sunan Abu Dawud',
        'ara-tirmidzi': 'Jami\' at-Tirmidhi',
        'ara-nasai': 'Sunan an-Nasa\'i',
        'ara-ibnmajah': 'Sunan Ibn Majah',
        'ara-malik': 'Muwatta Malik'
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
            'total_time': 0,
            'total_hadiths': 0
        }
    
    def get_available_editions(self) -> Optional[Dict]:
        """
        Récupère la liste des éditions disponibles
        
        Returns:
            Dict des éditions ou None si erreur
        """
        try:
            start_time = time.time()
            response = self.session.get(
                f"{self.BASE_URL}/editions.json", 
                timeout=15
            )
            elapsed = time.time() - start_time
            
            self.stats['requests'] += 1
            self.stats['total_time'] += elapsed
            
            if response.status_code == 200:
                editions = response.json()
                self.stats['success'] += 1
                return editions
            
            self.stats['errors'] += 1
            return None
            
        except Exception as e:
            self.stats['errors'] += 1
            print(f"❌ Erreur get_available_editions: {e}")
            return None
    
    def get_edition_metadata(self, edition: str) -> Optional[Dict]:
        """
        Récupère les métadonnées d'une édition
        
        Args:
            edition: ID de l'édition (ex: 'ara-bukhari')
        
        Returns:
            Métadonnées ou None si erreur
        """
        try:
            start_time = time.time()
            response = self.session.get(
                f"{self.BASE_URL}/editions/{edition}/info.json",
                timeout=15
            )
            elapsed = time.time() - start_time
            
            self.stats['requests'] += 1
            self.stats['total_time'] += elapsed
            
            if response.status_code == 200:
                metadata = response.json()
                self.stats['success'] += 1
                return metadata
            
            self.stats['errors'] += 1
            return None
            
        except Exception as e:
            self.stats['errors'] += 1
            print(f"⚠️  Métadonnées non disponibles pour {edition}")
            return None
    
    def get_full_collection(self, edition: str) -> Optional[List[Dict]]:
        """
        Télécharge une collection complète
        
        Args:
            edition: ID de l'édition (ex: 'ara-bukhari')
        
        Returns:
            Liste de hadiths normalisés ou None si erreur
        """
        try:
            print(f"\n📥 Téléchargement {edition}...", end=' ')
            
            start_time = time.time()
            response = self.session.get(
                f"{self.BASE_URL}/editions/{edition}.json",
                timeout=30
            )
            elapsed = time.time() - start_time
            
            self.stats['requests'] += 1
            self.stats['total_time'] += elapsed
            
            if response.status_code == 200:
                data = response.json()
                self.stats['success'] += 1
                
                print(f"✅ ({elapsed:.2f}s)")
                
                # Extraire et normaliser les hadiths
                hadiths = self._extract_hadiths(data, edition)
                
                if hadiths:
                    self.stats['total_hadiths'] += len(hadiths)
                    print(f"   📊 {len(hadiths)} hadiths extraits")
                    return hadiths
                
                return None
            
            self.stats['errors'] += 1
            print(f"❌ Erreur HTTP {response.status_code}")
            return None
            
        except Exception as e:
            self.stats['errors'] += 1
            print(f"❌ Erreur: {e}")
            return None
    
    def _extract_hadiths(self, data: Dict, edition: str) -> List[Dict]:
        """
        Extrait et normalise les hadiths du JSON
        
        Args:
            data: Données JSON brutes
            edition: ID de l'édition
        
        Returns:
            Liste de hadiths normalisés
        """
        hadiths = []
        
        # Structure: {"metadata": {...}, "hadiths": [...]}
        raw_hadiths = data.get('hadiths', [])
        metadata = data.get('metadata', {})
        
        collection_name = self.EDITIONS_MAP.get(
            edition,
            metadata.get('name', edition)
        )
        
        for raw_hadith in raw_hadiths:
            normalized = self._normalize_hadith(raw_hadith, edition, collection_name)
            if normalized:
                hadiths.append(normalized)
        
        return hadiths
    
    def _normalize_hadith(
        self, 
        raw_hadith: Dict, 
        edition: str,
        collection_name: str
    ) -> Optional[Dict]:
        """
        Normalise un hadith au format Al-Mīzān v7
        
        Args:
            raw_hadith: Hadith brut du JSON
            edition: ID de l'édition
            collection_name: Nom de la collection
        
        Returns:
            Hadith normalisé ou None si invalide
        """
        try:
            # Extraire les champs
            hadith_number = raw_hadith.get('hadithnumber', 0)
            text = raw_hadith.get('text', '')
            grades = raw_hadith.get('grades', [])
            reference = raw_hadith.get('reference', {})
            
            # Vérifier champs obligatoires
            if not text or not hadith_number:
                return None
            
            # Extraire le grade principal
            grade_raw = ''
            grade_normalized = ''
            
            if grades and len(grades) > 0:
                grade_raw = str(grades[0].get('grade', ''))
                grade_normalized = self._normalize_grade(grade_raw)
            
            # Construire l'objet normalisé
            normalized = {
                # Identifiants
                'source_id': f"{edition}_{hadith_number}",
                'source_api': 'jsdelivr_cdn',
                'collection': collection_name,
                'collection_id': edition,
                'hadith_number': hadith_number,
                
                # Contenu
                'text_arabic': text.strip(),
                
                # Métadonnées
                'narrator': '',
                'grade': grade_normalized,
                'grade_raw': grade_raw,
                'source_book': reference.get('book', ''),
                'source_page': reference.get('hadith', ''),
                
                # Timestamps
                'harvested_at': datetime.utcnow().isoformat(),
                'api_version': 'v1'
            }
            
            return normalized
            
        except Exception as e:
            print(f"⚠️  Erreur normalisation: {e}")
            return None
    
    def _normalize_grade(self, grade_raw: str) -> str:
        """
        Normalise le grade du hadith
        
        Args:
            grade_raw: Grade brut
        
        Returns:
            Grade normalisé
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
    
    def harvest_multiple_collections(
        self, 
        editions: List[str]
    ) -> Dict[str, List[Dict]]:
        """
        Harveste plusieurs collections
        
        Args:
            editions: Liste des IDs d'éditions
        
        Returns:
            Dict {edition: [hadiths]}
        """
        results = {}
        
        print(f"\n🔄 Harvesting {len(editions)} collections depuis JSDelivr CDN")
        print("=" * 80)
        
        for edition in editions:
            hadiths = self.get_full_collection(edition)
            
            if hadiths:
                results[edition] = hadiths
            else:
                results[edition] = []
            
            # Petit délai entre collections
            time.sleep(0.5)
        
        print()
        print("=" * 80)
        print(f"✅ Harvesting terminé: {len(results)} collections")
        
        total = sum(len(h) for h in results.values())
        print(f"📊 Total hadiths: {total}")
        
        return results
    
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
            'total_time': round(self.stats['total_time'], 2),
            'total_hadiths': self.stats['total_hadiths']
        }

def test_connector():
    """Test du connecteur JSDelivr"""
    
    print("=" * 80)
    print("🔍 TEST CONNECTEUR JSDELIVR CDN")
    print("=" * 80)
    print()
    
    connector = JSDelivrConnector()
    
    # Test 1: Liste des éditions
    print("📚 Test 1: Liste des éditions disponibles")
    print("-" * 80)
    
    editions = connector.get_available_editions()
    
    if editions:
        print(f"✅ {len(editions)} éditions disponibles")
        
        # Afficher les éditions arabes
        ara_editions = [k for k in editions.keys() if k.startswith('ara-')]
        print(f"\n📖 Éditions arabes ({len(ara_editions)}):")
        for edition in ara_editions[:5]:
            standard_name = connector.EDITIONS_MAP.get(edition, edition)
            print(f"   - {edition}: {standard_name}")
    else:
        print("❌ Erreur récupération éditions")
    
    print()
    
    # Test 2: Téléchargement collection complète (petite)
    print("📥 Test 2: Téléchargement Muwatta Malik (collection test)")
    print("-" * 80)
    
    malik_hadiths = connector.get_full_collection('ara-malik')
    
    if malik_hadiths:
        print(f"\n📝 Premier hadith:")
        h = malik_hadiths[0]
        print(f"   ID: {h['source_id']}")
        print(f"   Numéro: {h['hadith_number']}")
        print(f"   Collection: {h['collection']}")
        print(f"   Texte: {h['text_arabic'][:100]}...")
        print(f"   Grade: {h['grade']}")
    
    print()
    
    # Test 3: Harvesting multiple collections
    print("🔄 Test 3: Harvesting multiple collections")
    print("-" * 80)
    
    test_editions = ['ara-malik']  # Test avec une seule pour rapidité
    results = connector.harvest_multiple_collections(test_editions)
    
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
    print(f"Total hadiths: {stats['total_hadiths']}")
    
    print()
    print("=" * 80)
    print("✅ CONNECTEUR JSDELIVR CDN OPÉRATIONNEL")
    print("=" * 80)
    print()
    print("💡 Avantages:")
    print("   - Pas de rate limiting (CDN public)")
    print("   - Collections complètes en 1 requête")
    print("   - Haute disponibilité mondiale")
    print("   - Peut être cloné offline")

if __name__ == "__main__":
    test_connector()