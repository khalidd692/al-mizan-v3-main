#!/usr/bin/env python3
"""
Bulk Filler — Traitement batch des 26 168 hadiths d'Al-Mīzān

Pipeline par hadith:
  1. Pilier 1 — DB locale → zones 01, 02, 04, 05
  2. Pilier 2 — Dorar → zones 06-39
  3. Pilier 3 — mustalah_definitions_fr.json → zone 03
  4. Pilier 4 — HadeethEnc → zones 26-29 (optionnel)
  
Output: corpus/hadiths/hadith_{id}.json avec les 40 zones

RÈGLES V3:
  - LOI V3-9: HTTP client dans handler
  - LOI V3-10: await séquentiel — pas de asyncio.gather
  - LOI V3-11: index 0 est valide
  - Pause 1s entre appels Dorar
  - Error handling: log dans logs/bulk_errors.log, continue
"""

import json
import logging
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List

# Ajout du parent au path pour imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.agent_takhrij import analyze
from scripts.fetch_hadeethenc import fetch_and_store as fetch_hadeethenc

# Configuration
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "backend" / "database" / "almizan_v7.db"
OUTPUT_DIR = BASE_DIR / "corpus" / "hadiths"
LOG_DIR = BASE_DIR / "logs"

# Création des répertoires
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s] %(message)s"
)
logger = logging.getLogger("BULK")

# Fichier de log des erreurs
error_log_path = LOG_DIR / "bulk_errors.log"
error_logger = logging.getLogger("BULK_ERRORS")
error_handler = logging.FileHandler(error_log_path, mode='a')
error_handler.setLevel(logging.ERROR)
error_logger.addHandler(error_handler)


def _get_db_connection() -> Optional[sqlite3.Connection]:
    """Établit connexion à la base SQLite locale."""
    if not DB_PATH.exists():
        logger.error(f"[DB] Base introuvable: {DB_PATH}")
        return None
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=10)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"[DB] Erreur connexion: {e}")
        return None


def get_all_hadith_ids(conn: sqlite3.Connection) -> List[str]:
    """Récupère tous les IDs de hadiths depuis la DB."""
    try:
        cursor = conn.execute(
            "SELECT id FROM entries ORDER BY id"
        )
        return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"[DB] Erreur récupération IDs: {e}")
        return []


def process_single_hadith(hadith_id: str, skip_hadeethenc: bool = False) -> Optional[Dict]:
    """
    Traite un seul hadith selon le pipeline complet.
    
    Returns:
        Dict avec 40 zones, ou None si erreur
    """
    try:
        # Pilier 1-2-3: Agent Takhrij (DB + Dorar + Définitions)
        result = analyze(hadith_id)
        
        # Pilier 4: HadeethEnc (zones 26-29)
        if not skip_hadeethenc:
            # Récupère le texte arabe pour recherche
            text_ar = result.get("zone_01", {}).get("text_ar", "")
            
            if text_ar:
                hadeethenc_zones = fetch_hadeethenc(hadith_id, text_ar)
                
                # Merge des zones HadeethEnc
                for zone in ["zone_26", "zone_27", "zone_28", "zone_29"]:
                    if hadeethenc_zones.get(zone):
                        result[zone] = hadeethenc_zones[zone]
                        
                        # Mise à jour des listes
                        if zone not in result["_meta"]["zones_remplies"]:
                            result["_meta"]["zones_remplies"].append(zone)
                            result["_meta"]["filled_count"] += 1
                        if zone in result["_meta"]["zones_vides"]:
                            result["_meta"]["zones_vides"].remove(zone)
                            result["_meta"]["empty_count"] -= 1
        
        return result
        
    except Exception as e:
        error_logger.error(f"[{hadith_id}] {type(e).__name__}: {e}")
        logger.error(f"[BULK] Erreur traitement {hadith_id}: {e}")
        return None


def save_hadith_json(hadith_id: str, data: Dict) -> bool:
    """Sauvegarde le résultat dans corpus/hadiths/hadith_{id}.json"""
    try:
        output_file = OUTPUT_DIR / f"hadith_{hadith_id}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        error_logger.error(f"[{hadith_id}] SAVE_ERROR: {e}")
        return False


