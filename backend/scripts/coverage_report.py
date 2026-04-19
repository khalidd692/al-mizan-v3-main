#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère un rapport de couverture complet pour chaque zone du Vérificateur.
À exécuter AVANT et APRÈS chaque phase de harvesting pour suivre l'avancement.
"""
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

DB = Path("backend/mizan.db")

ZONES = [
    # (zone_id, zone_name, tables_qui_alimentent_la_zone)
    (1,  "Takhrij principal",              ["hadiths", "takhrij"]),
    (2,  "Mutabaʿat",                      ["takhrij"]),
    (3,  "Shawahid",                       ["takhrij"]),
    (4,  "Riwayat",                        ["takhrij"]),
    (5,  "Nombre asanid",                  ["sanad_chains"]),
    (6,  "Ittisal",                        ["sanad_chains", "sanad_links"]),
    (7,  "ʿAdalah",                        ["sanad_links", "rijal", "rijal_verdicts"]),
    (8,  "Dabt",                           ["rijal", "rijal_verdicts"]),
    (9,  "Sighat al-adaʾ",                 ["sanad_links"]),
    (10, "Liqaʾ/muʿasarah",                ["rijal_relations"]),
    (11, "Tadlis",                         ["sanad_links", "rijal"]),
    (12, "Ikhtilat",                       ["rijal"]),
    (13, "Fiche rawi",                     ["rijal"]),
    (14, "Jarh wa taʿdil",                 ["rijal_verdicts"]),
    (15, "Maitre-eleve",                   ["rijal_relations"]),
    (16, "Divergences critiques",          ["rijal_verdicts"]),
    (17, "Typologie quantitative",         ["hadiths"]),
    (18, "Attribution",                    ["hadiths"]),
    (19, "ʿIlal zahirah",                  ["ilal"]),
    (20, "ʿIlal khafiyyah",                ["ilal"]),
    (21, "Shudhudh",                       ["ilal"]),
    (22, "Nakarah",                        ["ilal"]),
    (23, "Idtirab",                        ["ilal"]),
    (24, "Concordance Qurʾan",             ["matn_analysis"]),
    (25, "Concordance Sunnah",             ["matn_analysis"]),
    (26, "Analyse linguistique",           ["matn_analysis"]),
    (27, "Alterations",                    ["matn_analysis"]),
    (28, "Hukm Mizan",                     ["hadiths"]),
    (29, "Verdicts classiques",            ["ahkam"]),
    (30, "Verdicts contemporains",         ["ahkam"]),
    (31, "Asbab al-wurud",                 ["fiqh_hadith"]),
    (32, "Fiqh",                           ["fiqh_hadith"]),
    (33, "Ziyadat al-thiqah",              ["ziyadat_thiqah"]),
    (34, "Wasl vs irsal",                  ["taʿarud_wasl_irsal"]),
    (35, "Rafʿ vs waqf",                   ["taʿarud_waqf_rafʿ"]),
    (36, "Mubham/muhmal",                  ["mubham_muhmal"]),
    (37, "Mazid muttasil",                 ["mazid_muttasil"]),
    (38, "Tafarrud",                       ["tafarrud"]),
    (39, "ʿAmal al-salaf",                 ["ʿamal_salaf"]),
    (40, "Mukhtalif al-hadith",            ["mukhtalif_hadith"]),
]

def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    total_hadiths = cur.execute("SELECT COUNT(*) FROM hadiths").fetchone()[0]
    print(f"\n{'='*70}")
    print(f"RAPPORT DE COUVERTURE MIZAN - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*70}")
    print(f"Total hadiths dans la base : {total_hadiths:,}")
    print(f"{'='*70}")

    print(f"\n{'Zone':<5} {'Nom':<35} {'Hadiths couverts':>17} {'%':>7}")
    print("-" * 70)

    for zone_id, zone_name, tables in ZONES:
        # On compte les hadith_id distincts ayant au moins une ligne dans une des tables
        union_queries = []
        for tbl in tables:
            try:
                # Vérifier si la table existe
                cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tbl}'")
                if not cur.fetchone():
                    continue
                    
                if tbl == "hadiths":
                    if zone_id == 28:
                        union_queries.append("SELECT id AS hid FROM hadiths WHERE grade_synthese IS NOT NULL")
                    else:
                        union_queries.append("SELECT id AS hid FROM hadiths")
                elif tbl == "sanad_chains":
                    union_queries.append("SELECT DISTINCT hadith_id AS hid FROM sanad_chains")
                elif tbl == "sanad_links":
                    union_queries.append("SELECT DISTINCT sc.hadith_id AS hid FROM sanad_chains sc JOIN sanad_links sl ON sl.chain_id=sc.id")
                elif tbl in ("rijal", "rijal_verdicts", "rijal_relations"):
                    # Ces tables ne sont pas directement liées à hadith_id
                    union_queries.append("SELECT DISTINCT sc.hadith_id AS hid FROM sanad_chains sc JOIN sanad_links sl ON sl.chain_id=sc.id WHERE sl.rawi_id IS NOT NULL")
                else:
                    union_queries.append(f"SELECT DISTINCT hadith_id AS hid FROM {tbl}")
            except sqlite3.OperationalError:
                continue

        if not union_queries:
            covered = 0
        else:
            query = " UNION ".join(union_queries)
            try:
                covered = cur.execute(f"SELECT COUNT(DISTINCT hid) FROM ({query})").fetchone()[0]
            except sqlite3.OperationalError:
                covered = 0

        pct = (covered / total_hadiths * 100) if total_hadiths else 0
        bar = "#" * int(pct / 2.5) + "." * (40 - int(pct / 2.5))
        status = "[OK]" if pct > 80 else ("[~]" if pct > 30 else "[!]")
        print(f"{status} {zone_id:<3} {zone_name:<33} {covered:>15,}  {pct:>5.1f}%")

    # Rapport spécifique sur ahkam
    print(f"\n{'='*70}")
    print("DETAIL DES VERDICTS (table ahkam)")
    print(f"{'='*70}")
    
    try:
        total_verdicts = cur.execute("SELECT COUNT(*) FROM ahkam").fetchone()[0]
        print(f"Total verdicts enregistres : {total_verdicts:,}")

        rows = cur.execute("""
          SELECT hukm_class, COUNT(*) AS c
          FROM ahkam
          GROUP BY hukm_class
          ORDER BY c DESC
        """).fetchall()
        
        if rows:
            print("\nDistribution par classe de hukm:")
            for cls, c in rows[:15]:  # Top 15
                print(f"  {cls:<30} {c:>8,}")
    except sqlite3.OperationalError:
        print("Table ahkam non encore peuplee")

    # Verdicts par imam
    print(f"\n{'='*70}")
    print("VERDICTS PAR IMAM (top 20)")
    print(f"{'='*70}")
    try:
        rows = cur.execute("""
          SELECT s.name_ar, COUNT(a.id) AS c
          FROM hukm_sources s
          LEFT JOIN ahkam a ON a.source_id = s.id
          GROUP BY s.id
          ORDER BY c DESC
          LIMIT 20
        """).fetchall()
        
        if rows:
            for name, c in rows:
                print(f"  {name:<35} {c:>8,}")
    except sqlite3.OperationalError:
        print("Tables hukm_sources/ahkam non encore peuplees")

    conn.close()
    print(f"\n{'='*70}")
    print("Rapport termine")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()