#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Harvester Automatique Dorar.net
Lance l'extraction sans interaction utilisateur
"""

import sys
import sqlite3
import hashlib
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dorar_html_parser import DorarHTMLParser

class AutoDorarHarvester:
    """Harvester automatique pour dorar.net"""
    
    # Livres prioritaires (ordre d'importance)
    PRIORITY_BOOKS = [
        # Kutub al-Sittah
        ('صحيح البخاري', 'sahih_bukhari'),
        ('صحيح مسلم', 'sahih_muslim'),
        ('سنن أبي داود', 'sunan_abu_dawud'),
        ('جامع الترمذي', 'jami_tirmidhi'),
        ('سنن النسائي', 'sunan_nasai'),
        ('سنن ابن ماجه', 'sunan_ibn_majah'),
        
        # Recueils populaires
        ('رياض الصالحين', 'riyad_salihin'),
        ('بلوغ المرام', 'bulugh_maram'),
        ('الأدب المفرد', 'adab_mufrad'),
        
        # Musnad
        ('مسند أحمد', 'musnad_ahmad'),
        ('موطأ مالك', 'muwatta_malik'),
    ]
    
    def __init__(self):
        self.db_path = Path(__file__).parent / 'almizane.db'
        self.parser = DorarHTMLParser()
        self.stats = {
            'total_inserted': 0,
            'total_duplicates': 0,
            'books_processed': 0,
            'errors': 0
        }
    
    def harvest_book(self, book_ar: str, book_en: str) -> tuple:
        """Harvest un livre spécifique"""
        print(f"\n{'='*70}")
        print(f"📚 {book_ar} ({book_en})")
        print('='*70)
        
        try:
            # Rechercher les hadiths
            hadiths = self.parser.search_hadith(book_ar)
            
            if not hadiths:
                print(f"⚠️  Aucun hadith trouvé pour {book_ar}")
                return 0, 0
            
            print(f"✅ {len(hadiths)} hadiths récupérés")
            
            # Insérer dans la base
            inserted, duplicates = self._insert_hadiths(hadiths, book_en)
            
            print(f"💾 {inserted} insérés, {duplicates} doublons")
            
            return inserted, duplicates
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            self.stats['errors'] += 1
            return 0, 0
    
    def _insert_hadiths(self, hadiths: list, collection: str) -> tuple:
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
                
                # Hash pour détecter doublons
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
                print(f"  ⚠️  Erreur insertion: {e}")
        
        conn.commit()
        conn.close()
        
        return inserted, duplicates
    
    def run(self):
        """Lance l'extraction automatique"""
        print("\n" + "="*70)
        print("🚀 HARVESTING AUTOMATIQUE DORAR.NET")
        print("="*70)
        print(f"\n📋 {len(self.PRIORITY_BOOKS)} livres à extraire")
        print()
        
        start_time = time.time()
        
        for book_ar, book_en in self.PRIORITY_BOOKS:
            inserted, duplicates = self.harvest_book(book_ar, book_en)
            
            self.stats['total_inserted'] += inserted
            self.stats['total_duplicates'] += duplicates
            self.stats['books_processed'] += 1
            
            # Pause entre les livres
            time.sleep(2)
        
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
        
        # État de la base
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM hadiths")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT collection) FROM hadiths")
        collections = cursor.fetchone()[0]
        
        print(f"\n📚 Base de données:")
        print(f"   Total: {total:,} hadiths")
        print(f"   Collections: {collections}")
        
        conn.close()
        
        print("\n" + "="*70)
        print("✅ HARVESTING TERMINÉ")
        print("="*70)

if __name__ == '__main__':
    try:
        harvester = AutoDorarHarvester()
        harvester.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompu")
    except Exception as e:
        print(f"\n\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()