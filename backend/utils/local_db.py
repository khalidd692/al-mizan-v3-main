"""Recherche locale dans la base SQLite Al-Mīzān (fallback si source externe indisponible).

Règle absolue : ne jamais lire le fichier .db comme texte.
Toutes les requêtes passent exclusivement par sqlite3.
"""
import os
import re
import sqlite3
from pathlib import Path
from typing import Optional

from backend.utils.logging import get_logger
from backend.utils.fr_ar_lexicon import (
    FR_TO_AR,
    get_token_groups,
    check_mawdu_whitelist,
)

log = get_logger("mizan.local_db")

# Pertinence minimale exigée pour considérer un résultat comme « trouvé ».
# En dessous, l'orchestrator déclenche un tawaqquf (« non trouvé »).
MIN_RELEVANCE_RATIO = 0.5

_TASHKEEL = re.compile(
    r"[ً-ٟؐ-ؚۖ-ۜ۟-۪ۤۧۨ-ٰۭ]"
)


def _get_db_path() -> Path:
    db_url = os.getenv("DATABASE_URL", "sqlite:///backend/database/almizan_v7.db")
    return Path(db_url.replace("sqlite:///", ""))


def _strip_tashkeel(text: str) -> str:
    return _TASHKEEL.sub("", text)


def search_hadith(query: str, limit: int = 5) -> list[dict]:
    """Recherche des hadiths dans la table `entries` par mots-clés.

    Stratégie :
      1. Nettoyer la requête (tashkeel, tokenisation)
      2. Chercher dans ar_text_clean, ar_text, fr_text, book_name_ar
      3. Trier par grade (Sahih > Hasan > Da'if) puis zone_id

    Retourne [] si la base est introuvable ou si aucun résultat.
    """
    # ── 0) Whitelist des mawdū‘ classiques : court-circuite la base ──
    whitelist_hit = check_mawdu_whitelist(query)
    if whitelist_hit is not None:
        whitelist_hit["_match_score"] = 100
        whitelist_hit["_match_ratio"] = 1.0
        whitelist_hit["_match_count"] = 0
        whitelist_hit["_from_whitelist"] = True
        log.info(
            f"[LOCAL_DB] Hit whitelist mawdū‘ « {whitelist_hit.get('id')} » "
            f"pour {query!r}"
        )
        return [whitelist_hit]

    db_path = _get_db_path()
    if not db_path.exists():
        log.warning(f"[LOCAL_DB] Base introuvable : {db_path}")
        return []

    clean = _strip_tashkeel(query)
    fr_tokens = [t for t in re.split(r"\s+", clean) if len(t) > 2][:6]
    if not fr_tokens:
        log.warning(f"[LOCAL_DB] Requête trop courte après nettoyage : {query!r}")
        return []

    # ── Traduction FR→AR : chaque token FR devient un groupe ──
    # [token_fr, *équivalents_arabes]. Le SQL fait un OR sur tous
    # les tokens du groupe ; le score compte les groupes matchés
    # (et non les tokens), pour ne pas fausser le ratio.
    groups = get_token_groups(fr_tokens)
    ar_tokens = [t for g in groups for t in g[1:]]
    log.info(
        f"[LOCAL_DB] Tokens FR={fr_tokens} | AR enrichis={ar_tokens}"
    )

    clauses, params = [], []
    for group in groups:
        inner = []
        for token in group:
            like = f"%{token}%"
            inner.append(
                "ar_text_clean LIKE ? OR ar_text LIKE ? OR fr_text LIKE ? OR book_name_ar LIKE ?"
            )
            params.extend([like, like, like, like])
        clauses.append("(" + " OR ".join(inner) + ")")

    sql = f"""
        SELECT
            id, ar_text, ar_text_clean, ar_narrator, ar_full_isnad,
            fr_text, fr_summary,
            grade_primary, grade_by_mohdith, grade_explanation,
            grade_albani, grade_ibn_baz, grade_ibn_uthaymin,
            book_name_ar, book_name_fr, hadith_number, hadith_id_dorar,
            source_api, source_url, takhrij, zone_id
        FROM entries
        WHERE {" OR ".join(clauses)}
        ORDER BY
            CASE grade_primary
                WHEN 'Sahih' THEN 1
                WHEN 'Hasan' THEN 2
                WHEN 'Da''if' THEN 3
                ELSE 4
            END,
            zone_id ASC
        LIMIT ?
    """
    params.append(limit)

    try:
        conn = sqlite3.connect(str(db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        results = [dict(r) for r in rows]

        # ── Score de pertinence : compter les GROUPES de concepts matchés ──
        # 1 groupe = 1 token FR + ses équivalents AR. Matcher n'importe lequel
        # de ses tokens (FR ou AR) compte pour 1 concept retrouvé.
        def _score(row: dict) -> tuple[int, float]:
            fr = (row.get("fr_text") or "").lower()
            fr += " " + (row.get("fr_summary") or "").lower()
            ar = row.get("ar_text_clean") or row.get("ar_text") or ""
            matched = 0
            for group in groups:
                if any(t.lower() in fr or t in ar for t in group):
                    matched += 1
            return matched, matched / len(groups)

        scored_results = []
        for r in results:
            matched_count, ratio = _score(r)
            r["_match_score"] = round(ratio * 100)
            r["_match_ratio"] = ratio
            r["_match_count"] = matched_count
            scored_results.append((matched_count, r))

        scored_results.sort(key=lambda x: x[0], reverse=True)
        sorted_results = [r for _, r in scored_results]

        # ── Filtre de pertinence stricte (≥ 50 % des concepts) ──────────
        # En deçà, on signale au orchestrator de renvoyer un tawaqquf.
        if sorted_results:
            best = sorted_results[0]
            log.info(
                f"[LOCAL_DB] {len(sorted_results)} résultat(s) pour {query!r} "
                f"| Meilleur match: grade_primary={best.get('grade_primary', 'NULL')} "
                f"(concepts={best.get('_match_count')}/{len(groups)} "
                f"= {best.get('_match_score')}%)"
            )
            if best["_match_ratio"] < MIN_RELEVANCE_RATIO:
                log.warning(
                    f"[LOCAL_DB] Pertinence {best['_match_score']}% < seuil "
                    f"{int(MIN_RELEVANCE_RATIO * 100)}% pour {query!r} → tawaqquf"
                )
                best["_non_trouve"] = True
                return [best]
        return sorted_results
    except sqlite3.Error as exc:
        log.error(f"[LOCAL_DB] Erreur SQLite : {exc}")
        return []


def row_to_hadith_core(row: dict) -> dict:
    """Convertit une ligne `entries` en format hadith_data standard pour les agents."""
    book = row.get("book_name_fr") or row.get("book_name_ar") or "Source inconnue"
    num = row.get("hadith_number", "")
    source_label = f"{book} n°{num}" if num else book
    return {
        # Texte arabe
        "matn": row.get("ar_text", "") or "",
        "matn_clean": row.get("ar_text_clean", "") or "",
        "text_ar": row.get("ar_text", "") or "",
        # Narrateur et isnād
        "narrator": row.get("ar_narrator", "") or "",
        "full_isnad": row.get("ar_full_isnad", "") or "",
        # Traduction
        "translation_fr": row.get("fr_text") or row.get("fr_summary") or "",
        # Source
        "source": source_label,
        "book_name_fr": row.get("book_name_fr", "") or "",
        "book_name_ar": row.get("book_name_ar", "") or "",
        # Grade principal — clé "grade_raw" attendue par dashboard.js
        "grade_raw": row.get("grade_primary", "") or "Non classé",
        "grade_primary": row.get("grade_primary", "") or "",
        "grade_by": row.get("grade_by_mohdith", "") or "",
        "grade_explanation": row.get("grade_explanation", "") or "",
        # Grades par savant
        "grade_albani": row.get("grade_albani", "") or "",
        "grade_ibn_baz": row.get("grade_ibn_baz", "") or "",
        "grade_ibn_uthaymin": row.get("grade_ibn_uthaymin", "") or "",
        "grade_muqbil": row.get("grade_muqbil", "") or "",
        # Identifiants
        "hadith_id": row.get("id", ""),
        "hadith_id_dorar": row.get("hadith_id_dorar", "") or "",
        "source_url": row.get("source_url", "") or "",
        # Analyse
        "takhrij": row.get("takhrij", "") or "",
        # Méta
        "zone_id": row.get("zone_id", 0),
        "bm25_rank": row.get("bm25_rank") or row.get("_match_score"),
        "from_local_db": True,
    }
