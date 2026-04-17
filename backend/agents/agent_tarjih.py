"""Agent 4 — Ijmāʿ, Khilāf, Mukhtalif, Audit, Tarjīḥ final."""

from backend.agents.base import BaseAgent

class AgentTarjih(BaseAgent):
    AGENT_NAME = "TARJIH"
    ZONES_PRODUCED = [15, 16, 17, 28, 29]

    async def _mock_output(self, hadith_data: dict) -> dict:
        return {
            "zone_15": {"type": "ijma", "ijma_detected": False, "mock": True},
            "zone_16": {"type": "khilaf", "divergences": [], "mock": True},
            "zone_17": {"type": "mukhtalif", "conflits": [], "mock": True},
            "zone_28": {"type": "audit_contemporain", "audits": [], "mock": True},
            "zone_29": {
                "type": "tarjih_final",
                "avis_rajih": "En attente du corpus réel",
                "mock": True,
            },
        }