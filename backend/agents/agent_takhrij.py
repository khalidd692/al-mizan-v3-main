"""Agent Takhrīj — Recherche et identification des sources du hadith."""

import sqlite3
from backend.agents.base import BaseAgent
from backend.database.db import DB_PATH


class AgentTakhrij(BaseAgent):
    """Agent responsable du takhrīj (recherche des sources et références)."""

    AGENT_NAME = "TAKHRIJ"
    ZONES_PRODUCED = [30, 31, 32]

    async def _mock_output(self, hadith_data: dict) -> dict:
        """Mode démo : retourne des données simulées pour les zones 30-32."""
        return {
            "zone_30": {
                "zone": 30,
                "type": "takhrij_mawsuu",
                "title": "التخريج الموسع",
                "title_fr": "Takhrij étendu",
                "tawaqquf": True,
                "reason": "En attente du corpus Al-Mīzān v5.0",
                "schema": {
                    "sources_primaires": [],
                    "recensions": [],
                    "versions_paralleles": []
                },
                "mock": True
            },
            "zone_31": {
                "zone": 31,
                "type": "takhrij_ahkam",
                "title": "أحكام التخريج",
                "title_fr": "Règles de takhrīj",
                "tawaqquf": True,
                "reason": "En attente du corpus Al-Mīzān v5.0",
                "schema": {
                    "regles_appliquees": [],
                    "differences_recensions": []
                },
                "mock": True
            },
            "zone_32": {
                "zone": 32,
                "type": "takhrij_tarjama",
                "title": "تراجم الرجال في التخريج",
                "title_fr": "Biographies des narrateurs",
                "tawaqquf": True,
                "reason": "En attente du corpus Al-Mīzān v5.0",
                "schema": {
                    "narrateurs_identifies": [],
                    "biographies_relevantes": []
                },
                "mock": True
            }
        }

    async def _real_output(self, hadith_data: dict) -> dict:
        """Mode réel : recherche les sources depuis la base locale."""
        hadith_id = hadith_data.get("hadith_id")
        if not hadith_id:
            return await self._mock_output(hadith_data)

        sources_primaires = []
        narrateurs_identifies = []

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Récupérer les sources associées au hadith
            cursor.execute(
                """
                SELECT source_book, source_reference, source_grade
                FROM hadith_sources
                WHERE hadith_id = ?
                """,
                (hadith_id,)
            )
            for row in cursor.fetchall():
                sources_primaires.append({
                    "livre": row[0],
                    "reference": row[1],
                    "grade": row[2]
                })

            # Récupérer les narrateurs de la chaîne pour identification
            cursor.execute(
                """
                SELECT a.arabic_name, a.french_name, a.nisba, a.grade
                FROM isnad_rawis r
                JOIN authorities a ON r.authority_id = a.id
                JOIN hadiths h ON r.isnad_id = h.isnad_id
                WHERE h.id = ?
                ORDER BY r.order_in_chain ASC
                """,
                (hadith_id,)
            )
            for row in cursor.fetchall():
                narrateurs_identifies.append({
                    "nom_arabe": row[0],
                    "nom_francais": row[1],
                    "nisba": row[2],
                    "grade": row[3]
                })

            conn.close()
        except sqlite3.Error as e:
            return {
                "zone_30": {
                    "zone": 30,
                    "type": "takhrij_mawsuu",
                    "tawaqquf": True,
                    "reason": f"Erreur base de données: {e}",
                    "schema": {}
                },
                "zone_31": {
                    "zone": 31,
                    "type": "takhrij_ahkam",
                    "tawaqquf": True,
                    "reason": f"Erreur base de données: {e}",
                    "schema": {}
                },
                "zone_32": {
                    "zone": 32,
                    "type": "takhrij_tarjama",
                    "tawaqquf": True,
                    "reason": f"Erreur base de données: {e}",
                    "schema": {}
                }
            }

        return {
            "zone_30": {
                "zone": 30,
                "type": "takhrij_mawsuu",
                "title": "التخريج الموسع",
                "title_fr": "Takhrij étendu",
                "tawaqquf": len(sources_primaires) == 0,
                "reason": None if sources_primaires else "Aucune source trouvée",
                "schema": {
                    "sources_primaires": sources_primaires,
                    "recensions": [],
                    "versions_paralleles": []
                },
                "mock": False
            },
            "zone_31": {
                "zone": 31,
                "type": "takhrij_ahkam",
                "title": "أحكام التخريج",
                "title_fr": "Règles de takhrīj",
                "tawaqquf": True,
                "reason": "Analyse LLM requise pour les règles de takhrīj",
                "schema": {
                    "regles_appliquees": [],
                    "differences_recensions": []
                },
                "mock": False
            },
            "zone_32": {
                "zone": 32,
                "type": "takhrij_tarjama",
                "title": "تراجم الرجال في التخريج",
                "title_fr": "Biographies des narrateurs",
                "tawaqquf": len(narrateurs_identifies) == 0,
                "reason": None if narrateurs_identifies else "Aucun narrateur identifié",
                "schema": {
                    "narrateurs_identifies": narrateurs_identifies,
                    "biographies_relevantes": []
                },
                "mock": False
            }
        }
