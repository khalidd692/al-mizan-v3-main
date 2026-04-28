"""Agent 3 — Takhrij (التخريج) : Sources et références du hadith.

Zone 4 : Extraction et référencement complet du hadith.
- Source principale (livre, numéro, grade)
- Sources secondaires (même matn dans autres collections)
- Takhrijat avec grade par source

Implémentation SQL uniquement - pas de LLM.
"""

import sqlite3
import os
from pathlib import Path
from backend.agents.base import BaseAgent
from backend.utils.logging import get_logger

log = get_logger("mizan.agent_takhrij")


def _get_db_path() -> Path:
    db_url = os.getenv("DATABASE_URL", "sqlite:///backend/mizan.db")
    return Path(db_url.replace("sqlite:///", ""))


class AgentTakhrij(BaseAgent):
    AGENT_NAME = "TAKHRIJ"
    ZONES_PRODUCED = [4]

    async def _mock_output(self, hadith_data: dict) -> dict:
        """Mode mock : retourne les données de takhrij basiques du hadith_data."""
        source = hadith_data.get("source", "Source inconnue")
        grade = hadith_data.get("grade_raw", "unknown")
        hadith_id = hadith_data.get("hadith_id", "")

        return {
            "zone_4": {
                "zone": 4,
                "type": "takhrij",
                "source_principale": {
                    "livre": source,
                    "grade": grade,
                    "reference": hadith_data.get("source", ""),
                },
                "sources_secondaires": [],
                "takhrijat": [],
                "mock": True,
            }
        }

    async def _real_output(self, hadith_data: dict) -> dict:
        """Mode réel : enrichit avec les données SQL de la base almizan_v7.db.

        Requêtes :
        1. Source principale détaillée depuis entries
        2. Sources secondaires : même matn (fr_text similaire) dans autres collections
        3. Takhrijat avec grades par source
        """
        hadith_id = hadith_data.get("hadith_id", "")
        fr_text = hadith_data.get("translation_fr", "")
        ar_text = hadith_data.get("matn_clean", "") or hadith_data.get("matn", "")

        db_path = _get_db_path()
        if not db_path.exists():
            log.warning(f"[TAKHRIJ] Base introuvable : {db_path}")
            return await self._mock_output(hadith_data)

        try:
            conn = sqlite3.connect(str(db_path), timeout=10)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # ── 1. Source principale détaillée ─────────────────────
            source_principale = self._get_source_principale(
                cursor, hadith_id, hadith_data
            )

            # ── 2. Sources secondaires (même matn, autres livres) ──
            sources_secondaires = self._get_sources_secondaires(
                cursor, hadith_id, fr_text, ar_text
            )

            # ── 3. Takhrijat avec grades ───────────────────────────
            takhrijat = self._get_takhrijat(cursor, hadith_id)

            conn.close()

            return {
                "zone_4": {
                    "zone": 4,
                    "type": "takhrij",
                    "source_principale": source_principale,
                    "sources_secondaires": sources_secondaires,
                    "takhrijat": takhrijat,
                    "hadith_id": hadith_id,
                    "source": "local_db",
                }
            }

        except sqlite3.Error as exc:
            log.error(f"[TAKHRIJ] Erreur SQLite : {exc}")
            return await self._mock_output(hadith_data)

    def _get_source_principale(
        self, cursor: sqlite3.Cursor, hadith_id: str, hadith_data: dict
    ) -> dict:
        """Récupère la source principale détaillée depuis entries."""
        if not hadith_id:
            return {
                "livre": hadith_data.get("source", "Source inconnue"),
                "grade": hadith_data.get("grade_raw", "unknown"),
                "reference": hadith_data.get("source", ""),
            }

        cursor.execute(
            """
            SELECT book_name_fr, book_name_ar, hadith_number,
                   grade_primary, grade_by_mohdith, grade_albani,
                   grade_ibn_baz, grade_ibn_uthaymin,
                   source_url, takhrij
            FROM entries
            WHERE id = ?
            """,
            (hadith_id,),
        )
        row = cursor.fetchone()

        if not row:
            return {
                "livre": hadith_data.get("source", "Source inconnue"),
                "grade": hadith_data.get("grade_raw", "unknown"),
                "reference": hadith_data.get("source", ""),
            }

        book_fr = row["book_name_fr"] or row["book_name_ar"] or "Source inconnue"
        hadith_num = row["hadith_number"] or ""

        # Compile tous les grades disponibles
        grades = {
            "primary": row["grade_primary"] or "unknown",
            "mohdith": row["grade_by_mohdith"] or "",
            "albani": row["grade_albani"] or "",
            "ibn_baz": row["grade_ibn_baz"] or "",
            "ibn_uthaymin": row["grade_ibn_uthaymin"] or "",
        }

        return {
            "livre": book_fr,
            "numero": hadith_num,
            "reference": f"{book_fr} n°{hadith_num}" if hadith_num else book_fr,
            "grades": grades,
            "grade_principal": row["grade_primary"] or "unknown",
            "source_url": row["source_url"] or "",
            "takhrij": row["takhrij"] or "",
        }

    def _get_sources_secondaires(
        self, cursor: sqlite3.Cursor, hadith_id: str, fr_text: str, ar_text: str
    ) -> list[dict]:
        """Cherche d'autres versions du même matn dans différentes collections.

        Stratégie : cherche des hadiths avec fr_text similaire ou ar_text_clean similaire,
        mais dans des livres différents (ex: même hadith dans Bukhari et Muslim).
        """
        sources = []

        if not (fr_text or ar_text):
            return sources

        # Extrait les 3 premiers mots significatifs du texte français pour la recherche
        search_terms = []
        if fr_text:
            words = [w for w in fr_text.lower().split() if len(w) > 3][:3]
            search_terms.extend(words)

        if not search_terms:
            return sources

        # Construit la clause LIKE pour chaque terme
        like_clauses = " OR ".join(["fr_text LIKE ?"] * len(search_terms))
        like_params = [f"%{term}%" for term in search_terms]

        # Exclut le hadith actuel et cherche dans d'autres livres
        sql = f"""
            SELECT id, book_name_fr, book_name_ar, hadith_number,
                   fr_text, grade_primary
            FROM entries
            WHERE ({like_clauses})
            AND id != ?
            AND fr_text IS NOT NULL
            LIMIT 10
        """
        params = like_params + [hadith_id or ""]

        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            seen_books = set()
            for row in rows:
                book = row["book_name_fr"] or row["book_name_ar"] or ""
                if not book:
                    continue

                # Évite les doublons de livres
                book_key = book.lower()
                if book_key in seen_books:
                    continue
                seen_books.add(book_key)

                sources.append({
                    "id": row["id"],
                    "livre": book,
                    "numero": row["hadith_number"] or "",
                    "grade": row["grade_primary"] or "unknown",
                    "texte": (row["fr_text"] or "")[:150] + "..."
                    if len(row["fr_text"] or "") > 150
                    else (row["fr_text"] or ""),
                })

        except sqlite3.Error as exc:
            log.error(f"[TAKHRIJ] Erreur recherche sources secondaires : {exc}")

        return sources[:5]  # Max 5 sources secondaires

    def _get_takhrijat(self, cursor: sqlite3.Cursor, hadith_id: str) -> list[dict]:
        """Récupère les takhrijat (références croisées) avec grades par source.

        Pour l'instant, extrait les informations depuis les champs de la table entries.
        Future : pourrait utiliser une table cross_refs dédiée.
        """
        takhrijat = []

        if not hadith_id:
            return takhrijat

        # Récupère les données brutes du hadith pour construire les takhrijat
        cursor.execute(
            """
            SELECT book_name_fr, book_name_ar, hadith_number,
                   grade_primary, grade_by_mohdith, grade_albani,
                   grade_ibn_baz, grade_ibn_uthaymin, grade_explanation,
                   takhrij
            FROM entries
            WHERE id = ?
            """,
            (hadith_id,),
        )
        row = cursor.fetchone()

        if not row:
            return takhrijat

        # Construit la liste des takhrijat basée sur les grades des savants
        book = row["book_name_fr"] or row["book_name_ar"] or "Source"
        hadith_num = row["hadith_number"] or ""

        # Takhrij principal (source primaire)
        if row["grade_primary"]:
            takhrijat.append({
                "source": book,
                "reference": f"{book} n°{hadith_num}" if hadith_num else book,
                "grade": row["grade_primary"],
                "auteur": "Muhaddith principal",
            })

        # Takhrij Albani
        if row["grade_albani"]:
            takhrijat.append({
                "source": "Sahih al-Jami' / Irwa'",
                "grade": row["grade_albani"],
                "auteur": "Al-Albani",
                "reference": row["takhrij"] or "",
            })

        # Takhrij Ibn Baz
        if row["grade_ibn_baz"]:
            takhrijat.append({
                "source": "Majmu' Fatawa",
                "grade": row["grade_ibn_baz"],
                "auteur": "Ibn Baz",
            })

        # Takhrij Ibn Uthaymin
        if row["grade_ibn_uthaymin"]:
            takhrijat.append({
                "source": "Sharh Riyad as-Salihin / Fatawa",
                "grade": row["grade_ibn_uthaymin"],
                "auteur": "Ibn Uthaymin",
            })

        return takhrijat
