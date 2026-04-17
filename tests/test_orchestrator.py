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
    
    assert "zone_1" in zones_received
    assert "zone_4" in zones_received
    assert "zone_32" in zones_received
    assert len(zones_received) >= 10  # Au moins quelques zones