#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filtre de Termes Protégés — AL-MĪZĀN V7.0
Détection regex AR/FR des déviations doctrinales (Bid'ah, Ta'wîl).
Tawaqquf forcé sur tout terme CRITIQUE — méthodologie des Salafs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class TermSeverity(str, Enum):
    CRITIQUE = "critique"           # Tawaqquf obligatoire, blocage immédiat
    AVERTISSEMENT = "avertissement" # Signalement, analyse continue
    INFO = "info"                   # Journal uniquement


class TermCategory(str, Enum):
    SIFAT_ILAHIYYA = "sifat_ilahiyya"  # Attributs divins protégés (AR)
    BIDAH_AR = "bidah_ar"              # Terme d'innovation en arabe
    TAWIL_FR = "tawil_fr"             # Ta'wîl interdit en français
    GRADE_SUSPECT = "grade_suspect"    # Formulation de grade ambiguë


@dataclass
class TermMatch:
    term: str
    category: TermCategory
    severity: TermSeverity
    context: str                        # Extrait du texte (fenêtre ±60 chars)
    position: int                       # Position du match dans le texte
    requires_tawaqquf: bool
    note_ar: Optional[str] = None       # Remarque savante en arabe
    note_fr: Optional[str] = None       # Explication en français


# ============================================================
# TERMES BID'AH EN ARABE
# Structure : pattern_regex → (catégorie, sévérité, note_ar, note_fr)
# ============================================================

_BIDAH_AR: Dict[str, Tuple] = {

    # ── KUFR EXPLICITE — Tawaqquf absolu ──────────────────────────────────────
    r'\bالحلول\b': (
        TermCategory.BIDAH_AR, TermSeverity.CRITIQUE,
        'الحلول: اعتقاد حلول ذات الله في خلقه — كفر بالإجماع',
        'Ḥulūl : croyance en l\'incarnation de l\'Essence divine dans la création — kufr',
    ),
    r'\bالاتحاد\b': (
        TermCategory.BIDAH_AR, TermSeverity.CRITIQUE,
        'الاتحاد: اتحاد الخالق بالمخلوق — كفر بالإجماع',
        'Ittiḥād : union du Créateur avec la création — kufr',
    ),
    r'وحدة\s+الوجود': (
        TermCategory.BIDAH_AR, TermSeverity.CRITIQUE,
        'وحدة الوجود: مذهب ابن عربي الباطني — كفر عند أهل السنة',
        'Waḥdat al-wujūd : panthéisme d\'Ibn ʿArabī — kufr selon Ahl al-Sunna',
    ),
    r'وحدة\s+الشهود': (
        TermCategory.BIDAH_AR, TermSeverity.CRITIQUE,
        'وحدة الشهود: مذهب السمناني — ضلال متصوف',
        'Waḥdat al-shuhūd : doctrine de al-Simnānī — égarement soufi',
    ),
    r'\bالتعطيل\b': (
        TermCategory.BIDAH_AR, TermSeverity.CRITIQUE,
        'التعطيل: نفي الصفات الإلهية كلياً أو جزئياً — ضلال الجهمية والمعتزلة',
        'Ta\'ṭīl : négation totale ou partielle des Attributs divins — déviance des Jahmiyya',
    ),

    # ── BID'AH — Tawaqquf recommandé ──────────────────────────────────────────
    r'\bالتأويل\b': (
        TermCategory.BIDAH_AR, TermSeverity.AVERTISSEMENT,
        'التأويل: صرف اللفظ عن ظاهره — ممنوع في باب الصفات عند السلف',
        'Ta\'wīl : détournement du sens apparent — interdit pour les Attributs divins',
    ),
    r'\bتأويل\b': (
        TermCategory.BIDAH_AR, TermSeverity.AVERTISSEMENT,
        'تأويل مطلق — يستلزم التوقف في باب الصفات والأسماء',
        'Ta\'wīl appliqué — Tawaqquf requis dans le domaine des Noms et Attributs',
    ),
    r'\bالتفويض\b': (
        TermCategory.BIDAH_AR, TermSeverity.AVERTISSEMENT,
        'التفويض: تفويض المعنى مع نفي الظاهر — بدعة محدثة عند كثير من المحققين',
        'Tafwīḍ : délégation du sens en niant l\'apparent — bid\'ah selon les muḥaqqiqūn',
    ),
    r'\bالتشبيه\b': (
        TermCategory.BIDAH_AR, TermSeverity.AVERTISSEMENT,
        'التشبيه: تشبيه صفات الخالق بصفات المخلوق — منهج المشبهة المردود',
        'Tashbīh : assimilation des Attributs du Créateur à ceux de la création — rejeté',
    ),
    r'\bالتجسيم\b': (
        TermCategory.BIDAH_AR, TermSeverity.AVERTISSEMENT,
        'التجسيم: إثبات جسم لله — غير لائق بجلاله سبحانه',
        'Tajsīm : affirmation d\'un corps pour Allah — incompatible avec Sa Majesté',
    ),
    r'\bالجسمية\b': (
        TermCategory.BIDAH_AR, TermSeverity.AVERTISSEMENT,
        'الجسمية: نسبة الجسم إلى الله — منهج المجسمة المذموم',
        'Jismiyya : doctrine des corporéistes — déviance documentée',
    ),
    r'\bالمعتزلة\b': (
        TermCategory.BIDAH_AR, TermSeverity.AVERTISSEMENT,
        'المعتزلة: من أهل البدع في باب الصفات (نفي الصفات الخبرية)',
        'Muʿtazila : innovateurs dans le domaine des Attributs (négation des Attributs rapportés)',
    ),
    r'\bالجهمية\b': (
        TermCategory.BIDAH_AR, TermSeverity.CRITIQUE,
        'الجهمية: من أشد الفرق ضلالاً في نفي الأسماء والصفات — فرقة ضالة',
        'Jahmiyya : parmi les sectes les plus égarées dans la négation des Noms et Attributs',
    ),
}

