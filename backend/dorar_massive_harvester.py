#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Harvester Massif pour Dorar.net
Extrait TOUS les livres de hadith disponibles sur dorar.net
Focus: Sources salafies authentiques
"""

import sys
import sqlite3
import hashlib
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent))
from dorar_html_parser import DorarHTMLParser

class DorarMassiveHarvester:
    """Harvester pour extraire massivement depuis dorar.net"""
    
    # Livres de hadith majeurs sur dorar.net
    MAJOR_BOOKS = {
        'kutub_sittah': [
            'صحيح البخاري',  # Sahih Bukhari
            'صحيح مسلم',      # Sahih Muslim
            'سنن أبي داود',   # Sunan Abu Dawud
            'جامع الترمذي',   # Jami' Tirmidhi
            'سنن النسائي',    # Sunan Nasa'i
            'سنن ابن ماجه',   # Sunan Ibn Majah
        ],
        'muwatta': [
            'موطأ مالك',      # Muwatta Malik
        ],
        'musnad': [
            'مسند أحمد',      # Musnad Ahmad
            'مسند الشافعي',   # Musnad Shafi'i
            'مسند أبي حنيفة', # Musnad Abu Hanifa
        ],
        'popular': [
            'رياض الصالحين',  # Riyad al-Salihin
            'بلوغ المرام',     # Bulugh al-Maram
            'الأدب المفرد',    # Al-Adab al-Mufrad
            'الأربعون النووية', # 40 Nawawi
            'شرح السنة',       # Sharh al-Sunnah
        ],
        'specialized': [
            'صحيح الترغيب والترهيب',  # Sahih Targhib
            'صحيح الجامع الصغير',     # Sahih Jami'
            'السلسلة الصحيحة',        # Silsilah Sahihah (Albani)
            'السلسلة الضعيفة',        # Silsilah Da'ifah (Albani)
            'إرواء الغليل',           # Irwa al-Ghalil (Albani)
        ],
        'fiqh': [
            'نيل الأوطار',     # Nayl al-Awtar
            'المحلى',          # Al-Muhalla (Ibn Hazm)
            'فتح الباري',      # Fath al-Bari
        ]
    }
    
    def __init__(self, db_path: str = None):
        """Initialise le harvester"""
        if db_path is None:
            db_path = Path(__file__).parent / 'almizane.db'
        
        self.db_path = db_path
        self.parser = DorarHTMLParser()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Al-Mizan-Harvester/8.0',
            'Accept': '*/*',
            'Referer': 'https://dorar.net/'
        })
    
    def get_all_books(self) -> List[str]:
        """Récupère la liste de tous les livres disponibles sur dorar.net"""
        print("🔍 Récupération de la liste des livres sur dorar.net...")
        
        try:
            response = self.session.get('https://dorar.net/hadith', timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Chercher les sélecteurs de livres
            books = []
            
            # Méthode 1: Chercher dans les options de sélection
            selects = soup.find_all('select')
            for select in selects:
                options = select.find_all('option')
                for option in options:
                    text = option.get_text(strip=True)
                    if text and len(text) > 3:  # Filtrer les options vides
                        books.append(text)
            
            # Méthode 2: Chercher dans les liens
            links = soup.find_all('a', href=True)
            for link in links:
                if '/hadith/' in link['href']:
                    text = link.get_text(strip=True)
                    if text and len(text) > 3:
                        books.append(text)
            
            # Dédupliquer
            books = list(set(books))
            
            print(f"✅ {len(books)} livres trouvés")
            return books
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return []
    
    def harvest_book(self, book_name: str, max_pages: int = 100) -> List[Dict]:
        """
        Harvest tous les hadiths d'un livre
        
        Args:
            book_name: Nom du livre en arabe
            max_pages: Nombre maximum de pages à parcourir
        """
        print(f"\n📚 Harvesting: {book_name}")
        print("-" * 70)
        
        all_hadiths = []
        page = 1
        consecutive_empty = 0
        
        while page <= max_pages and consecutive_empty < 3:
            try:
                # Recherche avec pagination
                params = {
                    'skey': book_name,
                    'page': page
                }
                
                hadiths = self.parser.search_hadith(book_name)
                
                if hadiths and len(hadiths) > 0:
                    all_hadiths.extend(hadiths)
                    consecutive_empty = 0
                    print(f"  Page {page}: {len(hadiths)} hadiths")
                else:
                    consecutive_empty += 1
                    print(f"  Page {page}: vide ({consecutive_empty}/3)")
                
                page += 1
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"  ❌ Erreur page {page}: {e}")
                consecutive_empty += 1
        
        print(f"✅ Total: {len(all_hadiths)} hadiths pour {book_name}")
        return all_hadiths
    
    def harvest_all_categories(self):
        """Harvest toutes les catégories de livres"""
        print("=" * 70)
        print("🚀 HARVESTING MASSIF DORAR.NET")
        print("=" * 70)
        print()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        total_inserted = 0
        total_duplicates = 0
        
        for category, books in self.MAJOR_BOOKS.items():
            print(f"\n📂 Catégorie: {category.upper()}")
            print("=" * 70)
            
            for book in books:
                hadiths = self.harvest_book(book)
                
                # Insérer dans la base
                inserted, duplicates = self._insert_hadiths(cursor, hadiths, book)
                total_inserted += inserted
                total_duplicates += duplicates
                
                conn.commit()
                
                print(f"  💾 {inserted} insérés, {duplicates} doublons")
                time.sleep(2)  # Pause entre les livres
        
        conn.close()
        
        print()
        print("=" * 70)
        print("📊 RÉSULTATS FINAUX")
        print("=" * 70)
        print(f"✅ Total hadiths insérés: {total_inserted:,}")
        print(f"⚠️  Total doublons évités: {total_duplicates:,}")
        print()
    
    def _insert_hadiths(self, cursor, hadiths: List[Dict], book_name: str) -> tuple:
        """Insère les hadiths dans la base"""
        inserted = 0
        duplicates = 0
        
        for hadith in hadiths:
            try:
                # Créer hash
                matn_hash = hashlib.sha256(
                    hadith.get('matn_ar', '').encode('utf-8')
                ).hexdigest()
                
                # Vérifier doublon
                cursor.execute(
                    "SELECT COUNT(*) FROM hadiths WHERE matn_hash = ?",
                    (matn_hash,)
                )
                
                if cursor.fetchone()[0] > 0:
                    duplicates += 1
                    continue
                
                # Insérer
                cursor.execute("""
                    INSERT INTO hadiths (
                        collection,
                        numero_hadith,
                        matn_ar,
                        matn_en,
                        grade_final,
                        reference,
                        source_api,
                        matn_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    book_name,
                    hadith.get('numero_hadith', ''),
                    hadith.get('matn_ar', ''),
                    hadith.get('matn_en', ''),
                    hadith.get('grade_final', ''),
                    hadith.get('reference', ''),
                    'dorar.net',
                    matn_hash
                ))
                
                inserted += 1
                
            except Exception as e:
                print(f"    ❌ Erreur insertion: {e}")
        
        return inserted, duplicates
    
    def harvest_custom_search(self, keywords: List[str]):
        """Harvest basé sur des mots-clés personnalisés"""
        print("\n🔍 Recherche personnalisée")
        print("=" * 70)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for keyword in keywords:
            print(f"\n🔎 Mot-clé: {keyword}")
            hadiths = self.parser.search_hadith(keyword)
            
            if hadiths:
                inserted, duplicates = self._insert_hadiths(cursor, hadiths, f"search_{keyword}")
                print(f"  ✅ {inserted} insérés, {duplicates} doublons")
                conn.commit()
            
            time.sleep(1)
        
        conn.close()

