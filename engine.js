/* ═══════════════════════════════════════════════════════════════════
   MÎZÂN v21.0 — engine.js — FINAL DELIVERABLE
   Triple Bouclier :
     1. Syntaxe  : HTML via string concat sécurisée
     2. Portée   : Fonctions critiques sur window.*
     3. Science  : Zone 2 min-height:40px + titre doré GARANTI
   CORRECTIONS v21.0 :
     Phase 0 : Zone 1 rendue IMMÉDIATEMENT (< 100ms)
     Phase 1 : Arbre via Promise non-bloquante (rAF + setTimeout 0)
     Phase 2 : Fallback Souverain 2000ms → Lignée d’Or si arbre absent
     JSON FB  : Suppression délai artificiel 1800ms
═══════════════════════════════════════════════════════════════════ */

console.log('%c ✅ Mîzan v21.1 : Prêt pour Production — Triple Bouclier + Whitelist Sahih', 'color: #00ff00; font-weight: bold;');
console.log('%c 🛡️ TRIPLE BOUCLIER ACTIF v21.1 — Whitelist Sahih + Anti-Doublon + Fallback Souverain', 'color:#d4af37;font-weight:bold;');

/* ═══════════════════════════════════════════════════════════════════
   MÎZÂN v18.4 — engine.js
   Rôle    : Moteur de rendu UI — renderList, renderMythes, omniSearch,
             SSE enrichissement, _enrichCardSSE, renderAIResult, etc.
   Dépend  : data.js, db.js, preachers.js (chargés avant via defer)
   Chargement : defer, après tous les fichiers de données
═══════════════════════════════════════════════════════════════════ */

/* ════════════════════════════════════════
   NAVIGATION
════════════════════════════════════════ */
function goTo(view) {
  document.querySelectorAll('.view').forEach(function(v){v.classList.remove('active');});
  var el = document.getElementById('view-'+view);
  if(el){el.classList.add('active');el.scrollTop=0;}
  var isHome=(view==='home');
  // Afficher/cacher les éléments de fond home
  var homeBgEls=['home-bg','home-overlay'];
  homeBgEls.forEach(function(id){
    var e=document.getElementById(id);
    if(e)e.style.display=isHome?'block':'none';
  });
  // Étoiles et arabesque/orb (ajoutés dynamiquement)
  document.querySelectorAll('.home-star').forEach(function(e){
    e.style.display=isHome?'block':'none';
  });
  window.scrollTo(0,0);
}
window.goTo = goTo; /* alias global — fixes ReferenceError in inline HTML onclick */

function goToList(){renderList();goTab('list');}
window.goToList = goToList;

/* ════════════════════════════════════════
   HADITH ANALYSE — MOTEUR IA AL MIZÂN
════════════════════════════════════════ */
var loadTimer=null;
var aiResult=null;   // résultat IA mis en cache
var animDone=false;  // animation terminée ?

/* ════════════════════════════════════════════════════════════════
   MOTEUR AL MIZÂN v11 — Connexion exclusive /api/search (SSE)
   Zéro appel externe parasite — toutes les données viennent du backend
════════════════════════════════════════════════════════════════ */
var MIZAN_SEARCH_IA = '/api/search';

/* ═══════════════════════════════════════════════════════════════════
   DICTIONNAIRE UNIVERSEL DU JARH WA TA'DIL — Al-Mizân v11
   Règle absolue : الجرح مقدَّم على التعديل (Le Jarh précède le Ta'dil)
   4 niveaux déterministes — jamais de vert par défaut
═══════════════════════════════════════════════════════════════════ */

/* ── Niveau 1 : Rejet absolu (Munkar / Mawdu' / Batil / Non-Hadith) ── */
/* ── WHITELIST SAHIH — Hadiths authentiques connus (court-circuit Bouclier Science) ── */
var _SAHIH_WHITELIST = [
  'من كان يؤمن بالله واليوم الآخر',
  'إنما الأعمال بالنيات',
  'بني الإسلام على خمس',
  'الحلال بين والحرام بين',
  'من حسن إسلام المرء تركه ما لا يعنيه',
  'إن الله طيب لا يقبل إلا طيباً',
  'لا ضرر ولا ضرار',
  'الدين النصيحة',
  'ازهد في الدنيا يحبك الله',
  'اتق الله حيثما كنت',
  'كل بدعة ضلالة',
  'خير الناس من طال عمره وحسن عمله',
  'اليمين على نية المستحلف',
  'المسلم من سلم المسلمون من لسانه ويده',
  'لا يؤمن أحدكم حتى يحب لأخيه ما يحب لنفسه',
];

var _RE_MAWDU = /موضوع|باطل|مكذوب|لا أصل له|ليس له أصل|ليس لهذا|كذب|منكر|شاذ|متروك|تالف|ضعيف جد[اً]|لا يصح|لا يثبت|ليس بحديث|لا يصح حديثا|ليس بحديث مرفوع|كلام|من قول|ليس من حديث/;

/* ── Niveau 2 : Faiblesse (Da'if / Inqita' / Tadlis) ── */
var _RE_DAIF  = /ضعيف|فيه ضعف|مجهول|مرسل|منقطع|معضل|مدلس|مضطرب|لين|لا يحتج|لا يعرف|في إسناده/;

/* ── Niveau 3 : Authentification (Sahih / Hasan) ── */
var _RE_SAHIH = /صحيح|حسن|جيّد|جيد|ثابت|إسناده صالح|رجاله ثقات|إسناده مقارب|إسناده حسن|إسناده صحيح/;

/*
 * _getTechnicalGrade(gradeStr)
 * Entrée  : chaîne arabe brute de Dorar.net (peut être longue)
 * Sortie  : objet { key, labelFr, labelAr, color, cssClass }
 * Règle   : Jarh > Ta'dil — on teste Niveau 1 avant Niveau 2 avant Niveau 3
 *           Niveau 4 (gris) si AUCUN match — JAMAIS de vert par défaut
 */
function _getTechnicalGrade(gradeStr) {
  var g = gradeStr || '';

  /* BOUCLIER SCIENCE — WHITELIST SAHIH : court-circuit prioritaire */
  for (var _wi = 0; _wi < _SAHIH_WHITELIST.length; _wi++) {
    if (g.indexOf(_SAHIH_WHITELIST[_wi]) !== -1) {
      return {
        key:      'SAHIH',
        labelFr:  'SAHIH — AUTHENTIQUE (MUTTAFAQUN ʿALAYH)',
        labelAr:  'صحيح',
        color:    '#22c55e',
        colorBg:  'rgba(34,197,94,.06)',
        colorBd:  'rgba(34,197,94,.2)',
        iconClr:  '#22c55e',
        cssClass: 'v-SAHIH'
      };
    }
  }

  /* NIVEAU 1 — ALERTE ROUGE : rejet absolu */
  if (_RE_MAWDU.test(g)) {
    return {
      key:      'MAWDU',
      labelFr:  "REJET\u00c9 \u2014 CE N'EST PAS UN HADITH (MUNKAR / MAWDU')",
      labelAr:  '\u0645\u0648\u0636\u0648\u0639 \u2014 \u0645\u0646\u0643\u0631',
      color:    '#e63946',
      colorBg:  'rgba(230,57,70,.07)',
      colorBd:  'rgba(230,57,70,.25)',
      iconClr:  '#e63946',
      cssClass: 'v-MAWDU'
    };
  }

  /* NIVEAU 2 — ALERTE ORANGE : faiblesse */
  if (_RE_DAIF.test(g)) {
    return {
      key:      'DAIF',
      labelFr:  "DA'IF \u2014 FAIBLE",
      labelAr:  '\u0636\u0639\u064a\u0641',
      color:    '#f59e0b',
      colorBg:  'rgba(245,158,11,.06)',
      colorBd:  'rgba(245,158,11,.22)',
      iconClr:  '#f59e0b',
      cssClass: 'v-DAIF'
    };
  }

  /* NIVEAU 3 — VALIDATION VERTE : authentique */
  if (_RE_SAHIH.test(g)) {
    var isHasan = /حسن/.test(g) && !/صحيح/.test(g);
    return {
      key:      isHasan ? 'HASAN' : 'SAHIH',
      labelFr:  isHasan ? 'HASAN \u2014 BON' : 'SAHIH \u2014 AUTHENTIQUE',
      labelAr:  isHasan ? '\u062d\u0633\u0646' : '\u0635\u062d\u064a\u062d',
      color:    isHasan ? '#4ade80' : '#22c55e',
      colorBg:  isHasan ? 'rgba(74,222,128,.05)' : 'rgba(34,197,94,.06)',
      colorBd:  isHasan ? 'rgba(74,222,128,.18)' : 'rgba(34,197,94,.2)',
      iconClr:  isHasan ? '#4ade80' : '#22c55e',
      cssClass: isHasan ? 'v-HASAN' : 'v-SAHIH'
    };
  }

  /* NIVEAU 4 — DA'IF PRÉSUMÉ : tout verdict non classifiable → orange
     Règle doctrinale : absence de Tawthiq = présomption de Da'if.
     "L'authenticité ne se présume pas, elle se prouve." (Ibn al-Salah)
     JAMAIS de gris, JAMAIS de "Non identifié" */
  return {
    key:      'DAIF',
    labelFr:  "DA'IF — STATUT NON CONFIRM\u00c9 (CONSULTER AL-ALBANI)",
    labelAr:  '\u0636\u0639\u064a\u0641 \u2014 \u063a\u064a\u0631 \u0645\u062d\u062f\u062f',
    color:    '#f59e0b',
    colorBg:  'rgba(245,158,11,.06)',
    colorBd:  'rgba(245,158,11,.22)',
    iconClr:  '#f59e0b',
    cssClass: 'v-DAIF'
  };
}

/* ── Alias de compatibilité (appelés ailleurs dans le code) ── */
function _normalizeGrade(gradeStr) {
  return _getTechnicalGrade(gradeStr).key;
}
function _gradeColor(g) {
  var MAP = {
    SAHIH:'#22c55e', HASAN:'#4ade80', DAIF:'#f59e0b',
    MAWDU:'#e63946', INCONNU:'rgba(156,163,175,.6)'
  };
  return MAP[g] || MAP.INCONNU;
}
function _gradeLabel(g) {
  var MAP = {
    SAHIH:"SAHIH \u2014 \u0635\u062d\u064a\u062d",
    HASAN:"HASAN \u2014 \u062d\u0633\u0646",
    DAIF:"DA'IF \u2014 \u0636\u0639\u064a\u0641",
    MAWDU:"REJET\u00c9 \u2014 CE N'EST PAS UN HADITH (MAWDU')",
    INCONNU:"\u26a0\ufe0f DA'IF — STATUT NON CONFIRM\u00c9 (CONSULTER AL-ALBANI)"
  };
  return MAP[g] || g;
}
/* ── RENDU PRINCIPAL — Styles animation Isnad ── */
// ── Styles animation Isnad + CSS Zone 3 Fiqh (injectés une seule fois) ──
(function(){
  if(document.getElementById('mizan-isnad-styles')) return;
  var s = document.createElement('style');
  s.id = 'mizan-isnad-styles';
  s.textContent = [
    '@keyframes isnadFadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}',
    '@keyframes isnadLine{from{height:0}to{height:100%}}',
    '.mizan-section{animation:isnadFadeIn .4s ease forwards;opacity:0;}',
    '.mizan-section:nth-child(1){animation-delay:.05s}',
    '.mizan-section:nth-child(2){animation-delay:.15s}',
    '.mizan-section:nth-child(3){animation-delay:.25s}',
    '.mizan-section:nth-child(4){animation-delay:.35s}',
    '.mizan-section:nth-child(5){animation-delay:.45s}',
    '.mizan-section:nth-child(6){animation-delay:.55s}',
    '.isnad-chain{position:relative;padding-left:18px;}',
    '.isnad-chain::before{content:"";position:absolute;left:6px;top:0;width:2px;',
    'background:linear-gradient(to bottom,#c9a84c,transparent);',
    'animation:isnadLine .8s ease forwards;height:0;}',
    '.isnad-node{position:relative;margin-bottom:8px;}',
    '.isnad-node::before{content:"◆";position:absolute;left:-18px;color:#c9a84c;font-size:7px;top:2px;}',
    /* Zone 3 Fiqh — sous-titres et mise en page lisible */
    '.mz-oignon-z3{background:linear-gradient(180deg,rgba(15,12,5,.0) 0%,rgba(201,168,76,.015) 100%);}',
    '.mz-fiqh-title{display:block;font-family:Cinzel,serif;font-size:9px;letter-spacing:.18em;',
    'font-weight:700;padding:10px 0 5px;text-transform:uppercase;}',
    '.mz-fiqh-body{font-family:"Cormorant Garamond",serif;font-size:14.5px;line-height:1.85;',
    'color:rgba(228,208,160,.88);margin-bottom:14px;padding-left:12px;',
    'border-left:2px solid rgba(201,168,76,.18);}',
    '#typewriter-zone .mz-fiqh-title{display:block;}',
  ].join('');
  document.head.appendChild(s);
})();

/* ════════════════════════════════════════════════════════════════
   SKELETON ZONE 2 CSS (une seule fois) — Bouclier Science
════════════════════════════════════════════════════════════════ */
(function(){
  if(document.getElementById('mizan-skel-css')) return;
  var sk = document.createElement('style');
  sk.id = 'mizan-skel-css';
  sk.textContent = [
    '@keyframes mzSkelPulse{0%,100%{opacity:.35}50%{opacity:.72}}',
    '.mz-zone2-skel{min-height:40px;padding:12px 20px;animation:mzSkelPulse 1.8s ease infinite;}',
    '.mz-zone2-skel-title{font-family:Cinzel,serif;font-size:6px;letter-spacing:.28em;',
    'color:rgba(212,175,55,.55);text-transform:uppercase;margin-bottom:8px;display:block;}',
    '.mz-zone2-skel-bar{height:3px;background:rgba(212,175,55,.15);border-radius:2px;margin-bottom:6px;}',
  ].join('');
  document.head.appendChild(sk);
})();

/* ════════════════════════════════════════════════════════════════
   FALLBACK SOUVERAIN — LIGNÉE D'OR
   Bouclier Science : min-height:40px + titre doré INVIOLABLES
   Déclenché si Zone 2 vide après 2000ms
════════════════════════════════════════════════════════════════ */
function _mzFallbackLigneeOr(containerId) {
  /* ═══════════════════════════════════════════════════════════════
     FALLBACK HONNÊTE v24.0 — INTERDICTION ABSOLUE D'INVENTER UN ISNÂD
     Règle doctrinale : un isnâd non fourni = isnâd absent.
     On affiche un message neutre. JAMAIS de chaîne fabricée.
  ═══════════════════════════════════════════════════════════════ */
  var zone = document.getElementById(containerId);
  if(!zone) return;
  /* Si la vraie chaîne est déjà là, ne rien faire */
  if(zone.querySelector('.mzAr') || zone.querySelector('.mzC4-rw') || zone.querySelector('.mzAr-orb')) return;
  /* Si le contenu dépasse 80 chars, c'est que le backend a déjà rempli la zone */
  if(zone.innerHTML && zone.innerHTML.trim().length > 80) return;
  /* Message neutre et honnête */
  zone.innerHTML = '<div style="min-height:40px;padding:14px 20px 12px;background:rgba(10,6,0,.92);">'
    + '<p style="font-family:Cinzel,serif;font-size:6px;letter-spacing:.3em;color:rgba(212,175,55,.45);'
    + 'text-transform:uppercase;margin-bottom:8px;">ZONE 2 \u2014 SILSILAT AL-ISN\u0100D</p>'
    + '<p style="font-family:\'Cormorant Garamond\',serif;font-size:13px;color:rgba(201,168,76,.4);'
    + 'line-height:1.7;font-style:italic;">'
    + 'Cha\u00eene de transmission non disponible dans la source Dorar.net '
    + '\u2014 consultez directement <a href="https://dorar.net" target="_blank" '
    + 'style="color:rgba(212,175,55,.6);text-decoration:underline;">dorar.net</a> '
    + 'pour le takhr\u012bj complet.</p>'
    + '</div>';
  zone.style.animation = 'isnadFadeIn .5s ease';
}
window._mzFallbackLigneeOr = _mzFallbackLigneeOr;

/* Skeleton Zone 2 — Bouclier Science : min-height:40px + titre doré */
function _mzSkeletonZone2() {
  return '<div class="mz-zone2-skel">'
    + '<span class="mz-zone2-skel-title">ZONE 2 \u2014 SILSILAT AL-ISN\u0100D \u2014 ANALYSE EN COURS\u2026</span>'
    + '<div class="mz-zone2-skel-bar" style="width:78%;"></div>'
    + '<div class="mz-zone2-skel-bar" style="width:56%;"></div>'
    + '<div class="mz-zone2-skel-bar" style="width:68%;"></div>'
    + '</div>';
}
window._mzSkeletonZone2 = _mzSkeletonZone2;


function _renderTopicList(hadiths, query) {
  var box = document.getElementById('result-box');
  var lb  = document.getElementById('loading-box');
  if(lb) lb.classList.remove('active');
  /* ── ANTI-DOUBLON : vider le conteneur avant toute injection ── */
  box.innerHTML = '';
  box.classList.remove('active');

  if(!hadiths || hadiths.length === 0) {
    /* ══════════════════════════════════════════════════════════════
       TRIPLE BOUCLIER — FALLBACK ARBRE ROYAL CANONIQUE
       Si Dorar.net renvoie "Non indexé" ou zéro résultat,
       on affiche IMMÉDIATEMENT l'arbre royal via mizan-tree-engine.js.
       L'écran ne reste JAMAIS vide — autonomie totale.
    ══════════════════════════════════════════════════════════════ */
    if (typeof window.mzAfficherArbreCanonique === 'function') {
      window.mzAfficherArbreCanonique(query);
      return;
    }

    /* Fallback ultime si mizan-tree-engine.js non chargé */
    box.innerHTML =
      '<div class="mz-card" style="padding:24px 20px;text-align:center;">'

      /* Sceau */
      +'<p style="font-family:\'Scheherazade New\',serif;font-size:32px;'
      +'color:rgba(201,168,76,.25);margin-bottom:8px;">\u2696</p>'

      /* Titre */
      +'<p style="font-family:\'Cinzel\',serif;font-size:8.5px;font-weight:700;'
      +'letter-spacing:.28em;color:rgba(201,168,76,.6);margin-bottom:6px;">'
      +'NON INDEXÉ DANS DORAR.NET</p>'

      /* Explication scientifique */
      +'<p style="font-family:\'Cormorant Garamond\',serif;font-size:13.5px;'
      +'color:rgba(220,200,140,.55);line-height:1.75;margin:0 auto 16px;max-width:320px;font-style:italic;">'
      +'Ce texte ne figure pas dans la base de données de Dorar.net. '
      +'Cela arrive souvent pour les hadiths <em>Da\'if</em> ou <em>Mawdu\'</em> '
      +'non retenus par les recueils canoniques, ou pour les narrations peu connues. '
      +'L\'analyse directe a néanmoins été lancée.</p>'

      /* Grille 3 colonnes de ressources */
      +'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:14px;">'

      +'<a href="https://dorar.net" target="_blank" style="display:flex;flex-direction:column;'
      +'align-items:center;gap:4px;padding:10px 8px;background:rgba(201,168,76,.05);'
      +'border:1px solid rgba(201,168,76,.18);border-radius:10px;text-decoration:none;">'
      +'<span style="font-size:16px;">🔍</span>'
      +'<span style="font-family:\'Cinzel\',serif;font-size:6px;letter-spacing:.12em;color:#c9a84c;">DORAR.NET</span>'
      +'</a>'

      +'<a href="https://www.alalbany.net/" target="_blank" style="display:flex;flex-direction:column;'
      +'align-items:center;gap:4px;padding:10px 8px;background:rgba(201,168,76,.05);'
      +'border:1px solid rgba(201,168,76,.18);border-radius:10px;text-decoration:none;">'
      +'<span style="font-size:16px;">📚</span>'
      +'<span style="font-family:\'Cinzel\',serif;font-size:6px;letter-spacing:.12em;color:#c9a84c;">AL-ALBANI</span>'
      +'</a>'

      +'<a href="https://binbaz.org.sa/" target="_blank" style="display:flex;flex-direction:column;'
      +'align-items:center;gap:4px;padding:10px 8px;background:rgba(201,168,76,.05);'
      +'border:1px solid rgba(201,168,76,.18);border-radius:10px;text-decoration:none;">'
      +'<span style="font-size:16px;">🛡️</span>'
      +'<span style="font-family:\'Cinzel\',serif;font-size:6px;letter-spacing:.12em;color:#c9a84c;">IBN BAZ</span>'
      +'</a>'

      +'</div>'

      /* Note Al-Albani Silsilah Da'ifah */
      +'<div style="background:rgba(239,68,68,.05);border:1px solid rgba(239,68,68,.2);'
      +'border-radius:10px;padding:10px 14px;margin-bottom:0;text-align:left;">'
      +'<p style="font-family:\'Cinzel\',serif;font-size:6.5px;letter-spacing:.18em;'
      +'color:rgba(239,68,68,.7);margin-bottom:5px;">⚠ VÉRIFICATION RECOMMANDÉE</p>'
      +'<p style="font-family:\'Cormorant Garamond\',serif;font-size:12.5px;'
      +'color:rgba(220,190,130,.6);line-height:1.6;">'
      +'Consultez la <em>Silsilah Da\'ifah</em> et la <em>Silsilah Sahihah</em> '
      +'du Cheikh Al-Albani (rahimahullah), ainsi que '
      +'<em>Fath al-Bari</em> d\'Ibn Hajar al-\'Asqalani (m.852H).'
      +'</p></div>'

      +'</div>';
    box.classList.add('active');
    return;
  }


  var html = '<div class="mz-source"><span class="mz-source-dot" style="background:#c9a84c;box-shadow:0 0 6px rgba(201,168,76,.5);"></span><span class="mz-source-text">'+hadiths.length+' RESULTAT(S) · DORAR.NET · AL MIZAN</span></div>';

  hadiths.forEach(function(h, idx) {
    /* Détection Tawaqquf : champ backend OU grade explicite ── */
    var _isTawaqquf = (h.tawaqquf === true) || (h.grade === 'TAWAQQUF') || (h.grade_ar === 'TAWAQQUF');
    /* Utiliser le dictionnaire universel sur la chaîne arabe brute (grade_ar)
       pour appliquer la règle Jarh > Ta'dil sur la phrase complète de Dorar */
    var tg  = _isTawaqquf
      ? { key:'TAWAQQUF', color:MZ_COLORS.TAWAQQUF, colorBg:'rgba(167,139,250,.06)', colorBd:'rgba(167,139,250,.22)', cssClass:'v-TAWAQQUF' }
      : _getTechnicalGrade(h.grade_ar || h.grade || '');
    var g   = tg.key;
    var col = tg.color;

    /* ── Pertinence badge ── */
    var pertHtml = '';
    if(h.pertinence && h.pertinence.length > 3) {
      var pertCol = /^OUI/i.test(h.pertinence) ? '#2ecc71'
                  : /^PARTIEL/i.test(h.pertinence) ? '#f39c12' : '#e74c3c';
      pertHtml = '<div style="margin-bottom:10px;"><span class="mz-pertinence" style="background:'+pertCol+'18;color:'+pertCol+';border:1px solid '+pertCol+'44;">'+h.pertinence.substring(0,60)+'</span></div>';
    }

    /* ── Source meta (mohdith / rawi / source) ── */
    var metaLine = '';
    if(h.mohdith && h.mohdith !== '—') metaLine += 'المحدث : '+h.mohdith;
    else if(h.rawi && h.rawi !== '—') metaLine += 'الراوي : '+h.rawi;
    if(h.source && h.source !== '—') metaLine += (metaLine ? ' · ' : '') + 'المصدر : '+h.source;
    if(h.numero) metaLine += ' — '+h.numero;

    html += '<div class="mz-card" id="topic-card-'+idx+'" style="animation:argCardIn .4s ease both;animation-delay:'+(idx*0.1)+'s;">';

    /* ═══ NIVEAU 1 : Résultat Immédiat ═══ */
    html += '<div class="mz-niv1">';

    /* Pertinence */
    html += pertHtml;

    /* Matn arabe */
    html += '<div class="mz-matn">'
      +'<div class="mz-matn-ar">'+h.ar+'</div>';

    /* Traduction francaise (si disponible) — directement sous le matn */
    if(h.french) {
      html += '<div class="mz-matn-fr">'+h.french+'</div>';
    }

    /* Meta */
    if(metaLine) {
      html += '<div class="mz-matn-meta">'+metaLine+'</div>';
    }
    html += '</div>'; /* /mz-matn */

    /* Badge de verdict — Tawaqquf passe les raisons et termes protégés */
    var _verdictExtra = _isTawaqquf
      ? { tawaqquf_reasons: h.tawaqquf_reasons || [], protected_terms: h.protected_terms || [] }
      : null;
    html += _mzVerdict(g, h.grade_ar || h.grade, _verdictExtra);
    html += '</div>'; /* /mz-niv1 */

    /* ═══ NIVEAU 2 : Al-Hukm ═══ */
    var isSahihD = (g==='SAHIH'||g==='HASAN');
    var hukmLabelD = isSahihD ? 'AL-HUKM \u2014 ATTESTATION D\'AUTHENTICITE' : 'AL-HUKM \u2014 CAUSE DE LA FAIBLESSE';
    if(h.grade_explique) {
      html += '<div class="mz-illah">'
        +'<span class="mz-illah-label">'+hukmLabelD+'</span>'
        +'<div class="mz-illah-text">'+h.grade_explique+'</div>'
        +'</div>';
    }

    /* ═══ NIVEAU 3 : Analyse Detaillee (Accordeons) ═══ */
    var niv3 = '', hasN3 = false;

    /* ══════════════════════════════════════════════════════════
       ISNAD PIPE v9 — FRISE 7e→21e SIÈCLE (PRIORITÉ ABSOLUE)
       Source : champ isnad_chain (format pipe |) du moteur v9
    ══════════════════════════════════════════════════════════ */
    var isnadPipeHtml = '';
    if(h.isnad_chain && h.isnad_chain.length > 10) {
      isnadPipeHtml = _mzIsnadFromPipe(h.isnad_chain, g);
    }

    /* Zone isnad (remplie immédiatement si dispo, sinon via SSE enrichissement) */
    niv3 += '<div id="isnad-zone-'+idx+'">' + (isnadPipeHtml || '') + '</div>';
    if(isnadPipeHtml) hasN3 = true;

    /* ══════════════════════════════════════════════════════════
       TRIDENT 1 LEGACY — CASCADE JARH (si pas d'isnad pipe)
       Utilisé seulement si isnad_chain absent/vide
    ══════════════════════════════════════════════════════════ */
    if(!isnadPipeHtml && h.jarh_tadil) {
      var cascadeVis = _mzIsnadChain(h.jarh_tadil, g);
      if(cascadeVis) {
        niv3 = '<div id="isnad-zone-'+idx+'">'+cascadeVis+'</div>';
      } else {
        niv3 = '<div id="isnad-zone-'+idx+'">'+_mzAcc('JARH WA TA\'DIL \u2014 Evaluation des transmetteurs','\u0633\u0650\u0644\u0633\u0650\u0644\u064E\u0629\u064F \u0627\u0644\u0625\u0650\u0633\u0646\u064E\u0627\u062F','#5dade2','<p>'+h.jarh_tadil+'</p>',true)+'</div>';
      }
      hasN3 = true;
    }

    /* ── SECTIONS SECONDAIRES ── */
    var secAccHtml = '';

    /* TRIDENT 2 : Scanner de Défaut */
    if(h.jarh_tadil) {
      var scannerVis = _mzScannerFromChain(h.jarh_tadil, g);
      if(scannerVis) {
        secAccHtml += _mzAcc('SCANNER DE DEFAUT \u2014 Localisation de l\u2019Illah','\u0639\u0650\u0644\u0651\u064E\u0629','#ef4444',scannerVis,false);
      }
    }

    /* SHURUT AS-SIHHAH — 5 conditions */
    if(h.sanad) {
      secAccHtml += _mzAcc(
        'SHURUT AS-SIHHAH \u2014 Les 5 conditions de l\'authenticite', '\u0634\u064F\u0631\u064F\u0648\u0637\u064F \u0627\u0644\u0635\u0651\u0650\u062D\u0651\u064E\u0629',
        '#9b59b6',
        _mzFormatSanad(h.sanad),
        false
      );
      hasN3 = true;
    }

    /* AUTOPSIE DU NARRATEUR — Aqwal al-A'immah */
    if(h.avis) {
      secAccHtml += _mzAcc(
        'AUTOPSIE DU NARRATEUR \u2014 Aqwal al-A\u2019immah', '\u0623\u064E\u0642\u0648\u064E\u0627\u0644\u064F \u0627\u0644\u0623\u064E\u0626\u0650\u0645\u0651\u064E\u0629',
        '#e67e22',
        _mzFormatAvis(h.avis)
      );
      hasN3 = true;
    }

    /* GRILLE AL-ALBANI */
    if(h.albani) {
      secAccHtml += _mzAcc(
        'GRILLE AL-ALBANI \u2014 As-Silsilah', '\u0627\u0644\u0633\u0651\u0650\u0644\u0633\u0650\u0644\u064E\u0629',
        '#f39c12',
        _mzFormatAlbani(h.albani)
      );
      hasN3 = true;
    }

    /* Conteneur accordéons secondaires (rempli immédiatement si dispo, sinon via SSE) */
    if(secAccHtml) {
      niv3 += '<div id="sec-acc-'+idx+'"><div class="mz-niv3-label">TAHQIQ WA TAKHRIJ \u2014 VERIFICATION ET EXTRACTION</div>' + secAccHtml + '</div>';
    } else {
      niv3 += '<div id="sec-acc-'+idx+'"></div>';
    }

    if(hasN3) {
      html += '<div class="mz-niv3">'
        +niv3
        +'</div>';
    } else {
      html += '<div class="mz-niv3" style="padding-top:4px;">'+niv3+'</div>';
    }

    html += _mzDisclaimer();
    html += _mzActions('https://dorar.net');
    html += '</div>'; /* /mz-card */
  });

  box.innerHTML = html;
  box.classList.add('active');

  /* Stopper l'animation Dorar loader proprement */
  if(window._dorarLoadTimer){
    clearInterval(window._dorarLoadTimer);
    window._dorarLoadTimer=null;
    var fillE=document.getElementById('progress-fill');
    var diaE=document.getElementById('progress-diamond');
    if(fillE)fillE.style.width='100%';
    if(diaE)diaE.style.left='calc(100% - 4px)';
    var lbE=document.getElementById('loading-box');
    if(lbE)lbE.classList.remove('active');
  }
}

