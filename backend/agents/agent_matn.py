"""Agent 3 — Matn, Gharīb, Sabab, Āthār des Salaf."""

from backend.agents.base import BaseAgent

class AgentMatn(BaseAgent):
    AGENT_NAME = "MATN"
    ZONES_PRODUCED = [9, 10, 11, 12, 13, 14]

    async def _mock_output(self, hadith_data: dict) -> dict:
        return {
            "zone_9": {"type": "gharib", "words": [], "mock": True},
            "zone_10": {"type": "sabab_wurud", "circonstance": "Non documentée dans le corpus mock", "mock": True},
            "zone_11": {
                "zone": 11,
                "type": "shuruh",
                "tawaqquf": True,
                "reason": "En attente du corpus Al-Mīzān v5.0",
                "schema": {
                    "commentaires": [],
                    "fath_al_bari": None,
                    "sharh_muslim": None
                },
                "mock": True
            },
            "zone_12": {"type": "athar_sahabah", "athar": [], "mock": True},
            "zone_13": {"type": "athar_tabiin", "athar": [], "mock": True},
            "zone_14": {"type": "positions_imams", "positions": [], "mock": True},
        }
