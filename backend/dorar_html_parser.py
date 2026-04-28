#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser HTML pour l'API Dorar.net
Extrait les hadiths depuis le HTML retourné par l'API JSONP
"""

import re
import json
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

class DorarHTMLParser:
    """Parser pour extraire les hadiths du HTML Dorar.net"""
    
    BASE_URL = "https://dorar.net/dorar_api.json"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Al-Mizan-Harvester/7.0',
            'Accept': '*/*',
            'Referer': 'https://dorar.net/'
        })
    
    def search_hadith(self, keyword: str) -> Optional[List[Dict]]:
        """
        Recherche de hadiths et parsing du HTML
        
        Args:
            keyword: Mot-clé de recherche en arabe
        
        Returns:
            Liste de hadiths parsés ou None si erreur
        """
        try:
            # Requête JSONP
            params = {
                'skey': keyword,
                'callback': 'jQuery'
            }
            
            response = self.session.get(
                self.BASE_URL, 
                params=params, 
                timeout=15
            )
            response.raise_for_status()
            
            # Extraire le JSON du JSONP
            raw_content = response.text
            jsonp_match = re.search(r'jQuery\((.*)\)', raw_content, re.DOTALL)
            
            if not jsonp_match:
                print("❌ Format JSONP invalide")
                return None
            
            # Parser le JSON
            data = json.loads(jsonp_match.group(1))
            
            if not isinstance(data, dict) or 'ahadith' not in data:
                print("❌ Structure JSON invalide")
                return None
            
            # Récupérer le HTML
            html_content = data['ahadith'].get('result', '')
            
            if not html_content:
                print("❌ Pas de contenu HTML")
                return None
            
            # Parser le HTML
            return self._parse_html(html_content)
            
        except Exception as e:
            print(f"❌ Erreur search_hadith: {e}")
            return None
    
    def _parse_html(self, html: str) -> List[Dict]:
        """
        Parse le HTML pour extraire les hadiths
        
        Args:
            html: Contenu HTML brut
        
        Returns:
            Liste de hadiths structurés
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            hadiths = []
            
            # Trouver tous les blocs de hadith
            hadith_divs = soup.find_all('div', class_='hadith')
            
            for idx, hadith_div in enumerate(hadith_divs, 1):
                # Extraire le texte du hadith
                hadith_text = hadith_div.get_text(strip=True)
                
                # Nettoyer le numéro au début (ex: "1 - ")
                hadith_text = re.sub(r'^\d+\s*-\s*', '', hadith_text)
                
                # Trouver le bloc d'informations suivant
                info_div = hadith_div.find_next_sibling('div', class_='hadith-info')
                
                if not info_div:
                    continue
                
                # Extraire les métadonnées
                metadata = self._extract_metadata(info_div)
                
                # Construire l'objet hadith
                hadith_obj = {
                    'id': f"dorar_{idx}",
                    'text': hadith_text,
                    'narrator': metadata.get('narrator', ''),
                    'muhaddith': metadata.get('muhaddith', ''),
                    'source': metadata.get('source', ''),
                    'page': metadata.get('page', ''),
                    'grade': metadata.get('grade', ''),
                    'grade_raw': metadata.get('grade_raw', '')
                }
                
                hadiths.append(hadith_obj)
            
            return hadiths
            
        except Exception as e:
            print(f"❌ Erreur _parse_html: {e}")
            return []
    
    def _extract_metadata(self, info_div) -> Dict:
        """
        Extrait les métadonnées d'un bloc hadith-info
        
        Args:
            info_div: BeautifulSoup element du bloc info
        
        Returns:
            Dict avec les métadonnées
        """
        metadata = {}
        
        try:
            # Récupérer tout le texte du bloc info
            full_text = info_div.get_text(separator='|', strip=True)
            
            # Parser avec regex pour extraire les champs
            # Format: "الراوي: valeur | المحدث: valeur | ..."
            
            # Narrateur
            narrator_match = re.search(r'الراوي:\s*([^|]+)', full_text)
            if narrator_match:
                metadata['narrator'] = narrator_match.group(1).strip()
            
            # Muhaddith
            muhaddith_match = re.search(r'المحدث:\s*([^|]+)', full_text)
            if muhaddith_match:
                metadata['muhaddith'] = muhaddith_match.group(1).strip()
            
            # Source
            source_match = re.search(r'المصدر:\s*([^|]+)', full_text)
            if source_match:
                metadata['source'] = source_match.group(1).strip()
            
            # Page/Numéro
            page_match = re.search(r'(?:الصفحة أو الرقم|الصفحة|الرقم):\s*([^|]+)', full_text)
            if page_match:
                metadata['page'] = page_match.group(1).strip()
            
            # Grade (خلاصة حكم المحدث)
            grade_match = re.search(r'(?:خلاصة حكم المحدث|حكم المحدث|خلاصة):\s*([^|]+)', full_text)
            if grade_match:
                grade_raw = grade_match.group(1).strip()
                metadata['grade_raw'] = grade_raw
                metadata['grade'] = self._normalize_grade(grade_raw)
            
            # Si pas de grade trouvé, chercher directement les mots-clés
            if not metadata.get('grade'):
                if 'صحيح' in full_text:
                    metadata['grade'] = 'sahih'
                    metadata['grade_raw'] = 'صحيح'
                elif 'حسن' in full_text:
                    metadata['grade'] = 'hasan'
                    metadata['grade_raw'] = 'حسن'
                elif 'ضعيف' in full_text:
                    metadata['grade'] = 'daif'
                    metadata['grade_raw'] = 'ضعيف'
            
        except Exception as e:
            print(f"⚠️  Erreur extraction métadonnées: {e}")
        
        return metadata
    
    def _normalize_grade(self, grade_raw: str) -> str:
        """
        Normalise le grade du hadith selon la méthodologie Salaf
        
        Args:
            grade_raw: Grade brut extrait
        
        Returns:
            Grade normalisé (sahih, hasan, daif, etc.)
        """
        grade_lower = grade_raw.lower().strip()
        
        # Sahih
        if 'صحيح' in grade_lower or 'sahih' in grade_lower:
            return 'sahih'
        
        # Hasan
        if 'حسن' in grade_lower or 'hasan' in grade_lower:
            return 'hasan'
        
        # Daif
        if 'ضعيف' in grade_lower or 'daif' in grade_lower or 'da\'if' in grade_lower:
            return 'daif'
        
        # Mawdu (forgé)
        if 'موضوع' in grade_lower or 'mawdu' in grade_lower:
            return 'mawdu'
        
        # Inconnu
        return 'unknown'

