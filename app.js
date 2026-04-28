/* ═══════════════════════════════════════════════════════════════════
   MÎZÂN v18.4 — app.js
   Rôle    : Navigation + Zone 2 (19 Plaques Silsilah al-Isnad)
   Données : EXTERNALISÉES dans data.js (window.SCHOLARS_DB, window.VERDICTS_DB)
   ─────────────────────────────────────────────────────────────────
   Bouclier de Portée  : window.goTo déclaré EN PREMIER — ABSOLU
   Bouclier de Syntaxe : createElement / textContent EXCLUSIVEMENT
   Bouclier de Science : Zone 2 min-height:40px + titre doré z-index:10
   Mouchard de Vérité  : console.log vert #00ff00 au démarrage
═══════════════════════════════════════════════════════════════════ */

console.log("%c ✅ Mîzân v18.4 : Prêt pour Production", "color: #00ff00; font-weight: bold;");

/* ══════════════════════════════════════════════════════════════
   BOUCLIER DE PORTÉE — window.goTo — POSITION ABSOLUE N°1
══════════════════════════════════════════════════════════════ */
window.goTo = function(view) {
  document.querySelectorAll('.view').forEach(function(v) {
    v.classList.remove('active');
  });
  var el = document.getElementById('view-' + view);
  if (el) { el.classList.add('active'); el.scrollTop = 0; }
};

/* ══════════════════════════════════════════════════════════════
   window.parseSiecle v18.4
   Retourne : { num, era, couche(1-5), numRaw }
   5 couches : Sahaba · Tabi'în · Fondateurs · Huffadh · Contemp.
══════════════════════════════════════════════════════════════ */
window.parseSiecle = function(s) {
  if (!s || typeof s !== 'string') return null;
  var m = s.match(/(\d+)/);
  if (!m) return null;
  var num = m[1], n = parseInt(num), era = '', couche = 3;
  if      (/sahab|compagnon|\u0635\u062d\u0627\u0628/i.test(s))        { era = 'Ère Prophétique'; couche = 1; }
  else if (/tabi|\u062a\u0627\u0628\u0639/i.test(s))                   { era = "Tabi'în";         couche = 2; }
  else if (/contemp|\u0645\u0639\u0627\u0635\u0631/i.test(s))          { era = 'Contemporain';    couche = 5; }
  else if (/huffadh|\u062d\u0641\u0627\u0638/i.test(s))                { era = 'Huffadh';         couche = 4; }
  else if (/fondateur|\u0645\u0624\u0633\u0633/i.test(s))              { era = 'Fondateurs';      couche = 3; }
  else if (/mecqu|\u0645\u0643\u064a/i.test(s))                        { era = 'Mecquois';        couche = 1; }
  else if (/medin|\u0645\u062f\u0646\u064a/i.test(s))                  { era = 'Médinois';        couche = 1; }
  else if (n <= 2)  { era = 'Sahaba';       couche = 1; }
  else if (n <= 4)  { era = "Tabi'în";      couche = 2; }
  else if (n <= 7)  { era = 'Fondateurs';   couche = 3; }
  else if (n <= 10) { era = 'Huffadh';      couche = 4; }
  else              { era = 'Contemporain'; couche = 5; }
  return { num: num + 'e', era: era, couche: couche, numRaw: n };
};

