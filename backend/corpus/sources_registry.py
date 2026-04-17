#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Registre des sources prioritaires AL-MĪZĀN V6.0
Définition des sources GitHub, Hugging Face et sites officiels
"""

from typing import Dict, List, Any
from datetime import datetime

# Sources GitHub prioritaires
GITHUB_SOURCES = [
    {
        'id': 'hadith-json-ahmedbaset',
        'name': 'AhmedBaset/hadith-json',
        'url': 'https://github.com/AhmedBaset/hadith-json',
        'type': 'github',
        'description': '50,884 hadiths, 17 livres, AR+EN',
        'raw_data_url': 'https://raw.githubusercontent.com/AhmedBaset/hadith-json/main/data',
        'books': [
            'bukhari', 'muslim', 'tirmidhi', 'abudawud', 'nasai', 
            'ibnmajah', 'malik', 'ahmad', 'darimi'
        ],
        'license': 'Open Data',
        'reliability_score': 95,
        'priority': 1
    },
    {
        'id': 'open-hadith-data-mhashim',
        'name': 'mhashim6/Open-Hadith-Data',
        'url': 'https://github.com/mhashim6/Open-Hadith-Data',
        'type': 'github',
        'description': '9 livres majeurs en CSV (format: numéro, texte complet)',
        'raw_data_url': 'https://raw.githubusercontent.com/mhashim6/Open-Hadith-Data/master',
        'books': {
            'bukhari': 'Sahih_Al-Bukhari/sahih_al-bukhari_ahadith.utf8.csv',
            'muslim': 'Sahih_Muslim/sahih_muslim_ahadith.utf8.csv',
            'tirmidhi': 'Sunan_Al-Tirmidhi/sunan_al-tirmidhi_ahadith.utf8.csv',
            'abudawud': 'Sunan_Abu-Dawud/sunan_abu-dawud_ahadith.utf8.csv',
            'nasai': 'Sunan_Al-Nasai/sunan_al-nasai_ahadith.utf8.csv',
            'ibnmajah': 'Sunan_Ibn-Maja/sunan_ibn-maja_ahadith.utf8.csv',
            'malik': 'Maliks_Muwataa/maliks_muwataa_ahadith.utf8.csv',
            'ahmad': 'Musnad_Ahmad_Ibn-Hanbal/musnad_ahmad_ibn-hanbal_ahadith.utf8.csv',
            'darimi': 'Sunan_Al-Darimi/sunan_al-darimi_ahadith.utf8.csv'
        },
        'format': 'csv',
        'columns': ['hadith_number', 'full_text'],
        'license': 'MIT',
        'reliability_score': 90,
        'priority': 2
    },
    {
        'id': 'hadith-api-fawazahmed',
        'name': 'fawazahmed0/hadith-api',
        'url': 'https://github.com/fawazahmed0/hadith-api',
        'type': 'github',
        'description': 'API multi-langues avec grades',
        'raw_data_url': 'https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1',
        'books': ['bukhari', 'muslim', 'tirmidhi', 'abudawud', 'nasai', 'ibnmajah'],
        'license': 'Public Domain',
        'reliability_score': 85,
        'priority': 3
    },
    {
        'id': 'shamela-ragaeeb',
        'name': 'ragaeeb/shamela',
        'url': 'https://github.com/ragaeeb/shamela',
        'type': 'github',
        'description': 'Bibliothèque Node/TS pour Shamela v4',
        'raw_data_url': None,  # Nécessite installation npm
        'books': [],
        'license': 'MIT',
        'reliability_score': 80,
        'priority': 4,
        'notes': 'Nécessite installation npm et téléchargement via API'
    }
]

# Sources Hugging Face
HUGGINGFACE_SOURCES = [
    {
        'id': 'hadith-datasets-meeatif',
        'name': 'meeAtif/hadith_datasets',
        'url': 'https://huggingface.co/datasets/meeAtif/hadith_datasets',
        'type': 'huggingface',
        'description': 'JSON/CSV des 6 livres majeurs',
        'raw_data_url': 'https://huggingface.co/datasets/meeAtif/hadith_datasets/resolve/main',
        'books': ['bukhari', 'muslim', 'tirmidhi', 'abudawud', 'nasai', 'ibnmajah'],
        'license': 'Apache 2.0',
        'reliability_score': 90,
        'priority': 2
    }
]

# Sites officiels Salafi (pour fatwas et tahqiq)
OFFICIAL_SITES = [
    {
        'id': 'binbaz-official',
        'name': 'binbaz.org.sa',
        'url': 'https://binbaz.org.sa',
        'type': 'fatwa_site',
        'description': 'Site officiel Cheikh Bin Bāz',
        'reliability_score': 100,
        'priority': 1,
        'notes': 'Source primaire pour fatwas et tahqiq Bin Bāz'
    },
    {
        'id': 'alifta-lajnah',
        'name': 'alifta.gov.sa',
        'url': 'https://www.alifta.gov.sa',
        'type': 'fatwa_site',
        'description': 'Lajnah Permanente (Comité Permanent)',
        'reliability_score': 100,
        'priority': 1,
        'notes': 'Fatwas officielles du Royaume'
    },
    {
        'id': 'rabee-net',
        'name': 'rabee.net',
        'url': 'https://www.rabee.net',
        'type': 'fatwa_site',
        'description': 'Site Cheikh Rabīʿ al-Madkhalī',
        'reliability_score': 95,
        'priority': 2,
        'notes': 'Spécialiste en Jarh wa Taʿdīl'
    },
    {
        'id': 'salafipublications',
        'name': 'salafipublications.com',
        'url': 'https://www.salafipublications.com',
        'type': 'website',
        'description': 'Publications salafies en anglais',
        'reliability_score': 90,
        'priority': 3,
        'notes': 'Traductions vérifiées'
    }
]

# Savants prioritaires pour tahqiq
PRIORITY_SCHOLARS = [
    {
        'name': 'Muhammad Nasir al-Din al-Albani',
        'name_ar': 'محمد ناصر الدين الألباني',
        'specialization': 'Hadith Science',
        'works': [
            'Silsilat al-Ahadith as-Sahihah',
            'Silsilat al-Ahadith ad-Daifah',
            'Sahih al-Jami',
            'Daif al-Jami'
        ],
        'reliability_level': 'thiqa',
        'priority': 1
    },
    {
        'name': 'Abdul-Aziz bin Baz',
        'name_ar': 'عبد العزيز بن باز',
        'specialization': 'Fiqh & Aqidah',
        'works': ['Majmu Fatawa', 'Tahqiq kutub'],
        'reliability_level': 'thiqa',
        'priority': 1
    },
    {
        'name': 'Muqbil bin Hadi al-Wadi\'i',
        'name_ar': 'مقبل بن هادي الوادعي',
        'specialization': 'Hadith Science',
        'works': ['Al-Jami as-Sahih', 'Al-Muharrar'],
        'reliability_level': 'thiqa',
        'priority': 1
    },
    {
        'name': 'Salih al-Fawzan',
        'name_ar': 'صالح الفوزان',
        'specialization': 'Fiqh & Aqidah',
        'works': ['Sharh Kitab at-Tawhid', 'Al-Mulakhas al-Fiqhi'],
        'reliability_level': 'thiqa',
        'priority': 2
    },
    {
        'name': 'Muhammad bin Salih al-Uthaymin',
        'name_ar': 'محمد بن صالح العثيمين',
        'specialization': 'Fiqh & Tafsir',
        'works': ['Sharh Bulugh al-Maram', 'Tafsir al-Quran'],
        'reliability_level': 'thiqa',
        'priority': 2
    }
]

def get_all_sources() -> List[Dict[str, Any]]:
    """Obtenir toutes les sources"""
    return GITHUB_SOURCES + HUGGINGFACE_SOURCES + OFFICIAL_SITES

def get_sources_by_priority() -> List[Dict[str, Any]]:
    """Obtenir les sources triées par priorité"""
    all_sources = get_all_sources()
    return sorted(all_sources, key=lambda x: x.get('priority', 999))

def get_source_by_id(source_id: str) -> Dict[str, Any]:
    """Obtenir une source par son ID"""
    for source in get_all_sources():
        if source['id'] == source_id:
            return source
    return None

def get_downloadable_sources() -> List[Dict[str, Any]]:
    """Obtenir uniquement les sources téléchargeables directement"""
    return [s for s in get_all_sources() if s.get('raw_data_url')]

def format_source_for_db(source: Dict[str, Any]) -> Dict[str, Any]:
    """Formater une source pour insertion en base de données"""
    return {
        'id': source['id'],
        'name': source['name'],
        'url': source['url'],
        'type': source['type'],
        'license': source.get('license'),
        'last_access': datetime.now().isoformat(),
        'reliability_score': source.get('reliability_score', 50),
        'notes': source.get('notes', source.get('description', ''))
    }

def get_source_stats() -> Dict[str, Any]:
    """Obtenir des statistiques sur les sources"""
    all_sources = get_all_sources()
    return {
        'total': len(all_sources),
        'github': len(GITHUB_SOURCES),
        'huggingface': len(HUGGINGFACE_SOURCES),
        'official_sites': len(OFFICIAL_SITES),
        'downloadable': len(get_downloadable_sources()),
        'avg_reliability': sum(s.get('reliability_score', 0) for s in all_sources) / len(all_sources)
    }

if __name__ == '__main__':
    print("=== REGISTRE DES SOURCES AL-MĪZĀN V6.0 ===\n")
    stats = get_source_stats()
    print(f"Total sources: {stats['total']}")
    print(f"  - GitHub: {stats['github']}")
    print(f"  - Hugging Face: {stats['huggingface']}")
    print(f"  - Sites officiels: {stats['official_sites']}")
    print(f"  - Téléchargeables: {stats['downloadable']}")
    print(f"  - Fiabilité moyenne: {stats['avg_reliability']:.1f}/100")
    
    print("\n=== SOURCES PAR PRIORITÉ ===")
    for source in get_sources_by_priority()[:5]:
        print(f"{source['priority']}. {source['name']} ({source['type']}) - Fiabilité: {source.get('reliability_score', 'N/A')}")