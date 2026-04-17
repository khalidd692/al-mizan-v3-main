#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test d'initialisation de la base de données"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database import get_db

def test_init():
    print("=== TEST INITIALISATION BASE DE DONNÉES ===\n")
    
    try:
        # Initialiser la base
        db = get_db()
        print("✅ Base de données initialisée")
        
        # Vérifier les zones
        zones = db.get_all_zones()
        print(f"✅ {len(zones)} zones chargées")
        
        # Afficher quelques zones
        print("\nPremières zones:")
        for zone in zones[:5]:
            print(f"  {zone['id']}. {zone['name']} ({zone['name_ar']}) - {zone['category']}")
        
        # Rapport de couverture
        stats = db.get_coverage_report()
        print(f"\n📊 Statistiques:")
        print(f"  Total entrées: {stats['total_entries']}")
        print(f"  Zones couvertes: {stats['zones_covered']}/{stats['zones_total']}")
        print(f"  Couverture: {stats['coverage_percent']}%")
        print(f"  Confiance moyenne: {stats['avg_confidence']}")
        
        print("\n✅ TOUS LES TESTS PASSÉS")
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_init()
    sys.exit(0 if success else 1)