/* ══════════════════════════════════════════════════════════════
   window.nodeVis v18.4
   Palette chromatique : chaque Kibâr a sa couleur signature
   Retourne : { dotC, dotGlow, dotSahaba, nameC, cenC, beamOp, vBg, vC }
══════════════════════════════════════════════════════════════ */
window.nodeVis = function(titre, verdict, idx, total) {
  var tv = ((titre || '') + ' ' + (verdict || '')).toLowerCase();
  var o = {
    dotC: '#d4af37', dotGlow: '0 0 10px rgba(212,175,55,.5)', dotSahaba: false,
    nameC: '#d4af37', cenC: 'rgba(212,175,55,.5)',
    beamOp: '.7', vBg: 'rgba(34,197,94,.08)', vC: '#22c55e'
  };
  if      (/sahab|compagnon|adul.*ijma|\u0635\u062d\u0627\u0628\u064a/i.test(tv)) {
    o.dotC = '#d4af37'; o.dotGlow = '0 0 22px #d4af37,0 0 44px rgba(212,175,55,.5)';
    o.dotSahaba = true; o.nameC = '#e8c96a';
    o.vBg = 'rgba(212,175,55,.1)'; o.vC = '#d4af37';
  } else if (/da.?if|faible|matruk|munkar|kadhdhab|majhul|layyin/i.test(tv)) {
    o.dotC = '#ef4444'; o.dotGlow = '0 0 12px rgba(239,68,68,.6)';
    o.nameC = '#fca5a5'; o.cenC = 'rgba(239,68,68,.5)'; o.beamOp = '.3';
    o.vBg = 'rgba(239,68,68,.08)'; o.vC = '#ef4444';
  } else if (/saduq|maqbul/i.test(tv)) {
    o.dotC = '#f59e0b'; o.dotGlow = '0 0 10px rgba(245,158,11,.5)';
    o.nameC = '#fbbf24'; o.vBg = 'rgba(245,158,11,.08)'; o.vC = '#f59e0b';
  } else if (/thiqah|thabt|hujjah|mutqin/i.test(tv)) {
    o.dotC = '#22c55e'; o.dotGlow = '0 0 12px rgba(34,197,94,.5)'; o.nameC = '#86efac';
  } else if (/albani|\u0623\u0644\u0628\u0627\u0646\u064a|muhaddith.*asr/i.test(tv)) {
    o.dotC = '#a78bfa'; o.dotGlow = '0 0 20px rgba(167,139,250,.7),0 0 44px rgba(167,139,250,.2)';
    o.nameC = '#c4b5fd'; o.cenC = 'rgba(167,139,250,.6)';
    o.vBg = 'rgba(167,139,250,.1)'; o.vC = '#a78bfa';
  } else if (/ibn.*baz|\u0628\u0646.*\u0628\u0627\u0632|mufti/i.test(tv)) {
    o.dotC = '#60a5fa'; o.dotGlow = '0 0 20px rgba(96,165,250,.7),0 0 44px rgba(96,165,250,.2)';
    o.nameC = '#93c5fd'; o.cenC = 'rgba(96,165,250,.6)';
    o.vBg = 'rgba(96,165,250,.1)'; o.vC = '#60a5fa';
  } else if (/uthaymin|\u0639\u062b\u064a\u0645\u064a\u0646/i.test(tv)) {
    o.dotC = '#34d399'; o.dotGlow = '0 0 20px rgba(52,211,153,.7),0 0 44px rgba(52,211,153,.2)';
    o.nameC = '#6ee7b7'; o.cenC = 'rgba(52,211,153,.6)';
    o.vBg = 'rgba(52,211,153,.1)'; o.vC = '#34d399';
  } else if (/muqbil|\u0645\u0642\u0628\u0644|wadi/i.test(tv)) {
    o.dotC = '#fbbf24'; o.dotGlow = '0 0 20px rgba(251,191,36,.7),0 0 44px rgba(251,191,36,.2)';
    o.nameC = '#fcd34d'; o.cenC = 'rgba(251,191,36,.6)';
    o.vBg = 'rgba(251,191,36,.1)'; o.vC = '#fbbf24';
  } else if (/rabi|\u0631\u0628\u064a\u0639|madkhali|\u0645\u062f\u062e\u0644\u064a/i.test(tv)) {
    o.dotC = '#f472b6'; o.dotGlow = '0 0 20px rgba(244,114,182,.7),0 0 44px rgba(244,114,182,.2)';
    o.nameC = '#f9a8d4'; o.cenC = 'rgba(244,114,182,.6)';
    o.vBg = 'rgba(244,114,182,.1)'; o.vC = '#f472b6';
  } else if (/fawzan|\u0641\u0648\u0632\u0627\u0646|imam|verificateur|compilateur/i.test(tv)) {
    o.dotC = '#a78bfa'; o.dotGlow = '0 0 14px rgba(167,139,250,.6)';
    o.nameC = '#c4b5fd'; o.cenC = 'rgba(167,139,250,.5)';
    o.vBg = 'rgba(167,139,250,.08)'; o.vC = '#a78bfa';
  }
  return o;
};

/* ══════════════════════════════════════════════════════════════
   window.mzCloseIsnadPanel — Fermeture offcanvas Zone 2
══════════════════════════════════════════════════════════════ */
window.mzCloseIsnadPanel = function() {
  var bd = document.getElementById('mz-isnad-panel-bd');
  var p  = document.getElementById('mz-isnad-panel');
  if (p)  p.style.transform = 'translateX(100%)';
  if (bd) bd.style.opacity  = '0';
  setTimeout(function() {
    if (bd) bd.remove();
    if (p)  p.remove();
  }, 400);
};

