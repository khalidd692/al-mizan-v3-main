"""Al-Mīzān v5.0 — Point d'entrée Starlette/uvicorn."""

import os
import pathlib
from dotenv import load_dotenv

# CRITIQUE : Charger .env AVANT toute autre import qui lit os.environ
load_dotenv()

from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse, StreamingResponse
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from collections import defaultdict
import time

from backend.orchestrator import Orchestrator
from backend.pipeline import ValidationPipeline
from backend.utils.logging import get_logger

log = get_logger("mizan.main")

# Rate limiting simple (10 requêtes/min par IP)
_rate_limiter = defaultdict(list)
RATE_LIMIT_MAX = 10
RATE_LIMIT_WINDOW = 60  # secondes

_orch = None
def _get_orch():
    global _orch
    if _orch is None:
        _orch = Orchestrator(api_key=os.environ.get("ANTHROPIC_API_KEY",""))
    return _orch

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

VERSION = "5.0.0-dev"

async def health(request):
    return JSONResponse({
        "status": "ok",
        "version": VERSION,
        "service": "Al-Mīzān — Moteur de Takhrīj",
    })

def _check_rate_limit(ip: str) -> tuple[bool, str]:
    """Vérifie le rate limit pour une IP"""
    now = time.time()
    
    # Nettoyer les anciennes entrées
    _rate_limiter[ip] = [t for t in _rate_limiter[ip] if now - t < RATE_LIMIT_WINDOW]
    
    # Vérifier la limite
    if len(_rate_limiter[ip]) >= RATE_LIMIT_MAX:
        return False, f"Rate limit dépassé: {RATE_LIMIT_MAX} requêtes/{RATE_LIMIT_WINDOW}s"
    
    # Enregistrer la requête
    _rate_limiter[ip].append(now)
    return True, ""

async def search(request):
    query = request.query_params.get("q", "").strip()
    if not query:
        return JSONResponse({"error": "Paramètre q requis"}, status_code=400)
    
    # Récupérer l'IP du client
    client_ip = request.client.host if request.client else "unknown"
    
    # Vérifier le rate limit
    allowed, error_msg = _check_rate_limit(client_ip)
    if not allowed:
        log.warning(f"[RATE_LIMIT] {client_ip}: {error_msg}")
        return JSONResponse(
            {"error": error_msg, "code": "RATE_LIMIT_EXCEEDED"},
            status_code=429
        )
    
    # Détecter le mode démo via header
    demo_mode = request.headers.get("X-Mizan-Demo", "").lower() == "true"
    
    log.info(f"[SEARCH] Query: {query} | Demo: {demo_mode} | IP: {client_ip}")
    
    return StreamingResponse(
        _get_orch().process(query, demo_mode=demo_mode),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "X-Mizan-Version": VERSION,
            "X-Mizan-Demo": "true" if demo_mode else "false",
        }
    )

async def harvest_and_process(request):
    """Endpoint SSE pour harvesting + validation + insertion automatique."""
    start_id = int(request.query_params.get("start_id", "1"))
    count = int(request.query_params.get("count", "1000"))
    rate_limit = float(request.query_params.get("rate_limit", "2.0"))
    
    log.info(f"[HARVEST] Démarrage: start_id={start_id}, count={count}, rate_limit={rate_limit}")
    
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    pipeline = ValidationPipeline(api_key)
    
    return StreamingResponse(
        pipeline.process_stream(start_id, count, rate_limit),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "X-Mizan-Version": VERSION,
        }
    )

routes = [
    Route("/api/health", health),
    Route("/api/search", search),
    Route("/api/harvest-and-process", harvest_and_process),
    Mount("/", app=StaticFiles(
        directory=str(_REPO_ROOT / "frontend"),
        html=True
    )),
]

# CORS : restreindre en production via variable d'env
raw = os.environ.get("MIZAN_ALLOWED_ORIGINS","*")
origins = ["*"] if raw.strip()=="*" else [o.strip() for o in raw.split(",") if o.strip()]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["Content-Type", "Accept", "Cache-Control", "X-Mizan-Demo"],
        expose_headers=["X-Mizan-Version", "X-Mizan-Demo"],
    ),
]

app = Starlette(routes=routes, middleware=middleware)