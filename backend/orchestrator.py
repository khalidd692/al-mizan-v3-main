"""Orchestrateur Al-Mīzān v5.0.

Pilote les 8 agents spécialisés en parallèle via une queue partagée.
Streame les 40 zones au fur et à mesure via SSE.
"""

import asyncio
import time
import json
import os
from pathlib import Path
from typing import AsyncGenerator

from backend.agents.agent_isnad import AgentIsnad
from backend.agents.agent_ilal import AgentIlal
from backend.agents.agent_matn import AgentMatn
from backend.agents.agent_tarjih import AgentTarjih
from backend.agents.agent_fawaid import AgentFawaid
from backend.agents.agent_aqidah import AgentAqidah
from backend.agents.agent_takhrij import AgentTakhrij
from backend.agents.agent_advanced import AgentAdvanced
from backend.agents.protected_terms import (
    should_force_sonnet,
    validate_response_safety,
    SECURITY_MESSAGE,
)
from backend.utils.sse import emit, keepalive
from backend.utils.logging import get_logger
from backend.utils.local_db import search_hadith, row_to_hadith_core
from backend.utils.fr_ar_lexicon import get_token_groups

log = get_logger("mizan.orchestrator")

GLOBAL_TIMEOUT_S = 55.0
KEEPALIVE_INTERVAL_S = 10.0

# Mode démo : false par défaut, activable via MOCK_MODE=true dans .env
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"


