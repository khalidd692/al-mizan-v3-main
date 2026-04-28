"""Lexique FR→AR pour la recherche locale Al-Mīzān.

Convertit les mots-clés français usuels en équivalents arabes (sans tashkeel)
afin que la recherche LIKE matche les colonnes ar_text/ar_text_clean en plus
de fr_text. Comprend aussi une whitelist de hadiths apocryphes (mawdū‘)
classiques pour fournir le grade authentique sans dépendre du corpus indexé.
"""
from __future__ import annotations

# FR (lowercase) → liste d'équivalents AR sans tashkeel.
FR_TO_AR: dict[str, list[str]] = {
    # Concepts fondamentaux
    "intention": ["النية", "النيات", "نية"],
    "intentions": ["النية", "النيات", "نية"],
    "niyya": ["النية", "نية"],
    "actes": ["الأعمال", "العمل"],
    "oeuvres": ["الأعمال"],
    "savoir": ["العلم", "علم"],
    "science": ["العلم", "علم"],
    "connaissance": ["العلم", "المعرفة"],
    "savant": ["العالم", "العلماء"],
    "savants": ["العلماء"],
    "ignorance": ["الجهل"],
    "ilm": ["العلم"],
    # Croyance
    "foi": ["الإيمان", "إيمان"],
    "croyance": ["الإيمان", "العقيدة"],
    "iman": ["الإيمان"],
    "tawhid": ["التوحيد"],
    "shirk": ["الشرك"],
    # Piliers
    "patience": ["الصبر", "صبر"],
    "prière": ["الصلاة", "صلاة"],
    "priere": ["الصلاة"],
    "salat": ["الصلاة"],
    "jeûne": ["الصوم", "الصيام"],
    "jeune": ["الصوم", "الصيام"],
    "ramadan": ["رمضان"],
    "aumône": ["الزكاة", "الصدقة"],
    "aumone": ["الزكاة", "الصدقة"],
    "zakat": ["الزكاة"],
    "sadaqa": ["الصدقة"],
    "pèlerinage": ["الحج"],
    "pelerinage": ["الحج"],
    "hajj": ["الحج"],
    "umra": ["العمرة"],
    # Eschatologie
    "paradis": ["الجنة"],
    "enfer": ["النار", "جهنم"],
    "ange": ["الملك", "الملائكة"],
    "anges": ["الملائكة"],
    # Personnes
    "prophète": ["النبي", "الرسول"],
    "prophete": ["النبي", "الرسول"],
    "messager": ["الرسول"],
    "compagnon": ["الصحابي", "الصحابة"],
    "compagnons": ["الصحابة"],
    "musulman": ["المسلم", "المسلمين"],
    "musulmans": ["المسلمين"],
    "croyant": ["المؤمن", "المؤمنين"],
    "croyants": ["المؤمنين"],
    # Spirituel
    "péché": ["الذنب", "المعصية"],
    "peche": ["الذنب", "المعصية"],
    "péchés": ["الذنوب"],
    "peches": ["الذنوب"],
    "repentir": ["التوبة"],
    "tawba": ["التوبة"],
    "amour": ["الحب", "حب"],
    "haine": ["البغض"],
    "patrie": ["الوطن"],
    # Géographie
    "chine": ["الصين"],
    "médine": ["المدينة"],
    "medine": ["المدينة"],
    "mecque": ["مكة"],
    "kaaba": ["الكعبة"],
    # Verbes / actions
    "cherchez": ["اطلبوا", "ابتغوا"],
    "chercher": ["طلب", "ابتغاء"],
    "demande": ["اطلب", "اسأل"],
    "demander": ["السؤال"],
    "voyager": ["السفر"],
    "voyage": ["السفر"],
    # Famille / société
    "mère": ["الأم"],
    "mere": ["الأم"],
    "père": ["الأب"],
    "pere": ["الأب"],
    "parents": ["الوالدين", "الوالدان"],
    "voisin": ["الجار", "الجيران"],
    "voisins": ["الجيران"],
    "orphelin": ["اليتيم"],
    "pauvre": ["المسكين", "الفقير"],
    "riche": ["الغني"],
}


def get_token_groups(tokens_fr: list[str]) -> list[list[str]]:
    """Pour chaque token FR, retourne le groupe [token_fr, *équivalents_ar].

    Un « groupe » représente un concept unique : matcher n'importe lequel de
    ses tokens (FR ou AR) compte pour 1 concept retrouvé. Cela évite que la
    duplication FR+AR fausse le ratio de pertinence.
    """
    groups: list[list[str]] = []
    for tok in tokens_fr:
        ar = FR_TO_AR.get(tok.lower(), [])
        groups.append([tok] + ar)
    return groups


