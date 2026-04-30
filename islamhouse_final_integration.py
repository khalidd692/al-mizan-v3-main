#!/usr/bin/env python3
"""
Intégration finale API IslamHouse v3 pour Al Mîzân
Utilise tous les livres de hadith disponibles
"""

import requests
import json
import os
from datetime import datetime

API_KEY = os.getenv("ISLAMHOUSE_API_KEY", "your_api_key_here")
BASE_URL = "https://api3.islamhouse.com/v3"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

def api_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_all_books():
    """Récupère tous les livres FR"""
    all_books = []
    for page in range(1, 10):
        url = f"{BASE_URL}/{API_KEY}/main/books/fr/fr/{page}/50/json"
        data = api_request(url)
        if data and isinstance(data, dict) and 'data' in data:
            books = data['data']
            all_books.extend(books)
            print(f"  Page {page}: {len(books)} livres")
            if len(books) < 50:
                break
        else:
            break
    return all_books

def find_hadith_books(books):
    """Trouve tous les livres liés au hadith"""
    keywords = [
        "hadith", "حديث", "sunna", "sunnah", "boukhari", "bukhari", 
        "muslim", "science", "terminologie", "mustalah", "isnad",
        "transmetteur", "rawi", "matn", "authenticité"
    ]
    
    hadith_books = []
    for book in books:
        title = book.get('title', '').lower()
        desc = (book.get('description') or '').lower()
        full_text = f"{title} {desc}"
        
        for kw in keywords:
            if kw in full_text:
                # Extraire PDF URL
                pdf_url = ""
                attachments = book.get('attachments', [])
                for att in attachments:
                    if att.get('extension_type') == 'PDF' or 'pdf' in att.get('mimetype', ''):
                        pdf_url = att.get('url', '')
                        if pdf_url and not pdf_url.startswith('http'):
                            pdf_url = f"https://d1.islamhouse.com/{pdf_url}"
                        break
                
                hadith_books.append({
                    'id': book.get('id'),
                    'title': book.get('title'),
                    'description': book.get('description', '')[:200],
                    'pdf_url': pdf_url,
                    'source_url': f"https://islamhouse.com/fr/books/{book.get('id', '')}",
                    'matched_keyword': kw
                })
                break
    
    return hadith_books

def update_zone_file(zone_file, entries, source_name="islamhouse_api"):
    """Met à jour un fichier de zone"""
    zone_path = f"sources_fr/{zone_file}.json"
    
    try:
        if os.path.exists(zone_path):
            with open(zone_path, 'r', encoding='utf-8') as f:
                zone_data = json.load(f)
        else:
            zone_num = zone_file.split('_')[1]
            zone_data = {
                "zone": int(zone_num),
                "nom": zone_file.replace('zone_', '').replace('_', ' ').upper(),
                "description": f"Zone {zone_num}",
                "entrees": [],
                "statut_global": "VIDE",
                "sources_utilisees": [],
                "count_entrees": 0
            }
        
        # Ajouter les entrées
        for entry in entries:
            zone_entry = {
                "contenu_fr": entry['description'] if entry['description'] else entry['title'],
                "source": source_name,
                "titre_ouvrage": entry['title'],
                "url": entry['source_url'],
                "pdf_url": entry['pdf_url'],
                "statut": "PENDING_FR",
                "id_islamhouse": entry['id']
            }
            zone_data['entrees'].append(zone_entry)
        
        zone_data['count_entrees'] = len(zone_data['entrees'])
        if zone_data['count_entrees'] > 0:
            zone_data['statut_global'] = "PARTIEL" if zone_data['count_entrees'] < 3 else "REMPLI"
        
        sources = zone_data.get('sources_utilisees', [])
        if source_name not in sources:
            sources.append(source_name)
        zone_data['sources_utilisees'] = sources
        
        with open(zone_path, 'w', encoding='utf-8') as f:
            json.dump(zone_data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"   Erreur: {e}")
        return False

