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
        log.info(f"[LOCAL_DB] {len(results)} résultat(s) pour {query!r}")
        return results
    except sqlite3.Error as exc:
        log.error(f"[LOCAL_DB] Erreur SQLite : {exc}")
        return []


def row_to_hadith_core(row: dict) -> dict:
    """Convertit une ligne `entries` en format hadith_data standard pour les agents."""
    book = row.get("book_name_fr") or row.get("book_name_ar") or "Source inconnue"
    num = row.get("hadith_number", "")
    source_label = f"{book} n°{num}" if num else book
    return {
        "matn": row.get("ar_text", ""),
        "matn_clean": row.get("ar_text_clean", ""),
        "narrator": row.get("ar_narrator", ""),
        "full_isnad": row.get("ar_full_isnad", ""),
        "translation_fr": row.get("fr_text") or row.get("fr_summary", ""),
        "source": source_label,
        "grade_raw": row.get("grade_primary", "unknown"),
        "grade_by": row.get("grade_by_mohdith", ""),
        "grade_explanation": row.get("grade_explanation", ""),
        "grade_albani": row.get("grade_albani", ""),
        "hadith_id": row.get("id", ""),
        "hadith_id_dorar": row.get("hadith_id_dorar", ""),
        "source_url": row.get("source_url", ""),
        "takhrij": row.get("takhrij", ""),
        "zone_id": row.get("zone_id", 0),
        "from_local_db": True,
    }
