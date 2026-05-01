"""
enrich_ar_text.py
=================
Remplit ar_text (et ar_text_clean) depuis hadith-json/db/by_book/.
Mode UPDATE uniquement — aucun INSERT, jamais de nouvelle ligne.

Logique :
  - Charge chaque JSON source en mémoire (index : idInBook → arabic)
  - Pour chaque entrée DB dont ar_text est un placeholder ou NULL,
    cherche le texte arabe via (book_name_fr, hadith_number)
  - UPDATE ar_text + ar_text_clean si trouvé
  - N'écrase PAS un ar_text déjà réel (heuristique : non-placeholder)

Usage :
  python backend/scripts/enrich_ar_text.py             # dry-run
  python backend/scripts/enrich_ar_text.py --apply     # applique
"""

import argparse
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

# ── Chemins ──────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "backend" / "database" / "almizan_v7.db"
BY_BOOK = ROOT / "backend" / "corpus" / "hadith-json" / "db" / "by_book"

# ── Mapping book_name_fr (DB) → chemin JSON relatif à BY_BOOK ────────────────
BOOK_MAP = {
    "Sahih al-Bukhari":      "the_9_books/bukhari.json",
    "Sahih Muslim":          "the_9_books/muslim.json",
    "Sunan an-Nasai":        "the_9_books/nasai.json",
    "Sunan Abu Dawud":       "the_9_books/abudawud.json",
    "Sunan Ibn Majah":       "the_9_books/ibnmajah.json",
    "Muwatta Malik":         "the_9_books/malik.json",
    "40 Hadiths de Nawawi":  "forties/nawawi40.json",
    "40 Hadiths de Dehlawi": "forties/shahwaliullah40.json",
    "40 Hadiths Qudsi":      "forties/qudsi40.json",
}

# Regex : détecte les placeholders générés ("حديث رقم 1", "hadith n 1", etc.)
PLACEHOLDER_RX = re.compile(
    r"^(حديث\s+رقم\s*\d+|hadith\s+(n[°o]?\.?\s*)?\d+)$",
    re.IGNORECASE | re.UNICODE,
)

# Diacritiques arabes (tashkeel) à retirer pour ar_text_clean
TASHKEEL_RX = re.compile(
    r"[\u064B-\u065F\u0610-\u061A\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]"
)


def strip_tashkeel(text: str) -> str:
    return TASHKEEL_RX.sub("", text).strip()


def is_placeholder(text: str | None) -> bool:
    if text is None:
        return True
    return bool(PLACEHOLDER_RX.match(text.strip()))


def load_book_index(json_path: Path) -> dict[int, str]:
    """Retourne {idInBook: arabic_text} pour un fichier by_book."""
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    hadiths = data.get("hadiths", [])
    index = {}
    for h in hadiths:
        num = h.get("idInBook")
        arabic = (h.get("arabic") or "").strip()
        if num is not None and arabic:
            try:
                index[int(num)] = arabic
            except (ValueError, TypeError):
                pass
    return index


