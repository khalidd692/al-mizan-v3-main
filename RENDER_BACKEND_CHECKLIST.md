# Render Backend Checklist

Checklist backend validee avant push Render pour `backend.main:app`.

## Commandes Render

- Build: `pip install -r requirements.txt`
- Start: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

## Variables d'environnement

- `PYTHONPATH=.`
- `MIZAN_ALLOWED_ORIGINS=*`
- `MIZAN_DEMO_MODE=0`
- `ANTHROPIC_API_KEY` si les appels externes hors mode demo sont utilises
- `DATABASE_URL=sqlite:///backend/database/almizan_v7.db` si valeur par defaut non surchargee

## Verification backend

- [x] `backend/main.py` utilise `entries_fts MATCH` au lieu de `LIKE '%...%'` pour la recherche SSE
- [x] Fallback exact conserve pour `id` et `hadith_id_dorar`
- [x] Index FTS5 present sur `entries_fts`
- [x] Base `backend/database/almizan_v7.db` enrichie en `ar_text`, `ar_text_clean`, `fr_text`, `grade_primary`

## Smoke tests executes le 2026-05-01

- [x] Demarrage ASGI local via `uvicorn backend.main:app`
- [x] `GET /api/health` retourne `200`
- [x] `GET /api/search?q=intention&limit=5` retourne `200`
- [x] Flux SSE contient `meta_pipeline_start`, `zone_3`, `done`
- [x] Flux SSE emet `40` zones distinctes
- [x] En mode test SSE `intention`, `34` zones sont materiellement alimentees
- [x] Profil Render simule avec `MIZAN_DEMO_MODE=0` valide (`demo_mode=false` sur `/api/health`)

## Verification post-deploiement Render

- [ ] Ouvrir `/api/health` et verifier `status=ok`
- [ ] Ouvrir `/api/search?q=intention&limit=5` avec `Accept: text/event-stream`
- [ ] Verifier presence des evenements `zone_1` a `zone_40`
- [ ] Verifier qu'aucune erreur SQLite `entries_fts` introuvable n'apparait dans les logs
- [ ] Verifier que la DB embarquee contient bien `backend/database/almizan_v7.db`

## Fichiers du slice backend a pousser

- `backend/main.py`
- `backend/database/almizan_v7.db`
- `backend/scripts/enrich_from_fawaz.py`
- `backend/scripts/enrich_ar_text.py`
- `backend/scripts/create_fts5_index.py`
- `RENDER_BACKEND_CHECKLIST.md`