/* ══════════════════════════════════════════════════════════════
   window.mzOpenIsnadPanel — OFFCANVAS Zone 2
   BOUCLIER SYNTAXE : createElement / textContent EXCLUSIVEMENT
   DONNÉES : déléguées à window.SCHOLARS_DB et window.VERDICTS_DB
══════════════════════════════════════════════════════════════ */
window.mzOpenIsnadPanel = function(nom, titre, verdict, siecle, dotC) {
  /* Nettoyage des instances précédentes */
  var old = document.getElementById('mz-isnad-panel-bd');
  if (old) old.remove();
  var oldP = document.getElementById('mz-isnad-panel');
  if (oldP) oldP.remove();

  /* ── DONNÉES : lookup dans data.js — ZÉRO data ici ── */
  var bio = window.SCHOLARS_DB ? window.SCHOLARS_DB[nom.toLowerCase()] : null;
  var vc  = (verdict || '').replace(/_/g, ' ');
  var vs  = window.VERDICTS_DB ? (window.VERDICTS_DB[vc.toLowerCase()] || '') : '';

  var isJarh = /da.?if|matruk|kadhdhab|munkar|majhul/i.test(vc);
  var vClr   = isJarh ? '#ef4444' : (dotC || '#4ade80');

  /* ── BACKDROP ── */
  var bd = document.createElement('div');
  bd.id = 'mz-isnad-panel-bd';
  bd.style.cssText = [
    'position:fixed;inset:0;z-index:9998;',
    'background:rgba(0,0,0,.6);backdrop-filter:blur(4px);',
    'opacity:0;transition:opacity .35s;'
  ].join('');
  bd.addEventListener('click', function(e) {
    if (e.target === bd) window.mzCloseIsnadPanel();
  });

  /* ── PANEL PRINCIPAL ── */
  var p = document.createElement('div');
  p.id = 'mz-isnad-panel';
  p.style.cssText = [
    'position:fixed;top:0;right:0;bottom:0;width:min(380px,88vw);z-index:9999;',
    'background:linear-gradient(170deg,#0d0a02,#111827);',
    'border-left:1px solid rgba(212,175,55,.2);',
    'box-shadow:-10px 0 60px rgba(0,0,0,.8);',
    'transform:translateX(100%);transition:transform .4s cubic-bezier(.4,0,.2,1);',
    'overflow-y:auto;'
  ].join('');

  /* ── HEADER ── */
  var header = document.createElement('div');
  header.style.cssText = 'padding:20px;border-bottom:1px solid rgba(212,175,55,.1);';

  var headerRow = document.createElement('div');
  headerRow.style.cssText = 'display:flex;justify-content:space-between;align-items:flex-start;';

  var headerLeft = document.createElement('div');

  var ficheLabel = document.createElement('p');
  ficheLabel.style.cssText = [
    'font-family:Cinzel,serif;font-size:5.5px;font-weight:700;',
    'letter-spacing:.35em;color:rgba(212,175,55,.4);margin-bottom:6px;'
  ].join('');
  ficheLabel.textContent = 'FICHE — SILSILAT AL-ISNĀD';

  var nomEl = document.createElement('p');
  nomEl.style.cssText = [
    'font-family:Scheherazade New,serif;font-size:24px;',
    'font-weight:700;line-height:1.2;color:' + (dotC || '#d4af37') + ';'
  ].join('');
  nomEl.textContent = nom;

  headerLeft.appendChild(ficheLabel);
  headerLeft.appendChild(nomEl);

  if (bio && bio.ar) {
    var nomAr = document.createElement('p');
    nomAr.style.cssText = 'font-family:Scheherazade New,serif;font-size:16px;color:rgba(212,175,55,.5);margin-top:2px;';
    nomAr.textContent = bio.ar;
    headerLeft.appendChild(nomAr);
  }

  /* Bouton fermer */
  var btnClose = document.createElement('button');
  btnClose.style.cssText = [
    'background:rgba(212,175,55,.07);border:1px solid rgba(212,175,55,.15);',
    'border-radius:50%;width:32px;height:32px;cursor:pointer;',
    'color:rgba(212,175,55,.5);font-size:16px;',
    'display:flex;align-items:center;justify-content:center;flex-shrink:0;'
  ].join('');
  btnClose.textContent = '×';
  btnClose.addEventListener('click', window.mzCloseIsnadPanel);

  headerRow.appendChild(headerLeft);
  headerRow.appendChild(btnClose);
  header.appendChild(headerRow);
  p.appendChild(header);

  /* ── BODY ── */
  var body = document.createElement('div');
  body.style.cssText = 'padding:20px;';

  /* Bloc verdict */
  var verdictBox = document.createElement('div');
  verdictBox.style.cssText = [
    'background:rgba(0,0,0,.3);',
    'border:1px solid ' + vClr + '22;border-left:3px solid ' + vClr + ';',
    'border-radius:8px;padding:14px 16px;margin-bottom:16px;'
  ].join('');

  var verdictLabel = document.createElement('p');
  verdictLabel.style.cssText = [
    'font-family:Cinzel,serif;font-size:6px;font-weight:700;',
    'letter-spacing:.25em;color:' + vClr + ';margin-bottom:6px;'
  ].join('');
  verdictLabel.textContent = 'VERDICT — JARḤ WA TAʿDĪL';

  var verdictVal = document.createElement('p');
  verdictVal.style.cssText = 'font-family:Cinzel,serif;font-size:11px;font-weight:700;color:' + vClr + ';margin-bottom:4px;';
  verdictVal.textContent = vc;

  verdictBox.appendChild(verdictLabel);
  verdictBox.appendChild(verdictVal);

  if (vs) {
    var verdictDesc = document.createElement('p');
    verdictDesc.style.cssText = [
      'font-family:Cormorant Garamond,serif;font-style:italic;',
      'font-size:13px;color:rgba(220,200,160,.65);line-height:1.6;'
    ].join('');
    verdictDesc.textContent = '→ ' + vs;
    verdictBox.appendChild(verdictDesc);
  }
  body.appendChild(verdictBox);

  /* Bloc bio — structure portée par data.js */
  if (bio) {
    var BIO_FIELDS = [
      { label: 'DATES',                     key: 'd' },
      { label: 'RÔLE DANS LA PRÉSERVATION', key: 'r' },
      { label: 'OUVRAGES MAJEURS',          key: 'o' }
    ];
    BIO_FIELDS.forEach(function(f) {
      if (!bio[f.key]) return;
      var lbl = document.createElement('p');
      lbl.style.cssText = [
        'font-family:Cinzel,serif;font-size:6px;font-weight:700;',
        'letter-spacing:.2em;color:rgba(212,175,55,.4);margin-bottom:6px;'
      ].join('');
      lbl.textContent = f.label;

      var val = document.createElement('p');
      val.style.cssText = [
        'font-family:Cormorant Garamond,serif;font-size:14px;',
        'color:rgba(220,200,160,.7);line-height:1.8;margin-bottom:14px;'
      ].join('');
      val.textContent = bio[f.key];

      body.appendChild(lbl);
      body.appendChild(val);
    });
  } else {
    var noData = document.createElement('p');
    noData.style.cssText = [
      'font-family:Cormorant Garamond,serif;font-style:italic;',
      'font-size:13px;color:rgba(201,168,76,.35);line-height:1.7;'
    ].join('');
    noData.textContent = 'Consultez le Taqrīb at-Tahdhīb d\'Ibn Ḥajar.';
    body.appendChild(noData);
  }

  p.appendChild(body);

  /* ── INJECTION & ANIMATION ── */
  document.body.appendChild(bd);
  document.body.appendChild(p);
  requestAnimationFrame(function() {
    bd.style.opacity  = '1';
    p.style.transform = 'translateX(0)';
  });
};

