#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schémas Pydantic v2 — AL-MĪZĀN V7.0
Validation structurée des entrées/sorties hadith.
Tawaqquf forcé automatiquement par model_validator sur terme CRITIQUE
ou confiance insuffisante — méthodologie des Salafs.
"""

from __future__ import annotations

from enum import Enum
from typing import ClassVar, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================
# ÉNUMÉRATIONS
# ============================================================

class GradeEnum(str, Enum):
    """Grades normalisés — seules valeurs autorisées dans le pipeline."""
    SAHIH = "صحيح"
    HASAN = "حسن"
    DAIF = "ضعيف"
    MAWDU = "موضوع"
    TAWAQQUF = "TAWAQQUF"   # Suspension du jugement — non publiable


class ScholarTier(str, Enum):
    """Hiérarchie géographique des savants (priorité décroissante)."""
    MEDINE = "Médine"
    ARABIE_SAOUDITE = "Arabie Saoudite"
    TAWAQQUF = "TAWAQQUF"   # Savant inconnu, déviant ou non-Salaf


class TawaqqufReason(str, Enum):
    """Causes documentées d'un Tawaqquf — chaque cause est traçable."""
    TERME_PROTEGE = "terme_protege_detecte"
    GRADE_AMBIGU = "grade_ambigu"
    SAVANT_INCONNU = "savant_inconnu"
    TAWIL_SUSPECTE = "tawil_suspecte"
    BIDAH_DETECTEE = "bidah_detectee"
    CONFIANCE_INSUFFISANTE = "confiance_insuffisante"


# ============================================================
# MODÈLES D'ENTRÉE
# ============================================================

class HadithInput(BaseModel):
    """
    Entrée validée d'un hadith brut avant traitement par le pipeline.
    Rejette silencieusement tout matn vide ou sans contenu arabe réel.
    """
    matn_ar: str = Field(..., description="Texte arabe du hadith (matn)")
    grade_raw: Optional[str] = Field(None, description="Grade brut pré-normalisation")
    source: Optional[str] = Field(None, description="Source (Dorar, HadeethEnc, fawazahmed0…)")
    rawi: Optional[str] = Field(None, description="Narrateur principal (Rāwī)")
    dorar_id: Optional[str] = Field(None, description="Identifiant Dorar.net")

    @field_validator("matn_ar")
    @classmethod
    def validate_arabic_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("matn_ar ne peut pas être vide")
        arabic_chars = sum(1 for c in v if "\u0600" <= c <= "\u06FF")
        if arabic_chars < 5:
            raise ValueError(
                f"matn_ar doit contenir au minimum 5 caractères arabes "
                f"(détecté : {arabic_chars})"
            )
        return v


class GradeNormInput(BaseModel):
    """
    Entrée de normalisation de grade brut vers GradeEnum.
    Gère les variantes arabes, translittérées et anglaises.
    """
    grade_raw: str
    source: Optional[str] = None

    # Table de correspondance exhaustive
    _GRADE_MAP: ClassVar[dict] = {
        # Arabe canonique
        "صحيح": "صحيح",
        "حسن": "حسن",
        "ضعيف": "ضعيف",
        "موضوع": "موضوع",
        # Variantes arabes
        "صحيح لغيره": "صحيح",
        "صحيح لذاته": "صحيح",
        "حسن لغيره": "حسن",
        "حسن لذاته": "حسن",
        "ضعيف جداً": "ضعيف",
        "ضعيف جدا": "ضعيف",
        "منكر": "ضعيف",
        "شاذ": "ضعيف",
        "مضطرب": "ضعيف",
        "معلول": "ضعيف",
        "مرسل": "ضعيف",
        "منقطع": "ضعيف",
        "مدلس": "ضعيف",
        "موضوع جداً": "موضوع",
        # Translittérations courantes
        "sahih": "صحيح",
        "sahîh": "صحيح",
        "hasan": "حسن",
        "daif": "ضعيف",
        "da'if": "ضعيف",
        "daïf": "ضعيف",
        "mawdu": "موضوع",
        "mawdou": "موضوع",
        "mawdū": "موضوع",
        # Anglais
        "authentic": "صحيح",
        "sound": "صحيح",
        "good": "حسن",
        "weak": "ضعيف",
        "fabricated": "موضوع",
        "forged": "موضوع",
        "false": "موضوع",
    }

    @field_validator("grade_raw")
    @classmethod
    def map_to_valid_grade(cls, v: str) -> str:
        key = v.strip().lower()
        return cls._GRADE_MAP.get(key, cls._GRADE_MAP.get(v.strip(), v.strip()))


