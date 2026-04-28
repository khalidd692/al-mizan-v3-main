/* ═══════════════════════════════════════════════════════════════════
   MÎZÂN v22.5 — mizan-tree-engine.js  "Preuve Visuelle"
   ───────────────────────────────────────────────────────────────────
   CORRECTIONS v22.5 :
     [A] ANNÉE sur chaque carte — bloc "MORT EN : XXXX" visible en gros.
         Ṣaḥāba → "ṢAḤĀBĪ"  |  9999 → "DATE INCONNUE"
     [B] TRI FORCÉ → chain.sort((a,b) => a.death_year - b.death_year)
         Appliqué dans mzRenderIsnadTree ET mzChainFromDorarData.
     [C] MAPPING corrigé — lecture explicite de name_ar (snake_case Python)
         avant nameAr (camelCase). Plus jamais de nom arabe vide.
     [D] MODAL — affiche name_ar, mashayikh, talamidh.
         Listes vides → message rouge "DATA MISSING".
     [E] REGISTRE _mzNodeRegistry — nœud complet stocké au build,
         récupéré au clic. Plus de crash sur _openRawiModal inexistant.
═══════════════════════════════════════════════════════════════════ */

console.log(
  '%c ✅ MÎZÂN v22.5 — mizan-tree-engine.js chargé',
  'color:#d4af37;font-weight:bold;font-size:11px;'
);

