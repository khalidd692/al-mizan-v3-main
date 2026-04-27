#!/usr/bin/env python3
"""
Ingestion de fawazahmed0_fr_dump.json dans almizane.db.
- Met à jour matn_fr pour les hadiths existants (match par collection + numero_hadith)
- Insère les nouveaux hadiths (fra-nawawi, fra-dehlawi, fra-qudsi)
- Marque les hadiths flaggés avec statut_import = 'methodologie_a_verifier'
- NE supprime rien, NE modifie pas matn_ar
"""

import json
import sqlite3
import hashlib
import datetime
import os
import sys

DB_PATH    = "/home/user/al-mizan-v3-main/backend/almizane.db"
DUMP_PATH  = "/home/user/al-mizan-v3-main/fawazahmed0_fr_dump.json"
REPORT_PATH = "/home/user/al-mizan-v3-main/FAWAZAHMED0_INGESTION_REPORT.md"

# Mapping édition → collections existantes dans la DB
# Les éditions sans entrée dans COLLECTION_MAP seront insérées comme nouvelles collections
COLLECTION_MAP = {
    "fra-abudawud": ["Sunan Abu Dawud"],
    "fra-bukhari":  ["Sahih Bukhari", "bukhari"],
    "fra-ibnmajah": ["Sunan Ibn Majah"],
    "fra-malik":    ["Muwatta Malik"],
    "fra-muslim":   ["Sahih Muslim", "muslim"],
    "fra-nasai":    ["Sunan an-Nasa'i", "nasai"],
    # fra-nawawi, fra-dehlawi, fra-qudsi → INSERT uniquement
}

NEW_COLLECTION_NAMES = {
    "fra-nawawi":  "Forty Hadith an-Nawawi (FR)",
    "fra-dehlawi": "Forty Hadith Dehlawi (FR)",
    "fra-qudsi":   "Forty Hadith Qudsi (FR)",
}

FLAG_EDITIONS = {"fra-nawawi", "fra-dehlawi"}
SOURCE_API    = "fawazahmed0_raw_github"
TIMESTAMP     = datetime.datetime.utcnow().isoformat()


