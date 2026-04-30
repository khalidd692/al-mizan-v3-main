#!/usr/bin/env python3
"""
Script d'aspiration des ouvrages complets de Muṣṭalaḥ al-Ḥadīth pour Al-Mīzān
Sources cibles :
    1. Taysīr Muṣṭalaḥ al-Ḥadīth — Dr. Mahmoud Aṭ-Ṭaḥḥān (ISBN 979-1092883022)
    2. Sharḥ al-Bayqūniyya — Cheikh Ibn al-ʿUthaymīn (ISBN 978-2875450845)
    3. Nukhbat al-Fikar — Ibn Ḥajar al-ʿAsqalānī + Sharḥ (disponible en arabe)

Sources numériques :
    - Internet Archive (archive.org)
    - Al-Maktaba (al-maktaba.org)
    - Sifatusafwa (sifatusafwa.com — extraits)
    - Cours audio Bayqūniyya — Abū Yūsuf al-ʿĀjī (archive.org)

Usage :
    python ingest_books_complete.py --book all --output-dir ./corpus/raw_books/
"""

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass
class BookSource:
    """Configuration d'une source de livre"""
    id: str
    title_ar: str
    title_fr: str
    author: str
    validating_scholar: str
    priority: int  # 1 = max
    sources: list[dict]  # URLs et types
    local_path: Optional[Path] = None
    status: str = "pending"


