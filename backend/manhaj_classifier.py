"""
Al-Mīzān v5.0 — Manhaj Classifier
Validates extracted hadith content against Islamic manhaj (methodology) standards.
Outputs: accept/reject decision + score + category + rejection logging.
"""

import hashlib
import json
import pathlib
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
REJECTIONS_FILE = _REPO_ROOT / "output" / "manhaj_rejections.json"

# ── Source trust scores (0-100) ───────────────────────────────────────────────
_TRUSTED_SOURCES: dict = {
    # Phase 1
    "hadithdujour.com": 85,
    "bibliotheque-islamique.fr": 82,
    "40-hadith-nawawi.com": 90,
    "hisnii.com": 88,
    "dammaj-fr.com": 90,
    "at-taqwa.fr": 88,
    "over-blog.com": 60,
    # Phase 2
    "islamhouse.com": 95,
    "alifta.gov.sa": 98,
    "islamqa.info": 92,
    "al-badr.fr": 90,
    "miraath.fr": 88,
    "3ilmchar3i.net": 85,
    "albassirah.com": 85,
    "sounnah-publication.fr": 88,
    "lavoiedroite.com": 85,
    "institutsounnah.com": 88,
    "dourous-sounnah.com": 87,
    "salafidemontreal.com": 85,
    "salafislam.fr": 85,
    "salafs.com": 82,
    "salafidunord.com": 82,
    "manhajulhaqq.com": 87,
    "an-nassiha.com": 85,
    "tchalabi.com": 83,
    "sahab.net": 90,
    # Phase 3
    "wixsite.com": 55,
    "dourouss-abdelmalik.com": 85,
    "ahl-al-athar.com": 85,
    "al-haqq.fr": 83,
    "salafi-guinee.fr": 82,
    "lavoieclaire.fr": 83,
    "lavoiedessalafs.com": 82,
    "lamaisondelislam.com": 80,
    "albayyinah.fr": 85,
    "markaz-al-forqane.be": 83,
    "mosquee-sounnah-toulouse.fr": 83,
    # Phase 4
    "wordpress.com": 55,
    "blogspot.com": 52,
    "ahlsunnahtraduction.com": 83,
    "salafiactu.wordpress.com": 70,
    "da3wasalafiya.wordpress.com": 70,
    "salafispublicationcastres.over-blog.com": 72,
    "almoufakkir.wordpress.com": 68,
    "salafidelest.wordpress.com": 70,
    "salafiyasona.wordpress.com": 68,
    "dawahsalafi.wordpress.com": 70,
    "abdulrahmaane.wordpress.com": 68,
    "la-hijra.blogspot.com": 65,
    "tebessasalaf.blogspot.com": 65,
    "awnad.over-blog.com": 68,
}

# ── Bid'ah flag terms (auto-reject on match) ──────────────────────────────────
_BIDAT_FLAGS: List[str] = [
    # Extremist Sufism
    "al-ghawth", "al-qutb", "le pôle",
    "wahdatul wujud", "wahdat al-wujud", "wahdat al wujud",
    "الغوث", "القطب",
    "tawassul par les morts", "istigatha",
    "intercession des saints",
    "célébration du mawlid", "la nuit du mawlid",
    # Shi'ism
    "twelver", "imami", "ja'fari", "jafari",
    "imam ali est le meilleur de la création",
    "massum", "infaillibilité des imams",
    # Fabrications
    "hadith fabriqué connu", "mawdou établi",
]

# ── Canonical collections (content boost) ────────────────────────────────────
_CANONICAL_COLLECTIONS: List[str] = [
    "bukhari", "bukhārī", "boukhâri", "al-bukhari",
    "muslim", "sahih muslim",
    "abu dawood", "abou daoud", "abū dāwūd", "sunan abi dawud",
    "tirmidhi", "tirmidhī", "at-tirmidhi", "sunan at-tirmidhi",
    "nasai", "nasā'ī", "an-nasa'i", "sunan an-nasai",
    "ibn majah", "ibn mâja", "sunan ibn majah",
    "ahmad", "musnad ahmad", "musnad de ahmad",
    "nawawi", "an-nawawi", "arba'in nawawi",
    "riyadh al-salihin", "riyad as-salihin", "riyad as-saliheen",
    "arbain", "arba'in", "arbaine",
    "omdatu al-ahkam", "umdatu al-ahkam", "omdatul ahkam",
    "hisn al-muslim", "forteresse du musulman",
    "qudsi", "hadith qudsi",
]

