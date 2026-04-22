"""Classe abstraite commune aux 4 agents."""

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
        self.MOCK_MODE = True

    @abstractmethod
    async def _mock_output(self, hadith_data: dict) -> dict:
        pass

    async def run(self, hadith_data: dict, queue: asyncio.Queue):
        """Point d'entrée appelé par l'orchestrateur."""
        try:
            if self.MOCK_MODE:
                output = await self._mock_output(hadith_data)
            else:
                raise NotImplementedError(f"{self.AGENT_NAME}: mode réel pas implémenté")

            for zone_num in self.ZONES_PRODUCED:
                zone_data = output.get(f"zone_{zone_num}", {"tawaqquf": True})
                await queue.put(emit(f"zone_{zone_num}", zone_data))
                await asyncio.sleep(0.3)

        except Exception as e:
            log.exception(f"[{self.AGENT_NAME}] Erreur")
            for zone_num in self.ZONES_PRODUCED:
                await queue.put(emit(f"zone_{zone_num}", {
                    "tawaqquf": True,
                    "reason": f"{self.AGENT_NAME} failed: {str(e)}"
                }))