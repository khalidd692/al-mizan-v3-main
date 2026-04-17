"""Agent 2 — ʿIlal, Tafarrud, Munkar."""

from backend.agents.base import BaseAgent

class AgentIlal(BaseAgent):
    AGENT_NAME = "ILAL"
    ZONES_PRODUCED = [6, 7, 8]

    async def _mock_output(self, hadith_data: dict) -> dict:
        return {
            "zone_6": {
                "type": "ilal",
                "illal_signalees": [],
                "conclusion": "Aucune ʿillah signalée dans le corpus Al-Mīzān",
                "mock": True,
            },
            "zone_7": {"type": "tafarrud", "est_isole": False, "mock": True},
            "zone_8": {"type": "munkar", "est_munkar": False, "mock": True},
        }