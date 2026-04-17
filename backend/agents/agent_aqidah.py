"""Agent 6 — ʿAqīdah (Mawḍūʿ, Attributs, Ẓāhir, Corroboration, Khulafāʾ)."""

from backend.agents.base import BaseAgent

class AgentAqidah(BaseAgent):
    AGENT_NAME = "AQIDAH"
    ZONES_PRODUCED = [23, 24, 25, 26, 27]

    async def _mock_output(self, hadith_data: dict) -> dict:
        return {
            "zone_23": {
                "zone": 23,
                "type": "mawduu_alerte",
                "tawaqquf": True,
                "reason": "En attente du corpus Al-Mīzān v5.0",
                "schema": {
                    "est_mawduu": None,
                    "est_daif_jiddan": None,
                    "fabricateur_identifie": None,
                    "sources": []
                },
                "mock": True
            },
            "zone_24": {
                "zone": 24,
                "type": "aqidah_attribut",
                "tawaqquf": True,
                "reason": "En attente du corpus Al-Mīzān v5.0",
                "schema": {
                    "concerne_attribut_divin": None,
                    "attribut": None,
                    "traduction_lexique_fer": None
                },
                "mock": True
            },
            "zone_25": {
                "zone": 25,
                "type": "dhahir_muqtada",
                "tawaqquf": True,
                "reason": "En attente du corpus Al-Mīzān v5.0",
                "schema": {
                    "sens_litteral_obligatoire": None,
                    "tawil_admis": None
                },
                "mock": True
            },
            "zone_26": {
                "zone": 26,
                "type": "corroboration_coranique",
                "tawaqquf": True,
                "reason": "En attente du corpus Al-Mīzān v5.0",
                "schema": [],
                "mock": True
            },
            "zone_27": {
                "zone": 27,
                "type": "khulafa_rashidun",
                "tawaqquf": True,
                "reason": "En attente du corpus Al-Mīzān v5.0",
                "schema": [],
                "mock": True
            }
        }