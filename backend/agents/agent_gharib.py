"""Agent Gharib al-Hadith — Termes rares ou techniques dans le matn."""

import sqlite3
import re
from backend.agents.base import BaseAgent
from backend.database.db_manager import get_db
import os
DB_TEST_PATH = "backend/database/almizan_test.db"

class AgentGharib(BaseAgent):
    AGENT_NAME = "GHARIB"
    ZONES_PRODUCED = [9]

    async def get_hadith_and_grade(self, hadith_id: str) -> tuple[str, str] | None:
        conn = None
        try:
            conn = sqlite3.connect(DB_TEST_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT fr_text, grade_primary FROM entries WHERE id = ?", (hadith_id,)
            )
            result = cursor.fetchone()
            if result:
                return result[0], result[1]
            return None
        except sqlite3.Error as e:
            print(f"Erreur SQLite lors de la récupération du hadith {hadith_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    async def _mock_output(self, hadith_data: dict) -> dict:
        return {
            "zone_9": {
                "zone": 9,
                "type": "gharib_hadith",
                "tawaqquf": True,
                "reason": "En attente de l'implémentation complète de Gharib al-Hadith",
                "schema": {
                    "termes_gharib": [
                        {"terme": "الكلمة الأولى", "definition": "Définition mock 1", "source": "Mock Source"},
                        {"terme": "الكلمة الثانية", "definition": "Définition mock 2", "source": "Mock Source"},
                    ]
                },
                "mock": True,
            },
        }

    async def _real_output(self, hadith_data: dict) -> dict:
        hadith_id = hadith_data.get("hadith_id")
        if not hadith_id:
            return await self._mock_output(hadith_data)

        fr_text, grade_primary = await self.get_hadith_and_grade(hadith_id)
        
        if not fr_text:
            return {
                "zone_9": {
                    "zone": 9,
                    "type": "gharib_hadith",
                    "tawaqquf": True,
                    "reason": f"Hadith avec ID {hadith_id} non trouvé.",
                    "schema": {},
                    "mock": False,
                },
            }

        # Logique de détection des termes gharib (simplifiée pour l'exemple)
        termes_gharib_detectes = []
        tawaqquf_status = False

        # Liste de mots clés "gharib" à détecter (à étendre avec une vraie base de données de termes gharib)
        gharib_keywords = {
            "\u0627\u0644\u0635\u064a\u0646": "La Chine, mention géographique spécifique.",
            "\u0627\u0644\u0646\u064a\u0627\u062a": "Les intentions, concept fondamental en Islam.",
            "\u0627\u0644\u0623\u0645\u0647\u0627\u062a": "Les mères, terme clé dans ce hadith.",
            "\u0635\u062f\u0642\u0629": "Aumône, concept religieux.",
            "\u0627\u0644\u0622\u062e\u0631": "L'Au-delà, concept eschatologique.",
            "\u0646\u0648\u0631": "Lumière, souvent utilisé métaphoriquement.",
            "\u0641\u0631\u064a\u0636\u0629": "Obligation religieuse.",
            "\u0627\u0644\u062c\u0646\u0629": "Le Paradis, concept eschatologique.",
            "\u064a\u062a\u0642\u0646\u0647": "Le perfectionner, faire avec excellence.",
            "\u0627\u0644\u0642\u0631\u0622\u0646": "Le Coran, livre sacré de l'Islam.",
            "\u0627\u0644\u0642\u064a\u0627\u0645\u0629": "Le Jour du Jugement, concept eschatologique.",
            "\u0627\u0644\u062d\u0643\u0645\u0629": "La sagesse, concept important.",
            "\u0627\u0644\u062a\u062c\u0631\u0628\u0629": "L'expérience, concept lié à la sagesse.",
        }

        # Utiliser le matn_arabic pour la détection si disponible, sinon fr_text
        text_to_analyze = hadith_data.get("matn_arabic", fr_text)

        if text_to_analyze:
            for terme, definition in gharib_keywords.items():
                # Utiliser re.search pour une détection plus flexible (mots entiers)
                if re.search(r'\b' + re.escape(terme) + r'\b', text_to_analyze):
                    termes_gharib_detectes.append({"terme": terme, "definition": definition, "source": "Détection simple par mot-clé"})
            
            if termes_gharib_detectes:
                tawaqquf_status = True

        return {
            "zone_9": {
                "zone": 9,
                "type": "gharib_hadith",
                "tawaqquf": tawaqquf_status,
                "reason": "Analyse des termes gharib effectuée.",
                "schema": {
                    "hadith_fr_text": fr_text,
                    "grade_primary": grade_primary,
                    "termes_gharib": termes_gharib_detectes,
                },
                "mock": False,
            },
        }
