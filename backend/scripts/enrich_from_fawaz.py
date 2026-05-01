"""
enrich_from_fawaz.py
====================
Mode ENRICHISSEMENT UNIQUEMENT — aucun INSERT, uniquement des UPDATE.

Sources utilisées :
  1. fawazahmed0_fr_dump.json  → fr_text, grade_primary, grade_albani
  2. (futur) hadith-json/by_book → ar_text (à activer séparément)

Clé de correspondance : book_name_fr (normalisé) + hadith_number (entier)

Usage :
  python backend/scripts/enrich_from_fawaz.py             # dry-run (aucune écriture)
  python backend/scripts/enrich_from_fawaz.py --apply     # applique les mises à jour
"""

import argparse
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

# ── Chemins ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
DB_PATH   = ROOT / "backend" / "database" / "almizan_v7.db"
FAWAZ_PATH = ROOT / "fawazahmed0_fr_dump.json"

# ── Correspondance clé fawaz → book_name_fr DB ───────────────────────────────
FAWAZ_BOOK_MAP = {
    "fra-bukhari":  "Sahih al-Bukhari",
    "fra-muslim":   "Sahih Muslim",
    "fra-nasai":    "Sunan an-Nasai",
    "fra-abudawud": "Sunan Abu Dawud",
    "fra-ibnmajah": "Sunan Ibn Majah",
    "fra-malik":    "Muwatta Malik",
    "fra-nawawi":   "40 Hadiths de Nawawi",
    "fra-dehlawi":  "40 Hadiths de Dehlawi",
    "fra-qudsi":    "40 Hadiths Qudsi",
}


def normalize_num(v) -> int | None:
    """Convertit hadithnumber (str ou int) en int, ou None si invalide."""
    try:
        return int(str(v).strip())
    except (ValueError, TypeError):
        return None


def extract_grade(grades_field) -> str | None:
    """
    Extrait le grade primaire depuis le champ `grades` de fawaz.
    grades peut être :  [{"name":"Al-Albani","grade":"Sahih"}, ...]
                     ou une string directe
    """
    if not grades_field:
        return None
    if isinstance(grades_field, str):
        return grades_field.strip() or None
    if isinstance(grades_field, list) and grades_field:
        # Premier grade de la liste
        g = grades_field[0]
        if isinstance(g, dict):
            return g.get("grade") or None
        return str(g) or None
    return None


def extract_albani_grade(grades_field) -> str | None:
    """Cherche spécifiquement le grade d'Al-Albani dans la liste."""
    if not isinstance(grades_field, list):
        return None
    for g in grades_field:
        if isinstance(g, dict):
            name = (g.get("name") or "").lower()
            if "albani" in name or "al-albani" in name:
                return g.get("grade") or None
    return None


def build_fawaz_index(fawaz_path: Path) -> dict:
    """
    Charge fawazahmed0_fr_dump.json et retourne un index plat :
        {(book_name_fr, hadith_number_int): {"fr_text": ..., "grade": ..., "albani": ...}}
    """
    with fawaz_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    index = {}
    for fawaz_key, book_data in raw.items():
        db_book_name = FAWAZ_BOOK_MAP.get(fawaz_key)
        if not db_book_name:
            print(f"  [WARN] Clé fawaz non mappée: {fawaz_key!r} — ignorée")
            continue

        hadiths = book_data.get("hadiths", []) if isinstance(book_data, dict) else book_data
        if not isinstance(hadiths, list):
            continue

        for h in hadiths:
            num = normalize_num(h.get("hadithnumber") or h.get("number"))
            if num is None:
                continue
            fr_text  = (h.get("text") or "").strip() or None
            grade    = extract_grade(h.get("grades"))
            albani   = extract_albani_grade(h.get("grades"))
            index[(db_book_name, num)] = {
                "fr_text": fr_text,
                "grade":   grade,
                "albani":  albani,
            }

    return index


