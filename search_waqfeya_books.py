#!/usr/bin/env python3
"""
Recherche et téléchargement de PDF arabes sur waqfeya.net et archive.org
Ouvrages cibles:
    - Taysīr Muṣṭalaḥ al-Ḥadīth (Ṭaḥḥān)
    - Nukhbat al-Fikar (Ibn Ḥajar)
    - Sharḥ Nuzhat an-Naẓar (al-Lāḥim)
    - Al-Mūqiẓa (adh-Dhahabī)

Usage:
    python search_waqfeya_books.py --book tahhan --download
    python search_waqfeya_books.py --book all --catalog-only
    python search_waqfeya_books.py --search "نخبة الفكر" --source waqfeya
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin, quote, urlparse


class WaqfeyaSearcher:
    """Chercheur de livres sur waqfeya.net et archive.org"""
    
    SOURCES = {
        "waqfeya": {
            "name": "Waqfeya Digital Library",
            "base_url": "https://waqfeya.net",
            "search_url": "https://waqfeya.net/search.php",
            "book_url": "https://waqfeya.net/book.php",
            "icon": "📚"
        },
        "archive": {
            "name": "Internet Archive",
            "base_url": "https://archive.org",
            "search_url": "https://archive.org/advancedsearch.php",
            "icon": "🌐"
        },
        "almaktaba": {
            "name": "Al-Maktaba al-Shamela",
            "base_url": "https://al-maktaba.org",
            "search_url": "https://al-maktaba.org/search",
            "icon": "📖"
        },
        "sifatusafwa": {
            "name": "Sifatusafwa (références)",
            "base_url": "https://sifatusafwa.com",
            "icon": "🏪"
        }
    }
    
    # Configuration des ouvrages recherchés
    TARGET_BOOKS = {
        "tahhan": {
            "title_ar": "تيسير مصطلح الحديث",
            "title_fr": "Taysīr Muṣṭalaḥ al-Ḥadīth",
            "author": "Dr. Mahmoud Aṭ-Ṭaḥḥān",
            "author_ar": "محمود الطحان",
            "priority": 1,
            "search_terms": [
                "تيسير مصطلح الحديث",
                "الطحان مصطلح",
                "taysir mustalah al-hadith"
            ],
            "expected_pdf": "taysir_mustalah_tahhan.pdf"
        },
        
        "nukhbat_fikar": {
            "title_ar": "نخبة الفكر في مصطلح أهل الأثر",
            "title_fr": "Nukhbat al-Fikar",
            "author": "Imām Ibn Ḥajar al-ʿAsqalānī",
            "author_ar": "ابن حجر العسقلاني",
            "priority": 1,
            "search_terms": [
                "نخبة الفكر",
                "ابن حجر مصطلح",
                "nukhbat al-fikar ibn hajar"
            ],
            "expected_pdf": "nukhbat_al_fikar.pdf"
        },
        
        "sharh_nuzhat": {
            "title_ar": "شرح نزهة النظر",
            "title_fr": "Sharḥ Nuzhat an-Naẓar",
            "author": "Dr. Ibrāhīm al-Lāḥim",
            "author_ar": "إبراهيم اللاحم",
            "priority": 2,
            "search_terms": [
                "شرح نزهة النظر",
                "اللاحم نخبة الفكر",
                "sharh nuzhat al-nazar"
            ],
            "expected_pdf": "sharh_nuzhat_lahim.pdf",
            "notes": "Commentaire de Nukhbat al-Fikar (~900 pages)"
        },
        
        "muqiza_dhahabi": {
            "title_ar": "المقيزة في علم مصطلح الحديث",
            "title_fr": "Al-Mūqiẓa fī ʿIlm Muṣṭalaḥ al-Ḥadīth",
            "author": "Imām adh-Dhahabī",
            "author_ar": "الذهبي",
            "priority": 3,
            "search_terms": [
                "المقيزة مصطلح الحديث",
                "الذهبي المقيزة",
                "al-muqiza dhahabi"
            ],
            "expected_pdf": "al_muqiza_dhahabi.pdf"
        },
        
        "bayquniyya_poem": {
            "title_ar": "منظومة البيقونية",
            "title_fr": "Al-Manẓūma al-Bayqūniyya",
            "author": "ʿUmar al-Bayqūnī",
            "author_ar": "عمر البيقوني",
            "priority": 2,
            "search_terms": [
                "منظومة البيقونية",
                "البيقوني مصطلح",
                "manzuma bayquniyyah"
            ],
            "expected_pdf": "manzuma_bayquniyya.pdf",
            "notes": "Poème de 34 vers — base du Sharḥ d'Ibn al-ʿUthaymīn"
        }
    }
    
    def __init__(self, output_dir: str = "./corpus/arabic_books/"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = {
            "searches": [],
            "found": [],
            "not_found": [],
            "downloads": []
        }
    
    def generate_search_urls(self, book_key: str) -> List[Dict]:
        """Génère les URLs de recherche pour un livre sur toutes les sources"""
        book = self.TARGET_BOOKS.get(book_key)
        if not book:
            return []
        
        urls = []
        
        # Waqfeya
        for term in book["search_terms"]:
            urls.append({
                "source": "waqfeya",
                "url": f"{self.SOURCES['waqfeya']['search_url']}?q={quote(term)}",
                "term": term,
                "book_key": book_key
            })
        
        # Archive.org
        archive_query = f"{book['title_ar']} OR {book['author_ar']}"
        urls.append({
            "source": "archive",
            "url": f"{self.SOURCES['archive']['search_url']}?q={quote(archive_query)}&mediatype=texts",
            "term": archive_query,
            "book_key": book_key
        })
        
        # Al-Maktaba
        urls.append({
            "source": "almaktaba",
            "url": f"{self.SOURCES['almaktaba']['search_url']}?q={quote(book['title_ar'])}",
            "term": book["title_ar"],
            "book_key": book_key
        })
        
        return urls
    
    def search_all(self, book_key: Optional[str] = None) -> Dict:
        """
        Lance les recherches pour tous les livres ou un seul
        
        Note: En pratique, cette méthode nécessite MCP Playwright pour
        naviguer et extraire les résultats. Ici on génère le catalogue.
        """
        targets = [book_key] if book_key else list(self.TARGET_BOOKS.keys())
        
        print("="*70)
        print("🔍 RECHERCHE PDF ARABES — Waqfeya/Archive/Al-Maktaba")
        print("="*70)
        
        for key in targets:
            book = self.TARGET_BOOKS[key]
            print(f"\n📚 {book['title_fr']}")
            print(f"   Auteur: {book['author']}")
            print(f"   Arabe: {book['title_ar']}")
            print(f"   Priorité: {book['priority']}")
            
            urls = self.generate_search_urls(key)
            
            print(f"\n   URLs de recherche générées:")
            for u in urls:
                icon = self.SOURCES[u['source']]['icon']
                print(f"   {icon} {u['source']}: {u['url'][:70]}...")
            
            self.results["searches"].append({
                "book_key": key,
                "book": book,
                "urls": urls
            })
            
            # Note: L'extraction réelle nécessite Playwright MCP
            print(f"   ⚠️  Extraction manuelle requise (Playwright MCP)")
            print(f"   → Instructions dans le rapport généré")
        
        return self.results
    
    def generate_manual_instructions(self) -> str:
        """Génère les instructions pour extraction manuelle"""
        instructions = """
