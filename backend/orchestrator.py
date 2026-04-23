"""Orchestrateur Al-Mīzān v5.0.

Pilote les 4 agents spécialisés en parallèle via une queue partagée.
Streame les 32 zones au fur et à mesure via SSE.
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
from backend.agents.protected_terms import (
    should_force_sonnet, 
    validate_response_safety,
    SECURITY_MESSAGE
)
from backend.utils.sse import emit, keepalive
from backend.utils.logging import get_logger

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
        ]
        for agent in self.agents:
            agent.MOCK_MODE = MOCK_MODE
        self.demo_responses = self._load_demo_responses()
    
    def _load_demo_responses(self) -> dict:
        """Charge les réponses de démo depuis fixtures"""
        fixtures_path = Path(__file__).parent / "fixtures" / "demo_responses.json"
        try:
            with open(fixtures_path, 'r', encoding='utf-8') as f:
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
            yield emit("zone_32", {"type": "done", "partial": True, "reason": "global_timeout"})
        except Exception as e:
            log.exception(f"[ORCHESTRATOR] Erreur critique")
            yield emit("error", {"message": str(e)})
            yield emit("zone_32", {"type": "done", "error": True})

    async def _process_inner(self, query: str, demo_mode: bool) -> AsyncGenerator[str, None]:
        deadline = time.monotonic() + GLOBAL_TIMEOUT_S
        
        # ── Zone 1 : INITIALISATION ───────────────────────────
        yield emit("zone_1", {
            "zone": 1, "step": "INITIALISATION",
            "message": "Ouverture des registres"
        })
        await asyncio.sleep(0.3)

        # ── Zone 2 : TRADUCTION ──────────────────────────────
        yield emit("meta_pipeline_traduction", {
            "step": "TRADUCTION",
            "message": f"Requête: {query}"
        })
        await asyncio.sleep(0.2)

        # ── MODE DÉMO : Utiliser les fixtures ────────────────
        if demo_mode:
            async for chunk in self._process_demo(query, deadline):
                yield chunk
            return
        
        # ── MODE RÉEL : Pipeline complet ─────────────────────
<<<<<<< HEAD
        # ── Zones 3-4 : DORAR ────────────────────────────────
=======
>>>>>>> db4d52f (fix(orchestrator): désactiver le forçage MOCK_MODE et ajouter .env.example)
        yield emit("meta_pipeline_dorar", {"step": "DORAR_REQUETE"})
        await asyncio.sleep(0.2)
        
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

<<<<<<< HEAD
        # ── Zones 30-32 : CLÔTURE ──────────────────────────────
=======
>>>>>>> db4d52f (fix(orchestrator): désactiver le forçage MOCK_MODE et ajouter .env.example)
        if time.monotonic() < deadline:
            yield emit("zone_30", {"zone": 30, "step": "SYNTHESE"})
            yield emit("zone_31", {"zone": 31, "step": "VERIFICATION"})
            yield emit("zone_32", {"zone": 32, "type": "done"})
        else:
            yield emit("zone_32", {"zone": 32, "type": "done", "partial": True, "reason": "deadline_exceeded"})
    
    async def _process_demo(self, query: str, deadline: float) -> AsyncGenerator[str, None]:
<<<<<<< HEAD
        """Mode démo avec fixtures - Simulation du streaming"""
        # Recherche dans les fixtures
=======
        """Mode démo avec fixtures + pipeline 40 zones complet."""
>>>>>>> db4d52f (fix(orchestrator): désactiver le forçage MOCK_MODE et ajouter .env.example)
        query_lower = query.lower()
        demo_data = None
        
        if "niyya" in query_lower or "intention" in query_lower:
            demo_data = self.demo_responses.get("niyya")
        elif "science" in query_lower or "ilm" in query_lower or "علم" in query_lower:
            demo_data = self.demo_responses.get("science")
        else:
            demo_data = self.demo_responses.get("default")
        
        if not demo_data:
            yield emit("error", {"message": "Aucun résultat trouvé", "code": "NO_RESULT"})
            yield emit("zone_32", {"zone": 32, "type": "done", "error": True})
            return
        
<<<<<<< HEAD
        # ── Zone 3-4 : Affichage du hadith ───────────────────
=======
>>>>>>> db4d52f (fix(orchestrator): désactiver le forçage MOCK_MODE et ajouter .env.example)
        yield emit("meta_pipeline_dorar", {"step": "DORAR_REQUETE"})
        await asyncio.sleep(0.3)
        
        yield emit("zone_4", {
            "zone": 4,
            "type": "hadith_core",
            "data": demo_data["hadith"]
        })
        await asyncio.sleep(0.4)
<<<<<<< HEAD
        
        # ── Zones 5-29 : Analyse progressive ─────────────────
        analysis = demo_data["analysis"]
        
        # Isnad (Zones 5-10)
        yield emit("zone_5", {"zone": 5, "step": "ISNAD_ANALYSE", "message": "Analyse de la chaîne..."})
        await asyncio.sleep(0.5)
        yield emit("zone_10", {"zone": 10, "type": "isnad_result", "data": analysis["isnad"]})
        
        # Matn (Zones 11-15)
        yield emit("zone_11", {"zone": 11, "step": "MATN_ANALYSE", "message": "Vérification du texte..."})
        await asyncio.sleep(0.5)
        yield emit("zone_15", {"zone": 15, "type": "matn_result", "data": analysis["matn"]})
        
        # Aqidah (Zones 16-20)
        yield emit("zone_16", {"zone": 16, "step": "AQIDAH_ANALYSE", "message": "Contrôle théologique..."})
        await asyncio.sleep(0.5)
        
        # Validation de sécurité
        is_safe, error_msg = validate_response_safety({"analysis": analysis})
=======

        is_safe, error_msg = validate_response_safety({"analysis": demo_data.get("analysis", {})})
>>>>>>> db4d52f (fix(orchestrator): désactiver le forçage MOCK_MODE et ajouter .env.example)
        if not is_safe:
            log.error(f"[SECURITY] Réponse bloquée: {error_msg}")
            yield emit("error", SECURITY_MESSAGE)
            yield emit("zone_32", {"zone": 32, "type": "done", "error": True})
            return
<<<<<<< HEAD
        
        yield emit("zone_20", {"zone": 20, "type": "aqidah_result", "data": analysis["aqidah"]})
        
        # Tarjih (Zones 21-25)
        yield emit("zone_21", {"zone": 21, "step": "TARJIH_ANALYSE", "message": "Évaluation finale..."})
        await asyncio.sleep(0.5)
        yield emit("zone_25", {"zone": 25, "type": "tarjih_result", "data": analysis["tarjih"]})
        
        # Fawaid (Zones 26-29)
        yield emit("zone_26", {"zone": 26, "step": "FAWAID_ANALYSE", "message": "Extraction des leçons..."})
        await asyncio.sleep(0.5)
        yield emit("zone_29", {"zone": 29, "type": "fawaid_result", "data": analysis["fawaid"]})
        
        # ── Zones 30-32 : CLÔTURE ────────────────────────────
        yield emit("zone_30", {"zone": 30, "step": "SYNTHESE"})
=======

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
>>>>>>> db4d52f (fix(orchestrator): désactiver le forçage MOCK_MODE et ajouter .env.example)
        await asyncio.sleep(0.2)
        yield emit("zone_31", {"zone": 31, "step": "VERIFICATION"})
        await asyncio.sleep(0.2)
        yield emit("zone_32", {"zone": 32, "type": "done", "demo": True})