def main():
    """Point d'entrée principal"""
    print("\n" + "=" * 70)
    print("🌟 DORAR.NET MASSIVE HARVESTER")
    print("=" * 70)
    print()
    print("Ce script va extraire TOUS les livres de hadith de dorar.net")
    print("Sources: Kutub Sittah, Musnad, Riyad al-Salihin, etc.")
    print()
    
    response = input("Continuer ? (o/n) : ")
    if response.lower() != 'o':
        print("❌ Annulé")
        return
    
    harvester = DorarMassiveHarvester()
    
    # Option 1: Harvest toutes les catégories prédéfinies
    print("\n1. Harvest catégories prédéfinies")
    print("2. Recherche personnalisée")
    print("3. Découvrir tous les livres disponibles")
    
    choice = input("\nChoix (1-3) : ")
    
    if choice == '1':
        harvester.harvest_all_categories()
    elif choice == '2':
        keywords = input("Mots-clés (séparés par des virgules) : ").split(',')
        keywords = [k.strip() for k in keywords]
        harvester.harvest_custom_search(keywords)
    elif choice == '3':
        books = harvester.get_all_books()
        print("\n📚 Livres disponibles:")
        for i, book in enumerate(books[:50], 1):
            print(f"  {i}. {book}")
        
        if len(books) > 50:
            print(f"  ... et {len(books) - 50} autres")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()