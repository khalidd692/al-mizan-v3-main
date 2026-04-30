#!/usr/bin/env python3
"""Test local des fonctions de recherche FTS5."""

import sys
sys.path.insert(0, '.')

from backend.utils.local_db import search_hadith, row_to_hadith_core

def test_search(query, expected_min=0):
    """Test une recherche et affiche les résultats."""
    print(f"\n{'='*60}")
    print(f"🔍 Test: '{query}'")
    print('='*60)
    
    results = search_hadith(query, limit=3)
    
    if not results:
        print(f"  ⚠️  Aucun résultat")
        if expected_min > 0:
            print(f"  ❌ FAIL: Attendu au moins {expected_min} résultats")
            return False
        return True
    
    print(f"  ✅ {len(results)} résultat(s) trouvé(s)")
    
    for i, row in enumerate(results[:2], 1):
        hadith_data = row_to_hadith_core(row)
        
        # Vérification des champs mappés
        grade = hadith_data.get('grade_raw', 'MISSING')
        source = hadith_data.get('source', 'MISSING')
        matn = hadith_data.get('matn', '')[:60]
        translation = hadith_data.get('translation_fr', '')[:60]
        
        print(f"\n  [{i}] grade_raw={grade}")
        print(f"      source={source}")
        print(f"      matn={matn}...")
        print(f"      translation={translation}...")
        
        # Vérification que grade_primary est bien mappé
        if grade == 'MISSING' or not grade:
            print(f"  ⚠️  WARNING: grade_raw non mappé (grade_primary={row.get('grade_primary')})")
    
    return True

print("\n" + "="*60)
print("TEST LOCAL FTS5 - Al-Mīzān")
print("="*60)

# Tests de recherche
tests = [
    ('jeûne', 1),
    ('patience', 1),
    ('prière', 1),
    ('ramadan', 1),
    ('xyzabc123', 0),  # Doit retourner vide
]

all_passed = True
for query, expected in tests:
    if not test_search(query, expected):
        all_passed = False

print("\n" + "="*60)
if all_passed:
    print("✅ TOUS LES TESTS PASSÉS")
else:
    print("❌ CERTAINS TESTS ÉCHOUÉS")
print("="*60)

sys.exit(0 if all_passed else 1)