class BookIngester:
    """Ingesteur d'ouvrages complets de Muṣṭalaḥ al-Ḥadīth"""

    # Configuration des ouvrages cibles
    TARGET_BOOKS = {
        "bayquniyya_uthaymin": BookSource(
            id="bayquniyya_uthaymin",
            title_ar="شرح المنظومة البيقونية في مصطلح الحديث",
            title_fr="Sharḥ al-Bayqūniyya — Commentaire du poème de ʿUmar al-Bayqūnī",
            author="ʿAllāma Muḥammad ibn Ṣāliḥ al-ʿUthaymīn",
            validating_scholar="Cheikh Ibn al-ʿUthaymīn (m. 1421 H)",
            priority=1,
            sources=[
                {
                    "type": "audio",
                    "platform": "archive.org",
                    "url": "https://archive.org/details/charh_al_bayquniyya",
                    "description": "9 cours audio en français par Abū Yūsuf ʿAbd Allāh Al-ʿĀjī (école de Dammāj)",
                    "reliability": "très_haute"
                },
                {
                    "type": "pdf_arabic",
                    "platform": "al-maktaba",
                    "search_terms": ["شرح البيقونية", "العثيمين", "مصطلح الحديث"],
                    "reliability": "haute"
                },
                {
                    "type": "print_reference",
                    "publisher": "Éditions Al-Ḥadīth",
                    "isbn": "978-2875450845",
                    "purchase_urls": [
                        "https://albayyinah.fr/hadith-sunnah/1533-le-commentaire-de-la-bayquniyya",
                        "https://www.librairie-sana.com/fr/le-hadith-livre/7239-le-commentaire-de-la-bayquniyya"
                    ],
                    "note": "Version imprimée française — référence maximale"
                }
            ]
        ),

        "taysir_tahhan": BookSource(
            id="taysir_tahhan",
            title_ar="تيسير مصطلح الحديث",
            title_fr="Taysīr Muṣṭalaḥ al-Ḥadīth — Précis des Sciences du Hadith",
            author="Dr. Mahmoud ibn Aḥmad Aṭ-Ṭaḥḥān",
            validating_scholar="Dr. Mahmoud Aṭ-Ṭaḥḥān (univ. Koweït/Médine)",
            priority=1,
            sources=[
                {
                    "type": "print_reference",
                    "publisher": "Éditions Al-Qalam",
                    "isbn": "979-1092883022",
                    "purchase_url": "https://albayyinah.fr/hadith-sunnah/1749-precis-des-sciences-du-hadith",
                    "note": "Manuel universitaire complet — référence très haute"
                },
                {
                    "type": "web_extracts",
                    "platform": "salafislam.fr",
                    "url": "https://salafislam.fr/introduction-sur-les-sciences-et-regles-du-hadith",
                    "description": "Extraits traduits du Taysīr (p. 100)",
                    "reliability": "très_haute"
                }
            ]
        ),

        "nukhbat_fikar": BookSource(
            id="nukhbat_fikar",
            title_ar="نخبة الفكر في مصطلح أهل الأثر",
            title_fr="Nukhbat al-Fikar — Le choix de la pensée sur la terminologie des gens du hadith",
            author="Imām Ibn Ḥajar al-ʿAsqalānī (m. 852 H)",
            validating_scholar="Ibn Ḥajar + Sharḥ al-Lāḥim",
            priority=2,
            sources=[
                {
                    "type": "pdf_arabic",
                    "platform": "al-maktaba.org",
                    "search_terms": ["نخبة الفكر", "ابن حجر", "مصطلح"],
                    "reliability": "haute"
                },
                {
                    "type": "sharh_pdf",
                    "title": "Sharḥ Nuzhat an-Naẓar",
                    "author": "Dr. Ibrāhīm al-Lāḥim (~900 pages)",
                    "platform": "sifatusafwa.com / al-maktaba",
                    "reliability": "très_haute"
                }
            ]
        ),

        "muqiza_dhahabi": BookSource(
            id="muqiza_dhahabi",
            title_ar="المقيزة في علم مصطلح الحديث",
            title_fr="Al-Mūqiẓa fī ʿIlm Muṣṭalaḥ al-Ḥadīth — L'éveil sur la science de la terminologie",
            author="Imām Adh-Dhahabī (m. 748 H)",
            validating_scholar="Adh-Dhahabī + Sharḥ al-Lāḥim + al-Rāziḥī",
            priority=3,
            sources=[
                {
                    "type": "pdf_arabic",
                    "platform": "al-maktaba.org",
                    "search_terms": ["المقيزة", "الذهبي", "مصطلح الحديث"],
                    "reliability": "haute"
                }
            ]
        )
    }

    def __init__(self, output_dir: str = "./corpus/raw_books/"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Session HTTP avec retry
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0"
        })

    def download_archive_org(self, identifier: str, output_subdir: str) -> dict:
        """
        Télécharge depuis Internet Archive
        
        Args:
            identifier: ID archive.org (ex: 'charh_al_bayquniyya')
            output_subdir: Sous-dossier de sortie
        """
        output_path = self.output_dir / output_subdir
        output_path.mkdir(parents=True, exist_ok=True)
        
        # API Archive.org
        metadata_url = f"https://archive.org/metadata/{identifier}"
        
        try:
            print(f"📡 Récupération métadonnées: {identifier}")
            resp = self.session.get(metadata_url, timeout=30)
            resp.raise_for_status()
            metadata = resp.json()
            
            files_info = []
            
            # Extraction des fichiers audio/PDF disponibles
            for file in metadata.get("files", []):
                name = file.get("name", "")
                
                # Priorité aux MP3 et PDF
                if name.endswith((".mp3", ".pdf", ".txt")):
                    download_url = f"https://archive.org/download/{identifier}/{name}"
                    local_file = output_path / name
                    
                    if local_file.exists():
                        print(f"   ⏭️  {name} déjà présent")
                        files_info.append({
                            "name": name,
                            "local_path": str(local_file),
                            "size": file.get("size"),
                            "status": "existing"
                        })
                        continue
                    
                    print(f"   ⬇️  Téléchargement: {name}")
                    try:
                        file_resp = self.session.get(download_url, stream=True, timeout=60)
                        file_resp.raise_for_status()
                        
                        with open(local_file, "wb") as f:
                            for chunk in file_resp.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        files_info.append({
                            "name": name,
                            "local_path": str(local_file),
                            "size": file.get("size"),
                            "status": "downloaded"
                        })
                        print(f"   ✅ {name} téléchargé")
                        
                    except Exception as e:
                        print(f"   ❌ Erreur {name}: {e}")
                        files_info.append({
                            "name": name,
                            "error": str(e),
                            "status": "error"
                        })
                    
                    time.sleep(0.5)  # Rate limiting
            
            return {
                "identifier": identifier,
                "title": metadata.get("metadata", {}).get("title", "Unknown"),
                "files": files_info,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "identifier": identifier,
                "error": str(e),
                "status": "error"
            }

    def search_al_maktaba(self, title_ar: str, author: str) -> dict:
        """
        Recherche sur al-maktaba.org (bibliothèque numérique arabe)
        
        Note: Cette méthode fait une recherche web et retourne les URLs candidates
        L'extraction directe nécessite une API ou du scraping avancé
        """
        search_query = f"{title_ar} {author} site:al-maktaba.org filetype:pdf"
        
        # Documentation de la source pour extraction manuelle
        return {
            "platform": "al-maktaba.org",
            "search_query": search_query,
            "note": "Recherche manuelle requise — al-maktaba.org n'a pas d'API publique",
            "direct_search_url": f"https://www.al-maktaba.org/?s={title_ar.replace(' ', '+')}",
            "status": "manual_required"
        }

    def generate_catalog(self) -> dict:
        """Génère le catalogue de tous les ouvrages cibles"""
        catalog = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "project": "Al-Mīzān — Ingestion ouvrages Muṣṭalaḥ",
            "books": []
        }
        
        for book_id, book in self.TARGET_BOOKS.items():
            book_data = {
                "id": book.id,
                "priority": book.priority,
                "title_ar": book.title_ar,
                "title_fr": book.title_fr,
                "author": book.author,
                "validating_scholar": book.validating_scholar,
                "sources": book.sources,
                "status": book.status
            }
            catalog["books"].append(book_data)
        
        return catalog

    def run_ingestion(self, book_ids: list[str] = None) -> dict:
        """
        Lance l'ingestion complète
        
        Args:
            book_ids: Liste des IDs à ingérer (None = tous)
        """
        results = {
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "downloads": {},
            "catalog": self.generate_catalog()
        }
        
        targets = book_ids or list(self.TARGET_BOOKS.keys())
        
        for book_id in targets:
            if book_id not in self.TARGET_BOOKS:
                print(f"⚠️  Livre inconnu: {book_id}")
                continue
            
            book = self.TARGET_BOOKS[book_id]
            print(f"\n{'='*60}")
            print(f"📚 {book.title_fr}")
            print(f"   Auteur: {book.author}")
            print(f"   Priorité: {book.priority}")
            print(f"{'='*60}")
            
            book_results = []
            
            for source in book.sources:
                source_type = source.get("type")
                
                if source_type == "audio" and source.get("platform") == "archive.org":
                    identifier = source["url"].split("/")[-1]
                    result = self.download_archive_org(identifier, book_id)
                    book_results.append({
                        "source": source,
                        "result": result
                    })
                    
                elif source_type == "pdf_arabic":
                    result = self.search_al_maktaba(book.title_ar, book.author)
                    book_results.append({
                        "source": source,
                        "result": result
                    })
                    
                elif source_type == "web_extracts":
                    # Documente l'URL pour extraction manuelle
                    book_results.append({
                        "source": source,
                        "result": {
                            "type": "web_reference",
                            "url": source.get("url"),
                            "note": "Extraits disponibles — extraction manuelle recommandée",
                            "status": "reference_only"
                        }
                    })
                    
                elif source_type == "print_reference":
                    # Référence d'achat
                    book_results.append({
                        "source": source,
                        "result": {
                            "type": "print_reference",
                            "isbn": source.get("isbn"),
                            "publisher": source.get("publisher"),
                            "purchase_urls": source.get("purchase_urls", [source.get("purchase_url")]),
                            "status": "purchase_required"
                        }
                    })
            
            results["downloads"][book_id] = book_results
            
            # Sauvegarde incrémentale
            report_path = self.output_dir / "ingestion_report.json"
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Rapport sauvegardé: {report_path}")
        
        results["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        return results


def main():
    parser = argparse.ArgumentParser(
        description="Ingestion des ouvrages complets de Muṣṭalaḥ al-Ḥadīth"
    )
    parser.add_argument(
        "--book",
        choices=["all", "bayquniyya", "taysir", "nukhbat", "muqiza"],
        default="all",
        help="Ouvrage à ingérer (default: all)"
    )
    parser.add_argument(
        "--output-dir",
        default="./corpus/raw_books/",
        help="Répertoire de sortie (default: ./corpus/raw_books/)"
    )
    parser.add_argument(
        "--catalog-only",
        action="store_true",
        help="Génère uniquement le catalogue sans téléchargement"
    )
    
    args = parser.parse_args()
    
    # Mapping des noms courts vers IDs
    book_map = {
        "bayquniyya": "bayquniyya_uthaymin",
        "taysir": "taysir_tahhan",
        "nukhbat": "nukhbat_fikar",
        "muqiza": "muqiza_dhahabi"
    }
    
    ingester = BookIngester(output_dir=args.output_dir)
    
    if args.catalog_only:
        catalog = ingester.generate_catalog()
        catalog_path = Path(args.output_dir) / "book_catalog.json"
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        with open(catalog_path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)
        print(f"📋 Catalogue généré: {catalog_path}")
        return
    
    # Détermine les cibles
    if args.book == "all":
        targets = None  # Tous
    else:
        targets = [book_map[args.book]]
    
    # Lance l'ingestion
    print("🚀 Démarrage ingestion ouvrages Al-Mīzān")
    print(f"   Output: {args.output_dir}")
    print(f"   Cibles: {targets or 'Tous'}")
    print()
    
    results = ingester.run_ingestion(targets)
    
    # Rapport final
    print(f"\n{'='*60}")
    print("📊 RAPPORT FINAL")
    print(f"{'='*60}")
    print(f"Démarré:  {results['started_at']}")
    print(f"Terminé:  {results['completed_at']}")
    print(f"Ouvrages traités: {len(results['downloads'])}")
    print()
    
    for book_id, book_results in results['downloads'].items():
        print(f"📚 {book_id}")
        for entry in book_results:
            result = entry.get('result', {})
            status = result.get('status', 'unknown')
            icon = "✅" if status == "success" else "⚠️" if status in ["manual_required", "reference_only", "purchase_required"] else "❌"
            print(f"   {icon} {entry['source'].get('type', 'unknown')}: {status}")
    
    print(f"\n💾 Rapport complet: {Path(args.output_dir) / 'ingestion_report.json'}")


if __name__ == "__main__":
    main()
