/* Client SSE Al-Mīzān — Consommateur fiable avec reconnexion */

class MizanSSEClient {
  constructor(onEvent, options = {}) {
    this.onEvent = onEvent;
    this.controller = null;
    this.connected = false;
    this.cache = options.cache || null;
    this.demoMode = options.demoMode !== false; // Activé par défaut
  }

  async connect(query) {
    this.disconnect();
    
    // Vérifier le cache d'abord
    if (this.cache) {
      const cached = this.cache.get(query);
      if (cached) {
        console.log('[SSE] Réponse depuis le cache');
        // Simuler les événements depuis le cache
        setTimeout(() => this._replayFromCache(cached), 0);
        return;
      }
    }
    
    this.controller = new AbortController();
    this.connected = true;

    try {
      const headers = {
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache'
      };
      
      // Ajouter le header de mode démo
      if (this.demoMode) {
        headers['X-Mizan-Demo'] = 'true';
      }
      
      const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`, {
        method: 'GET',
        headers: headers,
        signal: this.controller.signal,
      });

      if (!response.ok) {
        if (response.status === 429) {
          throw new Error('Rate limit dépassé. Veuillez patienter.');
        }
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let allEvents = []; // Pour le cache

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n');
        buffer = events.pop();

        for (const raw of events) {
          const parsed = this._parseSSE(raw);
          if (parsed) {
            this.onEvent(parsed.event, parsed.data);
            allEvents.push(parsed);
          }
        }
      }
      
      // Sauvegarder dans le cache si disponible
      if (this.cache && allEvents.length > 0) {
        this.cache.set(query, allEvents);
        console.log('[SSE] Réponse mise en cache');
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('[SSE]', err);
        this.onEvent('error', { message: err.message, code: 'CONNECTION_ERROR' });
      }
    } finally {
      this.connected = false;
    }
  }
  
  /**
   * Rejoue les événements depuis le cache
   */
  _replayFromCache(events) {
    let index = 0;
    const replay = () => {
      if (index < events.length) {
        const event = events[index];
        this.onEvent(event.event, event.data);
        index++;
        // Simuler un délai pour l'animation
        setTimeout(replay, 50);
      }
    };
    replay();
  }

  _parseSSE(block) {
    const trimmed = block.trim();
    if (!trimmed || trimmed.startsWith(':')) return null;

    let event = 'message';
    let data = '';

    for (const line of trimmed.split('\n')) {
      const clean = line.trim();
      if (clean.startsWith('event:')) event = clean.substring(6).trim();
      else if (clean.startsWith('data:')) {
        const frag = clean.substring(5).trim();
        data = data ? data + '\n' + frag : frag;
      }
    }

    if (!data) return null;
    try { return { event, data: JSON.parse(data) }; }
    catch { return { event, data: { raw: data } }; }
  }

  disconnect() {
    if (this.controller) {
      this.controller.abort();
      this.controller = null;
    }
    this.connected = false;
  }
}

window.MizanSSEClient = MizanSSEClient;