#!/usr/bin/env python3
"""
Script de scraping Dorar.net pour extraction des verdicts techniques
Traduit les grades Dorar vers le lexique Al-Mīzān issu des cours de Dammāj

Usage:
    python scrape_dorar_verdicts.py --hadith-id 1 --output-zones
    python scrape_dorar_verdicts.py --book bukhari --start 1 --count 100
    python scrape_dorar_verdicts.py --search-query "حديث النية" --max 50

Mapping grades Dorar → Al-Mīzān:
    - صحيح → Ṣaḥīḥ li-dhātihi / Ṣaḥīḥ li-ghayrihi
    - حسن → Ḥasan li-dhātihi / Ḥasan li-ghayrihi
    - ضعيف → Ḍaʿīf (avec classification du ʿillah)
    - ضعيف جداً → Ḍaʿīf jiddan / Matrūk
    - موضوع → Mawḍūʿ
    - منكر → Munkar
    - شاذ → Shādhdh
"""

import argparse
import asyncio
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin, quote


@dataclass
class DorarGrade:
    """Structure d'un grade Dorar avec traduction Al-Mīzān"""
    grade_ar: str           # Grade tel qu'affiché sur Dorar
    grade_darija: str       # Grade en arabe dialecte (commentaire)
    muhaddith: str          # Savant ayant donné le grade
    muhaddith_id: int       # ID Dorar du savant
    
    # Traduction vers terminologie Al-Mīzān
    almizan_category: str   # Catégorie (degré/rupture/défaut)
    almizan_term: str       # Terme technique exact
    almizan_term_ar: str    # Terme arabe
    
    # Explication du jugement
    explanation: str        # Texte explicatif du grade
    takhrij_details: str    # Détails du takhrij (sources)


@dataclass
class DorarHadith:
    """Hadith complet extrait de Dorar"""
    dorar_id: int
    matn_ar: str
    matn_clean: str
    isnad_ar: Optional[str]
    
    # Grades et jugements
    grades: List[DorarGrade]
    primary_grade: str      # Grade principal (consensus ou plus fiable)
    
    # Métadonnées
    book_name: str
    book_name_ar: str
    hadith_number: str
    chapter: Optional[str]
    bab: Optional[str]
    
    # Rapprochements
    similar_hadiths: List[Dict]
    sharh_available: bool
    
    # Source
    source_url: str
    scraped_at: str


