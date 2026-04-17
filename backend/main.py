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

from backend.orchestrator import Orchestrator
from backend.pipeline import ValidationPipeline
from backend.utils.logging import get_logger

log = get_logger("mizan.main")

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

async def search(request):
    query = request.query_params.get("q", "").strip()
    if not query:
        return JSONResponse({"error": "Paramètre q requis"}, status_code=400)
    
    log.info(f"[SEARCH] Query: {query}")
    
    return StreamingResponse(
        _get_orch().process(query),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "X-Mizan-Version": VERSION,
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
_allowed_origins = os.environ.get("MIZAN_ALLOWED_ORIGINS", "http://localhost:8000").split(",")

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["Content-Type", "Accept", "Cache-Control"],
    ),
]

app = Starlette(routes=routes, middleware=middleware)