"""Agent 1 — Chaîne d'Isnād et Jarḥ wa Taʿdīl."""

from backend.agents.base import BaseAgent

class AgentIsnad(BaseAgent):
    AGENT_NAME = "ISNAD"
    ZONES_PRODUCED = [2, 3]

    async def _mock_output(self, hadith_data: dict) -> dict:
        return {
            "zone_2": {
                "type": "isnad_chain",
                "chain": [
                    {"name_ar": "محمد بن إسماعيل البخاري", "name_fr": "Al-Bukhārī", "verdict": "imam", "tabaqa": 11, "death_h": 256},
                    {"name_ar": "عبد الله بن يوسف", "name_fr": "ʿAbd Allāh b. Yūsuf", "verdict": "thiqah", "tabaqa": 10, "death_h": 218},
                    {"name_ar": "مالك بن أنس", "name_fr": "Mālik b. Anas", "verdict": "imam", "tabaqa": 7, "death_h": 179},
                    {"name_ar": "يحيى بن سعيد الأنصاري", "name_fr": "Yaḥyā b. Saʿīd al-Anṣārī", "verdict": "thiqah", "tabaqa": 5, "death_h": 143},
                    {"name_ar": "محمد بن إبراهيم التيمي", "name_fr": "Muḥammad b. Ibrāhīm al-Taymī", "verdict": "thiqah", "tabaqa": 4, "death_h": 120},
                    {"name_ar": "علقمة بن وقاص الليثي", "name_fr": "ʿAlqamah b. Waqqāṣ al-Laythī", "verdict": "thiqah", "tabaqa": 2, "death_h": 80},
                    {"name_ar": "عمر بن الخطاب", "name_fr": "ʿUmar b. al-Khaṭṭāb", "verdict": "sahabi", "tabaqa": 1, "death_h": 23},
                ],
                "ittisal": True,
                "mock": True,
            },
            "zone_3": {
                "type": "jarh_tadil",
                "mock": True,
                "note": "Les vraies citations du corpus arriveront phase 2",
            }
        }