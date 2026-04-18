"""
Bouclier Doctrinal — AL-MĪZĀN V7.0
Lexique de Fer + Filtres Bid'ah/Ta'wîl.

Point d'entrée unique pour tous les contrôles doctrinaux du pipeline.
Remplace les stubs no-op de la phase 1.
"""

from __future__ import annotations

from typing import List, Tuple

from backend.utils.lexique_de_fer import valider_reponse_claude
from backend.utils.protected_terms import (
    TermMatch,
    get_tawaqquf_report,
    requires_tawaqquf,
    scan_arabic,
    scan_french,
)


def enforce_lexique_de_fer(chunk: str) -> str:
    """
    Vérifie et corrige une traduction française selon le Lexique de Fer.
    Applique la correction automatique si possible (appliquer_lexique_post_traduction).
    Retourne le texte corrigé — ou l'original si déjà conforme.
    """
    _valid, corrected, _errors = valider_reponse_claude(chunk)
    return corrected


def check_forbidden_terms(text: str) -> List[str]:
    """
    Détecte les termes de ta'wîl et de Bid'ah dans un texte mixte AR/FR.
    Retourne une liste de descriptions lisibles pour le journal.
    Compatible avec l'interface existante de constitution.py.
    """
    matches_fr = scan_french(text)
    matches_ar = scan_arabic(text)
    all_matches: List[TermMatch] = matches_ar + matches_fr

    return [
        f"[{m.severity.value.upper()}] {m.category.value}"
        f" — « {m.term} »"
        f"{': ' + m.note_fr if m.note_fr else ''}"
        for m in all_matches
    ]


def run_full_doctrinal_check(
    text_ar: str,
    text_fr: str,
) -> Tuple[bool, str]:
    """
    Contrôle doctrinal complet sur la paire (arabe, français) d'un hadith.

    Étapes :
    1. Scan arabe (Bid'ah + Sifat protégées)
    2. Correction automatique du français via Lexique de Fer
    3. Scan français post-correction (ta'wîl interdit + termes suspects)
    4. Décision Tawaqquf (True si au moins un terme CRITIQUE)

    Returns:
        (tawaqquf_required: bool, rapport: str)
    """
    matches_ar = scan_arabic(text_ar)

    corrected_fr = enforce_lexique_de_fer(text_fr)
    matches_fr = scan_french(corrected_fr)

    all_matches: List[TermMatch] = matches_ar + matches_fr
    tawaqquf = requires_tawaqquf(all_matches)
    report = get_tawaqquf_report(all_matches)

    return tawaqquf, report
