#!/usr/bin/env python3
"""
Script de recherche multi-sources de livres de science du hadith en français
Sources: islamhouse.com/fr, archive.org, github.com, et autres
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
import random
from urllib.parse import urljoin, quote, urlparse
from datetime import datetime

# Configuration
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7,ar;q=0.6",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# Sources à rechercher
SOURCES = {
    "islamhouse": {
        "name": "IslamHouse.com/fr",
        "base_url": "https://islamhouse.com",
        "reliability": "Haute - Source officielle",
        "price": "Gratuit"
    },
    "archive_org": {
        "name": "Archive.org",
        "base_url": "https://archive.org",
        "reliability": "Moyenne - Depot d'archives",
        "price": "Gratuit"
    },
    "github": {
        "name": "GitHub.com",
        "base_url": "https://github.com",
        "reliability": "Variable - Depend du depot",
        "price": "Gratuit"
    }
}

# Livres à rechercher avec métadonnées
TARGET_BOOKS = [
    {
        "title_fr": "Nukhbat Al-Fikar",
        "title_ar": "نخبة الفكر",
        "author": "Ibn Hajar Al-Asqalani",
        "keywords": ["nukhbat", "نخبة الفكر", "ibn hajar", "ابن حجر", "fikar", "الفكر"]
    },
    {
        "title_fr": "Taysir Mustalah Al-Hadith",
        "title_ar": "تيسير مصطلح الحديث",
        "author": "Mahmoud At-Tahhan",
        "keywords": ["taysir", "تيسير", "tahhan", "الطحان", "mustalah", "مصطلح"]
    },
    {
        "title_fr": "Al-Muqiza",
        "title_ar": "المقيزة",
        "author": "Adh-Dhahabi",
        "keywords": ["muqiza", "مقيزة", "dhahabi", "الذهبي"]
    },
    {
        "title_fr": "Ikhtisar Ulum Al-Hadith",
        "title_ar": "اختصار علوم الحديث",
        "author": "Ibn Kathir",
        "keywords": ["ikhtisar", "اختصار", "ulum", "علوم", "ibn kathir", "ابن كثير"]
    },
    {
        "title_fr": "Al-Baïqouniyya",
        "title_ar": "البيقونية",
        "author": "At-Taa'i",
        "keywords": ["baïqouniyya", "beyqouniyyah", "البيقونية", "baiquniyyah"]
    }
]

HADITH_KEYWORDS = [
    "hadith", "حديث", "mustalah", "مصطلح", "nukhbat", "نخبة", "fikar", "الفكر",
    "taysir", "تيسير", "muqiza", "مقيزة", "ikhtisar", "اختصار", "ulum", "علوم",
    "tahhan", "الطحان", "dhahabi", "الذهبي", "ibn hajar", "ابن حجر", 
    "ibn kathir", "ابن كثير", "baïqouniyya", "البيقونية", "terminologie",
    "science du hadith", "mustalah al-hadith", "jarh", "ta'dil", "isnad",
    "matn", "rawi", "transmetteur", "critique hadith"
]

# Stockage des résultats
all_results = {
    "search_date": datetime.now().isoformat(),
    "query_books": [b["title_fr"] for b in TARGET_BOOKS],
    "sources_searched": list(SOURCES.keys()),
    "books_found": []
}


def random_delay():
    """Delai aleatoire entre 2 et 5 secondes"""
    delay = random.uniform(2, 5)
    time.sleep(delay)


# Fix encoding for Windows
import sys
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')


def make_request(url, headers=None, timeout=30):
    """Effectue une requête HTTP avec gestion d'erreurs"""
    try:
        req_headers = headers or HEADERS
        response = requests.get(url, headers=req_headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"    [ERREUR HTTP] {e}")
        return None
    except Exception as e:
        print(f"    [ERREUR] {e}")
        return None


def search_islamhouse():
    """Recherche sur IslamHouse.com/fr"""
    print("\n" + "="*70)
    print("[SOURCE] IslamHouse.com/fr")
    print("="*70)
    
    base_url = SOURCES["islamhouse"]["base_url"]
    found_books = []
    
    # Recherche par mots-clés
    for book in TARGET_BOOKS:
        for keyword in book["keywords"][:2]:  # Limiter pour la rapidité
            search_url = f"{base_url}/fr/search?query={quote(keyword)}"
            print(f"[+] Recherche: '{keyword}'")
            
            response = make_request(search_url)
            if not response:
                random_delay()
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Chercher les liens de livres
            links = soup.find_all('a', href=re.compile(r'/fr/books/\d+'))
            for link in links:
                title = link.get_text(strip=True)
                href = link.get('href', '')
                if href and not href.startswith('http'):
                    href = urljoin(base_url, href)
                
                if title and len(title) > 3:
                    found_books.append({
                        "title": title,
                        "url": href,
                        "source": "islamhouse",
                        "search_keyword": keyword
                    })
            
            random_delay()
    
    # Parcourir les pages de livres
    for page in range(1, 3):
        url = f"{base_url}/fr/books/fr/{page}"
        print(f"[+] Parcours page {page}")
        
        response = make_request(url)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=re.compile(r'/fr/books/\d+'))
            
            for link in links:
                title = link.get_text(strip=True)
                href = link.get('href', '')
                if href and not href.startswith('http'):
                    href = urljoin(base_url, href)
                
                if title and len(title) > 3:
                    found_books.append({
                        "title": title,
                        "url": href,
                        "source": "islamhouse"
                    })
        
        random_delay()
    
    # Supprimer les doublons
    seen = set()
    unique_books = []
    for book in found_books:
        if book["url"] not in seen:
            seen.add(book["url"])
            unique_books.append(book)
    
    print(f"    → {len(unique_books)} livres uniques trouvés sur IslamHouse")
    return unique_books


