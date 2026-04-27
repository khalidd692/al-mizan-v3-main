"""
Al-Mīzān v5.0 — Phase 1 Spider Runner
Runs each Phase 1 spider sequentially and prints a report after each site.
Usage: python -m backend.spiders.phase1_runner [--site SITE_NAME]
"""

import asyncio
import json
import sys
import textwrap
from datetime import datetime
from typing import Dict, Any

# Ensure project root is in path when run directly
import pathlib
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from backend.spiders.phase1.hadithdujour_spider import HadithDuJourSpider
from backend.spiders.phase1.bibliotheque_islamique_spider import BibliothequeIslamisqueSpider
from backend.spiders.phase1.over_blog_spider import OverBlogSpider
from backend.spiders.phase1.nawawi_spider import NawawiSpider
from backend.spiders.phase1.hisnii_spider import HisniiSpider
from backend.spiders.phase1.dammaj_spider import DammajSpider
from backend.spiders.phase1.attaqwa_spider import AtTaqwaSpider

PHASE1_SPIDERS = [
    ("hadithdujour",          HadithDuJourSpider,          "https://www.hadithdujour.com"),
    ("bibliotheque_islamique", BibliothequeIslamisqueSpider, "https://bibliotheque-islamique.fr/hadith/"),
    ("over_blog",              OverBlogSpider,               "https://bibliotheque-islamique-coran-sunna.over-blog.com"),
    ("nawawi",                 NawawiSpider,                 "https://www.40-hadith-nawawi.com"),
    ("hisnii",                 HisniiSpider,                 "https://www.hisnii.com/40-hadith-qudsi/"),
    ("dammaj",                 DammajSpider,                 "https://dammaj-fr.com/omdatu-al-ahkam-le-livre-de-la-salat-complet/"),
    ("attaqwa",                AtTaqwaSpider,                "https://www.at-taqwa.fr/lexplication-de-omdatul-al-ahkam/"),
]

ALL_REPORTS = []


def print_report(report: Dict[str, Any], site_index: int, total_sites: int):
    """Print a formatted report for a single spider run."""
    sep = "═" * 64
    acc_rate = report.get("acceptance_rate", "N/A")
    status = "✓ OK" if report["errors"] < 3 else "⚠ ERRORS"

    print(f"\n{sep}")
    print(f"  RAPPORT PHASE 1 — Site {site_index}/{total_sites}: {report['spider'].upper()}")
    print(sep)
    print(f"  URL            : {report['url']}")
    print(f"  Pages crawlées : {report['pages_crawled']}")
    print(f"  Hadiths extraits      : {report['extracted']}")
    print(f"  Acceptés (manhaj ✓)   : {report['accepted']}")
    print(f"  Rejetés  (manhaj ✗)   : {report['rejected']}")
    print(f"  Taux d'acceptation    : {acc_rate}")
    print(f"  DB insérés            : {report['db_inserted']}")
    print(f"  DB mis à jour (UPSERT): {report['db_updated']}")
    print(f"  Erreurs réseau        : {report['errors']}")
    print(f"  Statut                : {status}")
    print(f"  Données JSON          : {report['data_file']}")
    print(f"  Démarré à             : {report['started_at']}")
    print(f"  Terminé à             : {report['finished_at']}")
    print(sep)


def save_phase1_summary(reports):
    """Save aggregate summary of all Phase 1 runs."""
    summary_path = _REPO_ROOT / "output" / "spider_data" / "phase1_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    total_extracted = sum(r["extracted"] for r in reports)
    total_accepted = sum(r["accepted"] for r in reports)
    total_rejected = sum(r["rejected"] for r in reports)
    total_inserted = sum(r["db_inserted"] for r in reports)
    total_updated = sum(r["db_updated"] for r in reports)
    total_errors = sum(r["errors"] for r in reports)

    summary = {
        "phase": 1,
        "generated_at": datetime.utcnow().isoformat(),
        "sites_crawled": len(reports),
        "total_extracted": total_extracted,
        "total_accepted": total_accepted,
        "total_rejected": total_rejected,
        "overall_acceptance_rate": f"{(total_accepted/total_extracted*100):.1f}%" if total_extracted else "N/A",
        "total_db_inserted": total_inserted,
        "total_db_updated": total_updated,
        "total_errors": total_errors,
        "per_site": reports,
    }

    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)

    print(f"\n{'═'*64}")
    print(f"  RÉSUMÉ PHASE 1 COMPLET")
    print(f"{'═'*64}")
    print(f"  Sites crawlés         : {len(reports)}")
    print(f"  Total hadiths extraits: {total_extracted}")
    print(f"  Total acceptés        : {total_accepted}")
    print(f"  Total rejetés         : {total_rejected}")
    print(f"  Taux global           : {summary['overall_acceptance_rate']}")
    print(f"  Total insérés en DB   : {total_inserted}")
    print(f"  Total mis à jour      : {total_updated}")
    print(f"  Résumé sauvegardé     : {summary_path}")
    print(f"{'═'*64}\n")

    return summary


async def run_single_spider(name, SpiderClass, url, site_idx, total):
    """Run one spider and print its report."""
    print(f"\n▶ Démarrage spider [{site_idx}/{total}]: {name}  ({url})")
    spider = SpiderClass()
    report = await spider.run()
    ALL_REPORTS.append(report)
    print_report(report, site_idx, total)
    return report


async def main(only_site: str = None):
    total = len(PHASE1_SPIDERS)

    for idx, (name, SpiderClass, url) in enumerate(PHASE1_SPIDERS, 1):
        if only_site and name != only_site:
            continue
        await run_single_spider(name, SpiderClass, url, idx, total)

    if ALL_REPORTS:
        save_phase1_summary(ALL_REPORTS)


if __name__ == "__main__":
    # CLI: python -m backend.spiders.phase1_runner [--site NAME]
    import argparse
    parser = argparse.ArgumentParser(description="Al-Mīzān Phase 1 Spider Runner")
    parser.add_argument("--site", default=None,
                        help="Run only a specific spider by name "
                             "(hadithdujour|bibliotheque_islamique|over_blog|nawawi|hisnii|dammaj|attaqwa)")
    args = parser.parse_args()

    asyncio.run(main(only_site=args.site))
