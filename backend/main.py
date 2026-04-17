"""Al-Mīzān v5.0 — Point d'entrée Starlette/uvicorn."""

import os
import pathlib
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse, StreamingResponse
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from backend.orchestrator import Orchestrator
from backend.utils.logging import get_logger

log = get_logger("mizan.main")

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

VERSION = "5.0.0-dev"

# Instance globale de l'orchestrateur
_orchestrator = Orchestrator(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

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
        _orchestrator.process(query),
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
    Mount("/", app=StaticFiles(
        directory=str(_REPO_ROOT / "frontend"),
        html=True
    )),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["Content-Type", "Accept", "Cache-Control"],
    ),
]

app = Starlette(routes=routes, middleware=middleware)