# ============================================================
# MODÈLE DE SORTIE — Résultat de validation complet
# ============================================================

class ProtectedTermInfo(BaseModel):
    """Résumé sérialisable d'un terme protégé détecté lors du scan."""
    term: str
    category: str
    severity: str
    context: str
    requires_tawaqquf: bool
    note_fr: Optional[str] = None


class ValidationResult(BaseModel):
    """
    Résultat complet d'un cycle de validation hadith.

    Règle doctrinale (model_validator) :
    - Si un terme CRITIQUE est détecté → Tawaqquf forcé, grade → TAWAQQUF
    - Si confiance globale < CONFIDENCE_THRESHOLD → Tawaqquf forcé
    - Un résultat sous Tawaqquf est non-publiable (is_publishable() → False)
    """

    # Seuil configurable — en dessous : Tawaqquf automatique
    CONFIDENCE_THRESHOLD: ClassVar[float] = 50.0

    grade_normalized: GradeEnum = GradeEnum.TAWAQQUF
    translation_fr: Optional[str] = None
    scholar_verdict: Optional[str] = None
    scholar_tier: ScholarTier = ScholarTier.TAWAQQUF
    confidence_score: float = Field(0.0, ge=0.0, le=100.0)

    tawaqquf: bool = False
    tawaqquf_reasons: List[TawaqqufReason] = Field(default_factory=list)
    protected_terms: List[ProtectedTermInfo] = Field(default_factory=list)
    reasoning: Optional[str] = None

    @model_validator(mode="after")
    def enforce_tawaqquf(self) -> "ValidationResult":
        """
        Application de la règle Tawaqquf :
        1. Terme CRITIQUE détecté → suspension obligatoire
        2. Confiance < seuil → suspension obligatoire
        Dans les deux cas : grade → TAWAQQUF, tier → TAWAQQUF
        """
        critical = [
            t for t in self.protected_terms
            if t.severity == "critique" and t.requires_tawaqquf
        ]

        if critical:
            self.tawaqquf = True
            if TawaqqufReason.TERME_PROTEGE not in self.tawaqquf_reasons:
                self.tawaqquf_reasons.append(TawaqqufReason.TERME_PROTEGE)

        if self.confidence_score < self.CONFIDENCE_THRESHOLD:
            self.tawaqquf = True
            if TawaqqufReason.CONFIANCE_INSUFFISANTE not in self.tawaqquf_reasons:
                self.tawaqquf_reasons.append(TawaqqufReason.CONFIANCE_INSUFFISANTE)

        if self.tawaqquf:
            self.grade_normalized = GradeEnum.TAWAQQUF
            self.scholar_tier = ScholarTier.TAWAQQUF

        return self

    def is_publishable(self) -> bool:
        """
        Un résultat sous Tawaqquf ou sous le seuil de confiance
        ne doit jamais être publié sans vérification humaine.
        """
        return (
            not self.tawaqquf
            and self.confidence_score >= 70.0
            and self.grade_normalized != GradeEnum.TAWAQQUF
        )

    def summary(self) -> str:
        """Résumé court lisible pour les logs."""
        status = "🛑 TAWAQQUF" if self.tawaqquf else "✅ Validé"
        reasons = (
            " | ".join(r.value for r in self.tawaqquf_reasons)
            if self.tawaqquf_reasons
            else "—"
        )
        return (
            f"{status} | Grade: {self.grade_normalized.value} "
            f"| Confiance: {self.confidence_score:.1f}% "
            f"| Tier: {self.scholar_tier.value} "
            f"| Raisons: {reasons}"
        )
