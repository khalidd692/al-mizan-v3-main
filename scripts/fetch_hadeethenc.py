#!/usr/bin/env python3
"""
Fetch HadeethEnc — Extraction des verdicts savants pour zones 26-29

Zones couvertes:
  - Zone 26: verdict Cheikh al-Albānī en français
  - Zone 27: verdict Cheikh Ibn Bāz en français  
  - Zone 28: verdict Cheikh Ibn al-ʿUthaymīn en français
  - Zone 29: autres avis de Muḥaddithīn contemporains en français

RÈGLES:
  - Jamais de traduction IA
  - Si absent → {} — jamais de placeholder
  - Stockage dans almizan_v7.db (colonnes grade_albani, grade_ibn_baz, grade_ibn_uthaymin)
  - Pause 1 seconde entre chaque appel API
"""

import json
import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List

import httpx

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s] %(message)s"
)
logger = logging.getLogger("HADEETHENC")

# Chemins
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "backend" / "database" / "almizan_v7.db"

# API HadeethEnc
HADEETHENC_API_URL = "https://hadeethenc.com/api/v1/hadeeth"
HADEETHENC_SEARCH_URL = "https://hadeethenc.com/api/v1/search"

# Mapping scholars HadeethEnc → zones Al-Mīzān
SCHOLAR_MAPPING = {
    "albani": {"zone": "zone_26", "name_fr": "Al-Albānī", "db_column": "grade_albani"},
    "ibn_baz": {"zone": "zone_27", "name_fr": "Ibn Bāz", "db_column": "grade_ibn_baz"},
    "ibn_uthaymin": {"zone": "zone_28", "name_fr": "Ibn al-ʿUthaymīn", "db_column": "grade_ibn_uthaymin"},
    # Zone 29 = autres scholars non listés ci-dessus
}


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


def fetch_hadeethenc_by_text(text_ar: str, timeout: float = 15.0) -> Optional[Dict[str, Any]]:
    """
    Recherche un hadith sur HadeethEnc par son texte arabe.
    
    LOI V3-9: Client HTTP instancié localement.
    """
    try:
        # Texte tronqué pour la recherche (premiers 100 caractères)
        search_text = text_ar[:100].strip()
        
        logger.info(f"[HADEETHENC] Recherche: {search_text[:50]}...")
        
        # Client instancié localement
        with httpx.Client(timeout=timeout) as client:
            # Recherche par texte
            resp = client.post(
                HADEETHENC_SEARCH_URL,
                json={"query": search_text, "language": "ar"},
                headers={"Content-Type": "application/json", "Accept": "application/json"}
            )
            resp.raise_for_status()
            data = resp.json()
        
        # Pause 1 seconde (V3-10)
        time.sleep(1.0)
        
        if not data or "results" not in data or not data["results"]:
            logger.warning("[HADEETHENC] Aucun résultat")
            return None
        
        # Récupère le premier résultat (meilleur match)
        # LOI V3-11: index 0 est valide
        first_result = data["results"][0]
        hadeeth_id = first_result.get("id")
        
        if not hadeeth_id:
            logger.warning("[HADEETHENC] Pas d'ID dans le résultat")
            return None
        
        # Deuxième appel: détails complets
        return fetch_hadeethenc_by_id(hadeeth_id)
        
    except httpx.TimeoutException:
        logger.error("[HADEETHENC] Timeout")
        time.sleep(1.0)
        return None
    except Exception as e:
        logger.error(f"[HADEETHENC] Erreur recherche: {e}")
        time.sleep(1.0)
        return None


def fetch_hadeethenc_by_id(hadeeth_id: str, timeout: float = 15.0) -> Optional[Dict[str, Any]]:
    """
    Récupère les détails d'un hadith par son ID HadeethEnc.
    """
    try:
        logger.info(f"[HADEETHENC] Fetch ID: {hadeeth_id}")
        
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(
                f"{HADEETHENC_API_URL}/{hadeeth_id}",
                headers={"Accept": "application/json"}
            )
            resp.raise_for_status()
            data = resp.json()
        
        time.sleep(1.0)
        
        if not data or "data" not in data:
            logger.warning(f"[HADEETHENC] Pas de données pour {hadeeth_id}")
            return None
        
        hadeeth = data["data"]
        
        # Extraction des grades par scholar
        grades = {}
        
        # Albānī
        if hadeeth.get("grade_albani"):
            grades["albani"] = {
                "verdict": hadeeth["grade_albani"],
                "scholar": "Al-Albānī",
                "source": "hadeethenc"
            }
        
        # Ibn Bāz
        if hadeeth.get("grade_ibn_baz"):
            grades["ibn_baz"] = {
                "verdict": hadeeth["grade_ibn_baz"],
                "scholar": "Ibn Bāz",
                "source": "hadeethenc"
            }
        
        # Ibn al-ʿUthaymīn
        if hadeeth.get("grade_ibn_uthaymin"):
            grades["ibn_uthaymin"] = {
                "verdict": hadeeth["grade_ibn_uthaymin"],
                "scholar": "Ibn al-ʿUthaymīn",
                "source": "hadeethenc"
            }
        
        # Autres scholars (zone_29)
        other_grades = []
        if hadeeth.get("other_grades"):
            for g in hadeeth["other_grades"]:
                if g.get("scholar") and g.get("grade"):
                    other_grades.append({
                        "scholar": g["scholar"],
                        "verdict": g["grade"],
                        "source": "hadeethenc"
                    })
        
        result = {
            "id_hadeethenc": hadeeth_id,
            "text_ar": hadeeth.get("text", ""),
            "grades": grades,
            "other_grades": other_grades,
            "source_url": f"https://hadeethenc.com/ar/hadeeth/{hadeeth_id}",
            "source": "hadeethenc"
        }
        
        logger.info(f"[HADEETHENC] {len(grades)} grades trouvés")
        return result
        
    except httpx.TimeoutException:
        logger.error(f"[HADEETHENC] Timeout pour {hadeeth_id}")
        time.sleep(1.0)
        return None
    except Exception as e:
        logger.error(f"[HADEETHENC] Erreur fetch: {e}")
        time.sleep(1.0)
        return None


