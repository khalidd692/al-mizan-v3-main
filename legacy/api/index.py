"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  MÎZÂN AS-SUNNAH — api/index.py — Version 25.0                              ║
║  « Silsila al-Kâmila » — Extraction Chirurgicale de l'Isnâd                 ║
║                                                                              ║
║  ARCHITECTURE :                                                              ║
║    • Zéro hallucination : données manquantes = "Non spécifié dans la source" ║
║    • Dictionnaire _HUKM_AR_FR exhaustif (90+ grades)                        ║
║    • Système VETO : détonateurs annulant Sahîh (gris/ambigu)                ║
║    • get_grade_from_hukm : VETO → FAIBLESSE → ACCEPTATION                  ║
║    • XPath ultra-précis sur HTML Dorar.net (9 sélecteurs en cascade)        ║
║    • Flux SSE : INIT → TRADUCTION → DORAR → SANAD → HUKM → ENVOI           ║
║    • httpx asynchrone — aucun blocage possible                               ║
║    • Groupement des verdicts par Mohaddith (évite les contradictions)        ║
║    • Référence Takhrîj complète : Source + Volume + Page + Numéro           ║
║    • Tri Sahîh en tête de liste (index 0)                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import unicodedata
from http.server import BaseHTTPRequestHandler
from typing import Any, AsyncGenerator
from urllib.parse import urlparse, parse_qs

import httpx
from lxml import html as lxml_html
from pydantic import BaseModel

# ─────────────────────────────────────────────────────────────────────────────
#  MODÈLE PYDANTIC — VALIDATION NŒUD SILSILA
# ─────────────────────────────────────────────────────────────────────────────

class SilsilaNode(BaseModel):
    rank: int = 0
    name_ar: str
    fr_name: str = ""
    role: str = "narrator"
    rawi_id: str | None = None
    rawi_url: str = ""
    century: str = ""
    death_year: int = 9999
    verified: bool = False


class HadithEnrichment(BaseModel):
    """
    Enrichissement textuel produit SOUS CONTRAINTE « Zéro Hallucination ».

    Chaque champ est soit :
      • une chaîne vide (absence honnête — Dorar ne contient pas l'info)
      • une chaîne renseignée (présence attestée, citation obligatoire)

    Règle d'or : aucun champ n'est jamais inventé par Claude.
    Source : .clauderules R8 (Protection Zones Al-Albani) + R21 (Test de
    Restauration Nulle) + demande utilisateur Action 2 (Amâna Médine).
    """
    grille_albani: str      = ""   # Verdict(s) d'Al-Albânî présents dans all_verdicts
    shurut_sihhah: str      = ""   # 5 conditions du Sahîh — déduites DÉTERMINISTEMENT
    gharib: str             = ""   # Vocabulaire des mots rares — Claude strict
    sabab_wurud: str        = ""   # Circonstance de narration — Claude strict (très rare)
    fawaid: str             = ""   # Leçons pratiques — Claude strict


# ─────────────────────────────────────────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[Mîzân v24 %(levelname)s] %(message)s",
)
log = logging.getLogger("mizan_v24")

# ─────────────────────────────────────────────────────────────────────────────
#  CONSTANTES
# ─────────────────────────────────────────────────────────────────────────────
VERSION         = "25.0"
DORAR_API_URL   = "https://dorar.net/dorar_api.json"
DORAR_BASE      = "https://dorar.net"
ANTHROPIC_URL   = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-sonnet-4-6"
MAX_RESULTS     = 5
TIMEOUT_DORAR   = 18.0
TIMEOUT_DETAIL  = 10.0
TIMEOUT_CLAUDE  = 12.0

# Constante de données manquantes — affiché à la place d'un champ vide
MISSING = "Non spécifié dans la source"

# ── Vérification startup : ANTHROPIC_API_KEY ────────────────────────────────
# Le grade vient exclusivement de Dorar.net et n'est JAMAIS corrompu par
# l'absence de clé. Seuls la traduction FR et l'enrichissement sont affectés.
if not os.environ.get("ANTHROPIC_API_KEY"):
    log.warning(
        "[STARTUP] ANTHROPIC_API_KEY absente — traduction FR→AR, "
        "traduction matn AR→FR et enrichissement IA désactivés. "
        "Les grades (hukm) ne sont PAS affectés."
    )