def run(apply: bool):
    print(f"\n{'='*60}")
    print(f"  enrich_from_fawaz.py — mode: {'APPLY' if apply else 'DRY-RUN'}")
    print(f"  DB     : {DB_PATH}")
    print(f"  Source : {FAWAZ_PATH}")
    print(f"  Date   : {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"{'='*60}\n")

    # ── Chargement index fawaz ────────────────────────────────────────────────
    print("[1/3] Chargement fawazahmed0_fr_dump.json …")
    fawaz = build_fawaz_index(FAWAZ_PATH)
    print(f"      → {len(fawaz):,} entrées indexées (book, hadith_number)\n")

    # ── Connexion DB ──────────────────────────────────────────────────────────
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()

    # ── Chargement toutes les entrées DB ──────────────────────────────────────
    print("[2/3] Lecture des entrées DB …")
    cur.execute("""
        SELECT id, book_name_fr, hadith_number,
               fr_text, grade_primary, grade_albani
        FROM entries
    """)
    db_rows = cur.fetchall()
    print(f"      → {len(db_rows):,} entrées lues\n")

    # ── Matching + préparation des UPDATE ─────────────────────────────────────
    stats = {
        "matched":        0,
        "not_found":      0,
        "upd_fr_text":    0,
        "upd_grade":      0,
        "upd_albani":     0,
        "skipped_full":   0,   # entrée déjà complète
    }

    updates = []   # liste de (id, fr_text, grade_primary, grade_albani)

    for row in db_rows:
        num = normalize_num(row["hadith_number"])
        key = (row["book_name_fr"], num) if num is not None else None

        fawaz_entry = fawaz.get(key) if key else None

        if fawaz_entry is None:
            stats["not_found"] += 1
            continue

        stats["matched"] += 1

        # Valeurs actuelles en DB
        cur_fr    = (row["fr_text"]    or "").strip()
        cur_grade = (row["grade_primary"] or "").strip()
        cur_alb   = (row["grade_albani"]  or "").strip()

        # Nouvelles valeurs candidates (seulement si champ DB vide)
        new_fr    = fawaz_entry["fr_text"]  if not cur_fr    else None
        new_grade = fawaz_entry["grade"]    if not cur_grade else None
        new_alb   = fawaz_entry["albani"]   if not cur_alb   else None

        if new_fr    : stats["upd_fr_text"] += 1
        if new_grade : stats["upd_grade"]   += 1
        if new_alb   : stats["upd_albani"]  += 1

        if not any([new_fr, new_grade, new_alb]):
            stats["skipped_full"] += 1
            continue

        updates.append({
            "id":            row["id"],
            "fr_text":       new_fr,
            "grade_primary": new_grade,
            "grade_albani":  new_alb,
        })

    print("[3/3] Résultats du matching")
    print(f"      Matchés          : {stats['matched']:>6,}")
    print(f"      Non trouvés      : {stats['not_found']:>6,}")
    print(f"      Déjà complets    : {stats['skipped_full']:>6,}")
    print(f"      → fr_text        : {stats['upd_fr_text']:>6,} à mettre à jour")
    print(f"      → grade_primary  : {stats['upd_grade']:>6,} à mettre à jour")
    print(f"      → grade_albani   : {stats['upd_albani']:>6,} à mettre à jour")
    print(f"      Total UPDATE     : {len(updates):>6,}\n")

    if not updates:
        print("Aucune mise à jour nécessaire — la base est déjà enrichie.")
        conn.close()
        return

    if not apply:
        # Afficher un aperçu des 5 premières mises à jour
        print("APERÇU (5 premières lignes qui seraient modifiées) :")
        for u in updates[:5]:
            changed = {k: v for k, v in u.items() if k != "id" and v is not None}
            print(f"  id={u['id']!r:20s}  champs: {list(changed.keys())}")
        print("\n[DRY-RUN] Aucune écriture effectuée. Relancez avec --apply pour valider.")
        conn.close()
        return

    # ── Application des UPDATE ────────────────────────────────────────────────
    print(f"Application de {len(updates):,} UPDATE …")
    applied = 0

    conn.execute("BEGIN")
    try:
        for u in updates:
            fields, params = [], []
            if u["fr_text"]:
                fields.append("fr_text = ?")
                params.append(u["fr_text"])
            if u["grade_primary"]:
                fields.append("grade_primary = ?")
                params.append(u["grade_primary"])
            if u["grade_albani"]:
                fields.append("grade_albani = ?")
                params.append(u["grade_albani"])

            if not fields:
                continue

            fields.append("updated_at = ?")
            params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            params.append(u["id"])

            sql = f"UPDATE entries SET {', '.join(fields)} WHERE id = ?"
            conn.execute(sql, params)
            applied += 1

        conn.commit()
        print(f"✓ {applied:,} entrées mises à jour avec succès.")

    except Exception as e:
        conn.rollback()
        print(f"✗ ERREUR — rollback effectué : {e}")
        raise

    finally:
        conn.close()

    # ── Rapport final ─────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  RAPPORT FINAL")
    print(f"{'='*60}")
    print(f"  Entrées DB totales   : {len(db_rows):,}")
    print(f"  Entrées matchées     : {stats['matched']:,}")
    print(f"  fr_text enrichis     : {stats['upd_fr_text']:,}")
    print(f"  grade_primary enrichis : {stats['upd_grade']:,}")
    print(f"  grade_albani enrichis  : {stats['upd_albani']:,}")
    print(f"  UPDATE appliqués     : {applied:,}")
    print(f"  Source               : fawazahmed0_fr_dump.json")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Enrichissement DB almizan_v7 depuis fawazahmed0_fr_dump.json (UPDATE uniquement)"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Applique les UPDATE (sans --apply = dry-run)"
    )
    args = parser.parse_args()
    run(apply=args.apply)
