#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Registre des sources AL-MĪZĀN V7.0
Sources vérifiées en temps réel (avril 2026)
Conforme au document Corpus V7.0
"""

from typing import Dict, List, Any
from datetime import datetime

# ============================================================
# PRIORITÉ 1 — fawazahmed0/hadith-api ✅ ACTIF
# ============================================================
FAWAZAHMED0_SOURCE = {
    'id': 'fawazahmed0-hadith-api',
    'name': 'fawazahmed0/hadith-api',
    'url': 'https://github.com/fawazahmed0/hadith-api',
    'type': 'github',
    'cdn_base': 'https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1',
    'description': '7 livres en français + éditions arabes',
    'priority': 1,
    'reliability_score': 95,
    'license': 'unknown',
    'version_pin': '@1',
    'status': 'active',
    'last_verified': '2026-04-17',
    'books_fr': {
        'fra-bukhari': 'Sahih al-Bukhâri',
        'fra-muslim': 'Sahih Muslim',
        'fra-abudawud': 'Sunan Abû Dâwûd',
        'fra-ibnmajah': 'Sunan Ibn Mâjah',
        'fra-malik': 'Muwatta\' Mâlik',
        'fra-dehlawi': '40 Hadith Dehlawî',
        'fra-nawawi': '40 Hadith An-Nawawî'
    },
    'books_ar': {
        'ara-bukhari': 'صحيح البخاري',
        'ara-muslim': 'صحيح مسلم',
        'ara-abudawud': 'سنن أبي داود',
        'ara-nasai': 'سنن النسائي',
        'ara-tirmidhi': 'سنن الترمذي',
        'ara-ibnmajah': 'سنن ابن ماجه',
        'ara-malik': 'موطأ مالك',
        'ara-ahmad': 'مسند أحمد'
    },
    'notes': 'Traducteur français: Unknown. Pin obligatoire: @1 (jamais main)'
}

# ============================================================
# PRIORITÉ 2 — AhmedElTabarani/dorar-hadith-api ✅ ACTIF
# ============================================================
DORAR_API_SOURCE = {
    'id': 'dorar-hadith-api',
    'name': 'AhmedElTabarani/dorar-hadith-api',
    'url': 'https://github.com/AhmedElTabarani/dorar-hadith-api',
    'type': 'api',
    'description': 'Wrapper Dorar.net — Moteur de recherche hadith',
    'priority': 2,
    'reliability_score': 100,
    'license': 'open',
    'status': 'active',
    'last_verified': '2026-04-17',
    'stars': 108,
    'base_url_local': 'http://localhost:5000/v1',
    'base_url_production': None,  # À déployer sur Railway/Render
    'muhaddithun_ids': {
        'bukhari': 256,
        'muslim': 261,
        'abu_dawud': 275,
        'nasai': 279,
        'tirmidhi': 279,
        'ibn_majah': 279,
        'ahmad': 241,
        'malik': 179,
        'shafii': 204
    },
    'book_ids': {
        'sahih_bukhari': 6216,
        'sahih_muslim': 3088,
        'sunan_abu_dawud': 275,
        'sunan_nasai': 103,
        'muwatta_malik': 131,
        'sahih_musnad_muqbil': 96,
        'arbaun_nawawi': 13457
    },
    'notes': 'Résout le blocage Cloudflare de Dorar.net. Self-host recommandé.'
}

# ============================================================
# PRIORITÉ 3 — HadeethEnc.com API officielle ✅ ACTIF
# ============================================================
HADEETHENC_SOURCE = {
    'id': 'hadeethenc-api',
    'name': 'HadeethEnc.com API',
    'url': 'https://hadeethenc.com/api/v1/',
    'github': 'https://github.com/islamhouse-dev/hadith-api',
    'type': 'api',
    'description': 'API officielle supervisée par des savants',
    'priority': 3,
    'reliability_score': 100,
    'license': 'conditions',
    'status': 'active',
    'last_verified': '2026-04-17',
    'languages': ['fr', 'ar', 'en', '+20 langues'],
    'endpoints': {
        'languages': '/languages/',
        'categories_roots': '/categories/roots/?language=fr',
        'categories_list': '/categories/list/?language=fr',
        'hadeeths_list': '/hadeeths/list/?language=fr&category_id={id}&page={page}',
        'hadeeths_one': '/hadeeths/one/?id={id}&language=fr'
    },
    'conditions': [
        'Aucune modification du contenu',
        'Référence obligatoire à HadeethEnc.com',
        'Usage commercial interdit sans autorisation'
    ],
    'notes': 'Explication simplifiée (explanation) déjà rédigée par des savants en français'
}

# ============================================================
# PRIORITÉ 4 — IslamHouse-API Hub Français ✅ ACTIF
# ============================================================
ISLAMHOUSE_SOURCE = {
    'id': 'islamhouse-api-hub-fr',
    'name': 'IslamHouse-API / Hub Français',
    'url': 'https://github.com/IslamHouse-API/french-quran-hadith-islamic-content-database-api-hub',
    'type': 'api',
    'description': 'Centralise IslamHouse + QuranEnc + HadeethEnc en français',
    'priority': 4,
    'reliability_score': 95,
    'license': 'official',
    'status': 'active',
    'last_verified': '2026-04-17',
    'endpoints': {
        'fatwas': 'https://islamhouse.com/api/v3/items/type/fatwa/?language=fr',
        'articles': 'https://islamhouse.com/api/v3/items/type/article/?language=fr&category=aqeedah'
    },
    'usage_zones': {
        30: 'Fatâwâ Salafiyyah',
        31: 'Manâqib/Sîrah',
        11: 'Grading (via HadeethEnc)'
    },
    'notes': 'Supervisé officiellement. Mis à jour avril 2026.'
}

# ============================================================
# PRIORITÉ 5 — meeAtif/hadith_datasets ✅ ACTIF
# ============================================================
MEEATIF_SOURCE = {
    'id': 'meeatif-hadith-datasets',
    'name': 'meeAtif/hadith_datasets',
    'url': 'https://huggingface.co/datasets/meeAtif/hadith_datasets',
    'type': 'huggingface',
    'description': 'Les 6 livres majeurs en JSON/CSV',
    'priority': 5,
    'reliability_score': 90,
    'license': 'MIT',
    'status': 'active',
    'last_verified': '2026-04-17',
    'base_url': 'https://huggingface.co/datasets/meeAtif/hadith_datasets/resolve/main',
    'books': [
        'Sahih al-Bukhari.json',
        'Sahih Muslim.json',
        'Sunan al-Tirmidhi.json',
        'Sunan Abu Dawud.json',
        'Sunan al-Nasai.json',
        'Sunan Ibn Majah.json'
    ],
    'columns': ['Arabic_Text', 'English_Text', 'Chapter_Number', 'Chapter_Title_Arabic', 'Chapter_Title_English'],
    'notes': 'Seule source open data avec licence MIT claire. Pas de traduction française.'
}

# ============================================================
# PRIORITÉ 6 — AhmedBaset/hadith-json ⚠️ AVEC RÉSERVES
# ============================================================
AHMEDBASET_SOURCE = {
    'id': 'ahmedbaset-hadith-json',
    'name': 'AhmedBaset/hadith-json',
    'url': 'https://github.com/AhmedBaset/hadith-json',
    'type': 'github',
    'description': '50,884 hadiths, 17 livres, AR+EN',
    'priority': 6,
    'reliability_score': 70,
    'license': 'unknown',
    'status': 'active_with_bug',
    'last_verified': '2026-04-17',
    'stars': 229,
    'version_pin': 'v1.2.0',
    'bug_critical': {
        'issue': '#11',
        'description': 'idinBook erroné pour la majorité des hadiths',
        'opened': '2024-08',
        'status': 'non résolu',
        'workaround': 'Ne jamais utiliser idinBook pour traçabilité'
    },
    'usage': 'Texte arabe brut uniquement. Ne pas afficher idinBook comme référence canonique.',
    'notes': 'Pin OBLIGATOIRE: v1.2.0 (jamais main). Données vraisemblablement scrapées de sunnah.com.'
}

# ============================================================
# PRIORITÉ 7 — abdelrahmaan/Hadith-Data-Sets ✅ STABLE
# ============================================================
ABDELRAHMAAN_SOURCE = {
    'id': 'abdelrahmaan-hadith-datasets',
    'name': 'abdelrahmaan/Hadith-Data-Sets',
    'url': 'https://github.com/abdelrahmaan/Hadith-Data-Sets',
    'type': 'github',
    'description': '62,169 hadiths avec et sans tashkîl',
    'priority': 7,
    'reliability_score': 85,
    'license': 'unknown',
    'status': 'stable',
    'last_verified': '2026-04-17',
    'stars': 317,
    'last_update': '2022',
    'format': 'Jupyter/JSON',
    'advantage': 'Double format (avec/sans diacritiques) idéal pour recherche arabe',
    'notes': 'Stable depuis 2022. Arabe uniquement.'
}

# ============================================================
# PRIORITÉ 8 — mhashim6/Open-Hadith-Data ⚠️ STALE
# ============================================================
MHASHIM_SOURCE = {
    'id': 'mhashim6-open-hadith-data',
    'name': 'mhashim6/Open-Hadith-Data',
    'url': 'https://github.com/mhashim6/Open-Hadith-Data',
    'type': 'github',
    'description': '9 livres majeurs en CSV',
    'priority': 8,
    'reliability_score': 60,
    'license': 'unknown',
    'status': 'stale',
    'last_verified': '2026-04-17',
    'last_commit': '2022-07',
    'usage': 'Source secondaire de dernier recours uniquement',
    'notes': 'Inactive depuis plus de 3 ans. Champ Tafseel potentiellement utile.'
}

# ============================================================
# BONUS — Jammooly1/hadiths-json-files ✅
# ============================================================
JAMMOOLY_SOURCE = {
    'id': 'jammooly1-hadiths-json',
    'name': 'Jammooly1/hadiths-json-files',
    'url': 'https://github.com/Jammooly1/hadiths-json-files',
    'type': 'github',
    'description': 'JSON avec grades Al-Albânî explicites',
    'priority': 9,
    'reliability_score': 85,
    'license': 'unknown',
    'status': 'active',
    'last_verified': '2026-04-17',
    'advantage': 'Grades Al-Albânî pré-inclus, format bilingue',
    'grade_format': 'Hasan Sahih (Al-Albani) حسن صحيح (الألباني)',
    'notes': 'Directement mappable en grade_albani'
}

# ============================================================
# BONUS — halimbahae/Hadith ✅
# ============================================================
HALIMBAHAE_SOURCE = {
    'id': 'halimbahae-hadith',
    'name': 'halimbahae/Hadith',
    'url': 'https://github.com/halimbahae/Hadith',
    'type': 'github',
    'description': '9 livres avec tashkîl + Tafseel',
    'priority': 10,
    'reliability_score': 80,
    'license': 'unknown',
    'status': 'active',
    'last_verified': '2026-04-17',
    'advantage': 'Meilleure qualité typographique arabe, RTL markers',
    'notes': 'Toujours maintenu. Meilleure qualité que mhashim6.'
}

# ============================================================
# SOURCES RETIRÉES
# ============================================================
REMOVED_SOURCES = {
    'ragaeeb-shamela': {
        'reason': 'Nécessite API key privée non disponible publiquement',
        'status': 'removed_v7',
        'notes': 'Le README déclare explicitement ne pas pouvoir fournir de clés API'
    }
}

# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def get_all_sources() -> List[Dict[str, Any]]:
    """Obtenir toutes les sources actives V7.0"""
    return [
        FAWAZAHMED0_SOURCE,
        DORAR_API_SOURCE,
        HADEETHENC_SOURCE,
        ISLAMHOUSE_SOURCE,
        MEEATIF_SOURCE,
        AHMEDBASET_SOURCE,
        ABDELRAHMAAN_SOURCE,
        MHASHIM_SOURCE,
        JAMMOOLY_SOURCE,
        HALIMBAHAE_SOURCE
    ]

def get_sources_by_priority() -> List[Dict[str, Any]]:
    """Obtenir les sources triées par priorité"""
    return sorted(get_all_sources(), key=lambda x: x['priority'])

def get_source_by_id(source_id: str) -> Dict[str, Any]:
    """Obtenir une source par son ID"""
    for source in get_all_sources():
        if source['id'] == source_id:
            return source
    return None

def get_french_sources() -> List[Dict[str, Any]]:
    """Obtenir uniquement les sources avec traductions françaises"""
    return [
        FAWAZAHMED0_SOURCE,
        HADEETHENC_SOURCE,
        ISLAMHOUSE_SOURCE
    ]

def get_api_sources() -> List[Dict[str, Any]]:
    """Obtenir uniquement les sources API"""
    return [s for s in get_all_sources() if s['type'] == 'api']

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
        'active': len([s for s in all_sources if s['status'] == 'active']),
        'with_french': len(get_french_sources()),
        'api_sources': len(get_api_sources()),
        'avg_reliability': sum(s.get('reliability_score', 0) for s in all_sources) / len(all_sources),
        'last_verified': '2026-04-17'
    }

if __name__ == '__main__':
    print("=== REGISTRE DES SOURCES AL-MĪZĀN V7.0 ===\n")
    stats = get_source_stats()
    print(f"Total sources: {stats['total']}")
    print(f"  - Actives: {stats['active']}")
    print(f"  - Avec français: {stats['with_french']}")
    print(f"  - APIs: {stats['api_sources']}")
    print(f"  - Fiabilité moyenne: {stats['avg_reliability']:.1f}/100")
    print(f"  - Dernière vérification: {stats['last_verified']}")
    
    print("\n=== SOURCES PAR PRIORITÉ ===")
    for source in get_sources_by_priority()[:5]:
        status_icon = "✅" if source['status'] == 'active' else "⚠️"
        print(f"{status_icon} {source['priority']}. {source['name']} — {source['description']}")