# ============================================================
# ATTRIBUTS DIVINS PROTÉGÉS EN ARABE
# Leur présence impose une traduction conforme au Lexique de Fer.
# ============================================================

_SIFAT_AR_PROTECTED: Dict[str, Tuple] = {

    r'استوى\s+على\s+العرش': (
        TermCategory.SIFAT_ILAHIYYA, TermSeverity.CRITIQUE,
        'استوى على العرش — الترجمة الوحيدة المقبولة: "S\'est établi sur le Trône"',
        'Istawā ʿalā al-ʿArsh — traduction imposée : "S\'est établi sur le Trône"',
    ),
    r'\bاستوى\b': (
        TermCategory.SIFAT_ILAHIYYA, TermSeverity.CRITIQUE,
        'استوى — يُترجم: "S\'est établi" فحسب، لا "s\'est élevé" ولا "استقر"',
        'Istawā — traduit : "S\'est établi" uniquement (jamais "s\'est élevé")',
    ),
    r'يدَا?\s+الله': (
        TermCategory.SIFAT_ILAHIYYA, TermSeverity.CRITIQUE,
        'يد الله / يدا الله — الترجمة الحرفية: "la Main d\'Allah" / "les deux Mains d\'Allah"',
        'Yad Allāh — traduction littérale imposée : "la Main d\'Allah"',
    ),
    r'\bيده\b': (
        TermCategory.SIFAT_ILAHIYYA, TermSeverity.CRITIQUE,
        'يده — يُترجم: "Sa Main" فقط',
        'Yadahu — traduit : "Sa Main" uniquement',
    ),
    r'\bيديه\b': (
        TermCategory.SIFAT_ILAHIYYA, TermSeverity.CRITIQUE,
        'يديه — يُترجم: "Ses deux Mains" فقط',
        'Yadayhi — traduit : "Ses deux Mains" uniquement',
    ),
    r'وجه\s+الله': (
        TermCategory.SIFAT_ILAHIYYA, TermSeverity.CRITIQUE,
        'وجه الله — الترجمة الحرفية: "la Face d\'Allah" (لا: "l\'essence")',
        'Wajh Allāh — traduction littérale : "la Face d\'Allah" (jamais "l\'essence")',
    ),
    r'\bوجهه\b': (
        TermCategory.SIFAT_ILAHIYYA, TermSeverity.CRITIQUE,
        'وجهه — يُترجم: "Sa Face" فقط',
        'Wajhahu — traduit : "Sa Face" uniquement',
    ),
    r'عين\s+الله': (
        TermCategory.SIFAT_ILAHIYYA, TermSeverity.CRITIQUE,
        'عين الله — يُترجم: "l\'Œil d\'Allah"',
        'ʿAyn Allāh — traduit : "l\'Œil d\'Allah"',
    ),
    r'\bعينه\b': (
        TermCategory.SIFAT_ILAHIYYA, TermSeverity.CRITIQUE,
        'عينه — يُترجم: "Son Œil"',
        'ʿAynahu — traduit : "Son Œil"',
    ),
    r'\b(?:ينزل|نزل)\b': (
        TermCategory.SIFAT_ILAHIYYA, TermSeverity.CRITIQUE,
        'نزول الله — يُترجم: "descend / est descendu" لا "se manifeste"',
        'Nuzūl d\'Allah — traduit : "descend / est descendu" (jamais "se manifeste")',
    ),
    r'\b(?:يأتي|أتى|جاء|يجيء)\b': (
        TermCategory.SIFAT_ILAHIYYA, TermSeverity.CRITIQUE,
        'مجيء الله — يُترجم: "vient / est venu" بالمعنى الحقيقي اللائق بجلاله',
        'Majī\' d\'Allah — traduit : "vient / est venu" selon ce qui convient à Sa Majesté',
    ),
    r'\bفوق\b': (
        TermCategory.SIFAT_ILAHIYYA, TermSeverity.CRITIQUE,
        'فوق — يُترجم: "au-dessus" لا "au-delà"',
        'Fawq — traduit : "au-dessus" (jamais "au-delà")',
    ),
    r'\bالعلو\b|علو\s+الله': (
        TermCategory.SIFAT_ILAHIYYA, TermSeverity.CRITIQUE,
        'علو الله — العلو الذاتي ثابت بالكتاب والسنة والعقل والفطرة',
        'ʿUluw d\'Allah — élévation essentielle prouvée par le Coran, la Sunna et la raison',
    ),
    r'\bالفوقية\b': (
        TermCategory.SIFAT_ILAHIYYA, TermSeverity.CRITIQUE,
        'الفوقية: صفة ثابتة لله — يُترجم: "le fait d\'être au-dessus"',
        'Al-Fawqiyya — traduit : "le fait d\'être au-dessus"',
    ),
    r'على\s+العرش': (
        TermCategory.SIFAT_ILAHIYYA, TermSeverity.CRITIQUE,
        'على العرش — يُترجم: "sur le Trône"',
        'ʿAlā al-ʿArsh — traduit : "sur le Trône"',
    ),
}

