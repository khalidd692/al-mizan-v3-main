"""
create_fts5_index.py
====================
Crée une table FTS5 virtuelle sur entries(ar_text_clean, fr_text).
Mode UPDATE uniquement — ne touche pas à la table entries.

Table créée : entries_fts  (virtuelle FTS5, shadow tables gérés par SQLite)

Colonnes indexées :
  - ar_text_clean  (texte arabe sans tashkeel)
  - fr_text        (texte français)
  - id             (colonne de contenu, non indexée, pour retrouver la ligne)

Type : content table → lit entries en live, pas de copie de données.
Tokenizer : unicode61 remove_diacritics 1  (normalise les diacritiques restants)

Usage :
  python backend/scripts/create_fts5_index.py           # dry-run
  python backend/scripts/create_fts5_index.py --apply   # crée l'index
  python backend/scripts/create_fts5_index.py --apply --test  # + test niyyat
"""

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT    = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "backend" / "database" / "almizan_v7.db"


def check_fts5(conn: sqlite3.Connection) -> bool:
    """Vérifie que FTS5 est disponible dans cette build SQLite."""
    try:
        conn.execute("CREATE VIRTUAL TABLE _fts5_probe USING fts5(x)")
        conn.execute("DROP TABLE _fts5_probe")
        return True
    except sqlite3.OperationalError:
        return False


def fts_table_exists(conn: sqlite3.Connection) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='entries_fts'"
    )
    return cur.fetchone() is not None


