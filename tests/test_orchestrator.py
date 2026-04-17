"""Tests de l'orchestrateur — Phase 1 mock."""

import pytest
from backend.orchestrator import Orchestrator

@pytest.mark.asyncio
async def test_orchestrator_mock_pipeline():
    """Vérifie que le pipeline mock produit les 32 zones."""
    orch = Orchestrator(api_key="mock")
    zones_received = []
    
    async for chunk in orch.process("test hadith"):
        if chunk.startswith("event:"):
            event_name = chunk.split("\n")[0].replace("event:", "").strip()
            zones_received.append(event_name)
    
    # Filtrer les events meta_pipeline_* qui ne sont pas des zones
    zones_only = [z for z in zones_received if z.startswith("zone_")]
    
    # Vérifier que les 32 zones sont émises
    expected_zones = [f"zone_{i}" for i in range(1, 33)]
    for zone in expected_zones:
        assert zone in zones_only, f"Zone manquante: {zone}"
    
    # Vérifier le nombre total
    assert len(zones_only) == 32, f"Attendu 32 zones, reçu {len(zones_only)}"
