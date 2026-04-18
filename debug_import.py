#!/usr/bin/env python3
"""
Debug Import - Voir les erreurs réelles
"""

import requests
import sqlite3
from datetime import datetime

def test_single_hadith():
    """Test import d'un seul hadith avec détails complets"""
    
    print("=" * 60)
    print("🔍 DEBUG IMPORT HADITH")
    print("=" * 60)
    
    # Test API
    print("\n1️⃣ Test API...")
    try:
        resp = requests.get("https://api.hadith.gading.dev/books/bukhari/1", timeout=10)
        print(f"   Status: {resp.status_code}")
        
        data = resp.json()
        print(f"   Code: {data.get('code')}")
        print(f"   Message: {data.get('message', 'N/A')}")
        
        if data.get('code') == 200:
            hadith = data.get('data', {})
            print(f"\n   📖 Hadith reçu:")
            print(f"      - ID: {hadith.get('id')}")
            print(f"      - Number: {hadith.get('number')}")
            print(f"      - Arab: {hadith.get('arab', '')[:50]}...")
            print(f"      - Indonesian: {hadith.get('id', '')[:50]}...")
    except Exception as e:
        print(f"   ❌ Erreur API: {e}")
        return
    
    # Test DB
    print("\n2️⃣ Test connexion DB...")
    try:
        conn = sqlite3.connect("backend/almizane.db")
        cursor = conn.cursor()
        
        # Vérifier schéma
        cursor.execute("PRAGMA table_info(hadiths)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"   Colonnes disponibles: {columns}")
        
        # Test doublon
        print("\n3️⃣ Test vérification doublon...")
        cursor.execute(
            "SELECT 1 FROM hadiths WHERE source_api = ? AND collection = ? AND numero_hadith = ? LIMIT 1",
            ("hadith_gading", "bukhari", "1")
        )
        exists = cursor.fetchone()
        print(f"   Hadith existe déjà: {exists is not None}")
        
        if not exists:
            # Test insertion
            print("\n4️⃣ Test insertion...")
            try:
                cursor.execute("""
                    INSERT INTO hadiths (
                        matn_ar, matn_fr, source_api, collection,
                        numero_hadith, inserted_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    hadith.get('arab', ''),
                    hadith.get('id', ''),
                    "hadith_gading",
                    "bukhari",
                    "1",
                    datetime.now().isoformat()
                ))
                conn.commit()
                print("   ✅ Insertion réussie!")
                
                # Vérifier
                cursor.execute(
                    "SELECT id, collection, numero_hadith FROM hadiths WHERE source_api = 'hadith_gading' AND collection = 'bukhari' AND numero_hadith = '1'"
                )
                result = cursor.fetchone()
                print(f"   Vérifié: ID={result[0]}, Collection={result[1]}, Numéro={result[2]}")
                
            except Exception as e:
                print(f"   ❌ Erreur insertion: {e}")
                print(f"   Type: {type(e).__name__}")
                import traceback
                traceback.print_exc()
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Erreur DB: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_single_hadith()