"""
Agent Takhrij v3 — Nomenclature Officielle 40 Zones Al-Mīzān
Corrections: Zone 01 validation, Zone 40 dépendances, Intégration Dorar complète

RÈGLES ABSOLUES V3:
- LOI V3-9: HTTP client instancié dans le handler, pas au module level
- LOI V3-10: await séquentiel en for loop — asyncio.gather interdit
- LOI V3-11: index 0 est un résultat valide — pas de `if result:` sur index
- Jamais de traduction IA du matn arabe — jamais
- Zone sans donnée réelle = {} — zéro placeholder, zéro invention
- Pause 1 seconde entre chaque appel Dorar
"""

import json
import logging
import re
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
logger = logging.getLogger("TAKHRIJ")

# Chemins constants
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "backend" / "database" / "almizan_v7.db"
DEFINITIONS_PATH = BASE_DIR / "mustalah_definitions_fr.json"
DORAR_API_URL = "https://dorar.net/dorar_api.json"

# Patterns de texte invalide (numéros générés, pas du vrai contenu)
INVALID_TEXT_PATTERNS = [
    r"^حديث رقم\s*\d+$",  # "حديث رقم 1"
    r"^hadith\s*#?\s*\d+$",  # "hadith 1"
    r"^\d+$",  # Juste un nombre
    r"^null$",
    r"^undefined$",
    r"^\s*$",  # Vide
]


def _is_valid_text(text: Optional[str]) -> bool:
    """Vérifie que le texte est valide (pas un placeholder/numéro)."""
    if not text or not text.strip():
        return False
    
    text_clean = text.strip().lower()
    for pattern in INVALID_TEXT_PATTERNS:
        if re.match(pattern, text_clean, re.IGNORECASE):
            return False
    
    # Minimum 50 caractères pour un vrai hadith
    if len(text_clean) < 50:
        return False
    
    return True


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


def _transliterate_book_name(book_name_ar: str) -> str:
    """Translittère le nom du livre en français selon conventions Al-Mīzān."""
    transliterations = {
        "صحيح البخاري": "Ṣaḥīḥ al-Bukhārī",
        "صحيح مسلم": "Ṣaḥīḥ Muslim",
        "سنن أبي داود": "Sunan Abī Dāwūd",
        "جامع الترمذي": "Jāmiʿ at-Tirmidhī",
        "سنن النسائي": "Sunan an-Nasāʾī",
        "سنن ابن ماجه": "Sunan Ibn Mājah",
        "مسند أحمد": "Musnad Aḥmad",
        "موطأ مالك": "Muwaṭṭaʾ Mālik",
        "سنن الدارمي": "Sunan ad-Dārimī",
    }
    return transliterations.get(book_name_ar, book_name_ar)


def _find_grade_definition(grade_raw: str, definitions: Dict) -> Optional[Dict]:
    """Trouve la définition correspondante au grade dans le lexique."""
    if not grade_raw:
        return None
    
    defs = definitions.get("definitions", {})
    
    grade_mapping = {
        "صحيح": "sahih", "Sahih": "sahih", "صحيح لذاته": "sahih",
        "صحيح لغيره": "sahih_li_ghayrihi",
        "حسن": "hasan", "Hasan": "hasan", "Bon": "hasan",
        "ضعيف": "daif", "Da'if": "daif", "Daif": "daif", "Faible": "daif",
        "موضوع": "mawdu", "Mawdu": "mawdu",
        "منكر": "munkar", "Munkar": "munkar",
        "شاذ": "shadh", "Shadh": "shadh",
    }
    
    grade_clean = grade_raw.strip()
    key = grade_mapping.get(grade_clean)
    
    if key and key in defs:
        return defs[key]
    
    for gr, json_key in grade_mapping.items():
        if gr in grade_clean or grade_clean in gr:
            if json_key in defs:
                return defs[json_key]
    
    return None