def bulk_process(
    start_idx: int = 0,
    end_idx: Optional[int] = None,
    skip_hadeethenc: bool = True  # Désactivé par défaut (trop lent pour 26k)
):
    """
    Traitement batch des hadiths.
    
    Args:
        start_idx: Index de départ (0-based)
        end_idx: Index de fin (None = tous)
        skip_hadeethenc: True pour ignorer HadeethEnc (recommandé pour test)
    """
    logger.info("=" * 70)
    logger.info("BULK FILLER — Traitement batch Al-Mīzān")
    logger.info("=" * 70)
    logger.info(f"Output: {OUTPUT_DIR}")
    logger.info(f"Logs erreurs: {error_log_path}")
    logger.info(f"Skip HadeethEnc: {skip_hadeethenc}")
    logger.info("")
    
    # Récupération des IDs
    conn = _get_db_connection()
    if not conn:
        logger.error("[BULK] Impossible de se connecter à la DB")
        return
    
    all_ids = get_all_hadith_ids(conn)
    conn.close()
    
    total = len(all_ids)
    logger.info(f"[BULK] {total} hadiths dans la base")
    
    # Slicing
    if end_idx is None:
        end_idx = total
    
    ids_to_process = all_ids[start_idx:end_idx]
    count = len(ids_to_process)
    
    logger.info(f"[BULK] Traitement de {start_idx} à {end_idx-1} ({count} hadiths)")
    logger.info("")
    
    # Compteurs
    success_count = 0
    error_count = 0
    start_time = time.time()
    
    # Traitement séquentiel (V3-10)
    for idx, hadith_id in enumerate(ids_to_process, start=start_idx + 1):
        # Affichage progress
        if idx % 10 == 0 or idx == start_idx + 1:
            elapsed = time.time() - start_time
            rate = idx / elapsed if elapsed > 0 else 0
            logger.info(f"[BULK] {idx}/{count} — {rate:.1f} hadiths/sec")
        
        # Traitement
        result = process_single_hadith(hadith_id, skip_hadeethenc=skip_hadeethenc)
        
        if result:
            # Sauvegarde
            if save_hadith_json(hadith_id, result):
                success_count += 1
                filled = result["_meta"]["filled_count"]
                logger.info(f"Hadith {idx}/{count} traité — zones remplies: {filled}/40")
            else:
                error_count += 1
                logger.error(f"Hadith {idx}/{count} — ERREUR SAUVEGARDE")
        else:
            error_count += 1
            logger.error(f"Hadith {idx}/{count} — ERREUR TRAITEMENT")
        
        # Petite pause pour ne pas saturer le CPU
        if idx % 100 == 0:
            time.sleep(0.5)
    
    # Résumé final
    elapsed = time.time() - start_time
    logger.info("")
    logger.info("=" * 70)
    logger.info("RÉSUMÉ")
    logger.info("=" * 70)
    logger.info(f"Total traités: {count}")
    logger.info(f"Succès: {success_count}")
    logger.info(f"Erreurs: {error_count}")
    logger.info(f"Temps: {elapsed:.1f}s ({count/elapsed:.1f} hadiths/sec)")
    logger.info(f"Output: {OUTPUT_DIR}")
    logger.info(f"Log erreurs: {error_log_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Bulk Filler — Traitement batch des hadiths Al-Mīzān"
    )
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="Index de départ (0-based, défaut: 0)"
    )
    parser.add_argument(
        "--end",
        type=int,
        default=None,
        help="Index de fin (défaut: tous)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Nombre max à traiter (alternative à --end)"
    )
    parser.add_argument(
        "--hadeeth",
        action="store_true",
        help="Activer HadeethEnc (zones 26-29) — lent"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Mode test: traite seulement IDs 1-10"
    )
    
    args = parser.parse_args()
    
    # Mode test
    if args.test:
        logger.info("[BULK] MODE TEST — IDs 1-10 uniquement")
        # Récupération des 10 premiers IDs
        conn = _get_db_connection()
        if conn:
            cursor = conn.execute("SELECT id FROM entries LIMIT 10")
            test_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            logger.info(f"[TEST] IDs à traiter: {test_ids}")
            
            for hadith_id in test_ids:
                result = process_single_hadith(hadith_id, skip_hadeethenc=not args.hadeeth)
                if result:
                    save_hadith_json(hadith_id, result)
                    filled = result["_meta"]["filled_count"]
                    print(f"✅ {hadith_id}: {filled}/40 zones")
                else:
                    print(f"❌ {hadith_id}: ERREUR")
        sys.exit(0)
    
    # Mode normal
    end = args.end
    if args.limit:
        end = args.start + args.limit
    
    bulk_process(
        start_idx=args.start,
        end_idx=end,
        skip_hadeethenc=not args.hadeeth
    )
