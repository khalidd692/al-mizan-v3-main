"""Agent 'Ilal — Défauts cachés de la chaîne de transmission."""

import sqlite3
from backend.agents.base import BaseAgent
from backend.database.db import DB_PATH

class AgentIlal(BaseAgent):
    AGENT_NAME = "ILAL"
    ZONES_PRODUCED = [6, 7, 8]

    async def _mock_output(self, hadith_data: dict) -> dict:
        return {
            "zone_6": {
                "zone": 6,
                "type": "ilal_ahkam",
                "title": "أحكام العلل",
                "title_fr": "Règles des 'ilal",
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
            "zone_7": {
                "zone": 7,
                "type": "ilal_mawduu",
                "title": "علل الموضوع",
                "title_fr": "Défauts du hadith mawdū'",
                "tawaqquf": True,
                "reason": "En attente de l'implémentation complète de 'Ilal",
                "schema": {
                    "indices_mawduu": [],
                    "historique_fabrication": []
                },
                "mock": True,
            },
            "zone_8": {
                "zone": 8,
                "type": "ilal_takhrij",
                "title": "التخريج والعلل",
                "title_fr": "Takhrij et 'ilal combinés",
                "tawaqquf": True,
                "reason": "En attente de l'implémentation complète de 'Ilal",
                "schema": {
                    "sources_critiques": [],
                    "references_jarh": []
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
                    "type": "ilal_ahkam",
                    "tawaqquf": True,
                    "reason": f"Erreur de base de données lors de la récupération des défauts: {e}",
                    "schema": {},
                },
                "zone_7": {
                    "zone": 7,
                    "type": "ilal_mawduu",
                    "tawaqquf": True,
                    "reason": f"Erreur de base de données: {e}",
                    "schema": {},
                },
                "zone_8": {
                    "zone": 8,
                    "type": "ilal_takhrij",
                    "tawaqquf": True,
                    "reason": f"Erreur de base de données: {e}",
                    "schema": {},
                },
            }

        return {
            "zone_6": {
                "zone": 6,
                "type": "ilal_ahkam",
                "title": "أحكام العلل",
                "title_fr": "Règles des 'ilal",
                "tawaqquf": False,
                "reason": None,
                "schema": {
                    "defauts_chaines": defauts_chaines
                },
                "mock": False,
            },
            "zone_7": {
                "zone": 7,
                "type": "ilal_mawduu",
                "title": "علل الموضوع",
                "title_fr": "Défauts du hadith mawdū'",
                "tawaqquf": True,
                "reason": "Analyse LLM requise pour les indices de fabrication",
                "schema": {
                    "indices_mawduu": [],
                    "historique_fabrication": []
                },
                "mock": False,
            },
            "zone_8": {
                "zone": 8,
                "type": "ilal_takhrij",
                "title": "التخريج والعلل",
                "title_fr": "Takhrij et 'ilal combinés",
                "tawaqquf": True,
                "reason": "Analyse croisée requise",
                "schema": {
                    "sources_critiques": [],
                    "references_jarh": []
                },
                "mock": False,
            },
        }