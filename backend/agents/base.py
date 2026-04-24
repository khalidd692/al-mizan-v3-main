"""Classe abstraite commune aux 8 agents."""

import asyncio
from abc import ABC, abstractmethod
from backend.utils.sse import emit
from backend.utils.logging import get_logger

log = get_logger("mizan.agents")


class BaseAgent(ABC):
    AGENT_NAME: str = ""
    ZONES_PRODUCED: list[int] = []
    MOCK_MODE: bool = True

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.MOCK_MODE = True  # sera écrasé par l'orchestrateur après __init__

    @abstractmethod
    async def _mock_output(self, hadith_data: dict) -> dict:
        pass

    async def _real_output(self, hadith_data: dict) -> dict:
        """Mode réel : utilise _mock_output comme base et enrichit avec les données DB.

        Chaque agent spécialisé peut surcharger cette méthode pour appeler une API.
        """
        output = await self._mock_output(hadith_data)
        source_label = "local_db" if hadith_data.get("from_local_db") else "live"
        hadith_id = hadith_data.get("hadith_id", "")
        for zone_data in output.values():
            if isinstance(zone_data, dict):
                zone_data.pop("mock", None)
                zone_data["source"] = source_label
                if hadith_id:
                    zone_data["hadith_id"] = hadith_id
        return output

    async def run(self, hadith_data: dict, queue: asyncio.Queue):
        """Point d'entrée appelé par l'orchestrateur."""
        try:
            output = (
                await self._mock_output(hadith_data)
                if self.MOCK_MODE
                else await self._real_output(hadith_data)
            )
            for zone_num in self.ZONES_PRODUCED:
                zone_data = output.get(f"zone_{zone_num}", {"tawaqquf": True})
                await queue.put(emit(f"zone_{zone_num}", zone_data))
                await asyncio.sleep(0.3)

        except Exception as e:
            log.exception(f"[{self.AGENT_NAME}] Erreur")
            for zone_num in self.ZONES_PRODUCED:
                await queue.put(emit(f"zone_{zone_num}", {
                    "tawaqquf": True,
                    "reason": f"{self.AGENT_NAME} failed: {str(e)}",
                }))