def main():
    print("="*70)
    print("INTÉGRATION FINALE ISLAMHOUSE API v3")
    print("="*70)
    
    # 1. Récupérer les livres
    print("\n📚 Récupération des livres...")
    books = get_all_books()
    print(f"   Total: {len(books)} livres")
    
    # 2. Trouver les livres de hadith
    print("\n🔍 Recherche des livres de hadith...")
    hadith_books = find_hadith_books(books)
    print(f"   Trouvé: {len(hadith_books)} livres liés au hadith")
    
    # 3. Afficher les livres trouvés
    print("\n📖 Livres de hadith trouvés:")
    for i, book in enumerate(hadith_books, 1):
        print(f"   {i}. {book['title'][:65]}")
        print(f"      (matched: {book['matched_keyword']})")
    
    # 4. Distribuer dans les zones appropriées
    print("\n📁 Distribution dans les zones...")
    
    # Zone 19: MASĀDIR THĀNAWIYYAH (sources secondaires)
    masadir_books = [b for b in hadith_books if any(k in b['title'].lower() for k in ['science', 'terminologie', 'mustalah', 'methodologie'])]
    
    # Zone 22: FAWĀʾID TARBAWIYYAH (leçons éducatives)
    tarbawi_books = [b for b in hadith_books if any(k in b['title'].lower() for k in ['leçon', 'conseil', 'exhortation', 'piété'])]
    
    # Zone 38: TAKHRĪJ WA TAḤQĪQ (recherche et authentification)
    takhrij_books = [b for b in hadith_books if any(k in b['title'].lower() for k in ['authentique', 'vérification', 'takhrij', 'tahqiq'])]
    
    # Zone 11: SHURŪḤ (commentaires)
    shuruh_books = [b for b in hadith_books if any(k in b['title'].lower() for k in ['explication', 'commentaire', 'sharh', 'biographie'])]
    
    # Tous les autres livres de hadith -> zone 22 ou zone 10
    other_hadith = [b for b in hadith_books if b not in masadir_books + tarbawi_books + takhrij_books + shuruh_books]
    
    # Distribuer les "autres" dans zone 22 (fawaid) et zone 10 (sabab al-wurud contexte)
    mid = len(other_hadith) // 2
    fawaid_books = other_hadith[:mid] if mid > 0 else other_hadith
    sabab_books = other_hadith[mid:] if mid > 0 else []
    
    # Mettre à jour les fichiers
    updates = []
    
    if masadir_books:
        if update_zone_file("zone_19_masadir_thanawiyyah", masadir_books):
            updates.append(f"zone_19 (+{len(masadir_books)})")
    
    if tarbawi_books or fawaid_books:
        combined = tarbawi_books + fawaid_books
        if update_zone_file("zone_22_fawaid_tarhawiyyah", combined):
            updates.append(f"zone_22 (+{len(combined)})")
    
    if takhrij_books:
        if update_zone_file("zone_38_takhrij_wa_tahqiq", takhrij_books):
            updates.append(f"zone_38 (+{len(takhrij_books)})")
    
    if shuruh_books:
        if update_zone_file("zone_11_shuruh", shuruh_books):
            updates.append(f"zone_11 (+{len(shuruh_books)})")
    
    if sabab_books:
        if update_zone_file("zone_10_sabab_al_wurud", sabab_books):
            updates.append(f"zone_10 (+{len(sabab_books)})")
    
    # 5. Sauvegarder le rapport
    report = {
        "date": datetime.now().isoformat(),
        "api": "IslamHouse v3",
        "total_books_fetched": len(books),
        "hadith_books_found": len(hadith_books),
        "zones_updated": updates,
        "hadith_books": hadith_books
    }
    
    with open("islamhouse_final_report.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 6. Résumé
    print("\n" + "="*70)
    print("RÉSULTAT FINAL")
    print("="*70)
    print(f"✅ API IslamHouse v3 intégrée")
    print(f"   • Livres FR: {len(books)}")
    print(f"   • Livres de hadith: {len(hadith_books)}")
    print(f"   • Zones mises à jour: {len(updates)}")
    for u in updates:
        print(f"      - {u}")
    print(f"\n📄 Rapport: islamhouse_final_report.json")
    
    return True

if __name__ == "__main__":
    main()