class Orchestrator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.agents = [
            AgentIsnad(api_key),
            AgentIlal(api_key),
            AgentMatn(api_key),
            AgentTarjih(api_key),
            AgentFawaid(api_key),
            AgentAqidah(api_key),
            AgentTakhrij(api_key),
            AgentAdvanced(api_key),
        ]
        for agent in self.agents:
            agent.MOCK_MODE = MOCK_MODE
        self.demo_responses = self._load_demo_responses()

    def _load_demo_responses(self) -> dict:
        fixtures_path = Path(__file__).parent / "fixtures" / "demo_responses.json"
        try:
            with open(fixtures_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.warning(f"Impossible de charger les fixtures: {e}")
            return {}

    async def process(self, query: str, demo_mode: bool = None) -> AsyncGenerator[str, None]:
        """Pipeline complet avec timeout global de sécurité."""
        if demo_mode is None:
            demo_mode = MOCK_MODE

        try:
            force_sonnet, reason = should_force_sonnet(query)
            if force_sonnet:
                log.info(f"[SECURITY] Sonnet forcé: {reason}")

            async for chunk in self._process_inner(query, demo_mode):
                yield chunk
        except asyncio.TimeoutError:
            log.warning(f"[TIMEOUT] Query dépassée: {query}")
            yield emit("zone_40", {"type": "done", "partial": True, "reason": "global_timeout"})
        except Exception as e:
            log.exception("[ORCHESTRATOR] Erreur critique")
            yield emit("error", {"message": str(e)})
            yield emit("zone_40", {"zone": 40, "type": "done", "error": True})

    async def _process_inner(self, query: str, demo_mode: bool) -> AsyncGenerator[str, None]:
        deadline = time.monotonic() + GLOBAL_TIMEOUT_S

        # ── Zone 1 : INITIALISATION ───────────────────────────
        yield emit("zone_1", {
            "zone": 1, "step": "INITIALISATION",
            "message": "Ouverture des registres",
        })
        await asyncio.sleep(0.3)

        # ── Zone 2 : TRADUCTION FR→AR ─────────────────────────
        # Tokenisation + équivalents arabes via le lexique. Les tokens AR
        # seront utilisés par search_hadith() pour matcher le corpus arabe.
        fr_tokens = [t for t in query.split() if len(t) > 2][:6]
        groups = get_token_groups(fr_tokens)
        ar_tokens = [t for g in groups for t in g[1:]]
        yield emit("meta_pipeline_traduction", {
            "step": "TRADUCTION",
            "message": f"Requête: {query}",
            "fr_tokens": fr_tokens,
            "ar_tokens": ar_tokens,
        })
        await asyncio.sleep(0.2)

        # ── MODE DÉMO : Utiliser les fixtures ──────────────────
        if demo_mode:
            async for chunk in self._process_demo(query, deadline):
                yield chunk
            return

        # ── MODE RÉEL : Recherche dans la base locale ──────────
        yield emit("meta_pipeline_dorar", {"step": "LOCAL_DB_SEARCH"})
        await asyncio.sleep(0.2)

        db_results = search_hadith(query)

        # Détection du flag "non_trouve" (score de correspondance < 30%)
        if db_results and db_results[0].get("_non_trouve"):
            score = db_results[0].get("_match_score", 0)
            log.warning(f"[ORCHESTRATOR] Score trop faible ({score}%) pour : {query!r}")
            yield emit("meta_pipeline_dorar", {"step": "NO_RESULT", "reason": "low_relevance_score", "score": score})
            yield emit("zone_3", {
                "zone": 3, "type": "no_result",
                "query": query, "tawaqquf": True,
                "message": "Aucun hadith trouvé en base locale",
                "reason": "low_relevance",
                "score": score,
            })
            yield emit("zone_40", {"zone": 40, "type": "done", "error": True, "reason": "no_hadith_found", "score": score})
            return

        if not db_results:
            log.warning(f"[ORCHESTRATOR] Aucun hadith trouvé pour : {query!r}")
            yield emit("meta_pipeline_dorar", {"step": "NO_RESULT"})
            yield emit("zone_3", {
                "zone": 3, "type": "no_result",
                "query": query, "tawaqquf": True,
                "message": "Aucun hadith correspondant dans la base locale",
            })
            yield emit("zone_40", {"zone": 40, "type": "done", "error": True, "reason": "no_hadith_found"})
            return

        hadith_data = row_to_hadith_core(db_results[0])
        log.info(f"[LOCAL_DB] Hadith trouvé : {hadith_data['source']}")
        yield emit("meta_pipeline_dorar", {
            "step": "LOCAL_DB_HIT",
            "count": len(db_results),
            "source": hadith_data["source"],
        })
        yield emit("zone_3", {
            "zone": 3,
            "type": "hadith_core",
            "data": hadith_data,
        })

        # ── Zones 4-40 : 8 agents en parallèle ──────────────────
        queue: asyncio.Queue = asyncio.Queue()

        async def run_all_agents():
            tasks = [agent.run(hadith_data, queue) for agent in self.agents]
            await asyncio.gather(*tasks, return_exceptions=True)
            await queue.put(None)

        agent_task = asyncio.create_task(run_all_agents())

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                log.warning("[TIMEOUT] Deadline globale atteinte")
                agent_task.cancel()
                raise asyncio.TimeoutError()

            timeout = min(KEEPALIVE_INTERVAL_S, remaining)
            try:
                chunk = await asyncio.wait_for(queue.get(), timeout=timeout)
                if chunk is None:
                    break
                yield chunk
            except asyncio.TimeoutError:
                if time.monotonic() < deadline:
                    yield keepalive()
                else:
                    agent_task.cancel()
                    raise

        await agent_task

        if time.monotonic() < deadline:
            yield emit("zone_38", {"zone": 38, "step": "SYNTHESE"})
            yield emit("zone_39", {"zone": 39, "step": "VERIFICATION"})
            yield emit("zone_40", {"zone": 40, "type": "done"})
        else:
            yield emit("zone_40", {"zone": 40, "type": "done", "partial": True, "reason": "deadline_exceeded"})

    async def _process_demo(self, query: str, deadline: float) -> AsyncGenerator[str, None]:
        """Mode démo avec fixtures + pipeline 40 zones complet."""
        query_lower = query.lower()

        if "niyya" in query_lower or "intention" in query_lower:
            demo_data = self.demo_responses.get("niyya")
        elif "science" in query_lower or "ilm" in query_lower or "علم" in query_lower:
            demo_data = self.demo_responses.get("science")
        else:
            demo_data = self.demo_responses.get("default")

        if not demo_data:
            yield emit("error", {"message": "Aucun résultat trouvé", "code": "NO_RESULT"})
            yield emit("zone_40", {"zone": 40, "type": "done", "error": True})
            return

        yield emit("meta_pipeline_dorar", {"step": "DORAR_REQUETE"})
        await asyncio.sleep(0.3)

        hadith_data = demo_data["hadith"]
        yield emit("zone_3", {"zone": 3, "type": "hadith_core", "data": hadith_data})
        await asyncio.sleep(0.4)

        is_safe, error_msg = validate_response_safety({"analysis": demo_data.get("analysis", {})})
        if not is_safe:
            log.error(f"[SECURITY] Réponse démo bloquée: {error_msg}")
            yield emit("error", SECURITY_MESSAGE)
            yield emit("zone_40", {"zone": 40, "type": "done", "error": True})
            return

        queue: asyncio.Queue = asyncio.Queue()

        async def run_all_agents():
            tasks = [agent.run(hadith_data, queue) for agent in self.agents]
            await asyncio.gather(*tasks, return_exceptions=True)
            await queue.put(None)

        agent_task = asyncio.create_task(run_all_agents())

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                log.warning("[TIMEOUT-DEMO] Deadline globale atteinte")
                agent_task.cancel()
                raise asyncio.TimeoutError()

            timeout = min(KEEPALIVE_INTERVAL_S, remaining)
            try:
                chunk = await asyncio.wait_for(queue.get(), timeout=timeout)
                if chunk is None:
                    break
                yield chunk
            except asyncio.TimeoutError:
                if time.monotonic() < deadline:
                    yield keepalive()
                else:
                    agent_task.cancel()
                    raise

        await agent_task

        yield emit("zone_38", {"zone": 38, "step": "SYNTHESE"})
        await asyncio.sleep(0.2)
        yield emit("zone_39", {"zone": 39, "step": "VERIFICATION"})
        await asyncio.sleep(0.2)
        yield emit("zone_40", {"zone": 40, "type": "done", "demo": True})
