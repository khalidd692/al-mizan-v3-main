/* ═══════════════════════════════════════════════════════════════════
   MÎZÂN v23.0 — rawi-modal.js — PANNEAU LATÉRAL BIOGRAPHIQUE
   Définit window.mzOpenIsnadPanel + window.mzCloseRawiPanel
   Chargé AVANT engine.js (defer)
═══════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';
  if (document.getElementById('mzRp-css')) return;

  /* ═══ CSS ═══ */
  var st = document.createElement('style');
  st.id = 'mzRp-css';
  st.textContent =
    '.mzRp-overlay{position:fixed;inset:0;background:rgba(0,0,0,.65);z-index:9998;opacity:0;pointer-events:none;transition:opacity .35s ease;-webkit-backdrop-filter:blur(2px);backdrop-filter:blur(2px)}'
  + '.mzRp-overlay.mzRp-open{opacity:1;pointer-events:auto}'
  + '.mzRp-panel{position:fixed;top:0;right:0;width:min(380px,88vw);height:100%;z-index:9999;overflow-y:auto;overscroll-behavior:contain;background:linear-gradient(175deg,#0a0600 0%,#0d0907 40%,#090d11 100%);border-left:1px solid rgba(201,168,76,.18);transform:translateX(100%);transition:transform .4s cubic-bezier(.22,1,.36,1);box-shadow:-12px 0 60px rgba(0,0,0,.7)}'
  + '.mzRp-panel.mzRp-open{transform:translateX(0)}'
  + '.mzRp-panel::-webkit-scrollbar{width:4px}'
  + '.mzRp-panel::-webkit-scrollbar-thumb{background:rgba(201,168,76,.18);border-radius:2px}'
  + '.mzRp-close{position:sticky;top:0;z-index:10;display:flex;justify-content:flex-end;padding:14px 16px 8px;background:linear-gradient(180deg,rgba(10,6,0,.97) 60%,transparent)}'
  + '.mzRp-close button{width:34px;height:34px;border-radius:50%;border:1px solid rgba(201,168,76,.22);background:rgba(201,168,76,.05);color:#c9a84c;font-size:18px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .25s;line-height:1}'
  + '.mzRp-close button:hover{background:rgba(201,168,76,.14);border-color:rgba(201,168,76,.5);transform:scale(1.08)}'
  + '.mzRp-hdr{padding:0 22px 18px;text-align:center;border-bottom:1px solid rgba(201,168,76,.08)}'
  + '.mzRp-name{font-family:"Scheherazade New",serif;font-size:24px;font-weight:700;line-height:1.35;margin-bottom:4px;direction:rtl}'
  + '.mzRp-role{font-family:Cinzel,serif;font-size:7.5px;letter-spacing:.2em;color:rgba(201,168,76,.42);text-transform:uppercase;margin-top:2px}'
  + '.mzRp-dates{font-family:"Cormorant Garamond",serif;font-size:13.5px;color:rgba(220,200,160,.45);font-style:italic;margin-top:5px}'
  + '.mzRp-verdict{display:inline-block;margin-top:12px;padding:5px 16px;border-radius:4px;font-family:Cinzel,serif;font-size:7.5px;font-weight:700;letter-spacing:.14em}'
  + '.mzRp-sec{padding:16px 22px}'
  + '.mzRp-sec-title{display:block;font-family:Cinzel,serif;font-size:6.5px;font-weight:700;letter-spacing:.22em;color:rgba(201,168,76,.38);text-transform:uppercase;margin-bottom:10px}'
  + '.mzRp-sec-body{font-family:"Cormorant Garamond",serif;font-size:14.5px;color:rgba(220,200,160,.7);line-height:1.85;font-style:italic}'
  + '.mzRp-sec-body strong{color:#d4af37;font-style:normal}'
  + '.mzRp-list{list-style:none;padding:0;margin:0}'
  + '.mzRp-list li{padding:7px 0;border-bottom:1px solid rgba(201,168,76,.05);font-family:"Scheherazade New",serif;font-size:15.5px;color:rgba(220,200,160,.62);direction:rtl;text-align:right;transition:color .2s}'
  + '.mzRp-list li:hover{color:rgba(220,200,160,.9)}'
  + '.mzRp-list li::before{content:"\u25c6";color:rgba(201,168,76,.25);margin-left:8px;font-size:6px;vertical-align:middle}'
  + '.mzRp-div{height:1px;margin:0;background:linear-gradient(90deg,transparent,rgba(201,168,76,.1),transparent)}'
  + '.mzRp-alert{padding:12px 14px;border-radius:6px;margin-top:10px;background:rgba(239,68,68,.04);border:1px solid rgba(239,68,68,.12)}'
  + '.mzRp-alert-title{font-family:Cinzel,serif;font-size:7px;font-weight:700;letter-spacing:.12em;color:#ef4444;margin-bottom:4px;display:block}'
  + '.mzRp-alert-body{font-family:"Cormorant Garamond",serif;font-size:12.5px;color:rgba(239,68,68,.6);line-height:1.65;font-style:italic}'
  + '@keyframes mzRpFade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}'
  + '.mzRp-sec{animation:mzRpFade .4s ease both}'
  + '.mzRp-sec:nth-child(2){animation-delay:.06s}'
  + '.mzRp-sec:nth-child(3){animation-delay:.12s}'
  + '.mzRp-sec:nth-child(4){animation-delay:.18s}'
  + '.mzRp-sec:nth-child(5){animation-delay:.24s}'
  + '.mzRp-sec:nth-child(6){animation-delay:.30s}'
  + '.mzRp-foot{font-family:Cinzel,serif;font-size:5.5px;letter-spacing:.2em;color:rgba(201,168,76,.14);text-align:center;padding:24px 0 32px}';
  document.head.appendChild(st);

  /* ═══ DOM ═══ */
  var overlay = document.createElement('div');
  overlay.id = 'mzRp-overlay';
  overlay.className = 'mzRp-overlay';
  document.body.appendChild(overlay);

  var panel = document.createElement('div');
  panel.id = 'mzRp-panel';
  panel.className = 'mzRp-panel';
  document.body.appendChild(panel);

  /* ═══ FERMETURE ═══ */
  function _close() {
    overlay.classList.remove('mzRp-open');
    panel.classList.remove('mzRp-open');
  }
  overlay.addEventListener('click', _close);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && panel.classList.contains('mzRp-open')) _close();
  });
  window.mzCloseRawiPanel = _close;

  /* ═══ VERDICT → COULEUR ═══ */
  function _vs(v) {
    var vl = (v || '').toLowerCase();
    if (/thiqah|\u062b\u0642\u0629|imam|\u0625\u0645\u0627\u0645|hujjah|thabt|hafidh/i.test(vl))
      return {bg:'rgba(34,197,94,.08)',c:'#22c55e',bd:'rgba(34,197,94,.22)'};
    if (/adil|\u0639\u062f\u0644|sahab|\u0635\u062d\u0627\u0628|sadouq|maqbul/i.test(vl))
      return {bg:'rgba(212,175,55,.08)',c:'#d4af37',bd:'rgba(212,175,55,.22)'};
    if (/kadhdhab|\u0643\u0630\u0627\u0628|matruk|\u0645\u062a\u0631\u0648\u0643|munkar|\u0645\u0646\u0643\u0631/i.test(vl))
      return {bg:'rgba(239,68,68,.08)',c:'#ef4444',bd:'rgba(239,68,68,.22)'};
    if (/da.if|\u0636\u0639\u064a\u0641|layyin|majhul|mudallis/i.test(vl))
      return {bg:'rgba(245,158,11,.08)',c:'#f59e0b',bd:'rgba(245,158,11,.22)'};
    return {bg:'rgba(201,168,76,.06)',c:'#c9a84c',bd:'rgba(201,168,76,.18)'};
  }

  /* ═══ OUVERTURE ═══ */
  function _open(name, role, verdict, dates, color, extra) {
    var ex = extra || {};
    var h = '';

    h += '<div class="mzRp-close"><button onclick="mzCloseRawiPanel()" aria-label="Fermer">\u00d7</button></div>';

    /* Header */
    h += '<div class="mzRp-hdr">';
    h += '<p class="mzRp-name" style="color:' + (color || '#e8d490') + ';">' + (name || '\u2014').replace(/\\n/g, '<br>') + '</p>';
    if (role) h += '<p class="mzRp-role">' + role.replace(/\\n/g, ' \u00b7 ') + '</p>';
    if (dates) h += '<p class="mzRp-dates">' + dates + '</p>';
    if (verdict) {
      var s = _vs(verdict);
      h += '<span class="mzRp-verdict" style="background:'+s.bg+';color:'+s.c+';border:1px solid '+s.bd+';">'+verdict+'</span>';
    }
    h += '</div><div class="mzRp-div"></div>';

    /* Bio Dhahabi / Ibn Hajar */
    if (ex.bio) {
      h += '<div class="mzRp-sec"><span class="mzRp-sec-title">CRITIQUE BIOGRAPHIQUE \u2014 DHAHABI / IBN HAJAR</span>';
      h += '<div class="mzRp-sec-body">' + ex.bio + '</div></div><div class="mzRp-div"></div>';
    }

    /* Verdict détaillé */
    if (verdict && verdict.length > 3) {
      h += '<div class="mzRp-sec"><span class="mzRp-sec-title">VERDICT \u2014 JARH WA TA\u2019DIL</span>';
      h += '<div class="mzRp-sec-body">' + verdict + '</div>';
      if (/kadhdhab|\u0643\u0630\u0627\u0628|matruk|\u0645\u062a\u0631\u0648\u0643|munkar|\u0645\u0646\u0643\u0631/i.test(verdict)) {
        h += '<div class="mzRp-alert"><span class="mzRp-alert-title">\u26a0 \u2018ILLAH \u2014 MAILLON ROMPU</span>';
        h += '<p class="mzRp-alert-body">al-Jar\u1e25 al-Mufassar muqaddam \u2018ala at-Ta\u2019d\u012bl \u2014 la critique argument\u00e9e pr\u00e9vaut.</p></div>';
      }
      h += '</div><div class="mzRp-div"></div>';
    }

    /* Mashayikh */
    if (ex.mashayikh && ex.mashayikh.length) {
      h += '<div class="mzRp-sec"><span class="mzRp-sec-title">MASH\u0100YIKH \u2014 SES PROFESSEURS</span><ul class="mzRp-list">';
      ex.mashayikh.forEach(function(m) {
        var n = typeof m === 'string' ? m : (m.name || '');
        if (n) h += '<li>' + n + '</li>';
      });
      h += '</ul></div><div class="mzRp-div"></div>';
    }

    /* Talamidh */
    if (ex.talamidh && ex.talamidh.length) {
      h += '<div class="mzRp-sec"><span class="mzRp-sec-title">TAL\u0100M\u012aDH \u2014 SES \u00c9L\u00c8VES</span><ul class="mzRp-list">';
      ex.talamidh.forEach(function(t) {
        var n = typeof t === 'string' ? t : (t.name || '');
        if (n) h += '<li>' + n + '</li>';
      });
      h += '</ul></div>';
    }

    h += '<p class="mzRp-foot">M\u00ceZ\u00c2N AS-SUNNAH \u2014 JARH WA TA\u2019DIL \u2014 MANHAJ SALAF</p>';

    panel.innerHTML = h;
    panel.scrollTop = 0;
    overlay.classList.add('mzRp-open');
    panel.classList.add('mzRp-open');
  }

  window.mzOpenIsnadPanel = _open;
  window.mzOpenRawiPanel  = _open;
})();
