"""Agent Shurut as-Sihhah — Vérification des conditions d'authenticité."""

import sqlite3
from backend.agents.base import BaseAgent
from backend.database.db import DB_PATH

class AgentConditions(BaseAgent):
    AGENT_NAME = "CONDITIONS"
    ZONES_PRODUCED = [5]

    async def _mock_output(self, hadith_data: dict) -> dict:
        return {
            "zone_5": {
                "zone": 5,
                "type": "shurut_sihhah",
                "tawaqquf": True,
                "reason": "En attente de l'implémentation complète des conditions d'authenticité",
                "schema": {
                    "conditions_verifiees": [
                        {"condition": "Connexion de la chaîne", "statut": "Inconnu", "details": "Mock details"},
                        {"condition": "Fiabilité des rapporteurs", "statut": "Inconnu", "details": "Mock details"},
                    ]
                },
                "mock": True,
            },
        }

    async def _real_output(self, hadith_data: dict) -> dict:
        hadith_id = hadith_data.get("hadith_id")
        if not hadith_id:
            return await self._mock_output(hadith_data)

        conditions_verifiees = []
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Ceci est un exemple. Le schéma de la DB doit inclure une table pour les conditions.
            # Supposons une table 'hadith_conditions' avec hadith_id, condition_name, status, details
            cursor.execute(
                """
                SELECT condition_name, status, details
                FROM hadith_conditions
                WHERE hadith_id = ?
                """,
                (hadith_id,)
            )
            for row in cursor.fetchall():
                conditions_verifiees.append({
                    "condition": row[0],
                    "statut": row[1],
                    "details": row[2],
                })
            conn.close()
        except sqlite3.Error as e:
            print(f"Erreur SQLite: {e}")
            return {
                "zone_5": {
                    "zone": 5,
                    "type": "shurut_sihhah",
                    "tawaqquf": True,
                    "reason": f"Erreur de base de données lors de la récupération des conditions: {e}",
                    "schema": {},
                },
            }

        return {
            "zone_5": {
                "zone": 5,
                "type": "shurut_sihhah",
                "tawaqquf": False,
                "reason": None,
                "schema": {
                    "conditions_verifiees": conditions_verifiees
                },
                "mock": False,
            },
        }