/* ══════════════════════════════════════════════════════════════
   ZONE 2 — INJECTION CSS CÉLESTE (unique)
   Bouclier Science : styles des 19 plaques + fil d'or
══════════════════════════════════════════════════════════════ */
window.mzInjectIsnadCSS = function() {
  if (document.getElementById('mzPipe-css')) return;
  var sc = document.createElement('style');
  sc.id = 'mzPipe-css';
  sc.textContent = [
    '@keyframes mzHalo{0%,100%{box-shadow:0 0 40px rgba(255,220,80,.55),0 0 80px rgba(212,175,55,.2)}50%{box-shadow:0 0 70px rgba(255,220,80,.9),0 0 130px rgba(212,175,55,.4)}}',
    '@keyframes mzGlow{0%,100%{text-shadow:0 0 14px rgba(212,175,55,.5)}50%{text-shadow:0 0 32px rgba(255,215,0,.9),0 0 60px rgba(212,175,55,.4)}}',
    '@keyframes mzIn{from{opacity:0;transform:translateY(16px) scale(.95)}to{opacity:1;transform:translateY(0) scale(1)}}',
    '@keyframes mzChain{0%{background-position:0 0}100%{background-position:0 40px}}',
    '@keyframes mzBranchL{from{opacity:0;transform:translateX(16px)}to{opacity:1;transform:translateX(0)}}',
    '@keyframes mzBranchR{from{opacity:0;transform:translateX(-16px)}to{opacity:1;transform:translateX(0)}}',
    '@keyframes mzRootGlow{0%,100%{opacity:.35}50%{opacity:.7}}',
    '.mzT{position:relative;width:100%;min-height:40px;display:flex;flex-direction:column;align-items:center;padding:0 4px 32px;overflow:hidden;background:radial-gradient(ellipse at 50% 0%,rgba(212,175,55,.06) 0%,transparent 65%);}',
    '.mzT-svg{position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0;}',
    '.mzT-ti{font-family:Cinzel,serif;font-size:5.5px;letter-spacing:.38em;color:rgba(212,175,55,.3);margin-bottom:14px;z-index:10;position:relative;text-align:center;padding-top:16px;}',
    '.mzT-ph{display:flex;flex-direction:column;align-items:center;z-index:10;position:relative;margin-bottom:2px;}',
    '.mzT-hl{width:100px;height:100px;border-radius:50%;background:radial-gradient(circle at 38% 32%,rgba(255,230,100,.28),rgba(212,175,55,.08) 55%,transparent 72%);border:2.5px solid rgba(212,175,55,.8);display:flex;align-items:center;justify-content:center;font-size:38px;animation:mzHalo 4s ease-in-out infinite;position:relative;box-shadow:0 0 0 6px rgba(212,175,55,.06),0 0 0 12px rgba(212,175,55,.03);}',
    '.mzT-hl::before{content:"";position:absolute;inset:-10px;border-radius:50%;border:1px solid rgba(212,175,55,.15);animation:mzHalo 4s ease-in-out infinite reverse;}',
    '.mzT-pn{font-family:Scheherazade New,serif;font-size:22px;font-weight:700;color:#d4af37;animation:mzGlow 3s ease-in-out infinite;margin:5px 0 1px;text-align:center;}',
    '.mzT-ps{font-family:Cinzel,serif;font-size:7.5px;font-weight:700;color:rgba(255,215,0,.7);letter-spacing:.12em;text-align:center;}',
    '.mzT-po{font-family:Cinzel,serif;font-size:5px;letter-spacing:.2em;color:rgba(212,175,55,.3);text-align:center;margin-top:3px;}',
    '.mzT-tk{width:6px;background:repeating-linear-gradient(180deg,rgba(212,175,55,.9) 0px,rgba(180,140,30,.5) 8px,rgba(212,175,55,.9) 16px);background-size:100% 40px;animation:mzChain 1.8s linear infinite;border-radius:3px;flex-shrink:0;margin:0 auto;z-index:5;position:relative;box-shadow:0 0 8px rgba(212,175,55,.25);}',
    '.mzT-bk{font-family:Cinzel,serif;font-size:5px;font-weight:700;letter-spacing:.14em;color:rgba(212,175,55,.4);padding:2px 10px;border:1px solid rgba(212,175,55,.12);border-radius:10px;background:rgba(8,5,0,.92);z-index:10;margin:4px auto;display:block;text-align:center;width:fit-content;position:relative;}',
    '.mzT-row{display:flex;align-items:center;justify-content:center;width:100%;max-width:370px;margin:4px auto;gap:0;z-index:10;position:relative;}',
    '.mzT-col{flex:0 0 110px;display:flex;flex-direction:column;gap:6px;}',
    '.mzT-col-c{flex:0 0 128px;display:flex;flex-direction:column;align-items:center;}',
    '.mzT-br{flex:1;height:2px;max-width:16px;min-width:6px;position:relative;align-self:center;}',
    '.mzT-brl{background:linear-gradient(to right,rgba(212,175,55,.08),rgba(212,175,55,.55));animation:mzBranchL .6s ease both;}',
    '.mzT-brr{background:linear-gradient(to left,rgba(212,175,55,.08),rgba(212,175,55,.55));animation:mzBranchR .6s ease both;}',
    '.mzT-crd{display:flex;flex-direction:column;align-items:center;cursor:pointer;width:128px;padding:12px 10px 10px;border-radius:4px 4px 12px 12px;border:1.5px solid;transition:all .28s cubic-bezier(.4,0,.2,1);animation:mzIn .55s ease both;text-align:center;position:relative;clip-path:polygon(8% 0%,92% 0%,100% 8%,100% 92%,92% 100%,8% 100%,0% 92%,0% 8%);}',
    '.mzT-crd::before{content:"";position:absolute;inset:0;background:linear-gradient(160deg,rgba(255,255,255,.05) 0%,transparent 55%);pointer-events:none;border-radius:inherit;}',
    '.mzT-crd:hover{transform:scale(1.06) translateY(-2px);z-index:20;}.mzT-crd:active{transform:scale(.97);}',
    '.mzT-cn{font-family:Cinzel,serif;font-size:8px;font-weight:900;letter-spacing:.06em;line-height:1.25;margin-bottom:2px;white-space:pre-line;}',
    '.mzT-cd{font-family:Cormorant Garamond,serif;font-size:10px;font-style:italic;opacity:.7;margin-bottom:3px;line-height:1.4;}',
    '.mzT-cr{font-family:Cinzel,serif;font-size:5.5px;opacity:.5;margin-bottom:6px;line-height:1.5;white-space:pre-line;}',
    '.mzT-vd{font-family:Cinzel,serif;font-size:7px;font-weight:900;letter-spacing:.15em;padding:3px 12px;border-radius:4px;border:1.5px solid;display:inline-block;}',
    '.mzT-mn{cursor:pointer;padding:8px 7px 7px;border-radius:8px;border:1px solid;transition:all .25s;animation:mzIn .5s ease both;text-align:center;width:100%;clip-path:polygon(6% 0%,94% 0%,100% 6%,100% 94%,94% 100%,6% 100%,0% 94%,0% 6%);}',
    '.mzT-mn:hover{transform:scale(1.05) translateY(-1px);z-index:20;}.mzT-mn:active{transform:scale(.97);}',
    '.mzT-mnn{font-family:Cinzel,serif;font-size:6px;font-weight:700;line-height:1.3;display:block;white-space:pre-line;}',
    '.mzT-mnd{font-family:Cormorant Garamond,serif;font-size:9px;font-style:italic;display:block;margin-top:1px;opacity:.65;}',
    '.mzT-mnr{font-family:Cinzel,serif;font-size:4.5px;letter-spacing:.06em;display:block;margin-top:2px;opacity:.5;white-space:pre-line;}',
    '.mzT-mnv{font-family:Cinzel,serif;font-size:6px;font-weight:700;letter-spacing:.1em;padding:2px 8px;border-radius:3px;border:1px solid;display:inline-block;margin-top:5px;}',
    '.mzV-T{background:rgba(34,197,94,.12);color:#22c55e;border-color:rgba(34,197,94,.45);}',
    '.mzV-A{background:rgba(212,175,55,.1);color:#d4af37;border-color:rgba(212,175,55,.4);}',
    '.mzV-M{background:rgba(239,68,68,.1);color:#ef4444;border-color:rgba(239,68,68,.4);}',
    '.mzT-rt{width:100%;max-width:320px;height:40px;position:relative;z-index:5;margin-top:4px;}',
    '.mzT-ft{font-family:Cinzel,serif;font-size:5px;letter-spacing:.26em;color:rgba(212,175,55,.14);text-align:center;margin-top:16px;padding-top:10px;border-top:1px solid rgba(212,175,55,.05);width:100%;z-index:10;position:relative;}'
  ].join('');
  document.head.appendChild(sc);
};

