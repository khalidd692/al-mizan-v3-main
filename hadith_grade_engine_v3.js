/**
 * AL MĪZĀN — Moteur de Verdict Infaillible v3.0 (FINAL)
 * ═══════════════════════════════════════════════════════
 * Audit croisé : Claude (Architecte) + Grok + DeepSeek
 * Méthodologie : Salaf aṣ-Ṣāliḥ / Imams Mutaqaddimūn
 * Source verdicts : Dorar.net (خلاصة حكم المحدث)
 *
 * GARANTIES :
 *   ① normalizeArabic — Tashkīl complet, Alif, Ya, ZWJ, chiffres arabes
 *   ② Négations par REGEX (pas indexOf) — fenêtre + motifs précis
 *   ③ Exception "إلا أن" — dégrade Sahih → Da'if si détectée
 *   ④ Tous les termes Mutaqaddimūn + Dorar.net (90+ termes)
 *   ⑤ validateConstitution — filtre sectarisme & rationalisme moderne
 *   ⑥ JAMAIS fallback Da'if — retourne غير مصنف si inconnu
 *   ⑦ requiresReview flag pour revue humaine
 */

'use strict';

// ═══════════════════════════════════════════════════════════════
// BLOC 1 — NORMALISATION ARABE EXHAUSTIVE
// Synthèse : Grok (Unicode étendu) + DeepSeek (Ya/chiffres/ZWJ) + Claude (Tatweel)
// ═══════════════════════════════════════════════════════════════