def update_db_with_grades(
    hadith_id: str,
    hadeethenc_data: Dict[str, Any]
) -> bool:
    """
    Met à jour almizan_v7.db avec les grades HadeethEnc.
    """
    conn = _get_db_connection()
    if not conn:
        return False
    
    try:
        grades = hadeethenc_data.get("grades", {})
        
        updates = {}
        if "albani" in grades:
            updates["grade_albani"] = grades["albani"]["verdict"]
        if "ibn_baz" in grades:
            updates["grade_ibn_baz"] = grades["ibn_baz"]["verdict"]
        if "ibn_uthaymin" in grades:
            updates["grade_ibn_uthaymin"] = grades["ibn_uthaymin"]["verdict"]
        
        if not updates:
            logger.info(f"[DB] Pas de grades à mettre à jour pour {hadith_id}")
            conn.close()
            return False
        
        # Construction de la requête UPDATE
        set_clause = ", ".join([f"{col} = ?" for col in updates.keys()])
        values = list(updates.values())
        
        # WHERE par ID local ou hadith_id_dorar
        values.extend([hadith_id, hadith_id])
        
        query = f"""
            UPDATE entries 
            SET {set_clause}
            WHERE id = ? OR hadith_id_dorar = ?
        """
        
        conn.execute(query, values)
        conn.commit()
        conn.close()
        
        logger.info(f"[DB] Grades mis à jour pour {hadith_id}: {list(updates.keys())}")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"[DB] Erreur UPDATE: {e}")
        try:
            conn.close()
        except:
            pass
        return False


def fetch_and_store(hadith_id: str, text_ar: Optional[str] = None) -> Dict[str, Any]:
    """
    Pipeline complet: fetch HadeethEnc + store dans DB.
    
    Returns:
        Dict avec zones 26-29 peuplées
    """
    logger.info(f"=" * 60)
    logger.info(f"[HADEETHENC] Traitement hadith_id={hadith_id}")
    logger.info(f"=" * 60)
    
    # Fetch par texte ou par ID
    if text_ar and len(text_ar) > 50:
        data = fetch_hadeethenc_by_text(text_ar)
    else:
        data = fetch_hadeethenc_by_id(hadith_id)
    
    if not data:
        logger.warning(f"[HADEETHENC] Aucune donnée pour {hadith_id}")
        return {
            "zone_26": {},
            "zone_27": {},
            "zone_28": {},
            "zone_29": {}
        }
    
    # Mise à jour DB
    update_db_with_grades(hadith_id, data)
    
    # Construction des zones
    result = {
        "zone_26": {},
        "zone_27": {},
        "zone_28": {},
        "zone_29": {}
    }
    
    grades = data.get("grades", {})
    
    # Zone 26: Albānī
    if "albani" in grades:
        result["zone_26"] = grades["albani"]
        logger.info("[HADEETHENC] zone_26 → RÉEL")
    else:
        logger.info("[HADEETHENC] zone_26 → ABSENT")
    
    # Zone 27: Ibn Bāz
    if "ibn_baz" in grades:
        result["zone_27"] = grades["ibn_baz"]
        logger.info("[HADEETHENC] zone_27 → RÉEL")
    else:
        logger.info("[HADEETHENC] zone_27 → ABSENT")
    
    # Zone 28: Ibn al-ʿUthaymīn
    if "ibn_uthaymin" in grades:
        result["zone_28"] = grades["ibn_uthaymin"]
        logger.info("[HADEETHENC] zone_28 → RÉEL")
    else:
        logger.info("[HADEETHENC] zone_28 → ABSENT")
    
    # Zone 29: Autres
    others = data.get("other_grades", [])
    if others:
        result["zone_29"] = {
            "verdicts": others,
            "count": len(others),
            "source": "hadeethenc"
        }
        logger.info(f"[HADEETHENC] zone_29 → RÉEL ({len(others)} avis)")
    else:
        logger.info("[HADEETHENC] zone_29 → ABSENT")
    
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch HadeethEnc pour zones 26-29")
    parser.add_argument("--hadith-id", required=True, help="ID du hadith")
    parser.add_argument("--text-ar", help="Texte arabe (optionnel)")
    
    args = parser.parse_args()
    
    result = fetch_and_store(args.hadith_id, args.text_ar)
    print(json.dumps(result, ensure_ascii=False, indent=2))
