/* Dashboard Al-Mīzān — Orchestration UI */

(function() {
  'use strict';

  const form = document.getElementById('mz-search-form');
  const queryInput = document.getElementById('mz-query');
  const matnAr = document.getElementById('matn-arabic');
  const matnFr = document.getElementById('matn-french');
  const matnSources = document.getElementById('matn-sources');
  const verdictBanner = document.getElementById('matn-verdict');
  const tabsContent = document.getElementById('tabs-content');
  const tabs = document.querySelectorAll('.mz-tab');
  const statusText = document.getElementById('status-text');
  const progressBar = document.getElementById('progress-bar');
  const isnadContainer = document.getElementById('isnad-tree');

  const tree = new IsnadTree(isnadContainer);
  const sse = new MizanSSEClient(onZone);

  let zonesReceived = 0;
  const TOTAL_ZONES = 32;

  // Mapping zones → tabs selon Constitution v4
  const ZONE_TO_TAB = {
    'zone_2': 'isnad', 'zone_3': 'isnad', 'zone_5': 'isnad',
    'zone_6': 'ilal', 'zone_7': 'ilal', 'zone_8': 'ilal',
    'zone_9': 'gharib', 'zone_10': 'sabab', 'zone_11': 'shuruh',
    'zone_12': 'athar', 'zone_13': 'athar', 'zone_14': 'athar',
    'zone_15': 'ijma', 'zone_16': 'mukhtalif', 'zone_17': 'mukhtalif',
    'zone_18': 'naskh', 'zone_19': 'naskh',
    'zone_20': 'fawaid', 'zone_21': 'fawaid', 'zone_22': 'fawaid',
    'zone_23': 'aqidah', 'zone_24': 'aqidah', 'zone_25': 'aqidah',
    'zone_26': 'aqidah', 'zone_27': 'aqidah',
    'zone_28': 'tarjih', 'zone_29': 'tarjih',
  };

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      showTabPanel(tab.dataset.tab);
    });
  });

  function showTabPanel(tabName) {
    const panels = tabsContent.querySelectorAll('.mz-tab-panel');
    panels.forEach(p => p.classList.remove('active'));
    const target = tabsContent.querySelector(`[data-panel="${tabName}"]`);
    if (target) target.classList.add('active');
  }

  if (tabs.length > 0) tabs[0].click();

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = queryInput.value.trim();
    if (!query) return;
    resetUI();
    setStatus('Recherche en cours...');
    setProgress(2);
    await sse.connect(query);
    setStatus('Terminé');
    setProgress(100);
  });

  function resetUI() {
    matnAr.textContent = '';
    matnFr.textContent = '';
    matnSources.textContent = '';
    verdictBanner.textContent = '';
    verdictBanner.className = 'mz-verdict-banner';
    tree.clear();
    tabsContent.innerHTML = '';
    zonesReceived = 0;
  }

  function setStatus(txt) { statusText.textContent = txt; }
  function setProgress(pct) {
    progressBar.classList.add('active');
    progressBar.style.setProperty('--progress', `${pct}%`);
  }

  function onZone(event, data) {
    if (event.startsWith('meta_')) return;
    zonesReceived++;
    setProgress(Math.min(95, (zonesReceived / TOTAL_ZONES) * 100));

    if (event === 'zone_1') {
      setStatus('Initialisation');
    } else if (event === 'zone_4') {
      renderHadithCore(data.data);
    } else if (event === 'zone_2') {
      renderIsnad(data);
    } else if (event === 'zone_32') {
      setStatus('Terminé ✓');
    } else if (event === 'error') {
      setStatus('Erreur : ' + (data.message || 'inconnue'));
    } else {
      // Mapper zone_X → tab correspondant
      const tab = ZONE_TO_TAB[event];
      if (tab) {
        renderTabPanel(tab, event, data);
      }
    }
  }

  function renderHadithCore(data) {
    if (!data) return;
    matnAr.textContent = data.matn || '';
    matnFr.textContent = data.translation_fr || '';
    matnSources.textContent = data.source || '';
    const grade = (data.grade_raw || '').toLowerCase();
    verdictBanner.className = 'mz-verdict-banner';
    if (grade.includes('صحيح')) verdictBanner.classList.add('sahih');
    verdictBanner.textContent = data.grade_raw || 'En cours...';
  }

  function renderIsnad(data) {
    if (data && data.chain) tree.render(data.chain);
  }

  function renderTabPanel(tabName, zoneId, data) {
    let panel = tabsContent.querySelector(`[data-panel="${tabName}"]`);
    if (!panel) {
      panel = document.createElement('div');
      panel.className = 'mz-tab-panel';
      panel.dataset.panel = tabName;
      tabsContent.appendChild(panel);
    }

    // Déduplique : supprime le bloc existant pour cette zone avant d'en injecter un nouveau
    const existing = panel.querySelector(`[data-zone="${zoneId}"]`);
    if (existing) existing.remove();

    const content = document.createElement('div');
    content.dataset.zone = zoneId;

    // Rendu spécial pour les zones en tawaqquf
    if (data && data.tawaqquf === true) {
      const typeLabel = getZoneTypeLabel(data.type);
      content.className = 'mz-tawaqquf-block';
      const h3 = document.createElement('div');
      h3.style.cssText = 'padding:20px;text-align:center;color:var(--mz-text-dim)';
      const title = document.createElement('h3');
      title.style.cssText = "font-family:'Scheherazade New',serif;font-size:18px;margin-bottom:10px;color:var(--mz-gold)";
      title.textContent = typeLabel;
      const badge = document.createElement('div');
      badge.style.cssText = 'display:inline-block;padding:6px 12px;background:#444;border-radius:4px;font-size:12px;color:#aaa';
      badge.textContent = 'En attente du corpus';
      h3.appendChild(title);
      h3.appendChild(badge);
      content.appendChild(h3);
    } else {
      // Rendu JSON standard pour les autres zones (textContent évite toute injection XSS)
      const pre = document.createElement('pre');
      pre.style.cssText = 'font-size:11px;white-space:pre-wrap;color:var(--mz-text-dim)';
      pre.textContent = JSON.stringify(data, null, 2);
      content.appendChild(pre);
    }

    panel.appendChild(content);
    if (!tabsContent.querySelector('.mz-tab-panel.active')) panel.classList.add('active');
  }
  
  function getZoneTypeLabel(type) {
    const labels = {
      'isnad_5_conditions': 'شروط الإسناد الخمسة',
      'shuruh': 'الشروح',
      'naskh': 'النسخ والمنسوخ',
      'takhrij_mawsuu': 'التخريج الموسع',
      'fawaid_fiqhiyyah': 'الفوائد الفقهية',
      'fawaid_aqadiyyah': 'الفوائد العقدية',
      'fawaid_tarbiyyah': 'الفوائد التربوية',
      'mawduu_alerte': 'تنبيه الموضوع',
      'aqidah_attribut': 'صفات الله',
      'dhahir_muqtada': 'الظاهر والمقتضى',
      'corroboration_coranique': 'المطابقة القرآنية',
      'khulafa_rashidun': 'عمل الخلفاء الراشدين'
    };
    return labels[type] || type.toUpperCase();
  }

})();