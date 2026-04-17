#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import Sahih al-Bukhari depuis mhashim6 vers la base de données
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from normalizer import HadithNormalizer
from database.db_manager import DatabaseManager
from sources_registry import get_source_by_id

def download_bukhari():
    """Télécharge Sahih al-Bukhari depuis mhashim6"""
    print("=== TÉLÉCHARGEMENT SAHIH AL-BUKHARI ===\n")
    
    source = get_source_by_id('open-hadith-data-mhashim')
    if not source:
        print("❌ Source non trouvée")
        return None
    
    url = f"{source['raw_data_url']}/{source['books']['bukhari']}"
    print(f"URL: {url}\n")
    
    try:
        print("📥 Téléchargement en cours...")
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        content = response.text
        print(f"✅ Téléchargé: {len(content)} caractères")
        print(f"   Lignes: ~{content.count(chr(10))}")
        
        return content
        
    except Exception as e:
        print(f"❌ Erreur téléchargement: {e}")
        return None

def import_to_database(csv_content: str, limit: int = None):
    """Importe les hadiths dans la base de données"""
    print("\n=== NORMALISATION ET IMPORT ===\n")
    
    # Normaliser
    normalizer = HadithNormalizer()
    hadiths = normalizer.normalize_mhashim6_csv(csv_content, 'bukhari')
    
    if limit:
        hadiths = hadiths[:limit]
        print(f"⚠️  Limitation à {limit} hadiths pour test\n")
    
    print(f"📊 Hadiths normalisés: {len(hadiths)}")
    
    # Connexion base de données
    try:
        db = DatabaseManager()
        print("✅ Connexion base de données établie\n")
        
        # Insérer les hadiths
        print("💾 Insertion en base de données...")
        inserted = 0
        errors = 0
        
        for i, hadith in enumerate(hadiths, 1):
            try:
                # Insérer le hadith
                cursor = db.conn.cursor()
                cursor.execute("""
                    INSERT INTO hadiths (
                        source, book, book_code, hadith_number,
                        full_text_ar, isnad_ar, matn_ar,
                        grade, imported_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    hadith['source'],
                    hadith['book'],
                    hadith['book_code'],
                    hadith['hadith_number'],
                    hadith['full_text_ar'],
                    hadith['isnad_ar'],
                    hadith['matn_ar'],
                    hadith['grade'],
                    hadith['imported_at']
                ))
                
                hadith_id = cursor.lastrowid
                
                # Insérer les narrateurs
                for narrator_name in hadith['narrator_chain']:
                    if narrator_name:
                        cursor.execute("""
                            INSERT OR IGNORE INTO narrators (name_ar)
                            VALUES (?)
                        """, (narrator_name,))
                
                db.conn.commit()
                inserted += 1
                
                if i % 100 == 0:
                    print(f"  Progression: {i}/{len(hadiths)} hadiths")
                
            except Exception as e:
                errors += 1
                if errors <= 5:  # Afficher seulement les 5 premières erreurs
                    print(f"  ⚠️  Erreur hadith #{hadith['hadith_number']}: {e}")
        
        print(f"\n✅ Import terminé:")
        print(f"   - Insérés: {inserted}")
        print(f"   - Erreurs: {errors}")
        
        # Statistiques
        stats = normalizer.get_stats()
        print(f"\n📊 Statistiques normalisation:")
        print(f"   - Total traité: {stats['total_processed']}")
        print(f"   - Succès: {stats['successful']}")
        print(f"   - Erreurs: {stats['errors']}")
        
        db.close()
        return inserted
        
    except Exception as e:
        print(f"❌ Erreur base de données: {e}")
        return 0

def main():
    """Fonction principale"""
    print("╔════════════════════════════════════════╗")
    print("║   IMPORT SAHIH AL-BUKHARI - AL-MĪZĀN  ║")
    print("╚════════════════════════════════════════╝\n")
    
    # Demander confirmation
    print("⚠️  Ce script va télécharger et importer Sahih al-Bukhari")
    print("   Source: mhashim6/Open-Hadith-Data")
    print("   Nombre estimé: ~7,500 hadiths\n")
    
    # Mode test ou complet
    mode = input("Mode [test=100 hadiths / full=tous] (défaut: test): ").strip().lower()
    
    if mode == 'full':
        limit = None
        print("\n🚀 Mode COMPLET activé\n")
    else:
        limit = 100
        print("\n🧪 Mode TEST activé (100 hadiths)\n")
    
    # Téléchargement
    csv_content = download_bukhari()
    if not csv_content:
        print("\n❌ Échec du téléchargement")
        return
    
    # Import
    inserted = import_to_database(csv_content, limit=limit)
    
    if inserted > 0:
        print(f"\n✅ SUCCÈS: {inserted} hadiths importés dans la base de données")
    else:
        print("\n❌ ÉCHEC: Aucun hadith importé")

if __name__ == '__main__':
    main()