# ── Arabic detection regex ────────────────────────────────────────────────────
_ARABIC_RE = re.compile(r'[؀-ۿ]{5,}')


@dataclass
class ClassificationResult:
    accepted: bool
    score: float
    manhaj_category: str   # MAQBUL | DAIF | MAWDUU | UNKNOWN | REJECTED
    reason: str
    sha256: str = ""
    source_url: str = ""
    flags: List[str] = field(default_factory=list)


def _sha256(matn_ar: Optional[str], matn_fr: Optional[str]) -> str:
    text = ((matn_ar or "").strip() + "|" + (matn_fr or "").strip())
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _source_score(source_url: str) -> float:
    url_lower = source_url.lower()
    for domain, score in _TRUSTED_SOURCES.items():
        if domain in url_lower:
            return float(score)
    return 40.0


def _bidat_flags(text: str) -> List[str]:
    text_l = text.lower()
    return [f for f in _BIDAT_FLAGS if f.lower() in text_l]


def _has_canonical(text: str) -> bool:
    text_l = text.lower()
    return any(col in text_l for col in _CANONICAL_COLLECTIONS)


def _grade_to_category(grade: str) -> str:
    g = grade.lower()
    if any(k in g for k in ["صحيح", "حسن", "sahih", "hasan", "sahīh", "authentique", "bon"]):
        return "MAQBUL"
    if any(k in g for k in ["ضعيف", "da'if", "da`if", "faible", "daif"]):
        return "DAIF"
    if any(k in g for k in ["موضوع", "mawdū", "mawdou", "fabriqué", "fabricated", "inventé"]):
        return "MAWDUU"
    return "UNKNOWN"


def classify(
    matn_ar: Optional[str],
    matn_fr: Optional[str],
    source_url: str,
    collection: Optional[str] = None,
    grade: Optional[str] = None,
    translator: Optional[str] = None,
) -> ClassificationResult:
    """
    Main classifier entry point.
    Returns ClassificationResult with accept/reject decision.
    """
    # Empty content — hard reject
    if not (matn_fr or matn_ar):
        return ClassificationResult(
            accepted=False, score=0.0,
            manhaj_category="REJECTED",
            reason="Contenu vide: aucun texte arabe ni traduction",
            source_url=source_url,
        )

    score = _source_score(source_url)
    flags: List[str] = []
    reasons: List[str] = []

    combined = " ".join(filter(None, [matn_ar, matn_fr, collection, grade]))

    # Bid'ah detection — heavy penalty
    detected = _bidat_flags(combined)
    if detected:
        flags.extend(detected)
        score -= 45
        reasons.append(f"Termes bid'ah: {', '.join(detected)}")

    # Canonical collection boost
    if _has_canonical(collection or combined):
        score += 5

    # Arabic text present
    if matn_ar and _ARABIC_RE.search(matn_ar):
        score += 5

    # French translation present and substantial
    if matn_fr and len(matn_fr.strip()) >= 30:
        score += 3

    # Grade present
    if grade and grade.strip():
        score += 3

    # Translator attribution
    if translator and translator.strip():
        score += 2

    # Very short content penalty
    if len((matn_fr or "").strip()) < 20 and len((matn_ar or "").strip()) < 10:
        score -= 20
        reasons.append("Texte trop court")

    score = round(max(0.0, min(100.0, score)), 1)

    manhaj_category = _grade_to_category(grade) if grade else "UNKNOWN"

    accepted = score >= 50 and not flags
    reason = "; ".join(reasons) if reasons else ("Accepté" if accepted else "Score insuffisant")

    return ClassificationResult(
        accepted=accepted,
        score=score,
        manhaj_category=manhaj_category,
        reason=reason,
        sha256=_sha256(matn_ar, matn_fr),
        source_url=source_url,
        flags=flags,
    )


def log_rejection(entry: dict, result: ClassificationResult) -> None:
    """Append rejected entry to manhaj_rejections.json."""
    REJECTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "source_url": result.source_url,
        "score": result.score,
        "reason": result.reason,
        "flags": result.flags,
        "manhaj_category": result.manhaj_category,
        "sha256": result.sha256,
        "matn_fr_preview": (entry.get("matn_fr") or "")[:120],
        "matn_ar_preview": (entry.get("matn_ar") or "")[:80],
    }
    try:
        data: list = []
        if REJECTIONS_FILE.exists():
            with open(REJECTIONS_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        data.append(record)
        with open(REJECTIONS_FILE, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
    except Exception:
        pass  # rejection logging is non-critical