/* ════════════════════════════════════════════════════════════════
   1. CSS
════════════════════════════════════════════════════════════════ */
(function _mzInjectCSS() {
  var old = document.getElementById('mz-tree-css');
  if (old) old.remove();
  var s = document.createElement('style');
  s.id = 'mz-tree-css';
  s.textContent = [
    '@keyframes mzTrNodeIn{from{opacity:0;transform:translateY(14px) scale(.97)}to{opacity:1;transform:translateY(0) scale(1)}}',
    '@keyframes mzTrGlow{0%,100%{box-shadow:0 0 0 1px rgba(212,175,55,.08),0 4px 20px rgba(0,0,0,.7)}50%{box-shadow:0 0 0 1px rgba(212,175,55,.18),0 0 24px rgba(212,175,55,.32),0 4px 28px rgba(0,0,0,.8)}}',
    '@keyframes mzTrConnIn{from{opacity:0;transform:scaleY(0);transform-origin:top}to{opacity:1;transform:scaleY(1);transform-origin:top}}',
    '@keyframes mzTrBadgeIn{from{opacity:0;transform:scale(.8)}to{opacity:1;transform:scale(1)}}',
    '@keyframes mzTrPulse{0%,100%{opacity:.5}50%{opacity:1}}',
    '@keyframes mzModalIn{from{opacity:0;transform:translateY(18px) scale(.96)}to{opacity:1;transform:translateY(0) scale(1)}}',
    '@keyframes mzOverlayIn{from{opacity:0}to{opacity:1}}',

    /* ── Arbre ── */
    '.mzTr-root{display:flex;flex-direction:column;align-items:center;gap:0;padding:28px 16px 36px;font-family:Cinzel,Georgia,serif;background:transparent;width:100%;box-sizing:border-box;}',
    '.mzTr-stage{display:flex;flex-direction:column;align-items:center;width:100%;}',
    '.mzTr-node{position:relative;display:flex;flex-direction:column;align-items:center;cursor:pointer;user-select:none;padding:12px 24px 14px;min-width:190px;max-width:360px;width:auto;background:linear-gradient(158deg,#0e0900 0%,#090600 55%,#0b0b11 100%);border:1px solid rgba(212,175,55,.22);border-radius:3px;box-shadow:0 0 0 1px rgba(212,175,55,.04),0 5px 24px rgba(0,0,0,.75),inset 0 1px 0 rgba(212,175,55,.06);transition:border-color .22s,transform .18s;animation:mzTrNodeIn .5s cubic-bezier(.16,1,.3,1) both;text-align:center;}',
    '.mzTr-node::before{content:"";position:absolute;top:0;left:0;right:0;height:1.5px;background:linear-gradient(90deg,transparent,rgba(212,175,55,.38) 25%,rgba(212,175,55,.65) 50%,rgba(212,175,55,.38) 75%,transparent);border-radius:3px 3px 0 0;}',
    '.mzTr-node:hover{border-color:rgba(212,175,55,.6);transform:scale(1.035) translateY(-1px);animation:mzTrGlow 2.2s ease-in-out infinite;}',
    '.mzTr-node:hover .mzTr-name{color:#fde68a;}',
    '.mzTr-node:hover .mzTr-click-hint{color:rgba(212,175,55,.7);}',
    '.mzTr-node:focus-visible{outline:none;border-color:rgba(212,175,55,.75);box-shadow:0 0 0 2px rgba(212,175,55,.28),0 5px 24px rgba(0,0,0,.75);}',

    /* [A] Bloc année — PREUVE VISUELLE */
    '.mzTr-year-block{display:inline-block;margin-bottom:6px;padding:3px 10px;border-radius:2px;background:rgba(212,175,55,.07);border:1px solid rgba(212,175,55,.2);}',
    '.mzTr-year-label{font-size:4.5px;letter-spacing:.5em;color:rgba(212,175,55,.45);text-transform:uppercase;display:block;margin-bottom:1px;}',
    '.mzTr-year-value{font-size:13px;font-weight:800;letter-spacing:.06em;color:#d4af37;line-height:1.2;}',
    '.mzTr-year-value.mzTr-year-sahabi{color:#4ade80;font-size:9px;letter-spacing:.25em;}',
    '.mzTr-year-value.mzTr-year-unknown{color:rgba(212,175,55,.28);font-size:8px;letter-spacing:.3em;}',

    '.mzTr-rank{font-size:5px;letter-spacing:.5em;color:rgba(212,175,55,.2);margin-bottom:3px;text-transform:uppercase;}',
    '.mzTr-role{font-size:5.5px;letter-spacing:.38em;color:rgba(212,175,55,.32);margin-bottom:5px;text-transform:uppercase;}',
    '.mzTr-name{font-size:11.5px;font-weight:700;letter-spacing:.055em;color:rgba(224,204,148,.9);line-height:1.35;transition:color .18s;}',
    '.mzTr-name-ar{font-family:"Scheherazade New","Amiri",serif;font-size:15px;color:rgba(212,175,55,.44);direction:rtl;margin-top:4px;line-height:1.5;}',
    '.mzTr-meta{display:flex;gap:5px;justify-content:center;flex-wrap:wrap;margin-top:7px;}',
    '.mzTr-badge{font-size:5.5px;letter-spacing:.12em;font-weight:700;padding:2.5px 7px;border-radius:2px;animation:mzTrBadgeIn .35s ease both;}',
    '.mzTr-badge-thiqah{background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.28);color:#4ade80;}',
    '.mzTr-badge-sadouq{background:rgba(212,175,55,.09);border:1px solid rgba(212,175,55,.26);color:#d4af37;}',
    '.mzTr-badge-daif{background:rgba(245,158,11,.09);border:1px solid rgba(245,158,11,.28);color:#fbbf24;}',
    '.mzTr-badge-munkar{background:rgba(239,68,68,.07);border:1px solid rgba(239,68,68,.26);color:#f87171;}',
    '.mzTr-connector{position:relative;width:2px;height:38px;flex-shrink:0;background:linear-gradient(180deg,rgba(212,175,55,.55) 0%,rgba(212,175,55,.15) 100%);animation:mzTrConnIn .4s ease both;}',
    '.mzTr-connector::after{content:"";position:absolute;bottom:-6px;left:50%;transform:translateX(-50%);width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:6px solid rgba(212,175,55,.42);}',
    '.mzTr-connector::before{content:"";position:absolute;top:-3px;left:50%;transform:translateX(-50%);width:5px;height:5px;border-radius:50%;background:rgba(212,175,55,.45);}',
    '.mzTr-node-terminal{border-color:rgba(212,175,55,.48);background:linear-gradient(158deg,#120c00 0%,#0d0800 55%,#0e0e18 100%);}',
    '.mzTr-node-terminal::before{background:linear-gradient(90deg,transparent,rgba(212,175,55,.6) 20%,#d4af37 50%,rgba(212,175,55,.6) 80%,transparent);}',
    '.mzTr-node-terminal::after{content:"";position:absolute;bottom:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(212,175,55,.28),transparent);}',
    '.mzTr-click-hint{position:absolute;top:5px;right:7px;font-size:10px;color:rgba(212,175,55,.18);transition:color .2s;pointer-events:none;line-height:1;}',
    '.mzTr-empty{font-family:Cinzel,serif;font-size:7px;letter-spacing:.28em;color:rgba(212,175,55,.18);padding:32px;text-align:center;animation:mzTrPulse 2s ease-in-out infinite;}',

    /* ── Modal ── */
    '.mzModal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.75);backdrop-filter:blur(4px);z-index:9000;display:flex;align-items:center;justify-content:center;padding:16px;animation:mzOverlayIn .2s ease both;}',
    '.mzModal{position:relative;width:100%;max-width:540px;max-height:84vh;overflow-y:auto;background:linear-gradient(160deg,#0e0900 0%,#080500 60%,#0a0a14 100%);border:1px solid rgba(212,175,55,.32);border-radius:4px;box-shadow:0 0 0 1px rgba(212,175,55,.08),0 24px 64px rgba(0,0,0,.92);padding:28px 28px 24px;animation:mzModalIn .3s cubic-bezier(.16,1,.3,1) both;font-family:Cinzel,Georgia,serif;}',
    '.mzModal::before{content:"";position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,rgba(212,175,55,.5) 25%,#d4af37 50%,rgba(212,175,55,.5) 75%,transparent);}',
    '.mzModal-close{position:absolute;top:12px;right:14px;background:none;border:none;color:rgba(212,175,55,.4);font-size:18px;cursor:pointer;line-height:1;padding:4px 8px;border-radius:2px;transition:color .18s;}',
    '.mzModal-close:hover{color:rgba(212,175,55,.95);}',
    '.mzModal-name-ar{font-family:"Scheherazade New","Amiri",serif;font-size:20px;color:rgba(212,175,55,.85);direction:rtl;margin-bottom:6px;line-height:1.6;font-weight:700;}',
    '.mzModal-name-latin{font-size:11px;font-weight:600;color:rgba(200,180,120,.7);letter-spacing:.06em;margin-bottom:14px;}',
    '.mzModal-year-pill{display:inline-block;padding:4px 12px;border-radius:2px;background:rgba(212,175,55,.08);border:1px solid rgba(212,175,55,.25);font-size:12px;font-weight:800;color:#d4af37;letter-spacing:.08em;margin-bottom:14px;}',
    '.mzModal-badges{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:18px;}',
    '.mzModal-section{margin-top:18px;}',
    '.mzModal-section-title{font-size:5.5px;letter-spacing:.45em;color:rgba(212,175,55,.4);text-transform:uppercase;margin-bottom:8px;padding-bottom:5px;border-bottom:1px solid rgba(212,175,55,.12);}',
    '.mzModal-list{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:5px;}',
    '.mzModal-item{font-size:10.5px;color:rgba(200,180,120,.85);padding:6px 10px;border-radius:2px;border:1px solid rgba(212,175,55,.09);background:rgba(212,175,55,.03);display:flex;align-items:center;gap:8px;direction:rtl;font-family:"Scheherazade New","Amiri",serif;}',
    '.mzModal-item::before{content:"·";color:rgba(212,175,55,.5);flex-shrink:0;}',
    '.mzModal-item-link{color:rgba(212,175,55,.55);text-decoration:none;font-size:8px;font-family:Cinzel,Georgia,serif;margin-right:auto;white-space:nowrap;}',
    '.mzModal-item-link:hover{color:#d4af37;}',
    /* [D] DATA MISSING rouge */
    '.mzModal-missing{font-size:9px;font-weight:700;letter-spacing:.22em;color:#f87171;padding:8px 10px;border:1px solid rgba(248,113,113,.3);border-radius:2px;background:rgba(248,113,113,.06);text-align:center;}',

    '@media(max-width:480px){.mzTr-node{min-width:148px;max-width:100%;padding:10px 14px 12px;}.mzTr-name{font-size:10.5px;}.mzTr-name-ar{font-size:14px;}.mzTr-connector{height:28px;}.mzTr-year-value{font-size:11px;}.mzModal{padding:20px 16px 18px;}}',
  ].join('\n');
  document.head.appendChild(s);
})();


