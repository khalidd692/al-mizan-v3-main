"""Agent 5 — Fawāʾid (Fiqhiyyah, ʿAqadiyyah, Tarbiyyah)."""

from backend.agents.base import BaseAgent

class AgentFawaid(BaseAgent):
    AGENT_NAME = "FAWAID"
    ZONES_PRODUCED = [20, 21, 22]

    async def _mock_output(self, hadith_data: dict) -> dict:
        return {
            "zone_20": {
                "zone": 20,
                "type": "fawaid_fiqhiyyah",
                "tawaqquf": True,
                "reason": "En attente du corpus Al-Mīzān v5.0",
                "schema": [],
                "mock": True
            },
            "zone_21": {
                "zone": 21,
                "type": "fawaid_aqadiyyah",
                "tawaqquf": True,
                "reason": "En attente du corpus Al-Mīzān v5.0",
                "schema": [],
                "mock": True
            },
            "zone_22": {
                "zone": 22,
                "type": "fawaid_tarbiyyah",
                "tawaqquf": True,
                "reason": "En attente du corpus Al-Mīzān v5.0",
                "schema": [],
                "mock": True
            }
        }