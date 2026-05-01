"""Al-Mīzān v5.0 — Point d'entrée Starlette/uvicorn."""

import os
import pathlib
import json
import sqlite3
import re
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

from backend.utils.logging import get_logger

log = get_logger("mizan.main")

# Rate limiting simple (10 requêtes/min par IP)
_rate_limiter = defaultdict(list)
RATE_LIMIT_MAX = 10
RATE_LIMIT_WINDOW = 60  # secondes

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_FRONTEND_DIR = _REPO_ROOT

VERSION = "5.0.0-dev"


def _get_db_path() -> pathlib.Path:
    db_url = os.environ.get("DATABASE_URL", "sqlite:///backend/database/almizan_v7.db")
    return pathlib.Path(db_url.replace("sqlite:///", "").replace("sqlite://", ""))


def _sse(event: str, payload: dict) -> bytes:
    body = json.dumps(payload, ensure_ascii=False)
    return f"event: {event}\ndata: {body}\n\n".encode("utf-8")


def _tokenize_fts_query(query: str) -> list[str]:
    return [token for token in re.findall(r"[\w\u0600-\u06FF]+", query, flags=re.UNICODE) if token]


def _build_fts_match(query: str) -> str:
    tokens = _tokenize_fts_query(query)
    if not tokens:
        raise ValueError("Requête vide après normalisation FTS")

    escaped_tokens = [token.replace('"', '""') for token in tokens]
    if len(escaped_tokens) == 1:
        term_expr = f'"{escaped_tokens[0]}"'
    else:
        term_expr = " AND ".join(f'"{token}"' for token in escaped_tokens)

    return f"(ar_text_clean : {term_expr}) OR (fr_text : {term_expr})"