def search_archive_org():
    """Recherche sur Archive.org"""
    print("\n" + "="*70)
    print("[SOURCE] Archive.org")
    print("="*70)
    
    found_books = []
    
    # Recherche par livre cible
    for book in TARGET_BOOKS:
        query = f"{book['title_fr']} hadith french"
        search_url = f"https://archive.org/search?query={quote(query)}"
        print(f"[+] Recherche: '{book['title_fr']}'")
        
        response = make_request(search_url)
        if not response:
            random_delay()
            continue
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Chercher les résultats
        results_divs = soup.find_all('div', class_=re.compile(r'result|item|tile'))
        for div in results_divs[:5]:  # Limiter les résultats
            link = div.find('a', href=re.compile(r'/details/'))
            title_elem = div.find(['h3', 'h4', '.title', '.ttl'])
            
            if link:
                href = link.get('href', '')
                if not href.startswith('http'):
                    href = f"https://archive.org{href}"
                
                title = title_elem.get_text(strip=True) if title_elem else "Sans titre"
                
                # Chercher lien PDF
                pdf_url = None
                pdf_link = div.find('a', href=re.compile(r'\.pdf', re.I))
                if pdf_link:
                    pdf_href = pdf_link.get('href', '')
                    if pdf_href and not pdf_href.startswith('http'):
                        pdf_url = f"https://archive.org{pdf_href}"
                    else:
                        pdf_url = pdf_href
                
                found_books.append({
                    "title": title,
                    "url": href,
                    "source": "archive_org",
                    "pdf_url": pdf_url,
                    "format": "PDF" if pdf_url else "HTML"
                })
        
        random_delay()
    
    print(f"    → {len(found_books)} résultats trouvés sur Archive.org")
    return found_books


def search_github():
    """Recherche sur GitHub"""
    print("\n" + "="*70)
    print("[SOURCE] GitHub.com")
    print("="*70)
    
    found_books = []
    queries = [
        "science hadith français PDF",
        "mustalah hadith français",
        "nukhbat fikar français",
        "taysir mustalah hadith"
    ]
    
    for query in queries:
        search_url = f"https://github.com/search?q={quote(query)}&type=repositories"
        print(f"[+] Recherche: '{query}'")
        
        response = make_request(search_url)
        if not response:
            random_delay()
            continue
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Chercher les dépôts
        repos = soup.find_all('a', href=re.compile(r'^/[^/]+/[^/]+$'))
        for repo in repos[:5]:
            href = repo.get('href', '')
            if href and not href.startswith('http'):
                href = f"https://github.com{href}"
            
            title = repo.get_text(strip=True)
            if title and len(title) > 3 and ' ' not in title:  # Format user/repo
                found_books.append({
                    "title": f"Dépôt: {title}",
                    "url": href,
                    "source": "github",
                    "format": "Git Repository"
                })
        
        random_delay()
    
    print(f"    → {len(found_books)} dépôts trouvés sur GitHub")
    return found_books


def get_book_details_full(book):
    """Récupère les détails complets d'un livre"""
    source = book.get("source", "")
    url = book.get("url", "")
    
    details = {
        "title": book.get("title", ""),
        "author": "",
        "translator": "",
        "pdf_url": book.get("pdf_url"),
        "source": SOURCES.get(source, {}).get("name", source),
        "source_url": url,
        "price": SOURCES.get(source, {}).get("price", "Inconnu"),
        "reliability": SOURCES.get(source, {}).get("reliability", "Inconnue"),
        "format": book.get("format", "PDF"),
        "language": "Français"
    }
    
    # Récupérer plus de détails si possible
    if source == "islamhouse" and not details["pdf_url"]:
        try:
            response = make_request(url)
            if response:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Chercher PDF
                pdf_link = soup.find('a', href=re.compile(r'\.pdf$', re.I))
                if pdf_link:
                    pdf_href = pdf_link.get('href', '')
                    if pdf_href:
                        if not pdf_href.startswith('http'):
                            pdf_href = urljoin(SOURCES["islamhouse"]["base_url"], pdf_href)
                        details["pdf_url"] = pdf_href
                
                # Auteur
                author_elem = soup.find(['.author', '.book-author'])
                if author_elem:
                    details["author"] = author_elem.get_text(strip=True)
                
                # Traducteur
                trans_elem = soup.find(text=re.compile(r'traducteur|ترجمة|traduit', re.I))
                if trans_elem:
                    parent = trans_elem.parent
                    if parent:
                        details["translator"] = parent.get_text(strip=True)[:100]
        except:
            pass
    
    # Identifier l'auteur par correspondance
    for target in TARGET_BOOKS:
        title_lower = details["title"].lower()
        for keyword in target["keywords"]:
            if keyword.lower() in title_lower:
                if not details["author"]:
                    details["author"] = target["author"]
                break
    
    return details