# Instructions d'extraction manuelle des PDF arabes

## waqfeya.net (priorité 1)

1. Visiter: https://waqfeya.net
2. Rechercher le titre arabe (ex: "تيسير مصطلح الحديث")
3. Identifier le livre dans les résultats
4. Cliquer sur le titre pour accéder à la page du livre
5. Chercher le lien de téléchargement PDF (généralement sous le titre)
6. Le format est souvent: `https://waqfeya.net/file.php?bid=XXXX`

## archive.org (priorité 2)

1. Visiter: https://archive.org
2. Rechercher: "نخبة الفكر ابن حجر"
3. Filtrer par "Texts" et langue "Arabic"
4. Identifier l'identifiant (ex: "nukhbat_al_fikar_2015")
5. Télécharger le PDF ou le fichier ZIP

## al-maktaba.org (priorité 3)

1. Nécessite une inscription gratuite
2. Rechercher le titre arabe
3. Télécharger via le bouton "تحميل"

## Vérification post-téléchargement

Pour chaque PDF téléchargé:
1. Vérifier que c'est bien l'ouvrage complet (pas un extrait)
2. Vérifier la pagination (ex: Taysīr ~300-400 pages)
3. Renommer selon le format: `{book_key}.pdf`
4. Placer dans: `./corpus/arabic_books/`
5. Mettre à jour: `arabic_books_catalog.json`

