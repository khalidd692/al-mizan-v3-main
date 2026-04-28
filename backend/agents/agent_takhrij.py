"""Agent Takhrîj — Attribution et recensement des sources."""

from backend.agents.base import BaseAgent


class AgentTakhrij(BaseAgent):
    AGENT_NAME = "TAKHRIJ"
    ZONES_PRODUCED = [4]

    async def _mock_output(self, hadith_data: dict) -> dict:
        source = hadith_data.get("source", "")
        return {
            "zone_4": {
                "zone": 4,
                "type": "takhrij",
                "tawaqquf": True,
                "reason": "En attente du corpus Al-Mīzān v5.0",
                "schema": {
                    "source_principale": source,
                    "sources_secondaires": [],
                    "takhrijat": [],
                },
                "mock": True,
            },
        }