var MZ_COUCHE_LABELS = {
  1: 'COUCHE 1 — AS-SAHĀBA',
  2: "COUCHE 2 — AT-TĀBI'ĪN & IMAMS",
  3: 'COUCHE 3 — FONDATEURS',
  4: 'COUCHE 4 — HUFFADH & PILIERS',
  5: 'COUCHE 5 — CONTEMPORAINS (15e S. HÉGIRE)'
};
var MZ_COUCHE_COLORS = {
  1: '#d4af37', 2: '#22c55e', 3: '#60a5fa', 4: '#f59e0b', 5: '#a78bfa'
};

/* ══════════════════════════════════════════════════════════════
   _mzBuildNodes — Parsing + Déduplication + Tri chrono
   Entrée  : isnadChain (string pipe-séparé)
   Sortie  : nodes[] triés par couche chronologique
══════════════════════════════════════════════════════════════ */
function _mzBuildNodes(isnadChain) {
  if (!isnadChain || typeof isnadChain !== 'string') return [];
  var rawStr = isnadChain.replace(/\\n/g, '\n');
  rawStr = rawStr.replace(/\s*[\u2014\u2013]\s*/g, ' | ').replace(/\s+-\s+/g, ' | ');
  var lines = rawStr.indexOf('\n') !== -1
    ? rawStr.split('\n')
    : rawStr.split(/(?=Maillon\s+\d)/i);
  lines = lines
    .map(function(l) { return typeof l === 'string' ? l.trim() : ''; })
    .filter(function(l) { return l.length > 2; });

  var nodes = [], seen = {};
  for (var i = 0; i < lines.length; i++) {
    try {
      var parts  = lines[i].split('|');
      var nom    = (parts[1] || '').trim();
      if (!nom || nom.length < 2) continue;
      var key = nom.toLowerCase()
        .replace(/[\u064B-\u065F\u0670]/g, '')
        .replace(/[^a-z0-9\u0600-\u06FF]/g, '');
      if (seen[key]) { console.log('[v18.4] Doublon filtré : ' + nom); continue; }
      seen[key] = true;
      var titR   = (parts[2] || '').trim();
      var verR   = (parts[3] || '').trim().replace(/_/g, ' ');
      var sieR   = (parts[4] || '').trim();
      var ep     = window.parseSiecle(sieR);
      var couche = ep ? ep.couche : 3;
      var numS   = ep ? ep.numRaw : 5;
      var combo  = (nom + ' ' + titR + ' ' + verR).toLowerCase();
      if (/albani|ibn.*baz|uthaymin|muqbil|rabi|madkhali|fawzan|contemporain|verificateur/i.test(combo)) {
        couche = 5;
        numS   = Math.max(numS, 14);
      }
      nodes.push({
        num: String(nodes.length + 1),
        nom: nom, titre: titR, verdict: verR, siecle: sieR,
        _c: couche, _n: numS
      });
    } catch(_) {}
  }

  nodes.sort(function(a, b) {
    return a._c !== b._c ? a._c - b._c : a._n - b._n;
  });
  for (var r = 0; r < nodes.length; r++) nodes[r].num = String(r + 1);
  return nodes;
}