def run(apply: bool, test: bool):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*62}")
    print(f"  create_fts5_index.py — mode: {'APPLY' if apply else 'DRY-RUN'}")
    print(f"  DB   : {DB_PATH}")
    print(f"  Date : {ts}")
    print(f"{'='*62}\n")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")

    # ── Vérifier FTS5 ─────────────────────────────────────────────────────────
    print("[1/4] Vérification FTS5 …")
    if not check_fts5(conn):
        print("  ✗ FTS5 non disponible dans cette build SQLite.")
        print("    Solution : mettre à jour SQLite (>= 3.20) ou installer pysqlite3.")
        conn.close()
        sys.exit(1)
    ver = sqlite3.sqlite_version
    print(f"  ✓ FTS5 disponible  (SQLite {ver})\n")

    # ── Vérifier état actuel ──────────────────────────────────────────────────
    print("[2/4] Vérification état DB …")
    already = fts_table_exists(conn)
    if already:
        print("  → Table entries_fts déjà présente.")
        if not apply:
            print("  [DRY-RUN] Rien à faire. Ajoutez --apply pour reconstruire.")
        else:
            print("  Suppression de l'ancienne table FTS5 …")

    cur = conn.execute("SELECT COUNT(*) FROM entries")
    total = cur.fetchone()[0]
    cur = conn.execute(
        "SELECT COUNT(*) FROM entries WHERE ar_text_clean IS NOT NULL AND ar_text_clean != ''"
    )
    ar_ok = cur.fetchone()[0]
    cur = conn.execute(
        "SELECT COUNT(*) FROM entries WHERE fr_text IS NOT NULL AND fr_text != ''"
    )
    fr_ok = cur.fetchone()[0]

    print(f"  Total entries          : {total:,}")
    print(f"  ar_text_clean rempli   : {ar_ok:,}")
    print(f"  fr_text rempli         : {fr_ok:,}")

    if not apply:
        print(f"\n[DRY-RUN] Plan :")
        print(f"  1. DROP TABLE IF EXISTS entries_fts (+ shadow tables)")
        print(f"  2. CREATE VIRTUAL TABLE entries_fts USING fts5(")
        print(f"       ar_text_clean, fr_text,")
        print(f"       content='entries', content_rowid='rowid',")
        print(f"       tokenize='unicode61 remove_diacritics 1'")
        print(f"     )")
        print(f"  3. INSERT INTO entries_fts(entries_fts) VALUES('rebuild')")
        print(f"     → popule l'index avec {total:,} lignes")
        print(f"  4. INSERT INTO entries_fts(entries_fts) VALUES('optimize')")
        print(f"\n[DRY-RUN] Aucune écriture. Relancez avec --apply pour créer.")
        conn.close()
        return

    # ── Création / reconstruction ─────────────────────────────────────────────
    print(f"\n[3/4] Création de la table FTS5 …")

    conn.execute("BEGIN")
    try:
        if already:
            # Supprimer proprement (FTS5 crée des shadow tables)
            conn.execute("DROP TABLE IF EXISTS entries_fts")

        conn.execute("""
            CREATE VIRTUAL TABLE entries_fts USING fts5(
                ar_text_clean,
                fr_text,
                content='entries',
                content_rowid='rowid',
                tokenize='unicode61 remove_diacritics 1'
            )
        """)
        print("  ✓ Table entries_fts créée")

        print(f"  Rebuild de l'index ({total:,} lignes) …")
        conn.execute("INSERT INTO entries_fts(entries_fts) VALUES('rebuild')")
        print("  ✓ Rebuild terminé")

        print("  Optimisation …")
        conn.execute("INSERT INTO entries_fts(entries_fts) VALUES('optimize')")
        print("  ✓ Index optimisé")

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"  ✗ ERREUR — rollback : {e}")
        conn.close()
        raise

    # ── Vérification taille index (via page_count PRAGMA) ────────────────────
    try:
        cur = conn.execute("PRAGMA page_count")
        pages = cur.fetchone()[0]
        cur = conn.execute("PRAGMA page_size")
        psize = cur.fetchone()[0]
        print(f"  DB totale              : {pages * psize / 1024 / 1024:.2f} MB\n")
    except Exception:
        print()

    # ── Test FTS5 ─────────────────────────────────────────────────────────────
    print("[4/4] Tests de validation …")

    # Test 1 : niyyāt en arabe
    print()
    print("  TEST 1 — arabe : إنما الأعمال بالنيات")
    cur = conn.execute("""
        SELECT e.id, e.book_name_fr, e.hadith_number, e.grade_primary,
               snippet(entries_fts, 0, '>>>', '<<<', '…', 15) AS snip_ar
        FROM entries_fts
        JOIN entries e ON e.rowid = entries_fts.rowid
        WHERE entries_fts MATCH 'ar_text_clean : "انما الاعمال بالنيات"'
        LIMIT 5
    """)
    hits = cur.fetchall()
    if hits:
        for h in hits:
            print(f"  ✓ {h[0]:<12s} {h[1]} n°{h[2]} [{h[3]}]")
            print(f"    {h[4][:100]}")
    else:
        # Fallback : recherche tokenisée simple
        cur = conn.execute("""
            SELECT e.id, e.book_name_fr, e.hadith_number, e.grade_primary,
                   snippet(entries_fts, 0, '>>>', '<<<', '…', 10) AS snip_ar
            FROM entries_fts
            JOIN entries e ON e.rowid = entries_fts.rowid
            WHERE entries_fts MATCH 'ar_text_clean : الاعمال النيات'
            LIMIT 5
        """)
        hits = cur.fetchall()
        if hits:
            for h in hits:
                print(f"  ✓ {h[0]:<12s} {h[1]} n°{h[2]} [{h[3]}]")
                print(f"    {h[4][:100]}")
        else:
            print("  ✗ Aucun résultat — vérifier ar_text_clean")

    # Test 2 : français "intention"
    print()
    print("  TEST 2 — français : intention")
    cur = conn.execute("""
        SELECT e.id, e.book_name_fr, e.hadith_number,
               snippet(entries_fts, 1, '>>>', '<<<', '…', 10) AS snip_fr
        FROM entries_fts
        JOIN entries e ON e.rowid = entries_fts.rowid
        WHERE entries_fts MATCH 'fr_text : intention'
        ORDER BY rank
        LIMIT 5
    """)
    hits = cur.fetchall()
    if hits:
        for h in hits:
            print(f"  ✓ {h[0]:<12s} {h[1]} n°{h[2]}")
            print(f"    {h[3][:100]}")
    else:
        print("  ✗ Aucun résultat")

    # Test 3 : vérifier dorar-1 directement
    print()
    print("  TEST 3 — dorar-1 direct via FTS")
    cur = conn.execute("""
        SELECT e.id, e.book_name_fr, e.hadith_number, e.ar_text_clean
        FROM entries e
        WHERE e.id = 'dorar-1'
    """)
    r = cur.fetchone()
    if r:
        # Chercher un token distinctif du matn (بالنيات)
        cur2 = conn.execute("""
            SELECT e.id, e.book_name_fr, e.hadith_number
            FROM entries_fts
            JOIN entries e ON e.rowid = entries_fts.rowid
            WHERE entries_fts MATCH 'ar_text_clean : بالنيات'
            LIMIT 3
        """)
        hits2 = cur2.fetchall()
        print(f"  dorar-1 ar_text_clean (50 chars) : {r[3][:50] if r[3] else 'NULL'}")
        print(f"  Recherche 'بالنيات' → {len(hits2)} résultat(s)")
        for h in hits2:
            print(f"    ✓ {h[0]} | {h[1]} n°{h[2]}")

    conn.close()
    print(f"\n{'='*62}")
    print("  FTS5 INDEX OPÉRATIONNEL")
    print(f"{'='*62}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Crée l'index FTS5 sur entries(ar_text_clean, fr_text)"
    )
    parser.add_argument("--apply", action="store_true", default=False)
    parser.add_argument("--test",  action="store_true", default=False,
                        help="Lance les tests même en dry-run (lecture seule)")
    args = parser.parse_args()
    run(apply=args.apply, test=args.test)
