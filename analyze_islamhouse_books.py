#!/usr/bin/env python3
"""
Analyse des livres IslamHouse FR pour trouver les livres de hadith
"""

import json

# Charger les livres
with open('islamhouse_all_books_fr.json', 'r', encoding='utf-8') as f:
    books = json.load(f)

print(f"Total livres: {len(books)}")
print("\n" + "="*70)
print("RECHERCHE DE LIVRES DE HADITH")
print("="*70)

# Mots-clés liés au hadith
hadith_keywords = [
    "hadith", "حديث", "sunna", "sunnah", "sunan",
    "bukhari", "boukhari", "muslim", "tirmidhi", "abu dawud",
    "nasaï", "ibn majah", "ahmad", "mousnad", "musnad",
    "terminologie", "mustalah", "science du hadith",
    "isnad", "matn", "rawi", "transmetteur"
]

# Chercher les livres de hadith
hadith_books = []
for book in books:
    title = book.get('title', '').lower()
    desc = book.get('description', '').lower() if book.get('description') else ''
    full_text = f"{title} {desc}"
    
    for keyword in hadith_keywords:
        if keyword in full_text:
            hadith_books.append({
                'title': book.get('title'),
                'id': book.get('id'),
                'keyword': keyword
            })
            break

print(f"\n📚 Livres liés au hadith trouvés: {len(hadith_books)}")
print("\nListe des livres de hadith:")
for i, book in enumerate(hadith_books[:30], 1):
    print(f"{i}. {book['title'][:70]}... (matched: {book['keyword']})")

print("\n" + "="*70)
print("RECHERCHE SPÉCIFIQUE DES LIVRES CIBLES")
print("="*70)

# Recherche spécifique avec variations
targets = {
    "Nukhbat": ["nukhbat", "نخبة", "nukhbah"],
    "Mustalah": ["mustalah", "مصطلح", "mustalaḥ"],
    "Taysir": ["taysir", "تيسير", "tayser"],
    "Muqiza": ["muqiza", "مقيزة", "muqizah"],
    "Baïqouniyya": ["baïqoun", "beyqoun", "baeqoun", "البيقونية", "beyquniyyah", "baiquniyyah", "al-bayquniyah"]
}

for target_name, keywords in targets.items():
    print(f"\n🔍 Recherche: {target_name}")
    found = []
    for book in books:
        title = book.get('title', '').lower()
        for kw in keywords:
            if kw.lower() in title:
                found.append(book)
                break
    
    if found:
        print(f"   ✅ Trouvé: {len(found)}")
        for b in found[:3]:
            print(f"      → {b.get('title')}")
    else:
        print(f"   ❌ Non trouvé")

# Afficher tous les titres pour analyse
print("\n" + "="*70)
print("TOUS LES TITRES DE LIVRES (pour référence)")
print("="*70)

for i, book in enumerate(books, 1):
    print(f"{i}. {book.get('title', 'N/A')}")
