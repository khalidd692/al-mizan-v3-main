"""
Agent Takhrij — Extraction structurée des grades et définitions pour Al-Mīzān

RÈGLES ABSOLUES :
- Dorar.net UNIQUEMENT pour données structurées (grade, référence, numéro)
- JAMAIS de texte narratif généré ou traduit
- Les champs arabes restent bruts
- Zone absente = {}
- Logging obligatoire de chaque source

Architecture:
  zone_02 → Grade depuis DB locale ou Dorar (arabe brut)
  zone_03 → Définition depuis mustalah_definitions_fr.json
  zone_04-16 → {} (absence honnête)
"""

import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

import httpx

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s] %(message)s"
)
logger = logging.getLogger("TAKHRIJ")

# Chemins constants
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "backend" / "database" / "almizan_v7.db"
DEFINITIONS_PATH = BASE_DIR / "mustalah_definitions_fr.json"
DORAR_API_URL = "https://dorar.net/dorar_api.json"


def _load_definitions() -> Dict[str, Any]:
    """Charge les définitions du lexique Muṣṭalaḥ."""
    try:
        with open(DEFINITIONS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[DEFINITIONS] Erreur chargement: {e}")
        return {"definitions": {}}


def _get_db_connection() -> Optional[sqlite3.Connection]:
    """Établit connexion à la base SQLite locale."""
    if not DB_PATH.exists():
        logger.warning(f"[DB] Base introuvable: {DB_PATH}")
        return None
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=10)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"[DB] Erreur connexion: {e}")
        return None


