"""Orchestrateur Al-Mīzān v5.0.

Pilote les 4 agents spécialisés en parallèle via une queue partagée.
Streame les 32 zones au fur et à mesure via SSE.
"""

import asyncio
import time
from typing import AsyncGenerator

from backend.agents.agent_isnad import AgentIsnad
from backend.agents.agent_ilal import AgentIlal
from backend.agents.agent_matn import AgentMatn
from backend.agents.agent_tarjih import AgentTarjih
from backend.utils.sse import emit, keepalive
from backend.utils.logging import get_logger

log = get_logger("mizan.orchestrator")

GLOBAL_TIMEOUT_S = 55.0
KEEPALIVE_INTERVAL_S = 10.0

class Orchestrator:
    def __init__(self, api_key: str):
        self.agents = [
            AgentIsnad(api_key),
            AgentIlal(api_key),
            AgentMatn(api_key),
            AgentTarjih(api_key),
        ]

    async def process(self, query: str) -> AsyncGenerator[str, None]:
        """Pipeline complet avec timeout global de sécurité."""
        try:
            async for chunk in self._process_inner(query):
                yield chunk
        except asyncio.TimeoutError:
            log.warning(f"[TIMEOUT] Query dépassée: {query}")
            yield emit("zone_32", {"type": "done", "partial": True, "reason": "global_timeout"})
        except Exception as e:
            log.exception(f"[ORCHESTRATOR] Erreur critique")
            yield emit("error", {"message": str(e)})
            yield emit("zone_32", {"type": "done", "error": True})

    async def _process_inner(self, query: str) -> AsyncGenerator[str, None]:
        # Deadline global pour éviter les blocages indéfinis
        deadline = time.monotonic() + GLOBAL_TIMEOUT_S
        
        # ── Zone 1 : INITIALISATION ───────────────────────────
        yield emit("zone_1", {
            "zone": 1, "step": "INITIALISATION",
            "message": "Ouverture des registres"
        })

        # ── Zone 2 : TRADUCTION (mock pour l'instant) ──────────
        # Note : la vraie traduction FR→AR sera réintroduite phase 2
        yield emit("meta_pipeline_traduction", {
            "step": "TRADUCTION",
            "message": f"Requête: {query}"
        })

        # ── Zones 3-4 : DORAR (mock pour l'instant) ────────────
        yield emit("meta_pipeline_dorar", {"step": "DORAR_REQUETE"})
        
        hadith_data = {
            "matn": "إنما الأعمال بالنيات، وإنما لكل امرئ ما نوى",
            "translation_fr": "Les actions ne valent que par les intentions, et chaque homme n'aura que ce qu'il a eu l'intention d'obtenir.",
            "source": "Ṣaḥīḥ al-Bukhārī n°1",
            "grade_raw": "صحيح",
            "mock": True,
        }
        
        yield emit("zone_4", {
            "zone": 4,
            "type": "hadith_core",
            "data": hadith_data
        })

        # ── Zones 5-29 : 4 agents en parallèle ─────────────────
        queue: asyncio.Queue = asyncio.Queue()

        async def run_all_agents():
            tasks = [agent.run(hadith_data, queue) for agent in self.agents]
            await asyncio.gather(*tasks, return_exceptions=True)
            await queue.put(None)  # Sentinelle

        agent_task = asyncio.create_task(run_all_agents())
        
        while True:
            # Vérifier le deadline global
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                log.warning("[TIMEOUT] Deadline globale atteinte")
                agent_task.cancel()
                raise asyncio.TimeoutError()
            
            # Timeout dynamique : min entre keepalive et temps restant
            timeout = min(KEEPALIVE_INTERVAL_S, remaining)
            
            try:
                chunk = await asyncio.wait_for(queue.get(), timeout=timeout)
                if chunk is None:
                    break
                yield chunk
            except asyncio.TimeoutError:
                # Simple keepalive si on n'a pas atteint le deadline
                if time.monotonic() < deadline:
                    yield keepalive()
                else:
                    agent_task.cancel()
                    raise

        await agent_task

        # ── Zones 30-32 : CLÔTURE ──────────────────────────────
        yield emit("zone_30", {"zone": 30, "step": "SYNTHESE", "message": "Pipeline terminé"})
        yield emit("zone_31", {"zone": 31, "step": "VERIFICATION"})
        yield emit("zone_32", {"zone": 32, "type": "done"})
