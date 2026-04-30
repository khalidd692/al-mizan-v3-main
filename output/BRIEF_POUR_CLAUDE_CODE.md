# Brief pour Claude Code — Diagnostic Zones SSE

## Situation actuelle

L'utilisateur a signalé que `document.querySelectorAll('[class*="zone"]').length = 0` dans F12, malgré le fait que :

- Le backend envoie bien les zones via SSE
- Le frontend reçoit bien les événements SSE

## Ce que j'ai trouvé (diagnostic dashboard.js)

**Fichier** : `frontend/js/dashboard.js`

### Fonction d'écoute SSE

- `onSearchEvent(e)` — lignes 116–174
- Elle route les zones vers `renderTabPanel(tab, event, data)` via la table `ZONE_TO_TAB`

### Fonction de création DOM

- `renderTabPanel(tabName, zoneId, data)` — lignes 191–235
- Elle crée bien un `<div>` pour chaque zone et l'injecte dans le DOM

### Le "bug"

Les éléments zone sont créés **sans classe CSS** :

```javascript
// Ligne 204-205 — PAS DE className ASSIGNÉ
const content = document.createElement("div");
content.dataset.zone = zoneId; // ← seul data-zone existe
```

**Résultat** :

- `document.querySelectorAll('[class*="zone"]').length` → **0** ❌
- `document.querySelectorAll('[data-zone]').length` → **> 0** ✅

**Conclusion** : les zones existent dans le DOM. Le sélecteur F12 utilisé par l'utilisateur cherchait une classe CSS, mais les zones n'en ont pas — elles ont uniquement l'attribut `data-zone="zone_X"`.

## Rapport complet

Voir `output/RAPPORT_DIAGNOSTIC_ZONES_SSE.md` pour le détail complet avec extraits de code.

## Backend

Redémarré et opérationnel sur `http://localhost:8000` (health check OK).

## Ce qui reste à décider

L'utilisateur n'a pas encore choisi s'il faut :

- **Option A** : Ajouter `content.className = "mz-zone"` dans `renderTabPanel()` (ligne 205)
- **Option B** : Garder le fonctionnement actuel (les zones existent, juste sans classe CSS)

Aucune modification n'a été apportée au code source à ce stade.
