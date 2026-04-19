#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test du matching entre collections et autorités
"""

import sqlite3
import sys
from pathlib import Path

# Ajouter backend au path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from corpus_validator import CorpusValidator

def test_matching():
    """Test le matching pour les collections problématiques"""
    validator = CorpusValidator()
    
    # Collections à tester
    test_collections = [
        "Sahih al-Bukhari",
        "Sunan Abu Dawud",
        "Jami at-Tirmidhi",
        "Muwatta Malik",
    ]
    
    print("\n" + "="*80)
    print("🔍 TEST DE MATCHING COLLECTIONS → AUTORITÉS")
    print("="*80)
    
    for collection in test_collections:
        is_auth, authority = validator.is_authorized_source(collection)
        
        print(f"\n📚 Collection: '{collection}'")
        if is_auth and authority:
            print(f"   ✅ MATCH trouvé: {authority.name_latin}")
            print(f"   📖 Œuvres: {', '.join(authority.major_works)}")
        else:
            print(f"   ❌ AUCUN MATCH")
            
            # Chercher manuellement
            print(f"\n   🔎 Recherche manuelle:")
            for key, auth in validator.authorities.items():
                if 'bukhari' in collection.lower() and 'bukhari' in key:
                    print(f"      - Clé: '{key}' → {auth.name_latin}")
                elif 'abu dawud' in collection.lower() and 'dawud' in key:
                    print(f"      - Clé: '{key}' → {auth.name_latin}")
                elif 'tirmidhi' in collection.lower() and 'tirmidhi' in key:
                    print(f"      - Clé: '{key}' → {auth.name_latin}")
                elif 'malik' in collection.lower() and 'malik' in key:
                    print(f"      - Clé: '{key}' → {auth.name_latin}")
    
    # Statistiques DB
    print("\n" + "="*80)
    print("📊 STATISTIQUES BASE DE DONNÉES")
    print("="*80)
    
    conn = sqlite3.connect("backend/almizane.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT collection, COUNT(*) as count
        FROM hadiths
        WHERE collection IN ('Sahih al-Bukhari', 'Sunan Abu Dawud', 
                            'Jami at-Tirmidhi', 'Muwatta Malik')
        GROUP BY collection
        ORDER BY count DESC
    """)
    
    total = 0
    for row in cursor.fetchall():
        collection, count = row
        is_auth, _ = validator.is_authorized_source(collection)
        status = "✅" if is_auth else "❌"
        print(f"\n{status} {collection}: {count:,} hadiths")
        if not is_auth:
            total += count
    
    conn.close()
    
    print(f"\n💡 Total hadiths non autorisés: {total:,}")
    print("\n" + "="*80)

if __name__ == "__main__":
    test_matching()