def _fetch_entries(query: str, limit: int) -> list[dict]:
    db_path = _get_db_path()
    if not db_path.exists():
        raise FileNotFoundError(f"Base SQLite introuvable: {db_path}")

    fts_query = _build_fts_match(query)
    sql = """
        WITH ranked_matches AS (
            SELECT
                e.rowid AS rowid,
                bm25(entries_fts) AS fts_rank,
                0 AS exact_match
            FROM entries_fts
            JOIN entries e ON e.rowid = entries_fts.rowid
            WHERE entries_fts MATCH ?

            UNION

            SELECT
                e.rowid AS rowid,
                0.0 AS fts_rank,
                1 AS exact_match
            FROM entries e
            WHERE e.id = ?
               OR e.hadith_id_dorar = ?
        ), deduped_matches AS (
            SELECT
                rowid,
                MIN(fts_rank) AS fts_rank,
                MAX(exact_match) AS exact_match
            FROM ranked_matches
            GROUP BY rowid
        )
        SELECT e.*
        FROM deduped_matches matches
        JOIN entries e ON e.rowid = matches.rowid
        ORDER BY
            matches.exact_match DESC,
            CASE grade_primary
                WHEN 'Sahih' THEN 1
                WHEN 'Hasan' THEN 2
                WHEN 'Da''if' THEN 3
                WHEN 'Mawdu''' THEN 4
                ELSE 5
            END,
            matches.fts_rank ASC,
            id ASC
        LIMIT ?
    """

    conn = sqlite3.connect(str(db_path), timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        fts_exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='entries_fts'"
        ).fetchone()
        if not fts_exists:
            raise sqlite3.OperationalError("Table FTS5 entries_fts introuvable")

        rows = conn.execute(
            sql,
            (fts_query, query, query, limit),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def _build_zone_payloads(row: dict) -> dict[int, dict]:
    """Construit les 40 zones à partir d'une ligne brute de `entries`."""
    source_label = row.get("book_name_fr") or row.get("book_name_ar") or ""
    hadith_number = row.get("hadith_number") or ""
    isnad_raw = row.get("ar_full_isnad") or ""
    narrator = row.get("ar_narrator") or ""

    # Zone 2 attend un format `isnad_chain` côté frontend.
    chain = []
    if narrator or isnad_raw:
        chain.append({
            "name_ar": narrator,
            "name_fr": "",
            "verdict": row.get("grade_primary") or "",
            "death_h": None,
            "raw_isnad": isnad_raw,
        })

    zones: dict[int, dict] = {
        1: {"zone": 1, "type": "init", "source": "db_locale"},
        2: {"zone": 2, "type": "isnad_chain", "chain": chain, "source": "db_locale"},
        3: {"zone": 3, "type": "hadith_core", "source": "db_locale"},
        4: {
            "zone": 4,
            "type": "takhrij",
            "schema": {
                "source_principale": source_label,
                "hadith_number": hadith_number,
                "hadith_id_dorar": row.get("hadith_id_dorar") or "",
                "source_url": row.get("source_url") or "",
            },
            "source": "db_locale",
        },
        5: {
            "zone": 5,
            "type": "isnad_5_conditions",
            "sanad_ittissal": row.get("sanad_ittissal"),
            "sanad_adalah": row.get("sanad_adalah"),
            "sanad_dabt": row.get("sanad_dabt"),
            "sanad_shudhudh": row.get("sanad_shudhudh"),
            "sanad_illa": row.get("sanad_illa"),
            "source": "db_locale",
        },
        6: {
            "zone": 6,
            "type": "ilal",
            "conclusion": row.get("grade_explanation") or "",
            "source": "db_locale",
        },
        7: {"zone": 7, "type": "tafarrud", "value": row.get("takhrij") or "", "source": "db_locale"},
        8: {"zone": 8, "type": "munkar", "value": row.get("grade_primary") or "", "source": "db_locale"},
        9: {"zone": 9, "type": "gharib", "value": row.get("fr_summary") or "", "source": "db_locale"},
        10: {"zone": 10, "type": "sabab_wurud", "circonstance": row.get("fr_explanation") or "", "source": "db_locale"},
        11: {"zone": 11, "type": "shuruh", "value": row.get("fr_explanation") or "", "source": "db_locale"},
        12: {"zone": 12, "type": "athar_sahabah", "narrator": narrator, "source": "db_locale"},
        13: {"zone": 13, "type": "athar_tabiin", "value": isnad_raw, "source": "db_locale"},
        14: {"zone": 14, "type": "positions_imams", "value": row.get("grade_by_mohdith") or "", "source": "db_locale"},
        15: {"zone": 15, "type": "ijma", "value": row.get("grade_primary") or "", "source": "db_locale"},
        16: {"zone": 16, "type": "khilaf", "value": row.get("grade_explanation") or "", "source": "db_locale"},
    }

    # Zones 17→40 : transport brut des champs DB sans génération.
    for zone_num in range(17, 41):
        zones[zone_num] = {
            "zone": zone_num,
            "type": "db_zone",
            "entry": row,
            "source": "db_locale",
        }

    return zones

def _is_demo_mode() -> bool:
    raw = os.environ.get("MIZAN_DEMO_MODE", "1").strip().lower()
    return raw in ("1", "true", "yes", "on")

async def health(request):
    return JSONResponse({
        "status": "ok",
        "version": VERSION,
        "service": "Al-Mīzān — Moteur de Takhrīj",
        "demo_mode": _is_demo_mode(),
        "demo_banner": "MODE DÉMONSTRATION" if _is_demo_mode() else None,
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

    try:
        limit = int(request.query_params.get("limit", "20"))
    except ValueError:
        return JSONResponse({"error": "Paramètre limit invalide"}, status_code=400)
    limit = max(1, min(limit, 100))
    
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
    
    log.info(f"[SEARCH] Query: {query} | Limit: {limit} | IP: {client_ip}")

    def event_stream():
        yield _sse("meta_pipeline_start", {
            "step": "DB_LOCAL_ENTRIES",
            "query": query,
            "limit": limit,
            "mode": "raw_db_only",
            "generated_content": False,
        })

        try:
            rows = _fetch_entries(query=query, limit=limit)
        except FileNotFoundError as exc:
            yield _sse("error", {"message": str(exc), "code": "DB_NOT_FOUND"})
            yield _sse("done", {"ok": False, "total": 0})
            return
        except sqlite3.Error as exc:
            yield _sse("error", {"message": f"Erreur SQLite: {exc}", "code": "DB_ERROR"})
            yield _sse("done", {"ok": False, "total": 0})
            return

        if not rows:
            yield _sse("zone_3", {"type": "no_result", "query": query})
            yield _sse("zone_40", {"zone": 40, "type": "done", "total": 0, "query": query, "source": "db_locale"})
            yield _sse("done", {"ok": True, "total": 0, "query": query})
            return

        primary_row = rows[0]
        zones = _build_zone_payloads(primary_row)

        # Compat front actuel: expose la première ligne comme hadith_core.
        yield _sse("zone_3", {"type": "hadith_core", "data": primary_row, "index": 0, "source": "db_locale"})

        # Émettre explicitement les zones 1→40.
        for zone_num in range(1, 41):
            # zone_3 déjà émise ci-dessus avec le format attendu.
            if zone_num == 3:
                continue
            yield _sse(f"zone_{zone_num}", zones[zone_num])

        for idx, row in enumerate(rows):
            yield _sse("db_row", {"index": idx, "row": row})

        yield _sse("done", {"ok": True, "total": len(rows), "query": query})
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "X-Mizan-Version": VERSION,
            "X-Mizan-Demo": "false",
        }
    )

routes = [
    Route("/api/health", health),
    Route("/api/search", search),
    Mount("/", app=StaticFiles(
        directory=str(_FRONTEND_DIR),
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