## Structure attendue après téléchargement

```
corpus/arabic_books/
├── tahhan.pdf              # Taysīr Muṣṭalaḥ al-Ḥadīth
├── nukhbat_fikar.pdf       # Nukhbat al-Fikar
├── sharh_nuzhat.pdf        # Sharḥ Nuzhat an-Naẓar
├── muqiza_dhahabi.pdf      # Al-Mūqiẓa
├── bayquniyya_poem.pdf     # Manẓūma al-Bayqūniyya
└── arabic_books_catalog.json
```
"""
        return instructions
    
    def save_catalog(self):
        """Sauvegarde le catalogue de recherche"""
        # Catalogue JSON
        catalog = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "books": []
        }
        
        for key, book in self.TARGET_BOOKS.items():
            catalog["books"].append({
                "key": key,
                **book,
                "search_urls": self.generate_search_urls(key),
                "status": "pending_search"
            })
        
        catalog_file = self.output_dir / "arabic_books_catalog.json"
        with open(catalog_file, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)
        
        # Instructions Markdown
        instructions = self.generate_manual_instructions()
        instructions_file = self.output_dir / "DOWNLOAD_INSTRUCTIONS.md"
        with open(instructions_file, "w", encoding="utf-8") as f:
            f.write(instructions)
        
        # Rapport de recherche
        report_file = self.output_dir / "search_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*70}")
        print("📊 RAPPORT DE RECHERCHE")
        print(f"{'='*70}")
        print(f"Catalogue: {catalog_file}")
        print(f"Instructions: {instructions_file}")
        print(f"Rapport: {report_file}")
        print(f"\n{len(catalog['books'])} livres catalogués")
        print(f"{len(self.results['searches'])} recherches générées")
        
        return catalog_file, instructions_file, report_file


def main():
    parser = argparse.ArgumentParser(
        description="Recherche de PDF arabes sur waqfeya.net et archive.org"
    )
    parser.add_argument(
        "--book",
        choices=["tahhan", "nukhbat_fikar", "sharh_nuzhat", "muqiza_dhahabi", "bayquniyya_poem", "all"],
        default="all",
        help="Livre spécifique à rechercher"
    )
    parser.add_argument(
        "--source",
        choices=["waqfeya", "archive", "almaktaba", "all"],
        default="all",
        help="Source de recherche"
    )
    parser.add_argument(
        "--catalog-only",
        action="store_true",
        help="Génère uniquement le catalogue sans recherche"
    )
    parser.add_argument(
        "--output-dir",
        default="./corpus/arabic_books/",
        help="Répertoire de sortie"
    )
    
    args = parser.parse_args()
    
    searcher = WaqfeyaSearcher(output_dir=args.output_dir)
    
    # Détermine les cibles
    targets = None if args.book == "all" else args.book
    
    # Lance la recherche
    searcher.search_all(book_key=targets)
    
    # Sauvegarde
    catalog, instructions, report = searcher.save_catalog()
    
    print(f"\n{'='*70}")
    print("✅ CATALOGUE GÉNÉRÉ")
    print(f"{'='*70}")
    print(f"\nProchaines étapes:")
    print(f"1. Lire: {instructions}")
    print(f"2. Visiter les URLs dans: {catalog}")
    print(f"3. Télécharger les PDF manuellement")
    print(f"4. Renommer et placer dans: {args.output_dir}")


if __name__ == "__main__":
    main()