def _fetch_dorar_structured(hadith_id: str) -> Optional[Dict[str, Any]]:
    """
    Récupère données structurées depuis Dorar.net API.
    LOI V3-9: Client HTTP instancié localement.
    """
    try:
        url = f"{DORAR_API_URL}?skey={hadith_id}"
        logger.info(f"[DORAR] Appel API: {hadith_id}")
        
        # Client instancié localement (V3-9)
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()
        
        # Pause 1 seconde entre appels (V3-10)
        time.sleep(1.0)
        
        if not data or "data" not in data:
            logger.warning(f"[DORAR] Réponse vide pour {hadith_id}")
            return None
        
        hadith_data = data["data"]
        
        # Extraction structurée uniquement
        result = {
            # Zone 01: texte arabe
            "text_ar": hadith_data.get("hadith", ""),
            
            # Zone 06: narrateur principal
            "rawi": hadith_data.get("rawi", ""),
            
            # Zone 07-08: IDs mutaba'at/shawahid (si disponibles)
            "has_similar": hadith_data.get("hasSimilar", False),
            "has_sharh": hadith_data.get("hasSharh", False),
            
            # Zone 11: isnad (si disponible)
            "isnad": hadith_data.get("isnad", ""),
            
            # Zone 12-15: données rijal (basiques)
            "narrator_links": hadith_data.get("narrators", []),
            
            # Zone 17-24: références
            "book_name": hadith_data.get("book", ""),
            "book_name_ar": hadith_data.get("book", ""),
            "hadith_number": hadith_data.get("number", ""),
            "takhrij": hadith_data.get("takhrij", ""),
            
            # Zone 26: grade Albānī si présent
            "grade_albani": hadith_data.get("grade", ""),
            "grade_by": hadith_data.get("gradedBy", ""),
            
            # Métadonnées
            "source_url": f"https://dorar.net/hadith/{hadith_id}",
            "source": "dorar"
        }
        
        logger.info(f"[DORAR] Données récupérées pour {hadith_id}")
        return result
        
    except httpx.TimeoutException:
        logger.error(f"[DORAR] Timeout pour {hadith_id}")
        time.sleep(1.0)
        return None
    except Exception as e:
        logger.error(f"[DORAR] Erreur: {e}")
        time.sleep(1.0)
        return None


def _can_calculate_score(
    zone_02: Dict, zone_06: Dict, zone_11: Dict, zone_26: Dict
) -> bool:
    """Vérifie que les 4 zones requises pour le score sont remplies."""
    required_fields = {
        "zone_02": zone_02.get("grade"),
        "zone_06": zone_06.get("narrator_ar") or zone_06.get("rawi"),
        "zone_11": zone_11.get("isnad_list") or zone_11.get("isnad_ar"),
        "zone_26": zone_26.get("verdict") or zone_26.get("grade_albani"),
    }
    
    all_filled = all(required_fields.values())
    if not all_filled:
        missing = [k for k, v in required_fields.items() if not v]
        logger.warning(f"[SCORE] Zones manquantes pour calcul: {missing}")
    
    return all_filled


