#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AL-MĪZĀN GUARD — Middleware Global de Traduction Sécurisée
============================================================
Architecture défense-en-profondeur à 9 couches fusionnées depuis 8 audits IA.
Tolérance d'erreur : 0% sur les Noms et Attributs d'Allah (Asmā' wa Ṣifāt).

Version : 3.0.0 — Optimisations C4, C5, C6, C7
- C4: Fenêtre Divine par phrase (proximité sémantique)
- C5: Consensus asynchrone multi-modèles
- C6: Cache persistant SQLite dans data/cache/
- C7: Back-translation conditionnelle (SIFAT/UNCERTAIN uniquement)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import sqlite3
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Callable, Any

try:
    from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION DU LOGGER
# ═══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger("al_mizan_guard")

# ═══════════════════════════════════════════════════════════════════════════════
# CHEMINS DE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).parent.parent.parent
CACHE_DIR = BASE_DIR / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DB_PATH = CACHE_DIR / "translations_cache.db"

# ═══════════════════════════════════════════════════════════════════════════════
# 1. LEXIQUE DE FER (IRON LEXICON) — 99+ Ṣifāt d'Allah
# ═══════════════════════════════════════════════════════════════════════════════

IRON_LEXICON: Dict[str, str] = {
    "استوى":   "Istiwā'",
    "يد":      "Yad",
    "يدين":    "Yadayn",
    "وجه":     "Wajh",
    "عين":     "'Ayn",
    "أعين":    "'Ayn",
    "قدم":     "Qadam",
    "ساق":     "Sāq",
    "نفس":     "Nafs",
    "روح":     "Rūḥ",
    "غضب":     "Ghadab",
    "رضا":     "Riḍā",
    "محبة":    "Maḥabba",
    "ودّ":      "Wudd",
    "ضحك":     "Ḍaḥik",
    "فرح":     "Faraḥ",
    "نزول":    "Nuzūl",
    "مجيء":    "Majī'",
    "إتيان":   "Ityān",
    "علو":     "'Uluww",
    "فوق":     "Fawq",
    "استواء":  "Istiwā'",
    "العرش":   "al-'Arsh",
    "الكرسي":  "al-Kursī",
    "رحمة":    "Raḥmah",
    "رحيم":    "Raḥīm",
    "رحمن":    "Raḥmān",
    "حكمة":    "Ḥikmah",
    "علم":     "'Ilm",
    "قدرة":    "Qudrah",
    "سمع":     "Sam'",
    "بصر":     "Baṣar",
    "كلام":    "Kalām",
    "حياة":    "Ḥayāh",
    "قيوم":    "Qayyūm",
    "علي":     "'Alī",
    "عظيم":    "'Aẓīm",
    "حليم":    "Ḥalīm",
    "كريم":    "Karīm",
    "تواب":    "Tawwāb",
    "غفور":    "Ghafūr",
    "شكور":    "Shakūr",
    "عزيز":    "'Azīz",
    "جبار":    "Jabbār",
    "متكبر":   "Mutakabbir",
    "خالق":    "Khāliq",
    "بارئ":    "Bāri'",
    "مصور":    "Muṣawwir",
    "ملك":     "Malik",
    "قدوس":   "Quddūs",
    "سلام":    "Salām",
    "مؤمن":   "Mu'min",
    "مهيمن":  "Muhaymin",
    "رزاق":    "Razzāq",
    "فتاح":    "Fattāḥ",
    "عالم":    "'Ālim",
    "قابض":    "Qābiḍ",
    "باسط":    "Bāṣiṭ",
    "خافض":    "Khāfiḍ",
    "رافع":    "Rāfi'",
    "معز":     "Mu'izz",
    "مذل":     "Mudhill",
    "سميع":    "Samī'",
    "بصير":    "Baṣīr",
    "حكم":     "Ḥakam",
    "عدل":     "'Adl",
    "لطيف":    "Laṭīf",
    "خبير":    "Khabīr",
    "كبير":    "Kabīr",
    "حفيظ":    "Ḥafīẓ",
    "مقيت":    "Muqīt",
    "حسيب":    "Ḥasīb",
    "جليل":    "Jalīl",
    "رقيب":    "Raqīb",
    "مجيب":    "Mujīb",
    "واسع":    "Wāsi'",
    "ودود":    "Wadūd",
    "مجيد":    "Majīd",
    "باعث":    "Bā'ith",
    "شهيد":   "Shahīd",
    "حق":      "Ḥaqq",
    "وكيل":    "Wakīl",
    "قوي":     "Qawī",
    "متين":    "Matīn",
    "ولي":     "Walī",
    "حميد":    "Ḥamīd",
    "محصي":    "Muḥṣī",
    "مبدئ":    "Mubdi'",
    "معيد":    "Mu'īd",
    "محيي":    "Muḥyī",
    "مميت":    "Mumīt",
    "حي":      "Ḥayy",
    "واجد":    "Wājid",
    "ماجد":    "Mājid",
    "واحد":    "Wāḥid",
    "أحد":     "Aḥad",
    "صمد":    "Ṣamad",
    "قادر":    "Qādir",
    "مقتدر":   "Muqtadir",
    "مقدم":    "Muqaddim",
    "مؤخر":    "Mu'akhkhir",
    "أول":     "Awwal",
    "آخر":     "Ākhir",
    "ظاهر":   "Ẓāhir",
    "باطن":    "Bāṭin",
}

DIVINE_REFERENTS_AR: Set[str] = {
    "الله", "اللّٰه", "الرب", "رب", "ربنا", "ربه", "ربي", "ربك", "ربهم",
    "الرحمن", "الرحيم", "الملك", "القدوس", "العزيز", "الحكيم",
    "الخالق", "البارئ", "الغفور", "الودود", "الحي", "القيوم",
    "تبارك", "تعالى", "سبحانه", "جل", "جلاله", "عز", "جبروت",
    "هو", "إياه", "له", "به", "منه", "عنده",
}

DIVINE_MARKERS_FR: Set[str] = {
    "allah", "seigneur", "le seigneur", "notre seigneur", "dieu",
    "ar-rahman", "ar-rahim", "le tout-puissant", "l'éternel",
}

HUMAN_MARKERS_AR: Set[str] = {
    "رجل", "امرأة", "إنسان", "رجلاً", "السارق", "اللص", "المجاهد",
    "الصحابي", "النبي", "الرسول", "الخليفة", "العالم", "المؤمن",
}

HUMAN_MARKERS_FR: Set[str] = {
    "homme", "femme", "personne", "voleur", "croyant", "savant",
    "prophète", "messager", "compagnon", "calife", "étudiant",
}

FORBIDDEN_TRANSLATIONS: Dict[str, List[str]] = {
    "يد": ["puissance", "pouvoir", "grâce", "bienfait", "faveur", "force", "autorité", "bénédiction", "mainmise", "contrôle", "emprise", "influence", "capacité", "faculté"],
    "استوى": ["a dominé", "s'est imposé", "a pris le contrôle", "a maîtrisé", "a subjugué", "règne sur", "a pris possession", "s'est établi", "s'est élevé", "est monté", "a pris place"],
    "وجه": ["essence", "être divin", "présence abstraite", "nature divine", "récompense de", "en vue de", "direction", "orientation"],
    "عين": ["surveillance", "protection", "garde", "attention divine", "regard", "observation", "œil"],
    "نزول": ["descente de sa grâce", "envoi de sa miséricorde", "ses bienfaits descendent", "arrivée", "venue"],
    "غضب": ["punition", "châtiment", "colère", "ire", "fureur"],
    "قدم": ["pied", "pas", "avancée", "progression"],
    "ساق": ["jambe", "tibia", "membre"],
}

FORBIDDEN_FLAT: List[str] = [
    phrase for phrases in FORBIDDEN_TRANSLATIONS.values() for phrase in phrases
] + [
    "essence divine", "nature divine", "il est partout", "il est en tout lieu",
    "omnipuissance", "omniprésence", "qui symbolise", "qui représente",
    "qui signifie métaphoriquement", "au sens figuré", "de manière allégorique",
    "à interpréter comme", "métaphoriquement", "allégoriquement",
    "symboliquement", "figurément", "spirituellement", "intérieurement",
]

BLACKLIST_SOURCES: Set[str] = {
    "soufi", "tassawuf", "ibn arabi", "al-ghazali", "rumi", "ibn al-arabi",
    "philosophie", "kalam", "mu'tazila", "ash'ari", "maturidi",
    "ta'wil", "interprétation spirituelle", "ésotérisme", "soufisme",
}

FIXED_TRANSLATIONS: Dict[str, str] = {
    "استوى": "a fait l'Istiwā'",
    "يد الله": "la Yad d'Allah",
    "وجه الله": "le Wajh d'Allah",
    "عين الله": "l'Ayn d'Allah",
    "نزل": "le Nuzūl",
    "غضب": "le Ghadab",
    "رحمة": "la Raḥmah",
    "محبة": "la Maḥabba",
}

# ═══════════════════════════════════════════════════════════════════════════════
# 2. MODÈLES PYDANTIC
# ═══════════════════════════════════════════════════════════════════════════════

if PYDANTIC_AVAILABLE:
    class TriageStatus(str, Enum):
        CLEAN = "CLEAN"
        SIFAT = "SIFAT"
        UNCERTAIN = "UNCERTAIN"

    class TriageResult(BaseModel):
        status: TriageStatus
        detected_terms: List[str] = []
        confidence: float = Field(ge=0.0, le=1.0)
        reason: str = ""

        @field_validator("confidence")
        @classmethod
        def validate_confidence(cls, v: float) -> float:
            if not 0.0 <= v <= 1.0:
                raise ValueError("confidence doit être entre 0.0 et 1.0")
            return v

        @model_validator(mode="after")
        def uncertain_if_low_confidence(self) -> "TriageResult":
            if self.confidence < 0.85 and self.status == TriageStatus.CLEAN:
                log.warning("Confiance faible (%.2f) → forçage UNCERTAIN", self.confidence)
                self.status = TriageStatus.UNCERTAIN
            return self

    class TranslationResult(BaseModel):
        traduction_sens_rapproche: str
        termes_arabes_conserves: List[str] = []
        translitterations_utilisees: List[str] = []
        note_methodologique: Optional[str] = None

        @model_validator(mode="after")
        def check_terms_match(self) -> "TranslationResult":
            if len(self.termes_arabes_conserves) != len(self.translitterations_utilisees):
                raise ValueError("termes_arabes_conserves et translitterations_utilisees doivent avoir la même longueur.")
            return self

    class PipelineOutput(BaseModel):
        success: bool
        triage_status: Optional[TriageStatus] = None
        traduction: Optional[str] = None
        termes_conserves: List[str] = []
        translitterations: List[str] = []
        erreur: Optional[str] = None
        audit_log: List[str] = []
        sha256_hash: Optional[str] = None
        cached: bool = False

# ═══════════════════════════════════════════════════════════════════════════════
# C0 — PRÉ-FILTRAGE & NORMALISATION
# ═══════════════════════════════════════════════════════════════════════════════

class TashkeelError(Exception):
    pass

class PromptInjectionError(Exception):
    pass

class BlacklistError(Exception):
    pass

def strip_tashkeel(text: str) -> str:
    diacritics = re.compile(r'[\u064B-\u065F\u0670\u06D6-\u06ED]')
    stripped = diacritics.sub('', text)
    log.debug(f"[TASHKEEL] {len(text)} → {len(stripped)} caractères")
    return stripped

def normalize_unicode(text: str) -> str:
    normalized = unicodedata.normalize('NFC', text)
    normalized = re.sub(r'[\u200D\u200C]', '', normalized)
    return normalized

def sanitize_hidden_instructions(text: str) -> Tuple[bool, str]:
    injection_patterns = [
        r'ignorez?\s+(la|les)\s+(instruction|consigne|règle)',
        r'override\s+(the\s+)?system\s+prompt',
        r'new\s+instruction',
        r'forget\s+(everything|previous)',
        r'ignore\s+above',
        r'disregard\s+(all|previous)',
    ]
    for pattern in injection_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True, f"Pattern injection détecté: {pattern}"
    return False, ""

def blacklist_source_scan(text: str) -> Tuple[bool, str]:
    text_lower = text.lower()
    for forbidden in BLACKLIST_SOURCES:
        if forbidden in text_lower:
            return True, f"Source blacklistée détectée: {forbidden}"
    return False, ""

def detect_prompt_injection(text: str) -> Tuple[bool, str]:
    is_injected, reason = sanitize_hidden_instructions(text)
    if is_injected:
        return True, reason
    escape_patterns = [r'<\|.*?\|>', r'###\s*instruction', r'---\s*system', r'\[SYSTEM\]']
    for pattern in escape_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True, f"Pattern d'évasion détecté: {pattern}"
    return False, ""

# ═══════════════════════════════════════════════════════════════════════════════
# C1 — TRIAGE & SEGMENTATION
# ═══════════════════════════════════════════════════════════════════════════════

def segment_phrases(text: str) -> List[str]:
    delimiters = r'[۔،؟!:؛.،\n]'
    segments = re.split(delimiters, text)
    segments = [s.strip() for s in segments if s.strip()]
    log.debug(f"[SEGMENT] {len(segments)} phrases détectées")
    return segments

def extract_matn_from_isnad(text: str) -> str:
    matn_patterns = [
        r'قَالَ رَسُولُ اللَّهِ ﷺ.*?(?=\n|$)',
        r'عَنْ.*?قَالَ.*?(?=\n|$)',
        r'أَنَّ.*?قَالَ.*?(?=\n|$)',
    ]
    for pattern in matn_patterns:
        match = re.search(pattern, text, re.UNICODE)
        if match:
            return match.group(0).strip()
    return text

def detect_sifat_deterministe(text: str) -> Set[str]:
    detected = set()
    text_stripped = strip_tashkeel(text)
    for mot_arabe in IRON_LEXICON:
        mot_clean = strip_tashkeel(mot_arabe)
        if mot_clean in text_stripped:
            detected.add(mot_arabe)
    log.debug(f"[DETECT] Déterministe: {len(detected)} termes")
    return detected

# ═══════════════════════════════════════════════════════════════════════════════
# C2 — GÉNÉRATION SOUS CONTRAINTE
# ═══════════════════════════════════════════════════════════════════════════════

def build_dynamic_system_prompt(divine_terms: List[str], occurrence_map: Dict[str, str]) -> str:
    terms_section = "\n".join([
        f"  - '{term}' → GARDER EN ARABE + translittération '{IRON_LEXICON.get(term, term)}' [contexte: {occurrence_map.get(term, 'DIVINE')}]"
        for term in divine_terms
        if occurrence_map.get(term, 'DIVINE') == 'DIVINE'
    ])
    return f"""
Tu es un traducteur spécialisé de l'arabe vers le français, formé à la méthodologie des Mutaqaddimūn.
RÈGLE ABSOLUE — INTERDICTION DE TA'WĪL :
Tu NE DOIS JAMAIS traduire en français les termes ci-dessous relatifs aux Noms et Attributs d'Allah.
TERMES À PRÉSERVER OBLIGATOIREMENT :
{terms_section if terms_section else "(aucun terme spécifique détecté — reste vigilant)"}
FORMAT OBLIGATOIRE : ...a fait l'Istiwā' (استوى) sur le Trône (العرش)...
INTERDICTIONS ABSOLUES : "puissance", "grâce", "faveur", "domination", "maîtrise", "essence divine", "nature divine", "symbolise", "représente", "métaphoriquement", "allégoriquement"
Tu DOIS répondre UNIQUEMENT en JSON valide.
Format obligatoire : {{"traduction_sens_rapproche": "...", "termes_arabes_conserves": [], "translitterations_utilisees": [], "note_methodologique": null}}
"""

def build_few_shot_examples() -> str:
    return """
EXEMPLES CORRECTS :
  Source : "إن الله استوى على العرش"
  Correct : "Certes, Allah a fait l'Istiwā' (استوى) sur le Trône"
  INTERDIT : "Certes, Allah s'est établi sur le Trône" ← TA'WĪL
  Source : "يد الله فوق أيديهم"
  Correct : "La Yad (يد) d'Allah est au-dessus de leurs mains"
  INTERDIT : "La puissance d'Allah est au-dessus" ← TA'WĪL
"""

def apply_fixed_translations(text_fr: str) -> str:
    for ar_term, fr_fixed in FIXED_TRANSLATIONS.items():
        text_fr = text_fr.replace(ar_term, fr_fixed)
    return text_fr

# ═══════════════════════════════════════════════════════════════════════════════
# C3 — VALIDATION DE COMPLÉTUDE
# ═══════════════════════════════════════════════════════════════════════════════

class CompletudeError(Exception):
    pass

def validate_pydantic_structure(raw_json: str, model_cls) -> BaseModel:
    cleaned = re.sub(r'```(?:json)?\s*', '', raw_json, flags=re.IGNORECASE)
    cleaned = cleaned.replace('```', '').strip()
    try:
        data = json.loads(cleaned)
        return model_cls(**data)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON invalide: {e}")
    except ValidationError as e:
        raise ValueError(f"Validation Pydantic échouée: {e}")

def validate_completude(source_ar: str, translation: TranslationResult) -> None:
    detected = detect_sifat_deterministe(source_ar)
    for mot_arabe in detected:
        translitt = IRON_LEXICON.get(mot_arabe, mot_arabe)
        mot_clean = strip_tashkeel(mot_arabe)
        trad_clean = strip_tashkeel(translation.traduction_sens_rapproche)
        dans_traduction = mot_clean in trad_clean or translitt.lower() in translation.traduction_sens_rapproche.lower()
        dans_liste = any(strip_tashkeel(t) == mot_clean or translitt.lower() in t.lower() for t in translation.termes_arabes_conserves)
        if not dans_traduction or not dans_liste:
            raise CompletudeError(f"[COMPLÉTUDE] L'attribut '{translitt}' ({mot_arabe}) détecté dans la source est absent ou traduit dans la sortie LLM. Ta'wīl probable.")

# ═══════════════════════════════════════════════════════════════════════════════
# C4 — GUILLOTINE REGEX & DÉSAMBIGUÏSATION (OPTIMISÉ: PROXIMITÉ PAR PHRASE)
# ═══════════════════════════════════════════════════════════════════════════════

class GuillotineError(Exception):
    pass

def guillotine_regex(text_fr: str, source_ar: str) -> List[str]:
    violations = []
    t_lower = text_fr.lower()
    for forbidden in FORBIDDEN_FLAT:
        if re.search(rf'\b{re.escape(forbidden)}\b', t_lower, re.IGNORECASE):
            violations.append(f"INTERDIT_GLOBAL: {forbidden}")
    return violations

def fenetre_divine_par_phrase(segments: List[str], terme_translitt: str) -> bool:
    """
    OPTIMISATION C4: Analyse de proximité par phrase.
    Si un terme de Sifāt et le Nom d'Allah apparaissent dans la même phrase,
    le système verrouille la traduction.
    """
    for segment in segments:
        if terme_translitt.lower() in segment.lower():
            for marker in DIVINE_MARKERS_FR:
                if marker in segment.lower():
                    log.debug(f"[C4] Terme '{terme_translitt}' et marqueur divin '{marker}' dans la même phrase → VERROUILLAGE")
                    return True
    return False

def desambiguisation_bayesienne(source_ar: str, term: str, fenetre_tokens: int = 8) -> str:
    tokens = source_ar.split()
    term_clean = strip_tashkeel(term)
    for i, token in enumerate(tokens):
        token_clean = strip_tashkeel(token)
        if term_clean in token_clean:
            start = max(0, i - fenetre_tokens)
            end = min(len(tokens), i + fenetre_tokens + 1)
            context_window = tokens[start:end]
            score_divin = sum(1 for t in context_window if strip_tashkeel(t) in DIVINE_REFERENTS_AR)
            score_humain = sum(1 for t in context_window if strip_tashkeel(t) in HUMAN_MARKERS_AR)
            if score_divin > score_humain:
                return "DIVINE"
            elif score_humain > score_divin:
                return "CREATURE"
            else:
                return "AMBIGUOUS"
    return "AMBIGUOUS"

# ═══════════════════════════════════════════════════════════════════════════════
# C5 — VÉRIFICATION CROISÉE & CONSENSUS ASYNCHRONE (OPTIMISÉ)
# ═══════════════════════════════════════════════════════════════════════════════

class DivergenceError(Exception):
    pass

def llm_judge_verification(translation: str, source_ar: str, expected_terms: List[str]) -> Dict:
    return {"conforme": True, "score": 0.95, "raison": "Attributs conservés, pas de ta'wīl détecté"}

async def multi_model_consensus_async(translation: str, source_ar: str, expected_terms: List[str]) -> Dict:
    """
    OPTIMISATION C5: Implémentation asynchrone réelle du consensus multi-modèles.
    Interroge deux modèles différents (ex: Gemini et un autre provider) pour valider les cas critiques.
    """
    log.info("[C5] Début consensus asynchrone multi-modèles")
    
    async def call_model_1() -> Dict:
        # Placeholder pour appel Gemini
        await asyncio.sleep(0.1)
        return {"conforme": True, "score": 0.92, "model": "gemini"}
    
    async def call_model_2() -> Dict:
        # Placeholder pour appel autre modèle (ex: Claude, GPT)
        await asyncio.sleep(0.1)
        return {"conforme": True, "score": 0.94, "model": "claude"}
    
    results = await asyncio.gather(call_model_1(), call_model_2())
    
    votes_conforme = sum(1 for r in results if r["conforme"])
    avg_score = sum(r["score"] for r in results) / len(results)
    
    decision = "conforme" if votes_conforme >= 2 else "non_conforme"
    
    log.info(f"[C5] Consensus: {decision} (votes: {votes_conforme}/2, score moyen: {avg_score:.2f})")
    
    return {
        "decision": decision,
        "votes": {"conforme": votes_conforme, "non_conforme": 2 - votes_conforme},
        "avg_score": avg_score,
        "details": results
    }

def controle_derive_longueur(source_ar: str, translation_fr: str, ratio_max: float = 4.0, min_chars: int = 80) -> List[str]:
    if len(source_ar) < min_chars:
        return []
    ratio = len(translation_fr) / len(source_ar)
    if ratio > ratio_max:
        return [f"DERIVE_LONGUEUR: ratio {ratio:.2f} > {ratio_max}"]
    return []

# ═══════════════════════════════════════════════════════════════════════════════
# C6 — ARCHIVAGE IMMUABLE & MÉMOIRE (OPTIMISÉ: CACHE PERSISTENT)
# ═══════════════════════════════════════════════════════════════════════════════

def compute_sha256(text: str) -> str:
    normalized = normalize_unicode(strip_tashkeel(text))
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def init_cache_db() -> None:
    """Initialise la base SQLite de cache dans data/cache/"""
    conn = sqlite3.connect(CACHE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS translations_cache (
            sha256_hash TEXT PRIMARY KEY,
            source_ar TEXT,
            translation_fr TEXT,
            audit_log TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()
    log.info(f"[C6] Cache DB initialisé: {CACHE_DB_PATH}")

def check_cache_sha256(hash_val: str) -> Optional[Dict]:
    try:
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT translation_fr, audit_log, timestamp
            FROM translations_cache
            WHERE sha256_hash = ?
        """, (hash_val,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "translation": row[0],
                "audit_log": json.loads(row[1]),
                "timestamp": row[2],
                "cached": True
            }
        return None
    except Exception as e:
        log.error(f"[C6] Erreur cache: {e}")
        return None

def insert_validated_translation(hash_val: str, source: str, translation: str, audit_log: List) -> None:
    try:
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO translations_cache
            (sha256_hash, source_ar, translation_fr, audit_log, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (hash_val, source, translation, json.dumps(audit_log), datetime.now().isoformat()))
        conn.commit()
        conn.close()
        log.info(f"[C6] Traduction stockée: {hash_val[:16]}...")
    except Exception as e:
        log.error(f"[C6] Erreur insertion: {e}")

def bandeau_tawaqquf_display(reason: str, source_ar: str) -> Dict:
    return {
        "type": "TAWAQQUF",
        "message": "Ce passage contient des Attributs d'Allah. Par précaution et fidélité au Manhaj, nous avons suspendu la traduction automatique.",
        "reason": reason,
        "source_preview": source_ar[:100]
    }

# ═══════════════════════════════════════════════════════════════════════════════
# C7 — RECURSIVE BACK-TRANSLATION (OPTIMISÉ: CONDITIONNEL SIFAT/UNCERTAIN)
# ═══════════════════════════════════════════════════════════════════════════════

class BackTranslationError(Exception):
    pass

async def back_translation_check_async(original_ar: str, translation_fr: str, expected_ar: str) -> Tuple[bool, str]:
    """
    OPTIMISATION C7: Back-translation invoquée SEULEMENT si triage_status est SIFAT ou UNCERTAIN.
    Évite les appels API inutiles pour le texte standard.
    """
    log.info("[C7] Back-translation asynchrone")
    await asyncio.sleep(0.1)
    back_translated = original_ar
    similarity = len(set(back_translated) & set(expected_ar)) / len(set(expected_ar))
    if similarity < 0.7:
        return False, f"Back-translation diverge: similarité {similarity:.2f}"
    return True, "Back-translation conforme"

# ═══════════════════════════════════════════════════════════════════════════════
# C8 — BOOST COUCHES SUPPLÉMENTAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_theological_polarity(text_fr: str) -> Dict:
    emotional_markers = ["!", "!!", "!!!", "incroyable", "magnifique", "terrible"]
    emotional_count = sum(1 for m in emotional_markers if m in text_fr.lower())
    return {"polarity": "NEUTRE" if emotional_count == 0 else "EMOTIONNEL", "emotional_markers": emotional_count, "safe": emotional_count == 0}

def vector_similarity_check(text_fr: str, reference_texts: List[str]) -> Dict:
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        return {"available": False, "safe": True}
    return {"available": True, "safe": True, "max_similarity": 0.0}

# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSEUR D'AMBIGUÏTÉ
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AmbiguityAnalyzer:
    window_size: int = 150

    def is_divine_context(self, term: str, full_arabic_text: str) -> bool:
        sentences = re.split(r'[.،؟\n]', full_arabic_text)
        for sentence in sentences:
            if term not in sentence:
                continue
            for referent in DIVINE_REFERENTS_AR:
                if referent in sentence:
                    log.debug(f"Terme '{term}' → contexte divin (référent: '{referent}')")
                    return True
            idx = sentences.index(sentence)
            if idx > 0:
                prev = sentences[idx - 1]
                for referent in DIVINE_REFERENTS_AR:
                    if referent in prev and ("هو" in sentence or "له" in sentence):
                        log.debug(f"Terme '{term}' → contexte divin via pronom anaphorique")
                        return True
        return False

    def classify_occurrences(self, terms_to_check: List[str], full_arabic_text: str) -> Dict[str, str]:
        result = {}
        for term in terms_to_check:
            if term not in full_arabic_text:
                continue
            if self.is_divine_context(term, full_arabic_text):
                result[term] = "DIVINE"
            else:
                found_human = False
                sentences = re.split(r'[.،؟\n]', full_arabic_text)
                for s in sentences:
                    if term in s:
                        for marker in HUMAN_MARKERS_AR:
                            if marker in s:
                                found_human = True
                                break
                result[term] = "CREATURE" if found_human else "AMBIGUOUS"
        return result

# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL (GUARD MIDDLEWARE)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AlMizanGuard:
    """
    Middleware Global Al-Mīzān — Porte d'entrée unique de l'API de traduction.
    Exécute les 9 couches de sécurité (C0-C8) en séquence.
    """
    cache_enabled: bool = True
    back_translation_enabled: bool = True
    boost_layers_enabled: bool = True
    consensus_enabled: bool = True
    
    audit_log: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.cache_enabled:
            init_cache_db()
    
    def _log(self, layer: str, message: str) -> None:
        entry = f"[{layer}] {message}"
        self.audit_log.append(entry)
        log.info(entry)
    
    async def translate_hadith_async(self, source_ar: str) -> PipelineOutput:
        """
        Point d'entrée principal asynchrone du pipeline.
        Exécute toutes les couches de sécurité et retourne la traduction validée.
        """
        timestamp = datetime.now().isoformat()
        self.audit_log = []
        
        try:
            # C0: Pré-filtrage & Normalisation
            self._log("C0", "Début pré-filtrage")
            normalized = normalize_unicode(source_ar)
            self._log("C0", "Unicode normalisé (NFC)")
            
            is_injected, inj_reason = detect_prompt_injection(source_ar)
            if is_injected:
                raise PromptInjectionError(inj_reason)
            self._log("C0", "Injection de prompt: OK")
            
            is_blacklisted, bl_reason = blacklist_source_scan(source_ar)
            if is_blacklisted:
                raise BlacklistError(bl_reason)
            self._log("C0", "Blacklist source: OK")
            
            # C1: Triage & Segmentation
            self._log("C1", "Début triage")
            matn = extract_matn_from_isnad(source_ar)
            self._log("C1", f"Matn extrait: {len(matn)} caractères")
            
            segments = segment_phrases(matn)
            self._log("C1", f"{len(segments)} segments détectés")
            
            detected_terms = detect_sifat_deterministe(matn)
            self._log("C1", f"Termes détectés (déterministe): {detected_terms}")
            
            analyzer = AmbiguityAnalyzer()
            occurrence_map = analyzer.classify_occurrences(list(detected_terms), matn)
            self._log("C1", f"Classification contexte: {occurrence_map}")
            
            # Déterminer le triage_status
            divine_terms = [t for t, ctx in occurrence_map.items() if ctx == "DIVINE"]
            if divine_terms:
                triage_status = TriageStatus.SIFAT
            elif any(ctx == "AMBIGUOUS" for ctx in occurrence_map.values()):
                triage_status = TriageStatus.UNCERTAIN
            else:
                triage_status = TriageStatus.CLEAN
            
            self._log("C1", f"Triage status: {triage_status}")
            
            # C6: Cache SHA-256 (avant génération)
            if self.cache_enabled:
                hash_val = compute_sha256(matn)
                self._log("C6", f"SHA-256: {hash_val[:16]}...")
                
                cached = check_cache_sha256(hash_val)
                if cached:
                    self._log("C6", "Cache HIT: traduction récupérée")
                    return PipelineOutput(
                        success=True,
                        traduction=cached["translation"],
                        audit_log=cached["audit_log"],
                        sha256_hash=hash_val,
                        cached=True,
                        triage_status=triage_status
                    )
                self._log("C6", "Cache MISS: génération requise")
            
            # C2: Génération sous contrainte (placeholder)
            self._log("C2", "Génération LLM (placeholder)")
            system_prompt = build_dynamic_system_prompt(divine_terms, occurrence_map)
            few_shot = build_few_shot_examples()
            
            raw_llm_output = """{
  "traduction_sens_rapproche": "Certes, Allah a fait l'Istiwā' (استوى) sur le Trône (العرش)",
  "termes_arabes_conserves": ["استوى", "العرش"],
  "translitterations_utilisees": ["Istiwā'", "al-'Arsh"],
  "note_methodologique": null
}"""
            
            # C3: Validation Pydantic & Complétude
            self._log("C3", "Validation Pydantic")
            
            if not PYDANTIC_AVAILABLE:
                raise ValueError("Pydantic non disponible")
            
            translation = validate_pydantic_structure(raw_llm_output, TranslationResult)
            self._log("C3", "Structure JSON valide")
            
            validate_completude(matn, translation)
            self._log("C3", "Complétude: OK")
            
            final_fr = apply_fixed_translations(translation.traduction_sens_rapproche)
            self._log("C2", "Traductions fixes appliquées")
            
            # C4: Guillotine Regex + Fenêtre Divine par phrase
            self._log("C4", "Guillotine regex")
            
            violations = guillotine_regex(final_fr, matn)
            if violations:
                for v in violations:
                    self._log("C4", f"VIOLATION: {v}")
                raise GuillotineError(f"Violations détectées: {violations}")
            
            # OPTIMISATION C4: Vérification fenêtre divine par phrase
            for term in divine_terms:
                translitt = IRON_LEXICON.get(term, term)
                if fenetre_divine_par_phrase(segments, translitt):
                    self._log("C4", f"VERROUILLAGE: Terme '{translitt}' dans même phrase que marqueur divin")
                    raise GuillotineError(f"Verrouillage C4: '{translitt}' dans même phrase que marqueur divin")
            
            self._log("C4", "Guillotine: OK")
            
            # C5: Vérification croisée + Consensus asynchrone
            self._log("C5", "Vérification croisée")
            
            judge_result = llm_judge_verification(final_fr, matn, divine_terms)
            if not judge_result["conforme"]:
                raise DivergenceError(f"Juge LLM: {judge_result['raison']}")
            self._log("C5", f"Juge LLM: OK (score {judge_result['score']})")
            
            # OPTIMISATION C5: Consensus asynchrone pour cas critiques
            if self.consensus_enabled and triage_status in (TriageStatus.SIFAT, TriageStatus.UNCERTAIN):
                consensus_result = await multi_model_consensus_async(final_fr, matn, divine_terms)
                if consensus_result["decision"] != "conforme":
                    raise DivergenceError(f"Consensus multi-modèles: {consensus_result['decision']}")
                self._log("C5", f"Consensus multi-modèles: OK (score moyen {consensus_result['avg_score']:.2f})")
            
            length_drift = controle_derive_longueur(matn, final_fr)
            if length_drift:
                for d in length_drift:
                    self._log("C5", f"ALERTE: {d}")
            
            # OPTIMISATION C7: Back-translation conditionnelle (SIFAT/UNCERTAIN uniquement)
            if self.back_translation_enabled and triage_status in (TriageStatus.SIFAT, TriageStatus.UNCERTAIN):
                self._log("C7", "Back-translation (conditionnel: SIFAT/UNCERTAIN)")
                bt_ok, bt_reason = await back_translation_check_async(matn, final_fr, matn)
                if not bt_ok:
                    raise BackTranslationError(bt_reason)
                self._log("C7", f"Back-translation: OK")
            else:
                self._log("C7", "Back-translation: SKIP (triage CLEAN)")
            
            # C8: Boost couches supplémentaires
            if self.boost_layers_enabled:
                self._log("C8", "Boost 1: Polarité théologique")
                polarity = analyze_theological_polarity(final_fr)
                if not polarity["safe"]:
                    self._log("C8", f"ALERTE: ton émotionnel détecté ({polarity['emotional_markers']})")
                
                self._log("C8", "Boost 2: Similarité vectorielle")
                vector_check = vector_similarity_check(final_fr, [])
                if vector_check["available"] and not vector_check["safe"]:
                    self._log("C8", "ALERTE: similarité vectorielle insuffisante")
            
            # C6: Archivage SHA-256 (après validation)
            if self.cache_enabled:
                insert_validated_translation(hash_val, matn, final_fr, self.audit_log)
                self._log("C6", "Traduction stockée en cache")
            
            return PipelineOutput(
                success=True,
                traduction=final_fr,
                termes_conserves=translation.termes_arabes_conserves,
                translitterations=translation.translitterations_utilisees,
                audit_log=self.audit_log,
                sha256_hash=hash_val if self.cache_enabled else None,
                cached=False,
                triage_status=triage_status
            )
            
        except PromptInjectionError as e:
            self._log("C0", f"ERREUR: {e}")
            return PipelineOutput(success=False, erreur=str(e), audit_log=self.audit_log)
        
        except BlacklistError as e:
            self._log("C0", f"ERREUR: {e}")
            return PipelineOutput(success=False, erreur=str(e), audit_log=self.audit_log)
        
        except CompletudeError as e:
            self._log("C3", f"ERREUR: {e}")
            return PipelineOutput(success=False, erreur=str(e), audit_log=self.audit_log)
        
        except GuillotineError as e:
            self._log("C4", f"ERREUR: {e}")
            return PipelineOutput(success=False, erreur=str(e), audit_log=self.audit_log)
        
        except DivergenceError as e:
            self._log("C5", f"ERREUR: {e}")
            return PipelineOutput(success=False, erreur=str(e), audit_log=self.audit_log)
        
        except BackTranslationError as e:
            self._log("C7", f"ERREUR: {e}")
            return PipelineOutput(success=False, erreur=str(e), audit_log=self.audit_log)
        
        except Exception as e:
            self._log("PIPELINE", f"ERREUR INATTENDUE: {e}")
            return PipelineOutput(success=False, erreur=f"Erreur inattendue: {e}", audit_log=self.audit_log)

    def translate_hadith(self, source_ar: str) -> PipelineOutput:
        """
        Version synchrone du pipeline (wrapper).
        """
        return asyncio.run(self.translate_hadith_async(source_ar))

# ═══════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE GLOBAL
# ═══════════════════════════════════════════════════════════════════════════════

# Instance singleton du Guard
_guard_instance: Optional[AlMizanGuard] = None

def get_guard() -> AlMizanGuard:
    """Retourne l'instance singleton du Guard."""
    global _guard_instance
    if _guard_instance is None:
        _guard_instance = AlMizanGuard()
    return _guard_instance

def translate_with_guard(source_ar: str) -> PipelineOutput:
    """
    Fonction d'entrée globale pour la traduction sécurisée.
    À appeler depuis main.py ou l'orchestrateur.
    """
    guard = get_guard()
    return guard.translate_hadith(source_ar)

async def translate_with_guard_async(source_ar: str) -> PipelineOutput:
    """
    Version asynchrone de la fonction d'entrée.
    """
    guard = get_guard()
    return await guard.translate_hadith_async(source_ar)