# ─────────────────────────────────────────────────────────────────────────────
#  █  DICTIONNAIRE HUKM — VERROUILLÉ — ZÉRO TRADUCTION EXTERNE
#
#  Sources doctrinales :
#    • Taysîr Mustalah al-Hadîth (Dr. Mahmûd al-Tahhân)
#    • Al-Bâ'ith al-Hathîth (Ahmad Shâkir sur Ibn Kathîr)
#    • Minhaj al-Naqd (Dr. Nûr al-Dîn 'Itr)
#    • An-Nukat 'alâ Ibn al-Salâh (Ibn Hajar al-'Asqalânî)
#
#  RÈGLE ABSOLUE : Si l'arabe dit "صحيح لغيره", afficher UNIQUEMENT
#  "Authentique par accumulation (Sahîh li-ghayrihi)". Rien d'autre.
# ─────────────────────────────────────────────────────────────────────────────
_HUKM_AR_FR: dict[str, dict[str, Any]] = {

    # ══ GRADES SAHIH ══════════════════════════════════════════════════════
    "صحيح": {
        "fr": "Authentique (Sahîh)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": (
            "Hadith dont la chaîne est continue de bout en bout, transmis par des "
            "narrateurs intègres ('adl) et précis (dâbit), sans anomalie (shudh) "
            "ni défaut caché ('illah)."
        ),
    },
    "صحيح لذاته": {
        "fr": "Authentique par lui-même (Sahîh li-dhâtihi)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": (
            "Hadith remplissant toutes les conditions du Sahîh de manière "
            "intrinsèque, sans recours à des voies de renfort."
        ),
    },
    "صحيح لغيره": {
        "fr": "Authentique par accumulation (Sahîh li-ghayrihi)",
        "level": "sahih",
        "color": "#16a34a",
        "definition": (
            "Hadith hasan dont la multiplicité des voies de transmission (turuq) "
            "compense les légères faiblesses et élève son degré au rang du Sahîh."
        ),
    },
    "صحيح الإسناد": {
        "fr": "Chaîne authentique (Sahîh al-Isnâd)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": (
            "Le muhaddith certifie l'authenticité de la chaîne uniquement, "
            "sans se prononcer explicitement sur le matn."
        ),
    },
    "إسناده صحيح": {
        "fr": "Sa chaîne est authentique (Isnâduhu Sahîh)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": "Formulation équivalente à Sahîh al-Isnâd.",
    },
    "إسناده ثابت": {
        "fr": "Sa chaîne est établie (Isnâduhu Thâbit)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": (
            "La chaîne de transmission est solidement prouvée et fiable "
            "selon les critères des muhaddithîn."
        ),
    },
    "رجاله ثقات": {
        "fr": "Ses narrateurs sont fiables (Rijâluhu Thiqât)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": (
            "Chaque narrateur de la chaîne a été classifié comme thiqah "
            "(fiable et précis) par les imams du Jarh wa at-Ta'dîl."
        ),
    },
    "رجاله رجال الصحيح": {
        "fr": "Ses narrateurs sont ceux du Sahîh (Rijâluhu Rijâl as-Sahîh)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": (
            "Tous les narrateurs de la chaîne figurent parmi les rapporteurs "
            "utilisés par Al-Bukhârî ou Muslim dans leur Sahîh."
        ),
    },
    "حديث مقبول": {
        "fr": "Hadith accepté (Hadîth Maqbûl)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": "Hadith reçu et accepté par les muhaddithîn.",
    },
    "حديث محتج به": {
        "fr": "Hadith servant de preuve (Hadîth Muhtajj bihi)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": "Hadith constituant un argument juridique valide (hujja).",
    },
    "حديث معمول به": {
        "fr": "Hadith mis en pratique (Hadîth Ma'mûl bihi)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": "Hadith sur lequel les fuqahâ' fondent des rulings pratiques.",
    },
    "حديث صحيح الإسناد": {
        "fr": "Hadith à chaîne authentique (Hadîth Sahîh al-Isnâd)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": "Formulation explicite certifiant la chaîne comme authentique.",
    },
    "حديث حسن الإسناد": {
        "fr": "Hadith à chaîne bonne (Hadîth Hasan al-Isnâd)",
        "level": "hasan",
        "color": "#84cc16",
        "definition": "Formulation certifiant la chaîne au rang de Hasan.",
    },
    "حديث جيد الإسناد": {
        "fr": "Hadith à chaîne solide (Hadîth Jayyid al-Isnâd)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": (
            "Terme d'approbation utilisé notamment par Ad-Dâraqutnî et Ibn Hajar, "
            "synonyme de Hasan fort tendant vers le Sahîh."
        ),
    },
    "حديث قوي": {
        "fr": "Hadith solide (Hadîth Qawî)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": "Hadith dont la chaîne est jugée forte et fiable.",
    },
    "حديث ثابت": {
        "fr": "Hadith établi (Hadîth Thâbit)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": "Hadith dont l'authenticité est fermement prouvée.",
    },
    "حديث محفوظ": {
        "fr": "Hadith préservé (Hadîth Mahfûz)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": (
            "Hadith jugé correct face à une version contradictoire d'un narrateur "
            "moins fiable (opposé de Shâdhdh)."
        ),
    },
    "حديث معروف": {
        "fr": "Hadith connu (Hadîth Ma'rûf)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": (
            "Hadith reconnu et accepté par les muhaddithîn, opposé du Munkar."
        ),
    },
    "حديث مسند": {
        "fr": "Hadith remontant au Prophète ﷺ (Hadîth Musnad)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": (
            "Hadith dont la chaîne remonte sans interruption au Prophète ﷺ "
            "avec mention explicite de chaque narrateur."
        ),
    },
    "حديث متصل": {
        "fr": "Hadith à chaîne continue (Hadîth Muttasil)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": (
            "Hadith dont chaque maillon de la chaîne est relié au suivant "
            "sans interruption, qu'il remonte au Prophète ﷺ ou à un Compagnon."
        ),
    },
    "حديث موصول": {
        "fr": "Hadith relié (Hadîth Mawsûl)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": "Synonyme de Muttasil — chaîne continue et ininterrompue.",
    },
    "حديث عال": {
        "fr": "Hadith à chaîne élevée (Hadîth 'Âlî)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": (
            "Hadith dont la chaîne comporte un nombre réduit de maillons, "
            "rapprochant du Prophète ﷺ — signe d'excellence."
        ),
    },
    "حديث عزيز": {
        "fr": "Hadith rare mais confirmé (Hadîth 'Azîz)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": (
            "Hadith transmis par au moins deux narrateurs à chaque niveau "
            "de la chaîne — confirmation par double voie."
        ),
    },
    "حديث مشهور": {
        "fr": "Hadith célèbre (Hadîth Mashhûr)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": (
            "Hadith transmis par trois narrateurs ou plus à chaque niveau "
            "de la chaîne sans atteindre le degré du Mutawâtir."
        ),
    },
    "حديث مستفيض": {
        "fr": "Hadith largement diffusé (Hadîth Mustafîd)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": (
            "Synonyme de Mashhûr — hadith transmis par un grand nombre "
            "de narrateurs à chaque génération."
        ),
    },
    "حديث متواتر": {
        "fr": "Hadith transmis par multitudes (Hadîth Mutawâtir)",
        "level": "sahih",
        "color": "#15803d",
        "definition": (
            "Hadith rapporté par un si grand nombre de narrateurs à chaque "
            "génération qu'il est impossible qu'ils se soient concertés pour mentir. "
            "Degré le plus élevé de certitude."
        ),
    },
    "متفق عليه": {
        "fr": "Unanimement reconnu (Muttafaq 'alayhi)",
        "level": "sahih",
        "color": "#15803d",
        "definition": (
            "Hadith rapporté à la fois par Al-Bukhârî et Muslim dans leur Sahîh "
            "respectif — plus haut degré d'authenticité consensuel."
        ),
    },
    "على شرط الشيخين": {
        "fr": "Selon les critères des Deux Cheikhs ('Alâ Shart ash-Shaykhayn)",
        "level": "sahih",
        "color": "#15803d",
        "definition": (
            "Hadith non rapporté par Bukhârî et Muslim mais dont les narrateurs "
            "remplissent tous les critères des Sahîhayn."
        ),
    },
    "على شرط البخاري": {
        "fr": "Selon les critères d'Al-Bukhârî ('Alâ Shart al-Bukhârî)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": (
            "Hadith dont les narrateurs remplissent les critères de sélection "
            "d'Al-Bukhârî dans son Sahîh."
        ),
    },
    "على شرط مسلم": {
        "fr": "Selon les critères de Muslim ('Alâ Shart Muslim)",
        "level": "sahih",
        "color": "#22c55e",
        "definition": (
            "Hadith dont les narrateurs remplissent les critères de sélection "
            "de Muslim dans son Sahîh."
        ),
    },
    "إسناده حسن": {
        "fr": "Sa chaîne est bonne (Isnâduhu Hasan)",
        "level": "hasan",
        "color": "#84cc16",
        "definition": "Formulation équivalente à Hasan al-Isnâd.",
    },

    # ══ GRADES HASAN ══════════════════════════════════════════════════════
    "حسن": {
        "fr": "Bon (Hasan)",
        "level": "hasan",
        "color": "#84cc16",
        "definition": (
            "Hadith dont tous les narrateurs sont connus et intègres, sans atteindre "
            "le degré de précision absolue du Sahîh, et dont la chaîne est continue."
        ),
    },
    "حسن لذاته": {
        "fr": "Bon par lui-même (Hasan li-dhâtihi)",
        "level": "hasan",
        "color": "#84cc16",
        "definition": (
            "Hadith remplissant les conditions du Hasan de manière intrinsèque, "
            "sans recours à des voies de renfort."
        ),
    },
    "حسن لغيره": {
        "fr": "Bon par accumulation (Hasan li-ghayrihi)",
        "level": "hasan",
        "color": "#65a30d",
        "definition": (
            "Hadith faible dont la multiplicité des voies compense la faiblesse "
            "et l'élève au degré du Hasan."
        ),
    },
    "حسن صحيح": {
        "fr": "Bon et authentique (Hasan Sahîh)",
        "level": "hasan",
        "color": "#4ade80",
        "definition": (
            "Formulation d'At-Tirmidhî indiquant soit que le hadith possède deux "
            "voies (l'une Hasan, l'autre Sahîh), soit que les savants divergent "
            "entre Hasan et Sahîh."
        ),
    },
    "حسن الإسناد": {
        "fr": "Chaîne bonne (Hasan al-Isnâd)",
        "level": "hasan",
        "color": "#84cc16",
        "definition": "Le muhaddith certifie la bonté de la chaîne uniquement.",
    },
    "مقبول": {
        "fr": "Acceptable (Maqbûl)",
        "level": "hasan",
        "color": "#a3e635",
        "definition": (
            "Terme technique d'Ibn Hajar désignant un narrateur dont le hadith "
            "est accepté en l'absence de contradicteur."
        ),
    },

    # ══ GRADES DA'IF ══════════════════════════════════════════════════════
    "ضعيف": {
        "fr": "Faible (Da'îf)",
        "level": "daif",
        "color": "#f59e0b",
        "definition": (
            "Hadith n'atteignant pas le degré du Hasan, en raison d'une coupure "
            "dans la chaîne, d'un narrateur défaillant dans son intégrité ou sa précision."
        ),
    },
    "ضعيف جداً": {
        "fr": "Très faible (Da'îf Jiddan)",
        "level": "daif",
        "color": "#d97706",
        "definition": (
            "Hadith dont la faiblesse est sévère : narrateur accusé de mensonge, "
            "de fabrication, ou chaîne comportant plusieurs défauts graves simultanés."
        ),
    },
    "ضعيف جدا": {
        "fr": "Très faible (Da'îf Jiddan)",
        "level": "daif",
        "color": "#d97706",
        "definition": "Variante orthographique de Da'îf Jiddan — même définition.",
    },
    "ضعيف بهذا الإسناد": {
        "fr": "Faible par cette chaîne (Da'îf bi-hâdhâ al-Isnâd)",
        "level": "daif",
        "color": "#f59e0b",
        "definition": (
            "Hadith faible spécifiquement par la voie de transmission citée, "
            "ne préjugeant pas d'autres voies éventuelles."
        ),
    },
    "حديث مردود": {
        "fr": "Hadith repoussé (Hadîth Mardûd)",
        "level": "daif",
        "color": "#f59e0b",
        "definition": "Hadith n'ayant pas rempli les conditions d'acceptation.",
    },
    "حديث غير مقبول": {
        "fr": "Hadith non accepté (Hadîth Ghayr Maqbûl)",
        "level": "daif",
        "color": "#f59e0b",
        "definition": "Hadith rejeté par les muhaddithîn pour cause de faiblesse.",
    },
    "لا يحتج به": {
        "fr": "On ne peut s'en servir de preuve (Lâ Yuhtajj bihi)",
        "level": "daif",
        "color": "#f59e0b",
        "definition": "Hadith inapte à fonder un argument juridique.",
    },
    "ضعيف الإسناد": {
        "fr": "Chaîne faible (Da'îf al-Isnâd)",
        "level": "daif",
        "color": "#f59e0b",
        "definition": (
            "Le muhaddith juge uniquement la chaîne faible, "
            "sans se prononcer sur le fond du matn."
        ),
    },
    "إسناده ضعيف": {
        "fr": "Sa chaîne est faible (Isnâduhu Da'îf)",
        "level": "daif",
        "color": "#f59e0b",
        "definition": "Formulation équivalente à Da'îf al-Isnâd.",
    },
    "واه": {
        "fr": "Très fragile (Wâhin)",
        "level": "daif",
        "color": "#d97706",
        "definition": (
            "Hadith extrêmement faible dont la chaîne est presque rédhibitoire."
        ),
    },
    "واه جداً": {
        "fr": "Extrêmement fragile (Wâhin Jiddan)",
        "level": "daif",
        "color": "#d97706",
        "definition": "Degré de faiblesse avoisinant le rejet total.",
    },
    "واه بهذا الإسناد": {
        "fr": "Fragile par cette chaîne (Wâhin bi-hâdhâ al-Isnâd)",
        "level": "daif",
        "color": "#d97706",
        "definition": "Hadith extrêmement faible par la voie citée spécifiquement.",
    },
    "ساقط": {
        "fr": "Tombé / Caduc (Sâqit)",
        "level": "rejected",
        "color": "#ef4444",
        "definition": "Hadith dont la chaîne est si faible qu'il est inutilisable.",
    },
    "ليس بثابت": {
        "fr": "Non établi (Laysa bi-Thâbit)",
        "level": "daif",
        "color": "#f59e0b",
        "definition": "Le hadith n'est pas prouvé selon les critères de la science du hadith.",
    },
    "ليس بصحيح": {
        "fr": "Non authentique (Laysa bi-Sahîh)",
        "level": "daif",
        "color": "#f59e0b",
        "definition": "Verdict explicite de non-authenticité.",
    },
    "ليس بمحفوظ": {
        "fr": "Non préservé (Laysa bi-Mahfûz)",
        "level": "daif",
        "color": "#f59e0b",
        "definition": (
            "Le hadith n'est pas reconnu comme la version correcte face aux "
            "contradictions dans la transmission."
        ),
    },
    "ليس بمعروف": {
        "fr": "Non connu (Laysa bi-Ma'rûf)",
        "level": "daif",
        "color": "#f59e0b",
        "definition": "Hadith non reconnu par les muhaddithîn.",
    },
    "ليس بالقوي": {
        "fr": "Pas solide (Laysa bi-l-Qawî)",
        "level": "daif",
        "color": "#f59e0b",
        "definition": "Hadith dont la force probante est insuffisante.",
    },
    "ليس بذاك القوي": {
        "fr": "Pas si solide que cela (Laysa bi-dhâk al-Qawî)",
        "level": "daif",
        "color": "#fbbf24",
        "definition": (
            "Formule d'adoucissement indiquant une faiblesse légère ; "
            "le hadith peut servir de renfort."
        ),
    },
    "ليس بذلك": {
        "fr": "Pas de ce rang-là (Laysa bi-dhâlik)",
        "level": "daif",
        "color": "#fbbf24",
        "definition": "Formule indiquant l'insuffisance du narrateur ou de la chaîne.",
    },
    "لين": {
        "fr": "Légèrement faible (Layyin)",
        "level": "daif",
        "color": "#fbbf24",
        "definition": (
            "Narrateur d'une intégrité acceptable mais dont la précision mémorielle "
            "est légèrement insuffisante. Son hadith peut servir de renfort."
        ),
    },
    "لين الحديث": {
        "fr": "Légèrement faible dans la narration (Layyin al-Hadîth)",
        "level": "daif",
        "color": "#fbbf24",
        "definition": (
            "Le narrateur commet quelques erreurs ; son hadith est retenu "
            "uniquement à titre complémentaire (shâhid ou mutâbi')."
        ),
    },
    "فيه ضعف": {
        "fr": "Comporte une faiblesse (Fîhi Da'f)",
        "level": "daif",
        "color": "#f59e0b",
        "definition": (
            "Le hadith présente une faiblesse identifiée mais non rédhibitoire ; "
            "il peut être cité à titre d'information."
        ),
    },
    "في إسناده ضعف": {
        "fr": "Sa chaîne comporte une faiblesse (Fî Isnâdihi Da'f)",
        "level": "daif",
        "color": "#f59e0b",
        "definition": "Faiblesse localisée dans la chaîne de transmission.",
    },
    "في إسناده مقال": {
        "fr": "Sa chaîne est sujette à discussion (Fî Isnâdihi Maqâl)",
        "level": "daif",
        "color": "#f59e0b",
        "definition": "La chaîne comporte un point de contestation entre savants.",
    },
    "في إسناده نظر": {
        "fr": "Sa chaîne nécessite examen (Fî Isnâdihi Nazar)",
        "level": "daif",
        "color": "#f59e0b",
        "definition": (
            "Terme prudent des muhaddithîn indiquant un doute sérieux "
            "sur la validité de la chaîne."
        ),
    },
    "فيه مقال": {
        "fr": "Sujet à discussion (Fîhi Maqâl)",
        "level": "daif",
        "color": "#f59e0b",
        "definition": (
            "Les savants divergent sur l'acceptabilité du narrateur ou de la chaîne ; "
            "la prudence s'impose."
        ),
    },
    "لا يصح في الباب شيء": {
        "fr": "Rien d'authentique dans ce chapitre (Lâ Yasihh fî al-Bâb Shay')",
        "level": "daif",
        "color": "#d97706",
        "definition": (
            "Verdict global indiquant qu'aucun hadith sur ce sujet n'atteint "
            "le degré d'authenticité."
        ),
    },
    "فيه متروك": {
        "fr": "Contient un narrateur abandonné (Fîhi Matrûk)",
        "level": "rejected",
        "color": "#ef4444",
        "definition": "La chaîne inclut un narrateur massivement rejeté.",
    },
    "فيه كذاب": {
        "fr": "Contient un menteur (Fîhi Kadhdhâb)",
        "level": "mawdu",
        "color": "#991b1b",
        "definition": "La chaîne inclut un narrateur accusé de mensonge délibéré.",
    },
    "فيه وضاع": {
        "fr": "Contient un fabricateur (Fîhi Waddâ')",
        "level": "mawdu",
        "color": "#7f1d1d",
        "definition": "La chaîne inclut un narrateur connu pour fabriquer des hadiths.",
    },
    "فيه متهم": {
        "fr": "Contient un narrateur accusé (Fîhi Muttaham)",
        "level": "rejected",
        "color": "#ef4444",
        "definition": (
            "La chaîne inclut un narrateur accusé de mensonge ou de fabrication "
            "sans preuve définitive."
        ),
    },
    "فيه مجهول": {
        "fr": "Contient un narrateur inconnu (Fîhi Majhûl)",
        "level": "daif",
        "color": "#f59e0b",
        "definition": "La chaîne inclut un narrateur dont l'identité ou la fiabilité est inconnue.",
    },
    "فيه من لم يسم": {
        "fr": "Contient un narrateur non nommé (Fîhi man lam Yusamm)",
        "level": "daif",
        "color": "#f59e0b",
        "definition": "La chaîne inclut un rapporteur dont le nom n'est pas mentionné.",
    },
    "فيه راو مبهم": {
        "fr": "Contient un narrateur ambigu (Fîhi Râwî Mubham)",
        "level": "daif",
        "color": "#f59e0b",
        "definition": "La chaîne inclut un narrateur dont l'identité est ambiguë.",
    },
    "فيه من لا يعرف": {
        "fr": "Contient un narrateur non identifié (Fîhi man lâ Yu'raf)",
        "level": "daif",
        "color": "#f59e0b",
        "definition": "La chaîne inclut un narrateur inconnu des spécialistes.",
    },
    "ليس بثقة": {
        "fr": "Non fiable (Laysa bi-Thiqah)",
        "level": "rejected",
        "color": "#ef4444",
        "definition": "Le narrateur est explicitement déclaré non fiable.",
    },
    "غير ثقة": {
        "fr": "Non fiable (Ghayr Thiqah)",
        "level": "rejected",
        "color": "#ef4444",
        "definition": "Formulation alternative déclarant le narrateur non fiable.",
    },
    "ذاهب الحديث": {
        "fr": "Hadith perdu / sans valeur (Dhâhib al-Hadîth)",
        "level": "rejected",
        "color": "#ef4444",
        "definition": "Son hadith est parti — terme de rejet sévère des muhaddithîn.",
    },
    "هالك": {
        "fr": "Perdu / Ruiné (Hâlik)",
        "level": "rejected",
        "color": "#dc2626",
        "definition": "Narrateur totalement rejeté et discrédité.",
    },
    "متروك الحديث": {
        "fr": "Hadith abandonné (Matrûk al-Hadîth)",
        "level": "rejected",
        "color": "#ef4444",
        "definition": (
            "Les muhaddithîn ont unanimement abandonné la narration de ce rapporteur."
        ),
    },
    "تركوه": {
        "fr": "Ils l'ont abandonné (Tarakûhu)",
        "level": "rejected",
        "color": "#ef4444",
        "definition": "Formule collective de rejet du narrateur par les imams.",
    },
    "مضطرب الحديث": {
        "fr": "Perturbé dans sa narration (Mudtarib al-Hadîth)",
        "level": "rejected",
        "color": "#f87171",
        "definition": (
            "Narrateur dont les transmissions sont contradictoires et incohérentes."
        ),
    },
    "يروي المناكير": {
        "fr": "Il rapporte des choses réprouvées (Yarwî al-Manâkîr)",
        "level": "rejected",
        "color": "#ef4444",
        "definition": "Narrateur connu pour transmettre des hadiths munkar.",
    },
    "يروي الموضوعات": {
        "fr": "Il rapporte des hadiths forgés (Yarwî al-Mawdû'ât)",
        "level": "mawdu",
        "color": "#7f1d1d",
        "definition": "Narrateur impliqué dans la transmission de hadiths fabriqués.",
    },
    "منكر الحديث": {
        "fr": "Réprouvé dans sa narration (Munkar al-Hadîth)",
        "level": "rejected",
        "color": "#ef4444",
        "definition": "Narrateur dont les hadiths sont massivement répréhensibles.",
    },
    "واهي الحديث": {
        "fr": "Fragile dans sa narration (Wâhî al-Hadîth)",
        "level": "daif",
        "color": "#d97706",
        "definition": "Narrateur dont les transmissions manquent de solidité.",
    },

    # ══ GRADES DÉFECTUEUX — RUPTURES DE CHAÎNE ═══════════════════════════
    "منكر": {
        "fr": "Répréhensible (Munkar)",
        "level": "rejected",
        "color": "#ef4444",
        "definition": (
            "Hadith transmis par un narrateur faible en contradiction directe avec "
            "un narrateur fiable. Terme de rejet formel dans la terminologie hadith."
        ),
    },
    "منكر جداً": {
        "fr": "Très répréhensible (Munkar Jiddan)",
        "level": "rejected",
        "color": "#dc2626",
        "definition": "Munkar aggravé — rejet catégorique et sans appel.",
    },
    "شاذ": {
        "fr": "Anomal / Déviant (Shâdhdh)",
        "level": "rejected",
        "color": "#f87171",
        "definition": (
            "Hadith dont un narrateur fiable contredit ce que rapportent d'autres "
            "narrateurs plus fiables ou plus nombreux."
        ),
    },
    "معلل": {
        "fr": "Défectueux caché (Mu'allal)",
        "level": "rejected",
        "color": "#dc2626",
        "definition": (
            "Hadith présentant un défaut caché ('illah) décelable uniquement par "
            "les experts du hadith."
        ),
    },
    "معلول": {
        "fr": "Défectueux caché (Ma'lûl)",
        "level": "rejected",
        "color": "#dc2626",
        "definition": (
            "Hadith présentant un défaut caché ('illah) décelable uniquement par "
            "les experts du hadith, malgré une apparence extérieure de solidité."
        ),
    },
    "معل": {
        "fr": "Défectueux (Mu'all)",
        "level": "rejected",
        "color": "#dc2626",
        "definition": "Variante de Ma'lûl — même définition.",
    },
    "فيه علة": {
        "fr": "Comporte un défaut caché (Fîhi 'Illah)",
        "level": "rejected",
        "color": "#dc2626",
        "definition": "Hadith comportant une 'illah (défaut subtil) identifiée.",
    },
    "مضطرب": {
        "fr": "Perturbé / Contradictoire (Mudtarib)",
        "level": "rejected",
        "color": "#f87171",
        "definition": (
            "Hadith rapporté de manières contradictoires (dans la chaîne ou le texte) "
            "sans qu'il soit possible de déterminer la version correcte."
        ),
    },
    "مقلوب": {
        "fr": "Inversé (Maqlûb)",
        "level": "rejected",
        "color": "#f87171",
        "definition": (
            "Hadith dont un nom de narrateur ou une portion du texte a été "
            "intervertie avec un autre."
        ),
    },
    "مدرج": {
        "fr": "Interpolé (Mudraj)",
        "level": "rejected",
        "color": "#fca5a5",
        "definition": (
            "Hadith dont le texte a été mélangé avec des paroles d'un narrateur "
            "sans séparation apparente."
        ),
    },
    "مصحف": {
        "fr": "Altéré par erreur d'écriture (Musahhaf)",
        "level": "rejected",
        "color": "#f87171",
        "definition": (
            "Hadith contenant une erreur de transcription altérant les points "
            "diacritiques des lettres (ex: حسن → خشن)."
        ),
    },
    "محرف": {
        "fr": "Altéré par déformation (Muharraf)",
        "level": "rejected",
        "color": "#f87171",
        "definition": (
            "Hadith contenant une erreur altérant les voyelles (tashkîl) "
            "ou la forme des mots sans changer les points."
        ),
    },
    "مدلس": {
        "fr": "Objet de talbîs / Dissimulé (Mudallis)",
        "level": "rejected",
        "color": "#fb7185",
        "definition": (
            "Le narrateur dissimule un défaut dans la chaîne ou présente une "
            "transmission directe fictive (tadlîs al-isnâd)."
        ),
    },
    "فيه انقطاع": {
        "fr": "Comporte une coupure (Fîhi Inqitâ')",
        "level": "rejected",
        "color": "#fb923c",
        "definition": "La chaîne contient une rupture de transmission identifiée.",
    },
    "ليس بمتصل": {
        "fr": "Chaîne non continue (Laysa bi-Muttasil)",
        "level": "rejected",
        "color": "#fb923c",
        "definition": "La continuité de la chaîne n'est pas établie.",
    },
    "مرسل": {
        "fr": "Interrompu côté Successeur (Mursal)",
        "level": "rejected",
        "color": "#f97316",
        "definition": (
            "Un Successeur (tâbi'î) cite directement le Prophète ﷺ sans mentionner "
            "le Compagnon intermédiaire."
        ),
    },
    "منقطع": {
        "fr": "Coupé (Munqati')",
        "level": "rejected",
        "color": "#fb923c",
        "definition": (
            "La chaîne comporte une coupure en un ou plusieurs endroits, "
            "hors le cas du Mursal."
        ),
    },
    "معضل": {
        "fr": "Doublement interrompu (Mu'dal)",
        "level": "rejected",
        "color": "#f87171",
        "definition": (
            "La chaîne comporte deux maillons consécutifs manquants ou plus."
        ),
    },
    "معلق": {
        "fr": "Suspendu / Début de chaîne omis (Mu'allaq)",
        "level": "rejected",
        "color": "#fca5a5",
        "definition": (
            "Un ou plusieurs narrateurs du début de la chaîne ont été omis "
            "par le compilateur."
        ),
    },
    "مقطوع": {
        "fr": "Arrêté au Successeur (Maqtû')",
        "level": "mawquf",
        "color": "#94a3b8",
        "definition": (
            "Paroles ou actes d'un Successeur (tâbi'î), non attribués au Prophète ﷺ."
        ),
    },
    "موقوف": {
        "fr": "Arrêté au Compagnon (Mawqûf)",
        "level": "mawquf",
        "color": "#94a3b8",
        "definition": (
            "Paroles ou actes d'un Compagnon (sahâbî), non attribués au Prophète ﷺ."
        ),
    },

    # ══ GRADES FORGÉS ═════════════════════════════════════════════════════
    "موضوع": {
        "fr": "Forgé / Inventé (Mawdû')",
        "level": "mawdu",
        "color": "#7f1d1d",
        "definition": (
            "Hadith fabriqué et faussement attribué au Prophète ﷺ. "
            "Sa propagation est strictement interdite sauf pour mettre en garde."
        ),
    },
    "باطل": {
        "fr": "Nul et non avenu (Bâtil)",
        "level": "mawdu",
        "color": "#991b1b",
        "definition": (
            "Hadith dont le contenu ou la chaîne est manifestement faux, "
            "sans aucune base dans la Sunnah."
        ),
    },
    "لا أصل له": {
        "fr": "Sans fondement (Lâ Asl Lahu)",
        "level": "mawdu",
        "color": "#7f1d1d",
        "definition": (
            "Verdict des muhaddithîn indiquant qu'aucune chaîne valide "
            "ne rattache ce texte au Prophète ﷺ."
        ),
    },
    "لا يصح": {
        "fr": "Non authentifié (Lâ Yasihh)",
        "level": "mawdu",
        "color": "#991b1b",
        "definition": "Verdict catégorique d'invalidité, plus sévère que Da'îf.",
    },
    "لا يثبت": {
        "fr": "Non établi (Lâ Yathbut)",
        "level": "mawdu",
        "color": "#7f1d1d",
        "definition": (
            "Le hadith n'est pas prouvé selon les critères reconnus "
            "de la science du hadith."
        ),
    },
    "مكذوب": {
        "fr": "Mensonge attribué (Makdhûb)",
        "level": "mawdu",
        "color": "#991b1b",
        "definition": (
            "Hadith attribué mensongèrement au Prophète ﷺ, "
            "par un narrateur menteur ou un fabricateur."
        ),
    },
    "مختلق": {
        "fr": "Inventé de toutes pièces (Mukhtalaq)",
        "level": "mawdu",
        "color": "#7f1d1d",
        "definition": "Hadith fabriqué de manière délibérée.",
    },
    "مصنوع": {
        "fr": "Fabriqué (Masnû')",
        "level": "mawdu",
        "color": "#7f1d1d",
        "definition": "Synonyme de Mawdû' — hadith manufacturé et faussement attribué.",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
#  █  HUKM_GLOSSARY — DICTIONNAIRE ACADÉMIQUE EXHAUSTIF
#
#  Glossaire Mustalah al-Hadîth couvrant :
#    ① Catégorie ACCEPTATION  (Sahîh / Hasan et dérivés)
#    ② Catégorie FAIBLESSE    (Da'îf, Wâhin, Matrûk…)
#    ③ Critique des narrateurs (Jarh wa at-Ta'dîl) — termes de Ta'dîl & Jarh
#    ④ Défauts techniques     (Irsâl, Inqitâ', Tadlîs, 'Illah…)
#    ⑤ Catégories spéciales   (Mawqûf, Maqtû', Mutawâtir…)
#
#  Sources doctrinales :
#    • Muqaddimat Ibn as-Salâh (m. 643H)
#    • Taysîr Mustalah al-Hadîth (Dr. Mahmûd at-Tahhân)
#    • Nukhbat al-Fikar (Ibn Hajar al-'Asqalânî, m. 852H)
#    • Al-Bâ'ith al-Hathîth (Ahmad Shâkir sur Ibn Kathîr)
#    • Minhaj an-Naqd fî 'Ulûm al-Hadîth (Dr. Nûr ad-Dîn 'Itr)
#    • Tadrîb ar-Râwî (Jalâl ad-Dîn as-Suyûtî sur 'Ulûm d'Ibn as-Salâh)
#
#  Définitions françaises neutres et académiques, conformes à la méthodologie
#  des Salaf as-Sâlih et des Imams Mutaqaddimîn. Aucune interprétation sectaire.
# ─────────────────────────────────────────────────────────────────────────────
HUKM_GLOSSARY: dict[str, str] = {

    # ══════════════════════════════════════════════════════════════════════
    #  ① CATÉGORIE ACCEPTATION — Sahîh & Hasan (grades verts)
    # ══════════════════════════════════════════════════════════════════════

    "صحيح": (
        "Qualifie un hadith remplissant les cinq conditions canoniques définies par "
        "Ibn as-Salâh : chaîne de transmission continue (ittisâl as-sanad), intégrité "
        "morale de chaque rapporteur ('adâlat ar-ruwât), précision mémorielle de chaque "
        "rapporteur (dabt ar-ruwât), absence d'anomalie ('adam ash-shudhûdh) et absence "
        "de défaut caché ('adam al-'illah). C'est le degré le plus élevé d'acceptation "
        "individuelle d'un hadith."
    ),
    "صحيح لذاته": (
        "Hadith authentique par lui-même (Sahîh li-dhâtihi). Il remplit les cinq "
        "conditions du Sahîh de manière intrinsèque, sans avoir besoin d'être renforcé "
        "par d'autres voies de transmission. Terme technique distinguant l'authenticité "
        "propre du hadith de celle acquise par accumulation."
    ),
    "صحيح لغيره": (
        "Hadith authentique par accumulation (Sahîh li-ghayrihi). À l'origine un hadith "
        "Hasan li-dhâtihi dont l'existence de multiples voies de transmission indépendantes "
        "(turuq) élève le degré au rang du Sahîh. La multiplicité des chaînes compense les "
        "légères insuffisances individuelles de chaque voie."
    ),
    "حسن": (
        "Hadith dont la chaîne est continue, transmis par des narrateurs intègres mais dont "
        "la précision mémorielle n'atteint pas le degré exigé pour le Sahîh, sans anomalie "
        "ni défaut caché. C'est le deuxième degré d'acceptation. At-Tirmidhî est le premier "
        "muhaddith à avoir systématisé l'usage de ce terme."
    ),
    "حسن لذاته": (
        "Hadith bon par lui-même (Hasan li-dhâtihi). Il remplit les conditions du Hasan "
        "de manière intrinsèque. Le narrateur est légèrement en deçà du critère de précision "
        "parfaite (tâmm ad-dabt) mais reste acceptable. Son hadith sert de preuve juridique."
    ),
    "حسن لغيره": (
        "Hadith bon par accumulation (Hasan li-ghayrihi). À l'origine un hadith Da'îf dont "
        "la faiblesse est légère (pas de mensonge ni d'accusation grave) et qui est renforcé "
        "par l'existence d'autres voies de transmission. Il est utilisable comme preuve "
        "juridique, contrairement au Da'îf simple."
    ),
    "حسن صحيح": (
        "Formulation spécifique d'At-Tirmidhî (m. 279H). Les savants divergent sur sa "
        "signification exacte : soit le hadith possède deux chaînes (l'une Hasan, l'autre "
        "Sahîh), soit les muhaddithîn hésitent entre les deux degrés. Dans les deux cas, "
        "il est accepté comme preuve."
    ),
    "إسناده ثابت": (
        "Sa chaîne de transmission est solidement établie (Isnâduhu Thâbit). Le muhaddith "
        "certifie la solidité de chaque maillon de la chaîne sans émettre de réserve. "
        "Terme équivalent à Sahîh al-Isnâd, utilisé notamment par les Hanbalites."
    ),
    "إسناده صحيح": (
        "Sa chaîne est authentique (Isnâduhu Sahîh). Le muhaddith certifie l'authenticité "
        "de la chaîne de transmission uniquement, sans se prononcer explicitement sur le "
        "contenu (matn) du hadith. En pratique, la plupart des savants considèrent que "
        "l'authentification de la chaîne implique celle du texte sauf preuve contraire."
    ),
    "صحيح الإسناد": (
        "Chaîne authentique (Sahîh al-Isnâd). Formulation syntaxiquement inverse de "
        "'Isnâduhu Sahîh' mais de sens identique. Le muhaddith atteste que chaque narrateur "
        "de la chaîne remplit les critères de fiabilité et de précision."
    ),
    "إسناده حسن": (
        "Sa chaîne est bonne (Isnâduhu Hasan). Le muhaddith juge la chaîne de transmission "
        "au degré du Hasan, ce qui implique que les narrateurs sont intègres mais leur "
        "précision mémorielle est légèrement inférieure au degré du Sahîh."
    ),
    "حسن الإسناد": (
        "Chaîne bonne (Hasan al-Isnâd). Formulation inverse de 'Isnâduhu Hasan'. "
        "Le muhaddith certifie la bonté de la chaîne sans se prononcer sur le matn. "
        "Utilisé notamment par An-Nawawî et Ibn Hajar."
    ),
    "رجاله ثقات": (
        "Ses narrateurs sont des gens de confiance (Rijâluhu Thiqât). Chaque rapporteur "
        "de la chaîne a été classifié comme thiqah (fiable, réunissant intégrité et "
        "précision) par les imams de la critique des narrateurs (Jarh wa at-Ta'dîl). "
        "Ce jugement n'implique pas nécessairement la continuité de la chaîne."
    ),
    "رجاله رجال الصحيح": (
        "Ses narrateurs sont ceux du Sahîh (Rijâluhu Rijâl as-Sahîh). Tous les "
        "rapporteurs de la chaîne figurent parmi les narrateurs utilisés par Al-Bukhârî "
        "ou Muslim dans leur Sahîh. Jugement de fiabilité par association aux critères "
        "les plus stricts de la science du hadith."
    ),
    "حديث مقبول": (
        "Hadith accepté (Hadîth Maqbûl). Terme générique des usûliyyîn désignant tout "
        "hadith remplissant les conditions d'acceptation (Sahîh ou Hasan). Il sert de "
        "preuve juridique (hujjah) et peut fonder un ruling pratique."
    ),
    "حديث محتج به": (
        "Hadith constituant une preuve (Hadîth Muhtajj bihi). Hadith pouvant être invoqué "
        "comme argument en jurisprudence (fiqh) ou en croyance ('aqîdah). "
        "Seuls les hadiths Sahîh et Hasan atteignent ce degré."
    ),
    "حديث معمول به": (
        "Hadith mis en pratique (Hadîth Ma'mûl bihi). Les fuqahâ' (juristes) ont fondé "
        "des rulings pratiques sur ce hadith. Indique une acceptation effective dans la "
        "tradition juridique islamique."
    ),
    "حديث صحيح الإسناد": (
        "Hadith dont la chaîne est authentique. Formulation explicite jugeant la chaîne "
        "de transmission au degré du Sahîh."
    ),
    "حديث حسن الإسناد": (
        "Hadith dont la chaîne est bonne. Formulation explicite jugeant la chaîne "
        "de transmission au degré du Hasan."
    ),
    "حديث جيد الإسناد": (
        "Hadith dont la chaîne est solide (Jayyid al-Isnâd). Terme d'approbation "
        "utilisé par Ad-Dâraqutnî, Ibn Hajar et d'autres. Équivalent d'un Hasan fort "
        "tendant vers le Sahîh."
    ),
    "حديث قوي": (
        "Hadith solide (Hadîth Qawî). Sa chaîne est jugée forte et résistante aux "
        "critiques. Terme générique d'approbation entre le Hasan et le Sahîh."
    ),
    "حديث ثابت": (
        "Hadith fermement établi (Hadîth Thâbit). L'authenticité est prouvée de manière "
        "incontestable."
    ),
    "حديث محفوظ": (
        "Hadith préservé (Hadîth Mahfûz). L'opposé du Shâdhdh : lorsque plusieurs "
        "versions contradictoires existent, le Mahfûz est la version du narrateur le "
        "plus fiable ou le plus nombreux."
    ),
    "حديث معروف": (
        "Hadith connu (Hadîth Ma'rûf). L'opposé du Munkar. La version du narrateur "
        "fiable face à la contradiction d'un narrateur faible."
    ),
    "حديث مسند": (
        "Hadith dont la chaîne remonte au Prophète ﷺ (Musnad). La transmission "
        "est reliée en continu du compilateur jusqu'au Prophète ﷺ."
    ),
    "حديث متصل": (
        "Hadith à chaîne continue (Muttasil). Chaque maillon est relié au suivant "
        "sans rupture. S'il remonte au Prophète ﷺ, il est marfû' ; s'il s'arrête "
        "au Compagnon, il est mawqûf."
    ),
    "حديث موصول": (
        "Hadith relié (Mawsûl). Synonyme exact de Muttasil. Chaîne continue "
        "et ininterrompue."
    ),
    "حديث عال": (
        "Hadith à chaîne élevée ('Âlî). Nombre réduit de maillons entre le compilateur "
        "et le Prophète ﷺ. Signe d'excellence réduisant les risques d'erreur."
    ),
    "حديث عزيز": (
        "Hadith rare mais confirmé ('Azîz). Au minimum deux narrateurs indépendants "
        "à chaque niveau de la chaîne. Les deux voies se confirment mutuellement."
    ),
    "حديث مشهور": (
        "Hadith célèbre (Mashhûr). Trois narrateurs ou plus à chaque génération, "
        "sans atteindre le degré du Mutawâtir."
    ),
    "حديث مستفيض": (
        "Hadith largement diffusé (Mustafîd). Synonyme de Mashhûr selon la majorité."
    ),
    "حديث متواتر": (
        "Hadith transmis par multitudes (Mutawâtir). Rapporté à chaque génération par "
        "un nombre si élevé de narrateurs qu'il est rationnellement impossible qu'ils se "
        "soient concertés pour mentir. Confère une connaissance certaine (yaqîn). "
        "Deux types : lafzî (textuel) et ma'nawî (thématique)."
    ),
    "متفق عليه": (
        "Unanimement reconnu (Muttafaq 'alayhi). Rapporté à la fois par Al-Bukhârî "
        "et Muslim dans leur Sahîh. Plus haut degré d'authenticité consensuel."
    ),
    "على شرط الشيخين": (
        "Selon les critères des Deux Cheikhs. Le hadith n'a pas été rapporté par "
        "Bukhârî ni Muslim mais chaque narrateur figure dans les deux Sahîh."
    ),
    "على شرط البخاري": (
        "Selon les critères d'Al-Bukhârî. Les narrateurs remplissent les conditions "
        "de sélection d'Al-Bukhârî, les plus strictes de la tradition du hadith."
    ),
    "على شرط مسلم": (
        "Selon les critères de Muslim. Les narrateurs remplissent les conditions "
        "de Muslim ibn al-Hajjâj."
    ),
    "مقبول": (
        "Acceptable (Maqbûl). Terme d'Ibn Hajar dans Taqrîb at-Tahdhîb : narrateur "
        "accepté à condition d'être corroboré (mutâba'ah). Sinon, son hadith est Layyin."
    ),

    # ══════════════════════════════════════════════════════════════════════
    #  ② CATÉGORIE FAIBLESSE — Da'îf et dérivés (grades orange/ambre)
    # ══════════════════════════════════════════════════════════════════════

    "ضعيف": (
        "Hadith n'ayant pas atteint le degré du Hasan en raison de la perte d'une ou "
        "plusieurs des cinq conditions d'acceptation. Il n'est pas une preuve juridique "
        "mais peut être cité à titre complémentaire selon certains savants, sous "
        "conditions strictes."
    ),
    "ضعيف جداً": (
        "Très faible (Da'îf Jiddan). La faiblesse est sévère et cumulative. Ce hadith "
        "ne peut servir de preuve en aucun contexte."
    ),
    "ضعيف جدا": (
        "Variante orthographique de Da'îf Jiddan (sans tanwîn). Même définition."
    ),
    "ضعيف بهذا الإسناد": (
        "Faible par cette chaîne spécifique. La faiblesse est localisée dans la voie "
        "de transmission citée. Le hadith peut exister par d'autres voies plus solides."
    ),
    "ضعيف الإسناد": (
        "Chaîne faible (Da'îf al-Isnâd). Le muhaddith juge uniquement la chaîne "
        "comme faible, sans se prononcer sur le texte."
    ),
    "إسناده ضعيف": (
        "Sa chaîne est faible (Isnâduhu Da'îf). Formulation équivalente à Da'îf al-Isnâd."
    ),
    "حديث مردود": (
        "Hadith repoussé (Mardûd). Terme générique des usûliyyîn pour tout hadith "
        "n'ayant pas rempli les conditions d'acceptation."
    ),
    "حديث غير مقبول": (
        "Hadith non accepté. Formulation explicite de rejet sans précision du degré."
    ),
    "لا يحتج به": (
        "On ne peut s'en servir de preuve (Lâ Yuhtajj bihi). Le hadith ne peut fonder "
        "un argument juridique ni doctrinal."
    ),
    "لا يصح": (
        "Non authentifié (Lâ Yasihh). Verdict catégorique d'invalidité, plus sévère "
        "que Da'îf simple."
    ),
    "لا يثبت": (
        "Non établi (Lâ Yathbut). Le hadith n'est pas prouvé selon les critères reconnus. "
        "Formule fréquente chez Ahmad ibn Hanbal et Ad-Dâraqutnî."
    ),
    "واه": (
        "Très fragile (Wâhin). Degré de faiblesse supérieur au Da'îf ordinaire. "
        "Le narrateur principal est massivement critiqué."
    ),
    "واه جداً": (
        "Extrêmement fragile (Wâhin Jiddan). Degré le plus bas avant le rejet total."
    ),
    "واه بهذا الإسناد": (
        "Fragile par cette chaîne (Wâhin bi-hâdhâ al-Isnâd). Faiblesse extrême "
        "localisée dans la voie citée."
    ),
    "واهي الحديث": (
        "Fragile dans sa narration (Wâhî al-Hadîth). Narrateur dont les transmissions "
        "manquent systématiquement de solidité."
    ),
    "ليس بثابت": (
        "Non établi (Laysa bi-Thâbit). Le hadith n'a pas pu être prouvé de manière "
        "satisfaisante."
    ),
    "ليس بصحيح": (
        "Non authentique (Laysa bi-Sahîh). Verdict explicite niant l'authenticité."
    ),
    "ليس بمحفوظ": (
        "Non préservé (Laysa bi-Mahfûz). La version rapportée n'est pas reconnue "
        "comme correcte face aux variantes contradictoires."
    ),
    "ليس بمعروف": (
        "Non connu (Laysa bi-Ma'rûf). Hadith non reconnu par les muhaddithîn."
    ),
    "ليس بالقوي": (
        "Pas solide (Laysa bi-l-Qawî). La force probante est insuffisante."
    ),
    "ليس بذاك القوي": (
        "Pas très solide (Laysa bi-dhâk al-Qawî). Formule d'adoucissement de "
        "Yahyâ ibn Ma'în indiquant une faiblesse légère."
    ),
    "ليس بذلك": (
        "Pas à ce niveau (Laysa bi-dhâlik). L'insuffisance du narrateur est notée "
        "sans rejet total."
    ),
    "لين": (
        "Légèrement faible (Layyin). Critique modérée : intégrité acceptable mais "
        "précision mémorielle légèrement insuffisante."
    ),
    "لين الحديث": (
        "Légèrement faible dans sa narration (Layyin al-Hadîth). Erreurs occasionnelles ; "
        "hadith retenu uniquement à titre complémentaire."
    ),
    "فيه ضعف": (
        "Comporte une faiblesse (Fîhi Da'f). Faiblesse identifiée mais non rédhibitoire."
    ),
    "في إسناده ضعف": (
        "Sa chaîne comporte une faiblesse (Fî Isnâdihi Da'f). Faiblesse localisée "
        "dans la chaîne."
    ),
    "في إسناده مقال": (
        "Sa chaîne est sujette à discussion (Fî Isnâdihi Maqâl). Divergence des savants "
        "sur l'acceptabilité d'un ou plusieurs narrateurs."
    ),
    "في إسناده نظر": (
        "Sa chaîne nécessite examen (Fî Isnâdihi Nazar). Doute sérieux — chez "
        "Al-Bukhârî et Ad-Dhahabî, souvent un euphémisme pour une critique sévère."
    ),
    "فيه مقال": (
        "Sujet à discussion (Fîhi Maqâl). Présence de réserves sans verdict catégorique."
    ),
    "لا يصح في الباب شيء": (
        "Rien d'authentique dans ce chapitre (Lâ Yasihh fî al-Bâb Shay'). Verdict "
        "global : aucun hadith sur ce sujet n'atteint le degré d'authenticité."
    ),

    # ══════════════════════════════════════════════════════════════════════
    #  ③ CRITIQUE DES NARRATEURS — Jarh wa at-Ta'dîl
    # ══════════════════════════════════════════════════════════════════════

    # ── Ta'dîl (approbation) ─────────────────────────────────────────────
    "ثقة": (
        "Fiable (Thiqah). Le narrateur réunit intégrité morale ('adâlah) et précision "
        "mémorielle (dabt). Degré le plus élevé de fiabilité individuelle. Son hadith "
        "est accepté sans réserve."
    ),
    "ثقة ثبت": (
        "Fiable et fermement établi (Thiqah Thabt). Rang supérieur au simple Thiqah : "
        "mémoire particulièrement rigoureuse et constante."
    ),
    "ثقة حافظ": (
        "Fiable et mémorisant (Thiqah Hâfiz). Fiable avec une capacité de mémorisation "
        "exceptionnelle caractérisant les plus grands muhaddithîn."
    ),
    "حجة": (
        "Preuve à lui seul (Hujjah). Sa parole constitue en elle-même une preuve "
        "suffisante sans besoin de corroboration."
    ),
    "إمام": (
        "Chef de file (Imâm). Référence dans la science du hadith. Ce titre dépasse "
        "le cadre du Ta'dîl et reconnaît une autorité globale dans la discipline."
    ),
    "صدوق": (
        "Véridique (Sadûq). Honnête et intègre mais précision mémorielle légèrement "
        "inférieure à celle du Thiqah. Son hadith est Hasan par défaut."
    ),
    "صدوق يهم": (
        "Véridique mais sujet à l'erreur (Sadûq Yahim). Honnête mais commet des "
        "erreurs de mémoire ponctuelles. Hadith nécessitant vérification."
    ),
    "صدوق يخطئ": (
        "Véridique mais fait des erreurs (Sadûq Yukhti'). Variante de Sadûq Yahim. "
        "Erreurs suffisamment fréquentes pour affecter la classification."
    ),
    "لا بأس به": (
        "Pas de mal en lui (Lâ Ba's bihi). Chez Ibn Ma'în, équivaut à Thiqah. "
        "Chez d'autres, rang légèrement inférieur proche du Sadûq."
    ),
    "محله الصدق": (
        "Sa place est celle de la véracité (Mahalluhu as-Sidq). Narrateur reconnu "
        "honnête. Fiabilité suffisante sans atteindre le rang du Thiqah."
    ),
    "يكتب حديثه": (
        "On transcrit son hadith (Yuktab Hadîthuhu). Pas assez fiable comme preuve "
        "autonome mais mérite d'être consigné pour comparaison (I'tibâr)."
    ),
    "يعتبر به": (
        "On peut s'en servir pour vérification (Yu'tabar bihi). Son hadith sert dans "
        "la confrontation des voies mais n'est pas une preuve autonome."
    ),
    "شيخ": (
        "Cheikh (Shaykh). Terme de Ta'dîl modéré. Narrateur acceptable mais non éminent."
    ),
    "سكت عنه": (
        "On s'est tu à son sujet (Sakata 'anhu). Chez Abû Dâwûd, équivaut à un "
        "Hasan implicite. Chez d'autres, signe de Jahâlah."
    ),

    # ── Jarh (critique) ──────────────────────────────────────────────────
    "كذاب": (
        "Menteur (Kadhdhâb). Accusation la plus grave : le narrateur a été pris en "
        "flagrant délit de mensonge dans le hadith. Son hadith est Mawdû'."
    ),
    "وضاع": (
        "Fabricateur (Waddâ'). Inventeur délibéré de hadiths. Degré extrême du Jarh. "
        "Transmission interdite sauf mise en garde."
    ),
    "متروك": (
        "Abandonné (Matrûk). Unanimement délaissé pour mensonge avéré ou suspecté, "
        "corruption morale, ou gravité des erreurs. Hadith inutilisable."
    ),
    "متهم": (
        "Accusé (Muttaham). Accusé de mensonge ou de fabrication sans preuve formelle "
        "définitive. L'accusation suffit pour le rejet."
    ),
    "متهم بالكذب": (
        "Accusé de mensonge (Muttaham bi-l-Kadhib). Soupçon convergent de mensonge "
        "sans preuve formelle."
    ),
    "مجهول": (
        "Inconnu (Majhûl). Identité ou fiabilité non attestée. Deux types : "
        "Majhûl al-'Ayn (personne non identifiée) et Majhûl al-Hâl (identifié "
        "mais qualités non attestées)."
    ),
    "مجهول الحال": (
        "Inconnu quant à ses qualités (Majhûl al-Hâl). Identifié mais aucun "
        "imam ne s'est prononcé sur sa fiabilité. Synonyme : Mastûr."
    ),
    "مجهول العين": (
        "Inconnu quant à sa personne (Majhûl al-'Ayn). Connu par un seul rapport. "
        "Son identité même n'est pas établie de manière satisfaisante."
    ),
    "مستور": (
        "Voilé (Mastûr). Synonyme de Majhûl al-Hâl. Identifié mais qualités "
        "de fiabilité et d'intégrité non attestées."
    ),
    "مبهم": (
        "Ambigu (Mubham). Narrateur mentionné sans nom dans la chaîne. Hadith "
        "rejeté tant que l'identité n'est pas élucidée."
    ),
    "ليس بثقة": (
        "Non fiable (Laysa bi-Thiqah). Déclaration explicite de non-fiabilité "
        "par les imams de la critique."
    ),
    "غير ثقة": (
        "Non fiable (Ghayr Thiqah). Le narrateur ne réunit pas les conditions "
        "de fiabilité."
    ),
    "ليس بحجة": (
        "Pas une preuve (Laysa bi-Hujjah). Le narrateur ne peut constituer seul "
        "une preuve. Corroboration externe impérative."
    ),
    "ذاهب الحديث": (
        "Son hadith est perdu (Dhâhib al-Hadîth). Rejet sévère — narrations "
        "sans aucune valeur probante."
    ),
    "هالك": (
        "Ruiné (Hâlik). Narrateur totalement discrédité. Corruption irréversible "
        "de sa fiabilité."
    ),
    "متروك الحديث": (
        "Hadith abandonné (Matrûk al-Hadîth). Les muhaddithîn ont unanimement "
        "délaissé ses narrations."
    ),
    "تركوه": (
        "Ils l'ont abandonné (Tarakûhu). Consensus des savants sur le rejet "
        "du narrateur."
    ),
    "تكلم فيه": (
        "On a parlé contre lui (Tukullima fîhi). Réserves des critiques, couvrant "
        "différents degrés de Jarh selon le contexte."
    ),
    "يروي المناكير": (
        "Il rapporte des choses réprouvées (Yarwî al-Manâkîr). Connu pour "
        "transmettre des hadiths contredisant les gens de confiance."
    ),
    "يروي الموضوعات": (
        "Il rapporte des hadiths forgés (Yarwî al-Mawdû'ât). Transmet des "
        "hadiths fabriqués, par sa fabrication ou par négligence coupable."
    ),
    "منكر الحديث": (
        "Réprouvé dans sa narration (Munkar al-Hadîth). Hadiths massivement "
        "contredits par les gens de confiance. Chez Al-Bukhârî, signifie souvent "
        "'il est interdit de rapporter de lui'."
    ),
    "مضطرب الحديث": (
        "Perturbé dans sa narration (Mudtarib al-Hadîth). Rapporte le même hadith "
        "de manières contradictoires sans version déterminable."
    ),
    "فيه متروك": (
        "Contient un narrateur abandonné (Fîhi Matrûk). Narrateur unanimement "
        "rejeté présent dans la chaîne."
    ),
    "فيه كذاب": (
        "Contient un menteur (Fîhi Kadhdhâb). Un menteur avéré dans la chaîne "
        "rend le hadith Mawdû'."
    ),
    "فيه وضاع": (
        "Contient un fabricateur (Fîhi Waddâ'). Un fabricateur dans la chaîne "
        "rend le hadith intégralement Mawdû'."
    ),
    "فيه متهم": (
        "Contient un narrateur accusé (Fîhi Muttaham). Narrateur accusé de "
        "mensonge ou de fabrication présent dans la chaîne."
    ),
    "فيه مجهول": (
        "Contient un narrateur inconnu (Fîhi Majhûl). Rupture de vérification "
        "dans la chaîne."
    ),
    "فيه من لم يسم": (
        "Contient un narrateur non nommé. L'anonymat empêche toute évaluation."
    ),
    "فيه راو مبهم": (
        "Contient un narrateur ambigu. Identité trop floue pour évaluation."
    ),
    "فيه من لا يعرف": (
        "Contient un narrateur non identifié. Personne ne reconnaît ce rapporteur."
    ),
    "فيه جهالة": (
        "Comporte un anonymat (Fîhi Jahâlah). Un ou plusieurs narrateurs inconnus "
        "dans la chaîne."
    ),

    # ══════════════════════════════════════════════════════════════════════
    #  ④ DÉFAUTS TECHNIQUES — Ruptures, altérations, dissimulations
    # ══════════════════════════════════════════════════════════════════════

    "مرسل": (
        "Interrompu côté Successeur (Mursal). Un Tâbi'î cite directement le "
        "Prophète ﷺ sans nommer le Compagnon intermédiaire. Rejeté par la majorité."
    ),
    "منقطع": (
        "Coupé (Munqati'). La chaîne comporte une coupure en un ou plusieurs endroits "
        "(un narrateur manquant entre deux maillons)."
    ),
    "معضل": (
        "Doublement interrompu (Mu'dal). Deux maillons consécutifs manquants ou plus. "
        "Plus grave que le Munqati'."
    ),
    "معلق": (
        "Suspendu (Mu'allaq). Narrateurs du début de la chaîne (côté compilateur) omis."
    ),
    "مدلس": (
        "Dissimulé (Mudallis). Le narrateur cache un défaut dans la chaîne ou suggère "
        "une transmission directe fictive. Ibn Hajar a classé les mudallisîn en "
        "cinq niveaux."
    ),
    "فيه انقطاع": (
        "Comporte une coupure (Fîhi Inqitâ'). Rupture de transmission identifiée "
        "dans la chaîne."
    ),
    "ليس بمتصل": (
        "Chaîne non continue (Laysa bi-Muttasil). La continuité n'est pas établie."
    ),
    "شاذ": (
        "Anomal (Shâdhdh). Rapporté par un narrateur fiable mais contredisant "
        "des narrateurs plus fiables ou plus nombreux. Version correcte : le Mahfûz."
    ),
    "منكر": (
        "Répréhensible (Munkar). Hadith rapporté par un narrateur faible contredisant "
        "les gens de confiance (thiqât). L'opposé du Ma'rûf."
    ),
    "منكر جداً": (
        "Très répréhensible (Munkar Jiddan). Contradiction flagrante d'un narrateur "
        "très faible avec le consensus des gens de confiance."
    ),
    "معلل": (
        "Défectueux (Mu'allal). Défaut caché ('illah) décelable uniquement par les "
        "experts. Le hadith semble authentique en apparence."
    ),
    "معلول": (
        "Défectueux caché (Ma'lûl). Synonyme de Mu'allal. Les grammairiens préfèrent "
        "'Mu'allal' mais 'Ma'lûl' est devenu courant."
    ),
    "معل": (
        "Défectueux (Mu'all). Forme abrégée de Ma'lûl/Mu'allal."
    ),
    "فيه علة": (
        "Comporte un défaut caché (Fîhi 'Illah). Défaut subtil invalidant la chaîne "
        "ou le texte, invisible à l'examen superficiel."
    ),
    "مضطرب": (
        "Perturbé (Mudtarib). Rapporté de manières contradictoires sans possibilité "
        "de départager les versions."
    ),
    "مقلوب": (
        "Inversé (Maqlûb). Un nom de narrateur ou une portion du texte a été "
        "intervertie. Deux types : Maqlûb as-Sanad et Maqlûb al-Matn."
    ),
    "مدرج": (
        "Interpolé (Mudraj). Le texte a été mélangé avec des paroles d'un narrateur "
        "sans distinction. L'Idrâj peut être au début, milieu ou fin."
    ),
    "مصحف": (
        "Altéré par erreur d'écriture (Musahhaf). Erreur de transcription altérant "
        "les points diacritiques (ex: بشر → نشر)."
    ),
    "محرف": (
        "Altéré par déformation (Muharraf). Erreur altérant les voyelles (harakat) "
        "sans changer les points diacritiques."
    ),
    "ساقط": (
        "Caduc (Sâqit). La chaîne est si défaillante que le hadith n'a aucune "
        "valeur probante."
    ),

    # ══════════════════════════════════════════════════════════════════════
    #  ⑤ CATÉGORIES SPÉCIALES & FORGERIES
    # ══════════════════════════════════════════════════════════════════════

    "موقوف": (
        "Arrêté au Compagnon (Mawqûf). Paroles, actes ou approbations d'un Compagnon "
        "(Sahâbî), non attribués au Prophète ﷺ."
    ),
    "مقطوع": (
        "Arrêté au Successeur (Maqtû'). Paroles ou actes d'un Tâbi'î. Ne pas "
        "confondre avec Munqati' (chaîne coupée)."
    ),
    "موضوع": (
        "Forgé (Mawdû'). Hadith fabriqué et faussement attribué au Prophète ﷺ. "
        "Transmission interdite sauf mise en garde. Identifié par aveu du "
        "fabricateur, preuves internes, ou présence d'un menteur dans la chaîne."
    ),
    "باطل": (
        "Nul et non avenu (Bâtil). Manifestement faux dans son contenu ou sa chaîne. "
        "Aucune base dans la Sunnah authentique."
    ),
    "لا أصل له": (
        "Sans fondement (Lâ Asl Lahu). Aucune chaîne de transmission valide ne "
        "rattache ce texte au Prophète ﷺ."
    ),
    "مكذوب": (
        "Mensonge attribué (Makdhûb). Mensongèrement attribué au Prophète ﷺ. "
        "Insiste sur l'acte délibéré du mensonge."
    ),
    "مختلق": (
        "Inventé de toutes pièces (Mukhtalaq). Fabriqué sans aucun fondement."
    ),
    "مصنوع": (
        "Fabriqué (Masnû'). Synonyme de Mawdû'. Hadith manufacturé et faussement "
        "attribué à la Sunnah prophétique."
    ),
}


def _glossary_lookup(ar_key: str) -> str:
    """
    Cherche la définition académique d'un terme dans HUKM_GLOSSARY.
    Essaie correspondance exacte, puis correspondance normalisée.
    Retourne chaîne vide si rien n'est trouvé.
    """
    if ar_key in HUKM_GLOSSARY:
        return HUKM_GLOSSARY[ar_key]

    norm = _normalize_ar(ar_key)
    for key, defn in HUKM_GLOSSARY.items():
        if _normalize_ar(key) == norm:
            return defn
    return ""


# ─────────────────────────────────────────────────────────────────────────────
#  █  SYSTÈME DE VETO — « DÉTONATEURS » QUI ANNULENT LE SAHÎH
#
#  Si l'une de ces séquences apparaît dans le hukm brut, le verdict Sahîh
#  est annulé et rétrogradé en « ambigu / gris ». Cela couvre les cas où
#  un muhaddith mentionne « صحيح » dans un contexte restrictif (ex :
#  « معناه صحيح » = « son sens est authentique » mais pas sa chaîne).
#
#  Source : lexiques de Mahmûd at-Tahhân, An-Nukat d'Ibn Hajar,
#  audit croisé Grok + DeepSeek.
# ─────────────────────────────────────────────────────────────────────────────
_VETO_PATTERNS: list[str] = [
    "معناه صحيح",             # Son sens est authentique (pas le isnâd)
    "شاهد صحيح",              # Un témoin est authentique (pas ce hadith)
    "إلا أن",                 # Sauf que… (restriction annulant le verdict)
    "لكن",                    # Mais… (restriction)
    "السابق صحيح أما هذا",    # Le précédent est sahih mais pas celui-ci
    "يصح بها",                # Il est rendu authentique par elles (conditionnel)
    "غير أن",                 # Hormis que… (restriction)
    "رغم وجود",               # Malgré l'existence de… (réserve)
    "صححه بعض",               # Certains l'ont authentifié (divergence)
]

# Regex compilée : détecte la mention de ضعف (faiblesse) après un صحيح الإسناد
_VETO_SAHIH_WITH_DAIF_RE = re.compile(
    r"صحيح\s+الإسناد.*(?:ضعف|ضعيف|مع\s+ذكر\s+ضعف)"
)


def get_grade_from_hukm(hukm_raw: str) -> dict[str, Any]:
    """
    Fonction de classification exhautive — scanne le hukm brut dans l'ordre :
      ① VETO        → Si un détonateur est présent, verdict « ambigu » (gris)
      ② FAIBLESSE   → Si un terme de rejet/faiblesse est détecté, JAMAIS vert
      ③ ACCEPTATION → Si un terme d'acceptation est détecté → sahih/hasan

    RÈGLE ABSOLUE : Si un mot de Faiblesse ou de Veto est présent dans le
    hukm brut, le résultat ne peut JAMAIS être « sahih » (vert).

    Retourne le même format que _apply_hukm() pour compatibilité pipeline.
    """
    if not hukm_raw or not hukm_raw.strip():
        return {
            "ar": MISSING, "fr": MISSING,
            "level": "unknown", "color": "#6b7280",
            "definition": MISSING, "raw": "",
        }

    cleaned = hukm_raw.strip()
    norm_in = _normalize_ar(cleaned)

    # ── PHASE 1 : VETO — Détonateurs qui annulent Sahîh ──────────────
    for veto_pattern in _VETO_PATTERNS:
        if _normalize_ar(veto_pattern) in norm_in:
            log.info(
                f"[VETO] Détonateur détecté : «{veto_pattern}» dans «{cleaned}»"
            )
            return {
                "ar": cleaned,
                "fr": f"Verdict ambigu — contexte restrictif détecté ({veto_pattern})",
                "level": "ambiguous",
                "color": "#9ca3af",  # Gris
                "definition": (
                    "Le verdict brut contient un marqueur restrictif qui neutralise "
                    "toute mention de 'Sahîh'. Une analyse manuelle est requise."
                ),
                "raw": cleaned,
            }

    # ── Veto spécial : صحيح الإسناد suivi de mention de ضعف ──────────
    if _VETO_SAHIH_WITH_DAIF_RE.search(cleaned):
        log.info(
            f"[VETO] Sahîh al-Isnâd + mention de faiblesse : «{cleaned}»"
        )
        return {
            "ar": cleaned,
            "fr": "Verdict ambigu — chaîne authentique mais faiblesse mentionnée",
            "level": "ambiguous",
            "color": "#9ca3af",
            "definition": (
                "La chaîne est déclarée authentique mais une faiblesse est "
                "explicitement signalée dans le même verdict."
            ),
            "raw": cleaned,
        }

    # ── PHASE 2 : FAIBLESSE — Scanner d'abord les termes de rejet ────
    # Les clés du dictionnaire sont triées par longueur décroissante
    # pour matcher les expressions composées avant les termes simples.
    weakness_levels = {"daif", "rejected", "mawdu", "mawquf"}
    sorted_keys = sorted(_HUKM_AR_FR.keys(), key=len, reverse=True)

    for ar_key in sorted_keys:
        data = _HUKM_AR_FR[ar_key]
        if data["level"] not in weakness_levels:
            continue
        norm_key = _normalize_ar(ar_key)
        if norm_key in norm_in or ar_key in cleaned:
            log.info(
                f"[GRADE] Faiblesse détectée : «{ar_key}» ({data['level']}) "
                f"dans «{cleaned}»"
            )
            glossary_def = _glossary_lookup(ar_key)
            result = {**data, "ar": cleaned, "raw": cleaned}
            if glossary_def:
                result["definition"] = glossary_def
            return result

    # ── PHASE 3 : ACCEPTATION — Sahîh / Hasan ────────────────────────
    acceptance_levels = {"sahih", "hasan"}

    for ar_key in sorted_keys:
        data = _HUKM_AR_FR[ar_key]
        if data["level"] not in acceptance_levels:
            continue
        norm_key = _normalize_ar(ar_key)
        if norm_key in norm_in or ar_key in cleaned:
            log.info(
                f"[GRADE] Acceptation détectée : «{ar_key}» ({data['level']}) "
                f"dans «{cleaned}»"
            )
            glossary_def = _glossary_lookup(ar_key)
            result = {**data, "ar": cleaned, "raw": cleaned}
            if glossary_def:
                result["definition"] = glossary_def
            return result

    # ── FALLBACK : grade non répertorié ───────────────────────────────
    return {
        "ar": cleaned,
        "fr": f"Grade non répertorié : {cleaned}",
        "level": "unknown",
        "color": "#6b7280",
        "definition": MISSING,
        "raw": cleaned,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  TRANSLITTÉRATIONS CANONIQUES
# ─────────────────────────────────────────────────────────────────────────────
_TRANSLITT: dict[str, str] = {
    "أبو هريرة":        "Abû Hurayra (رضي الله عنه)",
    "عائشة":            "ʿÂ'isha bint Abî Bakr (رضي الله عنها)",
    "ابن عمر":          "Ibn ʿUmar (رضي الله عنهما)",
    "عبد الله بن عمر":  "ʿAbdallâh ibn ʿUmar (رضي الله عنهما)",
    "ابن عباس":         "Ibn ʿAbbâs (رضي الله عنهما)",
    "عبد الله بن عباس": "ʿAbdallâh ibn ʿAbbâs (رضي الله عنهما)",
    "أنس بن مالك":      "Anas ibn Mâlik (رضي الله عنه)",
    "أنس":              "Anas ibn Mâlik (رضي الله عنه)",
    "جابر":             "Jâbir ibn ʿAbdallâh (رضي الله عنهما)",
    "جابر بن عبد الله": "Jâbir ibn ʿAbdallâh (رضي الله عنهما)",
    "أبو سعيد الخدري":  "Abû Saʿîd al-Khudrî (رضي الله عنه)",
    "أبو موسى":         "Abû Mûsâ al-Ash'arî (رضي الله عنه)",
    "معاذ بن جبل":      "Muʿâdh ibn Jabal (رضي الله عنه)",
    "عمر بن الخطاب":    "ʿUmar ibn al-Khattâb (رضي الله عنه)",
    "علي بن أبي طالب":  "ʿAlî ibn Abî Tâlib (رضي الله عنه)",
    "عثمان بن عفان":    "ʿUthmân ibn ʿAffân (رضي الله عنه)",
    "أبو بكر الصديق":   "Abû Bakr as-Siddîq (رضي الله عنه)",
    "البخاري":          "Al-Bukhârî رحمه الله (m. 256H)",
    "مسلم":             "Muslim ibn al-Hajjâj رحمه الله (m. 261H)",
    "الترمذي":          "At-Tirmidhî رحمه الله (m. 279H)",
    "أبو داود":         "Abû Dâwûd رحمه الله (m. 275H)",
    "النسائي":          "An-Nasâ'î رحمه الله (m. 303H)",
    "ابن ماجه":         "Ibn Mâja رحمه الله (m. 273H)",
    "أحمد":             "Ahmad ibn Hanbal رحمه الله (m. 241H)",
    "الحاكم":           "Al-Hâkim رحمه الله (m. 405H)",
    "الطبراني":         "At-Tabarânî رحمه الله (m. 360H)",
    "البيهقي":          "Al-Bayhaqî رحمه الله (m. 458H)",
    "الدارقطني":        "Ad-Dâraqutnî رحمه الله (m. 385H)",
    "ابن حبان":         "Ibn Hibbân رحمه الله (m. 354H)",
    "ابن خزيمة":        "Ibn Khuzayma رحمه الله (m. 311H)",
    "الدارمي":          "Ad-Dârimî رحمه الله (m. 255H)",
    "الألباني":         "Cheikh Al-Albânî رحمه الله (m. 1420H)",
    "ابن باز":          "Cheikh Ibn Bâz رحمه الله (m. 1420H)",
    "ابن حجر":          "Ibn Hajar al-ʿAsqalânî رحمه الله (m. 852H)",
    "الذهبي":           "Adh-Dhahabî رحمه الله (m. 748H)",
    "النووي":           "An-Nawawî رحمه الله (m. 676H)",
    "ابن كثير":         "Ibn Kathîr رحمه الله (m. 774H)",
    "السيوطي":          "As-Suyûtî رحمه الله (m. 911H)",
    "ابن الجوزي":       "Ibn al-Jawzî رحمه الله (m. 597H)",
    "العراقي":          "Al-ʿIrâqî رحمه الله (m. 806H)",
    "ابن تيمية":        "Ibn Taymiyya رحمه الله (m. 728H)",
    "ابن القيم":        "Ibn al-Qayyim رحمه الله (m. 751H)",
    "الوادعي":          "Cheikh Al-Wâdi'î رحمه الله (m. 1422H)",
    "أبو يعلى":         "Abû Ya'lâ رحمه الله (m. 307H)",
    "البزار":           "Al-Bazzâr رحمه الله (m. 292H)",
}

# ─────────────────────────────────────────────────────────────────────────────
#  BASE DES SAHABAS CONNUS (pour rôle dans la silsila)
# ─────────────────────────────────────────────────────────────────────────────
_SAHABAS: set[str] = {
    "أبو هريرة", "عائشة", "ابن عمر", "عبد الله بن عمر",
    "ابن عباس", "عبد الله بن عباس", "أنس بن مالك", "أنس",
    "جابر", "جابر بن عبد الله", "أبو سعيد الخدري", "أبو سعيد",
    "أبو موسى الأشعري", "أبو موسى", "معاذ بن جبل", "معاذ",
    "عمر بن الخطاب", "عمر", "علي بن أبي طالب", "علي",
    "عثمان بن عفان", "عثمان", "أبو بكر الصديق", "أبو بكر",
    "عبد الله بن عمرو", "سهل بن سعد", "البراء بن عازب",
    "النعمان بن بشير", "واثلة بن الأسقع", "أبو أمامة",
    "معاوية بن أبي سفيان", "معاوية", "سلمان الفارسي",
    "أبو ذر الغفاري", "أبو ذر", "بلال بن رباح", "بلال",
    "عبد الله بن مسعود", "ابن مسعود", "أبو الدرداء",
    "ثوبان", "رافع بن خديج", "حذيفة بن اليمان", "حذيفة",
    "أبو أيوب الأنصاري", "زيد بن ثابت", "أبو قتادة",
    "المقداد بن الأسود", "عمرو بن العاص", "خالد بن الوليد",
    "عبادة بن الصامت", "أبو هريرة الدوسي",
}

# ─────────────────────────────────────────────────────────────────────────────
#  ① UTILITAIRES — Normalisation et nettoyage
# ─────────────────────────────────────────────────────────────────────────────

def _strip_tashkil(text: str) -> str:
    """Supprime les diacritiques arabes (U+0610–U+061A, U+064B–U+065F, U+0670)."""
    return re.sub(r"[\u0610-\u061a\u064b-\u065f\u0670]", "", text)


def _normalize_ar(text: str) -> str:
    """Normalisation canonique : NFC + alif unifié + tashkil + espaces."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = _strip_tashkil(text)
    text = re.sub(r"[أإآ]", "ا", text)
    text = re.sub(r"[ىي]", "ي", text)
    return re.sub(r"\s+", " ", text).strip()


def _clean_text(raw: str) -> str:
    """Supprime balises HTML et normalise les espaces."""
    if not raw:
        return ""
    raw = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", raw).strip()


def _clean_name(raw: str) -> str:
    """Nettoie un nom de narrateur extrait du DOM."""
    if not raw:
        return ""
    raw = _clean_text(raw)
    # Supprimer les formules de transmission en tête
    raw = re.sub(
        r"^(عن|حدثنا|حدّثنا|أخبرنا|أخبرني|أنبأنا|أنبأني|قال|روى|سمعت|ثنا|نا)\s+",
        "", raw.strip()
    )
    # Supprimer les caractères parasites
    raw = re.sub(r"[\[\](){}\\/|0-9،,;]", "", raw)
    return re.sub(r"\s+", " ", raw).strip()


# Regex compilée une seule fois — supprime titres honorifiques et formules
# post-nom parasites dans les entrées de silsila/isnad.
_ISNAD_TITLE_RE = re.compile(
    r"""
    # ── Titres honorifiques pré-nom ──────────────────────────────────────
    \b(
        الإمام|الامام|الشيخ|الشّيخ|الحافظ|الحافظ|العلامة|العلامه|
        المحدث|المحدّث|الحجة|الثقة|الثّقة|الفقيه|القاضي|الحاكم|
        الخطيب|السيد|الأستاذ|الدكتور|سيدنا|مولانا|شيخنا|حافظنا
    )\s+
    |
    # ── Formules post-nom (bénédictions / métadonnées) ──────────────────
    \s*[–\-—]\s*.*$               # tiret suivi de métadonnées
    |
    \s*[،,]\s*\d+\s*[هـه]?\s*$   # numéro de décès en fin
    |
    \s*\(.*?\)                    # parenthèses entières
    |
    \s*(رحمه الله|رحمه الله تعالى|رضي الله عنه|رضي الله عنها|
        صلى الله عليه وسلم|عليه السلام|حفظه الله|وفقه الله|
        نفعنا الله به|أمد الله في عمره|المتوفى|ت\.)
    """,
    re.VERBOSE | re.UNICODE,
)


def _clean_isnad_name(raw: str) -> str:
    """
    Nettoie un nom dans la silsila/isnad :
      1. Applique _clean_name (formules de transmission, caractères parasites)
      2. Supprime les titres honorifiques (الإمام, الشيخ, الحافظ…)
      3. Supprime les formules post-nom (رحمه الله, رضي الله عنه…)
      4. Supprime les métadonnées entre parenthèses et après tiret

    Conserve UNIQUEMENT le nom propre canonique du narrateur.
    """
    name = _clean_name(raw)
    if not name:
        return ""
    name = _ISNAD_TITLE_RE.sub("", name)
    return re.sub(r"\s+", " ", name).strip()


def _is_arabic(text: str) -> bool:
    """True si le texte est majoritairement arabe (> 30 %)."""
    if not text:
        return False
    ar = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
    return ar > len(text.strip()) * 0.3


def _extract_rijal_id(href: str) -> str | None:
    """Extrait l'ID Dorar d'un narrateur depuis son URL /rijal/ID."""
    if not href:
        return None
    m = re.search(r"/rijal/([^/?#\s]+)", href)
    return m.group(1) if m else None


def _transliterate(ar_name: str) -> str:
    """Translittère un nom arabe selon le dictionnaire canonique."""
    if not ar_name:
        return ""
    norm = _normalize_ar(ar_name)
    for ar_key, fr_val in _TRANSLITT.items():
        norm_key = _normalize_ar(ar_key)
        if norm_key == norm or norm_key in norm or norm in norm_key:
            return fr_val
    return ar_name


def _is_sahabi(name: str) -> bool:
    """Vérifie si un nom correspond à un Sahabi de la base connue."""
    if not name:
        return False
    norm = _normalize_ar(name)
    for s in _SAHABAS:
        norm_s = _normalize_ar(s)
        if norm_s == norm or norm_s in norm or norm in norm_s:
            return True
    return False


def _infer_century(name: str) -> str:
    """Infère le siècle hégirien depuis le nom du muhaddith."""
    _MAP: dict[str, str] = {
        "مالك": "2H", "الأوزاعي": "2H", "سفيان الثوري": "2H",
        "شعبة": "2H", "ابن المبارك": "2H",
        "البخاري": "3H", "مسلم": "3H", "أبو داود": "3H",
        "الترمذي": "3H", "النسائي": "3H", "ابن ماجه": "3H",
        "أحمد": "3H", "ابن حنبل": "3H", "الدارمي": "3H",
        "الطبراني": "4H", "ابن خزيمة": "4H", "الحاكم": "4H",
        "أبو يعلى": "4H", "البزار": "4H", "الدارقطني": "4H",
        "ابن حبان": "4H", "البيهقي": "5H", "الخطيب البغدادي": "5H",
        "ابن الجوزي": "6H", "النووي": "7H", "الذهبي": "8H",
        "ابن كثير": "8H", "العراقي": "8H", "ابن حجر": "9H",
        "السيوطي": "9H", "ابن تيمية": "8H", "ابن القيم": "8H",
        "الألباني": "14H", "ابن باز": "14H", "ابن عثيمين": "14H",
        "الوادعي": "14H", "مقبل": "14H",
    }
    norm = _normalize_ar(name)
    for key, century in _MAP.items():
        if _normalize_ar(key) in norm:
            return century
    return MISSING


_CENTURY_TO_YEAR: dict[str, int] = {
    "1H": 100, "2H": 200, "3H": 300, "4H": 400, "5H": 500,
    "6H": 600, "7H": 700, "8H": 800, "9H": 900,
    "10H": 1000, "11H": 1100, "12H": 1200, "13H": 1300, "14H": 1400,
}


def _century_to_death_year(century: str) -> int:
    """Convertit un siècle hégirien (ex: '3H') en entier approximatif (ex: 300)."""
    return _CENTURY_TO_YEAR.get(century, 9999)


# ─────────────────────────────────────────────────────────────────────────────
#  ② APPLICATION DU HUKM — DICTIONNAIRE VERROUILLÉ
# ─────────────────────────────────────────────────────────────────────────────

def _apply_hukm(hukm_raw: str) -> dict[str, Any]:
    """
    Applique le dictionnaire _HUKM_AR_FR au grade brut via get_grade_from_hukm().

    Ordre de scan (get_grade_from_hukm) :
      1. VETO        → détonateurs qui annulent Sahîh → gris/ambigu
      2. FAIBLESSE   → termes de rejet/faiblesse → JAMAIS vert
      3. ACCEPTATION → termes sahih/hasan → vert/lime

    JAMAIS de donnée manquante dans le résultat — MISSING si vide.
    """
    return get_grade_from_hukm(hukm_raw)


# ─────────────────────────────────────────────────────────────────────────────
#  ②.4b RANG DE GRADE — HIÉRARCHIE SAHIH > HASAN > DA'IF > REJETÉ
#
#  Utilisé par le dédoublonnement pour départager des doublons de même
#  score d'autorité ET pour toujours conserver le meilleur hukm_raw.
# ─────────────────────────────────────────────────────────────────────────────

_GRADE_RANK: dict[str, int] = {
    "sahih": 4,
    "hasan": 3,
    "daif": 2,
    "ambiguous": 1,
    "mawquf": 1,
    "mawdu": 1,
    "rejected": 1,
    "unknown": 0,
}


def _hukm_rank(hukm_raw: str) -> int:
    """Rang numérique du grade (Sahih=4 > Hasan=3 > Da'if=2 > Rejeté=1 > Inconnu=0)."""
    if not hukm_raw:
        return 0
    level = _apply_hukm(hukm_raw).get("level", "unknown")
    return _GRADE_RANK.get(level, 0)


# ─────────────────────────────────────────────────────────────────────────────
#  ②.5  HIÉRARCHIE D'AUTORITÉ DES SOURCES — ANTI-DÉGRADATION SAHÎHAYN
#
#  Mission : corriger l'erreur grave d'Amâna où des hadiths rapportés par
#  Bukhârî ou Muslim étaient tagués Da'îf à cause d'un doublon (même matn)
#  provenant d'un recueil secondaire mal gradé sur Dorar. Le moteur doit
#  TOUJOURS privilégier la source la plus haute dans la hiérarchie classique
#  des muhaddithîn.
# ─────────────────────────────────────────────────────────────────────────────

def _get_authority_score(mohaddith: str, source: str) -> int:
    """
    Calcule le score d'autorité d'une source de hadith selon la hiérarchie
    classique des muhaddithîn.

    BARÈME DE FER — Règle de non-dégradation :
      • 100 : Al-Bukhârî / Muslim (Sahîhayn)    → Verdict forcé « صحيح »
      •  90 : Muwatta' Mâlik                    → Conserve verdict Dorar
      •  80 : Sunan (Abû Dâwûd, Tirmidhî, Nasâ'î, Ibn Mâja) + Musnad Ahmad
      •  70 : Cheikh Al-Albânî                  — Autorité moderne
      •   0 : Source inconnue ou non listée

    Règle d'inspection : les champs `mohaddith` ET `source` sont tous deux
    scannés — Dorar distribue parfois le nom du compilateur dans l'un ou
    l'autre selon le bloc HTML rendu.

    Ordre des vérifications : du plus spécifique (titre de livre complet)
    au plus générique (nom seul), pour éviter les faux positifs.
    """
    blob = f"{mohaddith or ''} {source or ''}"
    norm = _normalize_ar(blob)

    # ── 100 — Sahîhayn ───────────────────────────────────────────────────
    # Titres complets d'abord, puis nom court ; "صحيح مسلم" avant "مسلم"
    # pour éviter toute collision avec d'autres noms portant la racine.
    for key in (
        "صحيح البخاري", "الجامع الصحيح", "بخاري",
        "صحيح مسلم", "مسلم",
    ):
        if _normalize_ar(key) in norm:
            return 100

    # ── 90 — Muwatta' Mâlik ──────────────────────────────────────────────
    # "موطأ" et "موطأ مالك" d'abord ; "مالك بن أنس" ensuite ; "مالك" en
    # dernier (plus générique mais acceptable dans le champ mohaddith).
    for key in ("موطا مالك", "موطا", "مالك بن انس", "مالك"):
        if _normalize_ar(key) in norm:
            return 90

    # ── 80 — Sunan + Musnad Ahmad ─────────────────────────────────────────
    # "مسند أحمد" et "ابن حنبل" avant "أحمد" seul pour plus de précision.
    for key in (
        "مسند احمد", "ابن حنبل",
        "ابو داود", "ترمذي", "نسائي", "ابن ماجه",
        "احمد",
    ):
        if _normalize_ar(key) in norm:
            return 80

    # ── 70 — Al-Albânî ───────────────────────────────────────────────────
    # _normalize_ar unifie alif + ya → toutes variantes orthographiques
    # (الألباني / الألبانى / الالباني) convergent vers "الالباني".
    if _normalize_ar("الالباني") in norm:
        return 70

    return 0


def _dedupe_hadiths_by_authority(
    hadiths: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Déduplication STRICTE par matn arabe (normalisé) — BARÈME DE FER.

    Pour un même texte arabe (ou quasi-identique), on ne conserve QUE le
    hadith ayant le plus haut score d'autorité via `_get_authority_score`.
    Cela empêche qu'un hadith de Bukhârî/Muslim soit éliminé ou dégradé à
    cause d'un doublon issu d'un recueil secondaire mal gradé sur Dorar.

    Règle de fusion des verdicts :
      • Quel que soit le "gagnant" (score max), les `all_verdicts` des deux
        doublons sont FUSIONNÉS pour ne perdre aucun avis savant.
      • Le `detail_url` du perdant est conservé comme fallback si le gagnant
        n'en possède pas.

    L'ordre d'apparition relatif est préservé pour les matns uniques.
    La quasi-identité est obtenue via `_normalize_ar` (NFC + tashkîl +
    alif/yâ unifiés) tronqué à 220 caractères : absorbe les micro-variations
    de ponctuation et de longueur.
    """
    best: dict[str, dict[str, Any]] = {}
    order: list[str] = []

    for h in hadiths:
        ar_text = h.get("ar_text", "") or ""
        key = _normalize_ar(ar_text)[:220]
        if not key:
            # Matn absent → on garde le hadith sous une clé unique
            key = f"__no_matn__{len(order)}"

        score = _get_authority_score(
            h.get("mohaddith", ""),
            h.get("source", ""),
        )

        grade_rank = _hukm_rank(h.get("hukm_raw", ""))

        if key not in best:
            best[key] = {**h, "_authority_score": score, "_grade_rank": grade_rank}
            order.append(key)
            continue

        existing       = best[key]
        existing_score = existing.get("_authority_score", 0)
        existing_grade = existing.get("_grade_rank", 0)

        # Fusion des verdicts : on cumule toujours les avis savants des deux
        # doublons pour ne jamais perdre une opinion doctrinale.
        merged_verdicts: list[dict[str, Any]] = list(
            existing.get("all_verdicts") or []
        ) + list(h.get("all_verdicts") or [])

        # ── Préserver le meilleur hukm_raw entre les deux doublons ──
        # Quelle que soit l'issue (gagnant/perdant), le grade le plus
        # élevé (Sahih > Hasan > Da'if) est toujours porté par le survivant.
        if grade_rank >= existing_grade:
            best_hukm_raw   = h.get("hukm_raw", "")
            best_grade_rank = grade_rank
        else:
            best_hukm_raw   = existing.get("hukm_raw", "")
            best_grade_rank = existing_grade

        # ── Gagnant : autorité d'abord, grade comme départage ──
        new_wins = (
            score > existing_score
            or (score == existing_score and grade_rank > existing_grade)
        )

        if new_wins:
            log.info(
                f"[DEDUP] Matn dupliqué — remplacement "
                f"(score {existing_score} → {score}, "
                f"grade {existing_grade} → {grade_rank}) — "
                f"source retenue : {h.get('source', '?')} / "
                f"source écartée : {existing.get('source', '?')}"
            )
            best[key] = {
                **h,
                "_authority_score": score,
                "_grade_rank":      best_grade_rank,
                "hukm_raw":         best_hukm_raw,
                "all_verdicts":     merged_verdicts,
                "detail_url": (
                    h.get("detail_url")
                    or existing.get("detail_url")
                    or ""
                ),
            }
        else:
            log.info(
                f"[DEDUP] Matn dupliqué — conservation "
                f"(score {existing_score} ≥ {score}, "
                f"grade {existing_grade} vs {grade_rank}) — "
                f"source écartée : {h.get('source', '?')}"
            )
            best[key] = {
                **existing,
                "_grade_rank":  best_grade_rank,
                "hukm_raw":     best_hukm_raw,
                "all_verdicts": merged_verdicts,
                "detail_url": (
                    existing.get("detail_url")
                    or h.get("detail_url")
                    or ""
                ),
            }

    return [best[k] for k in order]


def _sort_sahih_first(
    hadiths: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Tri des résultats : les hadiths avec grade « sahih » sont placés en tête
    de liste (index 0), suivis de hasan, puis daif, puis le reste.

    Le tri est STABLE : l'ordre relatif entre hadiths de même grade est préservé.
    """
    return sorted(
        hadiths,
        key=lambda h: _hukm_rank(h.get("hukm_raw", "")),
        reverse=True,
    )


def _apply_authority_override(
    hadith: dict[str, Any],
    hukm: dict[str, Any],
) -> dict[str, Any]:
    """
    RÈGLE DE FER (Amâna Médine) : si le score d'autorité d'une source atteint
    100 (Bukhârî ou Muslim), on force le verdict à « صحيح » / « Sahih »,
    PEU IMPORTE ce que la chaîne de traitement ou Dorar a pu remonter.

    Cette règle écrase tout verdict contradictoire hérité d'un doublon ou
    d'un parsing partiel. Elle ne s'applique PAS aux scores < 100 — le
    dictionnaire Hukm verrouillé conserve alors sa préséance.
    """
    score = _get_authority_score(
        hadith.get("mohaddith", ""),
        hadith.get("source", ""),
    )
    if score < 100:
        return hukm

    log.info(
        f"[AUTHORITY=100] Override Sahîh forcé — "
        f"source : {hadith.get('source', '?')} — "
        f"ancien hukm : {hukm.get('ar', '?')}"
    )

    sahih_ref = _HUKM_AR_FR.get("صحيح", {})
    return {
        **hukm,
        "ar":         "صحيح",
        "fr":         "Sahih",
        "level":      "sahih",
        "color":      sahih_ref.get("color", "#22c55e"),
        "definition": sahih_ref.get("definition", hukm.get("definition", MISSING)),
        "raw":        hukm.get("raw", "") or "صحيح",
    }


def _group_verdicts_by_mohaddith(
    verdicts: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """
    Groupe les verdicts par Mohaddith pour éviter les contradictions visuelles.
    Un même muhaddith ne peut avoir qu'un seul verdict affiché.
    """
    grouped: dict[str, dict[str, Any]] = {}
    for v in verdicts:
        mohaddith_ar = v.get("mohaddith", "")
        key = _transliterate(mohaddith_ar) or mohaddith_ar or MISSING
        if key not in grouped:
            grouped[key] = {
                "ar_name": mohaddith_ar or MISSING,
                "fr_name": key,
                "hukm_ar": v.get("ar", MISSING),
                "hukm_fr": v.get("fr", MISSING),
                "level":   v.get("level", "unknown"),
                "color":   v.get("color", "#6b7280"),
            }
    return grouped


def _extract_albani_from_verdicts(verdicts: list[dict[str, Any]]) -> str:
    """
    Parcourt all_verdicts et retourne UNIQUEMENT les verdicts attribués
    à Shaykh Nâsir ad-Dîn al-Albânî, s'ils existent dans la réponse Dorar.

    PROTOCOLE ZÉRO HALLUCINATION :
      • Lecture seule du champ all_verdicts déjà scrapé.
      • Aucune invention, aucun appel IA.
      • Si Al-Albânî n'est pas présent → chaîne vide.
        Le fallback frontend « CONSULTER AL-ALBANI » (Rule 8) prend le relais.
    """
    lines: list[str] = []

    for v in verdicts:
        moh_ar = (v.get("mohaddith") or "")
        # Variantes orthographiques arabes courantes du nom
        if any(
            k in moh_ar
            for k in ("الألباني", "الألبانى", "الالباني", "الألبانِي")
        ):
            ar = (v.get("ar") or "").strip()
            fr = (v.get("fr") or "").strip()
            chunk: list[str] = []
            if ar:
                chunk.append(f"**Verdict arabe** : {ar}")
            if fr:
                chunk.append(f"**Traduction** : {fr}")
            if chunk:
                lines.append(" — ".join(chunk))

    if not lines:
        return ""

    return (
        "**GRILLE AL-ALBĀNĪ — Analyse selon Shaykh Nâsir ad-Dîn al-Albânî**\n\n"
        + "\n\n".join(lines)
    )


# ─────────────────────────────────────────────────────────────────────────────
#  ③ PARSING HTML DORAR — XPATH ULTRA-PRÉCIS
# ─────────────────────────────────────────────────────────────────────────────

def _parse_dorar_html(raw_html: str) -> list[dict[str, Any]]:
    """
    Parse le HTML de l'API Dorar.net avec XPath précis.

    Structure HTML réelle de Dorar (auditée sur le DOM en production) :
    ──────────────────────────────────────────────────────────────────
    • Les hadiths sont séparés par ' --- ' dans le JSON
    • Chaque bloc :
        div.hadith            → Matn arabe (excluant div.hadith-info)
        span.info-subtitle    → Labels : الراوي / المحدث / المصدر / الصفحة / الحكم
        a[href*=/rijal/]      → Liens narrateurs (silsila)
        a[href*=/hadith/]     → Lien page de détail (scraping silsila complète)
    ──────────────────────────────────────────────────────────────────
    """
    results: list[dict[str, Any]] = []
    if not raw_html or not raw_html.strip():
        return results

    blocks = re.split(r"\s*---\s*", raw_html)
    log.info(f"Dorar HTML → {len(blocks)} blocs bruts")

    for i, block_str in enumerate(blocks):
        block_str = block_str.strip()
        if not block_str or len(block_str) < 25:
            continue

        try:
            tree = lxml_html.fromstring(
                f"<div class='mz-wrapper'>{block_str}</div>"
            )
        except Exception as exc:
            log.warning(f"Bloc {i} : lxml échoué — {exc}")
            continue

        h: dict[str, Any] = {
            "ar_text":       "",
            "rawi":          "",
            "rawi_id":       None,
            "rawi_url":      "",
            "mohaddith":     "",
            "mohaddith_id":  None,
            "mohaddith_url": "",
            "source":        "",
            "source_url":    "",
            "volume":        MISSING,
            "page":          MISSING,
            "hadith_number": MISSING,
            "hukm_raw":      "",
            "hukm":          {},
            "detail_url":    None,
            "rijal_links":   [],
            "all_verdicts":  [],
        }

        # ── MATN — texte arabe ──────────────────────────────────────────
        for el in tree.xpath('.//div[contains(@class,"hadith")]'):
            if "hadith-info" in el.get("class", ""):
                continue
            text = el.text_content().strip()
            if text and len(text) > 15 and _is_arabic(text[:80]):
                h["ar_text"] = text
                break

        # Fallback sur paragraphes / divs arabes
        if not h["ar_text"]:
            for el in tree.xpath('.//p | .//div'):
                txt = el.text_content().strip()
                if len(txt) > 30 and _is_arabic(txt[:60]):
                    h["ar_text"] = txt[:1200]
                    break

        # ── MÉTADONNÉES via span.info-subtitle ─────────────────────────
        for label_el in tree.xpath('.//span[@class="info-subtitle"]'):
            label = label_el.text_content().strip()
            parent = label_el.getparent()
            if parent is None:
                continue

            parent_text = _clean_text(
                parent.text_content().replace(label, "", 1)
            )
            rij_links = parent.xpath('.//a[contains(@href,"/rijal/")]')
            src_links  = parent.xpath('.//a')

            if "الراوي" in label:
                h["rawi"] = _clean_name(parent_text)
                if rij_links:
                    href = rij_links[0].get("href", "")
                    h["rawi_id"] = _extract_rijal_id(href)
                    h["rawi_url"] = DORAR_BASE + href if href.startswith("/") else href
                    h["rijal_links"].append({
                        "name":    _clean_name(rij_links[0].text_content()),
                        "id":      h["rawi_id"],
                        "url":     h["rawi_url"],
                        "role":    "sahabi" if _is_sahabi(h["rawi"]) else "rawi",
                        "fr_name": _transliterate(h["rawi"]),
                    })

            elif "المحدث" in label:
                h["mohaddith"] = _clean_name(parent_text)
                if rij_links:
                    href = rij_links[0].get("href", "")
                    h["mohaddith_id"] = _extract_rijal_id(href)
                    h["mohaddith_url"] = DORAR_BASE + href if href.startswith("/") else href
                    h["rijal_links"].append({
                        "name":    _clean_name(rij_links[0].text_content()),
                        "id":      h["mohaddith_id"],
                        "url":     h["mohaddith_url"],
                        "role":    "mohaddith",
                        "fr_name": _transliterate(h["mohaddith"]),
                    })

            elif "المصدر" in label:
                h["source"] = _clean_name(parent_text)
                if src_links:
                    href = src_links[0].get("href", "")
                    h["source_url"] = DORAR_BASE + href if href.startswith("/") else href

            elif "الصفحة" in label or "الرقم" in label:
                raw_page = parent_text.strip()
                # Extraction Volume / Page / Numéro depuis la chaîne brute
                # Patterns : "3/45" ou "ص45" ou "رقم : 1234" ou "ح 567"
                vol_page_m = re.search(r"(\d+)\s*/\s*(\d+)", raw_page)
                num_m      = re.search(r"(?:رقم|ح|حديث)\s*:?\s*(\d+)", raw_page)
                page_m     = re.search(r"(?:ص|صفحة)\s*:?\s*(\d+)", raw_page)

                if vol_page_m:
                    h["volume"] = f"Vol. {vol_page_m.group(1)}"
                    h["page"]   = f"P. {vol_page_m.group(2)}"
                elif raw_page:
                    h["page"] = raw_page

                if num_m:
                    h["hadith_number"] = f"N° {num_m.group(1)}"
                if page_m and h["page"] == MISSING:
                    h["page"] = f"P. {page_m.group(1)}"

            elif "خلاصة حكم" in label or ("الحكم" in label and "خلاصة" in label):
                h["hukm_raw"] = parent_text.strip()
                hukm = _apply_hukm(parent_text.strip())
                h["hukm"] = hukm
                h["all_verdicts"].append({
                    "mohaddith": h.get("mohaddith", ""),
                    **hukm,
                })

        # ── URL page de détail ──────────────────────────────────────────
        for link in tree.xpath('.//a[contains(@href,"/hadith/")]'):
            href = link.get("href", "")
            if href:
                h["detail_url"] = DORAR_BASE + href if href.startswith("/") else href
                break

        # ── Validation minimale ─────────────────────────────────────────
        if h["ar_text"] or h["rawi"] or h["hukm_raw"]:
            results.append(h)

    log.info(f"Hadiths parsés : {len(results)}")
    return results


# ─────────────────────────────────────────────────────────────────────────────
#  ④ EXTRACTION SILSILA — SCRAPING PROFOND PAGE DE DÉTAIL
# ─────────────────────────────────────────────────────────────────────────────

# Sélecteurs XPath par ordre de précision décroissante
_SANAD_XPATHS: list[str] = [
    './/div[contains(@class,"sanad")]//a[contains(@href,"/rijal/")]',
    './/div[contains(@class,"isnad")]//a[contains(@href,"/rijal/")]',
    './/div[@id="sanad"]//a[contains(@href,"/rijal/")]',
    './/div[@id="isnad"]//a[contains(@href,"/rijal/")]',
    './/section[contains(@class,"sanad")]//a[contains(@href,"/rijal/")]',
    './/p[contains(@class,"sanad")]//a[contains(@href,"/rijal/")]',
    './/span[contains(@class,"sanad")]//a[contains(@href,"/rijal/")]',
    './/div[contains(@class,"hadith-body")]//a[contains(@href,"/rijal/")]',
    # Fallback global hors blocs de navigation
    (
        './/div[not(contains(@class,"navbar")) '
        'and not(contains(@class,"nav-")) '
        'and not(contains(@class,"menu")) '
        'and not(contains(@class,"footer")) '
        'and not(contains(@class,"header"))]'
        '//a[contains(@href,"/rijal/")]'
    ),
]


async def _fetch_silsila_from_detail(
    client: httpx.AsyncClient,
    detail_url: str,
) -> list[dict[str, Any]]:
    """
    Scrape la page de détail Dorar pour extraire la silsila complète.

    Essaie les 9 sélecteurs XPath par ordre de précision.
    Déduplique par ID Dorar puis par nom normalisé.
    Retourne [] si la page est inaccessible ou sans données.
    """
    chain: list[dict[str, Any]] = []
    if not detail_url:
        return chain

    try:
        resp = await client.get(
            detail_url,
            headers={"User-Agent": "Mozilla/5.0 (AlMizan/24.0; Islamic Science Research)"},
            timeout=TIMEOUT_DETAIL,
            follow_redirects=True,
        )
        if resp.status_code != 200:
            log.warning(f"Détail HTTP {resp.status_code} — {detail_url}")
            return chain

        tree = lxml_html.fromstring(resp.text)
        narrator_links: list[Any] = []

        for selector in _SANAD_XPATHS:
            try:
                links = tree.xpath(selector)
                if links:
                    log.info(f"Silsila via XPath ({len(links)} liens) : {selector[:55]}…")
                    narrator_links = links
                    break
            except Exception:
                continue

        if not narrator_links:
            log.warning(f"Aucun lien /rijal/ dans : {detail_url}")
            return chain

        seen_ids:   set[str] = set()
        seen_norms: set[str] = set()

        for link in narrator_links:
            href  = link.get("href", "")
            rid   = _extract_rijal_id(href)
            name  = _clean_isnad_name(link.text_content())

            if not name or len(name) < 2:
                continue

            norm = _normalize_ar(name)
            if rid and rid in seen_ids:
                continue
            if norm in seen_norms:
                continue

            if rid:
                seen_ids.add(rid)
            seen_norms.add(norm)

            _c = _infer_century(name)
            chain.append(SilsilaNode(
                name_ar=name,
                fr_name=_transliterate(name),
                role="sahabi" if _is_sahabi(name) else "narrator",
                rawi_id=rid,
                rawi_url=DORAR_BASE + href if href.startswith("/") else href,
                century=_c,
                death_year=_century_to_death_year(_c),
                verified=True,
            ).model_dump())

        log.info(f"Silsila extraite : {len(chain)} nœuds depuis {detail_url}")

    except httpx.TimeoutException:
        log.warning(f"Timeout scraping détail : {detail_url}")
    except Exception as exc:
        log.warning(f"Erreur scraping silsila : {exc}")

    return chain


# ─────────────────────────────────────────────────────────────────────────────
#  ⑤ RECONSTRUCTION SILSILA — ORDRE PROPHÉTIQUE
# ─────────────────────────────────────────────────────────────────────────────

def _build_silsila(
    hadith: dict[str, Any],
    detail_chain: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """
    Reconstruit la silsila dans l'ordre chronologique :
    Prophète ﷺ → Sahabi → Tâbi'î → … → Muhaddith compilateur.

    Priorité :
      ① detail_chain  : scraping direct de la page Dorar (source la plus fiable)
      ② Inférence     : depuis rawi + mohaddith + générations intermédiaires

    RÈGLE ABSOLUE : Le Prophète ﷺ est TOUJOURS le Nœud 1.
    Les nœuds inférés (non scrappés) sont marqués verified=False.
    """
    chain: list[dict[str, Any]] = []

    # ── Nœud 1 : LE PROPHÈTE ﷺ ─────────────────────────────────────────
    chain.append(SilsilaNode(
        rank=1,
        name_ar="النَّبِيُّ مُحَمَّد ﷺ",
        fr_name="Le Prophète Muhammad ﷺ",
        role="prophet",
        rawi_id=None,
        rawi_url="",
        century="1H",
        death_year=_century_to_death_year("1H"),
        verified=True,
    ).model_dump())

    # ── CAS 1 : chaîne extraite par scraping ───────────────────────────
    if detail_chain and len(detail_chain) >= 1:
        for rank_offset, node in enumerate(detail_chain, start=2):
            _c = node.get("century") or MISSING
            chain.append(SilsilaNode(
                rank=rank_offset,
                name_ar=node.get("name_ar") or MISSING,
                fr_name=node.get("fr_name") or _transliterate(node.get("name_ar", "")),
                role=node.get("role", "narrator"),
                rawi_id=node.get("rawi_id"),
                rawi_url=node.get("rawi_url", ""),
                century=_c,
                death_year=node.get("death_year", _century_to_death_year(_c)),
                verified=True,
            ).model_dump())
        log.info(f"Silsila (scraping) : {len(chain)} nœuds")
        return _dedup_chain(chain)

    # ── CAS 2 : inférence depuis rawi + mohaddith ───────────────────────
    rawi_name  = hadith.get("rawi", "")
    mohadd_name = hadith.get("mohaddith", "")

    if rawi_name:
        rawi_role = "sahabi" if _is_sahabi(rawi_name) else "narrator"
        _rc = "1H" if rawi_role == "sahabi" else "2H"
        chain.append(SilsilaNode(
            rank=2,
            name_ar=rawi_name,
            fr_name=_transliterate(rawi_name),
            role=rawi_role,
            rawi_id=hadith.get("rawi_id"),
            rawi_url=hadith.get("rawi_url", ""),
            century=_rc,
            death_year=_century_to_death_year(_rc),
            verified=True,
        ).model_dump())

        if rawi_role == "sahabi":
            # Tâbi'î toujours présent entre Sahabi et compilateur 3H+
            chain.append(SilsilaNode(
                rank=3,
                name_ar="تَابِعِيّ",
                fr_name="Tâbi'î — Génération des Successeurs (2H)",
                role="tabii",
                rawi_id=None,
                rawi_url="",
                century="2H",
                death_year=_century_to_death_year("2H"),
                verified=False,  # nœud INFÉRÉ
            ).model_dump())

            century_mohadd = _infer_century(mohadd_name)
            if century_mohadd not in ("1H", "2H") or century_mohadd == MISSING:
                chain.append(SilsilaNode(
                    rank=4,
                    name_ar="تَابِعُ التَّابِعِيّ",
                    fr_name="Tâbi' al-Tâbi'în — 2ème génération des Successeurs (3H)",
                    role="ttt",
                    rawi_id=None,
                    rawi_url="",
                    century="3H",
                    death_year=_century_to_death_year("3H"),
                    verified=False,  # nœud INFÉRÉ
                ).model_dump())

    if mohadd_name:
        _mc = _infer_century(mohadd_name)
        chain.append(SilsilaNode(
            rank=len(chain) + 1,
            name_ar=mohadd_name,
            fr_name=_transliterate(mohadd_name),
            role="muhaddith",
            rawi_id=hadith.get("mohaddith_id"),
            rawi_url=hadith.get("mohaddith_url", ""),
            century=_mc,
            death_year=_century_to_death_year(_mc),
            verified=True,
        ).model_dump())

    log.info(f"Silsila (inférée) : {len(chain)} nœuds")
    return _dedup_chain(chain)


def _dedup_chain(chain: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Déduplique les nœuds et renuméroter les rangs proprement."""
    seen:   set[str] = set()
    result: list[dict[str, Any]] = []

    for node in chain:
        key = _normalize_ar(node.get("name_ar", ""))
        role_key = f"__role__{node.get('role', '')}_{node.get('century', '')}"
        eff_key  = key if key else role_key

        if eff_key not in seen:
            seen.add(eff_key)
            result.append(node)

    for i, node in enumerate(result, start=1):
        node["rank"] = i

    return result


def _silsila_is_valid(chain: list[dict[str, Any]]) -> bool:
    """Valide si la silsila contient au moins 2 nœuds vérifiés."""
    return len(chain) >= 2 and sum(1 for n in chain if n.get("verified")) >= 2


def _derive_shurut_sihhah_from_silsila(
    silsila: list[dict[str, Any]],
    jarh_grouped: dict[str, dict[str, Any]],
    hukm_level: str,
    hukm_raw: str,
) -> str:
    """
    Déduit l'état des 5 conditions classiques du Sahîh (Ibn as-Salah,
    Muqaddima) UNIQUEMENT à partir des données déjà scrapées par Dorar
    et du dictionnaire Hukm verrouillé.

    Les 5 conditions canoniques :
      1. Ittisâl as-Sanad    — Continuité ininterrompue de la chaîne
      2. 'Adâlat ar-Ruwât    — Intégrité morale des rapporteurs
      3. Dabt ar-Ruwât       — Précision mémorielle des rapporteurs
      4. 'Adam ash-Shudhûdh  — Absence d'anomalie (contradiction de sens)
      5. 'Adam al-'Illah     — Absence de défaut caché

    PROTOCOLE ZÉRO HALLUCINATION :
      • Aucun appel IA, aucune supposition.
      • Si Dorar ne fournit aucun indicateur → « NON INDIQUÉE PAR LA SOURCE ».
      • « ÉTABLIE » seulement si la preuve est directe (hukm sahih/hasan
        + absence de marqueur négatif).
      • « ABSENTE » seulement si Dorar mentionne explicitement le défaut.

    Retourne un bloc markdown consommable par _mzMd côté frontend.
    """
    raw = hukm_raw or ""

    # ── Condition 1 : Ittisâl as-Sanad (continuité) ───────────────────
    n_verified = sum(1 for n in silsila if n.get("verified"))
    if n_verified >= 3:
        c1_state = "ÉTABLIE"
        c1_note  = f"silsila scrapée ({n_verified} nœuds vérifiés)"
    elif n_verified >= 2:
        c1_state = "PARTIELLE"
        c1_note  = f"chaîne minimale ({n_verified} nœuds vérifiés)"
    else:
        c1_state = "NON INDIQUÉE PAR LA SOURCE"
        c1_note  = "silsila insuffisante dans Dorar"

    # ── Condition 2 : 'Adâlat ar-Ruwât (intégrité morale) ─────────────
    jarh_neg_re = re.compile(
        r"كذاب|متروك|وضاع|متهم|kadhdhab|matruk|wadd|muttaham",
        re.IGNORECASE,
    )
    if jarh_neg_re.search(raw):
        c2_state = "ABSENTE"
        c2_note  = "rapporteur désigné menteur/abandonné dans hukm_raw"
    elif hukm_level in ("sahih", "hasan"):
        c2_state = "ÉTABLIE"
        c2_note  = "hukm global sahih/hasan — rapporteurs réputés intègres"
    else:
        c2_state = "NON INDIQUÉE PAR LA SOURCE"
        c2_note  = "intégrité non attestée explicitement par Dorar"

    # ── Condition 3 : Dabt ar-Ruwât (précision mémorielle) ────────────
    dabt_neg_re = re.compile(
        r"ضعيف|سيء\s*الحفظ|مختلط|لين|layyin|da'?if|sayyi'|mukhtalit",
        re.IGNORECASE,
    )
    if dabt_neg_re.search(raw):
        c3_state = "ABSENTE"
        c3_note  = "précision mémorielle explicitement contestée"
    elif hukm_level in ("sahih", "hasan"):
        c3_state = "ÉTABLIE"
        c3_note  = "hukm global sahih/hasan — précision reconnue"
    else:
        c3_state = "NON INDIQUÉE PAR LA SOURCE"
        c3_note  = "précision non attestée explicitement par Dorar"

    # ── Condition 4 : 'Adam ash-Shudhûdh (absence d'anomalie) ─────────
    if re.search(r"شاذ|منكر|shadh|munkar", raw, re.IGNORECASE):
        c4_state = "ABSENTE"
        c4_note  = "hadith marqué shâdh ou munkar"
    else:
        c4_state = "NON INDIQUÉE PAR LA SOURCE"
        c4_note  = "Dorar n'indique ni shudhûdh ni son absence"

    # ── Condition 5 : 'Adam al-'Illah (absence de défaut caché) ───────
    if re.search(r"معلول|معل\b|ma'?lul|mu'?allal", raw, re.IGNORECASE):
        c5_state = "ABSENTE"
        c5_note  = "hadith marqué mu'allal"
    else:
        c5_state = "NON INDIQUÉE PAR LA SOURCE"
        c5_note  = "Dorar n'indique aucune 'illah"

    return (
        f"**1. Ittisâl as-Sanad** (Continuité) : {c1_state} — {c1_note}\n\n"
        f"**2. 'Adâlat ar-Ruwât** (Intégrité) : {c2_state} — {c2_note}\n\n"
        f"**3. Dabt ar-Ruwât** (Précision) : {c3_state} — {c3_note}\n\n"
        f"**4. 'Adam ash-Shudhûdh** (Absence d'anomalie) : {c4_state} — {c4_note}\n\n"
        f"**5. 'Adam al-'Illah** (Absence de défaut caché) : {c5_state} — {c5_note}"
    )


# ─────────────────────────────────────────────────────────────────────────────
#  ⑥ TRADUCTION FR→AR VIA CLAUDE HAIKU
# ─────────────────────────────────────────────────────────────────────────────

async def _translate_query_fr_to_ar(
    client: httpx.AsyncClient,
    query_fr: str,
    api_key: str,
) -> str:
    """Traduit la requête de recherche française en arabe classique."""
    if not api_key:
        log.warning("ANTHROPIC_API_KEY manquante — traduction ignorée")
        return query_fr

    system_prompt = (
        "Tu es un traducteur spécialisé en arabe classique (fusha) pour la "
        "recherche de hadiths dans la base de données Dorar.net. "
        "Traduis UNIQUEMENT la requête ci-dessous en mots arabes adaptés à une "
        "recherche hadith. "
        "Retourne UNIQUEMENT les mots arabes, sans explication ni ponctuation."
    )

    try:
        resp = await client.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": ANTHROPIC_MODEL,
                "max_tokens": 150,
                "system": system_prompt,
                "messages": [{"role": "user", "content": f"Requête : {query_fr}"}],
            },
            timeout=TIMEOUT_CLAUDE,
        )
        if resp.status_code == 200:
            translated = (
                resp.json().get("content", [{}])[0].get("text", "").strip()
            )
            log.info(f"Traduction : «{query_fr}» → «{translated}»")
            return translated or query_fr
        else:
            log.error(f"ANTHROPIC FAILURE {resp.status_code} | URL: {resp.url} | Body: {resp.text}")
    except Exception as exc:
        log.warning(f"Erreur traduction : {exc}")

    return query_fr


async def _translate_matn_ar_to_fr(
    client: httpx.AsyncClient,
    ar_text: str,
    api_key: str,
    hukm_fr: str,
) -> str:
    """
    Traduit le matn arabe en français académique.
    Le glossaire protégé est injecté dans le prompt pour
    préserver les termes de 'Aqîdah intacts.
    """
    if not api_key or not ar_text:
        return MISSING

    glossaire_protege = (
        "TERMES PROTÉGÉS — À conserver tels quels avec translittération :\n"
        "• استوى على العرش → 'S'est établi sur le Trône' (Istawâ 'alâ al-'Arsh)\n"
        "• نزول / ينزل → 'Descente / Il descend' (An-Nuzûl / Yanzil)\n"
        "• يد الله → 'La Main d'Allah' (Yad Allâh)\n"
        "• وجه الله → 'Le Visage d'Allah' (Wajh Allâh)\n"
        "• ساق → 'Le Tibia' (As-Sâq)\n"
        "• صراط → 'Le Pont' (As-Sirât)\n"
        "• جنة → 'Le Paradis' (Al-Janna)\n"
        "• نار → 'L'Enfer' (An-Nâr)\n"
        "• شفاعة → 'L'Intercession' (Ash-Shafâ'a)\n"
    )

    prompt = (
        "Tu es un traducteur islamique académique spécialisé dans la science du hadith. "
        "Traduis ce hadith arabe en français classique et rigoureux. "
        "RÈGLES ABSOLUES :\n"
        "1. Ne modifie JAMAIS le sens théologique du texte.\n"
        "2. Place les termes arabes importants entre parenthèses après leur traduction.\n"
        "3. N'utilise JAMAIS 'pouvoir', 'autorité' ou 'présence' pour les Attributs d'Allah.\n"
        f"{glossaire_protege}\n"
        f"Grade de ce hadith selon les muhaddithîn : {hukm_fr}\n\n"
        f"Texte arabe :\n{ar_text}\n\n"
        "Traduction française :"
    )

    try:
        resp = await client.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": ANTHROPIC_MODEL,
                "max_tokens": 600,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=TIMEOUT_CLAUDE,
        )
        if resp.status_code == 200:
            result = (
                resp.json().get("content", [{}])[0].get("text", "").strip()
            )
            return result or MISSING
        else:
            log.error(f"ANTHROPIC FAILURE {resp.status_code} | URL: {resp.url} | Body: {resp.text}")
    except Exception as exc:
        log.warning(f"Erreur traduction matn : {exc}")

    return MISSING


async def _enrich_via_claude(
    client: httpx.AsyncClient,
    ar_text: str,
    hukm_fr: str,
    savant: str,
    source: str,
    api_key: str,
) -> dict[str, str]:
    """
    Enrichissement textuel d'un hadith via Claude Haiku 4.5 SOUS CONTRAINTE
    « Zéro Hallucination » — Protocole Amâna Médine (Action 2).

    Champs demandés :
      • gharib       → vocabulaire des mots rares du matn
      • sabab_wurud  → circonstance de narration SI attestée (très rare)
      • fawaid       → leçons pratiques concrètes

    Garanties anti-hallucination :
      1. temperature = 0.0 (déterminisme maximal)
      2. Prompt explicite : « vide par défaut, remplit seulement si cité »
      3. Extraction JSON stricte, fallback {} si parse échoue
      4. Toute exception → retour silencieux {"": "", "": "", "": ""}
         (Option Silencieuse validée Q3)
      5. Aucune clé ne peut être None — toujours str (compatible Pydantic)

    Retourne un dict à 3 clés str ; les valeurs peuvent être vides.
    """
    blank = {"gharib": "", "sabab_wurud": "", "fawaid": ""}

    if not api_key or not ar_text:
        return blank

    system_prompt = (
        "Tu es un savant du hadith travaillant pour Mîzân as-Sunnah, "
        "projet de science du hadith présenté à Médine.\n\n"
        "╔══════════════════════════════════════════════════════════════════╗\n"
        "║   PROTOCOLE AMÂNA — VERROU ABSOLU ZÉRO HALLUCINATION            ║\n"
        "╠══════════════════════════════════════════════════════════════════╣\n"
        "║  SOURCES AUTORISÉES — DEUX OUVRAGES UNIQUEMENT :                ║\n"
        "║    ① Fath al-Bârî  (ابن حجر العسقلاني)                         ║\n"
        "║    ② An-Nihâyah fî Gharîb al-Hadîth  (ابن الأثير)              ║\n"
        "║  RÈGLES ABSOLUES :                                               ║\n"
        "║  • Remplir un champ UNIQUEMENT si l'information est explicitement║\n"
        "║    attestée dans l'un de ces deux ouvrages.                      ║\n"
        "║  • Dans le DOUTE : chaîne vide \"\" — TOUJOURS.                  ║\n"
        "║  • NE JAMAIS deviner, extrapoler ou reformuler un champ.         ║\n"
        "║  • Mots interdits : « probablement », « sans doute »,           ║\n"
        "║    « peut-être », « il semble », « on peut dire ».              ║\n"
        "║  • Aucun texte hors du JSON (pas de markdown, pas de commentaire)║\n"
        "║  • Chaque valeur absente ou incertaine = chaîne vide \"\"         ║\n"
        "╚══════════════════════════════════════════════════════════════════╝"
    )

    user_content = (
        f"Hadith arabe :\n{ar_text}\n\n"
        f"Grade selon les muhaddithîn : {hukm_fr or 'non spécifié'}\n"
        f"Rapporté par : {savant or 'non spécifié'}\n"
        f"Source : {source or 'non spécifiée'}\n\n"
        "Retourne EXACTEMENT ce JSON (rien avant, rien après) :\n"
        '{\n'
        '  "gharib": "Explication des mots rares selon An-Nihâyah d\'Ibn al-Athîr — 1 à 3 mots MAX, format «mot : explication» séparés par «;». Chaîne vide \"\" si aucun mot rare ou si An-Nihâyah ne le mentionne pas.",\n'
        '  "sabab_wurud": "Circonstance de narration UNIQUEMENT si Ibn Hajar la cite dans Fath al-Bârî. Chaîne vide \"\" sinon — ce champ est \"\" dans 95% des cas.",\n'
        '  "fawaid": "1 à 3 leçons pratiques issues de Fath al-Bârî, format puces «• leçon». Chaîne vide \"\" si Fath al-Bârî n\'en mentionne pas pour ce hadith."\n'
        '}'
    )

    try:
        resp = await client.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key":         api_key,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
            },
            json={
                "model":       ANTHROPIC_MODEL,
                "max_tokens":  1024,
                "temperature": 0.0,  # Verrou déterministe
                "system":      system_prompt,
                "messages":    [{"role": "user", "content": user_content}],
            },
            timeout=TIMEOUT_CLAUDE,
        )
    except Exception as exc:
        log.warning(f"Erreur enrich Claude (réseau) : {exc}")
        return blank

    if resp.status_code != 200:
        log.error(f"ANTHROPIC FAILURE {resp.status_code} | URL: {resp.url} | Body: {resp.text}")
        return blank

    try:
        raw = (
            resp.json().get("content", [{}])[0].get("text", "") or ""
        ).strip()
    except Exception as exc:
        log.warning(f"Erreur enrich Claude (parse body) : {exc}")
        return blank

    # Extraction JSON robuste : Claude peut entourer de ```json … ```
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        log.warning("Enrich Claude : aucun objet JSON trouvé dans la réponse")
        return blank

    try:
        data = json.loads(match.group(0))
    except Exception as exc:
        log.warning(f"Erreur enrich Claude (json.loads) : {exc}")
        return blank

    if not isinstance(data, dict):
        return blank

    # Normalisation stricte : toutes les valeurs deviennent des str
    return {
        "gharib":      (data.get("gharib")      or "").strip() if isinstance(data.get("gharib"),      str) else "",
        "sabab_wurud": (data.get("sabab_wurud") or "").strip() if isinstance(data.get("sabab_wurud"), str) else "",
        "fawaid":      (data.get("fawaid")      or "").strip() if isinstance(data.get("fawaid"),      str) else "",
    }


# ─────────────────────────────────────────────────────────────────────────────
#  ⑦ CONSTRUCTION DU TAKHRÎJ (RÉFÉRENCE PHYSIQUE COMPLÈTE)
# ─────────────────────────────────────────────────────────────────────────────

def _build_takhrij(hadith: dict[str, Any]) -> dict[str, str]:
    """
    Construit la référence Takhrîj complète.
    Un savant doit pouvoir ouvrir le livre physique grâce à ces données.

    Champs retournés :
      source         → Nom du recueil en arabe
      source_url     → Lien Dorar vers le recueil
      volume         → Volume (ex: "Vol. 3") ou MISSING
      page           → Page (ex: "P. 45") ou MISSING
      hadith_number  → Numéro (ex: "N° 1234") ou MISSING
      full_ref       → Référence complète textuelle assemblée
      detail_url     → Lien vers la page de détail Dorar
    """
    source        = hadith.get("source", "") or MISSING
    source_url    = hadith.get("source_url", "") or ""
    volume        = hadith.get("volume", MISSING) or MISSING
    page          = hadith.get("page", MISSING) or MISSING
    hadith_number = hadith.get("hadith_number", MISSING) or MISSING
    detail_url    = hadith.get("detail_url", "") or ""

    parts: list[str] = []
    if source != MISSING:
        parts.append(source)
    if volume != MISSING:
        parts.append(volume)
    if page != MISSING:
        parts.append(page)
    if hadith_number != MISSING:
        parts.append(hadith_number)

    return {
        "source":        source,
        "source_url":    source_url,
        "volume":        volume,
        "page":          page,
        "hadith_number": hadith_number,
        "full_ref":      " — ".join(parts) if parts else MISSING,
        "detail_url":    detail_url,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  ⑧ MOTEUR PRINCIPAL — PIPELINE TAKHRÎJ
# ─────────────────────────────────────────────────────────────────────────────

async def _run_takhrij(query: str) -> dict[str, Any]:
    """
    Pipeline complet du Takhrîj v24.0.

    Ordre d'exécution :
      INIT       → Validation requête
      TRADUCTION → FR→AR via Claude Haiku si requête non arabe
      DORAR      → Appel API officielle Dorar.net
      PARSING    → lxml XPath sur HTML brut
      SANAD      → Scraping page de détail (silsila complète)
      HUKM       → Application dictionnaire verrouillé + groupement
      TRADUCTION → Matn AR→FR via Claude Haiku
      ENVOI      → Résultat JSON structuré complet
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(30.0, connect=6.0),
        headers={"User-Agent": "Mozilla/5.0 (AlMizan/24.0; Hadith Science)"},
        follow_redirects=True,
        trust_env=False,
    ) as client:

        query_original = query.strip()
        query_ar = query_original

        # ── TRADUCTION FR→AR ──────────────────────────────────────────────
        if not _is_arabic(query_ar):
            query_ar = await _translate_query_fr_to_ar(client, query_ar, api_key)

        if not query_ar:
            return _error("Requête vide après normalisation")

        log.info(f"Recherche Dorar : «{query_ar}»")

        # ── APPEL API DORAR ───────────────────────────────────────────────
        try:
            resp = await client.get(
                DORAR_API_URL,
                params={"skey": query_ar, "type": "1"},
                timeout=TIMEOUT_DORAR,
            )
        except httpx.TimeoutException:
            return _error("Dorar.net : délai dépassé — réessayez dans quelques instants")
        except httpx.ConnectError as e:
            return _error(f"Connexion Dorar.net impossible : {e}")
        except Exception as e:
            return _error(f"Erreur réseau : {e}")

        if resp.status_code != 200:
            return _error(f"Dorar.net a retourné HTTP {resp.status_code}")

        # ── PARSING JSON ──────────────────────────────────────────────────
        try:
            dorar_data = resp.json()
        except Exception:
            return _error("Réponse Dorar non-JSON — structure inattendue")

        raw_html = dorar_data.get("ahadith", {}).get("result", "")
        if not raw_html or not raw_html.strip():
            return {
                "status":     "not_found",
                "message":    "Aucun hadith trouvé dans la base Dorar pour cette requête.",
                "query_ar":   query_ar,
                "query_orig": query_original,
                "results":    [],
                "total":      0,
                "version":    VERSION,
            }

        # ── PARSING HTML ──────────────────────────────────────────────────
        hadiths_bruts = _parse_dorar_html(raw_html)
        if not hadiths_bruts:
            return _error("Aucun hadith extrait — structure HTML Dorar inattendue")

        # ── DÉDUPLICATION PAR AUTORITÉ (anti-dégradation Sahîhayn) ───────
        hadiths_bruts = _dedupe_hadiths_by_authority(hadiths_bruts)

        # ── TRI : Sahîh en tête de liste (index 0) ──────────────────────
        hadiths_bruts = _sort_sahih_first(hadiths_bruts)

        # ── ENRICHISSEMENT DE CHAQUE HADITH ──────────────────────────────
        results: list[dict[str, Any]] = []

        for hadith in hadiths_bruts[:MAX_RESULTS]:

            # Silsila (scraping page de détail en priorité)
            detail_chain: list[dict[str, Any]] = []
            if hadith.get("detail_url"):
                detail_chain = await _fetch_silsila_from_detail(
                    client, hadith["detail_url"]
                )

            silsila = _build_silsila(hadith, detail_chain or None)
            hukm    = hadith.get("hukm") or _apply_hukm(hadith.get("hukm_raw", ""))
            # RÈGLE DE FER : score 100 (Bukhârî/Muslim) → Sahîh forcé
            hukm    = _apply_authority_override(hadith, hukm)
            grouped = _group_verdicts_by_mohaddith(hadith.get("all_verdicts", []))
            takhrij = _build_takhrij(hadith)

            # ── Zones déterministes (zéro IA, lecture seule Dorar) ──
            grille_albani_txt = _extract_albani_from_verdicts(
                hadith.get("all_verdicts", [])
            )
            shurut_sihhah_txt = _derive_shurut_sihhah_from_silsila(
                silsila,
                grouped,
                hukm.get("level", "unknown"),
                hadith.get("hukm_raw", ""),
            )

            # ── Traduction matn + enrichissement Claude EN PARALLÈLE ──
            matn_fr, enrich = await asyncio.gather(
                _translate_matn_ar_to_fr(
                    client,
                    hadith.get("ar_text", ""),
                    api_key,
                    hukm.get("fr", ""),
                ),
                _enrich_via_claude(
                    client,
                    hadith.get("ar_text", ""),
                    hukm.get("fr", ""),
                    hadith.get("mohaddith", ""),
                    hadith.get("source", ""),
                    api_key,
                ),
            )

            results.append({
                # ── Clé 1 : Matn ─────────────────────────────────────────
                "matn": {
                    "ar": hadith.get("ar_text", "") or MISSING,
                    "fr": matn_fr,
                },
                # ── Clé 2 : Silsila / Isnad ──────────────────────────────
                "silsila": {
                    "nodes":        silsila,
                    "total":        len(silsila),
                    "is_valid":     _silsila_is_valid(silsila),
                    "has_inferred": any(not n.get("verified") for n in silsila),
                    "source":       "dorar_detail" if detail_chain else "inference",
                },
                # ── Clé 3 : Hukm / Verdict ───────────────────────────────
                "hukm": {
                    "ar":           hukm.get("ar", MISSING),
                    "fr":           hukm.get("fr", MISSING),
                    "level":        hukm.get("level", "unknown"),
                    "color":        hukm.get("color", "#6b7280"),
                    "definition":   hukm.get("definition", MISSING),
                    "raw":          hukm.get("raw", "") or "",
                    "by_mohaddith": grouped,
                },
                # ── Clé 4 : Takhrîj ──────────────────────────────────────
                "takhrij": takhrij,
                # ── Clé 5 : Enrichissement (Amâna — "" si absent) ────────
                "enrichment": {
                    "grille_albani":    grille_albani_txt    or "",
                    "sanad_conditions": shurut_sihhah_txt    or "",
                    "gharib":           enrich.get("gharib",      ""),
                    "sabab_wurud":      enrich.get("sabab_wurud", ""),
                    "fawaid":           enrich.get("fawaid",      ""),
                },
                # ── Clé 6 : Métadonnées sources ───────────────────────────
                "metadata": {
                    "rawi": {
                        "ar":      hadith.get("rawi", "") or MISSING,
                        "fr":      _transliterate(hadith.get("rawi", "")) or MISSING,
                        "id":      hadith.get("rawi_id") or MISSING,
                        "url":     hadith.get("rawi_url", "") or "",
                        "role":    "sahabi" if _is_sahabi(hadith.get("rawi", "")) else "narrator",
                    },
                    "mohaddith": {
                        "ar":      hadith.get("mohaddith", "") or MISSING,
                        "fr":      _transliterate(hadith.get("mohaddith", "")) or MISSING,
                        "id":      hadith.get("mohaddith_id") or MISSING,
                        "url":     hadith.get("mohaddith_url", "") or "",
                        "century": _infer_century(hadith.get("mohaddith", "")),
                    },
                    "source": {
                        "ar":  hadith.get("source", "") or MISSING,
                        "url": hadith.get("source_url", "") or "",
                    },
                    # ── Barème de Fer : score d'autorité (miroir backend) ─
                    "authority_score": hadith.get("_authority_score", 0),
                },
            })

        return {
            "status":     "success",
            "query_ar":   query_ar,
            "query_orig": query_original,
            "results":    results,
            "total":      len(results),
            "version":    VERSION,
        }


def _error(msg: str, query_ar: str = "", query_orig: str = "") -> dict[str, Any]:
    """Construit une réponse d'erreur standardisée — 6 clés conteneur garanties."""
    log.error(f"[Mîzân v24] {msg}")
    return {
        "status":     "error",
        "message":    msg,
        "query_ar":   query_ar,
        "query_orig": query_orig,
        "results":    [],
        "total":      0,
        "version":    VERSION,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  ⑨ GÉNÉRATEUR SSE — FLUX TEMPS RÉEL
#  Ordre des événements : INITIALISATION → TRADUCTION → DORAR →
#                         SANAD → HUKM → ENVOI
# ─────────────────────────────────────────────────────────────────────────────

def _sse(event: str, data: Any) -> str:
    """Formate un événement SSE."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _stream_takhrij(query: str) -> AsyncGenerator[str, None]:
    """Générateur SSE : pipeline complet avec signalement de chaque étape."""

    yield _sse("status", {"step": "INITIALISATION", "message": "Ouverture des registres"})
    await asyncio.sleep(0)

    api_key        = os.environ.get("ANTHROPIC_API_KEY", "")
    query_original = query.strip()
    query_ar       = query_original

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(30.0, connect=6.0),
        headers={"User-Agent": "Mozilla/5.0 (AlMizan/24.0)"},
        follow_redirects=True,
        trust_env=False,
    ) as client:

        # TRADUCTION ───────────────────────────────────────────────────────
        if not _is_arabic(query_ar):
            yield _sse("status", {
                "step":    "TRADUCTION",
                "message": f"Traduction de «{query_ar}» en arabe classique",
            })
            query_ar = await _translate_query_fr_to_ar(client, query_ar, api_key)

        # DORAR ────────────────────────────────────────────────────────────
        yield _sse("status", {
            "step":    "DORAR",
            "message": f"Recherche Dorar.net : {query_ar}",
        })

        try:
            resp = await client.get(
                DORAR_API_URL,
                params={"skey": query_ar, "type": "1"},
                timeout=TIMEOUT_DORAR,
            )
        except Exception as exc:
            yield _sse("error", {"message": f"Erreur Dorar : {exc}"})
            yield _sse("done", [])
            return

        if resp.status_code != 200:
            yield _sse("error", {"message": f"Dorar HTTP {resp.status_code}"})
            yield _sse("done", [])
            return

        try:
            dorar_data = resp.json()
        except Exception:
            yield _sse("error", {"message": "Réponse Dorar non-JSON"})
            yield _sse("done", [])
            return

        raw_html = dorar_data.get("ahadith", {}).get("result", "")
        if not raw_html:
            yield _sse("done", [])
            return

        hadiths_bruts = _parse_dorar_html(raw_html)
        if not hadiths_bruts:
            yield _sse("done", [])
            return

        # ── DÉDUPLICATION PAR AUTORITÉ (anti-dégradation Sahîhayn) ───────
        hadiths_bruts = _dedupe_hadiths_by_authority(hadiths_bruts)

        # ── TRI : Sahîh en tête de liste (index 0) ──────────────────────
        hadiths_bruts = _sort_sahih_first(hadiths_bruts)

        # Envoi immédiat des données brutes pour affichage instantané
        yield _sse("dorar", [
            {
                "arabic_text": h.get("ar_text", ""),
                "savant":      h.get("mohaddith", ""),
                "source":      h.get("source", ""),
                "grade":       h.get("hukm_raw", ""),
                "rawi":        h.get("rawi", ""),
            }
            for h in hadiths_bruts[:MAX_RESULTS]
        ])

        # SANAD + HUKM + ENRICHISSEMENT ────────────────────────────────────
        for idx, hadith in enumerate(hadiths_bruts[:MAX_RESULTS]):

            yield _sse("status", {
                "step":    "SANAD",
                "message": (
                    f"Extraction silsila hadith {idx + 1}/"
                    f"{min(len(hadiths_bruts), MAX_RESULTS)}"
                ),
            })

            detail_chain: list[dict[str, Any]] = []
            if hadith.get("detail_url"):
                detail_chain = await _fetch_silsila_from_detail(
                    client, hadith["detail_url"]
                )

            silsila = _build_silsila(hadith, detail_chain or None)

            yield _sse("status", {
                "step":    "HUKM",
                "message": f"Application du dictionnaire Hukm — hadith {idx + 1}",
            })

            hukm    = hadith.get("hukm") or _apply_hukm(hadith.get("hukm_raw", ""))
            # RÈGLE DE FER : score 100 (Bukhârî/Muslim) → Sahîh forcé
            hukm    = _apply_authority_override(hadith, hukm)
            grouped = _group_verdicts_by_mohaddith(hadith.get("all_verdicts", []))
            takhrij = _build_takhrij(hadith)

            # ── Zones déterministes (zéro IA, lecture seule Dorar) ──
            grille_albani_txt = _extract_albani_from_verdicts(
                hadith.get("all_verdicts", [])
            )
            shurut_sihhah_txt = _derive_shurut_sihhah_from_silsila(
                silsila,
                grouped,
                hukm.get("level", "unknown"),
                hadith.get("hukm_raw", ""),
            )

            # ── Traduction matn + enrichissement Claude EN PARALLÈLE ──
            #    Option Silencieuse : toute erreur → chaînes vides, pas de
            #    propagation au frontend, pas de badge UI.
            matn_fr, enrich = await asyncio.gather(
                _translate_matn_ar_to_fr(
                    client,
                    hadith.get("ar_text", ""),
                    api_key,
                    hukm.get("fr", ""),
                ),
                _enrich_via_claude(
                    client,
                    hadith.get("ar_text", ""),
                    hukm.get("fr", ""),
                    hadith.get("mohaddith", ""),
                    hadith.get("source", ""),
                    api_key,
                ),
            )

            yield _sse("hadith", {
                "index": idx,
                "data": {
                    # ── Zone 1 : Matn ───────────────────────────────────
                    "arabic_text":    hadith.get("ar_text", "") or MISSING,
                    "french_text":    matn_fr,
                    # ── Zone 2 : Métadonnées sources ────────────────────
                    "savant":         hadith.get("mohaddith", "") or MISSING,
                    "source":         hadith.get("source", "") or MISSING,
                    "rawi":           hadith.get("rawi", "") or MISSING,
                    # ── Zone 3 : Hukm / Verdict ─────────────────────────
                    "grade_ar":       hukm.get("ar", MISSING),
                    "grade_fr":       hukm.get("fr", MISSING),
                    "grade_level":    hukm.get("level", "unknown"),
                    "grade_color":    hukm.get("color", "#6b7280"),
                    "grade_def":      hukm.get("definition", MISSING),
                    "grade_by_mohadd": grouped,
                    # ── Zone 4 : Silsila / Isnad ─────────────────────────
                    "silsila":        silsila,
                    "silsila_nodes":  len(silsila),
                    "silsila_valid":  _silsila_is_valid(silsila),
                    # ── Zone 5 : Takhrîj ─────────────────────────────────
                    "takhrij":        takhrij,
                    # ── Zone 6 : Score d'autorité (Barème de Fer) ────────
                    "_authority_score": hadith.get("_authority_score", 0),
                    # ── Zones 7-12 : Enrichissement (Amâna — "" si absent) ─
                    "grille_albani":    grille_albani_txt    or "",
                    "sanad_conditions": shurut_sihhah_txt    or "",
                    "gharib":           enrich.get("gharib",      ""),
                    "sabab_wurud":      enrich.get("sabab_wurud", ""),
                    "fawaid":           enrich.get("fawaid",      ""),
                },
            })

        yield _sse("status", {
            "step": "HUKM", "message": "Pipeline terminé — résultats prêts"
        })
        yield _sse("done", {"total": min(len(hadiths_bruts), MAX_RESULTS)})


# ─────────────────────────────────────────────────────────────────────────────
#  ⑩ HANDLER VERCEL — BaseHTTPRequestHandler
# ─────────────────────────────────────────────────────────────────────────────

class handler(BaseHTTPRequestHandler):
    """
    Handler HTTP Vercel — Mîzân as-Sunnah v24.0.

    Routes :
      GET  /api/health        → Statut + statistiques du lexique
      GET  /api/search?q=...  → Flux SSE temps réel (Accept: text/event-stream)
                                ou JSON classique (fallback)
      POST /api/              → Takhrîj complet JSON {"query": "..."}
      OPTIONS *               → CORS preflight (204)
    """

    _CORS: dict[str, str] = {
        "Access-Control-Allow-Origin":  "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept",
        "Access-Control-Max-Age":       "86400",
    }

    def _json(self, data: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        for k, v in self._CORS.items():
            self.send_header(k, v)
        self.send_header("Content-Type",    "application/json; charset=utf-8")
        self.send_header("Content-Length",  str(len(body)))
        self.send_header("X-Mizan-Version", VERSION)
        self.end_headers()
        self.wfile.write(body)

    def _sse_headers(self) -> None:
        self.send_response(200)
        for k, v in self._CORS.items():
            self.send_header(k, v)
        self.send_header("Content-Type",      "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control",     "no-cache")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("X-Mizan-Version",   VERSION)
        self.end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        for k, v in self._CORS.items():
            self.send_header(k, v)
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)

        # ── Health check ─────────────────────────────────────────────────
        if path.endswith("health"):
            self._json({
                "status":       "ok",
                "version":      VERSION,
                "service":      "Mîzân as-Sunnah — Moteur de Takhrîj",
                "hukm_grades":  len(_HUKM_AR_FR),
                "hukm_glossary": len(HUKM_GLOSSARY),
                "veto_patterns": len(_VETO_PATTERNS),
                "translitt_db": len(_TRANSLITT),
                "sahabas_db":   len(_SAHABAS),
                "xpath_selectors": len(_SANAD_XPATHS),
                "pipeline":     [
                    "INITIALISATION", "TRADUCTION",
                    "DORAR", "SANAD", "HUKM", "ENVOI",
                ],
            })
            return

        # ── Recherche SSE ou JSON ─────────────────────────────────────────
        if path.endswith("search") and params.get("q"):
            query = params["q"][0].strip()
            if not query:
                self._json({"error": "Paramètre q vide"}, status=400)
                return

            accept = self.headers.get("Accept", "")

            if "text/event-stream" in accept:
                self._sse_headers()

                async def _run_sse() -> None:
                    async for chunk in _stream_takhrij(query):
                        try:
                            self.wfile.write(chunk.encode("utf-8"))
                            self.wfile.flush()
                        except BrokenPipeError:
                            break

                try:
                    asyncio.run(_run_sse())
                except Exception as exc:
                    log.exception(f"Erreur SSE : {exc}")
            else:
                try:
                    result = asyncio.run(_run_takhrij(query))
                    self._json(result)
                except Exception as exc:
                    log.exception("Erreur pipeline GET JSON")
                    self._json(_error(f"Erreur interne : {exc}"), status=500)
            return

        self._json({"error": "Route inconnue", "version": VERSION}, status=404)

    def log_message(self, fmt: str, *args: Any) -> None:
        log.info(fmt % args)
