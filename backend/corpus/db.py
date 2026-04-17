"""Al-Mīzān v5.0 — Gestionnaire Base de Données SQLite."""

import sqlite3
import aiosqlite
import pathlib
from typing import Optional, List, Dict, Any
from datetime import datetime

from backend.utils.logging import get_logger

log = get_logger("mizan.corpus.db")

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DB_PATH = _REPO_ROOT / "corpus" / "corpus.db"
SCHEMA_PATH = _REPO_ROOT / "backend" / "corpus" / "schema.sql"

class CorpusDB:
    """Gestionnaire async de la base de données corpus."""
    
    def __init__(self, db_path: pathlib.Path = DB_PATH):
        self.db_path = db_path
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Crée la base de données et applique le schéma si nécessaire."""
        if not self.db_path.exists():
            log.info(f"[DB] Création base de données: {self.db_path}")
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Créer la base avec le schéma
            conn = sqlite3.connect(str(self.db_path))
            with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
                schema = f.read()
            conn.executescript(schema)
            conn.commit()
            conn.close()
            log.info("[DB] Base de données créée avec succès")
        else:
            log.debug(f"[DB] Base de données existante: {self.db_path}")
    
    async def insert_raw_hadith(
        self,
        dorar_id: str,
        matn_ar: str,
        source: Optional[str] = None,
        grade_raw: Optional[str] = None,
        rawi: Optional[str] = None
    ) -> int:
        """Insère un hadith brut depuis Dorar.net.
        
        Returns:
            ID du hadith inséré, ou -1 si déjà existant
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            try:
                cursor = await db.execute(
                    """
                    INSERT INTO hadiths_raw (dorar_id, matn_ar, source, grade_raw, rawi)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (dorar_id, matn_ar, source, grade_raw, rawi)
                )
                await db.commit()
                hadith_id = cursor.lastrowid
                log.debug(f"[DB] Hadith brut inséré: ID={hadith_id}, dorar_id={dorar_id}")
                return hadith_id
            except sqlite3.IntegrityError:
                log.warning(f"[DB] Hadith déjà existant: dorar_id={dorar_id}")
                return -1
    
    async def get_unprocessed_hadiths(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère les hadiths non traités."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM hadiths_raw WHERE processed = 0 LIMIT ?",
                (limit,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def mark_as_processed(self, hadith_id: int):
        """Marque un hadith comme traité."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute(
                "UPDATE hadiths_raw SET processed = 1 WHERE id = ?",
                (hadith_id,)
            )
            await db.commit()
            log.debug(f"[DB] Hadith marqué comme traité: ID={hadith_id}")
    
    async def insert_validated_hadith(
        self,
        hadith_raw_id: int,
        matn_ar: str,
        translation_fr: str,
        grade_normalized: str,
        scholar_verdict: str,
        scholar_location: str,
        confidence_score: float,
        agent_isnad_output: str,
        agent_ilal_output: str,
        agent_matn_output: str,
        agent_tarjih_output: str
    ) -> int:
        """Insère un hadith validé après pipeline agents."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute(
                """
                INSERT INTO hadiths_validated (
                    hadith_raw_id, matn_ar, translation_fr, grade_normalized,
                    scholar_verdict, scholar_location, confidence_score,
                    agent_isnad_output, agent_ilal_output, agent_matn_output, agent_tarjih_output
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    hadith_raw_id, matn_ar, translation_fr, grade_normalized,
                    scholar_verdict, scholar_location, confidence_score,
                    agent_isnad_output, agent_ilal_output, agent_matn_output, agent_tarjih_output
                )
            )
            await db.commit()
            validated_id = cursor.lastrowid
            log.info(f"[DB] Hadith validé inséré: ID={validated_id}, confiance={confidence_score:.1f}%")
            return validated_id
    
    async def insert_pending_review(
        self,
        hadith_raw_id: int,
        reason: str,
        confidence_score: float,
        agent_outputs: str
    ) -> int:
        """Insère un hadith en attente de review manuelle."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute(
                """
                INSERT INTO pending_review (hadith_raw_id, reason, confidence_score, agent_outputs)
                VALUES (?, ?, ?, ?)
                """,
                (hadith_raw_id, reason, confidence_score, agent_outputs)
            )
            await db.commit()
            review_id = cursor.lastrowid
            log.warning(f"[DB] Hadith en review: ID={review_id}, raison={reason}, confiance={confidence_score:.1f}%")
            return review_id
    
    async def get_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques globales."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM v_stats")
            row = await cursor.fetchone()
            return dict(row) if row else {}
    
    async def get_hadith_by_id(self, hadith_id: int) -> Optional[Dict[str, Any]]:
        """Récupère un hadith brut par son ID."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM hadiths_raw WHERE id = ?",
                (hadith_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def search_validated_hadiths(
        self,
        query: str,
        grade: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Recherche dans les hadiths validés."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            
            if grade:
                cursor = await db.execute(
                    """
                    SELECT * FROM hadiths_validated 
                    WHERE (matn_ar LIKE ? OR translation_fr LIKE ?)
                    AND grade_normalized = ?
                    ORDER BY confidence_score DESC
                    LIMIT ?
                    """,
                    (f"%{query}%", f"%{query}%", grade, limit)
                )
            else:
                cursor = await db.execute(
                    """
                    SELECT * FROM hadiths_validated 
                    WHERE matn_ar LIKE ? OR translation_fr LIKE ?
                    ORDER BY confidence_score DESC
                    LIMIT ?
                    """,
                    (f"%{query}%", f"%{query}%", limit)
                )
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]