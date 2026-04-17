#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Normalizer AL-MĪZĀN V6.0
Uniformise les données de différentes sources vers le schéma standard
"""

import csv
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from io import StringIO

class HadithNormalizer:
    """Normalise les hadiths de différentes sources"""
    
    # Mapping des noms de livres
    BOOK_MAPPING = {
        'bukhari': 'Sahih al-Bukhari',
        'muslim': 'Sahih Muslim',
        'tirmidhi': 'Sunan al-Tirmidhi',
        'abudawud': 'Sunan Abu Dawud',
        'nasai': "Sunan al-Nasa'i",
        'ibnmajah': 'Sunan Ibn Majah',
        'malik': "Muwatta' Malik",
        'ahmad': 'Musnad Ahmad',
        'darimi': 'Sunan al-Darimi'
    }
    
    def __init__(self):
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'errors': 0,
            'by_source': {}
        }
    
    def normalize_mhashim6_csv(self, csv_content: str, book_name: str) -> List[Dict[str, Any]]:
        """
        Normalise les données CSV de mhashim6/Open-Hadith-Data
        Format: hadith_number, full_text
        """
        hadiths = []
        reader = csv.reader(StringIO(csv_content))
        
        # Sauter l'en-tête si présent
        first_row = next(reader, None)
        if first_row and not first_row[0].isdigit():
            pass  # C'était l'en-tête
        else:
            # Traiter la première ligne
            if first_row:
                hadith = self._process_mhashim6_row(first_row, book_name)
                if hadith:
                    hadiths.append(hadith)
        
        # Traiter le reste
        for row in reader:
            hadith = self._process_mhashim6_row(row, book_name)
            if hadith:
                hadiths.append(hadith)
                self.stats['successful'] += 1
            else:
                self.stats['errors'] += 1
            self.stats['total_processed'] += 1
        
        return hadiths
    
    def _process_mhashim6_row(self, row: List[str], book_name: str) -> Optional[Dict[str, Any]]:
        """Traite une ligne CSV de mhashim6"""
        if len(row) < 2:
            return None
        
        try:
            hadith_number = int(row[0])
            full_text = row[1].strip()
            
            # Extraire isnad et matn (approximatif)
            isnad, matn = self._split_isnad_matn(full_text)
            
            return {
                'source': 'mhashim6/Open-Hadith-Data',
                'book': self.BOOK_MAPPING.get(book_name, book_name),
                'book_code': book_name,
                'hadith_number': hadith_number,
                'full_text_ar': full_text,
                'isnad_ar': isnad,
                'matn_ar': matn,
                'grade': None,  # À enrichir plus tard
                'narrator_chain': self._extract_narrators(isnad),
                'imported_at': datetime.now().isoformat(),
                'metadata': {
                    'source_format': 'csv',
                    'original_number': hadith_number
                }
            }
        except Exception as e:
            print(f"Erreur traitement ligne: {e}")
            return None
    
    def _split_isnad_matn(self, text: str) -> tuple:
        """
        Sépare approximativement l'isnad du matn
        Cherche des marqueurs comme "قال" suivi de citation
        """
        # Marqueurs communs de début de matn
        markers = [
            'قال رسول الله',
            'قال النبي',
            'عن النبي',
            'أن رسول الله',
            'أن النبي'
        ]
        
        for marker in markers:
            if marker in text:
                parts = text.split(marker, 1)
                if len(parts) == 2:
                    return parts[0].strip(), marker + parts[1].strip()
        
        # Si pas de marqueur trouvé, considérer tout comme isnad+matn
        return text, ""
    
    def _extract_narrators(self, isnad: str) -> List[str]:
        """
        Extrait les noms des narrateurs de l'isnad
        Cherche les patterns "حدثنا X" ou "عن X"
        """
        narrators = []
        
        # Patterns de narration
        patterns = [
            r'حدثنا\s+([^قال]+?)(?=\s+قال|\s+عن|$)',
            r'أخبرنا\s+([^قال]+?)(?=\s+قال|\s+عن|$)',
            r'عن\s+([^قال]+?)(?=\s+قال|\s+عن|$)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, isnad)
            narrators.extend([m.strip() for m in matches])
        
        return narrators
    
    def normalize_json_source(self, json_data: Dict, source_name: str) -> List[Dict[str, Any]]:
        """Normalise les données JSON (pour sources futures)"""
        # À implémenter selon le format JSON
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de normalisation"""
        return self.stats
    
    def reset_stats(self):
        """Réinitialise les statistiques"""
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'errors': 0,
            'by_source': {}
        }

def test_normalizer():
    """Test du normalizer avec un échantillon"""
    print("=== TEST NORMALIZER ===\n")
    
    # Exemple de données CSV
    sample_csv = """1, حدثنا الحميدي عبد الله بن الزبير قال حدثنا سفيان قال حدثنا يحيى بن سعيد الأنصاري قال أخبرني محمد بن إبراهيم التيمي أنه سمع علقمة بن وقاص الليثي يقول سمعت عمر بن الخطاب رضي الله عنه على المنبر قال سمعت رسول الله صلى الله عليه وسلم يقول إنما الأعمال بالنيات وإنما لكل امرئ ما نوى فمن كانت هجرته إلى دنيا يصيبها أو إلى امرأة ينكحها فهجرته إلى ما هاجر إليه
2, حدثنا عبد الله بن يوسف قال أخبرنا مالك عن هشام بن عروة عن أبيه عن عائشة أم المؤمنين رضي الله عنها"""
    
    normalizer = HadithNormalizer()
    hadiths = normalizer.normalize_mhashim6_csv(sample_csv, 'bukhari')
    
    print(f"Hadiths normalisés: {len(hadiths)}\n")
    
    if hadiths:
        print("Exemple de hadith normalisé:")
        print(json.dumps(hadiths[0], indent=2, ensure_ascii=False))
    
    print(f"\nStatistiques:")
    print(json.dumps(normalizer.get_stats(), indent=2))

if __name__ == '__main__':
    test_normalizer()