# ============================================================
# TERMES TA'WÎL INTERDITS EN FRANÇAIS
# ============================================================

_TAWIL_FR_FORBIDDEN: Dict[str, Tuple] = {

    # ── TA'WÎL DE يد (Main d'Allah) ───────────────────────────────────────────
    r"\bpuissance\s+d['']Allah\b": (
        TermCategory.TAWIL_FR, TermSeverity.CRITIQUE,
        None,
        "Ta'wīl de يد الله par \"puissance d'Allah\" — interdit, terme kalam",
    ),
    r'\bsa\s+puissance\b': (
        TermCategory.TAWIL_FR, TermSeverity.CRITIQUE,
        None,
        'Ta\'wīl de يده par "sa puissance" — interdit',
    ),
    r'\bla\s+puissance\s+divine\b': (
        TermCategory.TAWIL_FR, TermSeverity.CRITIQUE,
        None,
        'Ta\'wīl générique des Attributs par "puissance divine" — interdit',
    ),

    # ── TA'WÎL DE وجه (Face d'Allah) ──────────────────────────────────────────
    r"\bessence\s+d['']Allah\b": (
        TermCategory.TAWIL_FR, TermSeverity.CRITIQUE,
        None,
        "Ta'wīl de وجه الله par \"essence d'Allah\" — interdit, terme soufie/mutakallimūn",
    ),
    r'\bson\s+essence\b': (
        TermCategory.TAWIL_FR, TermSeverity.CRITIQUE,
        None,
        'Ta\'wīl de وجهه par "son essence" — interdit',
    ),
    r"\bl['']essence\s+divine\b": (
        TermCategory.TAWIL_FR, TermSeverity.CRITIQUE,
        None,
        'Substitution philosophique de وجه par "essence divine" — interdit',
    ),

    # ── TA'WÎL DE نزل (descend) ───────────────────────────────────────────────
    r'\bse\s+manifeste\b': (
        TermCategory.TAWIL_FR, TermSeverity.CRITIQUE,
        None,
        'Ta\'wīl de ينزل par "se manifeste" — interdit (ta\'wīl des Ash\'aris)',
    ),
    r'\bsa\s+grâce\s+descend\b': (
        TermCategory.TAWIL_FR, TermSeverity.CRITIQUE,
        None,
        'Ta\'wīl du Nuzūl par "sa grâce descend" — substitution interdite',
    ),
    r"\bgrâce\s+d['']Allah\b": (
        TermCategory.TAWIL_FR, TermSeverity.CRITIQUE,
        None,
        "Ta'wīl de يد / رحمة par \"grâce d'Allah\" — interdit",
    ),

    # ── TA'WÎL DE استوى (S'est établi) ───────────────────────────────────────
    r"\bs['']élève\b": (
        TermCategory.TAWIL_FR, TermSeverity.CRITIQUE,
        None,
        "Ta'wīl de استوى par \"s'élève\" — interdit (ta'wīl al-Muʿtazila)",
    ),
    r"\bs['']installe\b": (
        TermCategory.TAWIL_FR, TermSeverity.CRITIQUE,
        None,
        "Ta'wīl de استوى par \"s'installe\" — interdit",
    ),
    r"\bs['']est\s+installé\b": (
        TermCategory.TAWIL_FR, TermSeverity.CRITIQUE,
        None,
        "Ta'wīl de استوى par \"s'est installé\" — interdit",
    ),
    r'\bprend\s+place\b': (
        TermCategory.TAWIL_FR, TermSeverity.CRITIQUE,
        None,
        'Ta\'wīl de استوى par "prend place" — interdit',
    ),

    # ── TA'WÎL DE فوق (au-dessus) ────────────────────────────────────────────
    r'\bau-delà\b': (
        TermCategory.TAWIL_FR, TermSeverity.CRITIQUE,
        None,
        'Ta\'wīl de فوق par "au-delà" — interdit (efface l\'élévation réelle)',
    ),

    # ── TERMES MÉTAPHORIQUES / ALLÉGORIQUES ──────────────────────────────────
    r'\bmétaphor\w*\b': (
        TermCategory.TAWIL_FR, TermSeverity.CRITIQUE,
        None,
        'Terme métaphorique — toute lecture métaphorique des Attributs est ta\'wīl',
    ),
    r'\ballégori\w*\b': (
        TermCategory.TAWIL_FR, TermSeverity.CRITIQUE,
        None,
        'Terme allégorique — ta\'wīl allégorique des Attributs divins interdit',
    ),
    r'\bsens\s+figuré\b': (
        TermCategory.TAWIL_FR, TermSeverity.CRITIQUE,
        None,
        '"Sens figuré" — ta\'wīl explicite, blocage absolu pour les Attributs',
    ),
    r'\bsymboliqu\w*\b': (
        TermCategory.TAWIL_FR, TermSeverity.CRITIQUE,
        None,
        'Interprétation symbolique — contraire au manhaj des Salaf al-Ṣāliḥ',
    ),
    r'\bne\s+pas\s+prendre\s+au\s+pied\s+de\s+la\s+lettre\b': (
        TermCategory.TAWIL_FR, TermSeverity.CRITIQUE,
        None,
        'Instruction de ta\'wīl explicite — blocage absolu',
    ),
    r'\bfigurativement\b': (
        TermCategory.TAWIL_FR, TermSeverity.CRITIQUE,
        None,
        '"Figurativement" — ta\'wīl déguisé, interdit pour les Attributs',
    ),

    # ── TERMES PHILOSOPHIQUES SUSPECTS ───────────────────────────────────────
    r'\bimmanent\w*\b': (
        TermCategory.TAWIL_FR, TermSeverity.AVERTISSEMENT,
        None,
        '"Immanent" — terme philosophique adjacent au Ḥulūl, Tawaqquf requis',
    ),
    r'\bprésence\s+divine\b': (
        TermCategory.TAWIL_FR, TermSeverity.AVERTISSEMENT,
        None,
        '"Présence divine" — formulation peut tendre vers le Ḥulūl',
    ),
    r'\blumière\s+divine\b': (
        TermCategory.TAWIL_FR, TermSeverity.AVERTISSEMENT,
        None,
        '"Lumière divine" — formulation soufie suspecte dans le contexte des Attributs',
    ),
    r'\banthropo\w*\b': (
        TermCategory.TAWIL_FR, TermSeverity.AVERTISSEMENT,
        None,
        '"Anthropomorphisme" — accusation de Tajsīm souvent inexacte envers l\'ithbāt',
    ),
    r'\btranscend\w*\b': (
        TermCategory.TAWIL_FR, TermSeverity.AVERTISSEMENT,
        None,
        '"Transcendant/transcendance" — terme philosophique à vérifier dans contexte',
    ),
    r"\breprésen\w*\s+(?:d['']Allah|divin\w*)\b": (
        TermCategory.TAWIL_FR, TermSeverity.AVERTISSEMENT,
        None,
        '"Représentation divine" — terminologie suspecte pour les Attributs',
    ),
}