def filter_hadith_books(books):
    """Filtre les livres liés à la science du hadith"""
    filtered = []
    for book in books:
        title_lower = book.get("title", "").lower()
        if any(keyword.lower() in title_lower for keyword in HADITH_KEYWORDS):
            filtered.append(book)
    return filtered


def sort_by_reliability(books):
    """Classe les livres par fiabilité"""
    reliability_order = {
        "Haute": 1,
        "Moyenne": 2,
        "Variable": 3,
        "Faible": 4,
        "Inconnue": 5
    }
    
    def get_reliability_rank(book):
        rel = book.get("reliability", "")
        for key in reliability_order:
            if key in rel:
                return reliability_order[key]
        return 99
    
    return sorted(books, key=get_reliability_rank)


def main():
    print("="*70)
    print(" RECHERCHE MULTI-SOURCES DE LIVRES DE SCIENCE DU HADITH")
    print(" Langue: Français")
    print("="*70)
    print()
    
    all_books = []
    
    # Recherche sur toutes les sources
    try:
        islamhouse_books = search_islamhouse()
        all_books.extend(islamhouse_books)
    except Exception as e:
        print(f"[ERREUR] IslamHouse: {e}")
    
    try:
        archive_books = search_archive_org()
        all_books.extend(archive_books)
    except Exception as e:
        print(f"[ERREUR] Archive.org: {e}")
    
    try:
        github_books = search_github()
        all_books.extend(github_books)
    except Exception as e:
        print(f"[ERREUR] GitHub: {e}")
    
    print("\n" + "="*70)
    print(f"[INFO] Total brut: {len(all_books)} résultats trouvés")
    print("="*70)
    
    # Filtrer les livres de hadith
    print("\n[FILTRAGE] Sélection des livres de science du hadith...")
    hadith_books = filter_hadith_books(all_books)
    print(f"    → {len(hadith_books)} livres de hadith identifiés")
    
    # Récupérer les détails
    print("\n[DÉTAILS] Récupération des informations détaillées...")
    detailed_books = []
    for i, book in enumerate(hadith_books, 1):
        print(f"  [{i}/{len(hadith_books)}] {book['title'][:50]}...")
        details = get_book_details_full(book)
        detailed_books.append(details)
        time.sleep(0.5)
    
    # Trier par fiabilité
    sorted_books = sort_by_reliability(detailed_books)
    
    # Sauvegarder
    all_results["books_found"] = sorted_books
    all_results["total_found"] = len(sorted_books)
    
    output_file = "islamic_books_fr.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    # Résumé
    print("\n" + "="*70)
    print(f"[TERMINÉ] {len(sorted_books)} livres sauvegardés dans '{output_file}'")
    print("="*70)
    
    print("\n" + "="*70)
    print(" RÉSULTATS PAR ORDRE DE FIABILITÉ")
    print("="*70)
    
    for i, book in enumerate(sorted_books, 1):
        rel_short = book["reliability"].split("-")[0].strip()
        pdf_status = "[OK PDF]" if book.get("pdf_url") else "[NO PDF]"
        print(f"\n{i}. [{rel_short}] {book['title'][:60]}")
        print(f"   Auteur: {book['author'] or 'Inconnu'}")
        if book.get("translator"):
            trans = book['translator'][:50]
            print(f"   Traducteur: {trans}")
        print(f"   Source: {book['source']}")
        print(f"   Format: {book['format']} ({pdf_status})")
        if book.get("pdf_url"):
            pdf = book['pdf_url'][:80]
            print(f"   PDF: {pdf}...")
        print(f"   Fiabilité: {book['reliability']}")
    
    # Recommandation
    print("\n" + "="*70)
    print(" RECOMMANDATION POUR PROJET ISLAMIQUE SÉRIEUX")
    print("="*70)
    
    high_reliability = [b for b in sorted_books if "Haute" in b["reliability"]]
    with_pdf = [b for b in sorted_books if b.get("pdf_url")]
    
    if high_reliability:
        print(f"\n[OK] {len(high_reliability)} livre(s) de source haute fiabilité trouvé(s)")
        for book in high_reliability[:3]:
            print(f"  - {book['title']}")
    
    if with_pdf:
        print(f"\n[OK] {len(with_pdf)} livre(s) avec PDF direct disponible")
        print("\n[RECOMMANDATION]")
        print("Pour un projet basé sur la méthodologie des Muhadditheen:")
        print("1. Privilégier les sources officielles (IslamHouse)")
        print("2. Vérifier la chaîne de transmission des traductions")
        print("3. Consulter les explications (sharh) des savants")


if __name__ == "__main__":
    main()