function normalizeArabic(text) {
  if (typeof text !== 'string' || !text) return '';

  return text
    // 1. Suppression exhaustive Tashkīl étendu (Grok + DeepSeek combinés)
    //    Couvre : Fatha, Damma, Kasra, Sukun, Shadda, Tanwin, Madd,
    //             diacritiques Coran, extensions Unicode arabes
    .replace(/[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u08D4-\u08FF]/g, '')

    // 2. Suppression Tatweel / Kashida ـ
    .replace(/\u0640/g, '')

    // 3. Suppression Zero-Width Joiners, LTR/RTL marks, BOM (DeepSeek)
    .replace(/[\u200B-\u200F\u202A-\u202E\uFEFF]/g, '')

    // 4. Normalisation Alif (toutes formes → ا)
    .replace(/[أإآٱ]/g, 'ا')

    // 5. Normalisation Ya et Alif Maqsura (DeepSeek : direct [ىئ] → ي)
    .replace(/[ىئ]/g, 'ي')

    // 6. Normalisation Waw Hamza
    .replace(/ؤ/g, 'و')

    // 7. Ta Marbuta → Ha (convention de matching)
    .replace(/ة/g, 'ه')

    // 8. Suppression Hamza isolée (DeepSeek)
    .replace(/ء/g, '')

    // 9. Normalisation chiffres arabes orientaux → latins
    .replace(/[٠-٩]/g, function(d) {
      return String.fromCharCode(d.charCodeAt(0) - 0x0660 + 48);
    })

    // 10. Ponctuation arabe → espace
    .replace(/[.,;:!?،؛؟«»"']/g, ' ')

    // 11. Espaces multiples
    .replace(/\s+/g, ' ')
    .trim();
}

// ═══════════════════════════════════════════════════════════════
// BLOC 2 — MOTIFS DE NÉGATION (REGEX — plus précis que indexOf)
// Synthèse : DeepSeek (regex) + Grok (liste) + Claude (fenêtre)
// ═══════════════════════════════════════════════════════════════

var NEGATION_PATTERNS = [
  /ليس\s+ب(صحيح|ثابت|حسن|قوي|شيء)/,     // Laysa bi-Sahih / bi-Shay' / bi-Hasan
  /غير\s+(صحيح|ثابت|محفوظ|حسن)/,          // Ghayr Sahih, Ghayr Thabit
  /لا\s+(يصح|يثبت|اصل\s+له|يصحح)/,        // La Yasihhu, La Asla Lahu
  /لم\s+(يثبت|يرد|يقم\s+به\s+سند)/,       // Lam Yathbut
  /غير\s+ثابت/,
  /لا\s+اصل\s+له/,
  /لا\s+يعرف\s+له\s+اصل/,
];

/**
 * Détecte si un match est précédé d'une négation.
 * Double approche : regex globaux + fenêtre 25 chars avant le match.
 */
function isNegated(normalizedFull, matchIndex) {
  // Approche 1 : regex sur tout le texte
  for (var i = 0; i < NEGATION_PATTERNS.length; i++) {
    if (NEGATION_PATTERNS[i].test(normalizedFull)) return true;
  }
  // Approche 2 : fenêtre avant le match
  var before = normalizedFull.substring(Math.max(0, matchIndex - 25), matchIndex);
  var windowPatterns = [/لا\s*$/, /لم\s*$/, /ليس\s*$/, /غير\s*$/];
  for (var j = 0; j < windowPatterns.length; j++) {
    if (windowPatterns[j].test(before)) return true;
  }
  return false;
}

/**
 * Détecte les exceptions du type "صحيح إلا أن فلاناً ضعيف"
 * → dégrade le verdict positif en Da'if
 */
function hasException(normalizedText) {
  return /(صحيح|حسن)\s+الا\s+ان/.test(normalizedText);
}

// ═══════════════════════════════════════════════════════════════
// BLOC 3 — DICTIONNAIRE EXHAUSTIF MUTAQADDIMŪN + DORAR.NET
// Synthèse : Claude (structure) + DeepSeek (patterns) + Grok (termes)
// Hiérarchie : MAWDU > MUNKAR > GHARIB > DAIF > HASAN > SAHIH
// ═══════════════════════════════════════════════════════════════

var HADITH_GRADES = {

  // ─────────────────────────────────────────────────────────────
  // NIVEAU 1 — MAWDU' — Forgé / Inventé
  // ─────────────────────────────────────────────────────────────
  MAWDU: {
    level: 1,
    labelAr: 'موضوع',
    labelFr: "Forgé / Inventé",
    labelIso: "Mawḍūʿ",
    color: '#4a148c',
    icon: '🟣',
    requiresReview: false,
    terms: [
      'موضوع', 'مكذوب', 'كذب', 'هذا كذب', 'باطل', 'باطل لا اصل له',
      'لا اصل له', 'لا يعرف له اصل', 'موضوع مكذوب', 'اختلقه',
      'افتراء', 'كذاب', 'كذاب خبيث', 'دجال', 'يضع الحديث',
      'يكذب', 'متروك الرواية', 'موضوع على رسول الله',
      'MAWDU', 'BATIL', 'MAKDHUB', 'LA_ASLA_LAHU'
    ]
  },

  // ─────────────────────────────────────────────────────────────
  // NIVEAU 2 — MUNKAR — Répréhensible / Sévèrement rejeté
  // ─────────────────────────────────────────────────────────────
  MUNKAR: {
    level: 2,
    labelAr: 'منكر',
    labelFr: "Répréhensible",
    labelIso: "Munkar",
    color: '#b71c1c',
    icon: '🔴',
    requiresReview: false,
    terms: [
      'منكر', 'منكر الحديث', 'منكر جدا', 'منكر بجمله',
      'يروي المناكير', 'فيه نكاره', 'هذا منكر',
      'ليس بشيء', 'لا شيء', 'لا يحتج به',
      'متروك', 'متروك الحديث',
      'مطروح',                    // Matruh — rejeté totalement
      'ساقط',                     // Saqit — tombé (DeepSeek)
      'شاذ',                      // Shadhdh — contredit thiqât
      'مخالف للثقات', 'مخالفه الثقات',
      'تفرد به ضعيف',
      'ضعف جدا',
      'MUNKAR', 'MATRUK', 'MATRUH', 'LAYSA_BI_SHAY', 'SHADHDH', 'SAQIT'
    ]
  },

  // ─────────────────────────────────────────────────────────────
  // NIVEAU 2.5 — GHARIB — Rare / Isolé
  // Narré par un seul râwî — pas automatiquement faible
  // ─────────────────────────────────────────────────────────────
  GHARIB: {
    level: 2.5,
    labelAr: 'غريب',
    labelFr: "Rare / Isolé",
    labelIso: "Gharīb",
    color: '#ff9800',
    icon: '🟠',
    requiresReview: true,   // Requiert examen — pas automatiquement faible
    terms: [
      'غريب', 'غريب جدا', 'فرد', 'فرد غريب', 'تفرد به',
      'لا يعرف الا من هذا الوجه',
      'لا نعرفه الا من حديث',
      'غريب من هذا الوجه',
      'GHARIB', 'FARD'
    ]
  },

  // ─────────────────────────────────────────────────────────────
  // NIVEAU 3 — DA'IF — Faible
  // ─────────────────────────────────────────────────────────────
  DAIF: {
    level: 3,
    labelAr: 'ضعيف',
    labelFr: "Faible",
    labelIso: "Ḍaʿīf",
    color: '#e65100',
    icon: '🟤',
    requiresReview: false,
    terms: [
      'ضعيف', 'ضعيف الاسناد', 'اسناده ضعيف',
      'ضعيف جدا',
      'فيه ضعف', 'فيه مقال', 'فيه نظر',
      'في اسناده ضعف',
      'غير ثابت',               // Terme composé — traité avant négation sur ثابت
      'لا يصح',
      'لا يثبت',
      'لم يثبت',
      'لم يصح',
      'واه', 'واه بمره', 'واه جدا',
      'ليس بذاك القوي',         // Laysa bi-dhak al-qawi (DeepSeek)
      'مجهول', 'مجهول الحال', 'مستور', 'مبهم',
      'ضعفه',
      'لين', 'لين الحديث',
      'تكلم فيه', 'فيه كلام',
      'مدلس', 'التدليس', 'تدليس',
      'مرسل', 'منقطع', 'معضل', 'معلق',
      'مضطرب', 'مقلوب',
      'معلول', 'معل',
      'خطا', 'وهم',
      'فيه فلان ضعيف',
      'في اسناده وهو ضعيف',
      'DAIF', 'DAIF_JIDDAN', 'MURSAL', 'MUNQATI',
      'MUDALLAS', 'MUDTARIB', 'MAQLUB', 'MUALLAL'
    ]
  },

  // ─────────────────────────────────────────────────────────────
  // NIVEAU 4 — HASAN — Bon
  // ─────────────────────────────────────────────────────────────
  HASAN: {
    level: 4,
    labelAr: 'حسن',
    labelFr: "Bon",
    labelIso: "Ḥasan",
    color: '#558b2f',
    icon: '🟢',
    requiresReview: false,
    terms: [
      // Termes composés en premier (priorité de matching)
      'حسن صحيح',               // Terme Tirmidhî — niveau élevé
      'حسن لغيره',
      'حسن الاسناد',
      'اسناده حسن',
      'حسن غريب',               // Composé : matche avant غريب seul
      'حسن غريب من هذا الوجه',
      'حسن غريب بغيره',
      'حسن',
      'لا باس به',               // Terme Mutaqaddimūn = Hasan
      'لا باس باسناده',
      'صالح',                    // Al-Bukhari : Hasan li-ghayrihi
      'صالح الحديث',
      'صالح الاسناد',
      'جيد',                     // Al-Daraqutni : synonyme Hasan
      'جيد الاسناد',
      'قوي', 'قوي الاسناد',
      'صدوق',                    // Râwî véridique → Hasan
      'محله الصدق',
      'شيخ',                     // Terme Mutaqaddimūn = acceptable
      'يكتب حديثه',
      'سكت عنه',
      'مقبول',                   // Maqbul (DeepSeek)
      'HASAN', 'LA_BAS', 'SALIH', 'JAYYID', 'SADUQ', 'MAQBUL'
    ]
  },

  // ─────────────────────────────────────────────────────────────
  // NIVEAU 5 — SAHIH — Authentique
  // ─────────────────────────────────────────────────────────────
  SAHIH: {
    level: 5,
    labelAr: 'صحيح',
    labelFr: "Authentique",
    labelIso: "Ṣaḥīḥ",
    color: '#2e7d32',
    icon: '✅',
    requiresReview: false,
    terms: [
      // Composés en premier
      'صحيح على شرط الشيخين',
      'صحيح على شرط البخاري',
      'صحيح على شرط مسلم',
      'صحيح الاسناد',
      'صحيح لغيره',
      'اسناده صحيح لغيره',
      'اسناده صحيح',
      'رجاله رجال الصحيح',
      'رواية صحيحه',
      'صح عن النبي',
      'صح عن رسول الله',
      // Termes simples
      'صحيح',
      'ثابت',
      'محفوظ',
      'متفق عليه',
      'اخرجه الشيخان',
      'رجاله ثقات',
      '[صحيح]', '[ثابت]',
      'SAHIH', 'MUTTAFAQ', 'THABIT'
    ]
  },

  // ─────────────────────────────────────────────────────────────
  // NIVEAU 0 — INDÉTERMINÉ — Tawaqquf
  // JAMAIS Da'if — revue humaine obligatoire
  // ─────────────────────────────────────────────────────────────
  UNDETERMINED: {
    level: 0,
    labelAr: 'غير مصنف — يحتاج لمراجعة يدوية',
    labelFr: "Non classifié — Revue humaine requise",
    labelIso: "Ghayr muṣannaf",
    color: '#757575',
    icon: '⬜',
    requiresReview: true,
    explanation: 'امتثالاً لمنهج السلف في التوقف'
  }
};

// ═══════════════════════════════════════════════════════════════
// BLOC 4 — VALIDATION CONSTITUTION SALAFI
// Filtre : sectarisme, rationalisme moderne, termes interdits
// Source : DeepSeek (termes arabes) + Grok (termes français)
// ═══════════════════════════════════════════════════════════════

var FORBIDDEN_TERMS = [
  // Sectes et méthodes égarées
  'اخواني', 'صوفي', 'قطبي', 'سروري', 'تبليغي',
  'رافضي', 'اشعري', 'ماتريدي',
  // Rationalisme moderne
  'حداثي', 'عقلاني', 'تنويري',
  'قراءه معاصره', 'نقد تاريخي',
  // Termes français interdits (Grok)
  'rationaliste', 'moderne', 'ijtihad personnel',
];

function validateConstitution(verdictResult, rawText) {
  var normRaw = normalizeArabic(rawText || '');
  for (var i = 0; i < FORBIDDEN_TERMS.length; i++) {
    var t = normalizeArabic(FORBIDDEN_TERMS[i]);
    if (normRaw.indexOf(t) !== -1) {
      console.error('[CONSTITUTION] Terme sectaire/rationaliste détecté :', FORBIDDEN_TERMS[i]);
      return {
        grade: 'UNDETERMINED',
        level: 0,
        labelAr: 'REVUE_HUMAINE — Terme sectaire',
        labelFr: 'REVUE HUMAINE OBLIGATOIRE — Terme interdit',
        labelIso: 'Ghayr muṣannaf',
        color: '#000000',
        icon: '🚫',
        requiresReview: true,
        explanation: 'Le verdict contient une terminologie non conforme au Manhaj.'
      };
    }
  }
  return verdictResult;
}

// ═══════════════════════════════════════════════════════════════
// BLOC 5 — MOTEUR DE CLASSIFICATION PRINCIPAL
// Ordre scan : termes composés longs d'abord, puis simples
// ═══════════════════════════════════════════════════════════════

function classifyHadithGrade(rawText) {

  // ① Entrée vide
  if (!rawText || rawText.trim() === '') {
    console.warn('[AL MĪZĀN] Grade vide reçu → UNDETERMINED');
    return _buildResult('UNDETERMINED', null);
  }

  var normalized = normalizeArabic(rawText);

  // ② Détection de termes négatifs composés DIRECTS (avant scan général)
  //    Ces termes SONT eux-mêmes des négations — ne pas les soumettre à isNegated()
  var directNegativeTerms = [
    { term: 'غير ثابت', grade: 'DAIF' },
    { term: 'لا يصح', grade: 'DAIF' },
    { term: 'لا يثبت', grade: 'DAIF' },
    { term: 'لم يثبت', grade: 'DAIF' },
    { term: 'لم يصح', grade: 'DAIF' },
    { term: 'غير صحيح', grade: 'DAIF' },
    { term: 'لا اصل له', grade: 'MAWDU' },
    { term: 'لا يعرف له اصل', grade: 'MAWDU' },
  ];
  for (var d = 0; d < directNegativeTerms.length; d++) {
    var dnt = directNegativeTerms[d];
    if (normalized.indexOf(normalizeArabic(dnt.term)) !== -1) {
      return _buildResult(dnt.grade, dnt.term);
    }
  }

  // ③ Détection d'exception "صحيح إلا أن" → Da'if
  if (hasException(normalized)) {
    console.warn('[AL MĪZĀN] Exception détectée (إلا أن) — dégradation → DAIF');
    return _buildResult('DAIF', 'exception:الا ان');
  }

  // ④ Hiérarchie de scan : MAWDU en premier (le plus grave)
  //    HASAN avant GHARIB pour que "حسن غريب" → HASAN (pas GHARIB)
  var hierarchy = ['MAWDU', 'MUNKAR', 'DAIF', 'HASAN', 'GHARIB', 'SAHIH'];

  for (var i = 0; i < hierarchy.length; i++) {
    var key = hierarchy[i];
    var grade = HADITH_GRADES[key];
    var terms = grade.terms;

    // Trier les termes par longueur décroissante (composés d'abord)
    var sortedTerms = terms.slice().sort(function(a, b) {
      return b.length - a.length;
    });

    for (var j = 0; j < sortedTerms.length; j++) {
      var termNorm = normalizeArabic(sortedTerms[j]);
      var idx = normalized.indexOf(termNorm);

      if (idx !== -1) {
        // ⑤ Vérification négation — sauf pour MAWDU/MUNKAR (toujours négatifs)
        if (key !== 'MAWDU' && key !== 'MUNKAR') {
          if (isNegated(normalized, idx)) {
            console.info('[AL MĪZĀN] "' + sortedTerms[j] + '" — NÉGATION détectée → ignoré');
            continue;
          }
        }
        return _buildResult(key, sortedTerms[j]);
      }
    }
  }

  // ⑥ Aucun terme reconnu → Tawaqquf — JAMAIS Da'if
  console.error('[AMĀNAH] Terme inconnu, retour UNDETERMINED :', rawText);
  return _buildResult('UNDETERMINED', null);
}

// ═══════════════════════════════════════════════════════════════
// BLOC 6 — FONCTION PRINCIPALE (avec Constitution)
// Point d'entrée unique pour l'application
// ═══════════════════════════════════════════════════════════════

function getHadithGrade(rawVerdict) {
  var classified = classifyHadithGrade(rawVerdict);
  return validateConstitution(classified, rawVerdict);
}

// ═══════════════════════════════════════════════════════════════
// BLOC 7 — UTILITAIRES
// ═══════════════════════════════════════════════════════════════

function _buildResult(gradeKey, matchedTerm) {
  var g = HADITH_GRADES[gradeKey];
  return {
    grade:          gradeKey,
    labelAr:        g.labelAr,
    labelFr:        g.labelFr,
    labelIso:       g.labelIso,
    level:          g.level,
    color:          g.color,
    icon:           g.icon,
    requiresReview: g.requiresReview || false,
    matchedTerm:    matchedTerm || null
  };
}

function renderGradeBadge(r) {
  return (
    '<span class="mizan-grade-badge" ' +
    'style="background:' + r.color + ';color:#fff;' +
    'padding:3px 10px;border-radius:4px;font-family:Amiri,serif;font-size:0.95em;">' +
    r.icon + ' ' + r.labelAr + ' — ' + r.labelFr +
    (r.requiresReview ? ' ⚠️' : '') +
    '</span>'
  );
}

// ═══════════════════════════════════════════════════════════════
// EXPORT
// ═══════════════════════════════════════════════════════════════

if (typeof module !== 'undefined') {
  module.exports = {
    HADITH_GRADES,
    normalizeArabic,
    isNegated,
    hasException,
    classifyHadithGrade,
    getHadithGrade,
    validateConstitution,
    renderGradeBadge
  };
}
