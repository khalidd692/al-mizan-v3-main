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

log = get_logger("mizan.local_db")

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
    db_path = _get_db_path()
    if not db_path.exists():
        log.warning(f"[LOCAL_DB] Base introuvable : {db_path}")
        return []

    clean = _strip_tashkeel(query)
    tokens = [t for t in re.split(r"\s+", clean) if len(t) > 2][:6]
    if not tokens:
        log.warning(f"[LOCAL_DB] Requête trop courte après nettoyage : {query!r}")
        return []

    clauses, params = [], []
    for token in tokens:
        like = f"%{token}%"
        clauses.append(
            "(ar_text_clean LIKE ? OR ar_text LIKE ? OR fr_text LIKE ? OR book_name_ar LIKE ?)"
        )
        params.extend([like, like, like, like])

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

        # ── Score de pertinence : trier par nombre de tokens matchés ──────
        # BUGFIX: Le résultat doit correspondre au hadith le PLUS proche de la
        # requête, pas le premier SQL. On trie par nombre de tokens matchés
        # décroissant. Pas de filtre 30% - tous les résultats sont retournés.
        def _score(row: dict) -> tuple[int, float]:
            """Retourne (tokens_matchés, ratio) pour tri et filtrage."""
            fr = (row.get("fr_text") or "").lower()
            ar = row.get("ar_text_clean") or row.get("ar_text") or ""
            matched = sum(
                1 for t in tokens
                if t.lower() in fr or t in ar
            )
            return matched, matched / len(tokens)

        # Calculer le score pour chaque résultat
        scored_results = []
        for r in results:
            matched_count, ratio = _score(r)
            r["_match_score"] = matched_count
            r["_match_ratio"] = ratio
            scored_results.append((matched_count, r))

        # Trier par nombre de tokens matchés décroissant (pertinence réelle)
        scored_results.sort(key=lambda x: x[0], reverse=True)

        # Retourner tous les résultats triés (pas de filtre 30%)
        sorted_results = [r for count, r in scored_results]

        # Logger le grade brut récupéré pour le premier résultat (le plus pertinent)
        if sorted_results:
            first = sorted_results[0]
            log.info(
                f"[LOCAL_DB] {len(sorted_results)} résultat(s) pour {query!r} "
                f"| Meilleur match: grade_primary={first.get('grade_primary', 'NULL')} "
                f"(tokens_matchés={first.get('_match_score')}/{len(tokens)})"
            )
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