# ============================================================
# FONCTIONS DE SCAN
# ============================================================

_CONTEXT_WINDOW = 60


def _extract_context(text: str, start: int, end: int) -> str:
    ctx_start = max(0, start - _CONTEXT_WINDOW)
    ctx_end = min(len(text), end + _CONTEXT_WINDOW)
    snippet = text[ctx_start:ctx_end]
    prefix = '…' if ctx_start > 0 else ''
    suffix = '…' if ctx_end < len(text) else ''
    return prefix + snippet + suffix


def scan_arabic(text: str) -> List[TermMatch]:
    """
    Scanne un texte arabe :
    - Termes Bid'ah (Ḥulūl, Ittiḥād, Waḥdat al-wujūd, Ta'ṭīl, Ta'wīl, Tafwīḍ…)
    - Attributs divins protégés (vérifie la présence pour forcer Lexique de Fer)
    """
    matches: List[TermMatch] = []
    all_patterns = {**_BIDAH_AR, **_SIFAT_AR_PROTECTED}

    for pattern, (category, severity, note_ar, note_fr) in all_patterns.items():
        for m in re.finditer(pattern, text, re.UNICODE):
            matches.append(TermMatch(
                term=m.group(),
                category=category,
                severity=severity,
                context=_extract_context(text, m.start(), m.end()),
                position=m.start(),
                requires_tawaqquf=(severity == TermSeverity.CRITIQUE),
                note_ar=note_ar,
                note_fr=note_fr,
            ))

    return matches