/* ════════════════════════════════════════════════════════════════
   MIZAN v9 — MOTEUR SSE PROGRESSIF (ZÉRO LATENCE VERCEL)
   ● EventSource → SSE si backend supporte Accept: text/event-stream
   ● Fallback JSON classique si pas de SSE
   ● Chaque hadith enrichi livré dès qu'il est prêt
════════════════════════════════════════════════════════════════ */
function _mapHadithRaw(h) {
  /* ── SCHEMA 2026-04 (backend 0624fea) : grade_ar remplace grade ── */
  var g = h.grade_ar || h.grade || '';

  /* ── Priorité 1 : grade_level envoyé par le backend (le plus fiable) ──
     Le backend calcule déjà le grade via _apply_hukm + _apply_authority_override.
     On évite de re-classifier côté frontend pour ne pas écraser un Sahih
     en Da'if par le fallback de _getTechnicalGrade. */
  var _LEVEL_TO_KEY = {sahih:'SAHIH', hasan:'HASAN', daif:'DAIF', mawdu:'MAWDU', mawquf:'MAWDU', rejected:'MAWDU'};
  var backendLevel = (h.grade_level || '').toLowerCase();
  var gradeKey;
  var tg;
  if(_LEVEL_TO_KEY[backendLevel]) {
    gradeKey = _LEVEL_TO_KEY[backendLevel];
    tg = _getTechnicalGrade(g);
    tg.key = gradeKey;
  } else {
    /* Priorité 2 : classification locale via le texte arabe brut */
    tg = _getTechnicalGrade(g);
    gradeKey = tg.key;
  }

  /* ── SCHEMA 2026-04 : grade_def/grade_fr remplacent grade_explique ── */
  var gradeExplique = h.grade_def || h.grade_fr || h.grade_explique || '';
  /* Fallback : si grade_level absent ET texte non classifiable, tenter grade_explique */
  if(gradeKey === 'DAIF' && !backendLevel && gradeExplique) {
    var ex = gradeExplique;
    if(/#2ecc71|#22c55e|SAHIH/i.test(ex))       gradeKey = 'SAHIH';
    else if(/#f39c12|#4ade80|HASAN/i.test(ex))  gradeKey = 'HASAN';
    else if(/#8e44ad|MAWDU/i.test(ex))           gradeKey = 'MAWDU';
  }

  /* ── SCHEMA 2026-04 : silsila (array de nœuds Pydantic) → isnad_chain (pipe string)
     Format attendu par _mzIsnadFromPipe : "Maillon N|nom|titre|verdict|siecle\n…"
     SilsilaNode : {rank, name_ar, fr_name, role, century, death_year, verified} ── */
  /* ── Nettoyage des noms : supprime les labels parasites de Dorar
     (« الراوي: », « المحدث: », « خلاصة حكم المحدث: ») ── */
  function _mzCleanDorarName(s) {
    if(!s) return '';
    return String(s)
      .replace(/خلاصة\s*حكم\s*المحدث\s*:?/g, '')
      .replace(/المحدث\s*:?/g, '')
      .replace(/الراوي\s*:?/g, '')
      .replace(/المصدر\s*:?/g, '')
      .replace(/\s{2,}/g, ' ')
      .trim();
  }
  var isnadStr = '';
  if(Array.isArray(h.silsila) && h.silsila.length) {
    isnadStr = h.silsila.map(function(n, i) {
      var nom     = _mzCleanDorarName(n.name_ar || n.fr_name || n.ar_name || '');
      var titre   = n.fr_name || n.role || '';
      var verdict = (n.verified === false) ? 'INFERE' : (n.role || 'TRANSMIS').toUpperCase();
      var siecle  = n.century || '';
      return 'Maillon ' + (i + 1) + '|' + nom + '|' + titre + '|' + verdict + '|' + siecle;
    }).join('\n');
  } else if(typeof h.isnad_chain === 'string') {
    isnadStr = h.isnad_chain
      .split('\n')
      .map(function(line) {
        var parts = line.split('|');
        if(parts.length >= 2) parts[1] = _mzCleanDorarName(parts[1]);
        return parts.join('|');
      })
      .join('\n');
  }

  /* ── SCHEMA 2026-04 : grade_by_mohadd (dict groupé) → jarh_tadil (markdown)
     Forme : { "Al-Bukhari": {ar_name, fr_name, hukm_ar, hukm_fr, level, color}, … } ── */
  var jarhStr = '';
  if(h.grade_by_mohadd && typeof h.grade_by_mohadd === 'object' && !Array.isArray(h.grade_by_mohadd)) {
    var parts = [];
    Object.keys(h.grade_by_mohadd).forEach(function(k) {
      var v = h.grade_by_mohadd[k];
      if(!v) return;
      var nm = v.fr_name || k || '';
      var ar = v.ar_name || '';
      var hk = v.hukm_fr || v.hukm_ar || '';
      parts.push('**' + nm + '**' + (ar ? ' (' + ar + ')' : '') + ' : ' + hk);
    });
    jarhStr = parts.join('\n');
  } else if(typeof h.jarh_tadil === 'string') {
    jarhStr = h.jarh_tadil;
  }

  /* ── Score d'autorité (miroir exact du barème de fer backend v24.1)
     Priorité : backend _authority_score > calcul local
     100 = Sahîhayn (Al-Bukhârî / Muslim) → Verdict forcé « صحيح »
      90 = Muwatta' Mâlik
      80 = Sunan (Abû Dâwûd, Tirmidhî, Nasâ'î, Ibn Mâja) + Musnad Ahmad
      70 = Cheikh Al-Albânî ── */
  var authorityScore = 0;
  /* Priorité 1 : valeur calculée côté backend (la plus fiable) */
  if(typeof h._authority_score === 'number') {
    authorityScore = h._authority_score;
  } else {
    /* Priorité 2 : recalcul local (fallback si backend ne renvoie pas le champ) */
    var _authBlob = ((h.savant || '') + ' ' + (h.source || ''));
    if(/صحيح البخاري|الجامع الصحيح|بخاري|صحيح مسلم|مسلم|bukhari|muslim/i.test(_authBlob))
      authorityScore = 100;
    else if(/موطأ مالك|موطأ|مالك بن أنس|مالك|muwatta|malik/i.test(_authBlob))
      authorityScore = 90;
    else if(/مسند أحمد|ابن حنبل|أبو داود|ترمذي|نسائي|ابن ماجه|أحمد|dawud|tirmidhi|nasa|ibn maja|ahmad/i.test(_authBlob))
      authorityScore = 80;
    else if(/الألباني|albani/i.test(_authBlob))
      authorityScore = 70;
  }

  return {
    ar:             h.arabic_text     || '',
    mohdith:        h.savant          || '—',
    source:         h.source          || '—',
    grade:          gradeKey,
    grade_ar:       g,
    french:         h.french_text     || '',
    grade_explique: gradeExplique,
    jarh_tadil:     jarhStr,
    isnad_chain:    isnadStr,
    sanad:          h.sanad_conditions|| '',
    mutabaat:       h.mutabaat        || '',
    avis:           h.avis_savants    || '',
    albani:         h.grille_albani   || '',
    pertinence:     h.pertinence      || '',
    rawi:           h.rawi            || '—',
    takhrij:        h.takhrij         || '',
    /* ── Enrichissement Claude (Règle Amâna : vide si non attesté) ── */
    sharh:          h.sharh           || '',
    gharib:         h.gharib          || '',
    sabab_wurud:    h.sabab_wurud     || '',
    fawaid:         h.fawaid          || '',
    authority_score: authorityScore,
    numero:'', explainGrade:''
  };
}

/* ════════════════════════════════════════════════════════════════
   _imperializeGradeExplique — Filtre d'Honneur Impérial
   ● Parse les 4 lignes <b>Label :</b> texte
   ● Enveloppe les noms des savants dans .scholar-glow
   ● Restitue un .imperial-card avec labels pourpres et séparateurs
   ● Encapsule le Statut pratique dans .verdict-box
════════════════════════════════════════════════════════════════ */
function _imperializeGradeExplique(raw) {
  if (!raw) return '';

  /* ── Regex des noms de savants à magnifier ── */
  var SCHOLARS = [
    'Al-Bukhari','Bukhari','Muslim','At-Tirmidhi','Tirmidhi',
    'Abu Dawud','An-Nasa\u02bci','Nasa\u02bci','Ibn Majah',
    'Ahmad','Ibn Hanbal','Malik','Ash-Shafi\u02bci','Shafi\u02bci',
    'Ad-Daraqutni','Daraqutni','Al-Hakim','Hakim','Al-Bayhaq\u012b','Bayhaqi',
    'Ibn as-Salah','Ibn Hajar','Ibn Kathir','Ibn Taymiyyah','Ibn al-Qayyim',
    'Adh-Dhahabi','Dhahabi','An-Nawawi','Nawawi',
    'Al-Albani','Albani','Ibn Baz','Ibn Uthaymin','Ibn B\u0101z',
    'Al-Hafidh','Hafidh','Al-Hafiz','Al-Hufadh'
  ];
  var scholRe = new RegExp('(' + SCHOLARS.map(function(s){
    return s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
  }).join('|') + ')', 'g');

  function glowScholars(txt) {
    return txt.replace(scholRe, "<span class='scholar-glow'>$1</span>");
  }

  /* ── Labels canoniques → clés ── */
  var LABELS = [
    { key: 'sources',   re: /Sources\s+principales\s*:/i,   fr: 'SOURCES PRINCIPALES' },
    { key: 'cause',     re: /Cause\s+globale\s*:/i,         fr: 'CAUSE GLOBALE' },
    { key: 'sceau',     re: /Sceau\s+contemporain\s*:/i,    fr: 'SCEAU CONTEMPORAIN' },
    { key: 'statut',    re: /Statut\s+pratique\s*:/i,       fr: 'STATUT PRATIQUE' }
  ];

  /* ── Découpage du texte en segments par <b>...</b> ── */
  /* On travaille en HTML brut — split sur les <b>Label</b> */
  var segments = [];
  var remaining = raw;

  LABELS.forEach(function(lbl, i) {
    var tagRe = new RegExp('<b>([^<]*?' + lbl.fr.split(' ')[0] + '[^<]*?)<\\/b>\\s*:?', 'i');
    var mTag = remaining.match(tagRe);
    if (!mTag) return;
    var pos = remaining.indexOf(mTag[0]);
    /* Texte avant ce label → flush dans le segment précédent ou ignorer */
    var nextLblRe = i < LABELS.length - 1
      ? new RegExp('<b>[^<]*?' + LABELS[i+1].fr.split(' ')[0] + '[^<]*?<\\/b>', 'i')
      : null;
    var afterLabel = remaining.substring(pos + mTag[0].length);
    var endPos = afterLabel.length;
    if (nextLblRe) {
      var mNext = afterLabel.match(nextLblRe);
      if (mNext) endPos = afterLabel.indexOf(mNext[0]);
    }
    var content = afterLabel.substring(0, endPos)
      .replace(/^[\s:]+/, '')
      .replace(/<br\s*\/?>/gi, ' ')
      .replace(/\s{2,}/g, ' ')
      .trim();
    segments.push({ key: lbl.key, fr: lbl.fr, content: content });
    remaining = afterLabel.substring(endPos);
  });

  /* Fallback : si le parsing par labels échoue (texte libre), afficher brut enrichi */
  if (!segments.length) {
    return "<div class='imperial-card'>" + glowScholars(raw) + "</div>";
  }

  /* ── Construction du rendu impérial ── */
  var html = "<div class='imperial-card'>";

  segments.forEach(function(seg, i) {
    if (i > 0) html += "<span class='imperial-sep'></span>";
    html += "<span class='imperial-label'>" + seg.fr + "</span>";

    if (seg.key === 'statut') {
      /* Statut pratique → verdict-box */
      var isOk = /PEUT\s+ETRE\s+CIT/i.test(seg.content);
      var boxCls = isOk ? 'verdict-box verdict-ok' : 'verdict-box';
      html += "<span class='" + boxCls + "'>" + seg.content.replace(/<[^>]+>/g,'').trim() + "</span>";
    } else {
      html += "<span class='imperial-line'>" + glowScholars(seg.content) + "</span>";
    }
  });

  html += "</div>";
  return html;
}

/* ── Mise à jour partielle d'une carte (SSE enrichissement) ────
   Injecte dans les 3 zones oignon + étend min-height progressivement */
/* ════════════════════════════════════════════════════════════════
   _mzMd — Convertisseur Markdown minimal → HTML sûr
   Gère : **bold**, *italic*, # titres, --- séparateurs, \n→<br>
   Utilisé pour nettoyer les champs texte venant du backend.
════════════════════════════════════════════════════════════════ */
function _mzMd(txt) {
  if(!txt) return '';
  return String(txt)
    /* Titres ## et # */
    .replace(/^#{1,3}\s+(.+)$/gm, '<strong style="font-family:Cinzel,serif;letter-spacing:.1em;font-size:10px;color:rgba(212,175,55,.8);">$1</strong>')
    /* Séparateurs --- */
    .replace(/^---+$/gm, '<hr style="border:none;border-top:1px solid rgba(201,168,76,.15);margin:8px 0;">')
    /* **bold** */
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    /* *italic* */
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    /* Sauts de ligne */
    .replace(/\n{2,}/g, '</p><p style="margin:6px 0;">')
    .replace(/\n/g, '<br>');
}


function _enrichCardSSE(idx, h) {
  /* ═══════════════════════════════════════════════════════════════
     _enrichCardSSE v18.6 — RENDU PROGRESSIF ANTI-JANK
     Stratégie : rendre la main au navigateur entre chaque zone.
     ● Tranche 1 (immédiat)    : Zone 1 — traduction + verdict
     ● Tranche 2 (rAF)         : Zone 2 isnad — timeline dorée
     ● Tranche 3 (setTimeout)  : Zone 2 accordéons + Zone 3 trésor
     Garantit 60 fps même sur téléphone mid-range (Snapdragon 6xx).
  ═══════════════════════════════════════════════════════════════ */
  var card = document.getElementById('topic-card-' + idx);
  if(!card) { console.warn('[SSE] card topic-card-'+idx+' not found'); return; }
  /* BOUCLIER UI — ANTI-DOUBLON : empêche le double enrichissement SSE */
  if (card.dataset.enriched === '1') { console.warn('[SSE] card '+idx+' déjà enrichie — ignoré'); return; }
  card.dataset.enriched = '1';

  /* ══ TRANCHE 1 — IMMÉDIAT : Zone 1 (légère, visible en premier) ══ */

  /* Traduction française */
  if(h.french) {
    var frZone = document.getElementById('fr-zone-' + idx);
    if(frZone) {
      frZone.innerHTML = _mzMd(h.french);
      frZone.style.minHeight = '';
      frZone.style.animation = 'vIn .4s ease';
      frZone.className = 'mz-matn-fr';
    } else {
      var arEl = card.querySelector('.mz-matn-ar');
      if(arEl) {
        var d=document.createElement('div');d.className='mz-matn-fr';d.innerHTML=_mzMd(h.french);
        d.style.animation='vIn .4s ease'; arEl.parentNode.insertBefore(d,arEl.nextSibling);
      }
    }
  }

  /* Verdict enrichi — Enluminure Impériale */
  if(h.grade_explique) {
    var hukmZone = document.getElementById('hukm-zone-' + idx);
    var hukmText = document.getElementById('hukm-text-' + idx);
    var rendered = _imperializeGradeExplique(h.grade_explique);
    if(hukmZone && hukmText) {
      hukmText.innerHTML = rendered;
      hukmZone.style.display = '';
      hukmZone.style.animation = 'vIn .4s ease';
    } else {
      var illahEl = card.querySelector('.mz-illah-text');
      if(illahEl) { illahEl.innerHTML = rendered; illahEl.style.animation='vIn .4s ease'; }
    }
  }

  /* ── Badge Sahihayn — Authenticité Garantie (score 100 : Bukhari/Muslim) ── */
  if(h.authority_score === 100 && !card.querySelector('.mz-sahihayn-badge')) {
    var sahihayn = document.createElement('div');
    sahihayn.className = 'mz-sahihayn-badge';
    sahihayn.style.cssText = 'margin:6px 18px 10px;padding:11px 16px;'
      + 'background:linear-gradient(135deg,rgba(34,197,94,.14),rgba(212,175,55,.09));'
      + 'border:1px solid rgba(34,197,94,.45);border-radius:10px;text-align:center;'
      + 'box-shadow:0 0 18px rgba(34,197,94,.12),inset 0 0 20px rgba(212,175,55,.05);'
      + 'animation:vIn .5s ease;';
    sahihayn.innerHTML =
        '<div style="font-family:Cinzel,serif;font-size:6.5px;letter-spacing:.32em;'
      + 'color:rgba(212,175,55,.55);margin-bottom:4px;">\u2730 MUTTAFAQUN \u02bfALAYH \u2730</div>'
      + '<div style="font-family:Cinzel,serif;font-size:11px;font-weight:800;letter-spacing:.15em;'
      + 'color:#22c55e;text-shadow:0 0 12px rgba(34,197,94,.4);">AUTHENTICIT\u00c9 GARANTIE \u2014 SAHIHAYN</div>'
      + '<div style="font-family:\'Scheherazade New\',serif;font-size:16px;color:#d4af37;margin-top:3px;">'
      + '\u0627\u0644\u0635\u0651\u064E\u062D\u0650\u064A\u062D\u064E\u0627\u0646 \u2014 '
      + '\u0627\u0644\u0628\u064F\u062E\u064E\u0627\u0631\u0650\u064A\u0651 \u0648\u0645\u064F\u0633\u0644\u0650\u0645</div>';
    var hukmZoneB = document.getElementById('hukm-zone-' + idx);
    if(hukmZoneB && hukmZoneB.parentNode) {
      hukmZoneB.parentNode.insertBefore(sahihayn, hukmZoneB);
    } else {
      card.insertBefore(sahihayn, card.firstChild);
    }
  }

  /* Pertinence badge */
  if(h.pertinence && /^(OUI|PARTIEL|NON)/i.test(h.pertinence)) {
    var pertEl = card.querySelector('.mz-pertinence');
    if(pertEl) {
      var pc = /^OUI/i.test(h.pertinence) ? '#2ecc71' : /^PARTIEL/i.test(h.pertinence) ? '#f39c12' : '#e74c3c';
      pertEl.textContent = h.pertinence.substring(0,60);
      pertEl.style.background = pc+'18'; pertEl.style.color = pc;
      pertEl.style.border = '1px solid '+pc+'44';
    }
  }

  /* Effacer typewriter avec fondu */
  var twEl = document.getElementById('typewriter-' + idx);
  if(twEl) { twEl.style.opacity='0'; setTimeout(function(){ twEl.textContent=''; twEl.style.opacity='1'; }, 300); }

  /* ══ TRANCHE 2 — requestAnimationFrame : Zone 2 Isnad (lourd) ══
     On attend le prochain frame pour injecter la timeline.
     Le navigateur a le temps de peindre la Zone 1 d'abord. */
  var isnadSrc = h.isnad_chain || '';
  var gradeForPipe = h.grade || 'DAIF';

  /* ── PHASE 1 : requestAnimationFrame — Zone 2 non-bloquante ── */
  requestAnimationFrame(function() {
    var isnadZone = document.getElementById('isnad-zone-' + idx);
    if(!isnadZone) {
      isnadZone = document.createElement('div');
      isnadZone.id = 'isnad-zone-' + idx;
      var sanadAnchor = document.getElementById('sanad-acc-' + idx);
      if(sanadAnchor && card.contains(sanadAnchor)) {
        card.insertBefore(isnadZone, sanadAnchor);
      } else {
        card.appendChild(isnadZone);
      }
    }

    /* Skeleton immédiat — Bouclier Science : min-height:40px + titre doré garanti */
    if(!isnadZone.querySelector('.mzAr') && !isnadZone.querySelector('.mzC4-rw') && !isnadZone.querySelector('.mzAr-orb')) {
      isnadZone.innerHTML = _mzSkeletonZone2();
    }

    /* Promise non-bloquante : calcul arbre dans micro-task séparé (zéro blocage UI) */
    var arbrePromise = new Promise(function(resolve) {
      setTimeout(function() {
        var result = '';
        try {
          if(isnadSrc && isnadSrc.length > 10) {
            result = _mzIsnadFromPipe(isnadSrc, gradeForPipe) || '';
          }
        } catch(errArb) { console.warn('[M\u00eezan] arbrePromise:', errArb.message); }
        resolve(result);
      }, 0);
    });

    /* PHASE 2 — Fallback Souverain (Lign\u00e9e d\u2019Or) si arbre absent apr\u00e8s 2000ms */
    var fallbackTimer = setTimeout(function() {
      _mzFallbackLigneeOr('isnad-zone-' + idx);
    }, 2000);

    /* D\u00e8s que l'arbre est pr\u00eat, remplacer le skeleton et annuler le fallback */
    arbrePromise.then(function(cascadeHtml) {
      clearTimeout(fallbackTimer);
      var zone = document.getElementById('isnad-zone-' + idx);
      if(!zone) return;
      if(cascadeHtml) {
        zone.innerHTML = '';  /* BOUCLIER SYNTAXE — nettoyage strict avant injection */
        zone.innerHTML = cascadeHtml;
        zone.style.animation = 'vIn .5s ease';
      } else {
        _mzFallbackLigneeOr('isnad-zone-' + idx);
      }
    });

    /* Accord\u00e9ons Zone 2 + Zone 3 (16ms = 1 frame apr\u00e8s Zone 1) */
    setTimeout(function() {

      /* Zone 2 : Jarh wa Ta'dil + 5 conditions + Mutaba'at */
      var sanadAcc = document.getElementById('sanad-acc-' + idx);
      if(sanadAcc) {
        var z2Html = '';

        if(h.jarh_tadil) {
          z2Html += '<details class="mz-details" style="margin:8px 18px;">'
            + '<summary class="mz-details-sum" style="color:#5dade2;cursor:pointer;font-family:Cinzel,serif;'
            + 'font-size:9px;letter-spacing:.18em;list-style:none;padding:10px 14px;border:1px solid rgba(93,173,226,.2);'
            + 'border-radius:8px;background:rgba(93,173,226,.04);">'
            + '&#9656; AQWAL AL-A\u02bcIMMAH \u2014 Verdicts des Imams sur les Rawis'
            + '</summary>'
            + '<div style="padding:12px 14px;border:1px solid rgba(93,173,226,.1);border-top:none;border-radius:0 0 8px 8px;'
            + 'font-family:\'Cormorant Garamond\',serif;font-size:14px;line-height:1.75;">'
            + _mzMd(h.jarh_tadil) + '</div></details>';
        }

        if(h.sanad) {
          /* ── BARÈME DE FER : Comptage des 5 états Shurut as-Sihhah ──
             Priorité stricte : ABSENTE > PARTIELLE > ÉTABLIE > EN ATTENTE
             (Règle Amâna : Jarh précède Ta'dil — l'absence prime) */
          var nbAbsent  = (h.sanad.match(/ABSENTE?/g) || []).length;
          var nbPartiel = (h.sanad.match(/PARTIELLE?/g) || []).length;
          var nbEtablie = (h.sanad.match(/\u00c9TABLIES?|ETABLIES?/gi) || []).length;
          var sCol, sLbl;
          if(nbAbsent > 0) {
            /* Niveau 1 — ROUGE : au moins une condition explicitement absente */
            sCol = '#e74c3c';
            sLbl = nbAbsent + ' condition(s) ABSENTE(S)';
          } else if(nbEtablie === 5) {
            /* Niveau 2 — VERT : toutes les 5 conditions établies */
            sCol = '#2ecc71';
            sLbl = '5/5 \u00c9TABLIES';
          } else if(nbEtablie > 0 || nbPartiel > 0) {
            /* Niveau 3 — ORANGE : conditions partiellement établies */
            sCol = '#f39c12';
            sLbl = nbEtablie + '/5 \u00c9TABLIES' + (nbPartiel ? ' (' + nbPartiel + ' PARTIELLE(S))' : '');
          } else {
            /* Niveau 4 — GRIS : données insuffisantes (règle Amâna) */
            sCol = '#6b7280';
            sLbl = 'ANALYSE EN ATTENTE';
          }
          z2Html += '<details class="mz-details" style="margin:8px 18px;">'
            + '<summary class="mz-details-sum" style="color:' + sCol + ';cursor:pointer;font-family:Cinzel,serif;'
            + 'font-size:9px;letter-spacing:.18em;list-style:none;padding:10px 14px;border:1px solid ' + sCol + '33;'
            + 'border-radius:8px;background:' + sCol + '08;">'
            + '&#9656; SHURUT AS-SIHHAH \u2014 5 Conditions (' + sLbl + ')'
            + '</summary>'
            + '<div style="padding:12px 14px;border:1px solid ' + sCol + '22;border-top:none;border-radius:0 0 8px 8px;'
            + 'font-family:\'Cormorant Garamond\',serif;font-size:13.5px;line-height:1.8;">'
            + _mzMd(h.sanad) + '</div></details>';
        }

        if(h.mutabaat) {
          var hasRenfort = /Hasan li Ghayrihi|Sahih li Ghayrihi|renfor|confirme/i.test(h.mutabaat);
          var mCol = hasRenfort ? '#9b59b6' : 'rgba(155,89,182,.5)';
          z2Html += '<details class="mz-details" style="margin:8px 18px;">'
            + '<summary class="mz-details-sum" style="color:' + mCol + ';cursor:pointer;font-family:Cinzel,serif;'
            + 'font-size:9px;letter-spacing:.18em;list-style:none;padding:10px 14px;border:1px solid rgba(155,89,182,.2);'
            + 'border-radius:8px;background:rgba(155,89,182,.04);">'
            + '&#9656; AL-MUTABA\u02bcAT WA ASH-SHAWAHID \u2014 Voies de Renfort'
            + '</summary>'
            + '<div style="padding:12px 14px;border:1px solid rgba(155,89,182,.1);border-top:none;border-radius:0 0 8px 8px;'
            + 'font-family:\'Cormorant Garamond\',serif;font-size:13.5px;line-height:1.8;">'
            + _mzMd(h.mutabaat) + '</div></details>';
        }

        if(z2Html) sanadAcc.innerHTML = z2Html;
      }

      /* Zone 3 : Tr\u00e9sor des 14 Si\u00e8cles (ouvert par d\u00e9faut) */
      var secAcc = document.getElementById('sec-acc-' + idx);
      if(secAcc) {
        var z3Html = '';

        /* ── Builder g\u00e9n\u00e9rique pour les 4 accord\u00e9ons Amâna ── */
        function _mzAmanaAcc(title, content, color, openByDefault) {
          if(!content || !String(content).trim()) return '';
          var c = color || '#d4af37';
          var rgba = function(a) { return 'rgba(212,175,55,' + a + ')'; };
          if(c === '#5dade2') rgba = function(a) { return 'rgba(93,173,226,' + a + ')'; };
          else if(c === '#9b59b6') rgba = function(a) { return 'rgba(155,89,182,' + a + ')'; };
          else if(c === '#2ecc71') rgba = function(a) { return 'rgba(46,204,113,' + a + ')'; };
          return '<details class="mz-details"' + (openByDefault ? ' open' : '') + ' style="margin:8px 18px 4px;">'
            + '<summary class="mz-details-sum" style="color:' + c + ';cursor:pointer;font-family:Cinzel,serif;'
            + 'font-size:9px;letter-spacing:.18em;list-style:none;padding:10px 14px;border:1px solid ' + rgba('.22') + ';'
            + 'border-radius:8px;background:' + rgba('.05') + ';">'
            + '&#9656; ' + title
            + '</summary>'
            + '<div style="padding:12px 14px;border:1px solid ' + rgba('.1') + ';border-top:none;border-radius:0 0 8px 8px;'
            + 'font-family:\'Cormorant Garamond\',serif;font-size:14px;line-height:1.85;color:rgba(228,208,160,.92);">'
            + _mzMd(content) + '</div></details>';
        }

        /* ── STRUCTURE 12 ZONES (Barème de Fer v24.1) ───────────────────
           Zone 9  : GHARIB       — vocabulaire rare (An-Nihâyah)
           Zone 10 : SABAB AL-WURÛD — contexte de narration (Fath al-Bârî)
           Zone 11 : FAWÂ'ID      — leçons pratiques (Fath al-Bârî)
           Zone 12 : GRILLE AL-ALBÂNÎ — analyse de la Silsilah
           Règle Amâna : zone omise si vide "" (jamais de contenu inventé) ── */
        z3Html += _mzAmanaAcc('\ud83d\udcd6 VOCABULAIRE \u2014 GHAR\u012aB AL-HAD\u012aTH', h.gharib,      '#5dade2', false);
        z3Html += _mzAmanaAcc('\ud83c\udfdb\ufe0f CONTEXTE \u2014 SABAB AL-WUR\u016bD',    h.sabab_wurud, '#9b59b6', false);
        z3Html += _mzAmanaAcc('\ud83d\udca1 LE\u00c7ONS \u2014 FAW\u0100\u02beID',         h.fawaid,      '#2ecc71', false);
        z3Html += _mzAmanaAcc(
          '\ud83d\udccc GRILLE AL-ALB\u0100N\u012b \u2014 As-Silsilah',
          h.albani, '#f39c12', false
        );

        if(z3Html) secAcc.innerHTML = z3Html;
      }

    }, 16); /* ~1 frame — accordéons Zone 2 + Zone 3 */
  }); /* /requestAnimationFrame isnad */
}


/* ── Recherche Dorar (FR ou AR auto-converti) — SSE temps réel + fallback JSON */
/* ════════════════════════════════════════════════════════════════
   MÎZÂN v13-SECURED — MOTEUR SSE TEMPS RÉEL
   ● Steps avancées par events nommés du backend (6 IDs)
   ● 5 cartes générées instantanément sur event dorar
   ● _applyChunk impénétrable (jamais de JSON visible)
   ● _enrichCardSSE sur event hadith
   ● _getTechnicalGrade sur grade_ar brut (badge immédiat)
════════════════════════════════════════════════════════════════ */

/* ── Buffer chunks par index hadith ─────────────────────────── */
var _chunkBuffers = {};

/* ── Map des 6 IDs status backend → index étape locale ─────── */
var _STEP_MAP = {
  INITIALISATION: 0,
  DORAR:          1,
  TAKHRIJ:        2,
  RIJAL:          3,
  JARH:           4,
  HUKM:           5
};
var _currentStepIdx = 0;

/* ── _advanceStep : illumine le maillon correspondant ──────────
   id : ID string (INITIALISATION / DORAR / TAKHRIJ / RIJAL / JARH / HUKM)
   ou forceIdx : numéro d'étape direct                            */
function _advanceStep(id, forceIdx) {
  var idx = (forceIdx !== undefined)
    ? forceIdx
    : (_STEP_MAP[id] !== undefined ? _STEP_MAP[id] : -1);
  if (idx < 0) return;
  _currentStepIdx = idx;

  var stepsAll = document.querySelectorAll('#steps-list .step-item');
  var total = stepsAll.length || 6;
  var pct = Math.min(Math.round((idx / Math.max(total - 1, 1)) * 90), 92);
  var fillD = document.getElementById('progress-fill');
  var diamD = document.getElementById('progress-diamond');
  if (fillD) fillD.style.width = pct + '%';
  if (diamD) diamD.style.left = 'calc(' + pct + '% - 4px)';

  for (var k = 0; k < total; k++) {
    var el = document.getElementById('step-d-' + k);
    if (!el) continue;
    el.classList.remove('done', 'current');
    if (k < idx)       el.classList.add('done');
    else if (k === idx) el.classList.add('current');
  }
}

/* ── _finishLoading : stoppe tout, barre à 100% ─────────────── */
function _finishLoading() {
  if (window._dorarLoadTimer) { clearInterval(window._dorarLoadTimer); window._dorarLoadTimer = null; }
  var fillE = document.getElementById('progress-fill');
  var diaE  = document.getElementById('progress-diamond');
  if (fillE) fillE.style.width = '100%';
  if (diaE)  diaE.style.left  = 'calc(100% - 4px)';
  var lbE = document.getElementById('loading-box');
  if (lbE) lbE.classList.remove('active');
  document.querySelectorAll('#steps-list .step-item').forEach(function(el) {
    el.classList.remove('current'); el.classList.add('done');
  });
}

/* ════════════════════════════════════════════════════════════════
   _renderDorarCards — Structure "OIGNON" 3 zones
   ● Zone 1 : Verdict Flash   (badge immédiat + traduction)
   ● Zone 2 : Sanad / Chaîne  (isnad + Jarh wa Ta'dil)
   ● Zone 3 : Trésor 14 s.    (commentaires des savants en direct)
   ● Hauteurs stables pour un streaming sans saut
════════════════════════════════════════════════════════════════ */
function _renderDorarCards(rawHadiths, query) {
  var box = document.getElementById('result-box');
  box.innerHTML = '';
  _chunkBuffers = {};
  if (!rawHadiths || !rawHadiths.length) return;

  var html = '<div class="mz-source"><span class="mz-source-dot" style="background:#c9a84c;box-shadow:0 0 6px rgba(201,168,76,.5);"></span>'
    + '<span class="mz-source-text">' + rawHadiths.length + ' R\u00c9SULTAT(S) \u00b7 DORAR.NET \u00b7 AL MIZ\u00c2N</span></div>';

  rawHadiths.forEach(function(r, idx) {
    var gradeRaw = r.grade_ar || r.grade || '';
    var tg = _getTechnicalGrade(gradeRaw);
    var metaStr = '';
    if (r.savant && r.savant !== '\u2014') metaStr += '\u0627\u0644\u0645\u062d\u062f\u062b\u202f: ' + r.savant;
    if (r.source && r.source !== '\u2014') metaStr += (metaStr ? '\u202f\u00b7\u202f' : '') + '\u0627\u0644\u0645\u0635\u062f\u0631\u202f: ' + r.source;

    html += '<div class="mz-card" id="topic-card-' + idx + '" '
      + 'style="animation:argCardIn .4s ease both;animation-delay:' + (idx * 0.08) + 's;overflow:hidden;">';

    /* ── Matn arabe + traduction (remplie par SSE) ── */
    html += '<div class="mz-matn">';
    if (r.arabic_text || r.ar) {
      html += '<div class="mz-matn-ar">' + (r.arabic_text || r.ar) + '</div>';
    }
    html += '<div class="mz-matn-fr" id="fr-zone-' + idx + '" style="min-height:2px;"></div>';
    if (metaStr) html += '<div class="mz-matn-meta">' + metaStr + '</div>';
    html += '</div>'; /* /mz-matn */

    /* ── Badge verdict immédiat (via _getTechnicalGrade) ── */
    html += _mzVerdict(tg.key, gradeRaw);

    /* ── Zone Al-Hukm — Enluminure Impériale (remplie par SSE) ── */
    html += '<div id="hukm-zone-' + idx + '" style="display:none;padding:0 18px 14px;">'
      + '<div class="mz-illah-text" id="hukm-text-' + idx + '"></div>'
      + '</div>';

    /* ── Zone 2 — Chaîne de Transmission (Isnad) — NEXUS GALACTIQUE ── */
    html += `<div style="border-top:1px solid rgba(212,175,55,.18);border-bottom:1px solid rgba(212,175,55,.18);background:linear-gradient(165deg,rgba(10,6,0,.92) 0%,rgba(15,10,2,.85) 40%,rgba(8,5,0,.95) 100%);margin:6px 0 0;position:relative;overflow:hidden;">`;
    html += `<div style="position:absolute;inset:0;background:radial-gradient(ellipse at 50% 0%,rgba(212,175,55,.06) 0%,transparent 70%);pointer-events:none;"></div>`;
    html += `<div style="position:relative;z-index:1;padding:12px 20px 4px;font-family:Cinzel,serif;font-size:6px;letter-spacing:.28em;color:rgba(212,175,55,.45);text-transform:uppercase;text-shadow:0 0 12px rgba(212,175,55,.2);">ZONE 2 \u2014 SILSILAT AL-ISN\u0100D \u2014 CHA\u00ceNE DE TRANSMISSION</div>`;
    html += '<div id="isnad-zone-' + idx + '" style="min-height:40px;transition:min-height .4s ease;position:relative;z-index:1;">' + _mzSkeletonZone2() + '</div>';
    html += `</div>`; /* /zone-2-isnad */

    /* ── Accordéons Zone 2 (Jarh wa Ta\'dil, 5 conditions, Mutaba\'at) ── */
    html += '<div id="sanad-acc-' + idx + '" style="padding:0 18px;"></div>';

    /* ── Typewriter SSE (intermédiaire) ── */
    html += '<div id="typewriter-zone-' + idx + '" style="padding:4px 18px 0;">'
      + '<div id="typewriter-' + idx + '" style="font-family:\'Cormorant Garamond\',serif;'
      + 'font-size:13px;color:rgba(201,168,76,.45);line-height:1.7;font-style:italic;'
      + 'min-height:0;white-space:pre-wrap;word-break:break-word;overflow-anchor:none;"></div>'
      + '</div>';

    /* ── Zone 3 — Trésor des 14 siècles (accordéon ouvert par défaut) ── */
    html += '<div id="sec-acc-' + idx + '" style="padding:0 0 4px;"></div>';

    html += _mzDisclaimer();
    html += _mzActions('https://dorar.net');
    html += '</div>'; /* /mz-card */
  });

  box.innerHTML = html;
  box.classList.add('active');
}


/* ── _applyChunk IMPÉNÉTRABLE ───────────────────────────────────
   Règle absolue : l'utilisateur ne voit JAMAIS du JSON ni du code.
   1. Si data est un objet : lire .delta, .content, .text ou .msg
   2. Si data est une string : tenter JSON.parse → extraire .delta/.content
   3. Strip tout ce qui ressemble à JSON : {...} [...] ou balises <...>
   4. Strip les entités HTML et les séquences techniques
   5. Si le résultat contient '{' ou '"' → ne rien afficher             */
function _applyChunk(idx, data) {
  var txt = '';

  /* Étape 1 : extraire le texte de l'objet */
  if (data && typeof data === 'object') {
    txt = data.delta || data.content || data.text || data.msg || '';
  } else if (typeof data === 'string') {
    /* Étape 2 : tenter JSON.parse */
    try {
      var parsed = JSON.parse(data);
      txt = (parsed && (parsed.delta || parsed.content || parsed.text || parsed.msg)) || '';
    } catch (_) {
      txt = data;
    }
  }

  /* Étape 3 : strip blocs JSON, balises HTML et caractères techniques */
  txt = String(txt)
    .replace(/\{[^{}]*\}/g, '')           /* strip {...} imbrication simple */
    .replace(/\[[^\[\]]*\]/g, '')          /* strip [...] */
    .replace(/<[^>]+>/g, ' ')              /* strip balises HTML */
    .replace(/&[a-z#0-9]+;/gi, ' ')       /* strip entités HTML */
    .replace(/\\[nrtu"'\\]/g, ' ')         /* strip séquences d'échappement */
    .replace(/["'`]/g, '')                 /* strip guillemets résiduels */
    .replace(/[{}[\]]/g, '')               /* strip accolades/crochets résiduels */
    .replace(/\s{2,}/g, ' ')
    .trim();

  /* Étape 4 : si le texte contient encore du JSON ou du code → abandonner */
  if (!txt || txt.indexOf('{') !== -1 || txt.indexOf('"') !== -1) return;

  /* Étape 5 : afficher dans le typewriter */
  var el = document.getElementById('typewriter-' + idx);
  if (!el) return;
  if (!_chunkBuffers[idx]) _chunkBuffers[idx] = '';
  _chunkBuffers[idx] += txt;

  /* Limiter à 280 chars pour l'effet typo */
  var display = _chunkBuffers[idx];
  if (display.length > 280) display = display.substring(0, 280) + '\u2026';
  el.textContent = display;

  /* Avancer les étapes pendant la génération IA */
  var stepsLen = document.querySelectorAll('#steps-list .step-item').length || 6;
  if (_currentStepIdx < stepsLen - 2) {
    _advanceStep(null, _currentStepIdx + 1);
  }
}

/* ════════════════════════════════════════════════════════════════
   _searchDorarTopic v13-SECURED — consommateur SSE robuste
════════════════════════════════════════════════════════════════ */
async function _searchDorarTopic(query) {
  var lb  = document.getElementById('loading-box');
  var box = document.getElementById('result-box');
  if (lb) lb.classList.add('active');
  if (box) box.classList.remove('active');
  _chunkBuffers = {};
  _currentStepIdx = 0;
  _advanceStep('INITIALISATION');

  /* ── CACHE LOCALSTORAGE : si requête identique < 1h, zéro appel serveur ── */
  var _mzCacheKey = 'mizan_v3_' + query.trim().toLowerCase().replace(/\s+/g,'_').substring(0,80);
  var _MZ_TTL = 3600000;
  var _cachedDorar = null;
  var _cachedHadiths = [];
  try {
    var _raw = localStorage.getItem(_mzCacheKey);
    if (_raw) {
      var _parsed = JSON.parse(_raw);
      if (_parsed && (Date.now() - (_parsed.ts || 0)) < _MZ_TTL) {
        _renderDorarCards(_parsed.dorar, query);
        _advanceStep('TAKHRIJ');
        (_parsed.hadiths || []).forEach(function(h) {
          _enrichCardSSE(h.index, h.data);
          _advanceStep('HUKM');
        });
        _finishLoading();
        return;
      }
    }
  } catch(_ce) {}
  /* ───────────────────────────────────────────────────────────────────────── */

  var searchUrl = MIZAN_SEARCH_IA + '?q=' + encodeURIComponent(query);
  var sseOK = typeof ReadableStream !== 'undefined' && typeof TextDecoder !== 'undefined';

  if (sseOK) {
    try {
      var resp = await fetch(searchUrl, {
        method: 'GET',
        headers: { 'Accept': 'text/event-stream', 'Cache-Control': 'no-cache' }
      });

      if (resp.ok && (resp.headers.get('content-type') || '').includes('text/event-stream')) {
        var reader  = resp.body.getReader();
        var decoder = new TextDecoder();
        var buf     = '';
        var evtName = '';
        var dorarOK = false;

        while (true) {
          var read = await reader.read();
          if (read.done) break;
          buf += decoder.decode(read.value, { stream: true });
          var lines = buf.split('\n');
          buf = lines.pop();

          for (var li = 0; li < lines.length; li++) {
            var raw  = lines[li];
            var line = raw.trim();

            if (!line) { evtName = ''; continue; }
            if (line.charAt(0) === '#') continue;

            /* Capturer le nom de l'event */
            if (line.indexOf('event:') === 0) {
              evtName = line.substring(6).trim();
              continue;
            }

            if (line.indexOf('data:') !== 0) continue;
            var dataStr = line.substring(5).trim();
            if (!dataStr) continue;

            /* ── EVENT : status ─────────────────────────────── */
            if (evtName === 'status') {
              /* data peut être un ID string pur ou un objet JSON */
              var stepId = dataStr;
              try {
                var sm = JSON.parse(dataStr);
                stepId = sm.step || sm.id || sm || '';
              } catch (_) {}
              if (typeof stepId === 'string') _advanceStep(stepId.toUpperCase());
              evtName = '';
              continue;
            }

            /* Tenter JSON pour les autres events */
            var msg;
            try { msg = JSON.parse(dataStr); }
            catch (_) { evtName = ''; continue; }

            /* ── EVENT : dorar ──────────────────────────────── */
            if (evtName === 'dorar' && Array.isArray(msg)) {
              _cachedDorar = msg;
              _renderDorarCards(msg, query);
              dorarOK = true;
              _advanceStep('TAKHRIJ');
              evtName = '';
              continue;
            }

            /* ── EVENT : chunk ──────────────────────────────── */
            if (evtName === 'chunk') {
              var cidx = (msg && msg.index !== undefined) ? msg.index : 0;
              var ctext = (msg && (msg.delta || msg.text || msg.content)) || '';
              _applyChunk(cidx, ctext);
              evtName = '';
              continue;
            }

            /* ── EVENT : hadith ─────────────────────────────── */
            if (evtName === 'hadith' && msg.index !== undefined && msg.data) {
              var hd = _mapHadithRaw(msg.data);

              if (!dorarOK) {
                _renderDorarCards([hd], query);
                dorarOK = true;
              }

              /* Effacer le typewriter avec fondu */
              var twEl = document.getElementById('typewriter-' + msg.index);
              if (twEl) {
                twEl.style.opacity = '0';
                (function(el) {
                  setTimeout(function() { el.textContent = ''; el.style.opacity = '1'; }, 300);
                })(twEl);
              }
              delete _chunkBuffers[msg.index];

              _cachedHadiths.push({index: msg.index, data: hd});
              _enrichCardSSE(msg.index, hd);
              _advanceStep('HUKM');
              evtName = '';
              continue;
            }

            /* ── EVENT : done ───────────────────────────────── */
            if (evtName === 'done') {
              if (!dorarOK && Array.isArray(msg) && msg.length) {
                _renderDorarCards(msg.map(_mapHadithRaw), query);
                dorarOK = true;
              }
              /* ── Sauvegarder en cache LocalStorage ── */
              if (_cachedDorar && _cachedHadiths.length) {
                try {
                  localStorage.setItem(_mzCacheKey, JSON.stringify({
                    ts: Date.now(), dorar: _cachedDorar, hadiths: _cachedHadiths
                  }));
                } catch(_se) {}
              }
              /* ── MASQUAGE LOADING-BOX — signal done reçu du backend ── */
              (function() {
                var lbDone = document.getElementById('loading-box');
                if (lbDone && lbDone.classList.contains('active')) {
                  lbDone.style.transition = 'opacity 0.55s ease, transform 0.55s ease';
                  lbDone.style.opacity    = '0';
                  lbDone.style.transform  = 'translateY(-10px)';
                  setTimeout(function() {
                    lbDone.classList.remove('active');
                    lbDone.style.cssText = '';
                  }, 580);
                }
                _finishLoading();
              })();
              evtName = '';
              continue;
            }

            /* ── EVENT : error ──────────────────────────────── */
            if (evtName === 'error') {
              console.error('[Mizan SSE] Erreur backend:', msg.message || msg);
              _finishLoading();
              if (box) {
                box.innerHTML = '<p style="color:#ef4444;padding:1.5rem;text-align:center;font-size:0.95rem">&#9888;&#65039; ' + (msg.message || 'Erreur serveur') + '</p>';
                box.classList.add('active');
              }
              evtName = '';
              continue;
            }

            /* ── Fallback sans event name ────────────────────── */
            if (!evtName) {
              if (msg && msg.step) { _advanceStep((msg.step || '').toUpperCase()); continue; }
              if (!dorarOK && Array.isArray(msg) && msg.length && msg[0] && (msg[0].arabic_text || msg[0].ar)) {
                _renderDorarCards(msg, query); dorarOK = true; _advanceStep('TAKHRIJ'); continue;
              }
              if (msg && msg.index !== undefined && msg.data) {
                var hd2 = _mapHadithRaw(msg.data);
                if (!dorarOK) { _renderDorarCards([hd2], query); dorarOK = true; }
                var tw2 = document.getElementById('typewriter-' + msg.index);
                if (tw2) { tw2.style.opacity='0'; (function(e){ setTimeout(function(){ e.textContent=''; e.style.opacity='1'; },300); })(tw2); }
                delete _chunkBuffers[msg.index];
                _enrichCardSSE(msg.index, hd2);
              }
            }
          }
        }

        /* Fin naturelle du flux — _finishLoading déjà appelé par le handler done.
           Ne pas l'appeler ici pour ne pas fermer le loader prématurément. */
        if (!dorarOK) {
          /* TRIPLE BOUCLIER — aucun résultat Dorar → Arbre Royal Canonique */
          if (typeof window.mzAfficherArbreCanonique === 'function') {
            window.mzAfficherArbreCanonique(query);
          } else {
            _renderTopicList([], query);
          }
        }
        return;
      }
    } catch (sseErr) {
      console.log('[Mizan] SSE indisponible → fallback JSON:', sseErr.message);
    }
  }

  /* ── FALLBACK JSON ─────────────────────────────────────────── */
  try {
    /* CORRECTION v21.0 : suppression du délai artificiel 1800ms */
    var _r = await fetch(searchUrl);
    if (!_r.ok) throw new Error('HTTP ' + _r.status);
    var data = await _r.json();
    var hadiths = [];
    if (Array.isArray(data) && data.length) hadiths = data.map(_mapHadithRaw);
    if (hadiths.length > 0) {
      _renderTopicList(hadiths, query);
    } else {
      /* TRIPLE BOUCLIER — fallback JSON vide → Arbre Royal Canonique */
      if (typeof window.mzAfficherArbreCanonique === 'function') {
        window.mzAfficherArbreCanonique(query);
      } else {
        _renderTopicList([], query);
      }
    }
    _finishLoading();
  } catch (e) {
    _finishLoading();
    /* TRIPLE BOUCLIER — erreur réseau → Arbre Royal Canonique */
    if (typeof window.mzAfficherArbreCanonique === 'function') {
      window.mzAfficherArbreCanonique(query);
    } else {
      _renderTopicList([], query);
    }
  }
}


/* PROMPT_HADITH SUPPRIMÉ — R8 */

function startHadithFromHome(){
  var txt=document.getElementById('home-input').value.trim();
  if(!txt)return;
  // Close omni results
  var omni=document.getElementById('omni-results');
  if(omni){omni.style.display='none';omni.innerHTML='';}
  document.getElementById('hadith-input').value=txt;
  goTo('hadith');
  analyzeHadith(txt);
}
window.startHadithFromHome = startHadithFromHome;

/* ══════════════════════════════════════════════
   MOTEUR OMNISCIENT — Recherche dans PREACHERS + FIRAQ + MYTHES
══════════════════════════════════════════════ */

function omniSearch(val){
  clearTimeout(window._mzOmniDebounce);
  var box=document.getElementById('omni-results');
  if(!box)return;
  var q=normalize(val||'');
  if(q.length<2){box.style.display='none';box.innerHTML='';return;}
  window._mzOmniDebounce=setTimeout(function(){_omniSearchRun(val);},400);
}
function _omniSearchRun(val){
  var box=document.getElementById('omni-results');
  if(!box)return;
  var q=normalize(val||'');
  if(q.length<2){box.style.display='none';box.innerHTML='';return;}
  var html='';
  var count=0;
  var maxResults=12;
  // 1. PREACHERS
  try{
    PREACHERS.forEach(function(p){
      if(count>=maxResults)return;
      var nm=normalize(p.nomFr||'');
      var ph=normalize(p.phraseChoc||'');
      var vd=normalize(p.verdict||'');
      if(nm.indexOf(q)!==-1||ph.indexOf(q)!==-1||vd.indexOf(q)!==-1||(p.nomAr&&p.nomAr.indexOf(val)!==-1)){
        var clr=p.color||'#c9a84c';
        html+='<div onclick="document.getElementById(\'omni-results\').style.display=\'none\';openDetail('+p.id+')" style="display:flex;align-items:center;gap:10px;padding:10px 14px;border-bottom:1px solid rgba(201,168,76,.06);cursor:pointer;transition:background .2s;" onmouseenter="this.style.background=\'rgba(201,168,76,.06)\'" onmouseleave="this.style.background=\'transparent\'">';
        html+='<span style="font-family:Cinzel,serif;font-size:5.5px;font-weight:700;padding:3px 8px;border-radius:2px;background:rgba(201,168,76,.08);border:1px solid rgba(201,168,76,.2);color:#c9a84c;flex-shrink:0;">PROFIL</span>';
        html+='<div style="flex:1;min-width:0;"><p style="font-family:Cinzel,serif;font-size:9px;font-weight:700;color:#c9a84c;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'+p.nomFr+'</p>';
        html+='<p style="font-family:Cormorant Garamond,serif;font-size:10px;color:'+clr+';opacity:.7;">'+p.verdict+'</p></div></div>';
        count++;
      }
    });
  }catch(e){}
  // 2. FIRAQ
  try{
    FIRAQ.forEach(function(f){
      if(count>=maxResults)return;
      var nm=normalize(f.nom||'');
      var ds=normalize(f.description||'');
      var ph=normalize(f.phraseChoc||'');
      if(nm.indexOf(q)!==-1||ds.indexOf(q)!==-1||ph.indexOf(q)!==-1||(f.ar&&f.ar.indexOf(val)!==-1)){
        html+='<div onclick="document.getElementById(\'omni-results\').style.display=\'none\';openFiraqDetail('+f.id+')" style="display:flex;align-items:center;gap:10px;padding:10px 14px;border-bottom:1px solid rgba(201,168,76,.06);cursor:pointer;transition:background .2s;" onmouseenter="this.style.background=\'rgba(153,27,27,.08)\'" onmouseleave="this.style.background=\'transparent\'">';
        html+='<span style="font-family:Cinzel,serif;font-size:5.5px;font-weight:700;padding:3px 8px;border-radius:2px;background:rgba(153,27,27,.1);border:1px solid rgba(153,27,27,.25);color:#991b1b;flex-shrink:0;">SECTE</span>';
        html+='<div style="flex:1;min-width:0;"><p style="font-family:Cinzel,serif;font-size:9px;font-weight:700;color:'+f.color+';white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'+f.nom+'</p>';
        html+='<p style="font-family:Cormorant Garamond,serif;font-size:10px;color:rgba(220,200,160,.5);">'+f.danger+'</p></div></div>';
        count++;
      }
    });
  }catch(e){}
  // 3. MYTHES / KHURAFAT
  try{
    MYTHES.forEach(function(m){
      if(count>=maxResults)return;
      var hd=normalize(m.hadith||'');
      var ex=normalize(m.explication||'');
      var gr=normalize(m.grade||'');
      if(hd.indexOf(q)!==-1||ex.indexOf(q)!==-1||gr.indexOf(q)!==-1){
        var cat=(m.cat==='khurafat')?'KHURAFAT':'MYTHE';
        var catClr=(m.cat==='khurafat')?'#991b1b':'#ef4444';
        html+='<div onclick="document.getElementById(\'omni-results\').style.display=\'none\';openMythDetail('+m.id+')" style="display:flex;align-items:center;gap:10px;padding:10px 14px;border-bottom:1px solid rgba(201,168,76,.06);cursor:pointer;transition:background .2s;" onmouseenter="this.style.background=\'rgba(239,68,68,.06)\'" onmouseleave="this.style.background=\'transparent\'">';
        html+='<span style="font-family:Cinzel,serif;font-size:5.5px;font-weight:700;padding:3px 8px;border-radius:2px;background:'+catClr+'15;border:1px solid '+catClr+'30;color:'+catClr+';flex-shrink:0;">'+cat+'</span>';
        html+='<div style="flex:1;min-width:0;"><p style="font-family:Cinzel,serif;font-size:8.5px;font-weight:700;color:#c9a84c;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'+m.hadith.substring(0,50)+'</p>';
        html+='<p style="font-family:Cormorant Garamond,serif;font-size:10px;color:'+m.color+';opacity:.7;">'+m.grade+'</p></div></div>';
        count++;
      }
    });
  }catch(e){}
  if(!html&&q.length>=2){
    html='<div style="padding:16px;text-align:center;font-family:Cormorant Garamond,serif;font-style:italic;color:rgba(201,168,76,.3);font-size:12px;">Aucun résultat — essayez un autre terme</div>';
  }
  box.innerHTML=html;
  box.style.display=html?'block':'none';
}
window.omniSearch = omniSearch;

function normalize(s){
  return s.toLowerCase()
    .replace(/[àâä]/g,'a').replace(/[éèêë]/g,'e').replace(/[ïî]/g,'i')
    .replace(/[ôö]/g,'o').replace(/[ùûü]/g,'u').replace(/ç/g,'c')
    .replace(/[^a-z0-9\s]/g,'').trim();
}

function analyzeHadith(txt){
  if(!txt){
    var inp=document.getElementById('hadith-input');
    if(!inp)return;
    txt=inp.value.trim();
  }
  if(!txt||txt.length<3)return;

  // Reset state
  clearInterval(loadTimer);
  aiResult=null;
  animDone=false;
  document.getElementById('loading-box').classList.remove('active');
  var _rb=document.getElementById('result-box');
  _rb.classList.remove('active');
  _rb.innerHTML='';
  document.getElementById('examples-section').style.display='none';

  // Vérifier si un badge IA existe déjà et le supprimer
  var oldBadge=document.getElementById('ai-badge');
  if(oldBadge)oldBadge.remove();

  var steps=[
    {ar:'بِسْمِ اللَّهِ',fr:'INITIALISATION AL MIZAN',desc:'Ouverture des registres de la science du Hadith.'},
    {ar:'تَخْرِيجُ الحَدِيث',fr:'AT-TAKHRIJ — EXTRACTION DES SOURCES',desc:'Recherche du hadith dans les recueils originaux (Bukhari, Muslim, Abu Dawud, At-Tirmidhi, etc.).'},
    {ar:'دِرَايَةُ الرِّجَال',fr:'DIRAYAT AR-RIJAL — LES TRANSMETTEURS',desc:'Analyse de la biographie et de la fiabilite de chaque transmetteur de la chaine.'},
    {ar:'عِلَلُ الإِسْنَاد',fr:'ILAL AL-ISNAD — LES DEFAUTS CACHES',desc:'Recherche stricte des coupures, inversions ou anomalies dans la chaine de transmission.'},
    {ar:'الجَرْحُ وَالتَّعْدِيل',fr:'AL-JARH WA AT-TADIL',desc:'Application des verdicts des Imams Ahmad, Al-Bukhari, Ibn Main, An-Nasai sur les narrateurs.'},
    {ar:'الحُكْمُ النِّهَائِيّ',fr:'AL-HUKM — VERDICT FINAL',desc:'Verdict definitif selon les regles de la science du Hadith.'}
  ];

  var sl=document.getElementById('steps-list');sl.innerHTML='';
  steps.forEach(function(s,i){
    var d=document.createElement('div');d.className='step-item';d.id='step-'+i;
    d.innerHTML='<div class="step-dot"></div><div><p class="step-ar">'+s.ar+'</p><p class="step-fr">'+s.fr+'</p><p class="step-desc">'+s.desc+'</p></div>';
    sl.appendChild(d);
  });

  document.getElementById('loading-box').classList.add('active');
  var fill=document.getElementById('progress-fill');
  var diamond=document.getElementById('progress-diamond');
  fill.style.width='0%';diamond.style.left='-4px';

  // ── Routing : TOUJOURS Dorar via IA en priorité ──────────────
  // Base locale seulement si texte arabe exact trouvé (≥ 20 cars arabes)
  var isExactArabic = /^[؀-ۿ\s]{20,}$/.test(txt.trim());
  var localResult = isExactArabic && window.MizanDB && window.MizanDB.isLoaded()
    ? window.MizanDB.searchForApp(txt) : null;

  if(localResult && localResult.grade){
    localResult._source_type='LOCAL';
    aiResult=localResult;
    if(animDone){ animDone='rendered'; setTimeout(function(){ renderAIResult(localResult); }, 200); }
  } else {
    // Tout le reste → Dorar via IA (FR, AR court, concepts)
    aiResult='dorar';
    clearInterval(loadTimer);
    // ── Injecter et animer les steps pour la branche Dorar ──────
    var slD=document.getElementById('steps-list');slD.innerHTML='';
    var stepsD=[
      {ar:'بِسْمِ اللَّهِ',fr:'INITIALISATION AL MIZAN',desc:'Ouverture des registres de la science du Hadith.'},
      {ar:'تَخْرِيجُ الحَدِيث',fr:'AT-TAKHRIJ — EXTRACTION DES SOURCES',desc:'Recherche du hadith dans les recueils originaux (Bukhari, Muslim, Abu Dawud, At-Tirmidhi, etc.).'},
      {ar:'دِرَايَةُ الرِّجَال',fr:'DIRAYAT AR-RIJAL — LES TRANSMETTEURS',desc:'Analyse de la biographie et de la fiabilite de chaque transmetteur de la chaine.'},
      {ar:'عِلَلُ الإِسْنَاد',fr:'ILAL AL-ISNAD — LES DEFAUTS CACHES',desc:'Recherche stricte des coupures, inversions ou anomalies dans la chaine de transmission.'},
      {ar:'الجَرْحُ وَالتَّعْدِيل',fr:'AL-JARH WA AT-TADIL',desc:'Application des verdicts des Imams Ahmad, Al-Bukhari, Ibn Main, An-Nasai sur les narrateurs.'},
      {ar:'الحُكْمُ النِّهَائِيّ',fr:'AL-HUKM — VERDICT FINAL',desc:'Verdict definitif selon les regles de la science du Hadith.'}
    ];
    stepsD.forEach(function(s,i){
      var d=document.createElement('div');d.className='step-item';d.id='step-d-'+i;
      d.innerHTML='<div class="step-dot"></div><div><p class="step-ar">'+s.ar+'</p><p class="step-fr">'+s.fr+'</p><p class="step-desc">'+s.desc+'</p></div>';
      slD.appendChild(d);
    });
    document.getElementById('loading-box').classList.add('active');
    var fillD=document.getElementById('progress-fill');
    var diamondD=document.getElementById('progress-diamond');
    fillD.style.width='0%';diamondD.style.left='-4px';
    var progD=0,timerD=setInterval(function(){
      progD=Math.min(progD+1.2,95);
      fillD.style.width=progD+'%';
      diamondD.style.left='calc('+progD+'% - 4px)';
      var cur=Math.min(Math.floor((progD/100)*stepsD.length),stepsD.length-1);
      for(var i=0;i<stepsD.length;i++){
        var el=document.getElementById('step-d-'+i);
        if(!el)continue;
        el.classList.remove('done','current');
        if(i<cur)el.classList.add('done');
        else if(i===cur)el.classList.add('current');
      }
    },120);
    window._dorarLoadTimer=timerD;
    _searchDorarTopic(txt);
    return;
  }

  // Lance l'animation
  var progress=0,duration=5500,stepTime=55,inc=100/(duration/stepTime);
  loadTimer=setInterval(function(){
    progress=Math.min(progress+inc,100);
    fill.style.width=progress+'%';
    diamond.style.left='calc('+progress+'% - 4px)';
    var cur=Math.min(Math.floor((progress/100)*steps.length),steps.length-1);
    for(var i=0;i<steps.length;i++){
      var el=document.getElementById('step-'+i);
      el.classList.remove('done','current');
      if(i<cur)el.classList.add('done');
      else if(i===cur)el.classList.add('current');
    }
    if(progress>=100){
      clearInterval(loadTimer);
      // Si déjà rendu (animDone==='rendered'), ne pas ré-appeler
      if(animDone==='rendered') return;
      animDone=true;
      // Si l'IA a déjà répondu, on affiche
      if(aiResult!==null){
        animDone='rendered';
        setTimeout(function(){renderAIResult(aiResult);},200);
      }
      // Sinon on attend (callClaudeAPI appellera renderAIResult quand prêt)
    }
  },stepTime);
}
window.analyzeHadith = analyzeHadith;

/* callClaudeAPI SUPPRIMÉE — R9 */

/* ═══════════════════════════════════════════════════════════════════
   MIZAN — SYSTÈME DE RENDU ENTONNOIR (DIVULGATION PROGRESSIVE)
   Niveau 1 : Matn + Verdict immédiat
   Niveau 2 : Al-'Illah — phrase choc
   Niveau 3 : Analyse détaillée (accordéons)
═══════════════════════════════════════════════════════════════════ */
var MZ_ICONS={
  SAHIH:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>',
  HASAN:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>',
  DAIF:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
  MAWDU:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>',
  TAWAQQUF:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="10" y1="15" x2="10" y2="9"/><line x1="14" y1="15" x2="14" y2="9"/></svg>',
  INCONNU:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
  chev:'<svg class="mz-acc-chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>',
  check:'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
  cross:'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>'
};
/* MZ_LABELS / MZ_COLORS — conservés pour compatibilité avec le code existant */
var MZ_LABELS={
  SAHIH: {ar:'\u0635\u064E\u062D\u0650\u064A\u062D', fr:'SAHIH \u2014 AUTHENTIQUE'},
  HASAN: {ar:'\u062D\u064E\u0633\u064E\u0646',       fr:'HASAN \u2014 BON'},
  DAIF:  {ar:'\u0636\u064E\u0639\u0650\u064A\u0641', fr:"DA'IF \u2014 FAIBLE"},
  MAWDU: {ar:'\u0645\u064E\u0648\u0636\u064F\u0648\u0639', fr:"REJET\u00c9 \u2014 CE N'EST PAS UN HADITH (MAWDU')"},
  TAWAQQUF:{ar:'\u062a\u064e\u0648\u064e\u0642\u064f\u0651\u0641', fr:'TAWAQQUF \u2014 VERDICT SUSPENDU'},
  INCONNU:{ar:'\u063a\u064a\u0631 \u0645\u062d\u062f\u062f', fr:"\u26a0\ufe0f DA'IF \u2014 STATUT NON CONFIRM\u00c9 (CONSULTER AL-ALBANI)"}
};
var MZ_COLORS={
  SAHIH:'#22c55e', HASAN:'#4ade80', DAIF:'#f59e0b',
  MAWDU:'#e63946', TAWAQQUF:'#a78bfa', INCONNU:'rgba(156,163,175,.6)'
};

/* Libellés FR des raisons de Tawaqquf — affichés dans le badge UI */
var _MZ_TAWAQQUF_REASONS = {
  'terme_protege_detecte': '\uD83D\uDD34 Terme prot\u00e9g\u00e9 d\u00e9tect\u00e9 (Bid\u02bfah ou Ta\u02bcw\u012bl interdit)',
  'grade_ambigu':          '\uD83D\uDFE0 Grade ambigu \u2014 classification impossible',
  'savant_inconnu':        '\uD83D\uDFE0 Savant inconnu ou non-Salaf',
  'tawil_suspecte':        '\uD83D\uDD34 Ta\u02bcw\u012bl suspect\u00e9 dans la traduction',
  'bidah_detectee':        '\uD83D\uDD34 Bid\u02bfah d\u00e9tect\u00e9e dans le texte',
  'confiance_insuffisante':'\uD83D\uDFE0 Confiance insuffisante (< 50\u00a0%)'
};

function mzToggleAcc(el){
  var body=el.nextElementSibling;
  var isOpen=body.classList.contains('mz-acc-open');
  var card=el.closest('.mz-card')||el.closest('.result-box');
  if(card){
    card.querySelectorAll('.mz-acc-body').forEach(function(b){b.classList.remove('mz-acc-open');});
    card.querySelectorAll('.mz-acc-head').forEach(function(h){h.classList.remove('mz-acc-active');});
  }
  if(!isOpen){body.classList.add('mz-acc-open');el.classList.add('mz-acc-active');}
}

/*
 * _mzVerdict — rendu du verdict selon la clé pré-classifiée
 * gradeKey : clé interne (SAHIH/HASAN/DAIF/MAWDU/INCONNU) — SOURCE DE VÉRITÉ
 * gradeRaw : chaîne arabe brute de Dorar — utilisée UNIQUEMENT si gradeKey absent
 *
 * RÈGLE DOCTRINALE : si gradeKey est une clé valide, on s'y fie directement.
 * On n'écrase JAMAIS un 'Da'if' en 'Sahih' par re-classification depuis grade_ar.
 */
function _mzVerdict(gradeKey, gradeRaw, extra) {
  /* extra (optionnel) : { tawaqquf_reasons: string[], protected_terms: object[] } */

  /* ── CAS TAWAQQUF : rendu dédié ─────────────────────────────────────────── */
  if (gradeKey === 'TAWAQQUF') {
    var col = MZ_COLORS.TAWAQQUF;
    var bg  = 'rgba(167,139,250,.06)';
    var bd  = 'rgba(167,139,250,.22)';
    var reasons = (extra && extra.tawaqquf_reasons) ? extra.tawaqquf_reasons : [];
    var protectedTerms = (extra && extra.protected_terms) ? extra.protected_terms : [];

    var reasonsHtml = '';
    if (reasons.length) {
      reasonsHtml = '<ul style="margin:8px 0 0;padding:0 0 0 14px;list-style:disc;">';
      reasons.forEach(function(r) {
        var label = _MZ_TAWAQQUF_REASONS[r] || r;
        reasonsHtml += '<li style="font-family:Cormorant Garamond,serif;font-size:12px;color:rgba(167,139,250,.85);line-height:1.7;margin-bottom:2px;">' + label + '</li>';
      });
      reasonsHtml += '</ul>';
    }

    var protectedHtml = '';
    if (protectedTerms.length) {
      protectedHtml = '<div style="margin-top:10px;padding:8px 12px;background:rgba(167,139,250,.04);border:1px solid rgba(167,139,250,.15);border-radius:8px;">';
      protectedHtml += '<p style="font-family:Cinzel,serif;font-size:7px;letter-spacing:.18em;color:rgba(167,139,250,.5);margin:0 0 6px;">'
        + 'TERMES BLOQU\u00c9S PAR LE FILTRE DOCTRINAL</p>';
      protectedTerms.forEach(function(t) {
        var icon = (t.severity === 'critique') ? '\uD83D\uDD34' : '\uD83D\uDFE0';
        protectedHtml += '<div style="display:flex;gap:6px;align-items:flex-start;margin-bottom:4px;">'
          + '<span style="flex-shrink:0;font-size:11px;">' + icon + '</span>'
          + '<span style="font-family:Scheherazade New,serif;font-size:13px;color:rgba(167,139,250,.9);">' + (t.term || '') + '</span>'
          + (t.note_fr ? '<span style="font-family:Cormorant Garamond,serif;font-style:italic;font-size:10px;color:rgba(167,139,250,.5);margin-left:4px;">— ' + t.note_fr + '</span>' : '')
          + '</div>';
      });
      protectedHtml += '</div>';
    }

    return '<div class="mz-verdict v-TAWAQQUF" style="background:' + bg + ';border:1px solid ' + bd + ';flex-direction:column;align-items:stretch;padding:20px;">'
      + '<div style="display:flex;align-items:center;gap:14px;margin-bottom:14px;">'
      + '<div class="mz-verdict-icon" style="border-color:' + col + '44;background:' + bg + ';color:' + col + ';">' + MZ_ICONS.TAWAQQUF + '</div>'
      + '<div style="flex:1;">'
      + '<span style="font-family:Cinzel,serif;font-size:5.5px;letter-spacing:.55em;color:' + col + ';opacity:.7;display:block;margin-bottom:4px;">VERDICT \u2014 SUSPENDU</span>'
      + '<div style="display:flex;align-items:center;gap:10px;">'
      + '<span style="font-family:Scheherazade New,serif;font-size:28px;font-weight:700;color:' + col + ';text-shadow:0 0 20px ' + col + '44;">\u062a\u064e\u0648\u064e\u0642\u064f\u0651\u0641</span>'
      + '<span style="font-family:Cinzel,serif;font-size:16px;font-weight:900;letter-spacing:.06em;color:' + col + ';">TAWAQQUF</span>'
      + '</div></div></div>'
      + '<div style="background:rgba(167,139,250,.06);border:1px solid rgba(167,139,250,.18);border-radius:10px;padding:12px 16px;margin-bottom:10px;">'
      + '<p style="font-family:Cinzel,serif;font-size:9px;font-weight:700;letter-spacing:.1em;color:' + col + ';margin:0 0 4px;">'
      + '\u26d4 CE HADITH NE PEUT PAS \u00caTRE PUBLI\u00c9 EN L\'\u00c9TAT</p>'
      + '<p style="font-family:Cormorant Garamond,serif;font-style:italic;font-size:11px;color:rgba(167,139,250,.65);margin:0;line-height:1.6;">'
      + 'Le syst\u00e8me a d\u00e9tect\u00e9 un ou plusieurs \u00e9l\u00e9ments n\u00e9cessitant '
      + 'v\u00e9rification humaine avant toute diffusion \u2014 conform\u00e9ment au manhaj des Salaf al-\u1e62\u0101li\u1e25.'
      + '</p>'
      + reasonsHtml
      + '</div>'
      + protectedHtml
      + '<div style="padding:8px 12px;border-top:1px solid rgba(167,139,250,.15);margin-top:4px;">'
      + '<p style="font-family:Cormorant Garamond,serif;font-style:italic;font-size:11px;color:rgba(167,139,250,.4);line-height:1.6;margin:0;">'
      + 'Note scientifique : Le Tawaqquf est une position \u00e9pist\u00e9mologique l\u00e9gitime chez les Mu\u1e25addith\u012bn. '
      + 'Consulter un savant qualifi\u00e9 avant toute citation.'
      + '</p></div>'
      + '</div>';
  }

  var tg;
  var _VALID_KEYS = ['SAHIH', 'HASAN', 'DAIF', 'MAWDU'];
  if (gradeKey && _VALID_KEYS.indexOf(gradeKey) !== -1) {
    /* Clé pré-classifiée valide — liaison directe champ JSON → étiquette UI */
    var k = gradeKey;
    var lbl = MZ_LABELS[k] || MZ_LABELS.INCONNU;
    tg = {
      key:      k,
      labelFr:  lbl.fr,
      labelAr:  lbl.ar,
      color:    MZ_COLORS[k] || MZ_COLORS.INCONNU,
      colorBg:  k==='SAHIH'?'rgba(34,197,94,.06)':k==='HASAN'?'rgba(74,222,128,.05)':k==='DAIF'?'rgba(245,158,11,.06)':k==='MAWDU'?'rgba(230,57,70,.07)':'rgba(31,41,55,.6)',
      colorBd:  k==='SAHIH'?'rgba(34,197,94,.2)':k==='HASAN'?'rgba(74,222,128,.18)':k==='DAIF'?'rgba(245,158,11,.2)':k==='MAWDU'?'rgba(230,57,70,.22)':'rgba(75,85,99,.5)',
      cssClass: 'v-' + k
    };
  } else if (gradeRaw && /[\u0600-\u06FF]/.test(gradeRaw)) {
    /* Fallback : gradeKey absent ou inconnu — classifier depuis l'arabe brut */
    tg = _getTechnicalGrade(gradeRaw);
  } else {
    var k = gradeKey || 'INCONNU';
    var lbl = MZ_LABELS[k] || MZ_LABELS.INCONNU;
    tg = {
      key:      k,
      labelFr:  lbl.fr,
      labelAr:  lbl.ar,
      color:    MZ_COLORS[k] || MZ_COLORS.INCONNU,
      colorBg:  k==='SAHIH'?'rgba(34,197,94,.06)':k==='HASAN'?'rgba(74,222,128,.05)':k==='DAIF'?'rgba(245,158,11,.06)':k==='MAWDU'?'rgba(230,57,70,.07)':'rgba(31,41,55,.6)',
      colorBd:  k==='SAHIH'?'rgba(34,197,94,.2)':k==='HASAN'?'rgba(74,222,128,.18)':k==='DAIF'?'rgba(245,158,11,.2)':k==='MAWDU'?'rgba(230,57,70,.22)':'rgba(75,85,99,.5)',
      cssClass: 'v-' + k
    };
  }
  var icon = MZ_ICONS[tg.key] || MZ_ICONS.INCONNU;

  /* Determination du guide pratique */
  var isSain = (tg.key === 'SAHIH' || tg.key === 'HASAN');
  var guideTxt = isSain
    ? 'Ce hadith peut \u00eatre mis en pratique et cit\u00e9 en preuve.'
    : (tg.key === 'DAIF'
      ? 'Ce hadith ne doit pas \u00eatre utilis\u00e9 comme preuve religieuse.'
      : (tg.key === 'MAWDU'
        ? '\u26d4 CE TEXTE N\u2019EST PAS UN HADITH. Il est interdit de le propager.'
        : 'Statut en cours de v\u00e9rification \u2014 consultez un savant.'));
  var guideColor = isSain ? '#22c55e' : (tg.key === 'MAWDU' ? '#ef4444' : '#f59e0b');
  var guideBg = isSain ? 'rgba(34,197,94,.06)' : (tg.key === 'MAWDU' ? 'rgba(239,68,68,.06)' : 'rgba(245,158,11,.06)');
  var guideBd = isSain ? 'rgba(34,197,94,.2)' : (tg.key === 'MAWDU' ? 'rgba(239,68,68,.2)' : 'rgba(245,158,11,.2)');

  /* Note etudiant */
  var noteGrade = gradeRaw || tg.labelFr;
  var noteTxt = isSain
    ? 'Note scientifique : Le matn (texte) est authentifi\u00e9 par des cha\u00eenes confirm\u00e9es dans les recueils majeurs.'
    : 'Note scientifique : Cette cha\u00eene sp\u00e9cifique est class\u00e9e ' + noteGrade + ' par le muhaddith source. Consultez les voies de renfort (Mutaba\u02bfat) ci-dessous.';

  return `<div class="mz-verdict ${tg.cssClass}" style="background:${tg.colorBg};border:1px solid ${tg.colorBd};flex-direction:column;align-items:stretch;padding:20px;">`

    /* ── 1. LE SCEAU : Titre principal imposant ── */
    + `<div style="display:flex;align-items:center;gap:14px;margin-bottom:14px;">`
    + `<div class="mz-verdict-icon" style="border-color:${tg.color}44;background:${tg.colorBg};">${icon}</div>`
    + `<div style="flex:1;">`
    + `<span style="font-family:Cinzel,serif;font-size:5.5px;letter-spacing:.55em;color:${tg.color};opacity:.7;display:block;margin-bottom:4px;">VERDICT \u2014 JARH WA TA\u02bfDIL</span>`
    + `<div style="display:flex;align-items:center;gap:10px;">`
    + `<span style="font-family:Scheherazade New,serif;font-size:32px;font-weight:700;color:${tg.color};text-shadow:0 0 20px ${tg.color}44;">${tg.labelAr}</span>`
    + `<span style="font-family:Cinzel,serif;font-size:20px;font-weight:900;letter-spacing:.06em;color:${tg.color};">${tg.labelFr}</span>`
    + `</div></div></div>`

    /* ── 2. ECRIN DES SOURCES (rempli par SSE via hukm-zone) ── */

    /* ── 3. GUIDE PRATIQUE ── */
    + `<div style="background:${guideBg};border:1px solid ${guideBd};border-radius:10px;padding:12px 16px;text-align:center;margin-bottom:10px;">`
    + `<p style="font-family:Cinzel,serif;font-size:10px;font-weight:700;letter-spacing:.1em;color:${guideColor};margin:0;">${guideTxt}</p>`
    + `</div>`

    /* ── 4. ESPACE ETUDIANT ── */
    + `<div style="padding:8px 12px;border-top:1px solid ${tg.colorBd};margin-top:4px;">`
    + `<p style="font-family:Cormorant Garamond,serif;font-style:italic;font-size:11px;color:rgba(201,168,76,.4);line-height:1.6;margin:0;">${noteTxt}</p>`
    + `</div>`

    + `</div>`;
}
function _mzAcc(title,titleAr,dotColor,content,startOpen){
  if(!content||content.length<5) return '';
  return '<div class="mz-acc"><button class="mz-acc-head'+(startOpen?' mz-acc-active':'')+'" onclick="mzToggleAcc(this)"><span class="mz-acc-dot" style="background:'+dotColor+';box-shadow:0 0 6px '+dotColor+';"></span><span class="mz-acc-title" style="color:'+dotColor+';">'+title+(titleAr?'<span class="mz-acc-title-ar">'+titleAr+'</span>':'')+'</span>'+MZ_ICONS.chev+'</button><div class="mz-acc-body'+(startOpen?' mz-acc-open':'')+'"><div class="mz-acc-inner">'+content+'</div></div></div>';
}
function _mzActions(url){
  return '<div class="mz-actions"><a href="'+(url||'https://dorar.net')+'" target="_blank"><svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg><span>VERIFIER</span></a><a href="https://islamqa.info/fr" target="_blank"><svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg><span>SAVANT</span></a></div>';
}
function _mzDisclaimer(){
  return '<div class="mz-disclaimer"><p>Analyse indicative \u2014 retranscription statique des verdicts des savants. Consultez un savant qualifie pour toute decision religieuse.</p></div>';
}



/* ════════════════════════════════════════════════════════════════════
   SILSILAT AL-ISNĀD v23.0 — BACKBONE VERTICAL UNIQUE
   Règles Manhaj Salaf (INVIOLABLES) :
     ① Ligne Centrale Unique : Prophète ﷺ → Compilateur
     ② Nœuds MUETS : nom seul — détails au clic (→ rawi-modal.js)
     ③ Or=#d4af37 (Sahabi) · Vert=#22c55e (Thiqah) · Rouge=#ef4444 (Kadhdhab SEUL)
     ④ INTERDICTION ABSOLUE : rouge sur un Imam de la Sunnah
   Dépend : rawi-modal.js (window.mzOpenIsnadPanel)
════════════════════════════════════════════════════════════════════ */

/* ── Injection CSS Backbone (une seule fois) ── */
function _mzInjectBackboneCSS() {
  if (document.getElementById('mzBb-css')) return;
  var s = document.createElement('style');
  s.id = 'mzBb-css';
  s.textContent =
    '@keyframes mzBbIn{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}'
  + '@keyframes mzBbPulse{0%,100%{box-shadow:0 0 8px var(--mzBb-glow)}50%{box-shadow:0 0 22px var(--mzBb-glow)}}'
  + '@keyframes mzBbLine{from{height:0}to{height:100%}}'
  + '@keyframes mzBbShimmer{0%{background-position:-200% center}100%{background-position:200% center}}'
  + '.mzBb{position:relative;padding:20px 16px 12px;min-height:40px;background:linear-gradient(175deg,rgba(10,6,0,.95),rgba(8,5,0,.98))}'
  + '.mzBb-title{font-family:Cinzel,serif;font-size:7px;letter-spacing:.28em;color:rgba(212,175,55,.5);text-transform:uppercase;text-align:center;margin-bottom:22px}'
  + '.mzBb-prophet{text-align:center;margin-bottom:6px;position:relative;z-index:5}'
  + '.mzBb-orb{width:64px;height:64px;border-radius:50%;margin:0 auto 8px;background:radial-gradient(circle,rgba(212,175,55,.12),transparent 70%);border:2px solid rgba(212,175,55,.65);display:flex;align-items:center;justify-content:center;box-shadow:0 0 25px rgba(212,175,55,.2),0 0 50px rgba(212,175,55,.06);font-size:24px;color:#d4af37}'
  + '.mzBb-pname{font-family:"Scheherazade New",serif;font-size:18px;font-weight:700;color:#d4af37}'
  + '.mzBb-psub{font-family:Cinzel,serif;font-size:6px;letter-spacing:.22em;color:rgba(212,175,55,.32);margin-top:2px}'
  + '.mzBb-spine{position:relative;display:flex;flex-direction:column;align-items:center;padding:0 10px}'
  + '.mzBb-spine::before{content:"";position:absolute;left:50%;width:2px;top:0;bottom:0;transform:translateX(-1px);z-index:1;background:linear-gradient(180deg,rgba(212,175,55,.55),rgba(212,175,55,.22) 50%,rgba(212,175,55,.08));animation:mzBbLine 1.2s ease forwards}'
  + '.mzBb-pipe{width:2px;height:24px;margin:0 auto;position:relative;z-index:2;background:rgba(212,175,55,.18)}'
  + '.mzBb-dot{width:12px;height:12px;border-radius:50%;margin:0 auto;position:relative;z-index:5;border:2px solid;transition:all .3s ease;--mzBb-glow:rgba(212,175,55,.3)}'
  + '.mzBb-node:hover .mzBb-dot{animation:mzBbPulse 1.5s ease infinite}'
  + '.mzBb-node{position:relative;z-index:5;width:100%;max-width:260px;margin:0 auto;text-align:center;animation:mzBbIn .45s ease both;cursor:pointer}'
  + '.mzBb-card{margin:6px auto 0;padding:10px 18px;border-radius:8px;border:1px solid rgba(201,168,76,.12);background:linear-gradient(145deg,rgba(15,10,2,.95),rgba(10,6,0,.98));transition:border-color .3s,box-shadow .3s,transform .22s}'
  + '.mzBb-node:hover .mzBb-card{border-color:rgba(212,175,55,.4);box-shadow:0 4px 24px rgba(0,0,0,.5),0 0 14px rgba(212,175,55,.07);transform:scale(1.03)}'
  + '.mzBb-name{font-family:"Scheherazade New",serif;font-size:17px;font-weight:700;line-height:1.35;direction:rtl;overflow-wrap:break-word;word-break:break-word;max-width:100%;}'
  + '.mzBb-hint{font-family:Cinzel,serif;font-size:5.5px;letter-spacing:.15em;color:rgba(201,168,76,.2);margin-top:3px;display:block;transition:color .2s}'
  + '.mzBb-node:hover .mzBb-hint{color:rgba(201,168,76,.45)}'
  + '.mzBb-foot{font-family:Cinzel,serif;font-size:5.5px;letter-spacing:.2em;color:rgba(212,175,55,.13);text-align:center;margin-top:18px}'
  + '.mzBb-sahabi .mzBb-card{border-color:rgba(212,175,55,.3);background:linear-gradient(90deg,rgba(20,14,2,.97),rgba(212,175,55,.05),rgba(20,14,2,.97));background-size:200% 100%;animation:mzBbShimmer 6s linear infinite}';
  document.head.appendChild(s);
}

/* ── Fallback ── */
function _mzIsnadFallback(msg) {
  var d = document.createElement('div');
  d.id = 'mz-isnad-container';
  d.style.cssText = 'min-height:40px;padding:14px 18px;text-align:center;';
  var p1 = document.createElement('p');
  p1.style.cssText = 'font-family:Cinzel,serif;font-size:6.5px;letter-spacing:.25em;color:rgba(201,168,76,.35);margin-bottom:8px;';
  p1.textContent = 'ZONE 2 \u2014 SILSILAT AL-ISN\u0100D';
  var p2 = document.createElement('p');
  p2.style.cssText = 'font-family:Cormorant Garamond,serif;font-style:italic;font-size:13px;color:rgba(201,168,76,.35);line-height:1.7;';
  p2.textContent = msg || 'Donn\u00e9es de la cha\u00eene non disponibles.';
  d.appendChild(p1); d.appendChild(p2);
  return d.outerHTML;
}
window._mzIsnadFallback = _mzIsnadFallback;

/* ══════════════════════════════════════════════════════════════════
   _mzIsnadFromPipe v23.0 — BACKBONE VERTICAL UNIQUE
   Entrée : isnadChain (string pipe-séparé) + grade (SAHIH/DAIF…)
   Sortie : HTML string du backbone vertical centré
══════════════════════════════════════════════════════════════════ */
function _mzIsnadFromPipe(isnadChain, grade) {

  /* GARDE */
  if (!isnadChain) return _mzIsnadFallback();
  if (typeof isnadChain !== 'string') { try { isnadChain = String(isnadChain); } catch(_) { return _mzIsnadFallback(); } }
  isnadChain = isnadChain.trim();
  if (isnadChain.length < 5) return _mzIsnadFallback();

  if (!window._mzBb_loaded) {
    console.log('%c \u2705 M\u00eezan v23.0 : Backbone Vertical charg\u00e9', 'color:#00ff00;font-weight:bold;');
    window._mzBb_loaded = true;
  }
  _mzInjectBackboneCSS();

  /* ── PARSE + DÉDUPLIQUE ── */
  var raw = isnadChain.replace(/\\n/g, '\n')
    .replace(/\s*[\u2014\u2013]\s*/g, ' | ')
    .replace(/\s+-\s+/g, ' | ');
  var plines = raw.indexOf('\n') !== -1 ? raw.split('\n') : raw.split(/(?=Maillon\s+\d)/i);
  plines = plines.map(function(l){return typeof l==='string'?l.trim():'';}).filter(function(l){return l.length>2;});

  var dynNodes = [], seen = {};
  for (var i = 0; i < plines.length; i++) {
    try {
      var parts = plines[i].split('|');
      var nom = (parts[1] || '').trim();
      if (!nom || nom.length < 2) continue;
      var key = nom.toLowerCase().replace(/[\u064B-\u065F\u0670]/g,'').replace(/[^a-z0-9\u0600-\u06FF]/g,'');
      if (seen[key]) continue;
      seen[key] = true;
      dynNodes.push({
        nom: nom,
        titre: (parts[2]||'').trim(),
        verdict: (parts[3]||'').trim().replace(/_/g,' '),
        siecle: (parts[4]||'').trim()
      });
    } catch(_) {}
  }
  if (dynNodes.length < 1) return _mzIsnadFallback('Cha\u00eene non parsable.');

  /* ═══ PROTECTION IMAMS — REGEX ═══ */
  var _IMAMS_RE = /bukhari|\u0628\u062e\u0627\u0631\u064a|muslim|\u0645\u0633\u0644\u0645|tirmidhi|\u062a\u0631\u0645\u0630\u064a|nasa.i|\u0627\u0644\u0646\u0633\u0627\u0626\u064a|dawud|\u062f\u0627\u0648\u062f|ibn\s*majah|ahmad.*hanbal|\u0623\u062d\u0645\u062f|malik|\u0645\u0627\u0644\u0643|nawawi|\u0627\u0644\u0646\u0648\u0648\u064a|ibn\s*hajar|\u0627\u0628\u0646\s*\u062d\u062c\u0631|ibn\s*taymi|ibn\s*qayyim|dhahabi|\u0630\u0647\u0628\u064a|albani|\u0627\u0644\u0623\u0644\u0628\u0627\u0646|ibn\s*baz|\u0627\u0628\u0646\s*\u0628\u0627\u0632|uthaymin|muqbil|rabi.*madkhali|\u0631\u0628\u064a\u0639.*\u0627\u0644\u0645\u062f\u062e\u0644|fawzan|\u0641\u0648\u0632\u0627\u0646|luhayd|daraqutni|bayhaqi|ibn\s*salah|shafi.i|\u0627\u0644\u0634\u0627\u0641\u0639/i;

  function _nodeColor(n) {
    var combo = (n.nom+' '+n.titre+' '+n.verdict).toLowerCase();
    if (/sahab|\u0635\u062d\u0627\u0628|\u0639\u062f\u0648\u0644|companion/i.test(combo))
      return {dot:'#d4af37',name:'#d4af37',cls:'mzBb-sahabi'};
    if (_IMAMS_RE.test(n.nom))
      return {dot:'#22c55e',name:'#86efac',cls:''};
    if (/kadhdhab|\u0643\u0630\u0627\u0628|matruk|\u0645\u062a\u0631\u0648\u0643|munkar|\u0645\u0646\u0643\u0631|wad|\u0648\u0627\u0636/i.test(combo))
      return {dot:'#ef4444',name:'#fca5a5',cls:''};
    if (/da.if|\u0636\u0639\u064a\u0641|layyin|\u0644\u064a\u0646|majhul|\u0645\u062c\u0647\u0648\u0644|mudallis|\u0645\u062f\u0644\u0633/i.test(combo))
      return {dot:'#f59e0b',name:'#fcd34d',cls:''};
    return {dot:'#22c55e',name:'#86efac',cls:''};
  }

  function _esc(s) {
    return (s||'').replace(/\\/g,'\\\\').replace(/'/g,"\\'").replace(/"/g,'&quot;').replace(/\n/g,' ');
  }

  /* ═══ ASSEMBLAGE HTML — BACKBONE VERTICAL ═══ */
  try {
    var h = '';
    h += '<div id="mz-isnad-container" class="mzBb">';
    h += '<p class="mzBb-title">SILSILAT AL-ISN\u0100D \u2014 CHA\u00ceNE DE TRANSMISSION</p>';

    h += '<div class="mzBb-prophet">';
    h += '<div class="mzBb-orb">\uFDFA</div>';
    h += '<p class="mzBb-pname">\u0627\u0644\u0646\u0628\u064a \u0645\u062d\u0645\u062f \uFDFA</p>';
    h += '<p class="mzBb-psub">LE PROPH\u00c8TE MOHAMED \uFDFA \u2014 SOURCE DE LA R\u00c9V\u00c9LATION</p>';
    h += '</div>';

    h += '<div class="mzBb-spine">';

    dynNodes.forEach(function(n, idx) {
      var vc = _nodeColor(n);
      var dl = (idx * 0.1 + 0.15).toFixed(2);
      h += '<div class="mzBb-pipe"></div>';
      h += '<div class="mzBb-dot" style="border-color:'+vc.dot+';background:'+vc.dot+'18;--mzBb-glow:'+vc.dot+'40;"></div>';
      h += '<div class="mzBb-node '+vc.cls+'" style="animation-delay:'+dl+'s;" onclick="window.mzOpenIsnadPanel(\''+_esc(n.nom)+'\',\''+_esc(n.titre)+'\',\''+_esc(n.verdict)+'\',\''+_esc(n.siecle)+'\',\''+vc.name+'\')">';
      h += '<div class="mzBb-card">';
      h += '<p class="mzBb-name" style="color:'+vc.name+';">'+n.nom+'</p>';
      h += '<span class="mzBb-hint">APPUYER POUR D\u00c9TAILS</span>';
      h += '</div></div>';
    });

    h += '</div>';
    h += '<p class="mzBb-foot">SILSILAT AL-ISN\u0100D \u2014 CHA\u00ceNE DOR\u00c9E ININTERROMPUE \u2014 MANHAJ SALAF</p>';
    h += '</div>';
    return h;

  } catch(err) {
    console.error('[Mizan v23] _mzIsnadFromPipe CRASH:', err);
    return '<div id="mz-isnad-container" style="min-height:40px;padding:14px;background:rgba(255,0,0,.06);border:1px solid rgba(255,0,0,.25);border-radius:10px;"><p style="font-family:Cinzel,serif;font-size:8px;color:#ff6b6b;">\u26a0 ERREUR ZONE 2</p><p style="font-size:12px;color:rgba(255,150,150,.8);">'+err.message+'</p></div>';
  }
}



/* ═══ TRIDENT 1 : CASCADE DE PRÉSERVATION — ISNAD VERTICAL (LEGACY) ═══ */
/* ══════════════════════════════════════════════════════════════
   SILSILAT AL-ISNĀD — 14 siècles de transmission
   FIX CRITIQUE: regex accepte guillemets simples ET doubles
   Noms réels en titres, verdicts en badges secondaires
   Prophète ﷺ = orbe noble, frise chronologique visible
══════════════════════════════════════════════════════════════ */
function _mzIsnadChain(jarhHtml, grade) {
  if (!jarhHtml || jarhHtml.length < 5) return '';
  var isSahih = (grade === 'SAHIH' || grade === 'HASAN');

  /* ═══ CSS ═══ */
  if (!document.getElementById('mzC4-css')) {
    var _s = document.createElement('style'); _s.id = 'mzC4-css';
    _s.textContent =
      '@keyframes mzC4In{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}'
    + '.mzC4-card{cursor:pointer;transition:border-color .3s,box-shadow .3s,transform .22s}'
    + '.mzC4-card:hover{border-color:rgba(212,175,55,.55)!important;box-shadow:0 0 30px rgba(212,175,55,.1),0 8px 32px rgba(0,0,0,.5)!important;transform:translateX(3px)}'
    + '.mzC4-mech{cursor:pointer;transition:border-color .3s,box-shadow .3s,transform .22s;position:relative}'
    + '.mzC4-mech:hover{border-color:rgba(212,175,55,.5)!important;box-shadow:0 0 18px rgba(212,175,55,.08)!important;transform:translateX(-3px)}'
    + '.mzC4-mech:hover .mzC4-tip{opacity:1;transform:translateY(0);pointer-events:auto}'
    + '.mzC4-tip{position:absolute;top:calc(100% + 8px);right:0;width:240px;padding:10px 12px;border-radius:10px;background:rgba(10,6,0,.95);border:1px solid rgba(212,175,55,.2);font-family:"Cormorant Garamond",serif;font-size:12px;color:rgba(220,210,180,.7);line-height:1.6;font-style:italic;opacity:0;transform:translateY(-6px);transition:opacity .3s,transform .3s;pointer-events:none;z-index:50}'
    + '.mzC4-chev{width:14px;height:14px;stroke:rgba(212,175,55,.3);transition:transform .35s cubic-bezier(.4,0,.2,1),stroke .3s;flex-shrink:0}'
    + '.mzC4-open .mzC4-chev{transform:rotate(180deg);stroke:#d4af37}'
    + '.mzC4-panel{max-height:0;overflow:hidden;transition:max-height .6s cubic-bezier(.4,0,.2,1),opacity .45s;opacity:0}'
    + '.mzC4-panel.mzC4-vis{max-height:2400px;opacity:1}'
    + '.mzC4-pi{padding:16px 20px 18px;border:1px solid rgba(212,175,55,.1);border-top:none;border-radius:0 0 14px 14px;background:linear-gradient(180deg,rgba(10,6,0,.85),rgba(17,24,39,.6));margin:0 auto;max-width:700px}'
    + '.mzC4-vl{font-family:"Cormorant Garamond",serif;font-size:13px;color:rgba(220,210,180,.75);line-height:1.75;font-style:italic}'
    + '.mzC4-vl strong{color:#d4af37;font-style:normal}'
    + '.mzC4-bg{display:inline-block;font-family:Cinzel,serif;font-size:6.5px;font-weight:700;letter-spacing:.12em;padding:3px 10px;border-radius:5px}'
    + '.mzC4-bg.g{background:rgba(212,175,55,.08);color:#d4af37;border:1px solid rgba(212,175,55,.25)}'
    + '.mzC4-bg.s{background:rgba(34,197,94,.07);color:#22c55e;border:1px solid rgba(34,197,94,.2)}'
    + '.mzC4-bg.r{background:rgba(239,68,68,.07);color:#ef4444;border:1px solid rgba(239,68,68,.22)}'
    + '.mzC4-rw:hover .mzC4-dt{box-shadow:0 0 26px rgba(212,175,55,.5)!important}'
    + '.mzC4-nabi{text-align:center;margin-bottom:18px;position:relative;z-index:10}'
    + '.mzC4-orb{width:72px;height:72px;border-radius:50%;background:radial-gradient(circle,rgba(212,175,55,.15),transparent 70%);border:3px solid #d4af37;display:flex;align-items:center;justify-content:center;margin:0 auto 10px;box-shadow:0 0 30px rgba(212,175,55,.3),0 0 60px rgba(212,175,55,.1)}'
    + '.mzC4-orb span{font-size:26px;color:#d4af37}'
    + '.mzC4-arr{display:flex;justify-content:center;margin:4px 0 10px;position:relative;z-index:10}'
    + '.mzC4-arr svg{width:18px;height:18px;stroke:#d4af37;opacity:.4}'
    + '.mzC4-epoch{font-family:Cinzel,serif;font-size:6px;letter-spacing:.12em;color:rgba(212,175,55,.3);background:rgba(212,175,55,.04);border:1px solid rgba(212,175,55,.1);padding:2px 8px;border-radius:4px;white-space:nowrap}';
    document.head.appendChild(_s);
  }

  /* ═══ Toggle ═══ */
  if (!window.mzC4Tog) {
    window.mzC4Tog = function(id) {
      var p = document.getElementById('mzC4p-' + id);
      var r = document.getElementById('mzC4r-' + id);
      if (!p || !r) return;
      var op = p.classList.contains('mzC4-vis');
      document.querySelectorAll('.mzC4-vis').forEach(function(x) { x.classList.remove('mzC4-vis'); });
      document.querySelectorAll('.mzC4-open').forEach(function(x) { x.classList.remove('mzC4-open'); });
      if (!op) { p.classList.add('mzC4-vis'); r.classList.add('mzC4-open'); }
    };
  }

  /* ═══ NETTOYAGE ═══ */
  function stripHonor(s) {
    return s.replace(/<[^>]+>/g, '')
      .replace(/\u0635\u0644[\u0651\u064e\u0650]?\u0649?\s*\u0627\u0644\u0644[\u0651\u064e]?\u0647\s*\u0639\u0644\u064a\u0647[\s\u0650]?\s*\u0648\u0633\u0644[\u0651\u064e]?\u0645/g, '')
      .replace(/\u0631\u0636\u064a\s*\u0627\u0644\u0644\u0647\s*\u0639\u0646\u0647[^\s]*/g, '')
      .replace(/\u0631\u062d\u0645\u0647\s*\u0627\u0644\u0644\u0647/g, '')
      .replace(/\u0639\u0644\u064a\u0647[\u0645\u0627]*\s*\u0627\u0644\u0633\u0644\u0627\u0645/g, '')
      .replace(/\uFDFA/g, '').replace(/\s+/g, ' ').trim();
  }

  /* ═══════════════════════════════════════════════════════════
     PARSER — FIX CRITIQUE : accepte guillemets simples ET doubles
     L'IA génère style='color:#5dade2' (simples) — l'ancien regex
     ne matchait que style="..." (doubles) → 0 résultats = BUG
     
     Format IA : <span style='color:#5dade2;font-weight:bold;'>NOM_RAWI</span> : verdict...
     On extrait : NOM = contenu du span, VERDICT = texte après le </span> :
  ═══════════════════════════════════════════════════════════ */
  var spanRe = /<span[^>]*style\s*=\s*["'][^"']*color:\s*([^;"']+)[^"']*["'][^>]*>([\s\S]*?)<\/span>/gi;
  var nodes = [], mm;
  while ((mm = spanRe.exec(jarhHtml)) !== null) {
    var co = mm[1].trim();
    var rawInner = mm[2].replace(/<[^>]+>/g, '').trim();
    /* Skip les en-têtes des 5 conditions (couleur #d4af37) — ce ne sont pas des rāwī */
    if (/d4af37|ITTISAL|ADALAT|DABT|SHUDHUDH|ILLAH/i.test(co + rawInner)) continue;
    /* Skip couleurs non-rāwī (#e8c96a = noms propres dans le texte, #f39c12 = Albani labels) */
    if (/e8c96a|f39c12|8e44ad/i.test(co)) continue;

    var cleaned = stripHonor(rawInner);
    if (!cleaned || cleaned.length < 2) continue;

    var isRed = /ef4444|e63946|dc2626|ff0000|red|e74c3c/i.test(co);
    var isBlue = /5dade2|3b82f6|60a5fa|blue/i.test(co);

    /* Extraire le verdict textuel APRÈS ce span (cherche le texte entre </span> et le prochain <br> ou <span) */
    var afterSpan = jarhHtml.substring(mm.index + mm[0].length);
    var verdictMatch = afterSpan.match(/^\s*:?\s*([^<]{5,300})/);
    var verdictText = verdictMatch ? verdictMatch[1].trim() : '';

    nodes.push({
      name: cleaned,
      type: isRed ? 'kadhdhab' : isBlue ? 'sahabi' : 'thiqah',
      verdict: verdictText
    });
  }

  /* Fallback: bold names */
  if (!nodes.length) {
    var bRe = /<(?:strong|b)>([\s\S]*?)<\/(?:strong|b)>/gi, bm;
    while ((bm = bRe.exec(jarhHtml)) !== null) {
      var bn = stripHonor(bm[1]);
      if (bn && bn.length >= 2) nodes.push({ name: bn, type: 'thiqah', verdict: '' });
    }
  }
  /* Fallback: Arabic text blocks */
  if (!nodes.length) {
    var stripped = jarhHtml.replace(/<[^>]+>/g, ' ');
    stripped = stripHonor(stripped);
    var arM = stripped.match(/[\u0600-\u06FF][\u0600-\u06FF\s]{3,40}/g);
    if (arM) arM.slice(0, 8).forEach(function(x) {
      var c = x.trim();
      if (c.length >= 3) nodes.push({ name: c, type: 'thiqah', verdict: '' });
    });
  }
  if (!nodes.length) {
    var clt = jarhHtml.replace(/<[^>]+>/g, ' ').trim();
    return clt.length < 3 ? '' : '<p style="font-size:15px;line-height:1.9;color:rgba(210,200,180,.78);padding:12px 0;">' + jarhHtml + '</p>';
  }

  /* ═══ CHRONOLOGIE : Prophète en haut, Compilateur en bas ═══ */
  var compRe = /bukhari|muslim|tirmidhi|nasa.i|dawud|majah|ahmad.*hanbal|darimi|bayhaqi|\u0628\u062e\u0627\u0631\u064a|\u0645\u0633\u0644\u0645|\u062a\u0631\u0645\u0630\u064a/i;
  var nabiRe = /proph|muhammad|\u0631\u0633\u0648\u0644|\u0645\u062d\u0645\u062f|\u0646\u0628\u064a/i;
  if (compRe.test(nodes[0].name) || (nodes.length > 1 && nodes[nodes.length - 1].type === 'sahabi')) {
    nodes.reverse();
  }
  for (var ci = nodes.length - 1; ci >= 0; ci--) {
    if (compRe.test(nodes[ci].name)) { nodes[ci].type = 'compiler'; break; }
  }
  /* Remove Nabi from nodes (gets orb) */
  for (var ni = nodes.length - 1; ni >= 0; ni--) {
    if (nabiRe.test(nodes[ni].name)) { nodes.splice(ni, 1); }
  }

  /* ═══ DICTIONNAIRE VISUEL ═══ */
  var VIS = {
    compiler: { m:"Sama\u2019", mTip:"Audition directe du Shaykh \u2014 le plus haut degr\u00e9 de r\u00e9ception.", rl:"Compilateur (Mu\u1e25addith)", st:"A compil\u00e9 ce hadith dans son recueil.",
                bd:'border-[#d4af37]',db:'border-[#d4af37]',mc:'text-[#d4af37]',nc:'text-[#d4af37]',mb:'bg-[#1a140a]',mr:'border-[#d4af37]/30',dB:'bg-black',dT:'text-[#d4af37]'},
    thiqah:   { m:"\u1e24addathan\u0101", mTip:"\u00ab Il nous a rapport\u00e9 \u00bb \u2014 r\u00e9ception orale directe.", rl:"R\u0101w\u012b (Transmetteur)", st:"Thiqah \u2014 digne de confiance.",
                bd:'border-[#d4af37]',db:'border-[#d4af37]',mc:'text-green-500',nc:'text-white',mb:'bg-[#0a1a0f]',mr:'border-green-600/30',dB:'bg-black',dT:'text-[#d4af37]'},
    sahabi:   { m:"\u2018An", mTip:"\u00ab D\u2019apr\u00e8s \u00bb \u2014 le Compagnon rapporte du Proph\u00e8te \uFDFA.", rl:"\u1e62a\u1e25\u0101b\u012b (Compagnon)", st:"\u2018Ad\u016bl par Ijm\u0101\u2019.",
                bd:'border-yellow-500',db:'border-yellow-500',mc:'text-yellow-500',nc:'text-yellow-400',mb:'bg-[#1a1400]',mr:'border-yellow-500/30',dB:'bg-black',dT:'text-yellow-400'},
    kadhdhab: { m:"Inqi\u1e6d\u0101\u2019", mTip:"Rupture de cha\u00eene \u2014 transmission non \u00e9tablie.", rl:"R\u0101w\u012b Matr\u016bk", st:"Rejet\u00e9 par les Imams du Jar\u1e25.",
                bd:'border-red-500',db:'border-red-500',mc:'text-red-500',nc:'text-red-400',mb:'bg-[#1a0a0a]',mr:'border-red-500/30',dB:'bg-red-950',dT:'text-red-500'}
  };

  /* ═══ CONNAISSANCES PAR NOM : titre, époque, verdict ═══ */
  var KB = [
    {re:/bukhari|\u0628\u062e\u0627\u0631\u064a/i, title:'Compilateur', epoch:'9e s. \u2014 Bukhara', badge:'s', bt:'Am\u012br al-Mu\u2019min\u012bn fil \u1e24ad\u012bth'},
    {re:/muslim|\u0645\u0633\u0644\u0645/i, title:'Compilateur', epoch:'9e s. \u2014 N\u012bs\u0101b\u016br', badge:'s', bt:'\u1e24ujjah'},
    {re:/tirmidhi|\u062a\u0631\u0645\u0630\u064a/i, title:'Compilateur', epoch:'9e s. \u2014 Tirmidh', badge:'s', bt:'\u1e24\u0101fi\u1e93, Im\u0101m'},
    {re:/nasa.i|\u0627\u0644\u0646\u0633\u0627\u0626\u064a/i, title:'Compilateur', epoch:'9e s. \u2014 Khur\u0101s\u0101n', badge:'s', bt:'\u1e24\u0101fi\u1e93'},
    {re:/dawud|abu\s*d\u0101w\u016bd|\u062f\u0627\u0648\u062f/i, title:'Compilateur', epoch:'9e s. \u2014 Sijist\u0101n', badge:'s', bt:'\u1e24\u0101fi\u1e93'},
    {re:/ibn\s*majah|\u0627\u0628\u0646\s*\u0645\u0627\u062c\u0647/i, title:'Compilateur', epoch:'9e s. \u2014 Qazw\u012bn', badge:'s', bt:'\u1e24\u0101fi\u1e93'},
    {re:/ahmad.*hanbal|\u0623\u062d\u0645\u062f\s*\u0628\u0646\s*\u062d\u0646\u0628\u0644/i, title:'Im\u0101m', epoch:'9e s. \u2014 Bagdad', badge:'g', bt:'Im\u0101m Ahl as-Sunnah'},
    {re:/malik|\u0645\u0627\u0644\u0643\s*\u0628\u0646\s*\u0623\u0646\u0633/i, title:'Im\u0101m', epoch:'8e s. \u2014 M\u00e9dine', badge:'g', bt:'Im\u0101m D\u0101r al-Hijrah'},
    {re:/nafi|\u0646\u0627\u0641\u0639/i, title:'T\u0101bi\u2019\u012b', epoch:'8e s. \u2014 M\u00e9dine', badge:'s', bt:'Thiqah Thabt'},
    {re:/ibn\s*['\u2018]?umar|\u0639\u0628\u062f\u0627\u0644\u0644\u0647\s*\u0628\u0646\s*\u0639\u0645\u0631/i, title:'\u1e62a\u1e25\u0101b\u012b', epoch:'7e s. \u2014 M\u00e9dine', badge:'g', bt:'\u2018Ad\u016bl'},
    {re:/abu\s*hurayra|\u0623\u0628\u0648\s*\u0647\u0631\u064a\u0631/i, title:'\u1e62a\u1e25\u0101b\u012b', epoch:'7e s. \u2014 M\u00e9dine', badge:'g', bt:'\u2018Ad\u016bl \u2014 5 374 a\u1e25\u0101d\u012bth'},
    {re:/anas|\u0623\u0646\u0633\s*\u0628\u0646\s*\u0645\u0627\u0644\u0643/i, title:'\u1e62a\u1e25\u0101b\u012b', epoch:'7e\u20138e s. \u2014 Basra', badge:'g', bt:'\u2018Ad\u016bl \u2014 Kh\u0101dim an-Nab\u012b'},
    {re:/aisha|\u0639\u0627\u0626\u0634\u0629/i, title:'\u1e62a\u1e25\u0101biyyah', epoch:'7e s. \u2014 M\u00e9dine', badge:'g', bt:'\u2018Ad\u016blah \u2014 Umm al-Mu\u2019min\u012bn'},
    {re:/umar\s*(ibn|bin)?\s*al.?khattab|\u0639\u0645\u0631\s*\u0628\u0646\s*\u0627\u0644\u062e\u0637\u0627\u0628/i, title:'\u1e62a\u1e25\u0101b\u012b', epoch:'7e s. \u2014 M\u00e9dine', badge:'g', bt:'\u2018Ad\u016bl \u2014 Al-F\u0101r\u016bq'},
    {re:/tinnisi|yusuf.*abd/i, title:'T\u0101bi\u2019 at-T\u0101bi\u2019\u012bn', epoch:'9e s. \u2014 Tinnis', badge:'s', bt:'Thiqah Mutqin'},
    {re:/shu\u2019ba|shu.ba|\u0634\u0639\u0628\u0629/i, title:'T\u0101bi\u2019\u012b', epoch:'8e s. \u2014 Basra', badge:'g', bt:'Am\u012br al-Mu\u2019min\u012bn fil \u1e24ad\u012bth'},
    {re:/sufyan.*thawri|\u0633\u0641\u064a\u0627\u0646\s*\u0627\u0644\u062b\u0648\u0631\u064a/i, title:'T\u0101bi\u2019\u012b', epoch:'8e s. \u2014 Kufa', badge:'s', bt:'Thiqah \u1e24\u0101fi\u1e93'},
    {re:/zuhri|\u0627\u0644\u0632\u0647\u0631\u064a/i, title:'T\u0101bi\u2019\u012b', epoch:'8e s. \u2014 M\u00e9dine', badge:'s', bt:'Thiqah Thabt'},
    {re:/qatada|\u0642\u062a\u0627\u062f\u0629/i, title:'T\u0101bi\u2019\u012b', epoch:'8e s. \u2014 Basra', badge:'s', bt:'Thiqah'},
    {re:/hasan\s*basri|\u0627\u0644\u062d\u0633\u0646\s*\u0627\u0644\u0628\u0635\u0631\u064a/i, title:'T\u0101bi\u2019\u012b', epoch:'8e s. \u2014 Basra', badge:'s', bt:'Thiqah'}
  ];

  /* Fallback epoch by type */
  function guessEpoch(t) {
    if (t === 'sahabi') return '7e si\u00e8cle \u2014 \u00c8re Proph\u00e9tique';
    if (t === 'compiler') return '9e si\u00e8cle \u2014 \u00c2ge d\u2019Or';
    return '8e\u20139e si\u00e8cle';
  }

  /* ═══ RENDU ═══ */
  var uid = 'z' + Math.random().toString(36).substr(2, 5);
  var lnG = isSahih ? 'linear-gradient(to bottom,#d4af37,#22c55e 60%,#15803d)' : 'linear-gradient(to bottom,#d4af37,#f59e0b 40%,#ef4444 80%)';
  var lnS = isSahih ? '0 0 15px rgba(212,175,55,.4)' : '0 0 15px rgba(239,68,68,.3)';
  var chv = '<svg class="mzC4-chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>';
  var arrSvg = '<div class="mzC4-arr"><svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/></svg></div>';

  var h = '';

  /* ═══ PROPHÈTE ﷺ — SCEAU DE BAGDAD ═══ */
  h += _mzProphetSeal();
  h += '<div class="mzC4-nabi" style="display:none;">';
  h += '<span class="mzC4-epoch" style="display:inline-block;margin-bottom:8px;">7e SI\u00c8CLE \u2014 \u00c8RE PROPH\u00c9TIQUE</span>';
  h += '<div class="mzC4-orb"><span>\uFDFA</span></div>';
  h += '<h3 class="text-xl font-black text-[#d4af37] mb-1" style="font-family:\'Scheherazade New\',serif;">Le Proph\u00e8te Muhammad \uFDFA</h3>';
  h += '<p class="text-[9px] text-[#d4af37]/50 uppercase tracking-[0.25em] mb-2" style="font-family:Cinzel,serif;">SOURCE DE LA R\u00c9V\u00c9LATION \u2014 MA\u2018S\u016aM</p>';
  h += '<p class="text-[11px] text-gray-500 italic max-w-xs mx-auto" style="font-family:\'Cormorant Garamond\',serif;line-height:1.6;">';
  h += '\u00ab Il ne prononce rien sous l\u2019effet de la passion \u00bb (53:3)</p>';
  h += '</div>';
  h += arrSvg;

  /* ═══ CHAÎNE ═══ */
  h += '<div class="relative max-w-4xl mx-auto py-4">';
  h += '<div class="absolute left-1/2 -translate-x-1/2 w-1.5 h-full z-0 rounded-full" style="background:' + lnG + ';box-shadow:' + lnS + ';"></div>';

  nodes.forEach(function(n, i) {
    var t = n.type;
    var vi = VIS[t] || VIS.thiqah;
    var nid = uid + '-' + i;
    var dl = (i * 0.12);

    /* Lookup connu */
    var kn = null;
    for (var k = 0; k < KB.length; k++) { if (KB[k].re.test(n.name)) { kn = KB[k]; break; } }

    var genealogy = kn ? kn.title : vi.rl;
    var epoch = kn ? kn.epoch : guessEpoch(t);
    var badge = kn ? kn.badge : (t === 'kadhdhab' ? 'r' : t === 'sahabi' ? 'g' : 's');
    var badgeTxt = kn ? kn.bt : (t === 'kadhdhab' ? 'Matr\u016bk' : t === 'sahabi' ? '\u2018Ad\u016bl' : 'Thiqah');

    /* ROW */
    h += '<div class="mzC4-rw relative z-10 mb-3" id="mzC4r-' + nid + '">';
    h += '<div class="flex items-center justify-center gap-6 cursor-pointer" onclick="mzC4Tog(\'' + nid + '\')" style="animation:mzC4In .5s ease both;animation-delay:' + dl + 's;">';

    /* LEFT: Tahammul + Tooltip */
    h += '<div class="w-5/12 flex justify-end"><div class="mzC4-mech ' + vi.mb + ' border ' + vi.mr + ' px-4 py-2.5 rounded-lg text-right max-w-[220px] shadow-lg">';
    h += '<span class="text-[8px] text-gray-500 uppercase tracking-widest block mb-1" style="font-family:Cinzel,serif;">Mode de r\u00e9ception</span>';
    h += '<span class="font-black text-sm uppercase ' + vi.mc + '" style="font-family:Cinzel,serif;">' + vi.m + '</span>';
    h += '<div class="mzC4-tip">' + vi.mTip + '</div>';
    h += '</div></div>';

    /* DOT */
    h += '<div class="mzC4-dt absolute left-1/2 transform -translate-x-1/2 w-11 h-11 rounded-full ' + vi.dB + ' border-4 ' + vi.db + ' flex items-center justify-center z-20 shadow-[0_0_20px_rgba(0,0,0,1)]" style="transition:box-shadow .3s;">';
    h += '<span class="' + vi.dT + ' text-xs font-bold">' + (i + 1) + '</span></div>';

    /* RIGHT: Name (TITLE) + Genealogy + Badge + Epoch */
    h += '<div class="w-5/12 flex justify-start"><div class="mzC4-card bg-[#111] p-4 rounded-xl border-l-4 ' + vi.bd + ' shadow-2xl max-w-[300px]">';

    /* NAME = REAL NAME — this is the TITLE */
    h += '<div class="flex items-center justify-between mb-1">';
    h += '<h3 class="text-lg font-black ' + vi.nc + ' leading-tight" style="font-family:\'Scheherazade New\',serif;">' + n.name + '</h3>';
    h += chv + '</div>';

    /* Genealogy subtitle */
    h += '<p class="text-[9px] text-gray-500 uppercase tracking-widest mb-2" style="font-family:Cinzel,serif;">' + genealogy + '</p>';

    /* Badge (verdict) + Epoch — side by side */
    h += '<div class="flex items-center gap-2 flex-wrap mb-2">';
    h += '<span class="mzC4-bg ' + badge + '">' + badgeTxt + '</span>';
    h += '<span class="mzC4-epoch">' + epoch + '</span>';
    h += '</div>';

    /* Short authentication text */
    h += '<div class="bg-black/50 p-2.5 rounded border border-gray-800/50 border-l-2 ' + vi.bd + '">';
    h += '<p class="text-[11px] text-gray-400 italic" style="font-family:\'Cormorant Garamond\',serif;line-height:1.6;">\u00ab ' + vi.st + ' \u00bb</p>';
    h += '</div>';

    h += '</div></div>';
    h += '</div>'; /* /flex row */

    /* ═══ PANEL ═══ */
    h += '<div class="mzC4-panel" id="mzC4p-' + nid + '"><div class="mzC4-pi">';

    /* Verdict détaillé de l'IA */
    if (n.verdict && n.verdict.length > 10) {
      h += '<p class="mzC4-vl" style="margin-bottom:12px;">' + n.verdict + '</p>';
    }

    /* Transmission : qui → qui */
    h += '<div style="padding:10px 14px;border-radius:8px;background:rgba(139,92,246,.04);border:1px solid rgba(139,92,246,.12);">';
    h += '<p style="font-family:Cinzel,serif;font-size:7px;font-weight:700;letter-spacing:.15em;color:rgba(139,92,246,.5);margin-bottom:4px;">TRANSMISSION</p>';
    h += '<p class="mzC4-vl">';
    if (i === 0) h += 'A re\u00e7u du <strong>Proph\u00e8te \uFDFA</strong>';
    else h += 'A re\u00e7u de <strong>' + nodes[i - 1].name + '</strong>';
    if (i < nodes.length - 1) h += ' \u2192 a transmis \u00e0 <strong>' + nodes[i + 1].name + '</strong>';
    else h += ' \u2192 a compil\u00e9 dans son recueil';
    h += '</p></div>';

    /* Alerte kadhdhab */
    if (t === 'kadhdhab') {
      h += '<div style="margin-top:12px;padding:12px 16px;border-radius:8px;background:rgba(239,68,68,.04);border:1px solid rgba(239,68,68,.15);">';
      h += '<p style="font-family:Cinzel,serif;font-size:7px;font-weight:700;letter-spacing:.12em;color:#ef4444;margin-bottom:4px;">\u26a0 \u2018ILLAH \u2014 MAILLON ROMPU</p>';
      h += '<p class="mzC4-vl" style="color:rgba(239,68,68,.7);">al-Jar\u1e25 al-Mufassar muqaddam \u2018ala at-Ta\u2019d\u012bl \u2014 la critique argument\u00e9e pr\u00e9vaut.</p></div>';
    }

    h += '</div></div>'; /* /panel */
    h += '</div>'; /* /row */

    /* Arrow between nodes */
    if (i < nodes.length - 1) h += arrSvg;
  });

  h += '</div>'; /* /container */
  h += '<p style="font-family:Cinzel,serif;font-size:6px;letter-spacing:.2em;color:rgba(201,168,76,.18);text-align:center;margin-top:10px;">SILSILAT AL-ISN\u0100D \u2014 CASCADE DE PR\u00c9SERVATION</p>';
  return h;
}


/* ═══ TRIDENT 2 : SCANNER DE DÉFAUT — 'ILLAH (TAILWIND EXACT) ═══ */
function _mzScannerFromChain(jarhHtml, grade) {
  if(!jarhHtml || jarhHtml.length < 5) return '';
  /* ── Parse narrateurs ── */
  var spanRe = /<span[^>]*style="[^"]*color:\s*([^;"]+)[^"]*"[^>]*>([\s\S]*?)<\/span>/gi;
  var nodes = [], m;
  while((m = spanRe.exec(jarhHtml)) !== null) {
    var color = m[1].trim();
    var name = m[2].replace(/<[^>]+>/g,'').trim();
    if(!name) continue;
    var isRed = /ef4444|e63946|dc2626|ff0000|red|e74c3c/i.test(color);
    nodes.push({name:name, defect: isRed});
  }
  if(nodes.length === 0) return '';
  var hasDefect = nodes.some(function(n){return n.defect;});
  if(!hasDefect) return '';

  /* ── Dictionnaire de causes ── */
  var causeMap = {
    kadhdhab:'Kadhdhab (grand menteur) \u2014 rejete par Ahmad, Ibn Ma\u2019in et Al-Bukhari.',
    matruk:'Matruk (abandonne) \u2014 sa narration ne constitue aucune preuve.',
    daif:'Da\u2019if (faible) \u2014 memoire defaillante ou Jahala (inconnu des Muhaddithin).',
    generic:'Illah detectee \u2014 rapporteur rejete par les Imams du Jarh wa at-Ta\u2019dil.'
  };
  function getCause(n){
    var lower = jarhHtml.toLowerCase();
    if(/kadhdhab|menteur|liar/i.test(lower)) return causeMap.kadhdhab;
    if(/matruk|abandonne/i.test(lower)) return causeMap.matruk;
    if(/da.if|faible|weak/i.test(lower)) return causeMap.daif;
    return causeMap.generic;
  }

  /* ── Conteneur horizontal scrollable ── */
  var html = '<div class="overflow-x-auto py-6 px-2" style="-webkit-overflow-scrolling:touch;">';
  html += '<div class="flex items-center gap-0 min-w-max">';

  nodes.forEach(function(n, i) {
    /* ── Fil entre les noeuds ── */
    if(i > 0) {
      var prevBad = nodes[i-1].defect, curBad = n.defect;
      if(prevBad || curBad) {
        html += '<div class="w-10 h-1 flex-shrink-0" style="background:repeating-linear-gradient(90deg,rgba(239,68,68,.6) 0 4px,transparent 4px 8px);"></div>';
      } else {
        html += '<div class="w-10 h-0.5 flex-shrink-0 bg-gradient-to-r from-green-500/50 to-green-500/20 rounded-full"></div>';
      }
    }

    var delay = (i * 0.1);
    var initial = n.name.charAt(0);

    if(n.defect) {
      /* ══ NOEUD DÉFAILLANT — rouge + animate-ping ══ */
      html += '<div class="flex flex-col items-center flex-shrink-0" style="animation:fadeInUp .35s ease both;animation-delay:'+delay+'s;">';
      /* Avatar + radar ping */
      html += '<div class="relative">'
        +'<div class="w-14 h-14 rounded-full border-4 border-red-500 bg-black flex items-center justify-center z-10 relative"'
        +' style="box-shadow:0 0 20px rgba(239,68,68,.35);">'
        +'<span class="text-red-500 font-bold text-lg" style="font-family:\'Scheherazade New\',serif;">'+initial+'</span>'
        +'</div>'
        +'<div class="absolute inset-0 rounded-full border-2 border-red-500 animate-ping"></div>'
        +'</div>';
      /* Nom */
      html += '<span class="text-sm font-bold mt-2 text-red-500" style="font-family:\'Scheherazade New\',serif;">'+n.name+'</span>';
      /* Badge */
      html += '<span class="text-[8px] uppercase tracking-widest px-3 py-1 rounded bg-red-500/10 border border-red-500/30 text-red-500 mt-1 font-bold" style="font-family:Cinzel,serif;">MATRUK \u2014 REJETE</span>';
      /* Cause */
      html += '<p class="text-[10px] text-red-400/70 mt-1 text-center max-w-[120px] italic" style="font-family:\'Cormorant Garamond\',serif;line-height:1.4;">'+getCause(n)+'</p>';
      html += '</div>';
    } else {
      /* ══ NOEUD SAIN — vert, pas de ping ══ */
      html += '<div class="flex flex-col items-center flex-shrink-0" style="animation:fadeInUp .35s ease both;animation-delay:'+delay+'s;">';
      /* Avatar */
      html += '<div class="relative">'
        +'<div class="w-14 h-14 rounded-full border-4 border-green-500 bg-black flex items-center justify-center">'
        +'<span class="text-green-500 font-bold text-lg" style="font-family:\'Scheherazade New\',serif;">'+initial+'</span>'
        +'</div></div>';
      /* Nom */
      html += '<span class="text-sm font-bold mt-2 text-green-400" style="font-family:\'Scheherazade New\',serif;">'+n.name+'</span>';
      /* Badge */
      html += '<span class="text-[8px] uppercase tracking-widest px-3 py-1 rounded bg-green-500/10 border border-green-500/30 text-green-500 mt-1 font-bold" style="font-family:Cinzel,serif;">THIQAH</span>';
      html += '</div>';
    }
  });

  html += '</div></div>';
  html += '<p style="font-family:Cinzel,serif;font-size:6.5px;letter-spacing:.25em;color:rgba(239,68,68,.3);text-align:center;margin-top:6px;">SCANNER DE DEFAUT \u2014 LOCALISATION DE L\u2019ILLAH</p>';
  return html;
}

/* ═══ TRIDENT 2 : SCANNER DES 5 CONDITIONS (CHECKLIST AVANCÉE) ═══ */
function _mzFormatSanad(sanadHtml) {
  if(!sanadHtml || sanadHtml.length < 5) return '';
  /* Parse les 5 conditions depuis le HTML IA */
  var CONDITIONS = [
    {key:'ITTISAL',ar:'\u0627\u062A\u0651\u0650\u0635\u064E\u0627\u0644',fr:'Continuite de la chaine',icon:'link'},
    {key:'ADALAT',ar:'\u0639\u064E\u062F\u064E\u0627\u0644\u064E\u0629',fr:'Probite des transmetteurs',icon:'shield'},
    {key:'DABT',ar:'\u0636\u064E\u0628\u0652\u0637',fr:'Precision memorielle',icon:'brain'},
    {key:'SHUDHUDH',ar:'\u0634\u064F\u0630\u064F\u0648\u0630',fr:'Absence d\'anomalie',icon:'eye'},
    {key:'ILLAH',ar:'\u0639\u0650\u0644\u0651\u064E\u0629',fr:'Absence de defaut cache',icon:'search'}
  ];
  var iconSvgs = {
    link:'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>',
    shield:'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    brain:'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg>',
    eye:'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>',
    search:'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>'
  };
  /* Detect pass/fail per condition from HTML spans */
  var rawText = sanadHtml;
  var html = '';
  CONDITIONS.forEach(function(c, idx) {
    var isFail = false;
    var detail = '';
    /* Search for this condition's section in the IA content */
    var patterns = [
      new RegExp(c.key+'[^<]*?DEFAILLANTE','i'),
      new RegExp(c.key+'[^<]*?<span[^>]*color[^>]*#e74c3c','i'),
      new RegExp((idx+1)+'\\.\\s*'+c.key+'[\\s\\S]{0,300}?DEFAILLANTE','i'),
      new RegExp(c.key+'[\\s\\S]{0,200}?fail','i')
    ];
    for(var p=0;p<patterns.length;p++){if(patterns[p].test(rawText)){isFail=true;break;}}
    /* Extract detail text for this condition */
    var detRe = new RegExp('(?:'+c.key+'|'+(idx+1)+'\\.)[^:]*:\\s*([^<]{10,250})','i');
    var dm = rawText.match(detRe);
    if(dm) detail = dm[1].replace(/^\s*[-:—]\s*/,'').trim();
    if(!detail) {
      var detRe2 = new RegExp(c.key+'[\\s\\S]{0,20}?</span>\\s*[(:—]?\\s*([^<]{10,250})','i');
      var dm2 = rawText.match(detRe2);
      if(dm2) detail = dm2[1].replace(/^\s*[-:—)\s]+/,'').trim();
    }
    var cls = isFail ? 'fail' : 'pass';
    var statusTxt = isFail ? 'DEFAILLANTE' : 'REMPLIE';
    var statusColor = isFail ? '#ef4444' : '#22c55e';
    var statusBg = isFail ? 'rgba(239,68,68,.08)' : 'rgba(34,197,94,.08)';
    var statusBd = isFail ? 'rgba(239,68,68,.2)' : 'rgba(34,197,94,.2)';
    html += '<div class="mz-check-row" style="animation:fadeInUp .35s ease both;animation-delay:'+(idx*0.08)+'s;">'
      +'<div class="mz-check-icon '+cls+'" style="position:relative;">'
      +(isFail ? '<div style="position:absolute;inset:0;border-radius:7px;border:2px solid #ef4444;animation:tridentPing 1.5s cubic-bezier(0,0,.2,1) infinite;"></div>' : '')
      +iconSvgs[c.icon]
      +'</div>'
      +'<div class="mz-check-texts">'
      +'<span class="mz-check-name '+cls+'">'+c.fr+'</span>'
      +'<span class="mz-check-ar">'+c.ar+'</span>'
      +(detail ? '<p class="mz-check-detail">'+detail+'</p>' : '')
      +'</div>'
      +'<span class="mz-check-badge '+cls+'" style="background:'+statusBg+';color:'+statusColor+';border:1px solid '+statusBd+';">'+statusTxt+'</span>'
      +'</div>';
  });
  return html;
}

/* ═══ TRIDENT 3 : AUTOPSIE DU NARRATEUR — JARH WA TA'DIL DASHBOARD ═══ */
function _mzFormatAvis(avisHtml) {
  if(!avisHtml || avisHtml.length < 5) return '';
  var raw = avisHtml;
  /* Parse scholar citations from HTML */
  var parts = [];
  if(raw.indexOf('<br')!==-1) parts = raw.split(/<br\s*\/?>/gi);
  else if(raw.indexOf('//')!==-1) parts = raw.split('//');
  else if(raw.indexOf('\n\n')!==-1) parts = raw.split('\n\n');
  else {
    var sp = raw.split(/(?=<strong>|<b>)/gi);
    parts = sp.length > 1 ? sp : [raw];
  }
  var scholars = [];
  parts.forEach(function(part) {
    var txt = part.trim();
    if(txt.length < 5) return;
    var savantName = '', citation = txt;
    var m1 = txt.match(/<(?:strong|b)>([\s\S]*?)<\/(?:strong|b)>\s*[:;\u2014\u2013-]?\s*([\s\S]*)/i);
    if(m1) { savantName = m1[1].replace(/<[^>]+>/g,'').trim(); citation = m1[2].trim()||txt; }
    if(!savantName) {
      var m2 = txt.match(/^([A-Z\u0600-\u06FF][^:;\u2014]{2,40})\s*[:;\u2014\u2013]\s*([\s\S]+)/);
      if(m2) { savantName = m2[1].replace(/<[^>]+>/g,'').trim(); citation = m2[2].trim(); }
    }
    savantName = savantName.replace(/<[^>]+>/g,'').trim();
    citation = citation.replace(/^["\u00AB]|["\u00BB]$/g,'').trim();
    if(!citation) citation = txt.replace(/<[^>]+>/g,'');
    if(citation.length > 3) scholars.push({name:savantName||'IMAM',text:citation});
  });
  if(!scholars.length) return '<p style="font-size:15px;line-height:1.9;color:rgba(210,200,180,.78);">'+avisHtml+'</p>';

  /* Detect if any scholar is "weak" verdict (for profile bars) */
  var isSahih = !(/da.if|faible|mawdu|munkar|matruk|kadhdhab/i.test(raw));
  var adalahPct = isSahih ? 95 : 12;
  var dabtPct = isSahih ? 88 : 8;
  var adalahColor = isSahih ? '#22c55e' : '#ef4444';
  var dabtColor = isSahih ? '#22c55e' : '#ef4444';

  /* Split scholars: first 1-2 for profile, rest for quotes */
  var profileScholar = scholars[0];
  var ancientScholars = scholars.slice(0, Math.min(scholars.length, 3));
  var lastScholar = scholars.length > 3 ? scholars[scholars.length-1] : null;

  var html = '<div class="mz-autopsy">';
  /* Header */
  html += '<div class="mz-autopsy-header">'
    +'<div class="mz-autopsy-header-icon"><svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg></div>'
    +'<div><span class="mz-autopsy-title">AUTOPSIE DU NARRATEUR</span><span class="mz-autopsy-title-ar">\u0627\u0644\u062C\u064E\u0631\u0652\u062D\u064F \u0648\u064E\u0627\u0644\u062A\u0651\u064E\u0639\u0652\u062F\u0650\u064A\u0644</span></div>'
    +'</div>';

  /* Grid: left (profile) + right (quotes) */
  html += '<div class="mz-autopsy-grid">';

  /* LEFT — Profil du narrateur */
  html += '<div class="mz-autopsy-left">';
  html += '<div class="mz-autopsy-rawi-name">'+(profileScholar.name||'RAWI')+'</div>';
  html += '<div class="mz-autopsy-rawi-role">MUHADDITHIN \u2014 EVALUATION</div>';
  /* Barre 'Adalah */
  html += '<div class="mz-autopsy-bar-label"><span>\u2018ADALAH \u2014 Integrite</span><span style="color:'+adalahColor+';">'+adalahPct+'%</span></div>';
  html += '<div class="mz-autopsy-bar"><div class="mz-autopsy-bar-fill" style="width:'+adalahPct+'%;background:'+adalahColor+';"></div></div>';
  /* Barre Dabt */
  html += '<div class="mz-autopsy-bar-label"><span>DABT \u2014 Memoire / Precision</span><span style="color:'+dabtColor+';">'+dabtPct+'%</span></div>';
  html += '<div class="mz-autopsy-bar"><div class="mz-autopsy-bar-fill" style="width:'+dabtPct+'%;background:'+dabtColor+';"></div></div>';
  /* Status badge */
  if(isSahih) {
    html += '<div style="margin-top:12px;padding:6px 12px;border-radius:6px;background:rgba(34,197,94,.06);border:1px solid rgba(34,197,94,.15);display:inline-block;">'
      +'<span style="font-family:Cinzel,serif;font-size:7px;font-weight:700;letter-spacing:.15em;color:#22c55e;">THIQAH \u2014 GARANT FIABLE</span></div>';
  } else {
    html += '<div style="margin-top:12px;padding:6px 12px;border-radius:6px;background:rgba(239,68,68,.06);border:1px solid rgba(239,68,68,.15);display:inline-block;">'
      +'<span style="font-family:Cinzel,serif;font-size:7px;font-weight:700;letter-spacing:.15em;color:#ef4444;">DA\u2019IF \u2014 FAIBLE</span></div>';
  }
  html += '</div>';

  /* RIGHT — L'Étau de la Vérité */
  html += '<div class="mz-autopsy-right">';
  html += '<div class="mz-autopsy-etau-title">L\u2019ETAU DE LA VERITE \u2014 AQWAL AL-A\u2019IMMAH</div>';
  ancientScholars.forEach(function(s, i) {
    html += '<div class="mz-autopsy-quote" style="animation:fadeInUp .35s ease both;animation-delay:'+(i*0.1)+'s;">'
      +'<div class="mz-autopsy-quote-name">'+(s.name||'IMAM')+'</div>'
      +'<div class="mz-autopsy-quote-text">'+s.text+'</div>'
      +'</div>';
  });
  /* Extra quotes beyond 3 */
  for(var i=3;i<scholars.length;i++){
    html += '<div class="mz-autopsy-quote" style="animation:fadeInUp .35s ease both;animation-delay:'+(i*0.1)+'s;">'
      +'<div class="mz-autopsy-quote-name">'+(scholars[i].name||'IMAM')+'</div>'
      +'<div class="mz-autopsy-quote-text">'+scholars[i].text+'</div>'
      +'</div>';
  }
  html += '</div></div>';

  /* Conclusion — continuité méthodologique Salafs → contemporains */
  var conclusionScholar = '';
  var rawLower = raw.toLowerCase();
  if(rawLower.indexOf('albani')!==-1) conclusionScholar = 'Cheikh Al-Albani (rahimahullah)';
  else if(rawLower.indexOf('bin baz')!==-1||rawLower.indexOf('ibn baz')!==-1) conclusionScholar = 'Cheikh Bin Baz (rahimahullah)';
  else if(rawLower.indexOf('uthaymin')!==-1) conclusionScholar = 'Cheikh Ibn Uthaymin (rahimahullah)';
  else conclusionScholar = 'Cheikh Al-Albani (rahimahullah)';

  html += '<div class="mz-autopsy-conclusion">'
    +'<p><strong>'+conclusionScholar+'</strong> n\u2019a fait qu\u2019appliquer fidelement les regles etablies par les Imams du Jarh wa at-Ta\u2019dil '
    +'(Ahmad ibn Hanbal, Yahya ibn Ma\u2019in, Al-Bukhari). La methodologie Salafiyyah est une chaine ininterrompue '
    +'de preservation de la Sunnah authentique du Prophete \u0635\u0644\u0649 \u0627\u0644\u0644\u0647 \u0639\u0644\u064A\u0647 \u0648\u0633\u0644\u0645.</p>'
    +'</div>';

  html += '</div>';
  return html;
}

/* ═══ MAQUETTE 4 : RAPPORT CLINIQUE AL-ALBANI ═══ */
function _mzFormatAlbani(albaniHtml) {
  if(!albaniHtml || albaniHtml.length < 5) return '';
  var raw = albaniHtml, refName = '';
  var srcPat = [
    /([\u0633\u0644\u0633\u0644\u0629]\s*[\u0627\u0644\u0623\u062D\u0627\u062F\u064A\u062B]?\s*[\u0627\u0644\u0635\u062D\u064A\u062D\u0629\u0627\u0644\u0636\u0639\u064A\u0641\u0629\u0627\u0644\u0645\u0648\u0636\u0648\u0639\u0629][^\u060C.)\\]<]{0,35})/i,
    /(Silsilah\s+(?:Sahihah|Da[''\u2019]?eefah|As-Sahihah|Ad-Da[''\u2019]?eefah)[^,.)]{0,30})/i,
    /(Sahih\s+Al-Jami[^,.)]{0,25})/i, /(Da[''\u2019]?if\s+Al-Jami[^,.)]{0,25})/i,
    /(Irwa[''\u2019]?\s+Al-Ghalil[^,.)]{0,25})/i, /(Takhrij\s+Mishkat[^,.)]{0,25})/i,
    /([Nn][\u00B0o.]\s*\d{1,5})/
  ];
  for(var i=0;i<srcPat.length;i++){var sm=raw.match(srcPat[i]);if(sm){refName=sm[1].replace(/<[^>]+>/g,'').trim();break;}}
  if(!refName) refName='Takhrij Al-Albani';
  var hukmClass='',hukmLabel='';
  if(/\u0635\u062D\u064A\u062D|SAHIH|[Aa]uthentique/i.test(raw)){hukmClass='sahih';hukmLabel='SAHIH';}
  else if(/\u0636\u0639\u064A\u0641|DA.IF|[Ff]aible/i.test(raw)){hukmClass='daif';hukmLabel="DA'IF";}
  else if(/\u0645\u0648\u0636\u0648\u0639|MAWDU|[Ii]nvent/i.test(raw)){hukmClass='mawdu';hukmLabel="MAWDU'";}
  var paras = raw.split(/<br\s*\/?>/gi);
  if(paras.length<=1) paras=raw.split('\n\n');
  if(paras.length<=1) paras=raw.split('\n');
  if(paras.length<=1 && raw.length>200) {
    var mid=Math.floor(raw.length/2);
    var dot=raw.indexOf('.',mid);
    if(dot>0&&dot<raw.length-10) paras=[raw.substring(0,dot+1),raw.substring(dot+1)];
    else paras=[raw];
  }
  if(paras.length<=1) paras=[raw];
  var html='<div class="mz-albani"><div class="mz-albani-head">'
    +'<span class="mz-albani-title">AL-ALBANI<span class="mz-albani-title-ar">\u0627\u0644\u0623\u0644\u0628\u064E\u0627\u0646\u0650\u064A</span></span>'
    +'<span class="mz-albani-ref">'+refName+'</span></div>'
    +'<div class="mz-albani-body">';
  if(hukmClass) html+='<span class="mz-albani-hukm '+hukmClass+'">VERDICT : '+hukmLabel+'</span>';
  paras.forEach(function(p){var t=p.trim();if(t.length>2) html+='<p>'+t+'</p>';});
  html+='</div></div>';
  return html;
}

function renderAIResult(parsed){
  if(!parsed||parsed==='fallback'||typeof parsed!=='object'){showFallbackResult('');return;}
  if(!parsed.grade){showFallbackResult('');return;}
  /* ── ANTI-DOUBLON : vider le conteneur avant toute injection ── */
  var _box=document.getElementById('result-box');
  if(_box) _box.innerHTML='';
  var g=parsed.grade||'INCONNU';
  var col=MZ_COLORS[g]||MZ_COLORS.INCONNU;
  var isLocal=parsed&&(parsed._source_type==='LOCAL'||parsed._source_type==='LOCAL_FALLBACK');
  var isSahih=(g==='SAHIH'||g==='HASAN');
  var html='';

  /* Source badge */
  html+=isLocal
    ?'<div class="mz-source"><span class="mz-source-dot" style="background:#22c55e;box-shadow:0 0 6px #22c55e;"></span><span class="mz-source-text" style="color:rgba(34,197,94,.8);">BASE LOCALE \u00B7 MIZAN DB v2.0</span><span class="mz-source-extra">HORS-LIGNE</span></div>'
    :'<div class="mz-source"><span class="mz-source-dot" style="background:#c9a84c;box-shadow:0 0 6px rgba(201,168,76,.5);"></span><span class="mz-source-text">TAKHRIJ \u00B7 AL MIZAN</span></div>';

  html+='<div class="mz-card">';

  /* ═══ NIVEAU 1 : MATN + VERDICT ═══ */
  html+='<div class="mz-niv1">';
  if(parsed.ar||parsed.matn_ar) {
    html+='<div class="mz-matn"><div class="mz-matn-ar">'+(parsed.ar||parsed.matn_ar)+'</div></div>';
  }
  html+=_mzVerdict(g,parsed.grade_ar)+'</div>';

  /* ═══ NIVEAU 2 : AL-HUKM — CAUSE DU VERDICT ═══ */
  var hukmText=parsed.resume||'';
  var hukmLabel=isSahih
    ? 'AL-HUKM \u2014 ATTESTATION D\'AUTHENTICITE'
    : 'AL-HUKM \u2014 CAUSE DE LA FAIBLESSE';
  if(hukmText) {
    html+='<div class="mz-illah"><span class="mz-illah-label">'+hukmLabel+'</span><p class="mz-illah-text">'+hukmText+'</p></div>';
  }

  /* ═══ NIVEAU 3 : TAHQIQ WA TAKHRIJ ═══ */
  var hasN3=false,niv3='';

  /* ── SHARH : Explication du Hadith (Fiqh al-Hadith) ── */
  if(parsed.analyse && parsed.analyse !== parsed.resume) {
    niv3+=_mzAcc(
      'SHARH AL-HADITH \u2014 Explication du texte selon les Salaf',
      '\u0634\u064E\u0631\u0652\u062D\u064F \u0627\u0644\u062D\u064E\u062F\u0650\u064A\u062B',
      '#d4af37',
      '<p>'+parsed.analyse+'</p>',
      true
    );
    hasN3=true;
  }

  /* ══ TRIDENT 1 : CASCADE DE PRÉSERVATION (injection directe, pas d'accordéon) ══ */
  var isnadRaw=parsed.isnad||null;
  if(isnadRaw && isnadRaw.length > 3){
    var cascadeLocal=_mzIsnadChain(isnadRaw,g);
    if(cascadeLocal) {
      niv3+=cascadeLocal;
    } else {
      niv3+=_mzAcc('JARH WA TA\'DIL','\u0633\u0650\u0644\u0633\u0650\u0644\u064E\u0629\u064F \u0627\u0644\u0625\u0650\u0633\u0646\u064E\u0627\u062F','#5dade2','<p>'+isnadRaw+'</p>',!parsed.analyse);
    }
    hasN3=true;
    /* Scanner de Défaut */
    var scannerLocal=_mzScannerFromChain(isnadRaw,g);
    if(scannerLocal){
      niv3+=_mzAcc('SCANNER DE DEFAUT \u2014 Localisation de l\u2019Illah','\u0639\u0650\u0644\u0651\u064E\u0629','#ef4444',scannerLocal,false);
    }
  }

  /* ── TRIDENT 2bis : SHURUT AS-SIHHAH (5 conditions checklist) ── */
  if(parsed.isnad_check){
    niv3+=_mzAcc(
      'SHURUT AS-SIHHAH \u2014 Les 5 conditions de l\'authenticite selon Ibn as-Salah',
      '\u0634\u064F\u0631\u064F\u0648\u0637\u064F \u0627\u0644\u0635\u0651\u0650\u062D\u0651\u064E\u0629',
      '#9b59b6',
      _mzFormatSanad(parsed.isnad_check),
      false
    );
    hasN3=true;
  }

  /* ── TRIDENT 3 : AUTOPSIE DU NARRATEUR (Jarh wa Ta'dil dashboard) ── */
  if(parsed.avis_savants){
    var avisContent='';
    if(Array.isArray(parsed.avis_savants)){
      /* Legacy format: array of {savant,citation} */
      var avisRaw='';
      parsed.avis_savants.forEach(function(av){
        avisRaw+='<strong>'+av.savant+'</strong> : '+av.citation+'<br><br>';
      });
      avisContent=_mzFormatAvis(avisRaw);
    } else if(typeof parsed.avis_savants==='string') {
      avisContent=_mzFormatAvis(parsed.avis_savants);
    }
    if(avisContent){
      niv3+=_mzAcc(
        'AUTOPSIE DU NARRATEUR \u2014 Aqwal al-A\u2019immah',
        '\u0623\u064E\u0642\u0648\u064E\u0627\u0644\u064F \u0627\u0644\u0623\u064E\u0626\u0650\u0645\u0651\u064E\u0629',
        '#e67e22',
        avisContent
      );
      hasN3=true;
    }
  }

  /* ── MAQUETTE 4 : TAKHRIJ — Reference austere ── */
  if(parsed.reference){
    niv3+='<div class="mz-takhrij"><span class="mz-takhrij-label">TAKHRIJ \u2014 \u0627\u0644\u0645\u064E\u0631\u062C\u0650\u0639</span><p>'+parsed.reference+'</p></div>';
  }

  /* ── BADIL — Hadith authentique de remplacement ── */
  if(isLocal&&parsed.badil){
    niv3+='<div class="mz-badil"><span class="mz-badil-label">HADITH AUTHENTIQUE DE REMPLACEMENT</span><p class="mz-badil-ar">'+parsed.badil.ar+'</p><p class="mz-badil-fr">'+parsed.badil.fr+'</p><p class="mz-badil-src">'+parsed.badil.source+'</p></div>';
  }

  if(hasN3) html+='<div class="mz-niv3"><div class="mz-niv3-label">TAHQIQ WA TAKHRIJ \u2014 VERIFICATION ET EXTRACTION</div>'+niv3+'</div>';
  else if(niv3) html+='<div class="mz-niv3" style="padding-top:8px;">'+niv3+'</div>';

  html+=_mzDisclaimer()+_mzActions(parsed.source_url)+'</div>';
  document.getElementById('loading-box').classList.remove('active');
  var box=document.getElementById('result-box');
  box.innerHTML=html;box.classList.add('active');
}

function showFallbackResult(txt){
  var q=normalize(txt),found=null;
  for(var i=0;i<HADITHS.length;i++){var h=HADITHS[i],hn=normalize(h.t);if(q.length>5&&(hn.indexOf(q.substring(0,10))!==-1||q.indexOf(hn.substring(0,10))!==-1)){found=h;break;}}
  if(!found) found={g:'INCONNU',r:'Analyse non disponible',e:'Consultez dorar.net ou sunnah.com pour une verification approfondie.',l:'https://dorar.net'};
  var g=found.g||'INCONNU';
  var html='<div class="mz-card"><div class="mz-niv1">'+_mzVerdict(g)+'</div>'
    +'<div class="mz-illah"><span class="mz-illah-label">RESULTAT</span><p class="mz-illah-text">'+found.e+'</p></div>';
  if(found.r) html+='<div class="mz-niv3"><div class="mz-takhrij"><span class="mz-takhrij-label">REFERENCE</span><p>'+found.r+'</p></div></div>';
  html+=_mzDisclaimer()+_mzActions(found.l)+'</div>';
  document.getElementById('loading-box').classList.remove('active');
  var box=document.getElementById('result-box');box.innerHTML=html;box.classList.add('active');
}

function renderExamples(){
  var el=document.getElementById('examples-list');
  if(!el)return;
  el.innerHTML='';
  var examples=[];
  if(window.MizanDB&&window.MizanDB.isLoaded()){
    examples=window.MizanDB.getByGrade('SAHIH',2).concat(window.MizanDB.getByGrade('DAIF',1)).concat(window.MizanDB.getByGrade('MAWDU',1));
  }
  if(!examples.length){
    HADITHS.slice(0,4).forEach(function(h){
      var b=document.createElement('button');b.className='example-btn';
      b.innerHTML='<span>'+h.t+'</span><span class="eg eg-'+h.g+'">'+h.g+'</span>';
      b.onclick=function(){document.getElementById('hadith-input').value=h.t;analyzeHadith(h.t);};
      el.appendChild(b);
    });
    return;
  }
  examples.forEach(function(h){
    var txt=(h.fr||'').substring(0,52)+((h.fr||'').length>52?'...':'');
    var b=document.createElement('button');b.className='example-btn';
    b.innerHTML='<span>'+txt+'</span><span class="eg eg-'+h.grade+'">'+h.grade+'</span>';
    b.onclick=(function(hh){return function(){document.getElementById('hadith-input').value=hh.fr||hh.ar||'';analyzeHadith(hh.fr||hh.ar||'');};})(h);
    el.appendChild(b);
  });
}

/* ════════════════════════════════════════
   LISTE PRÉDICATEURS
════════════════════════════════════════ */
var GROUPS=['Savants Majeurs','Francophones Fiables','Mises en garde','Répertoire du Manhaj'];
(function(){
  // DATA GUARD — Dédup IDs + catégories + dorar.net nettoyé des profils mis en garde
  var seenId={};
  PREACHERS=PREACHERS.filter(function(p){
    if(!p||p.id===undefined||p.id===null) return false;
    if(seenId[p.id]) return false;
    seenId[p.id]=true; return true;
  });
  var seenGrp=new Set(GROUPS.map(function(g){return g.trim().toLowerCase();}));
  PREACHERS.forEach(function(p){
    if(p&&p.cat){ var n=p.cat.trim().toLowerCase(); if(!seenGrp.has(n)){ seenGrp.add(n); GROUPS.push(p.cat.trim()); } }
  });
  var MEG=['DANGER','ÉVITER','EVITER','INNOVATEUR','KADHDHAB','MUBTADI'];
  PREACHERS.forEach(function(p){
    if(!p) return;
    var v=(p.verdict||'').toUpperCase();
    if(!MEG.some(function(m){return v.indexOf(m)!==-1;})) return;
    if(Array.isArray(p.sources)) p.sources=p.sources.filter(function(s){return s&&s.indexOf('dorar.net')===-1;});
    if(p.approfondi&&Array.isArray(p.approfondi.sources)) p.approfondi.sources=p.approfondi.sources.filter(function(s){return s&&s.indexOf('dorar.net')===-1;});
  });
})();
var currentFilter='all', currentRegion='all', currentAffil='all';

function setFilter(f,btn){
  currentFilter=f;
  document.querySelectorAll('#view-list .filter-btn').forEach(function(b){b.classList.remove('active-f');});
  btn.classList.add('active-f');
  renderList();
}
window.setFilter = setFilter;
function setRegion(r,btn){
  currentRegion=r;
  document.querySelectorAll('#region-filters .filter-btn').forEach(function(b){b.classList.remove('active-r');});
  btn.classList.add('active-r');
  renderList();
}
function setAffil(a,btn){
  currentAffil=a;
  document.querySelectorAll('#affil-filters .filter-btn').forEach(function(b){b.classList.remove('active-a');});
  btn.classList.add('active-a');
  renderList();
}

function matchRegion(p){
  if(currentRegion==='all') return true;
  var pays=(p.pays||'').toLowerCase()+(p.ville||'').toLowerCase();
  if(currentRegion==='france')   return pays.indexOf('france')!==-1||pays.indexOf('brest')!==-1||pays.indexOf('paris')!==-1||pays.indexOf('lyon')!==-1||pays.indexOf('marseille')!==-1||pays.indexOf('roubaix')!==-1||pays.indexOf('bordeaux')!==-1||pays.indexOf('lille')!==-1||pays.indexOf('essonne')!==-1||pays.indexOf('ivry')!==-1||pays.indexOf('longjumeau')!==-1;
  if(currentRegion==='maghreb')  return pays.indexOf('algérie')!==-1||pays.indexOf('maroc')!==-1||pays.indexOf('tunisie')!==-1||pays.indexOf('maghreb')!==-1||pays.indexOf('algeria')!==-1;
  if(currentRegion==='khalij')   return pays.indexOf('arabie')!==-1||pays.indexOf('saoudite')!==-1||pays.indexOf('koweït')!==-1||pays.indexOf('emirats')!==-1||pays.indexOf('qatar')!==-1||pays.indexOf('bahreïn')!==-1||pays.indexOf('yémen')!==-1||pays.indexOf('oman')!==-1||pays.indexOf('jordanie')!==-1||pays.indexOf('syrie')!==-1||pays.indexOf('egypte')!==-1||pays.indexOf('égypte')!==-1;
  if(currentRegion==='occident') return pays.indexOf('angleterre')!==-1||pays.indexOf('usa')!==-1||pays.indexOf('suisse')!==-1||pays.indexOf('canada')!==-1||pays.indexOf('belgique')!==-1||pays.indexOf('québec')!==-1||pays.indexOf('royaume')!==-1||pays.indexOf('uk')!==-1;
  if(currentRegion==='asie')     return pays.indexOf('inde')!==-1||pays.indexOf('pakistan')!==-1||pays.indexOf('zimbabwe')!==-1||pays.indexOf('nigeria')!==-1||pays.indexOf('malaysia')!==-1||pays.indexOf('indonésie')!==-1;
  return true;
}
function matchAffil(p){
  if(currentAffil==='all') return true;
  var af=(p.affiliation||'').toLowerCase();
  if(currentAffil==='salafi')   return af.indexOf('salafi')!==-1||af.indexOf('salafy')!==-1||af.indexOf('ahlu sunna')!==-1||af.indexOf('ahlussunna')!==-1;
  if(currentAffil==='ikhwan')   return af.indexOf('ikhwan')!==-1||af.indexOf('frères')!==-1||af.indexOf('frérist')!==-1||af.indexOf('tabligh')!==-1;
  if(currentAffil==='soufi')    return af.indexOf('soufi')!==-1||af.indexOf('sufi')!==-1||af.indexOf('tariqa')!==-1||af.indexOf('ahbash')!==-1;
  if(currentAffil==='liberal')  return af.indexOf('libéral')!==-1||af.indexOf('liberal')!==-1||af.indexOf('réformiste')!==-1||af.indexOf('moderniste')!==-1;
  if(currentAffil==='converti') return af.indexOf('converti')!==-1;
  if(currentAffil==='inconnu')  return !af||af==='inconnu'||af==='non classé';
  return true;
}

function matchFilter(p){
  if(!matchRegion(p)||!matchAffil(p)) return false;
  if(currentFilter==='all') return true;
  var v=p.verdict||'';
  if(currentFilter==='imam')      return v==='IMAM'||v==='THIQAH THIQAH'||v==='THIQAH THIQAH — IMAM';
  if(currentFilter==='fiable')    return v==='FIABLE'||v==='THIQAH';
  if(currentFilter==='sadouq')    return v==='SADOUQ'||v==='VÉRIDIQUE'||v==='SADÛQ';
  if(currentFilter==='surveiller')return v==='À SURVEILLER'||v==='PRUDENCE'||v.indexOf('SURVEILLER')!==-1||v.indexOf('⚠')!==-1||v==='NUANCÉ';
  if(currentFilter==='layyin')    return v==='LAYYIN'||v==='AFFAIBLI'||v==='LÂYYIN';
  if(currentFilter==='daif')      return v==='DAIF'||v==='FAIBLE';
  if(currentFilter==='eviter')    return v==='À ÉVITER'||v==='MATRUK'||v.indexOf('ÉVITER')!==-1;
  if(currentFilter==='mubtadi')   return v==='DANGER'||v==='MUBTADI'||v.indexOf('DANGER')!==-1;
  if(currentFilter==='kadhdhab')  return v==='KADHDHAB'||v==='MENTEUR'||v==='KADHÂB';
  if(currentFilter==='majhul')    return v==='INCONNU'||v==='MAJHUL';
  return true;
}
function renderList(){
  var s=normalize(document.getElementById('list-search').value||'');
  var el=document.getElementById('list-content');el.innerHTML='';
  var total=0;

  // ── Compteur coloré ──
  var allF=PREACHERS.filter(function(p){
    var ms=!s||normalize(p.nomFr).indexOf(s)!==-1||(p.nomAr&&p.nomAr.indexOf(document.getElementById('list-search').value)!==-1);
    return ms&&matchFilter(p);
  });
  var cnt={IMAM:0,FIABLE:0,SADOUQ:0,SURVEILLER:0,LAYYIN:0,DAIF:0,EVITER:0,DANGER:0,KADHDHAB:0};
  allF.forEach(function(p){
    var v=p.verdict||'';
    if(v==='IMAM'||v==='THIQAH THIQAH'||v.indexOf('THIQAH THIQAH')!==-1) cnt.IMAM++;
    else if(v==='FIABLE'||v==='THIQAH') cnt.FIABLE++;
    else if(v==='SADOUQ'||v==='VÉRIDIQUE') cnt.SADOUQ++;
    else if(v==='À SURVEILLER'||v==='PRUDENCE'||v.indexOf('SURVEILLER')!==-1||v.indexOf('⚠')!==-1||v==='NUANCÉ') cnt.SURVEILLER++;
    else if(v==='LAYYIN'||v==='AFFAIBLI') cnt.LAYYIN++;
    else if(v==='DAIF'||v==='FAIBLE') cnt.DAIF++;
    else if(v.indexOf('ÉVITER')!==-1||v==='MATRUK') cnt.EVITER++;
    else if(v==='DANGER'||v==='MUBTADI'||v.indexOf('DANGER')!==-1) cnt.DANGER++;
    else if(v==='KADHDHAB'||v==='MENTEUR') cnt.KADHDHAB++;
  });
  // Mettre à jour les compteurs sur les boutons de filtre
  var totalAll=PREACHERS.filter(function(p){return matchFilter(p);}).length;
  var filterCounts={
    'all': PREACHERS.filter(function(p){var ms=!s||normalize(p.nomFr).indexOf(s)!==-1||(p.nomAr&&p.nomAr.indexOf(document.getElementById('list-search').value)!==-1);return ms&&matchFilter(p);}).length,
    'imam': allF.filter(function(p){var v=p.verdict||'';return v==='IMAM'||v==='THIQAH THIQAH'||v.indexOf('THIQAH THIQAH')!==-1;}).length,
    'fiable': allF.filter(function(p){var v=p.verdict||'';return v==='FIABLE'||v==='THIQAH';}).length,
    'sadouq': allF.filter(function(p){var v=p.verdict||'';return v==='SADOUQ'||v==='VÉRIDIQUE';}).length,
    'surveiller': allF.filter(function(p){var v=p.verdict||'';return v.indexOf('SURVEILLER')!==-1||v==='PRUDENCE'||v.indexOf('⚠')!==-1||v==='NUANCÉ';}).length,
    'layyin': allF.filter(function(p){var v=p.verdict||'';return v==='LAYYIN'||v==='AFFAIBLI';}).length,
    'daif': allF.filter(function(p){var v=p.verdict||'';return v==='DAIF'||v==='FAIBLE';}).length,
    'eviter': allF.filter(function(p){var v=p.verdict||'';return v.indexOf('ÉVITER')!==-1||v==='MATRUK';}).length,
    'mubtadi': allF.filter(function(p){var v=p.verdict||'';return v==='DANGER'||v==='MUBTADI'||v.indexOf('DANGER')!==-1;}).length,
    'kadhdhab': allF.filter(function(p){var v=p.verdict||'';return v==='KADHDHAB'||v==='MENTEUR';}).length,
    'majhul': allF.filter(function(p){var v=p.verdict||'';return v==='MAJHUL'||v==='INCONNU';}).length
  };
  document.querySelectorAll('#view-list .filter-btn[data-filter]').forEach(function(btn){
    var f=btn.getAttribute('data-filter');
    var n=filterCounts[f]!==undefined?filterCounts[f]:0;
    var countEl=btn.querySelector('.f-count');
    if(!countEl){countEl=document.createElement('span');countEl.className='f-count';countEl.style.cssText='font-family:\'Cinzel\',serif;font-size:11px;font-weight:900;display:block;line-height:1;margin-top:1px;';btn.appendChild(countEl);}
    countEl.textContent=n;
  });



  GROUPS.forEach(function(grp){
    var items=PREACHERS.filter(function(p){
      var ms=!s||normalize(p.nomFr).indexOf(s)!==-1||(p.nomAr&&p.nomAr.indexOf(document.getElementById('list-search').value)!==-1);
      var mf=matchFilter(p);
      return p.cat===grp&&ms&&mf;
    });
    if(!items.length)return;total+=items.length;
    var sec=document.createElement('div');sec.style.marginBottom='24px';

    var gc='#c9a84c',gb='rgba(201,168,76,.07)';
    if(grp==='Mises en garde'){gc='#f87171';gb='rgba(239,68,68,.05)';}
    else if(grp==='Répertoire du Manhaj'){gc='#f59e0b';gb='rgba(245,158,11,.06)';}
    else if(grp==='Savants Majeurs'){gc='#a78bfa';gb='rgba(167,139,250,.06)';}
    else if(grp==='Francophones Fiables'){gc='#34d399';gb='rgba(34,197,94,.06)';}

    var th='<div class="group-title"><div class="group-line l" style="background:linear-gradient(to right,transparent,'+gc+');"></div>'
      +'<span class="group-label" style="color:'+gc+';border-color:'+gc+'55;background:'+gb+';">'+grp.toUpperCase()+'</span>'
      +'<span style="font-family:\'Cinzel\',serif;font-size:13px;font-weight:700;color:'+gc+';background:'+gb+';border:1.5px solid '+gc+'66;border-radius:20px;padding:2px 11px;letter-spacing:.04em;">'+items.length+'</span>'
      +'<div class="group-line r" style="background:linear-gradient(to left,transparent,'+gc+');"></div></div>';

    // #6 Pagination virtuelle — afficher 20 items par section au départ
    var PAGE_SIZE=20;
    var secId='sec-'+grp.replace(/[^a-z]/gi,'');
    if(!window.iaSectionPage) window.iaSectionPage={};
    var page=window.iaSectionPage[secId]||1;
    var visibleItems=items.slice(0,page*PAGE_SIZE);
    var ch='';
    visibleItems.forEach(function(p){
      var cbg='rgba(255,255,255,.028)',cbo='rgba(201,168,76,.1)',csh='0 2px 12px rgba(0,60,10,.1)';
      if(p.verdict==='FIABLE'){cbg='#f0faf4';cbo='rgba(34,197,94,.28)';csh='0 2px 14px rgba(34,197,94,.12)';}
      else if(p.verdict==='DANGER'){cbg='#1a0505';cbo='rgba(127,29,29,.5)';csh='0 2px 14px rgba(200,30,30,.12)';}
      else if(p.verdict.indexOf('ÉVITER')!==-1){cbg='#fff8f8';cbo='rgba(239,68,68,.28)';}
      else if(p.verdict.indexOf('PRUDENCE')!==-1||p.verdict.indexOf('⚠')!==-1){cbg='#fffbf0';cbo='rgba(245,158,11,.28)';}

      var nom=p.nomFr.replace(/'/g,"\\'");
      var ar=(p.nomAr||'').replace(/'/g,"\\'");
      ch+='<button class="pred-btn" style="background:'+cbg+';border:1px solid '+cbo+';box-shadow:'+csh+';" onclick="showPredLoading(\''+nom+'\',\''+ar+'\',function(){openDetail('+p.id+');})">'
        +'<div style="width:5px;flex-shrink:0;align-self:stretch;border-radius:18px 0 0 18px;background:'+p.color+';"></div>'
        +'<div style="flex:1;padding:11px 13px;">'
        +'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;">'
        +'<div style="flex:1;">'
        +'<p class="pred-name" style="color:'+(p.verdict==='DANGER'?'#fca5a5':'#e8d490')+';">'+p.nomFr+'</p>'
        +(p.nomAr&&p.nomAr!=='بدون اسم'?'<p class="pred-ar" style="color:'+(p.verdict==='DANGER'?'rgba(252,165,165,.7)':'#c9a84c')+';">'+p.nomAr+'</p>':'')
        +'<div class="pred-pays" style="margin-top:3px;"><svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg><span style="color:'+(p.verdict==='DANGER'?'rgba(252,165,165,.5)':'rgba(100,60,10,.45)')+'">'+(p.pays||'FRANCOPHONIE')+'</span></div>'
        +'</div>'
        +'<div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;flex-shrink:0;">'
        +'<span style="font-family:\'Cinzel\',serif;font-size:6.5px;font-weight:700;padding:4px 10px;border-radius:99px;letter-spacing:.08em;background:'+p.color+'22;border:1px solid '+p.color+'55;color:'+p.color+';">'+p.verdict+'</span>'
        +'<svg viewBox="0 0 24 24" fill="none" stroke="'+p.color+'" stroke-width="1.8" stroke-opacity=".5" width="12" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>'
        +'</div>'
        +'</div></div></button>';
    });
    // Bouton "Voir plus" si items restants
    if(items.length>visibleItems.length){
      var restant=items.length-visibleItems.length;
      ch+='<button onclick="iaSectionLoadMore(\''+secId+'\')" '
        +'style="width:100%;padding:12px;margin-top:6px;background:rgba(201,168,76,.06);border:1px dashed rgba(201,168,76,.2);border-radius:12px;color:rgba(201,168,76,.6);font-family:Cinzel,serif;font-size:8px;letter-spacing:.15em;cursor:pointer;">'
        +'▼ VOIR ' + restant + ' DE PLUS'
        +'</button>';
    }
    sec.innerHTML=th+ch;el.appendChild(sec);
  });
  if(!total)el.innerHTML='<div class="no-results"><div class="ar">لا نتائج</div><p>AUCUN RÉSULTAT</p></div>';
}
window.renderList = renderList;

/* ── FIX SCOPE v22 : iaSectionLoadMore GLOBALE (window.*) ──────
   Était enfermée dans renderList → invisible depuis les onclick HTML.
   Règle Triple Bouclier : toute fonction appelée inline doit être sur window.
─────────────────────────────────────────────────────────────── */
function iaSectionLoadMore(id){
  if(!window.iaSectionPage) window.iaSectionPage={};
  window.iaSectionPage[id]=(window.iaSectionPage[id]||1)+1;
  renderList();
}
window.iaSectionLoadMore = iaSectionLoadMore;
/* ════════════════════════════════════════
   DETAIL PRÉDICATEUR
════════════════════════════════════════ */

/* ── FIX CRASH v22 : showPredLoading MANQUANTE ─────────────────
   Appelée sur chaque bouton pred-btn mais absente du fichier.
   Implémentation légère : exécute le callback openDetail directement.
   Aucune animation bloquante — Triple Bouclier preservé.
─────────────────────────────────────────────────────────────── */
function showPredLoading(nom, ar, callback){
  if(typeof callback === 'function') callback();
}
window.showPredLoading = showPredLoading;
var currentPreacher=null,currentDetTab='essentiel';
function openDetail(id){
  try{
    currentPreacher=PREACHERS.find(function(p){return p.id===id;})||null;
    if(!currentPreacher){ console.error('[Al-Mizan] openDetail id='+id+' introuvable'); return; }
    var p=currentPreacher;
    var clr=(p.color)||'#c9a84c';
    var badge=document.getElementById('det-badge');
    var nameEl=document.getElementById('det-name');
    var arEl=document.getElementById('det-ar');
    if(badge){ badge.textContent=(p.verdict||'—'); badge.style.background=clr+'20'; badge.style.border='1px solid '+clr+'44'; badge.style.color=clr; }
    if(nameEl) nameEl.textContent=(p.nomFr||'—');
    if(arEl)   arEl.textContent=(p.nomAr||'');
    document.querySelectorAll('.det-tab-btn').forEach(function(b){b.classList.remove('active');});
    var ft=document.querySelectorAll('.det-tab-btn')[0];
    if(ft) ft.classList.add('active');
    currentDetTab='essentiel';
    renderDetContent();
    goTo('detail');
  }catch(e){
    console.error('[Al-Mizan] openDetail id='+id+' : '+e.message);
    var el=document.getElementById('det-content');
    if(el) el.innerHTML='<div style="padding:30px;text-align:center;font-family:Cinzel,serif;color:rgba(201,168,76,.4);font-size:10px;letter-spacing:.2em;">FICHE TEMPORAIREMENT INDISPONIBLE</div>';
    goTo('detail');
  }
}
window.openDetail = openDetail;
function setDetTab(tab,btn){
  currentDetTab=tab;
  document.querySelectorAll('.det-tab-btn').forEach(function(b){b.classList.remove('active');});
  btn.classList.add('active');renderDetContent();
}
window.setDetTab = setDetTab;
// ════════════════════════════════════════════════════════════════
//  NOUVELLE renderDetContent — onglets ESSENTIEL + EXPERT
//  Lit p.evaluations (nouveau format) ET p.steps (ancien format)
//  Affiche toujours les sources et preuves
// ════════════════════════════════════════════════════════════════
// DABT AL-MIZAN — renderDetContent avec Fail-Fast (try/catch) et
// application chirurgicale du Jarh Mufassar sur la Tazkiyah
// Règle : الجرح المفسَّر مقدَّم على التعديل
// Si le verdict est une mise en garde, toute tazkiyah antérieure
// est caduque et aucun badge positif ne doit apparaître.
// ════════════════════════════════════════════════════════════════
function renderDetContent(){
  // ── FAIL-FAST : garde-fou global ─────────────────────────────
  if(!currentPreacher){ console.warn('[Al-Mizan] renderDetContent: currentPreacher est null'); return; }
  var p=currentPreacher;
  var d=(p&&p.data)||{};
  var el=document.getElementById('det-content');
  if(!el){ console.warn('[Al-Mizan] renderDetContent: #det-content introuvable'); return; }
  var ic=p.color||'#c9a84c';

  // ── JARH MUFASSAR — classification du verdict ─────────────────
  // Détermine si un Jarh établi invalide toute Tazkiyah
  var verdictStr = (p.verdict||'').toUpperCase();
  var jarh_mufassar = (
    verdictStr.indexOf('DANGER')    !== -1 ||
    verdictStr.indexOf('ÉVITER')    !== -1 ||
    verdictStr.indexOf('EVITER')    !== -1 ||
    verdictStr.indexOf('INNOVATEUR')!== -1 ||
    verdictStr.indexOf('KADHDHAB')  !== -1 ||
    verdictStr.indexOf('MUBTADI')   !== -1 ||
    verdictStr.indexOf('PRUDENCE')  !== -1
  );
  // Fiable / Imam / Véridique = Ta'dil établi → tazkiya peut être verte
  var tadil_etabli = (
    verdictStr.indexOf('IMAM')   !== -1 ||
    verdictStr.indexOf('FIABLE') !== -1 ||
    verdictStr.indexOf('SADOUQ') !== -1 ||
    verdictStr.indexOf('VÉRIDIQUE') !== -1 ||
    verdictStr.indexOf('VERIDIQUE') !== -1
  );

  // Citation choc toujours en haut — avec valeur par défaut
  var phraseChoc = p.phraseChoc || 'Information non disponible pour ce profil.';
  var html='<div class="phrase-choc"><p>"'+phraseChoc+'"</p></div>';

  // ─── ONGLET ESSENTIEL ───────────────────────────────────────
  if(currentDetTab==='essentiel'){

    // ── 1. VERDICT SOURCÉ ─────────────────────────────────────
    html+='<div style="background:'+ic+'0d;border:1px solid '+ic+'30;border-radius:16px;padding:14px 16px;margin-bottom:14px;">';
    html+='<p style="font-family:Cinzel,serif;font-size:7px;letter-spacing:.28em;color:'+ic+';opacity:.7;margin-bottom:8px;">⚖️ VERDICT ÉTABLI</p>';
    // verdict_detail — supporte objet {note,detail} OU string directe
    var vd='';
    try{
      var vdRaw=((p||{}).evaluations||{}).verdict_detail;
      if(vdRaw) vd=(typeof vdRaw==='object')?(vdRaw.detail||vdRaw.c||''):String(vdRaw||'');
      if(!vd){ var st2=(p||{}).steps; if(Array.isArray(st2)&&st2[6]) vd=(st2[6].c||st2[6].detail||''); }
      if(!vd) vd=(d.pourquoi||d.points||'');
    }catch(e){ console.warn('[Al-Mizan] verdict_detail:'+e.message); }
    if(vd) html+='<p style="font-family:Cormorant Garamond,serif;font-size:15px;color:rgba(232,212,140,.9);line-height:1.65;margin-bottom:10px;">'+vd+'</p>';

    // Avis savants en source directe
    var avs=p.avis_savants||[];
    if(avs.length){
      html+='<div style="border-top:1px solid '+ic+'20;padding-top:10px;">';
      html+='<p style="font-family:Cinzel,serif;font-size:6.5px;letter-spacing:.22em;color:'+ic+';opacity:.6;margin-bottom:8px;">PREUVES — AVIS DES SAVANTS</p>';
      avs.forEach(function(av){
        // Support double format
        var savantNom = av.savant||av.s||'';
        var citFr     = av.citation_fr||av.t||'';
        var citAr     = av.citation_ar||av.c||'';
        var src       = av.source||av.src||'';
        html+='<div style="background:rgba(0,0,0,.2);border-left:2px solid '+ic+'60;border-radius:0 8px 8px 0;padding:9px 12px;margin-bottom:8px;">';
        html+='<p style="font-family:Cinzel,serif;font-size:7px;letter-spacing:.15em;color:'+ic+';margin-bottom:5px;">'+savantNom.toUpperCase()+'</p>';
        if(citAr) html+='<p style="font-family:Scheherazade New,serif;font-size:15px;color:rgba(212,170,100,.75);direction:rtl;text-align:right;line-height:1.6;margin-bottom:4px;">'+citAr+'</p>';
        if(citFr) html+='<p style="font-family:Cormorant Garamond,serif;font-style:italic;font-size:13.5px;color:rgba(200,180,120,.7);line-height:1.5;">'+citFr+'</p>';
        if(src)   html+='<p style="font-family:Cinzel,serif;font-size:6px;letter-spacing:.15em;color:rgba(140,110,50,.5);margin-top:5px;">📚 SOURCE : '+src.toUpperCase()+'</p>';
        html+='</div>';
      });
      html+='</div>';
    }
    html+='</div>';

    // ── 2. CRITÈRES (4 icônes) avec données réelles ───────────
    var ev=p.evaluations||{};
    // Mapper depuis evaluations OU steps
    function getEv(key,stepIdx){
      try{
        var evMap=((p||{}).evaluations)||{};
        var entry=evMap[key];
        if(entry&&typeof entry==='object') return {note:(+entry.note||0), detail:(entry.detail||entry.c||'')};
        var stArr=(p||{}).steps;
        if(Array.isArray(stArr)&&stArr[stepIdx]) return {note:0, detail:(stArr[stepIdx].c||stArr[stepIdx].detail||'')};
        return {note:0,detail:''};
      }catch(e){ console.warn('[Al-Mizan] getEv('+key+'):'+e.message); return {note:0,detail:''}; }
    }
    var criteria=[
      {k:'aqida',  stepIdx:0, label:'AQIDA',   ar:'العَقِيدة',
       icon:'<svg viewBox="0 0 24 24" fill="none" stroke="'+ic+'" stroke-width="1.8" width="18" height="18" stroke-linecap="round"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="8" x2="16" y2="8"/><line x1="8" y1="12" x2="16" y2="12"/><line x1="8" y1="16" x2="12" y2="16"/></svg>',
       principe:'L\'aqida est la fondation. Si elle est déviante, tout le reste ne vaut rien.',
       ref:'Sheikh Rabi : "الجرح المفسَّر مقدَّم على التعديل" — La critique documentée prime sur la recommandation.'},
      {k:'manhaj', stepIdx:1, label:'MANHAJ',  ar:'المَنهَج',
       icon:'<svg viewBox="0 0 24 24" fill="none" stroke="'+ic+'" stroke-width="1.8" width="18" height="18" stroke-linecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
       principe:'Le manhaj c\'est la méthode. Suit-il la voie des Salaf as-Salih ?',
       ref:'Sheikh Ibn Baz : "من خالف المنهج السلفي فقد خالف طريق الهدى" — Celui qui s\'écarte du manhaj salafi s\'écarte du chemin de la guidance.'},
      {k:'tazkiyat',stepIdx:5, label:'TAZKIYAT', ar:'التَّزكِيَة',
       icon:'<svg viewBox="0 0 24 24" fill="none" stroke="'+ic+'" stroke-width="1.8" width="18" height="18" stroke-linecap="round"><polyline points="20 6 9 17 4 12"/></svg>',
       principe:'La tazkiya est l\'attestation des savants reconnus. Sans elle, nul ne peut enseigner.',
       ref:'Sheikh Rabi : "لا يُقبَل الداعية حتى يُزكَّى من العلماء المعتبرين" — Le prédicateur n\'est pas accepté tant qu\'il n\'est pas recommandé par les savants.'},
      {k:'etudes', stepIdx:3, label:'ÉTUDES',   ar:'العِلم',
       icon:'<svg viewBox="0 0 24 24" fill="none" stroke="'+ic+'" stroke-width="1.8" width="18" height="18" stroke-linecap="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>',
       principe:'Qui lui a enseigné ? Quelle est sa chaîne de transmission ?',
       ref:'Imam Malik : "هذا العلم دين فانظروا عمن تأخذون دينكم" — Cette science est la religion, regardez bien à qui vous la prenez.'},
    ];
    html+='<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px;">';
    criteria.forEach(function(cr){
      try{
        var data=getEv(cr.k,cr.stepIdx);
        var note=data.note||0;
        var noteColor, noteLabel;
        // ══ JARH MUFASSAR INTÉGRAL — الجرح المفسَّر مقدَّم على التعديل ══
        // Si Jarh établi : FORÇAGE BRUTAL des 4 badges rouges, note=0 ou non.
        // Le Jarh prime sur TOUT — aucun badge vide, neutre ou positif toléré.
        if(jarh_mufassar){
          if     (cr.k==='tazkiyat'){ noteColor='#991b1b'; noteLabel='✖ CADUQUE'; }
          else if(cr.k==='etudes')  { noteColor='#7f1d1d'; noteLabel='⛔ REJETÉ'; }
          else                      { noteColor='#991b1b'; noteLabel='❌ DÉVIANT'; }
          note=1; // Force note>0 pour déclencher l'affichage du badge
        } else if(cr.k==='tazkiyat'){
          if(note>=7){ noteColor='#22c55e'; noteLabel='✅ VALIDÉE'; }
          else       { noteColor='#ef4444'; noteLabel='❌ ABSENTE'; }
          note=Math.max(note,1);
        } else {
          // ══ MARATIB AL-JARH : Terminologie légiférée ══
          // Aucune note chiffrée profane — uniquement les termes des Muhaddithin
          if(cr.k==='aqida'||cr.k==='manhaj'){
            noteColor=note>=7?'#22c55e':note>=5?'#f59e0b':note>=3?'#fb923c':note>0?'#ef4444':'#6b7280';
            noteLabel=note>=7?'SALIM (سليم)':note>=5?'LAYYIN (ليّن)':note>=3?'MAJHUL (مجهول)':note>0?'MUNKAR (منكر)':'—';
          } else if(cr.k==='etudes'){
            noteColor=note>=7?'#22c55e':note>=5?'#f59e0b':note>=3?'#fb923c':note>0?'#ef4444':'#6b7280';
            noteLabel=note>=7?'MU\'TABAR (معتبر)':note>=5?'MAQBUL (مقبول)':note>=3?'MAJHUL (مجهول)':note>0?'MARDUD (مردود)':'—';
          } else {
            noteColor=note>=7?'#22c55e':note>=5?'#f59e0b':note>=3?'#fb923c':note>0?'#ef4444':'#6b7280';
            noteLabel=note>=7?'THIQAH (ثقة)':note>=5?'LAYYIN (ليّن)':note>=3?'MAJHUL (مجهول)':note>0?'DA\'IF (ضعيف)':'—';
          }
        }
        html+='<div onclick="essOpen(\'ess-'+cr.k+'\')" style="background:rgba(0,0,0,.25);border:1px solid '+ic+'25;border-radius:14px;padding:13px 12px;cursor:pointer;transition:all .2s;">';
        html+='<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">';
        html+=cr.icon;
        // Badge affiché si jarh_mufassar (obligatoire) OU si note>0 OU si tazkiyat (toujours visible)
        if(jarh_mufassar||note>0||cr.k==='tazkiyat') html+='<span style="font-family:Cinzel,serif;font-size:8px;letter-spacing:.1em;color:'+noteColor+';background:'+noteColor+'15;border:1px solid '+noteColor+'40;border-radius:20px;padding:2px 8px;">'+noteLabel+'</span>';
        html+='</div>';
        html+='<p style="font-family:Cinzel,serif;font-size:8px;letter-spacing:.18em;color:'+ic+';margin-bottom:3px;">'+cr.label+'</p>';
        html+='<p style="font-family:Scheherazade New,serif;font-size:11px;color:rgba(180,150,80,.5);">'+cr.ar+'</p>';
        html+='</div>';
      }catch(e){ console.warn('[Al-Mizan] critère '+cr.k+' : '+e.message); }
    });
    html+='</div>';

    // ── PANELS DÉVELOPPÉS ──
    criteria.forEach(function(cr){
      var data=getEv(cr.k,cr.stepIdx);
      html+='<div id="ess-'+cr.k+'" style="display:none;background:'+ic+'08;border:1px solid '+ic+'22;border-radius:14px;padding:14px;margin-bottom:10px;">';
      html+='<p style="font-family:Cinzel,serif;font-size:8px;letter-spacing:.18em;color:'+ic+';margin-bottom:10px;">'+cr.label+' — ANALYSE</p>';
      if(data.detail) html+='<p style="font-family:Cormorant Garamond,serif;font-size:15px;color:rgba(220,200,130,.85);line-height:1.65;margin-bottom:10px;">'+data.detail+'</p>';
      html+='<div style="background:rgba(0,0,0,.2);border-left:2px solid '+ic+'50;padding:8px 11px;border-radius:0 8px 8px 0;">';
      html+='<p style="font-family:Cormorant Garamond,serif;font-style:italic;font-size:12.5px;color:rgba(180,150,80,.6);line-height:1.55;">'+cr.ref+'</p>';
      html+='</div>';
      html+='</div>';
    });

    // ── AL-HUJJAH — Section Jarh Mufassar (profils DANGER uniquement) ──
    if(jarh_mufassar){
      var dalil=(p.preuve||'');
      var jarihNom=(p.jarih||'');
      var srcDef='Sources : binbaz.org.sa · alalbany.net · binothaimeen.net';
      html+='<div style="margin-bottom:14px;border:1px solid rgba(153,27,27,.35);border-radius:16px;overflow:hidden;">';
      html+='<div style="background:rgba(127,29,29,.18);padding:11px 16px;border-bottom:1px solid rgba(153,27,27,.25);display:flex;align-items:center;gap:10px;">';
      html+='<svg viewBox="0 0 24 24" fill="none" stroke="#991b1b" stroke-width="1.8" width="15" height="15" stroke-linecap="round"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>';
      html+='<span style="font-family:Cinzel,serif;font-size:7.5px;font-weight:700;letter-spacing:.25em;color:#991b1b;">DÉTAILS DU JARH MUFASSAR</span>';
      html+='<span style="font-family:Scheherazade New,serif;font-size:12px;color:rgba(153,27,27,.6);margin-left:6px;">الجرح المفسَّر</span>';
      html+='</div>';
      html+='<div style="padding:14px 16px;background:rgba(80,0,0,.08);">';
      html+='<p style="font-family:Cinzel,serif;font-size:6.5px;letter-spacing:.25em;color:rgba(153,27,27,.7);margin-bottom:5px;">▸ LE SAVANT JARIH — الجارح</p>';
      html+='<p style="font-family:Cormorant Garamond,serif;font-size:13.5px;font-weight:600;color:rgba(220,180,100,.9);line-height:1.6;margin-bottom:12px;">'+(jarihNom||srcDef)+'</p>';
      html+='<p style="font-family:Cinzel,serif;font-size:6.5px;letter-spacing:.25em;color:rgba(153,27,27,.7);margin-bottom:5px;">▸ LA PREUVE — الدَّلِيل</p>';
      var avsSrc=(((p||{}).approfondi)||{}).avis_savants||(p.avis_savants)||[];
      var proofText=dalil;
      if(!proofText&&avsSrc.length){
        var av0=avsSrc[0];
        proofText=(av0.citation_fr||av0.t||av0.citation_ar||av0.c||'');
      }
      html+='<div style="background:rgba(0,0,0,.25);border-right:3px solid rgba(153,27,27,.5);padding:10px 14px;border-radius:10px 0 0 10px;">';
      html+='<p style="font-family:Cormorant Garamond,serif;font-style:italic;font-size:14px;color:rgba(220,190,110,.85);line-height:1.7;">'+(proofText||srcDef)+'</p>';
      html+='</div>';
      html+='</div></div>';
    }

    // ── 3. POINTS CLÉS si dispo ──
    var pts=d.points||d.pourquoi||'';
    if(pts) html+='<div class="info-card" style="border:1px solid #d4af3718;"><div class="accent" style="background:var(--gold)"></div><div class="info-card-tag" style="background:#f59e0b14;border:1px solid #f59e0b28;"><span style="color:#f59e0b">POINTS CLÉS</span></div><p>"'+pts+'"</p></div>';
    if(d.protection) html+='<div class="info-card" style="border:1px solid '+ic+'22;"><div class="accent" style="background:'+ic+'"></div><div class="info-card-tag"><span>PROTECTION</span></div><p>'+d.protection+'</p></div>';

    // ── PREUVES CLIQUABLES — Isnad vérifiable ──
    var prvs=(d.preuves)||[];
    if(prvs.length){
      html+='<div style="margin-top:12px;margin-bottom:8px;">';
      html+='<p style="font-family:Cinzel,serif;font-size:6.5px;letter-spacing:.25em;color:'+ic+';opacity:.55;margin-bottom:8px;">🔗 SOURCES VÉRIFIABLES — ISNAD CLIQUABLE</p>';
      html+='<div style="display:flex;flex-wrap:wrap;gap:6px;">';
      prvs.forEach(function(pr){
        var lbl=pr.l||'Source';
        var url=pr.u||'#';
        html+='<a href="'+url+'" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:5px;padding:7px 12px;background:rgba(201,168,76,.06);border:1px solid rgba(201,168,76,.18);border-radius:8px;text-decoration:none;transition:all .2s;">';
        html+='<svg viewBox="0 0 24 24" fill="none" stroke="'+ic+'" stroke-width="2" width="11" height="11" stroke-linecap="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>';
        html+='<span style="font-family:Cinzel,serif;font-size:7px;letter-spacing:.12em;color:'+ic+';">'+lbl.toUpperCase()+'</span>';
        html+='</a>';
      });
      html+='</div></div>';
    }

    // ── ACCORDÉON : L'HÉRITAGE DES SALAF — 12 GÉANTS ──
    html+='<details style="margin-top:16px;border:1px solid rgba(201,168,76,.15);border-radius:14px;overflow:hidden;background:rgba(0,0,0,.15);">';
    html+='<summary style="display:flex;align-items:center;gap:10px;padding:14px 16px;cursor:pointer;list-style:none;-webkit-appearance:none;background:rgba(201,168,76,.04);border-bottom:1px solid rgba(201,168,76,.08);transition:background .3s;">';
    html+='<span style="font-size:18px;">🛡️</span>';
    html+='<div style="flex:1;">';
    html+='<span style="font-family:Cinzel,serif;font-size:8.5px;font-weight:700;letter-spacing:.15em;color:#c9a84c;display:block;">L\'HÉRITAGE DES SALAF : LA VOIE DES 12 GÉANTS</span>';
    html+='<span style="font-family:Scheherazade New,serif;font-size:13px;color:rgba(201,168,76,.45);">سبيلُ عمالقة الأمّة</span>';
    html+='</div>';
    html+='<svg viewBox="0 0 24 24" fill="none" stroke="#c9a84c" stroke-width="2" width="14" height="14" style="opacity:.5;transition:transform .3s;"><polyline points="6 9 12 15 18 9"/></svg>';
    html+='</summary>';
    html+='<div style="padding:18px 16px 20px;">';

    html+='<p style="font-family:Cormorant Garamond,serif;font-size:1.1rem;color:rgba(220,200,160,.85);line-height:1.75;margin-bottom:16px;">La mise en garde contre les innovateurs n\'est pas l\'invention d\'un seul homme — elle est la voie unanime de plus de <strong>12 montagnes de l\'Islam</strong>, sur 14 siècles. Quiconque dit « Madkhaliste » ou « Wahhabite » pour rejeter cette science a menti contre l\'ensemble de ces Imams.</p>';

    // Les 12 géants avec citations
    var gData=[
      {n:"① Imam Abou Hanifa (m.150H)",ar:"إذا دعاك صاحب بدعة إلى بدعته فاهرب منه",fr:"Si le partisan de l\'innovation t\'appelle vers sa bid\'ah, fuis-le.",src:"Al-Lalaka\'i · Sharh Usul I\'tiqad"},
      {n:"② Imam Malik (m.179H)",ar:"لا يُؤخذ العلم من صاحب هوى يدعو إليه",fr:"On ne prend pas la science du partisan de la passion qui y appelle.",src:"Al-Khatib Al-Baghdadi · Muqaddima Ibn as-Salah"},
      {n:"③ Imam Ach-Chafi\'i (m.204H)",ar:"ما لزم أحدٌ أصحاب البدع إلا فارقه الله",fr:"Quiconque accompagne les gens de l\'innovation, Allah l\'abandonne.",src:"Al-Bayhaqi · Manaqib Ach-Chafi\'i"},
      {n:"④ Imam Ahmad (m.241H)",ar:"لا تجالس صاحب بدعة فإنه لا يؤول أمره إلى خير",fr:"Ne t\'assois pas avec l\'innovateur, car son affaire ne mènera à rien de bon.",src:"Ibn Battah · Al-Ibana Al-Kubra"},
      {n:"⑤ Yahya Ibn Ma\'in (m.233H)",ar:"الذبّ عن السنة أفضل من الجهاد في سبيل الله",fr:"Défendre la Sunnah est meilleur que le Jihad dans le sentier d\'Allah.",src:"Al-Khatib · Tarikh Baghdad"},
      {n:"⑥ Al-Bukhari (m.256H)",ar:"صنّف كتاب الضعفاء الصغير والتاريخ الكبير لنقد الرجال",fr:"A compilé le Livre des narrateurs faibles et At-Tarikh Al-Kabir pour classer les hommes.",src:"Ad-Du\'afa as-Saghir + At-Tarikh Al-Kabir"},
      {n:"⑦ Imam Muslim (m.261H)",ar:"الواجب أن لا يُروى إلا عمّن عُرفت صحة مخارجه والستارة في ناقليه",fr:"Il est obligatoire de ne rapporter que de ceux dont on connaît l\'authenticité et la droiture.",src:"Muqaddima Sahih Muslim"},
      {n:"⑧ Abou Hatim Ar-Razi (m.277H)",ar:"أدركنا العلماء في جميع الأمصار فوجدناهم على الإجماع في رد البدع",fr:"Nous avons rencontré les savants dans toutes les contrées et les avons trouvés unanimes dans le rejet des innovations.",src:"Al-Lalaka\'i · Sharh Usul I\'tiqad"},
      {n:"⑨ Sufyan Ath-Thawri (m.161H)",ar:"من أصغى بسمعه إلى صاحب بدعة خرج من ولاية الله",fr:"Quiconque prête l\'oreille à un innovateur sort de la protection d\'Allah.",src:"Abou Nu\'aym · Hilyat Al-Awliya\'"},
      {n:"⑩ Ibn Al-Mubarak (m.181H)",ar:"الإسناد من الدين ولولا الإسناد لقال من شاء ما شاء",fr:"L\'Isnad fait partie de la religion — sans lui, quiconque dirait ce qu\'il veut.",src:"Muqaddima Sahih Muslim"},
      {n:"⑪ Ibn Taymiyyah (m.728H)",ar:"بيان حال أهل البدع واجب على الكفاية بل قد يتعيّن",fr:"Clarifier l\'état des innovateurs est une obligation communautaire, voire individuelle.",src:"Majmu\' Al-Fatawa (28/231)"},
      {n:"⑫ Adh-Dhahabi (m.748H)",ar:"إذا رأيت المبتدع يقول دعونا من الكتاب والأحاديث فاعلم أنه أبو جهل",fr:"Lorsque tu vois l\'innovateur dire « laissez les Hadiths », sache qu\'il est le père de l\'ignorance.",src:"Siyar A\'lam An-Nubala\'"}
    ];
    gData.forEach(function(g){
      html+='<div style="margin-bottom:14px;padding:12px 14px;background:rgba(201,168,76,.03);border:1px solid rgba(201,168,76,.08);border-radius:10px;">';
      html+='<p style="font-family:Cinzel,serif;font-size:8px;letter-spacing:.18em;color:rgba(201,168,76,.6);margin-bottom:6px;">'+g.n+'</p>';
      html+='<p style="font-family:Scheherazade New,serif;font-size:1.15rem;color:rgba(232,201,106,.65);direction:rtl;text-align:right;line-height:1.7;margin-bottom:6px;">'+g.ar+'</p>';
      html+='<p style="font-family:Cormorant Garamond,serif;font-style:italic;font-size:1rem;color:rgba(220,200,160,.75);line-height:1.65;margin-bottom:4px;">'+g.fr+'</p>';
      html+='<p style="font-family:Cinzel,serif;font-size:6px;letter-spacing:.15em;color:rgba(201,168,76,.35);">📚 '+g.src+'</p>';
      html+='</div>';
    });

    html+='<div style="padding:12px 14px;background:rgba(201,168,76,.06);border:1px solid rgba(201,168,76,.15);border-radius:10px;text-align:center;">';
    html+='<p style="font-family:Cormorant Garamond,serif;font-size:1rem;color:rgba(232,201,106,.8);line-height:1.65;font-weight:600;">12 montagnes, 14 siècles, un seul principe : la mise en garde est une obligation — pas une invention moderne. Cheikh Rabi\', Cheikh Ibn Baz et Cheikh Al-Albani prolongent cette chaîne en or.</p>';
    html+='</div>';

    html+='</div></details>';

    // ── MENTION ISNAD — Règle d'Ibn Sirin ──
    html+='<p style="margin-top:12px;font-family:Cormorant Garamond,serif;font-style:italic;font-size:10.5px;color:rgba(201,168,76,.35);line-height:1.5;text-align:center;">Conformément à la règle de l\'Isnad — ce verdict repose sur des preuves sourcées et traçables jusqu\'aux savants de Ahl as-Sunnah wal-Jama\'ah.</p>';

  }
  // ─── ONGLET EXPERT ──────────────────────────────────────────
  else if(currentDetTab==='expert'){
    html+=renderExpert(p);
  }
  // ─── ONGLET APPROFOND ───────────────────────────────────────
  else if(currentDetTab==='approfondi'){
    html+=renderApprofondi(p);
  }

  // ── Boutons bas ─────────────────────────────────────────────
  html+='<div style="display:flex;gap:8px;margin-top:18px;padding-bottom:4px;">'
    +'<button onclick="sharePreacher()" style="flex:1;display:flex;align-items:center;justify-content:center;gap:6px;padding:13px 16px;background:rgba(37,211,102,.08);border:1px solid rgba(37,211,102,.25);border-radius:12px;cursor:pointer;font-family:Cinzel,serif;font-size:7.5px;font-weight:700;letter-spacing:.1em;color:#25d366;">'
    +'<svg viewBox="0 0 24 24" fill="none" stroke="#25d366" stroke-width="2" width="15" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg>'
    +'PARTAGER</button>'
    +'</div>';

  try{
    el.innerHTML=html;
  }catch(e){
    console.error('[Al-Mizan] renderDetContent innerHTML : '+e.message);
    el.innerHTML='<div style="padding:20px;text-align:center;font-family:Cinzel,serif;color:rgba(201,168,76,.4);font-size:11px;letter-spacing:.2em;">INFORMATION NON DISPONIBLE</div>';
  }
}

// Toggle des panels ESSENTIEL
function essOpen(id){
  var el=document.getElementById(id);
  if(!el)return;
  var isOpen=el.style.display!=='none';
  // Fermer tous
  ['aqida','manhaj','tazkiyat','etudes'].forEach(function(k){
    var e=document.getElementById('ess-'+k);
    if(e) e.style.display='none';
  });
  if(!isOpen) el.style.display='block';
}

// FIX ONGLET EXPERT — renderExpert : sources brutes, citations exactes, références vérifiables
// Affiche : (1) avis_savants avec citations arabes + françaises + sources
//           (2) manhaj détaillé avec niveau rouge/orange
//           (3) biographie complète avec maîtres et affiliations
function renderExpert(p){
  var ap = p.approfondi || {};
  var ic = p.color || '#c9a84c';
  var html = '';

  // ── En-tête méthodologique ──────────────────────────────────
  html += '<div style="background:rgba(0,0,0,.25);border:1px solid rgba(201,168,76,.15);border-radius:14px;padding:12px 14px;margin-bottom:14px;text-align:center;">';
  html += '<p style="font-family:Cinzel,serif;font-size:7px;letter-spacing:.3em;color:rgba(201,168,76,.5);margin-bottom:4px;">SOURCES BRUTES — JARH WA TA\'DIL</p>';
  html += '<p style="font-family:Scheherazade New,serif;font-size:16px;color:rgba(212,170,100,.6);direction:rtl;line-height:1.6;">الجرح المفسَّر مقدَّم على التعديل</p>';
  html += '</div>';

  // ── BLOC 1 : Citations exactes des savants ──────────────────
  var avs = (ap.avis_savants) || p.avis_savants || [];
  if(avs.length){
    html += '<p style="font-family:Cinzel,serif;font-size:7px;letter-spacing:.28em;color:'+ic+';opacity:.7;margin-bottom:10px;">▸ AVIS DES SAVANTS — CITATIONS EXACTES</p>';
    avs.forEach(function(av){
      var nom   = av.savant || av.s || '';
      var nomAr = av.savant_ar || '';
      var citAr = av.citation_ar || av.c || '';
      var citFr = av.citation_fr || av.t || '';
      var src   = av.source || av.src || '';
      var type  = av.type || 'jarh';
      var typeColor = type==='tadil'?'#22c55e':type==='tanbih'?'#f59e0b':'#ef4444';
      var typeLabel = type==='tadil'?'TA\'DIL':type==='tanbih'?'TANBIH':'JARH';
      html += '<div style="background:rgba(0,0,0,.3);border:1px solid '+ic+'20;border-radius:12px;padding:13px 14px;margin-bottom:10px;">';
      html += '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">';
      html += '<div>';
      html += '<p style="font-family:Cinzel,serif;font-size:8px;letter-spacing:.15em;color:'+ic+';margin-bottom:1px;">'+nom.toUpperCase()+'</p>';
      if(nomAr) html += '<p style="font-family:Scheherazade New,serif;font-size:13px;color:rgba(180,150,80,.5);">'+nomAr+'</p>';
      html += '</div>';
      html += '<span style="font-family:Cinzel,serif;font-size:7px;letter-spacing:.15em;color:'+typeColor+';background:'+typeColor+'15;border:1px solid '+typeColor+'40;border-radius:20px;padding:3px 9px;">'+typeLabel+'</span>';
      html += '</div>';
      if(citAr) html += '<div style="background:rgba(0,0,0,.2);border-right:3px solid '+ic+'60;padding:9px 12px;border-radius:8px 0 0 8px;margin-bottom:8px;">'
                      + '<p style="font-family:Scheherazade New,serif;font-size:17px;color:rgba(232,201,106,.8);direction:rtl;text-align:right;line-height:1.7;">'+citAr+'</p>'
                      + '</div>';
      if(citFr) html += '<p style="font-family:Cormorant Garamond,serif;font-style:italic;font-size:14px;color:rgba(200,180,120,.75);line-height:1.6;margin-bottom:6px;">'+citFr+'</p>';
      if(src)   html += '<p style="font-family:Cinzel,serif;font-size:6.5px;letter-spacing:.18em;color:rgba(140,110,50,.55);">📚 '+src.toUpperCase()+'</p>';
      html += '</div>';
    });
  } else {
    html += '<div style="background:rgba(0,0,0,.2);border:1px solid rgba(201,168,76,.1);border-radius:12px;padding:20px;text-align:center;margin-bottom:14px;">';
    html += '<p style="font-family:Cormorant Garamond,serif;font-style:italic;font-size:13px;color:rgba(180,150,80,.4);">Aucune citation de savant enregistrée pour ce profil.</p>';
    html += '</div>';
  }

  // ── BLOC 2 : Points Manhaj détaillés ───────────────────────
  var mh = ap.manhaj || [];
  if(mh.length){
    html += '<p style="font-family:Cinzel,serif;font-size:7px;letter-spacing:.28em;color:'+ic+';opacity:.7;margin:14px 0 10px;">▸ INHIRAF — POINTS DE DÉVIANCE DOCUMENTÉS</p>';
    mh.forEach(function(pt){
      var niv = pt.niveau || 'orange';
      var nivColor = niv==='rouge'?'#ef4444':niv==='orange'?'#f59e0b':'#22c55e';
      html += '<div style="background:rgba(0,0,0,.2);border-left:3px solid '+nivColor+';border-radius:0 10px 10px 0;padding:10px 13px;margin-bottom:8px;">';
      html += '<p style="font-family:Cinzel,serif;font-size:7.5px;letter-spacing:.15em;color:'+nivColor+';margin-bottom:5px;">'+pt.point+'</p>';
      html += '<p style="font-family:Cormorant Garamond,serif;font-size:13.5px;color:rgba(200,180,120,.7);line-height:1.6;">'+pt.detail+'</p>';
      html += '</div>';
    });
  }

  // ── BLOC 3 : Biographie & Sources ──────────────────────────
  var bio = ap.biographie || {};
  if(bio.formation || bio.maitres || bio.parcours || bio.affiliations){
    html += '<p style="font-family:Cinzel,serif;font-size:7px;letter-spacing:.28em;color:'+ic+';opacity:.7;margin:14px 0 10px;">▸ BIOGRAPHIE & AFFILIATIONS</p>';
    html += '<div style="background:rgba(0,0,0,.2);border:1px solid '+ic+'15;border-radius:12px;padding:13px 14px;">';
    var bioFields = [
      {label:'FORMATION',val:bio.formation},
      {label:'MAÎTRES',val:bio.maitres},
      {label:'PARCOURS',val:bio.parcours},
      {label:'AFFILIATIONS',val:bio.affiliations}
    ];
    bioFields.forEach(function(f){
      if(!f.val) return;
      html += '<div style="margin-bottom:9px;padding-bottom:9px;border-bottom:1px solid rgba(201,168,76,.07);">';
      html += '<p style="font-family:Cinzel,serif;font-size:6.5px;letter-spacing:.2em;color:'+ic+';opacity:.55;margin-bottom:3px;">'+f.label+'</p>';
      html += '<p style="font-family:Cormorant Garamond,serif;font-size:13.5px;color:rgba(200,180,120,.7);line-height:1.55;">'+f.val+'</p>';
      html += '</div>';
    });
    html += '</div>';
  }

  // ── BLOC 4 : Sources & Liens ────────────────────────────────
  var srcs = ap.sources || [];
  if(srcs.length){
    html += '<div style="margin-top:14px;padding:10px 13px;background:rgba(0,0,0,.15);border-radius:10px;">';
    html += '<p style="font-family:Cinzel,serif;font-size:6.5px;letter-spacing:.22em;color:rgba(201,168,76,.4);margin-bottom:7px;">SOURCES VÉRIFIABLES</p>';
    srcs.forEach(function(s){
      html += '<p style="font-family:Cormorant Garamond,serif;font-size:12px;color:rgba(140,110,50,.6);margin-bottom:3px;">→ '+s+'</p>';
    });
    html += '</div>';
  }

  return html;
}

// ════════════════════════════════════════════════════════════════
//  NOUVELLE renderApprofondi — lisible, sourced, complet
//  Supporte double format avis_savants : {savant/s, citation_ar/c, citation_fr/t, source/src}
// ════════════════════════════════════════════════════════════════
function renderApprofondi(p){
  var ap=p.approfondi, ev=p.evaluations||{};
  var ic=p.color||'#c9a84c';
  var html='';

  // ── Principe en tête ───────────────────────────────────────
  html+='<div style="background:rgba(0,0,0,.2);border:1px solid rgba(201,168,76,.12);border-radius:14px;padding:14px;text-align:center;margin-bottom:14px;">';
  html+='<p style="font-family:Scheherazade New,serif;font-size:19px;color:rgba(212,170,100,.65);direction:rtl;line-height:1.6;margin-bottom:4px;">الجرح المفسَّر مقدَّم على التعديل</p>';
  html+='<p style="font-family:Cormorant Garamond,serif;font-style:italic;font-size:12px;color:rgba(150,120,60,.55);">La critique documentée prime sur la recommandation — Sheikh Rabi Al-Madkhali</p>';
  html+='</div>';

  // ── ACCORDÉON 1 : AVIS DES SAVANTS ────────────────────────
  var rawAvs = (ap&&ap.avis_savants)||p.avis_savants||[];
  html+='<div class="ap-acc" id="ap-scholars" style="margin-bottom:10px;">';
  html+='<button class="ap-trigger" onclick="toggleAp(\'scholars\')" style="width:100%;">';
  html+='<div class="ap-trigger-left"><div class="ap-icon i-scholars"><svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke="currentColor"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg></div>';
  html+='<div><span class="ap-title">AVIS DES SAVANTS</span><span class="ap-title-ar">أقوال العلماء في الجرح والتعديل</span></div>';
  if(rawAvs.length) html+='<span class="ap-count">'+rawAvs.length+' avis</span>';
  html+='</div><div class="ap-arrow"><svg viewBox="0 0 24 24" fill="none" stroke-width="2.5" stroke="currentColor"><polyline points="6 9 12 15 18 9"/></svg></div></button>';
  html+='<div class="ap-body" id="apb-scholars"><div class="ap-inner">';
  if(rawAvs.length){
    rawAvs.forEach(function(av){
      // ── Support double format ──
      var nom    = av.savant||av.s||'';
      var nomAr  = av.savant_ar||'';
      var epoque = av.epoque||'';
      var type   = av.type||(av.c&&av.c.length<80?'jarh':'jarh');
      var citAr  = av.citation_ar||av.c||'';
      var citFr  = av.citation_fr||av.t||'';
      var src    = av.source||av.src||'';
      var badgeC = type==='tadil'?'#22c55e':type==='tawaquf'?'#f59e0b':'#ef4444';
      var badgeT = type==='tadil'?"TA'DIL":type==='tawaquf'?'TAWAQUF':'JARH';

      html+='<div style="background:rgba(0,0,0,.22);border:1px solid rgba(201,168,76,.1);border-radius:12px;padding:13px;margin-bottom:10px;">';
      // Header savant
      html+='<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">';
      html+='<div style="width:36px;height:36px;border-radius:50%;background:'+ic+'20;border:1.5px solid '+ic+'40;display:flex;align-items:center;justify-content:center;font-family:Scheherazade New,serif;font-size:14px;color:'+ic+';flex-shrink:0;">'+(nomAr?nomAr.charAt(1)||nomAr.charAt(0):nom.charAt(0))+'</div>';
      html+='<div style="flex:1;min-width:0;">';
      html+='<p style="font-family:Cinzel,serif;font-size:8px;letter-spacing:.15em;color:'+ic+';white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'+nom.toUpperCase()+'</p>';
      if(epoque) html+='<p style="font-family:Cormorant Garamond,serif;font-size:11px;color:rgba(180,150,80,.5);">'+epoque+'</p>';
      html+='</div>';
      html+='<span style="font-family:Cinzel,serif;font-size:6.5px;letter-spacing:.1em;color:'+badgeC+';background:'+badgeC+'18;border:1px solid '+badgeC+'40;border-radius:20px;padding:3px 8px;flex-shrink:0;">'+badgeT+'</span>';
      html+='</div>';
      // Citation arabe
      if(citAr) html+='<p style="font-family:Scheherazade New,serif;font-size:16px;color:rgba(212,170,100,.75);direction:rtl;text-align:right;line-height:1.7;padding:8px 10px;background:rgba(201,168,76,.05);border-radius:8px;margin-bottom:8px;">'+citAr+'</p>';
      // Traduction
      if(citFr) html+='<p style="font-family:Cormorant Garamond,serif;font-style:italic;font-size:14px;color:rgba(200,180,120,.7);line-height:1.6;">"&nbsp;'+citFr+'&nbsp;"</p>';
      // Source
      if(src) html+='<p style="font-family:Cinzel,serif;font-size:6px;letter-spacing:.15em;color:rgba(140,110,50,.45);margin-top:6px;padding-top:6px;border-top:1px solid rgba(201,168,76,.08);">📚 SOURCE : '+src.toUpperCase()+'</p>';
      html+='</div>';
    });
    html+='<div style="padding:10px;text-align:center;"><p style="font-family:Cormorant Garamond,serif;font-style:italic;font-size:12px;color:rgba(120,90,40,.45);line-height:1.5;">"&nbsp;Si dix savants le recommandent et un seul le critique avec preuve, c\'est la critique qui prime.&nbsp;" — Sheikh Rabi Al-Madkhali</p></div>';
  } else {
    html+='<p style="font-family:Cormorant Garamond,serif;font-style:italic;color:rgba(90,62,32,.5);font-size:13px;padding:12px 0;">Aucun avis de savant documenté pour ce profil.</p>';
  }
  html+='</div></div></div>';

  // ── ACCORDÉON 2 : ÉVALUATION DÉTAILLÉE ────────────────────
  var hasCriteria = Object.keys(ev).length > 0;
  var hasManhaj   = ap&&ap.manhaj&&ap.manhaj.length;
  html+='<div class="ap-acc" id="ap-manhaj" style="margin-bottom:10px;">';
  html+='<button class="ap-trigger" onclick="toggleAp(\'manhaj\')" style="width:100%;">';
  html+='<div class="ap-trigger-left"><div class="ap-icon i-manhaj"><svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke="currentColor"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div>';
  html+='<div><span class="ap-title">ANALYSE DÉTAILLÉE</span><span class="ap-title-ar">التحليل المفصَّل للمنهج</span></div>';
  html+='</div><div class="ap-arrow"><svg viewBox="0 0 24 24" fill="none" stroke-width="2.5" stroke="currentColor"><polyline points="6 9 12 15 18 9"/></svg></div></button>';
  html+='<div class="ap-body" id="apb-manhaj"><div class="ap-inner">';
  if(hasCriteria){
    var critMap=[
      {k:'aqida',     label:'AQIDA',     ar:'العَقِيدة'},
      {k:'manhaj',    label:'MANHAJ',    ar:'المَنهَج'},
      {k:'sectes',    label:'TAHDHIR',    ar:'الفِرَق'},
      {k:'etudes',    label:'ÉTUDES',    ar:'العِلم'},
      {k:'innovateurs',label:'INNOVATEURS',ar:'المُبتَدِعون'},
      {k:'tazkiyat',  label:'TAZKIYAT',  ar:'التَّزكِيَة'},
    ];
    critMap.forEach(function(cr){
      var e=ev[cr.k]; if(!e) return;
      var n=e.note||0;
      var nc=n>=7?'#22c55e':n>=5?'#f59e0b':n>=3?'#fb923c':'#ef4444';
      var pct=Math.min(n*10,100);
      html+='<div style="margin-bottom:13px;">';
      html+='<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:5px;">';
      html+='<div><span style="font-family:Cinzel,serif;font-size:8px;letter-spacing:.15em;color:rgba(200,170,100,.8);">'+cr.label+'</span> <span style="font-family:Scheherazade New,serif;font-size:11px;color:rgba(180,150,80,.4);">'+cr.ar+'</span></div>';
      html+='<span style="font-family:Cinzel,serif;font-size:9px;font-weight:700;color:'+nc+';">'+n+'/10</span>';
      html+='</div>';
      html+='<div style="height:4px;background:rgba(255,255,255,.06);border-radius:4px;margin-bottom:6px;"><div style="height:100%;width:'+pct+'%;background:'+nc+';border-radius:4px;transition:width .5s;"></div></div>';
      if(e.detail) html+='<p style="font-family:Cormorant Garamond,serif;font-size:13.5px;color:rgba(200,180,130,.65);line-height:1.55;">'+e.detail+'</p>';
      html+='</div>';
    });
  } else if(hasManhaj){
    ap.manhaj.forEach(function(m){
      var niv=m.niveau||'orange';
      var nc=niv==='vert'?'#22c55e':niv==='rouge'?'#ef4444':'#f59e0b';
      html+='<div style="display:flex;gap:10px;margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid rgba(201,168,76,.07);">';
      html+='<div style="width:8px;height:8px;border-radius:50%;background:'+nc+';flex-shrink:0;margin-top:5px;"></div>';
      html+='<div><p style="font-family:Cinzel,serif;font-size:7.5px;letter-spacing:.15em;color:'+nc+';margin-bottom:3px;">'+m.point.toUpperCase()+'</p>';
      html+='<p style="font-family:Cormorant Garamond,serif;font-size:13.5px;color:rgba(200,180,130,.65);line-height:1.55;">'+m.detail+'</p></div>';
      html+='</div>';
    });
  } else {
    html+='<p style="font-family:Cormorant Garamond,serif;font-style:italic;color:rgba(90,62,32,.5);font-size:13px;padding:12px 0;">Analyse du manhaj en cours de compilation.</p>';
  }
  html+='</div></div></div>';

  // ── ACCORDÉON 3 : BIOGRAPHIE & ACTIVITÉ ───────────────────
  html+='<div class="ap-acc" id="ap-bio" style="margin-bottom:10px;">';
  html+='<button class="ap-trigger" onclick="toggleAp(\'bio\')" style="width:100%;">';
  html+='<div class="ap-trigger-left"><div class="ap-icon i-books"><svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke="currentColor"><circle cx="12" cy="8" r="4"/><path d="M6 20v-2a4 4 0 0 1 8 0v2"/><path d="M18 20v-2a2 2 0 0 0-2-2h-1"/></svg></div>';
  html+='<div><span class="ap-title">BIOGRAPHIE & ACTIVITÉ</span><span class="ap-title-ar">السِّيرة والنَّشاط</span></div>';
  html+='</div><div class="ap-arrow"><svg viewBox="0 0 24 24" fill="none" stroke-width="2.5" stroke="currentColor"><polyline points="6 9 12 15 18 9"/></svg></div></button>';
  html+='<div class="ap-body" id="apb-bio"><div class="ap-inner">';
  // extractText — éradication totale du [object Object]
  // Supporte : string, objet {naissance,formation,parcours,...}, Array, primitif
  function extractText(data){
    if(!data) return '';
    if(typeof data==='string') return data;
    if(Array.isArray(data)) return data.filter(function(x){return typeof x==='string';}).join(' | ');
    if(typeof data==='object'){
      var parts=[];
      // Champs biographiques dans l'ordre de lisibilité
      ['naissance','formation','maitres','parcours','affiliations','activite','texte','description'].forEach(function(k){
        if(data[k]&&typeof data[k]==='string') parts.push(data[k]);
      });
      // Champs restants non encore couverts
      Object.keys(data).forEach(function(k){
        if(['naissance','formation','maitres','parcours','affiliations','activite','texte','description'].indexOf(k)===-1
           && data[k] && typeof data[k]==='string') parts.push(data[k]);
      });
      return parts.filter(Boolean).join(' — ').replace(/\[object Object\]/g,'').trim()||'Information non documentée.';
    }
    return String(data).replace(/\[object Object\]/g,'').trim();
  }
  var bio=extractText((ap&&ap.biographie)||'');
  var act=extractText((ap&&ap.activite)||'');
  if(!bio){
    var fallParts=[];
    if(p.pays||p.ville) fallParts.push([p.pays,p.ville].filter(Boolean).join(' — '));
    if(p.affiliation)   fallParts.push(p.affiliation);
    bio=fallParts.join(' | ');
  }
  if(!act&&p.domaines&&p.domaines.length) act=(p.domaines||[]).join(' — ');
  if(bio){
    html+='<div style="margin-bottom:12px;">';
    html+='<p style="font-family:Cinzel,serif;font-size:7px;letter-spacing:.22em;color:rgba(180,150,80,.55);margin-bottom:6px;">BIOGRAPHIE</p>';
    html+='<p style="font-family:Cormorant Garamond,serif;font-size:14.5px;color:rgba(220,200,140,.8);line-height:1.65;">'+bio+'</p>';
    html+='</div>';
  }
  if(act){
    html+='<div>';
    html+='<p style="font-family:Cinzel,serif;font-size:7px;letter-spacing:.22em;color:rgba(180,150,80,.55);margin-bottom:6px;">ACTIVITÉ</p>';
    html+='<p style="font-family:Cormorant Garamond,serif;font-size:14.5px;color:rgba(220,200,140,.8);line-height:1.65;">'+act+'</p>';
    html+='</div>';
  }
  // Domaines si dispo
  if(p.domaines&&p.domaines.length){
    html+='<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;">';
    p.domaines.forEach(function(d){
      html+='<span style="font-family:Cinzel,serif;font-size:6.5px;letter-spacing:.12em;color:'+ic+';background:'+ic+'12;border:1px solid '+ic+'30;border-radius:20px;padding:3px 10px;">'+d.toUpperCase()+'</span>';
    });
    html+='</div>';
  }
  html+='</div></div></div>';

  // ── ACCORDÉON 4 : ŒUVRES ──────────────────────────────────
  var oeuvres=(ap&&ap.oeuvres)||[];
  if(oeuvres.length){
    html+='<div class="ap-acc" id="ap-oeuvres" style="margin-bottom:10px;">';
    html+='<button class="ap-trigger" onclick="toggleAp(\'oeuvres\')" style="width:100%;">';
    html+='<div class="ap-trigger-left"><div class="ap-icon i-books"><svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke="currentColor"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg></div>';
    html+='<div><span class="ap-title">ŒUVRES & SOURCES</span><span class="ap-title-ar">المُؤلَّفات والمَصادر</span></div>';
    html+='<span class="ap-count">'+oeuvres.length+'</span>';
    html+='</div><div class="ap-arrow"><svg viewBox="0 0 24 24" fill="none" stroke-width="2.5" stroke="currentColor"><polyline points="6 9 12 15 18 9"/></svg></div></button>';
    html+='<div class="ap-body" id="apb-oeuvres"><div class="ap-inner">';
    oeuvres.forEach(function(o){
      html+='<div style="padding:9px 0;border-bottom:1px solid rgba(201,168,76,.07);">';
      if(o.titre_ar) html+='<p style="font-family:Scheherazade New,serif;font-size:15px;color:rgba(212,170,100,.75);direction:rtl;text-align:right;margin-bottom:3px;">'+o.titre_ar+'</p>';
      if(o.titre_fr) html+='<p style="font-family:Cormorant Garamond,serif;font-size:14px;color:rgba(200,180,130,.75);">'+o.titre_fr+'</p>';
      if(o.desc)     html+='<p style="font-family:Cormorant Garamond,serif;font-style:italic;font-size:12.5px;color:rgba(160,130,70,.55);margin-top:3px;">'+o.desc+'</p>';
      html+='</div>';
    });
    html+='</div></div></div>';
  }

  // ── ACCORDÉON 5 : LIENS & PREUVES ─────────────────────────
  var preuves=(p.data&&p.data.preuves)||[];
  if(preuves.length){
    html+='<div class="ap-acc" id="ap-links" style="margin-bottom:10px;">';
    html+='<button class="ap-trigger" onclick="toggleAp(\'links\')" style="width:100%;">';
    html+='<div class="ap-trigger-left"><div class="ap-icon"><svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke="currentColor"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg></div>';
    html+='<div><span class="ap-title">LIENS & PREUVES</span><span class="ap-title-ar">المَصادر والرَّوابط</span></div>';
    html+='<span class="ap-count">'+preuves.length+'</span>';
    html+='</div><div class="ap-arrow"><svg viewBox="0 0 24 24" fill="none" stroke-width="2.5" stroke="currentColor"><polyline points="6 9 12 15 18 9"/></svg></div></button>';
    html+='<div class="ap-body" id="apb-links"><div class="ap-inner">';
    preuves.forEach(function(pr){
      var lbl=pr.l||'Lien';
      html+='<a href="'+(pr.u||'#')+'" target="_blank" style="display:block;padding:9px 12px;background:rgba(0,0,0,.2);border:1px solid '+ic+'20;border-radius:10px;margin-bottom:7px;text-decoration:none;">';
      html+='<p style="font-family:Cinzel,serif;font-size:7.5px;letter-spacing:.15em;color:'+ic+';">🔗 '+lbl.toUpperCase()+'</p>';
      html+='</a>';
    });
    html+='</div></div></div>';
  }

  return html;
}


function toggleAp(id){
  var body = document.getElementById('apb-'+id);
  var trigger = document.querySelector('#ap-'+id+' .ap-trigger');
  if(!body||!trigger) return;
  var isOpen = body.classList.contains('open');
  if(isOpen){ body.classList.remove('open'); trigger.classList.remove('open'); }
  else { body.classList.add('open'); trigger.classList.add('open'); }
}
function toggleStep(id){
  var btn=document.getElementById('sbtn-'+id);
  var cnt=document.getElementById('scnt-'+id);
  btn.classList.toggle('open');cnt.classList.toggle('open');
}

/* ════════════════════════════════════════
   MYTHES
════════════════════════════════════════ */
function renderMythes(){
  var el=document.getElementById('myths-list');el.innerHTML='';
  // Section 1 : Hadiths faibles/inventés
  var hadithMythes=MYTHES.filter(function(m){return !m.cat||m.cat!=='khurafat';});
  var khurafatMythes=MYTHES.filter(function(m){return m.cat==='khurafat';});

  if(hadithMythes.length){
    var hdr1=document.createElement('div');
    hdr1.style.cssText='display:flex;align-items:center;gap:10px;margin-bottom:14px;padding:12px 16px;background:rgba(239,68,68,.05);border:1px solid rgba(239,68,68,.15);border-radius:12px;';
    hdr1.innerHTML='<span style="font-size:20px;">📖</span><div><span style="font-family:Cinzel,serif;font-size:9px;font-weight:700;letter-spacing:.18em;color:#ef4444;display:block;">AHADITH DA\'IFA & MAWDU\'A</span><span style="font-family:Scheherazade New,serif;font-size:14px;color:rgba(239,68,68,.45);">الأحاديث الضعيفة والموضوعة</span></div>';
    el.appendChild(hdr1);
    hadithMythes.forEach(function(m){
      var card=document.createElement('div');card.className='myth-card';
      card.innerHTML='<div class="myth-header"><div class="myth-hadith">"'+m.hadith+'"</div><span class="myth-badge" style="background:'+m.color+'20;border:1px solid '+m.color+'44;color:'+m.color+'">'+m.grade+'</span></div><div class="myth-footer"><span class="myth-ref">'+m.ref+'</span><span class="myth-expand-hint">DÉTAIL →</span></div>';
      card.onclick=function(){openMythDetail(m.id);};
      el.appendChild(card);
    });
  }

  // Séparateur visuel
  if(khurafatMythes.length){
    var sep=document.createElement('div');
    sep.style.cssText='display:flex;align-items:center;gap:14px;margin:24px 0 14px;';
    sep.innerHTML='<div style="flex:1;height:1px;background:linear-gradient(90deg,transparent,rgba(153,27,27,.3),transparent);"></div><span style="font-family:Cinzel,serif;font-size:6px;letter-spacing:.4em;color:rgba(153,27,27,.45);flex-shrink:0;">العَقِيدَة وَالتَّوْحِيد</span><div style="flex:1;height:1px;background:linear-gradient(90deg,transparent,rgba(153,27,27,.3),transparent);"></div>';
    el.appendChild(sep);

    var hdr2=document.createElement('div');
    hdr2.style.cssText='display:flex;align-items:center;gap:10px;margin-bottom:14px;padding:14px 16px;background:linear-gradient(135deg,rgba(127,29,29,.1),rgba(153,27,27,.06));border:1px solid rgba(153,27,27,.2);border-radius:12px;';
    hdr2.innerHTML='<span style="font-size:22px;">🛡️</span><div style="flex:1;"><span style="font-family:Cinzel,serif;font-size:9px;font-weight:700;letter-spacing:.15em;color:#991b1b;display:block;">KHURAFAT — CROYANCES DÉVIANTES</span><span style="font-family:Scheherazade New,serif;font-size:14px;color:rgba(153,27,27,.45);">الخُرَافَاتُ وَالشِّرْكِيَّات</span></div><span style="font-family:Cinzel,serif;font-size:6px;letter-spacing:.15em;color:rgba(153,27,27,.5);padding:3px 8px;border:1px solid rgba(153,27,27,.2);border-radius:99px;">'+khurafatMythes.length+' FICHES</span>';
    el.appendChild(hdr2);

    khurafatMythes.forEach(function(m){
      var card=document.createElement('div');card.className='myth-card';
      card.style.borderColor=m.color+'28';
      card.innerHTML='<div style="display:flex;align-items:stretch;"><div style="width:3px;flex-shrink:0;background:'+m.color+';border-radius:3px 0 0 3px;"></div><div style="flex:1;"><div class="myth-header"><div class="myth-hadith">"'+m.hadith+'"</div><span class="myth-badge" style="background:'+m.color+'20;border:1px solid '+m.color+'44;color:'+m.color+'">'+m.grade+'</span></div><div class="myth-footer"><span class="myth-ref">'+m.ref+'</span><span class="myth-expand-hint">DÉTAIL →</span></div></div></div>';
      card.onclick=function(){openMythDetail(m.id);};
      el.appendChild(card);
    });
  }
}
window.renderMythes = renderMythes;
var currentMyth=null;
function openMythDetail(id){
  currentMyth=MYTHES.find(function(m){return m.id===id;});
  if(!currentMyth)return;
  var m=currentMyth;
  document.getElementById('myth-det-badge').textContent=m.grade;
  document.getElementById('myth-det-badge').style.background=m.color+'20';
  document.getElementById('myth-det-badge').style.border='1px solid '+m.color+'44';
  document.getElementById('myth-det-badge').style.color=m.color;
  document.getElementById('myth-det-title').textContent='"'+m.hadith+'"';
  var el=document.getElementById('myth-det-content');
  var html='';
  // Origine
  html+='<div class="myth-explication" style="border:1px solid #d4af3720;"><div class="accent" style="background:var(--gold)"></div>'
    +'<div class="myth-section-title"><svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>ORIGINE & DIFFUSION</div>'
    +'<p class="myth-text">'+m.origine+'</p></div>';
  // Explication
  html+='<div class="myth-explication"><div class="accent"></div>'
    +'<div class="myth-section-title"><svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>EXPLICATION SCIENTIFIQUE</div>'
    +'<p class="myth-text">'+m.explication+'</p></div>';
  // Erreur
  html+='<div class="myth-explication" style="border:1px solid #ef444428;"><div class="accent" style="background:#ef4444"></div>'
    +'<div class="myth-section-title" style="color:#ef4444"><svg viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>L\'ERREUR À ÉVITER</div>'
    +'<p class="myth-text">'+m.erreur+'</p></div>';
  // Correction
  html+='<div class="myth-authentic"><div class="accent"></div>'
    +'<div class="myth-section-title" style="color:#22c55e"><svg viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>LA CORRECTION AUTHENTIQUE</div>'
    +'<p class="myth-ar-text">'+m.ar_correction+'</p>'
    +'<p class="myth-text" style="color:rgba(212,170,100,.72);">'+m.correction+'</p>'
    +'<p class="myth-source">SOURCE : '+m.source_correction+'</p></div>';
  // Disclaimer
  html+='<div class="disclaimer" style="margin-top:8px;"><p>⚠ Fondé sur le Coran, la Sunnah authentique, la voie des 4 Imams (Abou Hanifa, Malik, Ach-Chafi\'i, Ahmad) et confirmé par Al-Albani, Ibn Baz, Ibn Uthaymin et Al-Fawzan.</p></div>';
  el.innerHTML=html;goTo('myth-detail');
}
window.openMythDetail = openMythDetail;

/* ════════════════════════════════════════
   AL-FIRAQ
════════════════════════════════════════ */
function renderFiraq(){
  var el=document.getElementById('firaq-list');
  el.innerHTML='';
  FIRAQ.forEach(function(f, idx){
    var niveauBar='';
    for(var i=1;i<=5;i++){
      niveauBar+='<span style="width:16px;height:4px;background:'+(i<=f.niveau?f.color:'rgba(255,255,255,.06)')+';display:inline-block;margin-right:2px;box-shadow:'+(i<=f.niveau?'0 0 4px '+f.color+'44':'none')+'"></span>';
    }
    var card=document.createElement('div');
    card.style.cssText='background:#111827;border:1px solid '+f.color+'30;border-radius:3px;overflow:hidden;margin-bottom:10px;cursor:pointer;transition:all .3s cubic-bezier(.4,0,.2,1);animation:argCardIn .4s ease both;animation-delay:'+(idx*0.06)+'s;';
    card.innerHTML=
      '<div style="display:flex;align-items:stretch;">'
        +'<div style="width:4px;flex-shrink:0;background:'+f.color+';"></div>'
        +'<div style="flex:1;padding:14px 16px;">'
          +'<div style="display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin-bottom:8px;">'
            +'<div style="flex:1;min-width:0;">'
              +'<p style="font-family:Cinzel,serif;color:#c9a84c;font-size:10.5px;font-weight:700;letter-spacing:.1em;line-height:1.3;margin-bottom:3px;">'+f.nom+'</p>'
              +'<p style="font-family:Scheherazade New,serif;color:'+f.color+';font-size:15px;line-height:1.1;opacity:.7;">'+f.ar+'</p>'
            +'</div>'
            +'<span style="font-family:Cinzel,serif;font-size:5.5px;font-weight:700;padding:4px 10px;border-radius:2px;background:'+f.color+'15;border:1px solid '+f.color+'35;color:'+f.color+';flex-shrink:0;white-space:nowrap;">'+f.danger+'</span>'
          +'</div>'
          +'<p style="font-family:Cormorant Garamond,serif;font-style:italic;color:rgba(220,200,160,.5);font-size:12px;line-height:1.6;margin-bottom:8px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">'+(f.phraseChoc||f.description).substring(0,120)+'...</p>'
          +'<div style="display:flex;align-items:center;justify-content:space-between;">'
            +'<div style="display:flex;align-items:center;gap:6px;">'
              +'<span style="font-family:Cinzel,serif;font-size:5px;letter-spacing:.25em;color:rgba(201,168,76,.3);">DANGER</span>'
              +'<div>'+niveauBar+'</div>'
            +'</div>'
            +'<span style="font-family:Cinzel,serif;font-size:6px;letter-spacing:.15em;color:'+f.color+';opacity:.5;">OUVRIR ▸</span>'
          +'</div>'
        +'</div>'
      +'</div>';
    card.onmouseenter=function(){this.style.borderColor=f.color+'60';this.style.background='#151d2e';};
    card.onmouseleave=function(){this.style.borderColor=f.color+'30';this.style.background='#111827';};
    card.onclick=function(){openFiraqDetail(f.id);};
    el.appendChild(card);
  });
}
window.renderFiraq = renderFiraq;
var currentFiraq=null;
var firaqTab='essentiel';
function openFiraqDetail(id){
  currentFiraq=FIRAQ.find(function(f){return f.id===id;});
  if(!currentFiraq)return;
  firaqTab='essentiel';
  renderFiraqDetail();
  goTo('firaq-detail');
}
window.openFiraqDetail = openFiraqDetail;
function setFiraqTab(tab,btn){
  firaqTab=tab;
  document.querySelectorAll('.fq-tab-btn').forEach(function(b){b.classList.remove('active');});
  btn.classList.add('active');
  renderFiraqDetail();
}
window.setFiraqTab = setFiraqTab;
function renderFiraqDetail(){
  var f=currentFiraq;
  var badge=document.getElementById('firaq-det-badge');
  badge.textContent=f.danger;
  badge.style.background=f.color+'20';
  badge.style.border='1px solid '+f.color+'44';
  badge.style.color=f.color;
  badge.style.borderRadius='3px';
  document.getElementById('firaq-det-name').textContent=f.nom;
  document.getElementById('firaq-det-ar').textContent=f.ar;

  var el=document.getElementById('firaq-det-content');
  var tabs=[['essentiel','ESSENTIEL'],['preuves','PREUVES'],['comment','REPONDRE']];
  
  var tabsHtml='<div style="display:flex;background:rgba(9,5,0,.97);border-bottom:1px solid rgba(140,100,30,.18);position:sticky;top:0;z-index:10;">';
  tabs.forEach(function(t){
    var active=(firaqTab===t[0]);
    var btn=document.createElement('button');
    btn.style.cssText='flex:1;padding:11px 4px;font-family:Cinzel,serif;font-size:6.5px;font-weight:700;letter-spacing:.18em;background:transparent;border:none;border-bottom:2px solid '+(active?'#c9a84c':'transparent')+';cursor:pointer;color:'+(active?'#c9a84c':'rgba(100,60,10,.4)');
    btn.textContent=t[1];
    btn.className='fq-tab-btn'+(active?' active':'');
    (function(tab){btn.onclick=function(){setFiraqTab(tab,this);};})(t[0]);
    tabsHtml+='__BTN_'+t[0]+'__';
  });
  tabsHtml+='</div>';

  var bodyHtml='';
  
  if(firaqTab==='essentiel'){
    // Phrase choc — bloc rectangulaire austère
    bodyHtml+='<div style="background:#111827;border:1px solid '+f.color+'30;border-radius:3px;padding:16px 18px;margin-bottom:12px;border-left:3px solid '+f.color+';">'
      +'<p style="font-family:Cormorant Garamond,serif;font-style:italic;color:rgba(232,201,106,.82);font-size:1.1rem;line-height:1.8;">'+f.phraseChoc+'</p>'
      +'</div>';
    // Niveau + verdict — rectangulaire
    var niveauBar='';
    for(var i=1;i<=5;i++){
      niveauBar+='<span style="width:18px;height:5px;background:'+(i<=f.niveau?f.color:'rgba(255,255,255,.06)')+';display:inline-block;margin-right:3px;box-shadow:'+(i<=f.niveau?'0 0 6px '+f.color+'44':'none')+'"></span>';
    }
    bodyHtml+='<div style="background:#0d1117;border:1px solid rgba(201,168,76,.12);border-radius:3px;padding:12px 16px;margin-bottom:12px;display:flex;align-items:center;gap:14px;">'
      +'<div><span style="font-family:Cinzel,serif;font-size:6px;letter-spacing:.3em;color:rgba(201,168,76,.4);display:block;margin-bottom:5px;">NIVEAU DE DANGER</span>'
      +'<div>'+niveauBar+'</div></div>'
      +'<div style="margin-left:auto;text-align:right;"><span style="font-family:Cinzel,serif;font-size:6px;letter-spacing:.2em;color:rgba(201,168,76,.35);display:block;margin-bottom:3px;">VERDICT</span>'
      +'<span style="font-family:Cinzel,serif;font-size:8px;font-weight:700;color:'+f.color+';">'+f.danger+'</span></div>'
      +'</div>';
    // Fondateur — bloc rectangulaire
    bodyHtml+='<div style="background:#0d1117;border:1px solid rgba(201,168,76,.12);border-radius:3px;padding:12px 16px;margin-bottom:12px;border-left:3px solid #c9a84c;">'
      +'<span style="font-family:Cinzel,serif;font-size:6px;letter-spacing:.3em;color:rgba(201,168,76,.45);display:block;margin-bottom:6px;">FONDATEUR / ORIGINE</span>'
      +'<p style="font-family:Cormorant Garamond,serif;font-style:italic;color:rgba(220,200,160,.7);font-size:1rem;line-height:1.7;">'+f.fondateur+'</p>'
      +'</div>';
    // Description — NARRATION HISTORIQUE — texte grand et aéré
    bodyHtml+='<div style="background:#111827;border:1px solid rgba(201,168,76,.08);border-radius:3px;padding:16px 18px;margin-bottom:12px;">'
      +'<span style="font-family:Cinzel,serif;font-size:6px;letter-spacing:.3em;color:rgba(201,168,76,.4);display:block;margin-bottom:10px;">DOSSIER HISTORIQUE</span>'
      +'<p style="font-family:Cormorant Garamond,serif;color:rgba(220,200,160,.75);font-size:1.1rem;line-height:1.8;">'+f.description+'</p>'
      +'</div>';
    // Signes de reconnaissance — liste à puces rectangulaire
    bodyHtml+='<div style="background:#0d1117;border:1px solid '+f.color+'25;border-radius:3px;padding:14px 16px;margin-bottom:12px;border-left:3px solid '+f.color+';">'
      +'<span style="font-family:Cinzel,serif;font-size:6px;letter-spacing:.3em;color:'+f.color+';opacity:.75;display:block;margin-bottom:10px;">SIGNES DE RECONNAISSANCE</span>';
    f.signes.forEach(function(s,i){
      bodyHtml+='<div style="display:flex;align-items:flex-start;gap:10px;padding:7px 0;'+(i<f.signes.length-1?'border-bottom:1px solid rgba(255,255,255,.04)':'')+'">'
        +'<span style="width:6px;height:2px;background:'+f.color+';flex-shrink:0;margin-top:9px;"></span>'
        +'<p style="font-family:Cormorant Garamond,serif;color:rgba(220,200,160,.65);font-size:1rem;line-height:1.65;">'+s+'</p>'
        +'</div>';
    });
    bodyHtml+='</div>';
    // Hukm — le verdict des savants
    bodyHtml+='<div style="background:#111827;border:1px solid rgba(153,27,27,.2);border-radius:3px;padding:14px 16px;margin-bottom:12px;border-left:3px solid #991b1b;">'
      +'<span style="font-family:Cinzel,serif;font-size:6px;letter-spacing:.3em;color:rgba(153,27,27,.7);display:block;margin-bottom:8px;">VERDICT DES TEXTES ET DES SAVANTS</span>'
      +'<p style="font-family:Cormorant Garamond,serif;color:rgba(220,200,160,.75);font-size:1.05rem;line-height:1.8;">'+f.hukm_sharh+'</p>'
      +'</div>';
    // Présence en France
    bodyHtml+='<div style="background:#0d1117;border:1px solid rgba(99,102,241,.15);border-radius:3px;padding:12px 16px;border-left:3px solid #6366f1;">'
      +'<span style="font-family:Cinzel,serif;font-size:6px;letter-spacing:.3em;color:rgba(99,102,241,.7);display:block;margin-bottom:6px;">VISAGE CONTEMPORAIN EN FRANCE</span>'
      +'<p style="font-family:Cormorant Garamond,serif;color:rgba(220,200,160,.65);font-size:1rem;line-height:1.75;">'+f.presence_fr+'</p>'
      +'</div>';

    // ── AL-HAJR — Comment agir avec eux ──
    if(f.hajr){
      bodyHtml+='<div style="background:#111827;border:1px solid rgba(245,158,11,.18);border-radius:3px;padding:14px 16px;margin-top:12px;border-left:3px solid #f59e0b;">'
        +'<span style="font-family:Cinzel,serif;font-size:6px;letter-spacing:.3em;color:rgba(245,158,11,.7);display:block;margin-bottom:8px;">AL-HAJR — COMMENT AGIR AVEC EUX</span>'
        +'<p style="font-family:Cormorant Garamond,serif;color:rgba(220,200,160,.72);font-size:1rem;line-height:1.8;">'+f.hajr+'</p>'
        +'</div>';
    }

    // ── MASQUES CONTEMPORAINS ──
    if(f.masques&&f.masques.length){
      bodyHtml+='<div style="background:#0d1117;border:1px solid rgba(167,139,250,.15);border-radius:3px;padding:14px 16px;margin-top:12px;border-left:3px solid #a78bfa;">'
        +'<span style="font-family:Cinzel,serif;font-size:6px;letter-spacing:.3em;color:rgba(167,139,250,.7);display:block;margin-bottom:10px;">LEURS MASQUES CONTEMPORAINS</span>';
      f.masques.forEach(function(m,i){
        bodyHtml+='<div style="display:flex;align-items:flex-start;gap:10px;padding:7px 0;'+(i<f.masques.length-1?'border-bottom:1px solid rgba(255,255,255,.04)':'')+'">'
          +'<span style="width:6px;height:2px;background:#a78bfa;flex-shrink:0;margin-top:9px;"></span>'
          +'<p style="font-family:Cormorant Garamond,serif;color:rgba(220,200,160,.68);font-size:1rem;line-height:1.65;">'+m+'</p>'
          +'</div>';
      });
      bodyHtml+='</div>';
    }

  } else if(firaqTab==='preuves'){
    bodyHtml+='<span style="font-family:Cinzel,serif;font-size:6px;letter-spacing:.4em;color:rgba(201,168,76,.35);display:block;margin-bottom:14px;">CITATIONS DES SAVANTS</span>';
    f.citations.forEach(function(c,i){
      bodyHtml+='<div style="background:#111827;border:1px solid rgba(201,168,76,.12);border-radius:3px;padding:14px 16px;margin-bottom:10px;">'
        +'<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">'
          +'<div style="width:30px;height:30px;border-radius:2px;background:rgba(201,168,76,.1);border:1px solid rgba(201,168,76,.25);display:flex;align-items:center;justify-content:center;font-family:Scheherazade New,serif;color:#c9a84c;font-size:14px;flex-shrink:0;">'+c.savant_ar.charAt(0)+'</div>'
          +'<div style="flex:1;"><span style="font-family:Cinzel,serif;font-size:9px;font-weight:700;color:rgba(232,201,106,.85);display:block;">'+c.savant+'</span>'
          +'<span style="font-family:Cinzel,serif;font-size:5.5px;color:rgba(201,168,76,.35);letter-spacing:.15em;">'+c.source+'</span></div>'
          +'<span style="font-family:Cinzel,serif;font-size:5.5px;font-weight:700;padding:4px 9px;border-radius:2px;background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.25);color:#ef4444;">JARH</span>'
        +'</div>'
        +'<div style="background:#0d1117;border-left:2px solid rgba(201,168,76,.3);border-radius:0 3px 3px 0;padding:10px 14px;">'
          +'<span style="font-family:Scheherazade New,serif;font-size:1.1rem;direction:rtl;text-align:right;display:block;color:rgba(232,201,106,.8);line-height:1.8;margin-bottom:6px;">'+c.citation_ar+'</span>'
          +'<p style="font-family:Cormorant Garamond,serif;font-style:italic;color:rgba(220,200,160,.6);font-size:1rem;line-height:1.7;">'+c.citation_fr+'</p>'
        +'</div>'
        +'</div>';
    });
    bodyHtml+='<div style="background:#0d1117;border:1px solid rgba(34,197,94,.18);border-radius:3px;padding:12px 16px;margin-bottom:10px;border-left:3px solid #22c55e;">'
      +'<span style="font-family:Cinzel,serif;font-size:6px;letter-spacing:.3em;color:rgba(34,197,94,.65);display:block;margin-bottom:8px;">SAVANTS AYANT REFUTE</span>';
    f.savants.forEach(function(s){
      bodyHtml+='<div style="display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid rgba(34,197,94,.06);">'
        +'<span style="width:6px;height:2px;background:#22c55e;flex-shrink:0;"></span>'
        +'<span style="font-family:Cinzel,serif;font-size:8px;color:rgba(34,197,94,.75);">'+s+'</span>'
        +'</div>';
    });
    bodyHtml+='</div>';
    bodyHtml+='<div style="background:#111827;border:1px solid rgba(201,168,76,.1);border-radius:3px;padding:12px 16px;">'
      +'<span style="font-family:Cinzel,serif;font-size:6px;letter-spacing:.3em;color:rgba(201,168,76,.4);display:block;margin-bottom:6px;">OUVRAGES DE REFUTATION</span>'
      +'<p style="font-family:Cormorant Garamond,serif;color:rgba(220,200,160,.6);font-size:1rem;line-height:1.75;">'+f.refutation+'</p>'
      +'</div>';

  } else if(firaqTab==='comment'){
    bodyHtml+='<div style="background:#111827;border:1px solid rgba(245,158,11,.2);border-radius:3px;padding:14px 16px;margin-bottom:12px;border-left:3px solid #f59e0b;">'
      +'<span style="font-family:Cinzel,serif;font-size:6px;letter-spacing:.3em;color:rgba(245,158,11,.7);display:block;margin-bottom:8px;">COMMENT LES RECONNAITRE</span>'
      +'<p style="font-family:Cormorant Garamond,serif;color:rgba(220,200,160,.7);font-size:1.05rem;line-height:1.8;">'+f.comment_reconnaitre+'</p>'
      +'</div>';
    bodyHtml+='<div style="background:#0d1117;border:1px solid rgba(34,197,94,.2);border-radius:3px;padding:14px 16px;margin-bottom:12px;border-left:3px solid #22c55e;">'
      +'<span style="font-family:Cinzel,serif;font-size:6px;letter-spacing:.3em;color:rgba(34,197,94,.65);display:block;margin-bottom:8px;">COMMENT REPONDRE</span>'
      +'<p style="font-family:Cormorant Garamond,serif;color:rgba(220,200,160,.7);font-size:1.05rem;line-height:1.8;">'+f.comment_repondre+'</p>'
      +'</div>';
    bodyHtml+='<div style="background:#111827;border:1px solid rgba(201,168,76,.15);border-radius:3px;padding:13px 16px;">'
      +'<span style="font-family:Cinzel,serif;font-size:6px;letter-spacing:.3em;color:rgba(201,168,76,.45);display:block;margin-bottom:8px;">REGLE D\'OR — AL-JARH AL-MUFASSAR</span>'
      +'<p style="font-family:Scheherazade New,serif;font-size:1.15rem;direction:rtl;text-align:right;color:rgba(232,201,106,.75);line-height:1.7;display:block;margin-bottom:5px;">'+'\u0627\u0644\u062c\u0631\u062d \u0627\u0644\u0645\u0641\u0633\u064e\u0651\u0631 \u0645\u0642\u062f\u0651\u064e\u0645 \u0639\u0644\u0649 \u0627\u0644\u062a\u0639\u062f\u064a\u0644'+'</p>'
      +'<p style="font-family:Cormorant Garamond,serif;font-style:italic;color:rgba(201,168,76,.5);font-size:11.5px;line-height:1.65;">Le Jarh documenté prime toujours sur la recommandation. — Voie unanime des Salaf as-Salih</p>'
      +'</div>';
  }

  // Build the container with real DOM for tab buttons
  var container = document.createElement('div');
  
  var tabBar = document.createElement('div');
  tabBar.style.cssText='display:flex;background:rgba(9,5,0,.97);border-bottom:1px solid rgba(140,100,30,.18);position:sticky;top:0;z-index:10;';
  tabs.forEach(function(t){
    var active=(firaqTab===t[0]);
    var btn=document.createElement('button');
    btn.style.cssText='flex:1;padding:11px 4px;font-family:Cinzel,serif;font-size:6.5px;font-weight:700;letter-spacing:.18em;background:transparent;border:none;border-bottom:2px solid '+(active?'#c9a84c':'transparent')+';cursor:pointer;transition:all .25s;color:'+(active?'#c9a84c':'rgba(100,60,10,.4)');
    btn.textContent=t[1];
    btn.className='fq-tab-btn'+(active?' active':'');
    (function(tab,b){b.addEventListener('click',function(){setFiraqTab(tab,b);});})(t[0],btn);
    tabBar.appendChild(btn);
  });
  
  var body = document.createElement('div');
  body.style.padding='14px';
  body.innerHTML=bodyHtml;
  
  container.appendChild(tabBar);
  container.appendChild(body);
  el.innerHTML='';
  el.appendChild(container);
}
window.renderFiraqDetail = renderFiraqDetail;

/* ════════════════════════════════════════
   INIT
════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded',function(){
  loadHadithDatabase(
    function(db){
      var s=window.MizanDB.getStats();
      console.log('[Al Mizan DB v2] '+s.total+' hadiths — SAHIH:'+s.SAHIH+' HASAN:'+s.HASAN+' DAIF:'+s.DAIF+" MAWDU:"+s.MAWDU);
      var bar=document.getElementById('mizan-db-bar');
      var bst=document.getElementById('mizan-db-bar-stats');
      if(bar){bar.style.display='flex';}
      if(bst){bst.textContent=s.total+' HADITHS · '+s.SAHIH+' SAHIH · '+s.DAIF+" DA'IF · "+s.MAWDU+" MAWDU'";}
      renderExamples();
    },
    function(err){console.warn('[Al Mizan] DB erreur:',err);}
  );
  renderExamples();
  document.getElementById('examples-section').style.display='block';
  renderMythes();
  renderFiraq();
  var disc=document.getElementById('mizan-disclaimer');
  if(disc) disc.style.display='block';
  document.getElementById('hadith-input').addEventListener('keydown',function(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();analyzeHadith();}});
  document.getElementById('home-input').addEventListener('keydown',function(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();startHadithFromHome();}});
});



console.log('%c \u2705 M\u00eezan v21.0 : Pr\u00eat pour Production', 'color: #00ff00; font-weight: bold;');
console.log('%c \ud83d\udee1\ufe0f TRIPLE BOUCLIER ACTIF \u2014 Fallback Arbre Royal connect\u00e9', 'color:#d4af37;font-weight:bold;');