def _fetch_from_dorar(hadith_id: str) -> Optional[Dict[str, Any]]:
    """
    Récupère données structurées depuis Dorar.net
    UNIQUEMENT: grade, référence, numéro — jamais de texte narratif
    """
    try:
        url = f"{DORAR_API_URL}?skey={hadith_id}"
        logger.info(f"[DORAR] Requête API: hadith_id={hadith_id}")
        
        resp = httpx.get(url, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()
        
        if not data or "data" not in data:
            logger.warning(f"[DORAR] Réponse vide pour {hadith_id}")
            return None
        
        # Extraction données structurées uniquement
        hadith_data = data["data"]
        
        result = {
            "grade_ar": hadith_data.get("grade", ""),  # Arabe brut
            "grade_by": hadith_data.get("graded_by", ""),  # Nom du savant
            "hadith_number": hadith_data.get("hadith_number", ""),
            "book_name_ar": hadith_data.get("book_name", ""),  # Arabe brut
            "source_url": f"https://dorar.net/hadith/{hadith_id}",
            "source": "dorar"
        }
        
        logger.info(f"[DORAR] Données structurées récupérées: grade={result['grade_ar']}")
        return result
        
    except httpx.TimeoutException:
        logger.error(f"[DORAR] Timeout pour {hadith_id}")
        return None
    except Exception as e:
        logger.error(f"[DORAR] Erreur: {e}")
        return None


def _find_grade_definition(grade_ar: str, definitions: Dict) -> Optional[Dict]:
    """
    Trouve la définition correspondante au grade dans le lexique.
    Mapping flexible des grades arabes vers les clés du JSON.
    """
    if not grade_ar:
        return None
    
    defs = definitions.get("definitions", {})
    
    # Mapping grade arabe/anglais/français → clé JSON
    grade_mapping = {
        # Arabe (Dorar.net)
        "صحيح": "sahih",
        "صحيح لذاته": "sahih_lidhatihi",
        "صحيح لغيره": "sahih_li_ghayrihi",
        "حسن": "hasan",
        "حسن لذاته": "hasan_lidhatihi",
        "حسن لغيره": "hasan_li_ghayrihi",
        "ضعيف": "daif",
        "ضعيف جدا": "daif",
        "موضوع": "mawdu",
        "منكر": "munkar",
        "شاذ": "shadh",
        "متروك": "matruk",
        "معلق": "muallaq",
        "منقطع": "munqati",
        "مرسل": "mursal",
        "مدلس": "mudallas",
        "معضل": "mudal",
        "مضطرب": "mudtarib",
        "مدرج": "mudraj",
        "مقلوب": "maqlob",
        "معلل": "mualal",
        "متواتر": "al_mutawatir",
        "آحاد": "al_ahad",
        "مشهور": "mashhur",
        "عزيز": "aziz",
        "غريب": "gharib",
        # Anglais (DB locale)
        "Sahih": "sahih",
        "Hasan": "hasan",
        "Da'if": "daif",
        "Daif": "daif",
        "Mawdu": "mawdu",
        "Munkar": "munkar",
        "Shadh": "shadh",
        "Matruk": "matruk",
        # Français (DB locale)
        "Authentique": "sahih",
        "Bon": "hasan",
        "Faible": "daif",
    }
    
    # Normalisation du grade
    grade_clean = grade_ar.strip()
    key = grade_mapping.get(grade_clean)
    
    if key and key in defs:
        return defs[key]
    
    # Recherche partielle si match exact échoue
    for ar_grade, json_key in grade_mapping.items():
        if ar_grade in grade_clean or grade_clean in ar_grade:
            if json_key in defs:
                return defs[json_key]
    
    logger.warning(f"[DEFINITION] Aucune définition trouvée pour grade: {grade_ar}")
    return None


def analyze(hadith_id: str) -> Dict[str, Any]:
    """
    Analyse un hadith et retourne les zones 01-16 selon les règles strictes.
    
    Args:
        hadith_id: Identifiant du hadith (peut être ID local ou Dorar)
        
    Returns:
        Dict structuré avec zones 02-16 et métadonnées
    """
    timestamp = datetime.now().isoformat()
    zones_remplies = []
    zones_vides = []
    
    logger.info(f"=" * 60)
    logger.info(f"[TAKHRIJ] Analyse hadith_id={hadith_id}")
    logger.info(f"=" * 60)
    
    # Chargement des définitions
    definitions_data = _load_definitions()
    
    # ─────────────────────────────────────────────────────────────────
    # ZONE 02 — Grade (depuis DB locale ou Dorar)
    # ─────────────────────────────────────────────────────────────────
    zone_02 = {}
    grade_source = None
    
    # Essai DB locale d'abord
    conn = _get_db_connection()
    if conn:
        try:
            # Recherche par ID local ou hadith_id_dorar
            row = conn.execute(
                """
                SELECT id, grade_primary, grade_by_mohdith, 
                       book_name_ar, book_name_fr, hadith_number,
                       hadith_id_dorar, source_url
                FROM entries 
                WHERE id = ? OR hadith_id_dorar = ?
                LIMIT 1
                """,
                (hadith_id, hadith_id)
            ).fetchone()
            
            if row:
                row_dict = dict(row)
                if row_dict.get("grade_primary"):
                    zone_02 = {
                        "grade": row_dict["grade_primary"],  # Peut être FR ou AR
                        "grade_by": row_dict.get("grade_by_mohdith", ""),
                        "book_name": row_dict.get("book_name_ar") or row_dict.get("book_name_fr", ""),
                        "hadith_number": row_dict.get("hadith_number", ""),
                        "hadith_id_dorar": row_dict.get("hadith_id_dorar", ""),
                        "source_url": row_dict.get("source_url", ""),
                        "source": "db_locale"
                    }
                    grade_source = "db_locale"
                    zones_remplies.append("zone_02")
                    logger.info(f"[TAKHRIJ] zone_02 → RÉEL (db) | grade={row_dict['grade_primary']}")
            
            conn.close()
        except sqlite3.Error as e:
            logger.error(f"[DB] Erreur requête: {e}")
    
    # Fallback Dorar si DB vide ou grade absent
    if not zone_02.get("grade"):
        dorar_data = _fetch_from_dorar(hadith_id)
        if dorar_data and dorar_data.get("grade_ar"):
            zone_02 = {
                "grade": dorar_data["grade_ar"],  # Arabe brut
                "grade_by": dorar_data.get("grade_by", ""),
                "book_name": dorar_data.get("book_name_ar", ""),  # Arabe brut
                "hadith_number": dorar_data.get("hadith_number", ""),
                "source_url": dorar_data.get("source_url", ""),
                "source": "dorar"
            }
            grade_source = "dorar"
            zones_remplies.append("zone_02")
            logger.info(f"[TAKHRIJ] zone_02 → RÉEL (dorar) | grade={dorar_data['grade_ar']}")
    
    if not zone_02:
        zones_vides.append("zone_02")
        logger.info(f"[TAKHRIJ] zone_02 → ABSENT")
    
    # ─────────────────────────────────────────────────────────────────
    # ZONE 03 — Définition du grade (depuis mustalah_definitions_fr.json)
    # ─────────────────────────────────────────────────────────────────
    zone_03 = {}
    
    if zone_02.get("grade"):
        definition = _find_grade_definition(zone_02["grade"], definitions_data)
        if definition:
            zone_03 = {
                "term_ar": definition.get("term_ar", ""),
                "term_fr": definition.get("term_fr", ""),
                "transliteration": definition.get("transliteration", ""),
                "category": definition.get("category", ""),
                "definition_fr": definition.get("definition_fr", ""),
                "source_reference": definition.get("source_reference", ""),
                "source_url": definition.get("source_url", ""),
                "validating_scholar": definition.get("validating_scholar", ""),
                "source": "mustalah_definitions_fr.json"
            }
            zones_remplies.append("zone_03")
            logger.info(f"[TAKHRIJ] zone_03 → RÉEL (json) | term={definition.get('term_fr', 'N/A')}")
        else:
            zones_vides.append("zone_03")
            logger.info(f"[TAKHRIJ] zone_03 → ABSENT (définition non trouvée)")
    else:
        zones_vides.append("zone_03")
        logger.info(f"[TAKHRIJ] zone_03 → ABSENT (pas de grade)")
    
    # ─────────────────────────────────────────────────────────────────
    # ZONES 04-16 — Absence honnête ({})
    # ─────────────────────────────────────────────────────────────────
    empty_zones = [
        "zone_04", "zone_05", "zone_06", "zone_07",
        "zone_08", "zone_09", "zone_10", "zone_11",
        "zone_12", "zone_13", "zone_14", "zone_15", "zone_16"
    ]
    
    for z in empty_zones:
        zones_vides.append(z)
        logger.info(f"[TAKHRIJ] {z} → ABSENT")
    
    # Assemblage résultat
    result = {
        "zone_02": zone_02,
        "zone_03": zone_03,
        "zone_04": {},
        "zone_05": {},
        "zone_06": {},
        "zone_07": {},
        "zone_08": {},
        "zone_09": {},
        "zone_10": {},
        "zone_11": {},
        "zone_12": {},
        "zone_13": {},
        "zone_14": {},
        "zone_15": {},
        "zone_16": {},
        "_meta": {
            "hadith_id": hadith_id,
            "zones_remplies": zones_remplies,
            "zones_vides": zones_vides,
            "timestamp": timestamp,
            "grade_source": grade_source
        }
    }
    
    logger.info(f"=" * 60)
    logger.info(f"[TAKHRIJ] Terminé — {len(zones_remplies)} zones remplies, {len(zones_vides)} vides")
    logger.info(f"=" * 60)
    
    return result
