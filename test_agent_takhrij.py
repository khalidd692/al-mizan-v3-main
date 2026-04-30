#!/usr/bin/env python3
"""Test rapide de l'agent Takhrij"""

from api.agent_takhrij import analyze
import json

result = analyze('1')

print('=== AGENT TAKHRIJ — RÉSULTAT ===')
print(json.dumps(result, ensure_ascii=False, indent=2))

print('\n=== RÉSUMÉ ===')
print(f"Zones remplies: {len(result['_meta']['zones_remplies'])}")
print(f"Zones vides: {len(result['_meta']['zones_vides'])}")
print(f"Source grade: {result['_meta'].get('grade_source', 'N/A')}")

# Vérification structure
if result.get('zone_02') and result['zone_02'].get('grade'):
    print(f"\n✅ Zone 02: Grade trouvé = {result['zone_02']['grade']}")
else:
    print("\n⚠️ Zone 02: Pas de grade")
