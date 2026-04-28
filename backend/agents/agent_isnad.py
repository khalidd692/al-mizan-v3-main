"""Agent Isnād — Analyse de la chaîne de transmission."""

import sqlite3
from backend.agents.base import BaseAgent
from backend.database.db import DB_PATH

class AgentIsnad(BaseAgent):
    AGENT_NAME = "ISNAD"
    ZONES_PRODUCED = [2]

    async def _mock_output(self, hadith_data: dict) -> dict:
        # Sortie simulée pour la zone 2
        return {
            "zone_2": {
                "zone": 2,
                "type": "isnad",
                "tawaqquf": True,
                "reason": "En attente de l'implémentation complète de l'isnād",
                "schema": {
                    "rapporteurs": [
                        {"ordre": 1, "nom_arabe": "الراوي الأول", "nom_francais": "Rapporteur 1"},
                        {"ordre": 2, "nom_arabe": "الراوي الثاني", "nom_francais": "Rapporteur 2"},
                    ]
                },
                "mock": True,
            },
        }

    async def _real_output(self, hadith_data: dict) -> dict:
        hadith_id = hadith_data.get("hadith_id")
        if not hadith_id:
            return await self._mock_output(hadith_data)

        rapporteurs_data = []
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Récupérer l'isnad_id du hadith
            cursor.execute("SELECT isnad_id FROM hadiths WHERE id = ?", (hadith_id,))
            isnad_id = cursor.fetchone()
            if isnad_id:
                isnad_id = isnad_id[0]

                # Récupérer les rapporteurs pour cet isnad_id
                cursor.execute(
                    """
                    SELECT r.order_in_chain, a.arabic_name, a.french_name
                    FROM isnad_rawis r
                    JOIN authorities a ON r.authority_id = a.id
                    WHERE r.isnad_id = ?
                    ORDER BY r.order_in_chain ASC
                    """,
                    (isnad_id,)
                )
                for row in cursor.fetchall():
                    rapporteurs_data.append({
                        "ordre": row[0],
                        "nom_arabe": row[1],
                        "nom_francais": row[2],
                    })
            conn.close()
        except sqlite3.Error as e:
            print(f"Erreur SQLite: {e}")
            return {
                "zone_2": {
                    "zone": 2,
                    "type": "isnad",
                    "tawaqquf": True,
                    "reason": f"Erreur de base de données lors de la récupération de l'isnād: {e}",
                    "schema": {},
                },
            }

        return {
            "zone_2": {
                "zone": 2,
                "type": "isnad",
                "tawaqquf": False,
                "reason": None,
                "schema": {
                    "rapporteurs": rapporteurs_data
                },
                "mock": False,
            },
        }