def sha256_of(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def grade_fr(grades: list) -> str:
    """Prend le premier grade disponible comme grade_final."""
    if grades:
        return grades[0].get("grade", "")
    return ""


def ensure_statut_column(cur):
    cur.execute("PRAGMA table_info(hadiths)")
    cols = [r[1] for r in cur.fetchall()]
    if "statut_import" not in cols:
        cur.execute("ALTER TABLE hadiths ADD COLUMN statut_import TEXT DEFAULT NULL")
        print("[MIGRATION] Colonne statut_import ajoutée à la table hadiths")


def ingest(con):
    cur = con.cursor()
    ensure_statut_column(cur)
    con.commit()

    with open(DUMP_PATH, "r", encoding="utf-8") as f:
        dump = json.load(f)

    stats = {}

    for edition, data in dump.items():
        hadiths  = data.get("hadiths", [])
        flag     = data.get("flag")
        statut   = flag if flag else None
        total    = len(hadiths)
        updated  = 0
        inserted = 0
        skipped  = 0
        no_match = 0

        print(f"\n[{edition}] {total} hadiths — statut_import={statut!r}")

        if edition in COLLECTION_MAP:
            # ── Mode UPDATE ──────────────────────────────────────────────
            collections = COLLECTION_MAP[edition]

            # Construire un index local : numero_hadith → id
            placeholders = ",".join("?" * len(collections))
            cur.execute(
                f"SELECT id, numero_hadith, matn_fr FROM hadiths WHERE collection IN ({placeholders})",
                collections,
            )
            rows = cur.fetchall()
            # Certaines entrées ont matn_fr déjà rempli
            index = {}  # str(numero) → (id, matn_fr_actuel)
            for row_id, num, mfr in rows:
                index[str(num)] = (row_id, mfr)

            for h in hadiths:
                num_str = str(h["hadithnumber"])
                text_fr = h.get("text", "").strip()

                if num_str not in index:
                    no_match += 1
                    continue

                row_id, matn_fr_actuel = index[num_str]

                if matn_fr_actuel and matn_fr_actuel.strip():
                    # Déjà une traduction — on n'écrase pas, on met juste le statut si flaggé
                    if statut:
                        cur.execute(
                            "UPDATE hadiths SET statut_import=? WHERE id=?",
                            (statut, row_id),
                        )
                    skipped += 1
                    continue

                cur.execute(
                    "UPDATE hadiths SET matn_fr=?, source_api=?, statut_import=? WHERE id=?",
                    (text_fr, SOURCE_API, statut, row_id),
                )
                updated += 1

        else:
            # ── Mode INSERT (nouvelles collections) ───────────────────────
            collection_name = NEW_COLLECTION_NAMES.get(edition, edition)

            for h in hadiths:
                text_fr  = h.get("text", "").strip()
                num      = h["hadithnumber"]
                livre    = str(h.get("reference", {}).get("book", ""))
                grade    = grade_fr(h.get("grades", []))
                sha      = sha256_of(f"{collection_name}|{num}|{text_fr}")

                # Éviter les doublons si le script tourne deux fois
                cur.execute(
                    "SELECT id FROM hadiths WHERE sha256=?", (sha,)
                )
                if cur.fetchone():
                    skipped += 1
                    continue

                cur.execute(
                    """INSERT INTO hadiths
                       (sha256, collection, numero_hadith, livre,
                        matn_ar, matn_fr, grade_final, categorie,
                        source_api, statut_import, inserted_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (sha, collection_name, str(num), livre,
                     "", text_fr, grade or "", "hadith_fr_only",
                     SOURCE_API, statut, TIMESTAMP),
                )
                inserted += 1

        con.commit()

        stats[edition] = {
            "total":    total,
            "updated":  updated,
            "inserted": inserted,
            "skipped":  skipped,
            "no_match": no_match,
            "flag":     flag,
        }
        print(f"  updated={updated} inserted={inserted} skipped={skipped} no_match={no_match}")

    return stats


def make_report(stats):
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    total_updated  = sum(v["updated"]  for v in stats.values())
    total_inserted = sum(v["inserted"] for v in stats.values())
    total_skipped  = sum(v["skipped"]  for v in stats.values())
    total_no_match = sum(v["no_match"] for v in stats.values())
    total_hadiths  = sum(v["total"]    for v in stats.values())

    lines = [
        "# FAWAZAHMED0 — Rapport d'ingestion FR",
        "",
        f"**Date** : {now}  ",
        f"**Source** : `fawazahmed0_fr_dump.json`  ",
        f"**Base** : `backend/almizane.db`  ",
        "",
        "## Résumé global",
        "",
        f"| Métrique | Valeur |",
        f"|----------|--------|",
        f"| Hadiths dans le dump | {total_hadiths:,} |",
        f"| Traductions mises à jour (UPDATE matn_fr) | {total_updated:,} |",
        f"| Nouveaux hadiths insérés (INSERT) | {total_inserted:,} |",
        f"| Ignorés (matn_fr déjà présent) | {total_skipped:,} |",
        f"| Sans correspondance en DB | {total_no_match:,} |",
        "",
        "## Détail par édition",
        "",
        "| Édition | Total dump | Mis à jour | Insérés | Ignorés | Sans match | Flag |",
        "|---------|-----------|-----------|---------|---------|-----------|------|",
    ]

    for edition, v in stats.items():
        flag_col = f"`{v['flag']}`" if v["flag"] else "—"
        lines.append(
            f"| `{edition}` | {v['total']:,} | {v['updated']:,} | {v['inserted']:,} "
            f"| {v['skipped']:,} | {v['no_match']:,} | {flag_col} |"
        )

    lines += [
        "",
        "## Colonne ajoutée",
        "",
        "La colonne `statut_import TEXT` a été ajoutée à la table `hadiths` si elle n'existait pas.",
        "",
        "- Valeur `methodologie_a_verifier` → hadiths issus de `fra-nawawi` et `fra-dehlawi`",
        "- Valeur `NULL` → hadiths des 7 autres éditions (pas de doute méthodologique)",
        "",
        "## Zones Al-Mīzān",
        "",
        "Les hadiths ingérés alimentent principalement :",
        "",
        "| Zone | Pertinence |",
        "|------|-----------|",
        "| **Zone 2 — Matn** | Texte français disponible pour analyse du contenu |",
        "| **Zone 11 — Grading** | Grades fawazahmed0 importés dans `grade_final` (nouvelles collections) |",
        "| **Zone 13 — Daif / Zone 17 — Mawdu** | Hadiths `methodologie_a_verifier` à traiter en priorité |",
        "| **Zone 4 — Takhrij** | Source `fawazahmed0_raw_github` tracée dans `source_api` |",
        "",
        "## Prochaines étapes",
        "",
        "1. Vérifier manuellement les 82 hadiths `methodologie_a_verifier` (`fra-nawawi` + `fra-dehlawi`)",
        "2. Croiser les `no_match` avec les doublons de collection (`bukhari` vs `Sahih Bukhari`)",
        "3. Ingérer les `avis_savants` depuis les grades fawazahmed0 (champ `grades[]`)",
        "4. Activer les migrations 001/002 pour `needs_human_review` et table `authorities`",
        "",
    ]

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n[RAPPORT] {REPORT_PATH}")


def main():
    print(f"[DB] {DB_PATH}")
    print(f"[DUMP] {DUMP_PATH}")

    con = sqlite3.connect(DB_PATH)
    try:
        stats = ingest(con)
    finally:
        con.close()

    make_report(stats)

    total_updated  = sum(v["updated"]  for v in stats.values())
    total_inserted = sum(v["inserted"] for v in stats.values())
    print(f"\n{'='*55}")
    print(f"TERMINÉ — {total_updated} mis à jour | {total_inserted} insérés")
    print(f"Rapport : {REPORT_PATH}")
    print(f"{'='*55}")


if __name__ == "__main__":
    main()
