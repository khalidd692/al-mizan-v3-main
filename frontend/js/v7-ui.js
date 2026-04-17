/* AL-MĪZĀN V7.0 — Composants UI */

(function(window) {
  'use strict';

  // ============================================================
  // ZONES V7.0 — Définition complète des 32 zones
  // ============================================================
  
  const ZONES_V7 = [
    { id: 1, ar: 'الإسناد', fr: 'Isnad (Chaîne)', category: 'isnad' },
    { id: 2, ar: 'المتن', fr: 'Matn (Corps)', category: 'isnad' },
    { id: 3, ar: 'الترجيح', fr: 'Tarjîh (Prépondérance)', category: 'isnad' },
    { id: 4, ar: 'التخريج', fr: 'Takhrîj (Attribution)', category: 'isnad' },
    { id: 5, ar: 'العلل', fr: '\'Ilal (Défauts cachés)', category: 'isnad' },
    { id: 6, ar: 'الشروح', fr: 'Shurûh (Commentaires)', category: 'isnad' },
    { id: 7, ar: 'النسخ', fr: 'Naskh (Abrogation)', category: 'isnad' },
    { id: 8, ar: 'مختلف الحديث', fr: 'Mukhtalif al-Hadith', category: 'isnad' },
    { id: 9, ar: 'القواعد', fr: 'Qawâ\'id (Règles)', category: 'isnad' },
    { id: 10, ar: 'علم الرجال', fr: 'Rijal (Biographies)', category: 'isnad' },
    
    { id: 11, ar: 'الحكم العام', fr: 'Grading global', category: 'grading' },
    { id: 12, ar: 'صحيح', fr: 'Sahîh', category: 'grading' },
    { id: 13, ar: 'حسن', fr: 'Hasan', category: 'grading' },
    { id: 14, ar: 'ضعيف', fr: 'Da\'îf', category: 'grading' },
    { id: 15, ar: 'موضوع', fr: 'Mawdû\' (forgé)', category: 'grading' },
    { id: 16, ar: 'متواتر', fr: 'Mutawâtir', category: 'grading' },
    { id: 17, ar: 'آحاد', fr: 'Âhâd', category: 'grading' },
    { id: 18, ar: 'المرسل / المنقطع', fr: 'Mursal / Munqati\'', category: 'grading' },
    { id: 19, ar: 'مسند أحمد', fr: 'Musnad Ahmad', category: 'grading' },
    { id: 20, ar: 'سلسلة الألباني', fr: 'Silsilah Al-Albânî', category: 'grading' },
    
    { id: 21, ar: 'العقيدة', fr: 'Aqîdah (Croyance)', category: 'thematic' },
    { id: 22, ar: 'فقه العبادات', fr: 'Fiqh al-\'Ibâdât', category: 'thematic' },
    { id: 23, ar: 'المعاملات', fr: 'Mu\'âmalât', category: 'thematic' },
    { id: 24, ar: 'الحديث القدسي', fr: 'Hadith Qudsî', category: 'thematic' },
    { id: 25, ar: 'آثار الصحابة', fr: 'Âthâr as-Sahâbah', category: 'thematic' },
    { id: 26, ar: 'النواهي', fr: 'Nawâhî (Interdictions)', category: 'thematic' },
    { id: 27, ar: 'الفضائل', fr: 'Fadâ\'il (Vertus)', category: 'thematic' },
    { id: 28, ar: 'الذكر والدعاء', fr: 'Dhikr et Du\'â\'', category: 'thematic' },
    { id: 29, ar: 'الزهد والرقائق', fr: 'Zuhd et Raqâ\'iq', category: 'thematic' },
    { id: 30, ar: 'الفتاوى السلفية', fr: 'Fatâwâ Salafiyyah', category: 'thematic' },
    { id: 31, ar: 'المناقب والسيرة', fr: 'Manâqib et Sîrah', category: 'thematic' },
    { id: 32, ar: 'الحديث الموضوع', fr: 'Hadith Fabricado', category: 'thematic' }
  ];

  // ============================================================
  // MUHADDITHÎN — Liste des savants du hadith
  // ============================================================
  
  const MUHADDITHUN = [
    { id: 256, name_ar: 'البخاري', name_fr: 'Al-Bukhârî', dorar_id: 256 },
    { id: 261, name_ar: 'مسلم', name_fr: 'Muslim', dorar_id: 261 },
    { id: 275, name_ar: 'أبو داود', name_fr: 'Abû Dâwûd', dorar_id: 275 },
    { id: 279, name_ar: 'الترمذي', name_fr: 'At-Tirmidhî', dorar_id: 279 },
    { id: 303, name_ar: 'النسائي', name_fr: 'An-Nasâ\'î', dorar_id: 303 },
    { id: 273, name_ar: 'ابن ماجه', name_fr: 'Ibn Mâjah', dorar_id: 273 },
    { id: 179, name_ar: 'مالك', name_fr: 'Mâlik', dorar_id: 179 },
    { id: 241, name_ar: 'أحمد', name_fr: 'Ahmad ibn Hanbal', dorar_id: 241 },
    { id: 'albani', name_ar: 'الألباني', name_fr: 'Al-Albânî', dorar_id: null },
    { id: 'ibn_baz', name_ar: 'ابن باز', name_fr: 'Ibn Bâz', dorar_id: null },
    { id: 'ibn_uthaymin', name_ar: 'ابن عثيمين', name_fr: 'Ibn \'Uthaymîn', dorar_id: null },
    { id: 'muqbil', name_ar: 'مقبل', name_fr: 'Muqbil ibn Hâdî', dorar_id: null }
  ];

  // ============================================================
  // COMPOSANT : Badge Source
  // ============================================================
  
  function createSourceBadge(source) {
    const badge = document.createElement('span');
    badge.className = `mz-source-badge ${source}`;
    
    const labels = {
      'fawazahmed0': 'Traduit (fawazahmed0)',
      'hadeethenc': 'HadeethEnc',
      'dorar': 'Dorar',
      'manual': 'Manuel',
      'unknown': 'Source inconnue'
    };
    
    badge.textContent = labels[source] || labels.unknown;
    return badge;
  }

  // ============================================================
  // COMPOSANT : Bouton "Voir la source"
  // ============================================================
  
  function createSourceLink(url) {
    if (!url) return null;
    
    const link = document.createElement('a');
    link.className = 'mz-source-link';
    link.href = url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = 'Voir la source primaire';
    
    return link;
  }

  // ============================================================
  // COMPOSANT : Accordion Explication
  // ============================================================
  
  function createExplanationAccordion(explanation, source) {
    if (!explanation) return null;
    
    const accordion = document.createElement('div');
    accordion.className = 'mz-explanation-accordion';
    
    const header = document.createElement('div');
    header.className = 'mz-explanation-header';
    
    const title = document.createElement('h3');
    title.className = 'mz-explanation-title';
    title.textContent = 'شرح الحديث — Explication savante';
    
    const toggle = document.createElement('span');
    toggle.className = 'mz-explanation-toggle';
    toggle.textContent = '▼';
    
    header.appendChild(title);
    header.appendChild(toggle);
    
    const content = document.createElement('div');
    content.className = 'mz-explanation-content';
    
    const body = document.createElement('div');
    body.className = 'mz-explanation-body';
    body.textContent = explanation;
    
    content.appendChild(body);
    
    // Attribution HadeethEnc si nécessaire
    if (source === 'hadeethenc') {
      const attribution = document.createElement('div');
      attribution.className = 'mz-attribution';
      attribution.innerHTML = 'Traduction et explication : <a href="https://hadeethenc.com" target="_blank">HadeethEnc.com</a>';
      content.appendChild(attribution);
    }
    
    accordion.appendChild(header);
    accordion.appendChild(content);
    
    // Toggle accordion
    header.addEventListener('click', () => {
      accordion.classList.toggle('open');
    });
    
    return accordion;
  }

  // ============================================================
  // COMPOSANT : Navigation 32 zones
  // ============================================================
  
  function createZonesNavigation(onZoneClick) {
    const nav = document.createElement('div');
    nav.className = 'mz-zones-nav';
    
    ZONES_V7.forEach(zone => {
      const card = document.createElement('div');
      card.className = 'mz-zone-card';
      card.dataset.zoneId = zone.id;
      
      const number = document.createElement('div');
      number.className = 'mz-zone-number';
      number.textContent = `Zone ${zone.id}`;
      
      const nameAr = document.createElement('div');
      nameAr.className = 'mz-zone-name-ar';
      nameAr.textContent = zone.ar;
      
      const nameFr = document.createElement('div');
      nameFr.className = 'mz-zone-name-fr';
      nameFr.textContent = zone.fr;
      
      card.appendChild(number);
      card.appendChild(nameAr);
      card.appendChild(nameFr);
      
      card.addEventListener('click', () => {
        nav.querySelectorAll('.mz-zone-card').forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        if (onZoneClick) onZoneClick(zone);
      });
      
      nav.appendChild(card);
    });
    
    return nav;
  }

  // ============================================================
  // COMPOSANT : Filtre Muhaddithîn
  // ============================================================
  
  function createMuhaddithFilter(onFilterChange) {
    const filter = document.createElement('div');
    filter.className = 'mz-muhaddith-filter';
    
    const selectedMuhaddithun = new Set();
    
    MUHADDITHUN.forEach(muhaddith => {
      const chip = document.createElement('div');
      chip.className = 'mz-muhaddith-chip';
      chip.dataset.muhaddithId = muhaddith.id;
      chip.textContent = muhaddith.name_ar;
      chip.title = muhaddith.name_fr;
      
      chip.addEventListener('click', () => {
        chip.classList.toggle('active');
        
        if (chip.classList.contains('active')) {
          selectedMuhaddithun.add(muhaddith.id);
        } else {
          selectedMuhaddithun.delete(muhaddith.id);
        }
        
        if (onFilterChange) {
          onFilterChange(Array.from(selectedMuhaddithun));
        }
      });
      
      filter.appendChild(chip);
    });
    
    return filter;
  }

  // ============================================================
  // COMPOSANT : Grading multi-savants
  // ============================================================
  
  function createGradingPanel(grades) {
    const panel = document.createElement('div');
    panel.className = 'mz-grading-panel';
    
    const scholars = [
      { key: 'grade_primary', label: 'Grade principal' },
      { key: 'grade_albani', label: 'الألباني (Al-Albânî)' },
      { key: 'grade_ibn_baz', label: 'ابن باز (Ibn Bâz)' },
      { key: 'grade_ibn_uthaymin', label: 'ابن عثيمين (Ibn \'Uthaymîn)' },
      { key: 'grade_muqbil', label: 'مقبل (Muqbil)' }
    ];
    
    scholars.forEach(scholar => {
      const grade = grades[scholar.key];
      if (!grade) return;
      
      const card = document.createElement('div');
      card.className = 'mz-grade-card';
      
      const scholarName = document.createElement('div');
      scholarName.className = 'mz-grade-scholar';
      scholarName.textContent = scholar.label;
      
      const gradeValue = document.createElement('div');
      gradeValue.className = 'mz-grade-value';
      gradeValue.textContent = grade;
      
      // Ajouter classe de couleur selon le grade
      const gradeLower = grade.toLowerCase();
      if (gradeLower.includes('صحيح') || gradeLower.includes('sahih')) {
        gradeValue.classList.add('sahih');
      } else if (gradeLower.includes('حسن') || gradeLower.includes('hasan')) {
        gradeValue.classList.add('hasan');
      } else if (gradeLower.includes('ضعيف') || gradeLower.includes('daif')) {
        gradeValue.classList.add('daif');
      } else if (gradeLower.includes('موضوع') || gradeLower.includes('mawdu')) {
        gradeValue.classList.add('mawdu');
      }
      
      card.appendChild(scholarName);
      card.appendChild(gradeValue);
      panel.appendChild(card);
    });
    
    return panel;
  }

  // ============================================================
  // COMPOSANT : Analyse Sanad (5 conditions)
  // ============================================================
  
  function createSanadAnalysis(sanad) {
    const analysis = document.createElement('div');
    analysis.className = 'mz-sanad-analysis';
    
    const conditions = [
      { key: 'sanad_ittissal', label: 'الاتصال\nContinuité' },
      { key: 'sanad_adalah', label: 'العدالة\nProbité' },
      { key: 'sanad_dabt', label: 'الضبط\nExactitude' },
      { key: 'sanad_shudhudh', label: 'عدم الشذوذ\nSans anomalie' },
      { key: 'sanad_illa', label: 'عدم العلة\nSans défaut' }
    ];
    
    conditions.forEach(condition => {
      const value = sanad[condition.key];
      
      const conditionDiv = document.createElement('div');
      conditionDiv.className = 'mz-sanad-condition';
      
      const icon = document.createElement('div');
      icon.className = 'mz-sanad-icon';
      
      if (value === 1) {
        icon.textContent = '✓';
        icon.classList.add('ok');
      } else if (value === 0) {
        icon.textContent = '✗';
        icon.classList.add('fail');
      } else {
        icon.textContent = '?';
        icon.classList.add('unknown');
      }
      
      const label = document.createElement('div');
      label.className = 'mz-sanad-label';
      label.textContent = condition.label;
      
      conditionDiv.appendChild(icon);
      conditionDiv.appendChild(label);
      analysis.appendChild(conditionDiv);
    });
    
    return analysis;
  }

  // ============================================================
  // EXPORT
  // ============================================================
  
  window.MizanV7UI = {
    ZONES_V7,
    MUHADDITHUN,
    createSourceBadge,
    createSourceLink,
    createExplanationAccordion,
    createZonesNavigation,
    createMuhaddithFilter,
    createGradingPanel,
    createSanadAnalysis
  };

})(window);