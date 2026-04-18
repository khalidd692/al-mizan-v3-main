/* Gestionnaire de Cache LocalStorage pour Al-Mīzān */

class MizanCacheManager {
  constructor() {
    this.CACHE_PREFIX = 'mizan:cache:v1:';
    this.CACHE_EXPIRY = 24 * 60 * 60 * 1000; // 24 heures
  }

  /**
   * Génère une clé de cache normalisée
   */
  _getCacheKey(query) {
    return this.CACHE_PREFIX + query.toLowerCase().trim();
  }

  /**
   * Récupère une réponse du cache
   */
  get(query) {
    try {
      const key = this._getCacheKey(query);
      const cached = localStorage.getItem(key);
      
      if (!cached) return null;
      
      const data = JSON.parse(cached);
      
      // Vérifier l'expiration
      if (Date.now() - data.timestamp > this.CACHE_EXPIRY) {
        localStorage.removeItem(key);
        return null;
      }
      
      return data.result;
    } catch (err) {
      console.warn('[CACHE] Erreur de lecture:', err);
      return null;
    }
  }

  /**
   * Stocke une réponse dans le cache
   */
  set(query, result) {
    try {
      const key = this._getCacheKey(query);
      const data = {
        timestamp: Date.now(),
        query: query,
        result: result
      };
      
      localStorage.setItem(key, JSON.stringify(data));
      return true;
    } catch (err) {
      console.warn('[CACHE] Erreur d\'écriture:', err);
      // Quota dépassé ? Nettoyer le cache
      if (err.name === 'QuotaExceededError') {
        this.clear();
      }
      return false;
    }
  }

  /**
   * Vérifie si une requête est en cache
   */
  has(query) {
    return this.get(query) !== null;
  }

  /**
   * Supprime une entrée du cache
   */
  remove(query) {
    try {
      const key = this._getCacheKey(query);
      localStorage.removeItem(key);
      return true;
    } catch (err) {
      console.warn('[CACHE] Erreur de suppression:', err);
      return false;
    }
  }

  /**
   * Vide tout le cache Al-Mīzān
   */
  clear() {
    try {
      const keys = Object.keys(localStorage);
      let count = 0;
      
      for (const key of keys) {
        if (key.startsWith(this.CACHE_PREFIX)) {
          localStorage.removeItem(key);
          count++;
        }
      }
      
      console.log(`[CACHE] ${count} entrées supprimées`);
      return count;
    } catch (err) {
      console.warn('[CACHE] Erreur de nettoyage:', err);
      return 0;
    }
  }

  /**
   * Nettoie les entrées expirées
   */
  cleanup() {
    try {
      const keys = Object.keys(localStorage);
      let count = 0;
      const now = Date.now();
      
      for (const key of keys) {
        if (key.startsWith(this.CACHE_PREFIX)) {
          try {
            const data = JSON.parse(localStorage.getItem(key));
            if (now - data.timestamp > this.CACHE_EXPIRY) {
              localStorage.removeItem(key);
              count++;
            }
          } catch {
            // Entrée corrompue, la supprimer
            localStorage.removeItem(key);
            count++;
          }
        }
      }
      
      if (count > 0) {
        console.log(`[CACHE] ${count} entrées expirées nettoyées`);
      }
      return count;
    } catch (err) {
      console.warn('[CACHE] Erreur de nettoyage:', err);
      return 0;
    }
  }

  /**
   * Obtient des statistiques sur le cache
   */
  getStats() {
    try {
      const keys = Object.keys(localStorage);
      let count = 0;
      let totalSize = 0;
      
      for (const key of keys) {
        if (key.startsWith(this.CACHE_PREFIX)) {
          count++;
          const value = localStorage.getItem(key);
          totalSize += key.length + (value ? value.length : 0);
        }
      }
      
      return {
        entries: count,
        sizeBytes: totalSize,
        sizeKB: (totalSize / 1024).toFixed(2)
      };
    } catch (err) {
      console.warn('[CACHE] Erreur de stats:', err);
      return { entries: 0, sizeBytes: 0, sizeKB: '0' };
    }
  }
}

// Utilitaires de throttle et debounce
class MizanUtils {
  /**
   * Throttle - Limite l'exécution à une fois par période
   */
  static throttle(func, delay) {
    let lastCall = 0;
    let timeoutId = null;
    
    return function(...args) {
      const now = Date.now();
      const timeSinceLastCall = now - lastCall;
      
      if (timeSinceLastCall >= delay) {
        lastCall = now;
        func.apply(this, args);
      } else {
        // Planifier l'exécution à la fin de la période
        if (timeoutId) clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
          lastCall = Date.now();
          func.apply(this, args);
        }, delay - timeSinceLastCall);
      }
    };
  }

  /**
   * Debounce - Attend que l'utilisateur arrête d'agir
   */
  static debounce(func, delay) {
    let timeoutId = null;
    
    return function(...args) {
      if (timeoutId) clearTimeout(timeoutId);
      
      timeoutId = setTimeout(() => {
        func.apply(this, args);
      }, delay);
    };
  }
}

// Export global
window.MizanCacheManager = MizanCacheManager;
window.MizanUtils = MizanUtils;