def run(apply: bool):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*62}")
    print(f"  enrich_ar_text.py — mode: {'APPLY' if apply else 'DRY-RUN'}")
    print(f"  DB     : {DB_PATH}")
    print(f"  Source : {BY_BOOK}")
    print(f"  Date   : {ts}")
    print(f"{'='*62}\n")

    # ── Charger tous les index JSON ───────────────────────────────────────────
    print("[1/4] Chargement des fichiers by_book …")
    book_indexes: dict[str, dict[int, str]] = {}
    for book_name_fr, rel_path in BOOK_MAP.items():
        fpath = BY_BOOK / rel_path
        if not fpath.exists():
            print(f"  [WARN] Fichier manquant : {fpath}")
            continue
        idx = load_book_index(fpath)
        book_indexes[book_name_fr] = idx
        print(f"  ✓ {book_name_fr:<30s}  {len(idx):>6,} hadiths indexés")
    print()

    # ── Connexion + lecture DB ────────────────────────────────────────────────
    print("[2/4] Lecture des entrées DB …")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, book_name_fr, hadith_number, ar_text
        FROM entries
    """)
    db_rows = cur.fetchall()
    print(f"      → {len(db_rows):,} entrées lues\n")

    # ── Matching ──────────────────────────────────────────────────────────────
    print("[3/4] Matching …")
    stats = {
        "placeholder":   0,
        "already_real":  0,
        "book_unknown":  0,
        "num_invalid":   0,
        "not_in_json":   0,
        "to_update":     0,
    }

    updates: list[dict] = []

    for row in db_rows:
        ar_current = row["ar_text"]

        if not is_placeholder(ar_current):
            stats["already_real"] += 1
            continue

        stats["placeholder"] += 1

        book_fr = row["book_name_fr"]
        if book_fr not in book_indexes:
            stats["book_unknown"] += 1
            continue

        try:
            num = int(str(row["hadith_number"]).strip())
        except (ValueError, TypeError):
            stats["num_invalid"] += 1
            continue

        arabic = book_indexes[book_fr].get(num)
        if not arabic:
            stats["not_in_json"] += 1
            continue

        stats["to_update"] += 1
        updates.append({
            "id":            row["id"],
            "ar_text":       arabic,
            "ar_text_clean": strip_tashkeel(arabic),
        })

    print(f"      Placeholders détectés   : {stats['placeholder']:>6,}")
    print(f"      Déjà texte réel         : {stats['already_real']:>6,}")
    print(f"      Livre inconnu           : {stats['book_unknown']:>6,}")
    print(f"      Numéro invalide         : {stats['num_invalid']:>6,}")
    print(f"      Introuvable dans JSON   : {stats['not_in_json']:>6,}")
    print(f"      ─────────────────────────────────")
    print(f"      → UPDATE prévus         : {stats['to_update']:>6,}\n")

    if not updates:
        print("Aucune mise à jour nécessaire.")
        conn.close()
        return

    # ── Aperçu dry-run ───────────────────────────────────────────────────────
    if not apply:
        print("APERÇU (10 premières lignes) :")
        print(f"  {'id':<20s}  {'ar_text (60 premiers chars)':60s}")
        print(f"  {'-'*20}  {'-'*60}")
        for u in updates[:10]:
            print(f"  {u['id']:<20s}  {u['ar_text'][:60]}")
        print(f"\n[DRY-RUN] Aucune écriture. Relancez avec --apply pour valider.")
        conn.close()
        return

    # ── Application des UPDATE ────────────────────────────────────────────────
    print(f"[4/4] Application de {len(updates):,} UPDATE …")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    applied = 0

    conn.execute("BEGIN")
    try:
        for u in updates:
            conn.execute(
                """UPDATE entries
                   SET ar_text = ?,
                       ar_text_clean = ?,
                       updated_at = ?
                   WHERE id = ?""",
                (u["ar_text"], u["ar_text_clean"], now, u["id"]),
            )
            applied += 1

        conn.commit()
        print(f"\n✓ {applied:,} entrées mises à jour avec succès.\n")

    except Exception as e:
        conn.rollback()
        print(f"\n✗ ERREUR — rollback effectué : {e}")
        conn.close()
        raise

    conn.close()

    # ── Rapport final ─────────────────────────────────────────────────────────
    print(f"{'='*62}")
    print("  RAPPORT FINAL")
    print(f"{'='*62}")
    print(f"  Entrées totales en DB   : {len(db_rows):,}")
    print(f"  Placeholders trouvés    : {stats['placeholder']:,}")
    print(f"  ar_text enrichis        : {applied:,}")
    print(f"  Non couverts (JSON)     : {stats['not_in_json']:,}")
    print(f"  Livre non mappé         : {stats['book_unknown']:,}")
    print(f"  Source                  : hadith-json/db/by_book/")
    print(f"{'='*62}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Enrichit ar_text depuis hadith-json/by_book (UPDATE uniquement)"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Applique les UPDATE (sans --apply = dry-run)",
    )
    args = parser.parse_args()
    run(apply=args.apply)