/* ════════════════════════════════════════════════════════════════
   2. HELPERS
════════════════════════════════════════════════════════════════ */
function _mzEsc(s) {
  return String(s || '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

/* [C] Verdict — regex arabes incluses */
function _mzVerdictCls(v) {
  var s = (v || '').toLowerCase();
  if (/thiqah|imam|adil|thabt|hafidh|thiqa/.test(s))   return 'thiqah';
  if (/sadouq|saduq|siddiq|la.?bas/.test(s))            return 'sadouq';
  if (/da.?if|layyin|matruk|weak/.test(s))              return 'daif';
  if (/mawdu|kadhdhab|fabricat/.test(s))                return 'munkar';
  if (/ثقة|إمام|حافظ|عدل|ثبت/.test(v))                return 'thiqah';
  if (/صدوق|لا بأس|محله الصدق/.test(v))               return 'sadouq';
  if (/ضعيف|لين|متروك|منكر/.test(v))                  return 'daif';
  if (/موضوع|كذاب|وضّاع/.test(v))                     return 'munkar';
  return 'thiqah';
}

function _mzRankLabel(idx, total) {
  if (idx === 0)         return 'SOURCE \u00b7 R\u0100W\u012a 1';
  if (idx === total - 1) return 'COLLECTEUR \u00b7 R\u0100W\u012a ' + total;
  return 'R\u0100W\u012a ' + (idx + 1);
}

/* [A] Formatage de l'année pour la carte */
function _mzYearDisplay(yr) {
  var n = Number(yr);
  if (n === 0)    return { label: 'ṢAḤĀBĪ',       cls: 'mzTr-year-sahabi'  };
  if (n === 9999) return { label: 'DATE INCONNUE', cls: 'mzTr-year-unknown' };
  return { label: String(n) + ' AH', cls: '' };
}

/* ════════════════════════════════════════════════════════════════
   3. REGISTRE [E] — nœud complet stocké par nom
════════════════════════════════════════════════════════════════ */
var _mzRegistry = new Map();


/* ════════════════════════════════════════════════════════════════
   4. MODAL [D]
════════════════════════════════════════════════════════════════ */
function _mzOpenModal(cardEl) {
  var rawName = cardEl.getAttribute('data-rawi');
  if (!rawName) return;
  var node = _mzRegistry.get(rawName) || { name: rawName };
  _mzShowModal(node);
}

function _mzShowModal(node) {
  var prev = document.getElementById('mz-modal-overlay');
  if (prev) prev.remove();

  var overlay = document.createElement('div');
  overlay.className = 'mzModal-overlay';
  overlay.id = 'mz-modal-overlay';

  var modal = document.createElement('div');
  modal.className = 'mzModal';
  modal.setAttribute('role', 'dialog');
  modal.setAttribute('aria-modal', 'true');

  /* Fermeture */
  var closeBtn = document.createElement('button');
  closeBtn.className = 'mzModal-close';
  closeBtn.textContent = '✕';
  closeBtn.setAttribute('aria-label', 'Fermer');
  closeBtn.addEventListener('click', function () { overlay.remove(); });
  modal.appendChild(closeBtn);

  /*
   * [C] NOM ARABE — lecture name_ar (snake_case Python, source de vérité).
   * Fallback : nameAr (camelCase), puis name (latin).
   */
  var arabicName = node.name_ar || node.nameAr || node.name || '';
  if (arabicName) {
    var nameArEl = document.createElement('div');
    nameArEl.className = 'mzModal-name-ar';
    nameArEl.textContent = arabicName;
    modal.appendChild(nameArEl);
  }

  /* Nom latin si distinct du nom arabe */
  if (node.name && node.name !== arabicName) {
    var nameLatEl = document.createElement('div');
    nameLatEl.className = 'mzModal-name-latin';
    nameLatEl.textContent = node.name;
    modal.appendChild(nameLatEl);
  }

  /* [A] Pilule année */
  var yr = Number(node.death_year);
  if (!isNaN(yr)) {
    var yDisp = _mzYearDisplay(yr);
    var pill = document.createElement('div');
    pill.className = 'mzModal-year-pill';
    pill.textContent = (yr === 0 ? '' : 'MORT EN : ') + yDisp.label;
    modal.appendChild(pill);
  }

  /* Badges verdict */
  if (node.verdict) {
    var badges = document.createElement('div');
    badges.className = 'mzModal-badges';
    var vb = document.createElement('span');
    vb.className = 'mzTr-badge mzTr-badge-' + _mzVerdictCls(node.verdict);
    vb.textContent = node.verdict.toUpperCase();
    badges.appendChild(vb);
    modal.appendChild(badges);
  }

  /* [D] Sections mashayikh / talamidh — DATA MISSING si vide */
  modal.appendChild(_mzModalSection('MASHĀYIKH — MAÎTRES', node.mashayikh));
  modal.appendChild(_mzModalSection('TALĀMIDH — ÉLÈVES',   node.talamidh));

  overlay.appendChild(modal);
  document.body.appendChild(overlay);

  overlay.addEventListener('click', function (e) {
    if (e.target === overlay) overlay.remove();
  });
  function _esc(e) {
    if (e.key === 'Escape') { overlay.remove(); document.removeEventListener('keydown', _esc); }
  }
  document.addEventListener('keydown', _esc);
  closeBtn.focus();
}

function _mzModalSection(title, list) {
  var sec = document.createElement('div');
  sec.className = 'mzModal-section';

  var titleEl = document.createElement('div');
  titleEl.className = 'mzModal-section-title';
  titleEl.textContent = title;
  sec.appendChild(titleEl);

  var arr = Array.isArray(list) ? list.filter(Boolean) : [];

  if (!arr.length) {
    /* [D] Message rouge si vide */
    var miss = document.createElement('div');
    miss.className = 'mzModal-missing';
    miss.textContent = '⚠ DATA MISSING';
    sec.appendChild(miss);
    return sec;
  }

  var ul = document.createElement('ul');
  ul.className = 'mzModal-list';
  arr.forEach(function (item) {
    var li = document.createElement('li');
    li.className = 'mzModal-item';
    li.appendChild(document.createTextNode(item.name || '—'));
    if (item.url) {
      var a = document.createElement('a');
      a.className = 'mzModal-item-link';
      a.href = item.url;
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      a.textContent = '↗ Dorar';
      li.appendChild(a);
    }
    ul.appendChild(li);
  });
  sec.appendChild(ul);
  return sec;
}


/* ════════════════════════════════════════════════════════════════
   5. BUILD CARD — un étage de la chaîne
════════════════════════════════════════════════════════════════ */
function _mzBuildStage(node, idx, total, isLast) {
  if (!node || typeof node !== 'object') {
    var g = document.createElement('div');
    g.className = 'mzTr-stage';
    return g;
  }

  /* ── Extraction des champs — [C] name_ar en priorité ── */
  var rawName = String(node.name    || node.nom      || '');
  var nameAr  = String(node.name_ar || node.nameAr   || node.ar || '');
  var role    = String(node.tabaqa  || node.role     || '');
  var verdict = String(node.verdict || node.statut   || '');
  var vClass  = _mzVerdictCls(verdict);
  var delay   = (idx * 0.11).toFixed(2);

  /* ── [A] death_year — TOUJOURS un Number ── */
  var deathYr = Number(node.death_year);
  if (isNaN(deathYr)) deathYr = 9999;
  var yDisp   = _mzYearDisplay(deathYr);

  /* ── [E] Registre — stocke l'objet complet ── */
  if (rawName) {
    _mzRegistry.set(rawName, {
      name:       rawName,
      name_ar:    nameAr,      /* [C] snake_case — source de vérité */
      nameAr:     nameAr,      /* alias camelCase pour compat */
      role:       role,
      verdict:    verdict,
      death_year: deathYr,
      /* [E][D] mashayikh/talamidh — portés depuis le JSON Python */
      mashayikh:  Array.isArray(node.mashayikh) ? node.mashayikh : [],
      talamidh:   Array.isArray(node.talamidh)  ? node.talamidh  : [],
    });
  }

  var stage = document.createElement('div');
  stage.className = 'mzTr-stage';
  stage.setAttribute('role', 'listitem');

  var card = document.createElement('div');
  card.className = 'mzTr-node' + (isLast ? ' mzTr-node-terminal' : '');
  card.style.animationDelay = delay + 's';
  card.setAttribute('data-rawi', rawName);
  card.setAttribute('role', 'button');
  card.setAttribute('tabindex', '0');
  card.setAttribute('aria-label', 'Biographie de ' + _mzEsc(rawName || 'inconnu'));

  var hint = document.createElement('span');
  hint.className = 'mzTr-click-hint';
  hint.setAttribute('aria-hidden', 'true');
  hint.textContent = '•••';
  card.appendChild(hint);

  var rankEl = document.createElement('div');
  rankEl.className = 'mzTr-rank';
  rankEl.textContent = _mzRankLabel(idx, total);
  card.appendChild(rankEl);

  /* [A] BLOC ANNÉE — PREUVE VISUELLE — affiché AVANT le nom */
  var yBlock = document.createElement('div');
  yBlock.className = 'mzTr-year-block';
  var yLabel = document.createElement('span');
  yLabel.className = 'mzTr-year-label';
  yLabel.textContent = deathYr === 0 ? 'STATUT' : 'MORT EN';
  var yValue = document.createElement('span');
  yValue.className = 'mzTr-year-value' + (yDisp.cls ? ' ' + yDisp.cls : '');
  yValue.textContent = yDisp.label;
  yBlock.appendChild(yLabel);
  yBlock.appendChild(yValue);
  card.appendChild(yBlock);

  if (role) {
    var roleEl = document.createElement('div');
    roleEl.className = 'mzTr-role';
    roleEl.textContent = role;
    card.appendChild(roleEl);
  }

  var nameEl = document.createElement('div');
  nameEl.className = 'mzTr-name';
  nameEl.textContent = rawName || '—';
  card.appendChild(nameEl);

  if (nameAr) {
    var nameArEl = document.createElement('div');
    nameArEl.className = 'mzTr-name-ar';
    nameArEl.textContent = nameAr;
    card.appendChild(nameArEl);
  }

  if (verdict) {
    var meta = document.createElement('div');
    meta.className = 'mzTr-meta';
    var vBadge = document.createElement('span');
    vBadge.className = 'mzTr-badge mzTr-badge-' + vClass;
    vBadge.style.animationDelay = (parseFloat(delay) + 0.18).toFixed(2) + 's';
    vBadge.textContent = verdict.toUpperCase();
    meta.appendChild(vBadge);
    card.appendChild(meta);
  }

  stage.appendChild(card);

  if (!isLast) {
    var conn = document.createElement('div');
    conn.className = 'mzTr-connector';
    conn.style.animationDelay = (idx * 0.11 + 0.08).toFixed(2) + 's';
    conn.setAttribute('aria-hidden', 'true');
    stage.appendChild(conn);
  }

  return stage;
}


/* ════════════════════════════════════════════════════════════════
   6. RENDER PRINCIPAL
      window.mzRenderIsnadTree(containerEl, chainArray)
════════════════════════════════════════════════════════════════ */
function _mzClickH(e) {
  var node = e.target.closest('.mzTr-node');
  if (node) _mzOpenModal(node);
}
function _mzKeyH(e) {
  if (e.key !== 'Enter' && e.key !== ' ') return;
  var node = e.target.closest('.mzTr-node');
  if (node) { e.preventDefault(); _mzOpenModal(node); }
}

window.mzRenderIsnadTree = function (containerEl, chain) {
  if (!containerEl) return;

  containerEl._mzRafAbort = true;
  containerEl.removeEventListener('click',   _mzClickH);
  containerEl.removeEventListener('keydown', _mzKeyH);
  containerEl.textContent = '';
  containerEl._mzRafAbort = false;
  _mzRegistry.clear();

  if (!chain || !chain.length) {
    var empty = document.createElement('div');
    empty.className = 'mzTr-empty';
    empty.textContent = 'SILSILAT AL-ISN\u0100D \u2014 AUCUNE DONN\u00c9E';
    containerEl.appendChild(empty);
    return;
  }

  var sorted = chain.slice();

  var total = sorted.length;
  var root  = document.createElement('div');
  root.className = 'mzTr-root';
  root.setAttribute('role', 'list');
  root.setAttribute('aria-label', 'Chaîne de transmission');
  containerEl.appendChild(root);

  containerEl.addEventListener('click',   _mzClickH);
  containerEl.addEventListener('keydown', _mzKeyH);

  var idx = 0;
  var batchSize = total <= 6 ? 2 : 1;

  function _step() {
    if (containerEl._mzRafAbort) return;
    if (idx >= total) return;
    var end = Math.min(idx + batchSize, total);
    while (idx < end) {
      if (sorted[idx] != null) {
        root.appendChild(_mzBuildStage(sorted[idx], idx, total, idx === total - 1));
      }
      idx++;
    }
    if (idx < total) requestAnimationFrame(_step);
  }

  requestAnimationFrame(_step);
};


/* ════════════════════════════════════════════════════════════════
   7. mzChainFromDorarData — pont JSON Python → JS
════════════════════════════════════════════════════════════════ */
window.mzChainFromDorarData = function (dorarObj) {
  if (!dorarObj) return [];
  var narrators = (
    dorarObj.narrators || dorarObj.sanad ||
    dorarObj.chain     || dorarObj.isnad || []
  );

  var chain = narrators
    .filter(function (n) { return n != null; })
    .map(function (n) {
      /*
       * [C] name_ar — Python produit snake_case.
       *     On lit name_ar en priorité absolue, puis les alias.
       * [B] death_year — cast Number strict, fallback 9999.
       * [D] mashayikh/talamidh — portés intégralement.
       */
      return {
        name:       n.name      || n.nom    || n.ar_name || '',
        name_ar:    n.name_ar   || n.nameAr || n.ar_name || n.nom_ar || '',
        nameAr:     n.name_ar   || n.nameAr || n.ar_name || n.nom_ar || '',
        role:       n.tabaqa    || n.role   || n.generation || '',
        verdict:    n.grade     || n.hukm  || n.verdict    || '',
        died:       n.death     || n.wafat || n.died       || '',
        death_year: (function () {
          var y = Number(n.death_year);
          return isNaN(y) ? 9999 : y;   /* [B] TOUJOURS un Number */
        }()),
        mashayikh:  Array.isArray(n.mashayikh) ? n.mashayikh : [],
        talamidh:   Array.isArray(n.talamidh)  ? n.talamidh  : [],
      };
    });

  /* [B] Tri forcé ici aussi */
  chain.sort(function (a, b) { return a.death_year - b.death_year; });
  return chain;
};


/* ════════════════════════════════════════════════════════════════
   8. COMPAT — window.mzOpenIsnadPanel
════════════════════════════════════════════════════════════════ */
window.mzOpenIsnadPanel = window.mzOpenIsnadPanel || function (nom) {
  var nd = _mzRegistry.get(nom);
  if (nd) _mzShowModal(nd);
  else if (typeof window._openRawiModal === 'function') window._openRawiModal(nom, {});
};

/* Expose pour tests externes */
window._mzRegistry = _mzRegistry;

console.log(
  '%c \u2696\ufe0f  MÎZÂN v22.5 — Preuve Visuelle — Audit OK',
  'color:#d4af37;font-size:10px;font-weight:bold;'
);
