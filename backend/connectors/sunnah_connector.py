#!/usr/bin/env python3
"""
Connecteur pour sunnah.com API
Permet d'importer :
- 40 Hadiths de Nawawi (An-Nawawi's 40 Hadith)
- Riyad al-Salihin
- Al-Adab Al-Mufrad
- Bulugh al-Maram
"""

import requests
import time
import json
from typing import Dict, List, Optional

class SunnahConnector:
    """Connecteur pour l'API sunnah.com"""
    
    BASE_URL = "https://api.sunnah.com/v1"
    
    # Mapping des collections
    COLLECTIONS = {
        'nawawi40': {
            'name': 'An-Nawawi\'s 40 Hadith',
            'collection_name': 'nawawi40',
            'total_hadiths': 42
        },
        'riyadussalihin': {
            'name': 'Riyad as-Salihin',
            'collection_name': 'riyadussalihin',
            'total_hadiths': 1896
        },
        'adab': {
            'name': 'Al-Adab Al-Mufrad',
            'collection_name': 'adab',
            'total_hadiths': 1322
        },
        'bulugh': {
            'name': 'Bulugh al-Maram',
            'collection_name': 'bulugh',
            'total_hadiths': 1358
        }
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise le connecteur
        
        Args:
            api_key: Clé API sunnah.com (optionnelle pour certaines requêtes)
        """
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'X-API-Key': api_key})
    
    def get_collection_info(self, collection_key: str) -> Dict:
        """Récupère les informations d'une collection"""
        if collection_key not in self.COLLECTIONS:
            raise ValueError(f"Collection inconnue : {collection_key}")
        
        return self.COLLECTIONS[collection_key]
    
    def get_hadith(self, collection: str, hadith_number: int) -> Optional[Dict]:
        """
        Récupère un hadith spécifique
        
        Args:
            collection: Nom de la collection (ex: 'nawawi40')
            hadith_number: Numéro du hadith
            
        Returns:
            Dict contenant les données du hadith ou None si erreur
        """
        url = f"{self.BASE_URL}/collections/{collection}/hadiths/{hadith_number}"
        
        try:
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_hadith(data, collection)
            elif response.status_code == 404:
                print(f"Hadith {hadith_number} non trouvé dans {collection}")
                return None
            else:
                print(f"Erreur {response.status_code} pour hadith {hadith_number}")
                return None
                
        except Exception as e:
            print(f"Erreur lors de la récupération du hadith {hadith_number}: {e}")
            return None
    
    def get_all_hadiths(self, collection_key: str, delay: float = 0.5) -> List[Dict]:
        """
        Récupère tous les hadiths d'une collection
        
        Args:
            collection_key: Clé de la collection (ex: 'nawawi40')
            delay: Délai entre les requêtes en secondes
            
        Returns:
            Liste des hadiths
        """
        collection_info = self.get_collection_info(collection_key)
        collection_name = collection_info['collection_name']
        total = collection_info['total_hadiths']
        
        print(f"\n📚 Import de {collection_info['name']}")
        print(f"Total attendu : {total} hadiths")
        print("-" * 60)
        
        hadiths = []
        errors = 0
        
        for i in range(1, total + 1):
            hadith = self.get_hadith(collection_name, i)
            
            if hadith:
                hadiths.append(hadith)
                if i % 10 == 0:
                    print(f"✅ {i}/{total} hadiths récupérés")
            else:
                errors += 1
            
            # Respecter le rate limiting
            time.sleep(delay)
        
        print(f"\n✅ Import terminé : {len(hadiths)} hadiths récupérés")
        if errors > 0:
            print(f"⚠️  {errors} erreurs rencontrées")
        
        return hadiths
    
    def _parse_hadith(self, data: Dict, collection: str) -> Dict:
        """
        Parse les données d'un hadith depuis l'API sunnah.com
        
        Args:
            data: Données brutes de l'API
            collection: Nom de la collection
            
        Returns:
            Dict formaté pour notre base de données
        """
        hadith_data = data.get('hadith', [{}])[0] if isinstance(data.get('hadith'), list) else data.get('hadith', {})
        
        # Extraire le texte arabe
        matn_ar = ''
        if 'body' in hadith_data:
            matn_ar = hadith_data['body']
        elif 'hadithArabic' in hadith_data:
            matn_ar = hadith_data['hadithArabic']
        
        # Extraire le texte anglais
        matn_en = ''
        if 'hadithEnglish' in hadith_data:
            matn_en = hadith_data['hadithEnglish']
        
        # Extraire la référence
        reference = ''
        if 'reference' in hadith_data:
            ref_data = hadith_data['reference']
            if isinstance(ref_data, dict):
                reference = ref_data.get('book', '') + ' ' + str(ref_data.get('hadith', ''))
            else:
                reference = str(ref_data)
        
        # Extraire le grade
        grade = ''
        if 'grades' in hadith_data and hadith_data['grades']:
            grades = hadith_data['grades']
            if isinstance(grades, list) and len(grades) > 0:
                grade = grades[0].get('grade', '')
        
        # Normaliser le nom de la collection
        collection_normalized = self._normalize_collection_name(collection)
        
        return {
            'collection': collection_normalized,
            'numero_hadith': str(hadith_data.get('hadithNumber', '')),
            'matn_ar': self._clean_text(matn_ar),
            'matn_en': self._clean_text(matn_en),
            'grade_final': grade,
            'reference': reference,
            'source_api': 'sunnah.com'
        }
    
    def _normalize_collection_name(self, collection: str) -> str:
        """Normalise le nom de la collection"""
        mapping = {
            'nawawi40': 'forty_hadith_nawawi',
            'riyadussalihin': 'riyad_salihin',
            'adab': 'adab_mufrad',
            'bulugh': 'bulugh_maram'
        }
        return mapping.get(collection, collection)
    
    def _clean_text(self, text: str) -> str:
        """Nettoie le texte (enlève les balises HTML, etc.)"""
        if not text:
            return ''
        
        # Enlever les balises HTML simples
        import re
        text = re.sub(r'<[^>]+>', '', text)
        
        # Nettoyer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def export_to_json(self, hadiths: List[Dict], filename: str):
        """Exporte les hadiths en JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(hadiths, f, ensure_ascii=False, indent=2)
        print(f"✅ Hadiths exportés vers {filename}")

def main():
    """Test du connecteur"""
    connector = SunnahConnector()
    
    # Test avec les 40 Hadiths de Nawawi (petit dataset)
    print("🧪 Test avec les 40 Hadiths de Nawawi...")
    hadiths = connector.get_all_hadiths('nawawi40', delay=0.5)
    
    if hadiths:
        print(f"\n📊 Exemple de hadith récupéré:")
        print(json.dumps(hadiths[0], ensure_ascii=False, indent=2))
        
        # Exporter
        connector.export_to_json(hadiths, 'output/nawawi40_test.json')

if __name__ == '__main__':
    main()