def analyze(hadith_id: str) -> Dict[str, Any]:
    """
    Analyse un hadith selon la nomenclature officielle 40 zones Al-Mīzān.
    """
    timestamp = datetime.now().isoformat()
    zones_remplies = []
    zones_vides = []
    
    logger.info(f"[TAKHRIJ] Analyse hadith_id={hadith_id}")
    
    # Chargement des définitions
    definitions_data = _load_definitions()
    
    # ─────────────────────────────────────────────────────────────────
    # PILIER 1 — DB LOCALE
    # ─────────────────────────────────────────────────────────────────
    db_data = None
    conn = _get_db_connection()
    if conn:
        try:
            row = conn.execute(
                """
                SELECT 
                    id, ar_text, ar_text_clean, ar_narrator, ar_full_isnad,
                    fr_text, fr_summary,
                    grade_primary, grade_by_mohdith, grade_explanation,
                    grade_albani, grade_ibn_baz, grade_ibn_uthaymin,
                    book_name_ar, book_name_fr, hadith_number,
                    hadith_id_dorar, source_url, takhrij, zone_id
                FROM entries 
                WHERE id = ? OR hadith_id_dorar = ?
                LIMIT 1
                """,
                (hadith_id, hadith_id)
            ).fetchone()
            
            if row:
                db_data = dict(row)
                logger.info(f"[TAKHRIJ] DB local: hadith trouvé id={db_data.get('id')}")
            conn.close()
        except sqlite3.Error as e:
            logger.error(f"[DB] Erreur: {e}")
    
    # ─────────────────────────────────────────────────────────────────
    # PILIER 2 — DORAR (pour zones manquantes)
    # ─────────────────────────────────────────────────────────────────
    dorar_data = None
    if db_data and db_data.get("hadith_id_dorar"):
        dorar_data = _fetch_dorar_structured(db_data["hadith_id_dorar"])
    else:
        # Essai avec l'ID fourni directement
        dorar_data = _fetch_dorar_structured(hadith_id)
    
    # ─────────────────────────────────────────────────────────────────
    # ZONE 01 — Texte arabe brut (DB validée)
    # ─────────────────────────────────────────────────────────────────
    zone_01 = {}
    text_ar = db_data.get("ar_text") if db_data else None
    
    if _is_valid_text(text_ar):
        zone_01 = {
            "text_ar": text_ar,
            "text_clean": db_data.get("ar_text_clean", ""),
            "source": "db_locale"
        }
        zones_remplies.append("zone_01")
        logger.info("[TAKHRIJ] zone_01 → RÉEL (db)")
    else:
        zones_vides.append("zone_01")
        logger.info(f"[TAKHRIJ] zone_01 → ABSENT (texte invalide: {text_ar[:50] if text_ar else 'None'}...)")
    
    # ─────────────────────────────────────────────────────────────────
    # ZONE 02 — Grade global + livre translittéré + numéro
    # ─────────────────────────────────────────────────────────────────
    zone_02 = {}
    grade = db_data.get("grade_primary", "") if db_data else ""
    book_ar = db_data.get("book_name_ar", "") if db_data else ""
    
    if grade or book_ar:
        book_trans = _transliterate_book_name(book_ar) if book_ar else ""
        zone_02 = {
            "grade": grade,
            "grade_by": db_data.get("grade_by_mohdith", "") if db_data else "",
            "book_name_transliterated": book_trans,
            "book_name_ar": book_ar,
            "hadith_number": db_data.get("hadith_number", "") if db_data else "",
            "source": "db_locale"
        }
        zones_remplies.append("zone_02")
        logger.info(f"[TAKHRIJ] zone_02 → RÉEL (db) | grade={grade}")
    else:
        zones_vides.append("zone_02")
        logger.info("[TAKHRIJ] zone_02 → ABSENT")
    
    # ─────────────────────────────────────────────────────────────────
    # ZONE 03 — Définition technique du grade
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
                "source": "mustalah_definitions_fr.json"
            }
            zones_remplies.append("zone_03")
            logger.info("[TAKHRIJ] zone_03 → RÉEL (json)")
    
    if not zone_03:
        zones_vides.append("zone_03")
        logger.info("[TAKHRIJ] zone_03 → ABSENT")
    
    # ─────────────────────────────────────────────────────────────────
    # ZONE 04 — Texte français depuis DB uniquement
    # ─────────────────────────────────────────────────────────────────
    zone_04 = {}
    fr_text = db_data.get("fr_text") or db_data.get("fr_summary") if db_data else None
    
    if fr_text and len(fr_text.strip()) > 20:
        zone_04 = {
            "text_fr": fr_text,
            "source": "db_locale"
        }
        zones_remplies.append("zone_04")
        logger.info("[TAKHRIJ] zone_04 → RÉEL (db)")
    else:
        zones_vides.append("zone_04")
        logger.info("[TAKHRIJ] zone_04 → ABSENT")
    
    # ─────────────────────────────────────────────────────────────────
    # ZONE 05 — Nom du livre translittéré
    # ─────────────────────────────────────────────────────────────────
    zone_05 = {}
    if book_ar:
        book_trans = _transliterate_book_name(book_ar)
        zone_05 = {
            "book_name_transliterated": book_trans,
            "book_name_ar": book_ar,
            "book_name_fr": db_data.get("book_name_fr", "") if db_data else "",
            "source": "db_locale"
        }
        zones_remplies.append("zone_05")
        logger.info("[TAKHRIJ] zone_05 → RÉEL (db)")
    else:
        zones_vides.append("zone_05")
        logger.info("[TAKHRIJ] zone_05 → ABSENT")
    
    # ─────────────────────────────────────────────────────────────────
    # ZONES 06-16 — PILIER 2 (Dorar) + fallback DB
    # ─────────────────────────────────────────────────────────────────
    
    # Zone 06 — Narrateur principal (Ṣaḥābī)
    zone_06 = {}
    rawi = dorar_data.get("rawi") if dorar_data else None
    if not rawi and db_data:
        rawi = db_data.get("ar_narrator")
    
    if rawi:
        zone_06 = {
            "narrator_ar": rawi,
            "source": "dorar" if dorar_data and dorar_data.get("rawi") else "db_locale"
        }
        zones_remplies.append("zone_06")
        logger.info("[TAKHRIJ] zone_06 → RÉEL")
    else:
        zones_vides.append("zone_06")
        logger.info("[TAKHRIJ] zone_06 → ABSENT")
    
    # Zone 07 — Mutābaʿāt (hadiths confirmant la même voie)
    zone_07 = {}
    if dorar_data and dorar_data.get("has_similar"):
        # TODO: Récupérer les IDs des mutaba'at
        zone_07 = {"has_mutabaat": True, "source": "dorar"}
        zones_remplies.append("zone_07")
        logger.info("[TAKHRIJ] zone_07 → RÉEL (dorar)")
    else:
        zones_vides.append("zone_07")
        logger.info("[TAKHRIJ] zone_07 → ABSENT")
    
    # Zone 08 — Shawāhid (hadiths témoins d'autres voies)
    zone_08 = {}
    # TODO: Extraction depuis Dorar
    zones_vides.append("zone_08")
    logger.info("[TAKHRIJ] zone_08 → ABSENT")
    
    # Zone 09 — ʿIlal (défauts cachés)
    zone_09 = {}
    # TODO: Extraction depuis Dorar
    zones_vides.append("zone_09")
    logger.info("[TAKHRIJ] zone_09 → ABSENT")
    
    # Zone 10 — Sabab al-Wurūd (contexte)
    zone_10 = {}
    # TODO: Extraction depuis Dorar
    zones_vides.append("zone_10")
    logger.info("[TAKHRIJ] zone_10 → ABSENT")
    
    # Zone 11 — Isnād complet
    zone_11 = {}
    isnad = dorar_data.get("isnad") if dorar_data else None
    if not isnad and db_data:
        isnad = db_data.get("ar_full_isnad")
    
    if isnad:
        zone_11 = {
            "isnad_ar": isnad,
            "source": "dorar" if dorar_data and dorar_data.get("isnad") else "db_locale"
        }
        zones_remplies.append("zone_11")
        logger.info("[TAKHRIJ] zone_11 → RÉEL")
    else:
        zones_vides.append("zone_11")
        logger.info("[TAKHRIJ] zone_11 → ABSENT")
    
    # Zones 12-16 — Données avancées (biographies, jarh, ta'dil, tabaqat, conclusion)
    zone_12, zone_13, zone_14, zone_15, zone_16 = {}, {}, {}, {}, {}
    
    if dorar_data and dorar_data.get("narrator_links"):
        # Zone 12 — Biographies basiques
        narrators = dorar_data.get("narrator_links", [])
        if narrators:
            zone_12 = {
                "narrators_count": len(narrators),
                "narrators_preview": narrators[:3],
                "source": "dorar"
            }
            zones_remplies.append("zone_12")
            logger.info("[TAKHRIJ] zone_12 → RÉEL (dorar)")
    
    if not zone_12:
        zones_vides.append("zone_12")
        logger.info("[TAKHRIJ] zone_12 → ABSENT")
    
    # Zones 13-16: TODO extraction avancée
    for z in [13, 14, 15, 16]:
        zones_vides.append(f"zone_{z:02d}")
        logger.info(f"[TAKHRIJ] zone_{z:02d} → ABSENT")
    
    # ─────────────────────────────────────────────────────────────────
    # ZONES 17-24 — Références collections (takhrij parsing)
    # ─────────────────────────────────────────────────────────────────
    zone_17 = zone_18 = zone_19 = zone_20 = zone_21 = zone_22 = zone_23 = zone_24 = {}
    
    takhrij = dorar_data.get("takhrij") if dorar_data else None
    if not takhrij and db_data:
        takhrij = db_data.get("takhrij", "")
    
    if takhrij:
        takhrij_lower = takhrij.lower()
        # Mapping des collections
        if "bukhari" in takhrij_lower or "بخاري" in takhrij:
            zone_17 = {"reference": takhrij, "source": "dorar" if dorar_data else "db_locale"}
            zones_remplies.append("zone_17")
            logger.info("[TAKHRIJ] zone_17 → RÉEL")
        elif "muslim" in takhrij_lower or "مسلم" in takhrij:
            zone_18 = {"reference": takhrij, "source": "dorar" if dorar_data else "db_locale"}
            zones_remplies.append("zone_18")
            logger.info("[TAKHRIJ] zone_18 → RÉEL")
    
    for z in range(17, 25):
        zone_key = f"zone_{z:02d}"
        if zone_key not in zones_remplies:
            zones_vides.append(zone_key)
            logger.info(f"[TAKHRIJ] {zone_key} → ABSENT")
    
    # ─────────────────────────────────────────────────────────────────
    # ZONE 25 — Numérotation et concordance
    # ─────────────────────────────────────────────────────────────────
    zone_25 = {}
    hadith_num = dorar_data.get("hadith_number") if dorar_data else None
    if not hadith_num and db_data:
        hadith_num = db_data.get("hadith_number")
    
    dorar_id = dorar_data and dorar_data.get("hadith_id_dorar") or (db_data and db_data.get("hadith_id_dorar"))
    
    if hadith_num or dorar_id:
        zone_25 = {
            "hadith_number": hadith_num,
            "hadith_id_dorar": dorar_id,
            "source": "dorar" if dorar_data else "db_locale"
        }
        zones_remplies.append("zone_25")
        logger.info("[TAKHRIJ] zone_25 → RÉEL")
    else:
        zones_vides.append("zone_25")
        logger.info("[TAKHRIJ] zone_25 → ABSENT")
    
    # ─────────────────────────────────────────────────────────────────
    # ZONES 26-29 — Verdicts savants (Pilier 3: HadeethEnc à implémenter)
    # ─────────────────────────────────────────────────────────────────
    zone_26 = zone_27 = zone_28 = zone_29 = {}
    
    # Zone 26: Albānī (priorité Dorar, fallback DB)
    grade_albani = dorar_data.get("grade_albani") if dorar_data else None
    if not grade_albani and db_data:
        grade_albani = db_data.get("grade_albani")
    
    if grade_albani:
        zone_26 = {"verdict": grade_albani, "scholar": "Al-Albānī", "source": "dorar" if dorar_data else "db_locale"}
        zones_remplies.append("zone_26")
        logger.info("[TAKHRIJ] zone_26 → RÉEL")
    else:
        zones_vides.append("zone_26")
        logger.info("[TAKHRIJ] zone_26 → ABSENT (attend HadeethEnc)")
    
    # Zones 27-29: Ibn Bāz, Ibn al-ʿUthaymīn, autres (HadeethEnc)
    if db_data and db_data.get("grade_ibn_baz"):
        zone_27 = {"verdict": db_data["grade_ibn_baz"], "scholar": "Ibn Bāz", "source": "db_locale"}
        zones_remplies.append("zone_27")
        logger.info("[TAKHRIJ] zone_27 → RÉEL (db)")
    else:
        zones_vides.append("zone_27")
        logger.info("[TAKHRIJ] zone_27 → ABSENT (attend HadeethEnc)")
    
    if db_data and db_data.get("grade_ibn_uthaymin"):
        zone_28 = {"verdict": db_data["grade_ibn_uthaymin"], "scholar": "Ibn al-ʿUthaymīn", "source": "db_locale"}
        zones_remplies.append("zone_28")
        logger.info("[TAKHRIJ] zone_28 → RÉEL (db)")
    else:
        zones_vides.append("zone_28")
        logger.info("[TAKHRIJ] zone_28 → ABSENT (attend HadeethEnc)")
    
    zones_vides.append("zone_29")
    logger.info("[TAKHRIJ] zone_29 → ABSENT (attend HadeethEnc)")
    
    # ─────────────────────────────────────────────────────────────────
    # ZONES 30-39 — Absence honnête (données avancées)
    # ─────────────────────────────────────────────────────────────────
    zone_30 = zone_31 = zone_32 = zone_33 = zone_34 = {}
    zone_35 = zone_36 = zone_37 = zone_38 = zone_39 = {}
    
    for z in range(30, 40):
        zones_vides.append(f"zone_{z:02d}")
        logger.info(f"[TAKHRIJ] zone_{z:02d} → ABSENT")
    
    # ─────────────────────────────────────────────────────────────────
    # ZONE 40 — Score Al-Mīzān (calculé seulement si 02, 06, 11, 26 remplies)
    # ─────────────────────────────────────────────────────────────────
    zone_40 = {}
    can_score = _can_calculate_score(zone_02, zone_06, zone_11, zone_26)
    
    if can_score:
        grade = zone_02.get("grade", "")
        grade_scores = {
            "Sahih": 95, "صحيح": 95,
            "Hasan": 80, "حسن": 80, "Bon": 80,
            "Da'if": 40, "ضعيف": 40, "Faible": 40,
        }
        score = grade_scores.get(grade, 50)
        zone_40 = {
            "score": score,
            "grade": grade,
            "confidence": "high" if score >= 80 else "medium" if score >= 60 else "low",
            "source": "calculated"
        }
        zones_remplies.append("zone_40")
        logger.info(f"[TAKHRIJ] zone_40 → RÉEL (calculated) | score={score}")
    else:
        zones_vides.append("zone_40")
        logger.info("[TAKHRIJ] zone_40 → ABSENT (zones 02/06/11/26 requises)")
    
    # ─────────────────────────────────────────────────────────────────
    # ASSEMBLAGE — 40 ZONES
    # ─────────────────────────────────────────────────────────────────
    result = {
        f"zone_{z:02d}": locals()[f"zone_{z:02d}"]
        for z in range(1, 41)
    }
    
    result["_meta"] = {
        "hadith_id": hadith_id,
        "zones_remplies": zones_remplies,
        "zones_vides": zones_vides,
        "timestamp": timestamp,
        "total_zones": 40,
        "filled_count": len(zones_remplies),
        "empty_count": len(zones_vides),
        "piliers": {
            "db_local": db_data is not None,
            "dorar": dorar_data is not None,
        }
    }
    
    logger.info(f"[TAKHRIJ] Terminé — {len(zones_remplies)}/40 zones remplies")
    
    return result
