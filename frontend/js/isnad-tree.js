/* Arbre d'Isnād vertical — rendu DOM léger */

class IsnadTree {
  constructor(container) {
    this.container = container;
  }

  render(chain) {
    if (!chain || chain.length === 0) {
      this.container.innerHTML = '<p class="mz-empty">Pas de chaîne disponible</p>';
      return;
    }

    this.container.innerHTML = '';

    chain.forEach((narrator, idx) => {
      const node = document.createElement('div');
      node.className = 'isnad-node';

      const circle = document.createElement('div');
      circle.className = `isnad-node-circle verdict-${narrator.verdict || 'unknown'}`;
      circle.textContent = this._shortName(narrator.name_ar || '');
      node.appendChild(circle);

      const label = document.createElement('div');
      label.className = 'isnad-node-label';
      label.textContent = narrator.name_fr || '';
      if (narrator.death_h) label.textContent += ` (m. ${narrator.death_h}H)`;
      node.appendChild(label);

      this.container.appendChild(node);

      if (idx < chain.length - 1) {
        const connector = document.createElement('div');
        connector.className = 'isnad-connector';
        this.container.appendChild(connector);
      }
    });
  }

  _shortName(fullName) {
    if (!fullName) return '?';
    const parts = fullName.split(' ');
    if (parts.length <= 2) return fullName;
    return parts.slice(0, 2).join(' ');
  }

  clear() {
    this.container.innerHTML = '<p class="mz-empty">En attente de données...</p>';
  }
}

window.IsnadTree = IsnadTree;