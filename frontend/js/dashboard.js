/* Dashboard Al-Mīzān — Orchestration UI */

(function() {
  'use strict';

  console.log('[Dashboard] Initialisation...');

  const form = document.getElementById('mz-search-form');
  console.log('[Dashboard] Form trouvé:', form);
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

  console.log('[Dashboard] IsnadTree:', typeof IsnadTree);
  console.log('[Dashboard] MizanSSEClient:', typeof MizanSSEClient);

  const tree = new IsnadTree(isnadContainer);
  const sse = new MizanSSEClient(onZone);

  console.log('[Dashboard] Instances créées');

  let zonesReceived = 0;
  const TOTAL_ZONES = 32;

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
    console.log('[Dashboard] Submit déclenché');
    const query = queryInput.value.trim();
    console.log('[Dashboard] Query:', query);
    if (!query) return;
    resetUI();
    setStatus('Recherche en cours...');
    setProgress(2);
    console.log('[Dashboard] Connexion SSE...');
    await sse.connect(query);
    setStatus('Terminé');
    setProgress(100);
  });

  console.log('[Dashboard] Event listener ajouté au formulaire');

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
    console.log(`[ZONE] ${event}`, data);
    zonesReceived++;
    setProgress(Math.min(95, (zonesReceived / TOTAL_ZONES) * 100));

    if (event === 'zone_1') setStatus('Initialisation');
    else if (event === 'zone_4') renderHadithCore(data.data);
    else if (event === 'zone_2') renderIsnad(data);
    else if (event === 'zone_32') setStatus('Terminé ✓');
    else if (event === 'error') setStatus('Erreur : ' + (data.message || 'inconnue'));
    else renderTabPanel(event.replace('zone_', ''), data);
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

  function renderTabPanel(tabName, data) {
    let panel = tabsContent.querySelector(`[data-panel="${tabName}"]`);
    if (!panel) {
      panel = document.createElement('div');
      panel.className = 'mz-tab-panel';
      panel.dataset.panel = tabName;
      tabsContent.appendChild(panel);
    }
    const content = document.createElement('div');
    content.innerHTML = `<pre style="font-size:11px;white-space:pre-wrap;color:var(--mz-text-dim);">${JSON.stringify(data, null, 2)}</pre>`;
    panel.appendChild(content);
    if (!tabsContent.querySelector('.mz-tab-panel.active')) panel.classList.add('active');
  }

})();