class DorarScraper:
    """Scraper pour Dorar.net utilisant Playwright MCP"""
    
    BASE_URL = "https://dorar.net"
    
    # Mapping des grades Dorar vers terminologie Al-Mīzān
    GRADE_MAPPING = {
        "صحيح": {
            "category": "degré",
            "term": "Ṣaḥīḥ li-dhātihi",
            "term_ar": "صحيح لذاته",
            "priority": 1
        },
        "صحيح لغيره": {
            "category": "degré",
            "term": "Ṣaḥīḥ li-ghayrihi",
            "term_ar": "صحيح لغيره",
            "priority": 2
        },
        "حسن": {
            "category": "degré",
            "term": "Ḥasan li-dhātihi",
            "term_ar": "حسن لذاته",
            "priority": 3
        },
        "حسن لغيره": {
            "category": "degré",
            "term": "Ḥasan li-ghayrihi",
            "term_ar": "حسن لغيره",
            "priority": 4
        },
        "ضعيف": {
            "category": "degré",
            "term": "Ḍaʿīf",
            "term_ar": "ضعيف",
            "priority": 5,
            "requires_illah": True  # Nécessite identification de l'ʿillah
        },
        "ضعيف جداً": {
            "category": "degré",
            "term": "Ḍaʿīf jiddan",
            "term_ar": "ضعيف جداً",
            "priority": 6
        },
        "موضوع": {
            "category": "défaut",
            "term": "Mawḍūʿ",
            "term_ar": "موضوع",
            "priority": 7,
            "alert": True
        },
        "منكر": {
            "category": "défaut",
            "term": "Munkar",
            "term_ar": "منكر",
            "priority": 8
        },
        "شاذ": {
            "category": "défaut",
            "term": "Shādhdh",
            "term_ar": "شاذ",
            "priority": 9
        },
        "متروك": {
            "category": "défaut",
            "term": "Matrūk",
            "term_ar": "متروك",
            "priority": 10
        },
        "معلق": {
            "category": "rupture",
            "term": "Muʿallaq",
            "term_ar": "معلق",
            "priority": 11
        },
        "منقطع": {
            "category": "rupture",
            "term": "Munqaṭiʿ",
            "term_ar": "منقطع",
            "priority": 12
        },
        "مرسل": {
            "category": "rupture",
            "term": "Mursal",
            "term_ar": "مرسل",
            "priority": 13
        }
    }
    
    # IDs des savants importants dans Dorar
    SCHOLARS_ID = {
        "albani": 1,
        "ibn_baz": 2,
        "ibn_uthaymin": 3,
        "fawzan": 4,
        "muqbil": 5
    }
    
    def __init__(self, output_dir: str = "./corpus/dorar_scraped/"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.session_stats = {
            "requests": 0,
            "success": 0,
            "errors": 0,
            "grades_extracted": 0
        }
    
    async def scrape_hadith_page(self, hadith_id: int) -> Optional[DorarHadith]:
        """
        Scrape une page de hadith Dorar
        
        Cette méthode utilise Playwright MCP pour extraire le contenu rendu
        """
        url = f"{self.BASE_URL}/hadith/{hadith_id}"
        
        print(f"🔍 Scraping hadith #{hadith_id}...")
        print(f"   URL: {url}")
        
        try:
            # Note: En pratique, cette méthode serait appelée via MCP
            # Ici on documente la structure pour intégration
            
            self.session_stats["requests"] += 1
            
            # Simulation de la structure de données attendue
            # Dans l'implémentation réelle avec MCP:
            # 1. browser_navigate(url)
            # 2. browser_snapshot pour obtenir le HTML
            # 3. Parsing avec BeautifulSoup ou regex
            
            # Structure type d'une page Dorar:
            # - .hadith-card : conteneur principal
            # - .matn : texte du hadith
            # - .isnad : chaîne de transmission
            # - .grades-list : liste des grades
            # - .grade-item : grade individuel avec savant
            
            return None  # À implémenter avec MCP réel
            
        except Exception as e:
            self.session_stats["errors"] += 1
            print(f"   ❌ Erreur: {e}")
            return None
    
    def parse_grade_text(self, grade_text: str, muhaddith: str) -> DorarGrade:
        """
        Parse le texte d'un grade Dorar et mappe vers Al-Mīzān
        
        Args:
            grade_text: Texte du grade (ex: "ضعيف — الألباني")
            muhaddith: Nom du savant
            
        Returns:
            DorarGrade structuré avec mapping Al-Mīzān
        """
        # Extraction du grade de base
        grade_clean = grade_text.split("—")[0].strip() if "—" in grade_text else grade_text.strip()
        
        # Recherche dans le mapping
        mapping = self.GRADE_MAPPING.get(grade_clean, {
            "category": "unknown",
            "term": "unknown",
            "term_ar": grade_clean,
            "priority": 99
        })
        
        # Construction de l'objet
        return DorarGrade(
            grade_ar=grade_clean,
            grade_darija=grade_text,
            muhaddith=muhaddith,
            muhaddith_id=self._get_scholar_id(muhaddith),
            almizan_category=mapping["category"],
            almizan_term=mapping["term"],
            almizan_term_ar=mapping["term_ar"],
            explanation="",
            takhrij_details=""
        )
    
    def _get_scholar_id(self, name: str) -> int:
        """Retourne l'ID Dorar d'un savant par son nom"""
        name_lower = name.lower()
        for scholar, sid in self.SCHOLARS_ID.items():
            if scholar in name_lower or name_lower in scholar:
                return sid
        return 0
    
    def save_to_zones(self, hadith: DorarHadith):
        """
        Sauvegarde un hadith scrapé dans les zones Al-Mīzān correspondantes
        
        Mapping zones:
        - Grade Ṣaḥīḥ/Ḥasan → Zone 04 (SHUDHŪDH)
        - Grade Ḍaʿīf → Zone 08 (TAKHRĪJ ʿILAL)
        - Grade Mawḍūʿ → Zone 23 (MAWḌŪʿ ALERTE)
        - Grade Munkar/Shādhdh → Zone 04 ou 08
        """
        zones_data = {}
        
        for grade in hadith.grades:
            zone_id = self._grade_to_zone(grade)
            
            if zone_id not in zones_data:
                zones_data[zone_id] = []
            
            zones_data[zone_id].append({
                "dorar_id": hadith.dorar_id,
                "matn_preview": hadith.matn_clean[:200] + "...",
                "grade_dorar": grade.grade_ar,
                "grade_almizan": grade.almizan_term,
                "muhaddith": grade.muhaddith,
                "explanation": grade.explanation,
                "source_url": hadith.source_url,
                "scraped_at": hadith.scraped_at
            })
        
        # Sauvegarde par zone
        for zone_id, entries in zones_data.items():
            zone_file = self.output_dir / f"zone_{zone_id:02d}_dorar_entries.json"
            
            # Charge existant ou crée nouveau
            existing = []
            if zone_file.exists():
                with open(zone_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            
            # Merge et sauvegarde
            existing.extend(entries)
            with open(zone_file, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)
            
            print(f"   💾 Zone {zone_id:02d}: +{len(entries)} entrées (total: {len(existing)})")
    
    def _grade_to_zone(self, grade: DorarGrade) -> int:
        """Mappe un grade vers un ID de zone Al-Mīzān"""
        zone_mapping = {
            "degré": 4,      # Zone 04: SHUDHŪDH
            "rupture": 8,    # Zone 08: TAKHRĪJ ʿILAL
            "défaut": 7 if grade.almizan_term == "Mawḍūʿ" else 4,
            "unknown": 38    # Zone 38: TAKHRĪJ WA TAQĪQ
        }
        return zone_mapping.get(grade.almizan_category, 38)
    
    def generate_verdict_template(self, hadith: DorarHadith) -> Dict:
        """
        Génère un template de verdict structuré pour Al-Mīzān
        
        Ce template peut être utilisé par les agents pour remplir les zones
        """
        primary = hadith.grades[0] if hadith.grades else None
        
        return {
            "verdict_id": f"dorar_{hadith.dorar_id}",
            "hadith_ref": {
                "dorar_id": hadith.dorar_id,
                "book": hadith.book_name,
                "number": hadith.hadith_number
            },
            "matn_ar": hadith.matn_ar,
            "grades": [
                {
                    "source": g.muhaddith,
                    "grade_dorar": g.grade_ar,
                    "grade_almizan": g.almizan_term,
                    "category": g.almizan_category,
                    "confidence": "high" if g.muhaddith_id in [1, 2, 3] else "medium"
                }
                for g in hadith.grades
            ],
            "consensus": self._determine_consensus(hadith.grades),
            "recommended_zone": self._grade_to_zone(primary) if primary else 38,
            "evidence_text": f"Verdict de {primary.muhaddith if primary else 'inconnu'} "
                           f"({primary.grade_ar if primary else 'N/A'}) → "
                           f"{primary.almizan_term if primary else 'N/A'}",
            "source": {
                "api": "dorar",
                "url": hadith.source_url,
                "scraped_at": hadith.scraped_at
            }
        }
    
    def _determine_consensus(self, grades: List[DorarGrade]) -> str:
        """Détermine s'il y a consensus ou divergence entre les savants"""
        if not grades:
            return "unknown"
        
        categories = set(g.almizan_category for g in grades)
        
        if len(categories) == 1:
            return "consensus"
        elif len(categories) == 2 and "degré" in categories and "défaut" in categories:
            return "khilaf_fiqhi"  # Différence de jugement acceptée
        else:
            return "divergence_significative"


async def main():
    parser = argparse.ArgumentParser(
        description="Scraping Dorar.net pour verdicts techniques → Al-Mīzān"
    )
    parser.add_argument(
        "--hadith-id",
        type=int,
        help="ID spécifique d'un hadith Dorar"
    )
    parser.add_argument(
        "--book",
        choices=["bukhari", "muslim", "abudawud", "tirmidhi", "nasai", "ibnmajah"],
        help="Livre à scraper"
    )
    parser.add_argument(
        "--start",
        type=int,
        default=1,
        help="Numéro de hadith de départ"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Nombre de hadiths à scraper"
    )
    parser.add_argument(
        "--search-query",
        help="Recherche par texte arabe"
    )
    parser.add_argument(
        "--output-zones",
        action="store_true",
        help="Sauvegarde directe dans les zones Al-Mīzān"
    )
    parser.add_argument(
        "--output-dir",
        default="./corpus/dorar_scraped/",
        help="Répertoire de sortie"
    )
    
    args = parser.parse_args()
    
    scraper = DorarScraper(output_dir=args.output_dir)
    
    print("="*70)
    print("🌐 DORAR.NET SCRAPER → Al-Mīzān")
    print("="*70)
    print(f"   Output: {args.output_dir}")
    print(f"   Mapping grades: {len(scraper.GRADE_MAPPING)} grades connus")
    print()
    
    # TODO: Implémentation avec MCP Playwright
    print("⚠️  Ce script nécessite l'intégration MCP Playwright pour fonctionner")
    print("   Étapes d'utilisation:")
    print("   1. Utiliser mcp5_browser_navigate pour charger la page")
    print("   2. Utiliser mcp5_browser_snapshot pour extraire le contenu")
    print("   3. Parser avec BeautifulSoup")
    print("   4. Mapper vers Al-Mīzān avec GRADE_MAPPING")
    print()
    
    print("📋 Structure de données prête:")
    print(f"   - DorarHadith: hadith complet avec métadonnées")
    print(f"   - DorarGrade: grade avec mapping Al-Mīzān")
    print(f"   - save_to_zones(): sauvegarde dans zones 04, 08, 23, 38")
    print(f"   - generate_verdict_template(): template de verdict structuré")


if __name__ == "__main__":
    asyncio.run(main())
