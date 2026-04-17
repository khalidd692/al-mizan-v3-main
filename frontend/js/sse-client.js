/* Client SSE Al-Mīzān — Consommateur fiable avec reconnexion */

class MizanSSEClient {
  constructor(onEvent) {
    this.onEvent = onEvent;
    this.controller = null;
    this.connected = false;
  }

  async connect(query) {
    this.disconnect();
    this.controller = new AbortController();
    this.connected = true;

    try {
      const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`, {
        method: 'GET',
        headers: { 'Accept': 'text/event-stream', 'Cache-Control': 'no-cache' },
        signal: this.controller.signal,
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n');
        buffer = events.pop();

        for (const raw of events) {
          const parsed = this._parseSSE(raw);
          if (parsed) this.onEvent(parsed.event, parsed.data);
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('[SSE]', err);
        this.onEvent('error', { message: err.message });
      }
    } finally {
      this.connected = false;
    }
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