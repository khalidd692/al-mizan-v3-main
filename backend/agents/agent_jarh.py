"""Agent Jarh wa Ta'dīl — Jugements sur les rapporteurs."""

import sqlite3
from backend.agents.base import BaseAgent
from backend.database.db import DB_PATH

class AgentJarh(BaseAgent):
    AGENT_NAME = "JARH"
    ZONES_PRODUCED = [3]

    async def _mock_output(self, hadith_data: dict) -> dict:
        return {
            "zone_3": {
                "zone": 3,
                "type": "jarh_taadil",
                "tawaqquf": True,
                "reason": "En attente de l'implémentation complète de Jarh wa Ta'dīl",
                "schema": {
                    "rapporteurs_jugements": [
                        {"nom_arabe": "الراوي الأول", "jugement": "ثقة", "source": "Mock Source"},
                        {"nom_arabe": "الراوي الثاني", "jugement": "ضعيف", "source": "Mock Source"},
                    ]
                },
                "mock": True,
            },
        }

    async def _real_output(self, hadith_data: dict) -> dict:
        hadith_id = hadith_data.get("hadith_id")
        if not hadith_id:
            return await self._mock_output(hadith_data)

        rapporteurs_jugements = []
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute("SELECT isnad_id FROM hadiths WHERE id = ?", (hadith_id,))
            isnad_id = cursor.fetchone()
            if isnad_id:
                isnad_id = isnad_id[0]

                cursor.execute(
                    """
                    SELECT a.arabic_name, aj.judgment, aj.source
                    FROM isnad_rawis ir
                    JOIN authorities a ON ir.authority_id = a.id
                    LEFT JOIN authority_judgments aj ON a.id = aj.authority_id
                    WHERE ir.isnad_id = ?
                    ORDER BY ir.order_in_chain ASC
                    """,
                    (isnad_id,)
                )
                for row in cursor.fetchall():
                    rapporteurs_jugements.append({
                        "nom_arabe": row[0],
                        "jugement": row[1],
                        "source": row[2],
                    })
            conn.close()
        except sqlite3.Error as e:
            print(f"Erreur SQLite: {e}")
            return {
                "zone_3": {
                    "zone": 3,
                    "type": "jarh_taadil",
                    "tawaqquf": True,
                    "reason": f"Erreur de base de données lors de la récupération des jugements: {e}",
                    "schema": {},
                },
            }

        return {
            "zone_3": {
                "zone": 3,
                "type": "jarh_taadil",
                "tawaqquf": False,
                "reason": None,
                "schema": {
                    "rapporteurs_jugements": rapporteurs_jugements
                },
                "mock": False,
            },
        }