# ── Whitelist des hadiths apocryphes (mawdū‘) classiques ──────────────
# Chaque entrée déclenche un retour direct si tous les motifs match_fr_all
# OU tous les motifs match_ar_all sont présents dans la requête (lower).
MAWDU_WHITELIST: list[dict] = [
    {
        "name": "savoir_chine",
        "match_fr_all": ["savoir", "chine"],
        "match_fr_alt": [["science", "chine"], ["connaissance", "chine"]],
        "match_ar_all": ["العلم", "الصين"],
        "row": {
            "id": "mawdu-001",
            "ar_text": "اطلبوا العلم ولو بالصين",
            "ar_text_clean": "اطلبوا العلم ولو بالصين",
            "ar_narrator": "—",
            "ar_full_isnad": "—",
            "fr_text": "Cherchez la science même en Chine.",
            "fr_summary": (
                "Hadith très répandu mais classé apocryphe (mawdū‘) par les "
                "muḥaddithūn. Aucune chaîne authentique ne le rattache au "
                "Prophète ﷺ."
            ),
            "grade_primary": "Mawdu'",
            "grade_by_mohdith": "Ibn al-Jawzī, Ibn Ḥibbān, al-Albānī",
            "grade_explanation": (
                "Mentionné par Ibn al-Jawzī dans Al-Mawḍū‘āt (1/215) et "
                "déclaré bāṭil. Al-Albānī l'a classé Mawḍū‘ dans Silsilat "
                "al-Aḥādīth aḍ-Ḍa‘īfa wal-Mawḍū‘a (n°416)."
            ),
            "grade_albani": "Mawdu'",
            "grade_ibn_baz": "",
            "grade_ibn_uthaymin": "",
            "grade_muqbil": "",
            "book_name_ar": "—",
            "book_name_fr": "Hadith apocryphe (mawdū‘)",
            "hadith_number": "",
            "hadith_id_dorar": "",
            "source_api": "whitelist_mawdu",
            "source_url": "",
            "takhrij": (
                "Ibn al-Jawzī, Al-Mawḍū‘āt 1/215 ; "
                "al-Albānī, aḍ-Ḍa‘īfa n°416."
            ),
            "zone_id": 0,
        },
    },
    {
        "name": "amour_patrie_foi",
        "match_fr_all": ["amour", "patrie"],
        "match_ar_all": ["حب", "الوطن"],
        "row": {
            "id": "mawdu-002",
            "ar_text": "حب الوطن من الإيمان",
            "ar_text_clean": "حب الوطن من الإيمان",
            "ar_narrator": "—",
            "ar_full_isnad": "—",
            "fr_text": "L'amour de la patrie fait partie de la foi.",
            "fr_summary": (
                "Adage populaire faussement attribué au Prophète ﷺ — sans "
                "chaîne authentique."
            ),
            "grade_primary": "Mawdu'",
            "grade_by_mohdith": "as-Sakhāwī, al-Albānī",
            "grade_explanation": (
                "As-Sakhāwī écrit dans al-Maqāṣid al-Ḥasana (n°386) : "
                "« Lā aṣla lahu » (sans fondement). Al-Albānī le classe "
                "Mawḍū‘ dans aḍ-Ḍa‘īfa (n°36)."
            ),
            "grade_albani": "Mawdu'",
            "grade_ibn_baz": "",
            "grade_ibn_uthaymin": "",
            "grade_muqbil": "",
            "book_name_ar": "—",
            "book_name_fr": "Hadith apocryphe (mawdū‘)",
            "hadith_number": "",
            "hadith_id_dorar": "",
            "source_api": "whitelist_mawdu",
            "source_url": "",
            "takhrij": (
                "as-Sakhāwī, al-Maqāṣid al-Ḥasana n°386 ; "
                "al-Albānī, aḍ-Ḍa‘īfa n°36."
            ),
            "zone_id": 0,
        },
    },
]


def check_mawdu_whitelist(query: str) -> dict | None:
    """Renvoie une copie de la row whitelistée si la requête correspond à un
    mawdū‘ connu, sinon None.

    Match : tous les motifs FR (ou une alternative `match_fr_alt`) présents
    dans la requête en minuscules, OU tous les motifs AR présents tels quels.
    """
    q_lower = query.lower()
    for entry in MAWDU_WHITELIST:
        fr_all = entry.get("match_fr_all") or []
        if fr_all and all(m.lower() in q_lower for m in fr_all):
            return dict(entry["row"])

        for alt in entry.get("match_fr_alt") or []:
            if alt and all(m.lower() in q_lower for m in alt):
                return dict(entry["row"])

        ar_all = entry.get("match_ar_all") or []
        if ar_all and all(m in query for m in ar_all):
            return dict(entry["row"])
    return None
