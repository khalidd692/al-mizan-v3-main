"""Agent Takhrij — Recherche des mutābaʿāt et shawāhid (Zones 04-05)."""

import json
from backend.agents.base import BaseAgent


class AgentTakhrij(BaseAgent):
    """
    Agent spécialisé dans la recherche de:
    - Zone 04: Mutābaʿāt (parallèles de chaînes de transmission)
    - Zone 05: Shawāhid (témoins / corroborations thématiques)
    
    Sources: Muʿjam aṭ-Ṭabarānī, Musnad Aḥmad, etc.
    """
    AGENT_NAME = "TAKHRIJ"
    ZONES_PRODUCED = [4, 5]

    async def _mock_output(self, hadith_data: dict) -> dict:
        """Mode démo avec données simulées de mutābaʿāt et shawāhid."""
        return {
            "zone_4": {
                "zone": 4,
                "type": "mutabaat",
                "title": "المتابعات",
                "title_fr": "Mutābaʿāt (parallèles de chaînes)",
                "note": "Recherche de parallèles complets et partiels dans les corpus de hadiths",
                "tawaqquf": True,
                "reason": "Corpus takhrij en cours d'intégration",
                "count": 0,
                "items": [],
                "schema": {
                    "mutabaat_tamma": [],  # Parallèles complets
                    "mutabaat_qasira": [],  # Parallèles partiels
                },
                "mock": True
            },
            "zone_5": {
                "zone": 5,
                "type": "shawahid",
                "title": "الشواهد",
                "title_fr": "Shawāhid (témoins thématiques)",
                "note": "Recherche de témoignages corroborants par thème",
                "tawaqquf": True,
                "reason": "Corpus takhrij en cours d'intégration",
                "count": 0,
                "items": [],
                "schema": {
                    "shawahid_sahaba": [],  # Témoins de Compagnons
                    "shawahid_tabiin": [],  # Témoins de Successeurs
                },
                "mock": True
            }
        }

    async def _real_output(self, hadith_data: dict) -> dict:
        """
        Mode réel: recherche dans corpus.db des mutābaʿāt et shawāhid.
        
        À implémenter: connexion à corpus.db et recherche FTS5
        """
        # TODO: Implémenter la recherche réelle dans corpus.db
        return await self._mock_output(hadith_data)
