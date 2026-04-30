#!/usr/bin/env python3
"""
migrate_fts.py — Crée et peuple la table FTS5 depuis `entries`.

Usage : python backend/migrate_fts.py
Idempotent : peut être relancé sans risque (rebuild complet à chaque fois).
"""

import os
import sqlite3
import sys
from pathlib import Path


# Détection auto du chemin DB
DB_PATH = Path(os.environ.get(
    "DATABASE_URL", "sqlite:///backend/database/almizan_v7.db"
).replace("sqlite:///", "").replace("sqlite://", ""))


def migrate():
    """Crée la table FTS5 et la peuple depuis entries."""
    if not DB_PATH.exists():
        print(f"[FTS5] ERREUR: Base introuvable: {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # 1. Supprimer et recréer la table FTS5 - UNIQUEMENT FRANÇAIS
    # ar_text et ar_text_clean retirés car ils ne contiennent que des placeholders
    cur.execute("DROP TABLE IF EXISTS entries_fts")
    cur.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
            entries_id UNINDEXED,
            fr_text,
            fr_summary,
            ar_narrator,
            book_name_ar,
            book_name_fr,
            tokenize='unicode61 remove_diacritics 2'
        );
    """)
    print("[FTS5] Table entries_fts créée (index français uniquement)")

    # 2. Peuplement initial depuis entries
    print("[FTS5] Peuplement de l'index...")
    
    # Supprimer les triggers existants
    cur.execute("DROP TRIGGER IF EXISTS entries_fts_insert")
    cur.execute("DROP TRIGGER IF EXISTS entries_fts_update")  
    cur.execute("DROP TRIGGER IF EXISTS entries_fts_delete")
    
    # Insérer uniquement les colonnes françaises pertinentes
    cur.execute("""
        INSERT INTO entries_fts(entries_id, fr_text, fr_summary, ar_narrator, book_name_ar, book_name_fr)
        SELECT 
            id,
            COALESCE(fr_text, ''),
            COALESCE(fr_summary, ''),
            COALESCE(ar_narrator, ''),
            COALESCE(book_name_ar, ''),
            COALESCE(book_name_fr, '')
        FROM entries
        WHERE fr_text IS NOT NULL
    """)
    print(f"[FTS5] {cur.rowcount} lignes insérées")

    # 3. Note: Pas de triggers pour l'instant - la synchronisation se fait
    # via migration complète (rapide sur ~26k entrées)
    # Pour ajouts incrémentaux, relancer migrate_fts.py
    print("[FTS5] Note: Synchronisation par migration complète (pas de triggers)")

    # 4. Optimiser l'index
    try:
        cur.execute("INSERT INTO entries_fts(entries_fts) VALUES('optimize');")
        print("[FTS5] Index optimisé")
    except:
        pass

    # 5. Vérification
    count = cur.execute("SELECT COUNT(*) FROM entries_fts").fetchone()[0]
    entries_count = cur.execute("SELECT COUNT(*) FROM entries").fetchone()[0]

    conn.commit()
    conn.close()

    print(f"[FTS5] ✓ Migration terminée: {count} entrées indexées (sur {entries_count} dans entries)")

    if count == 0 and entries_count > 0:
        print("[FTS5] ⚠️ AVERTISSEMENT: L'index est vide mais entries contient des données!")
        print("[FTS5] Relancez avec: python backend/migrate_fts.py --force")
        sys.exit(1)

    return 0


def force_repopulate():
    """Force le repeuplement complet (si rebuild échoue)."""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # Supprimer et recréer
    cur.execute("DROP TABLE IF EXISTS entries_fts")
    conn.commit()
    conn.close()

    # Relancer la migration normale
    return migrate()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Migration FTS5 pour Al-Mīzān")
    parser.add_argument("--force", action="store_true", help="Force le repeuplement complet")
    args = parser.parse_args()

    if args.force:
        sys.exit(force_repopulate())
    else:
        sys.exit(migrate())