/* ══════════════════════════════════════════════════════════════
   _mzAppendFil — Fil d'or entre deux plaques (helper)
   Bouclier Syntaxe : createElement / textContent
══════════════════════════════════════════════════════════════ */
function _mzAppendTrunk(parent, h) {
  var d = document.createElement('div');
  d.className = 'mzT-tk';
  d.style.height = h || '24px';
  parent.appendChild(d);
}
function _mzAppendFil(parent, height, opacity, label) {
  var d = document.createElement('div');
  d.className = 'mzT-tk';
  d.style.cssText = 'height:' + height + ';opacity:' + opacity + ';';
  parent.appendChild(d);
}

function _mzRenderZone2(container, nodes) {
  container.id        = 'mz-isnad-container';
  container.className = 'mzT';
  container.style.minHeight = '40px';

  /* ── SVG fond arbre organique ── */
  var svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
  svg.setAttribute('class','mzT-svg');
  svg.setAttribute('viewBox','0 0 370 1100');
  svg.setAttribute('preserveAspectRatio','xMidYMid slice');
  /* Gradient tronc */
  var def=document.createElementNS('http://www.w3.org/2000/svg','defs');
  var grd=document.createElementNS('http://www.w3.org/2000/svg','linearGradient');
  grd.setAttribute('id','mzTkG');grd.setAttribute('x1','0');grd.setAttribute('y1','0');grd.setAttribute('x2','0');grd.setAttribute('y2','1');
  [{o:'0',c:'rgba(212,175,55,.7)'},{o:'.4',c:'rgba(180,140,30,.3)'},{o:'.7',c:'rgba(212,175,55,.6)'},{o:'1',c:'rgba(160,120,20,.4)'}].forEach(function(s){var st=document.createElementNS('http://www.w3.org/2000/svg','stop');st.setAttribute('offset',s.o);st.setAttribute('stop-color',s.c);grd.appendChild(st);});
  def.appendChild(grd);svg.appendChild(def);
  /* Tronc principal tresse */
  [{d:'M183 110 C177 260,189 400,181 540 C173 680,185 820,179 960 C175 1040,180 1080,183 1100',sw:'8',sc:'url(#mzTkG)'},{d:'M186 110 C194 185,178 260,187 335 C196 410,180 485,189 560 C198 635,183 710,192 785 C201 860,186 935,194 1010 C200 1060,191 1080,188 1100',sw:'4',sc:'rgba(180,140,30,.4)'},{d:'M179 110 C171 185,183 260,175 335 C167 410,179 485,172 560 C165 635,177 710,170 785 C163 860,175 935,168 1010 C164 1060,172 1080,175 1100',sw:'3',sc:'rgba(160,120,20,.35)'}].forEach(function(t){var p=document.createElementNS('http://www.w3.org/2000/svg','path');p.setAttribute('d',t.d);p.setAttribute('stroke',t.sc);p.setAttribute('stroke-width',t.sw);p.setAttribute('fill','none');p.setAttribute('stroke-linecap','round');svg.appendChild(p);});
  /* Branches gauches */
  ['M181 210 C155 205,115 192,72 180','M180 335 C152 330,112 312,68 292','M180 460 C150 456,110 440,64 422','M179 585 C148 582,107 568,61 553','M179 710 C148 707,106 694,60 679','M178 835 C148 832,106 818,60 805'].forEach(function(d){var p=document.createElementNS('http://www.w3.org/2000/svg','path');p.setAttribute('d',d);p.setAttribute('stroke','rgba(212,175,55,.3)');p.setAttribute('stroke-width','2');p.setAttribute('fill','none');svg.appendChild(p);});
  /* Branches droites */
  ['M189 210 C215 205,255 192,298 180','M190 335 C218 330,258 312,302 292','M190 460 C220 456,260 440,306 422','M191 585 C222 582,263 568,309 553','M191 710 C222 707,264 694,310 679','M192 835 C222 832,264 818,310 805'].forEach(function(d){var p=document.createElementNS('http://www.w3.org/2000/svg','path');p.setAttribute('d',d);p.setAttribute('stroke','rgba(212,175,55,.3)');p.setAttribute('stroke-width','2');p.setAttribute('fill','none');svg.appendChild(p);});
  /* Racines */
  ['M183 1100 C163 1110,133 1115,100 1118','M183 1100 C183 1112,183 1118,183 1120','M183 1100 C203 1110,233 1115,266 1118','M183 1100 C148 1108,113 1116,83 1120','M183 1100 C218 1108,253 1116,283 1120'].forEach(function(d){var p=document.createElementNS('http://www.w3.org/2000/svg','path');p.setAttribute('d',d);p.setAttribute('stroke','rgba(212,175,55,.22)');p.setAttribute('stroke-width','2.5');p.setAttribute('fill','none');svg.appendChild(p);});
  container.appendChild(svg);

  /* ── Titre doré z-index:10 INEFFACABLE ── */
  var ti=document.createElement('p'); ti.className='mzT-ti'; ti.textContent='ZONE 2 — SILSILAT AL-ISNAD — 14 SIECLES'; container.appendChild(ti);

  /* ── Halo prophétique ── */
  var ph=document.createElement('div'); ph.className='mzT-ph';
  var hl=document.createElement('div'); hl.className='mzT-hl'; hl.textContent='\uFDFA'; ph.appendChild(hl);
  var pn=document.createElement('p'); pn.className='mzT-pn'; pn.textContent='\u0627\u0644\u0646\u0628\u064a \u0645\u062d\u0645\u062f \uFDFA'; ph.appendChild(pn);
  var ps=document.createElement('p'); ps.className='mzT-ps'; ps.textContent='LE PROPHETE MOHAMED \uFDFA'; ph.appendChild(ps);
  var po=document.createElement('p'); po.className='mzT-po'; po.textContent='SOURCE DE LA REVELATION — MISSION INFAILLIBLE'; ph.appendChild(po);
  container.appendChild(ph);

  /* ════════ DATA LIGNEE — identique image ════════ */
  var L=[
    {lft:[{n:'MUHAMMAD IBN ISMAIL\nAL-BUKHARI',d:'m. 256H',r:'Imam, Mouhaddith, Fakih\nSahih Al-Bukhari',v:'THIQAH',vc:'T'}],ctr:{n:'AHMAD IBN\nHANBAL',d:'m. 241H',r:'Imam, Mouhaddith, Fakih\nImam, Thiqah',v:'THIQAH',nc:'#fde68a',bc:'rgba(251,191,36,.09)',bd:'rgba(251,191,36,.5)'},rgt:[]},
    {lft:[{n:"BARI'\nAL-MADKHALI",d:'m. 1min.',r:'Mouhaddith, Adil',v:'MUDALLIS',vc:'M'}],ctr:{n:'AN-NAWAWI',d:'m. 676H',r:'Imam\nMouhaddith, Adil',v:'ADIL',nc:'#d4af37',bc:'rgba(212,175,55,.08)',bd:'rgba(212,175,55,.42)'},rgt:[{n:'IBN HAJAR\nAL-ASQALANI',d:'n. 853H',r:'Hafidh\nMouhadditheen, Adil',v:'ADIL',vc:'A'}]},
    {lft:[{n:'IBN AL-QASIM',d:'m. Ant.',r:'Fakih\nMouhaddith',v:'ADIL',vc:'A'}],ctr:{n:'IBN AL-QAYYIM',d:'m. 751H',r:'Fakih\nMouhaddith, Adil',v:'ADIL',nc:'#d4af37',bc:'rgba(212,175,55,.08)',bd:'rgba(212,175,55,.42)'},rgt:[{n:'IBN HAJAR\nAL-ASQALANI',d:'m. 852H',r:'Hafidh\nMouhaddith, Thiqah',v:'THIQAH',vc:'T'}]},
    {lft:[{n:"RABI'\nAL-MADKHALI",d:'5h. Jarh',r:'Fakih, Mouhaddith\nAdil',v:'THIQAH',vc:'T'}],ctr:{n:'IBN HAJAR',d:'m. 852H',r:'Hafidh\nMouhaddith, Adil',v:'THIQAH',nc:'#93c5fd',bc:'rgba(96,165,250,.08)',bd:'rgba(96,165,250,.42)'},rgt:[{n:'IBN HAJAR\nAL-ASQALANI',d:'m. 852H',r:'Mouhaddith\nThiqah',v:'THIQAH',vc:'T'},{n:"RABI'\nAL-MADKHALI",d:'n. Fakih',r:'Prane\nMoohsodit, Adil',v:'MUDALLIS',vc:'M'}]},
    {lft:[{n:'IBN AL-SHENIN',d:'m. 65H',r:'Fakin\nMoncar',v:'MUDALLIS',vc:'M'}],ctr:{n:'IBN HAJAR\nAL-ASQALANI',d:'m. 852H',r:'Mouhaddith\nThiqah',v:'THIQAH',nc:'#93c5fd',bc:'rgba(96,165,250,.08)',bd:'rgba(96,165,250,.42)'},rgt:[{n:'AL-AL-QYIM',d:'m. 751H',r:'Fakih\nMohacash',v:'MUNKAR',vc:'M'}]},
    {lft:[{n:"RABI'\nAL-MADKHALI",d:'m. 1445H',r:'Mouhaddith, Adil',v:'THIQAH',vc:'T'}],ctr:{n:"RABI'\nAL-MADKHALI",d:'m. 1445H',r:'Mouhaddith, Adil',v:'THIQAH',nc:'#86efac',bc:'rgba(34,197,94,.09)',bd:'rgba(34,197,94,.45)'},rgt:[{n:"RABI'\nAL-MADKHALI",d:'m. 1445H',r:'Mouhaddith, Adil',v:'THIQAH',vc:'T'}]}
  ];

  function _vCls(v){return v==='THIQAH'||v==='THIQAH THABT'?'mzV-T':v==='MUDALLIS'||v==='MUNKAR'||v==='MODALLIS'?'mzV-M':'mzV-A';}
  function _vCol(vc){return vc==='T'?'#22c55e':vc==='M'?'#ef4444':'#d4af37';}

  function _mini(d,dl,cb){
    var col=_vCol(d.vc);
    var m=document.createElement('div'); m.className='mzT-mn'; m.style.cssText='border-color:'+col+'28;background:'+col+'09;animation-delay:'+dl; m.addEventListener('click',cb);
    var nm=document.createElement('span'); nm.className='mzT-mnn'; nm.style.color=col; nm.textContent=d.n; m.appendChild(nm);
    if(d.d){var dd=document.createElement('span');dd.className='mzT-mnd';dd.textContent='('+d.d+')';m.appendChild(dd);}
    if(d.r){var rr=document.createElement('span');rr.className='mzT-mnr';rr.textContent=d.r;m.appendChild(rr);}
    var vv=document.createElement('span'); vv.className='mzT-mnv '+_vCls(d.v); vv.textContent=d.v; m.appendChild(vv);
    return m;
  }

  function _card(d,dl,cb){
    var c=document.createElement('div'); c.className='mzT-crd'; c.style.cssText='border-color:'+d.bd+';background:'+d.bc+';animation-delay:'+dl; c.addEventListener('click',cb);
    var nm=document.createElement('p'); nm.className='mzT-cn'; nm.style.color=d.nc; nm.textContent=d.n; c.appendChild(nm);
    if(d.d){var dd=document.createElement('p');dd.className='mzT-cd';dd.textContent='('+d.d+')';c.appendChild(dd);}
    if(d.r){var rr=document.createElement('p');rr.className='mzT-cr';rr.textContent=d.r;c.appendChild(rr);}
    var vv=document.createElement('span'); vv.className='mzT-vd '+_vCls(d.v); vv.textContent=d.v; c.appendChild(vv);
    return c;
  }

  /* Tronc initial */
  var tk0=document.createElement('div'); tk0.className='mzT-tk'; tk0.style.height='20px'; container.appendChild(tk0);
  var bk0=document.createElement('span'); bk0.className='mzT-bk'; bk0.textContent='a transmis a'; container.appendChild(bk0);

  var delay=0;
  L.forEach(function(rang,ri){
    delay+=0.09;
    var row=document.createElement('div'); row.className='mzT-row';
    var colL=document.createElement('div'); colL.className='mzT-col';
    (rang.lft||[]).forEach(function(d,i){var dl=(delay+i*.06).toFixed(2)+'s'; var dn=d; colL.appendChild(_mini(dn,dl,function(){window.mzOpenIsnadPanel(dn.n,dn.r,dn.v,'',_vCol(dn.vc));}));});
    var brL=document.createElement('div'); brL.className='mzT-br mzT-brl'; brL.style.animationDelay=(delay+.05)+'s';
    var colC=document.createElement('div'); colC.className='mzT-col-c'; var cd=rang.ctr; var dl2=(delay+.1).toFixed(2)+'s';
    colC.appendChild(_card(cd,dl2,function(){window.mzOpenIsnadPanel(cd.n,cd.r,cd.v,'',cd.nc);}));
    var brR=document.createElement('div'); brR.className='mzT-br mzT-brr'; brR.style.animationDelay=(delay+.05)+'s';
    var colR=document.createElement('div'); colR.className='mzT-col';
    (rang.rgt||[]).forEach(function(d,i){var dl=(delay+i*.06+.04).toFixed(2)+'s'; var dn=d; colR.appendChild(_mini(dn,dl,function(){window.mzOpenIsnadPanel(dn.n,dn.r,dn.v,'',_vCol(dn.vc));}));});
    row.appendChild(colL); row.appendChild(brL); row.appendChild(colC); row.appendChild(brR); row.appendChild(colR);
    container.appendChild(row);
    if(ri<L.length-1){var tk=document.createElement('div');tk.className='mzT-tk';tk.style.height='18px';container.appendChild(tk); var bk=document.createElement('span');bk.className='mzT-bk';bk.textContent='ont transmis aux';container.appendChild(bk);}
    delay+=0.08;
  });

  /* Racines SVG */
  var rt=document.createElement('div'); rt.className='mzT-rt';
  var rs=document.createElementNS('http://www.w3.org/2000/svg','svg'); rs.setAttribute('viewBox','0 0 320 40'); rs.setAttribute('style','width:100%;height:40px;');
  ['M160 0 C140 10,110 22,80 35','M160 0 C160 12,160 25,160 40','M160 0 C180 10,210 22,240 35','M160 0 C130 14,95 28,65 40','M160 0 C190 14,225 28,255 40'].forEach(function(d,i){var p=document.createElementNS('http://www.w3.org/2000/svg','path');p.setAttribute('d',d);p.setAttribute('stroke','rgba(212,175,55,.18)');p.setAttribute('stroke-width','2.5');p.setAttribute('fill','none');p.style.animation='mzRootGlow 2.5s ease-in-out infinite';p.style.animationDelay=(i*.15)+'s';rs.appendChild(p);});
  rt.appendChild(rs); container.appendChild(rt);

  /* Pied */
  var ft=document.createElement('p'); ft.className='mzT-ft'; ft.textContent='SILSILAT AL-ISNAD — CHAINE DOREE ININTERROMPUE DE 14 SIECLES — EDIFICE ROYAL DE LA TRANSMISSION'; container.appendChild(ft);
}/* ══════════════════════════════════════════════════════════════
   window.mzRenderIsnadZone — API PUBLIQUE ZONE 2
   Point d'entrée unique appelé depuis l'enrichissement SSE
   Usage : window.mzRenderIsnadZone(targetElement, isnadChainString)
══════════════════════════════════════════════════════════════ */
window.mzRenderIsnadZone = function(targetEl, isnadChain) {
  window.mzInjectIsnadCSS();

  if (!targetEl) {
    console.warn('[v18.4] mzRenderIsnadZone : targetEl introuvable');
    return;
  }

  /* Vidage propre sans innerHTML */
  while (targetEl.firstChild) targetEl.removeChild(targetEl.firstChild);

  var nodes = _mzBuildNodes(isnadChain);

  /* Fallback — Bouclier Science : min-height:40px garanti */
  if (!nodes.length) {
    targetEl.id = 'mz-isnad-container';
    targetEl.style.cssText = 'min-height:40px;padding:14px 18px;text-align:center;';

    var fbLabel = document.createElement('p');
    fbLabel.style.cssText = [
      'font-family:Cinzel,serif;font-size:6.5px;letter-spacing:.25em;',
      'color:rgba(201,168,76,.35);margin-bottom:8px;z-index:10;position:relative;'
    ].join('');
    fbLabel.textContent = 'ZONE 2 — SILSILAT AL-ISNĀD';

    var fbMsg = document.createElement('p');
    fbMsg.style.cssText = [
      'font-family:Cormorant Garamond,serif;font-style:italic;',
      'font-size:13px;color:rgba(201,168,76,.35);line-height:1.7;'
    ].join('');
    fbMsg.textContent = 'Données de la chaîne non disponibles.';

    targetEl.appendChild(fbLabel);
    targetEl.appendChild(fbMsg);
    return;
  }

  _mzRenderZone2(targetEl, nodes);
};

/* ══════════════════════════════════════════════════════════════
   CONFIRMATION FINALE — Mouchard secondaire
══════════════════════════════════════════════════════════════ */
console.log('%c ✅ Mîzân v18.4 : window.goTo + nodeVis + parseSiecle + mzOpenIsnadPanel + mzRenderIsnadZone OK', 'color:#d4af37;font-weight:bold;');