def scan_french(text: str) -> List[TermMatch]:
    """
    Scanne un texte français pour détecter les formulations de ta'wîl interdites
    et les termes philosophiques suspects.
    """
    matches: List[TermMatch] = []

    for pattern, (category, severity, note_ar, note_fr) in _TAWIL_FR_FORBIDDEN.items():
        for m in re.finditer(pattern, text, re.IGNORECASE | re.UNICODE):
            matches.append(TermMatch(
                term=m.group(),
                category=category,
                severity=severity,
                context=_extract_context(text, m.start(), m.end()),
                position=m.start(),
                requires_tawaqquf=(severity == TermSeverity.CRITIQUE),
                note_ar=note_ar,
                note_fr=note_fr,
            ))

    return matches


def requires_tawaqquf(matches: List[TermMatch]) -> bool:
    """Retourne True si au moins un match de sévérité CRITIQUE est présent."""
    return any(m.severity == TermSeverity.CRITIQUE for m in matches)


def get_tawaqquf_report(matches: List[TermMatch]) -> str:
    """Génère un rapport textuel lisible pour le journal et le débogage."""
    if not matches:
        return "✅ Aucun terme protégé détecté."

    lines = [f"⚠️  {len(matches)} terme(s) protégé(s) détecté(s) :"]
    for m in matches:
        icon = "🔴" if m.severity == TermSeverity.CRITIQUE else "🟠"
        note = m.note_fr or m.note_ar or "—"
        lines.append(
            f"  {icon} [{m.category.value.upper()}] « {m.term} »"
            f"\n      ↳ {note}"
        )

    if requires_tawaqquf(matches):
        lines.append("\n🛑 TAWAQQUF forcé — verdict suspendu, vérification humaine requise.")

    return "\n".join(lines)
