#!/usr/bin/env python3
"""Test du flux SSE pour la recherche."""

import sys
import json
sys.path.insert(0, '.')

from backend.utils.local_db import search_hadith, row_to_hadith_core

def sse_event(event, data):
    """Formate un événement SSE."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

def simulate_search_stream(query):
    """Simule le flux SSE de recherche."""
    print(f"\n{'='*60}")
    print(f"🔍 Simulation SSE pour: '{query}'")
    print('='*60)
    
    # Étape 1: Initialisation
    yield sse_event("status", {"step": "INITIALISATION", "message": "Recherche locale FTS5"})
    
    # Étape 2: Recherche
    db_results = search_hadith(query, limit=10)
    
    if not db_results:
        yield sse_event("error", {"message": "Aucun hadith trouvé pour cette recherche."})
        yield sse_event("done", {"total": 0})
        return
    
    print(f"  📊 {len(db_results)} résultats trouvés")
    
    # Étape 3: Résultats
    for i, row in enumerate(db_results[:3], 1):  # Limite à 3 pour l'affichage
        hadith_data = row_to_hadith_core(row)
        
        # Vérifier le mapping
        print(f"\n  [{i}] Mapping vérifié:")
        print(f"      - grade_raw: {hadith_data.get('grade_raw')}")
        print(f"      - source: {hadith_data.get('source')}")
        print(f"      - matn présent: {'Oui' if hadith_data.get('matn') else 'Non'}")
        print(f"      - translation_fr présente: {'Oui' if hadith_data.get('translation_fr') else 'Non'}")
        
        yield sse_event("zone_3", {
            "zone": 3,
            "type": "hadith_core",
            "data": hadith_data,
            "source": "local_db",
        })
    
    yield sse_event("done", {"total": len(db_results), "source": "local_db"})

# Test
print("\n" + "="*60)
print("TEST SSE SIMULATION")
print("="*60)

for chunk in simulate_search_stream('jeûne'):
    # Affiche juste les événements (pas les data complètes pour la lisibilité)
    if 'zone_3' in chunk:
        print(f"\n  📤 SSE: event=zone_3 (hadith_core)")
    elif 'done' in chunk:
        print(f"\n  📤 SSE: event=done")
    elif 'error' in chunk:
        print(f"\n  📤 SSE: event=error")
    else:
        print(f"\n  📤 SSE: {chunk[:100]}...")

print("\n" + "="*60)
print("✅ TEST SSE PASSÉ")
print("="*60)
