#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dorar.net Paginated Harvester
Extrait TOUS les hadiths avec pagination complète
"""

import sys
import sqlite3
import hashlib
import time
import json
import re
import requests
from pathlib import Path
from typing import List, Dict
from bs4 import BeautifulSoup

class DorarPaginatedHarvester:
    """Harvester avec pagination pour dorar.net"""
    
    BASE_URL = 'https://dorar.net/hadith/search'
    
    # Livres prioritaires avec leurs IDs dorar.net
    BOOKS = [
        ('صحيح البخاري', 'sahih_bukhari', 1),
        ('صحيح مسلم', 'sahih_muslim', 2),
        ('سنن أبي داود', 'sunan_abu_dawud', 3),
        ('جامع الترمذي', 'jami_tirmidhi', 4),
        ('سنن النسائي', 'sunan_nasai', 5),
        ('سنن ابن ماجه', 'sunan_ibn_majah', 6),
        ('رياض الصالحين', 'riyad_salihin', 11),
        ('بلوغ المرام', 'bulugh_maram', 12),
        ('الأدب المفرد', 'adab_mufrad', 13),
        ('مسند أحمد', 'musnad_ahmad', 7),
        ('موطأ مالك', 'muwatta_malik', 8),
    ]
    
    def __init__(self):
        self.db_path = Path(__file__).parent / 'almizane.db'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Referer': 'https://dorar.net/'
        })
        self.stats = {
            'total_inserted': 0,
            'total_duplicates': 0,
            'books_processed': 0,
            'errors': 0
        }
    
    def harvest_book_paginated(self, book_ar: str, book_en: str, book_id: int) -> tuple:
        """Harvest un livre avec pagination complète"""
        print(f"\n{'='*70}")
        print(f"📚 {book_ar} ({book_en})")
        print('='*70)
        
        all_hadiths = []
        page = 1
        consecutive_empty = 0
        max_pages = 500  # Limite de sécurité
        
        while page <= max_pages and consecutive_empty < 3:
            try:
                print(f"  📄 Page {page}...", end=' ', flush=True)
                
                # Requête avec pagination
                params = {
                    'skey': book_ar,
                    'page': page,
                    'callback': 'jQuery'
                }
                
                response = self.session.get(
                    self.BASE_URL,
                    params=params,
                    timeout=15
                )
                response.raise_for_status()
                
                # Parser JSONP
                jsonp_match = re.search(r'jQuery\((.*)\)', response.text, re.DOTALL)
                if not jsonp_match:
                    print("❌ Format invalide")
                    consecutive_empty += 1
                    page += 1
                    continue
                
                data = json.loads(jsonp_match.group(1))
                html_content = data.get('ahadith', {}).get('result', '')
                
                if not html_content or html_content.strip() == '':
                    print("vide")
                    consecutive_empty += 1
                    page += 1
                    continue
                
                # Parser HTML
                hadiths = self._parse_html(html_content)
                
                if hadiths and len(hadiths) > 0:
                    all_hadiths.extend(hadiths)
                    print(f"✅ {len(hadiths)} hadiths")
                    consecutive_empty = 0
                else:
                    print("vide")
                    consecutive_empty += 1
                
                page += 1
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Erreur: {e}")
                consecutive_empty += 1
                page += 1
        
        print(f"\n✅ Total récupéré: {len(all_hadiths)} hadiths")
        
        # Insérer dans la base
        if all_hadiths:
            inserted, duplicates = self._insert_hadiths(all_hadiths, book_en)
            print(f"💾 {inserted} insérés, {duplicates} doublons")
            return inserted, duplicates
        
        return 0, 0
    
    def _parse_html(self, html: str) -> List[Dict]:
        """Parse le HTML pour extraire les hadiths"""
        soup = BeautifulSoup(html, 'html.parser')
        hadiths = []
        
        # Chercher les divs de hadiths
        hadith_divs = soup.find_all('div', class_='hadith')
        
        for div in hadith_divs:
            try:
                hadith = {}
                
                # Texte du hadith
                matn_elem = div.find('div', class_='hadith_text')
                if matn_elem:
                    hadith['matn_ar'] = matn_elem.get_text(strip=True)
                
                # Référence
                ref_elem = div.find('div', class_='hadith_reference')
                if ref_elem:
                    hadith['reference'] = ref_elem.get_text(strip=True)
                
                # Grade
                grade_elem = div.find('span', class_='grade')
                if grade_elem:
                    hadith['grade_final'] = grade_elem.get_text(strip=True)
                
                # Numéro
                num_elem = div.find('span', class_='hadith_number')
                if num_elem:
                    hadith['numero_hadith'] = num_elem.get_text(strip=True)
                
                if hadith.get('matn_ar'):
                    hadiths.append(hadith)
                    
            except Exception as e:
                continue
        
        return hadiths
    
    def _insert_hadiths(self, hadiths: List[Dict], collection: str) -> tuple:
        """Insère les hadiths dans la base"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        inserted = 0
        duplicates = 0
        
        for hadith in hadiths:
            try:
                matn_ar = hadith.get('matn_ar', '')
                if not matn_ar:
                    continue
                
                # Hash
                matn_hash = hashlib.sha256(matn_ar.encode('utf-8')).hexdigest()
                
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
                        grade_final,
                        reference,
                        source_api,
                        matn_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    collection,
                    hadith.get('numero_hadith', ''),
                    matn_ar,
                    hadith.get('grade_final', ''),
                    hadith.get('reference', ''),
                    'dorar.net',
                    matn_hash
                ))
                
                inserted += 1
                
            except Exception as e:
                pass
        
        conn.commit()
        conn.close()
        
        return inserted, duplicates
    
    def run(self):
        """Lance l'extraction complète"""
        print("\n" + "="*70)
        print("🚀 DORAR.NET PAGINATED HARVESTER")
        print("="*70)
        print(f"\n📋 {len(self.BOOKS)} livres à extraire avec pagination complète")
        print()
        
        start_time = time.time()
        
        for book_ar, book_en, book_id in self.BOOKS:
            inserted, duplicates = self.harvest_book_paginated(book_ar, book_en, book_id)
            
            self.stats['total_inserted'] += inserted
            self.stats['total_duplicates'] += duplicates
            self.stats['books_processed'] += 1
            
            time.sleep(2)  # Pause entre livres
        
        elapsed = time.time() - start_time
        
        # Rapport final
        print("\n" + "="*70)
        print("📊 RAPPORT FINAL")
        print("="*70)
        print(f"✅ Livres traités: {self.stats['books_processed']}")
        print(f"✅ Hadiths insérés: {self.stats['total_inserted']:,}")
        print(f"⚠️  Doublons évités: {self.stats['total_duplicates']:,}")
        print(f"❌ Erreurs: {self.stats['errors']}")
        print(f"⏱️  Temps: {elapsed/60:.1f} minutes")
        
        # État base
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM hadiths")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT collection) FROM hadiths")
        collections = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT collection, COUNT(*) 
            FROM hadiths 
            GROUP BY collection 
            ORDER BY COUNT(*) DESC
        """)
        
        print(f"\n📚 Base de données:")
        print(f"   Total: {total:,} hadiths")
        print(f"   Collections: {collections}")
        print(f"\n📖 Par collection:")
        for coll, count in cursor.fetchall():
            print(f"   {coll}: {count:,}")
        
        conn.close()
        
        print("\n" + "="*70)
        print("✅ HARVESTING TERMINÉ")
        print("="*70)

if __name__ == '__main__':
    try:
        harvester = DorarPaginatedHarvester()
        harvester.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompu")
    except Exception as e:
        print(f"\n\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()