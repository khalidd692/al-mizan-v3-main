"""Agent 'Ilal — Défauts cachés de la chaîne de transmission."""

import sqlite3
from backend.agents.base import BaseAgent
from backend.database.db import DB_PATH

class AgentIlal(BaseAgent):
    AGENT_NAME = "ILAL"
    ZONES_PRODUCED = [6]

    async def _mock_output(self, hadith_data: dict) -> dict:
        return {
            "zone_6": {
                "zone": 6,
                "type": "ilal",
                "tawaqquf": True,
                "reason": "En attente de l'implémentation complète de 'Ilal",
                "schema": {
                    "defauts_chaines": [
                        {"type": "inqita", "description": "Interruption dans la chaîne", "details": "Mock details"},
                        {"type": "tadlis", "description": "Dissimulation", "details": "Mock details"},
                    ]
                },
                "mock": True,
            },
        }

    async def _real_output(self, hadith_data: dict) -> dict:
        hadith_id = hadith_data.get("hadith_id")
        if not hadith_id:
            return await self._mock_output(hadith_data)

        defauts_chaines = []
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute("SELECT isnad_id FROM hadiths WHERE id = ?", (hadith_id,))
            isnad_id = cursor.fetchone()
            if isnad_id:
                isnad_id = isnad_id[0]

                # Exemple de récupération de défauts (à adapter selon le schéma de la DB)
                cursor.execute(
                    """
                    SELECT type, description, details
                    FROM isnad_defects
                    WHERE isnad_id = ?
                    """,
                    (isnad_id,)
                )
                for row in cursor.fetchall():
                    defauts_chaines.append({
                        "type": row[0],
                        "description": row[1],
                        "details": row[2],
                    })
            conn.close()
        except sqlite3.Error as e:
            print(f"Erreur SQLite: {e}")
            return {
                "zone_6": {
                    "zone": 6,
                    "type": "ilal",
                    "tawaqquf": True,
                    "reason": f"Erreur de base de données lors de la récupération des défauts: {e}",
                    "schema": {},
                },
            }

        return {
            "zone_6": {
                "zone": 6,
                "type": "ilal",
                "tawaqquf": False,
                "reason": None,
                "schema": {
                    "defauts_chaines": defauts_chaines
                },
                "mock": False,
            },
        }