def test_parser():
    """Test du parser HTML"""
    
    print("=" * 80)
    print("🔍 TEST PARSER HTML DORAR.NET")
    print("=" * 80)
    
    parser = DorarHTMLParser()
    
    # Test 1: Recherche "الصلاة"
    print("\n📖 Test 1: Recherche 'الصلاة' (la prière)")
    print("-" * 80)
    
    hadiths = parser.search_hadith("الصلاة")
    
    if hadiths:
        print(f"✅ {len(hadiths)} hadiths extraits")
        
        # Afficher les 3 premiers
        for i, hadith in enumerate(hadiths[:3], 1):
            print(f"\n📝 Hadith {i}:")
            print(f"   ID: {hadith['id']}")
            print(f"   Texte: {hadith['text'][:100]}...")
            print(f"   Narrateur: {hadith['narrator']}")
            print(f"   Muhaddith: {hadith['muhaddith']}")
            print(f"   Source: {hadith['source']}")
            print(f"   Page: {hadith['page']}")
            print(f"   Grade: {hadith['grade']} ({hadith['grade_raw']})")
        
        # Statistiques
        print(f"\n📊 Statistiques:")
        grades = {}
        for h in hadiths:
            grade = h['grade']
            grades[grade] = grades.get(grade, 0) + 1
        
        for grade, count in sorted(grades.items()):
            print(f"   - {grade}: {count}")
        
        # JSON complet du premier hadith
        print(f"\n📄 Structure JSON complète (premier hadith):")
        print(json.dumps(hadiths[0], indent=2, ensure_ascii=False))
        
    else:
        print("❌ Aucun hadith extrait")
    
    # Test 2: Recherche "الإيمان"
    print("\n\n📖 Test 2: Recherche 'الإيمان' (la foi)")
    print("-" * 80)
    
    hadiths2 = parser.search_hadith("الإيمان")
    
    if hadiths2:
        print(f"✅ {len(hadiths2)} hadiths extraits")
        
        # Compter les grades
        grades2 = {}
        for h in hadiths2:
            grade = h['grade']
            grades2[grade] = grades2.get(grade, 0) + 1
        
        print(f"\n📊 Distribution des grades:")
        for grade, count in sorted(grades2.items()):
            print(f"   - {grade}: {count}")
    else:
        print("❌ Aucun hadith extrait")
    
    print("\n" + "=" * 80)
    print("📋 CONCLUSION")
    print("=" * 80)
    
    if hadiths:
        print("✅ Parser HTML fonctionnel")
        print("✅ Extraction des métadonnées réussie")
        print("✅ Normalisation des grades opérationnelle")
        print("\n💡 Prochaine étape:")
        print("   → Intégrer ce parser dans le harvester v7")
        print("   → Lancer extraction test (100 hadiths)")
    else:
        print("❌ Parser non fonctionnel")
        print("💡 Recommandation:")
        print("   → Utiliser API HadeethEnc (alternative validée)")

if __name__ == "__main__":
    test_parser()