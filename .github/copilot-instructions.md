Lire REGLES_SUPREMES.md en priorité avant toute action.

> ⚠️ RÈGLE SUPRÊME — PRIORITÉ ABSOLUE
> G est le seul décideur du projet. Si une règle de ce fichier bloque une tâche concrète, l'agent signale immédiatement : (1) quelle règle, (2) pourquoi, (3) proposition de modification. G valide ou refuse. Aucun blocage silencieux. Contrainte absolue unique : conformité manhaj Salaf as-Ṣāliḥ — al-Albānī, Ibn Bāz, Ibn ʿUthaymīn.

# ══════════════════════════════════════════════════════════════════

# COPILOT INSTRUCTIONS — AL-MĪZĀN v5.0

# Équivalent du .clauderules — Priorité absolue sur toute suggestion.

# Toute violation est un arrêt immédiat.

# ══════════════════════════════════════════════════════════════════

## IDENTITÉ DU PROJET

Al-Mīzān est une encyclopédie des sciences du Ḥadīth. C'est un instrument
d'**Amānah** (fidélité à la transmission). Il ne produit aucun avis personnel,
aucune traduction d'Attribut divin non conforme aux Salaf, aucun taʾwīl sans
preuve textuelle des trois premières générations.

Stack : Python 3.12 / Starlette + uvicorn / SQLite FTS5 / JavaScript vanilla.
Déploiement : Render (backend) + static frontend servi depuis `_REPO_ROOT`.

---

## 🔴 RÈGLE 0 — ZÉRO GÉNÉRATION DE CONTENU RELIGIEUX

**Copilot ne génère JAMAIS :**

- Un texte arabe de ḥadīth de sa propre initiative (fabrication = Waḍʿ)
- Une attribution de ḥadīth sans source primaire identifiée
- Une traduction d'Attribut divin par un sens figuré
- Un verdict de grade (Ṣaḥīḥ / Ḍaʿīf / Mawḍūʿ) sans citation d'Imām source
- Un taʾwīl ésotérique sans preuve explicite des Salaf
- Un avis personnel sur une question de Fiqh ou ʿAqīdah

**Si une tâche implique du contenu religieux : afficher les données existantes
en DB ou les citer depuis les fichiers du projet. Jamais inventer.**

---

## 🔴 RÈGLE 1 — DROIT DE VETO (DIFF OBLIGATOIRE)

Avant tout `git commit`, afficher obligatoirement :

- `git diff --stat` — liste exacte des fichiers modifiés
- `git diff` section `-` — résumé ligne par ligne des suppressions
- Attendre une validation explicite ("oui", "go", "valide")

**Aucune exception. Même pour un changement d'une seule ligne.**

---

## 🔴 RÈGLE 1 BIS — VERROU `_FRONTEND_DIR`

**Ne jamais modifier `_FRONTEND_DIR` dans `backend/main.py` sans validation
explicite de l'architecte.**

Le frontend est servi depuis `_REPO_ROOT` (racine du dépôt), pas depuis un
sous-dossier. Ligne de référence :

```python
_FRONTEND_DIR = _REPO_ROOT   # NE PAS CHANGER
```

---

## 🔴 RÈGLE 2 — LE SANCTUAIRE (Fichiers JS protégés)

**Interdiction formelle** de modifier les éléments suivants sans le mot-clé
**"DÉVERROU-SANCTUAIRE"** dans le message utilisateur :

### Fonctions protégées dans `engine.js`

- `_getTechnicalGrade` — logique de verdict hadith
- `_normalizeGrade` — normalisation des grades
- `_gradeColor` / `_gradeLabel` / `_mzVerdictCls` — affichage verdict
- `_RE_MAWDU` / `_RE_DAIF` / `_RE_SAHIH` — regex doctrinales
- `_SAHIH_WHITELIST` — liste de référence scientifique Al-Albani/Bukhari/Muslim

### Ordre immuable dans `_getTechnicalGrade()`

1. WHITELIST SAHIH (court-circuit prioritaire)
2. `_RE_MAWDU` → REJETÉ (rouge)
3. `_RE_DAIF` → DA'IF (orange)
4. `_RE_SAHIH` → SAHIH/HASAN (vert)
5. FALLBACK → DA'IF présumé (jamais de vert par défaut)

**Inverser cet ordre = falsification doctrinale. Interdit.**

### Fichiers de données — lecture seule sans DÉVERROU-SANCTUAIRE

- `data.js` — données hadith
- `db.js` — base de données JS
- `preachers.js` — prédicateurs
- `glossaire.js` — glossaire islamique
- `faq.js` — FAQ

---

## 🔴 RÈGLE 3 — VERROU DE SYNTAXE JS

Avant tout `git push`, vérification obligatoire :

```bash
node --check engine.js && node --check mizan-tree-engine.js && node --check app.js
```

Si `node --check` échoue → **push bloqué, corriger d'abord**.
S'applique à **tous** les fichiers `.js` touchés dans le commit.

---

## 🟠 RÈGLE 4 — ORDRE DE CHARGEMENT DES SCRIPTS (`index.html`)

L'ordre `defer` est une dépendance technique absolue — ne jamais modifier :

```
data.js → db.js → preachers.js → rawi-modal.js → mizan-tree-engine.js
→ engine.js → glossaire.js → faq.js → app.js
```

Modifier cet ordre = crash silencieux. Interdit sans test complet.

---

## 🟠 RÈGLE 5 — NAMESPACE GLOBAL `window.*` — FONCTIONS INTOUCHABLES

Ces fonctions sont appelées depuis les `onclick` HTML. Ne jamais renommer,
déplacer ou supprimer sans modifier `index.html` en même temps :

- `window.goTo` — navigation entre vues (position absolue N°1 dans `app.js`)
- `window.goToList` / `window.renderList` / `window.renderMythes`
- `window.omniSearch` — moteur de recherche global
- `window.parseSiecle` / `window.nodeVis`
- `window.mzRenderIsnadTree` / `window.mzChainFromDorarData`

---

## 🟠 RÈGLE 6 — GARDES CSS ANTI-DOUBLON (sacrées)

Ne jamais supprimer :

- `engine.js` : `if(document.getElementById('mizan-isnad-styles')) return;`
- `mizan-tree-engine.js` : `var old = document.getElementById('mz-tree-css'); if (old) old.remove();`

---

## 🟠 RÈGLE 7 — INTÉGRITÉ `_mzRegistry` ET TRI CHRONOLOGIQUE

Dans `mizan-tree-engine.js`, `mzRenderIsnadTree()` doit toujours :

1. Appeler `_mzRegistry.clear()` avant tout nouveau rendu
2. Conserver `containerEl._mzRafAbort` (annulation RAF)
3. `removeEventListener` avant d'en ajouter de nouveaux

Le tri `chain.sort((a, b) => a.death_year - b.death_year)` est obligatoire
dans `mzRenderIsnadTree()` ET `mzChainFromDorarData()`. Le supprimer inverse
l'ordre de la chaîne isnad — erreur scientifique grave.

---

## 🟠 RÈGLE 8 — ANTI-REFACTORING

Interdiction absolue de "nettoyer", "simplifier" ou "refactoriser" du code
qui n'est pas directement visé par la tâche en cours.

- Si une fonction n'est pas cassée → elle n'est pas touchée
- Interdit sans ordre explicite : fusionner des fonctions, remplacer `var` par
  `const`, extraire des helpers, réorganiser l'ordre des fonctions,
  supprimer des `console.log`

---

## 🟠 RÈGLE 9 — SERVICE WORKER (Cache Poisoning)

Toute modification de `index.html` doit s'accompagner d'un bump de la variable
`CACHE="almizan-vX-final"` (incrément du suffixe). Sans bump → les utilisateurs
mobiles voient l'ancienne version. Ne jamais cacher les appels API (`/api/*`).

---

## 🟠 RÈGLE 10 — DOM STALE APRÈS `innerHTML = ''`

Tout `setTimeout`/`Promise.then`/`requestAnimationFrame` ciblant `isnad-zone-X`,
`sanad-acc-X`, `sec-acc-X` doit commencer par :

```javascript
var el = document.getElementById(...); if (!el) return;
```

---

## 📁 ARCHITECTURE — RÈGLE 1 FICHIER = 1 AGENT

```
backend/
  main.py              — Point d'entrée Starlette (NE PAS FRAGMENTER)
  agents/
    agent_isnad.py     — Analyse chaîne de transmission
    agent_jarh.py      — Jarḥ wa Taʿdīl
    agent_matn.py      — Critique du matn
    agent_takhrij.py   — Takhrīj (sourçage)
    agent_tarjih.py    — Tarjīḥ (pondération)
    agent_ilal.py      — ʿIlal (causes cachées)
    agent_aqidah.py    — Filtre aqidal
    agent_validator.py — Validation finale
    agent_gharib.py    — Vocabulaire rare
    agent_fawaid.py    — Fawāʾid
    agent_conditions.py
    agent_advanced.py
  database/
    almizan_v7.db      — DB principale (SQLite FTS5)
  scripts/
    enrich_from_fawaz.py  — Enrichissement fawazahmed0 (UPDATE uniquement)
```

Chaque agent a sa propre responsabilité. Ne jamais fusionner deux agents.

---

## 🗄️ SCHÉMA DB — TABLE `entries` (almizan_v7.db)

Colonnes clés : `id`, `book_name_fr`, `hadith_number`, `ar_text`,
`ar_text_clean`, `fr_text`, `grade_primary`, `grade_albani`,
`sanad`, `matn`, `updated_at`.

FTS5 via `entries_fts` — recherche sur `ar_text_clean` et `fr_text`.
Requête type : `entries_fts MATCH "token1" AND "token2"`.

**Ne jamais DROP ou ALTER TABLE sans migration versionnée.**

---

## 📚 HIÉRARCHIE DES SOURCES ISLAMIQUES (Non négociable)

### Niveau 1 — Mutaqaddimūn (Iᵉʳ–IVᵉ siècle H.) — Juge ultime

Ṣaḥīḥayn (Bukhārī + Muslim) = VERROU ABSOLU.
Sunan canoniques : Abū Dāwūd, Tirmidhī, Nasāʾī, Ibn Mājah, Mālik.
ʿIlal : ad-Dāraquṭnī, Ibn Abī Ḥātim, Aḥmad, ʿAlī ibn al-Madīnī.
Rijāl : Ibn Maʿīn, Abū Ḥātim, Abū Zurʿah, al-Bukhārī (Tārīkh Kabīr).

### Niveau 2 — Khalaf (Vᵉ–XIIᵉ siècle H.) — Codification

Ibn Ḥajar (Fatḥ al-Bārī, Tahdhīb), adh-Dhahabī (Mīzān, Siyar), al-Mizzī
(Tahdhīb al-Kamāl), an-Nawawī (⚠️ réserve aqidale Attributs).

### Niveau 3 — Contemporains (XIIIᵉ–XVᵉ H.) — Audit conditionnel

Al-Albānī, Shuʿayb al-Arnaʾūṭ, etc. Leur verdict ne vaut QUE s'ils s'appuient
explicitement sur les Niveaux 1–2. Ils ne peuvent jamais renverser un
Mutaqaddim sans preuve textuelle nouvelle.

### Règle de conflit

Niveau 1 > Niveau 2 > Niveau 3. En cas de conflit :

1. Citer le verdict ancien avec source exacte (auteur + livre + tome/page)
2. Citer le verdict contemporain avec source exacte
3. Exposer si le contemporain apporte une preuve textuelle nouvelle
4. Trancher : sans preuve nouvelle → verdict ancien = `marjūḥ` du contemporain

---

## ⚠️ SAVANTS AVEC RÉSERVE AQIDALE

| Savant         | Usage permis         | Restriction                          |
| -------------- | -------------------- | ------------------------------------ |
| An-Nawawī      | Ḥadīth, Fiqh Shāfiʿī | ⚠️ Ashʿarite sur les Attributs       |
| Ibn Ḥajar      | Rijāl, Fatḥ al-Bārī  | ⚠️ Tafwīḍ ponctuel sur Attributs     |
| Az-Zamakhsharī | Lexique uniquement   | ❌ Jamais pour ʿAqīdah (Muʿtazilite) |
| Al-Ḥākim       | Source secondaire    | ⚠️ Mutasāhil — croiser avec Dhahabī  |
| Ibn Ḥibbān     | Rijāl avec prudence  | ⚠️ Mutasāhil dans tawthīq            |

---

## 🔵 API — CONTRATS SSE

Le backend expose des Server-Sent Events (SSE) sur `/api/search`.
Format événements :

- `event: zone` — payload JSON d'une zone de résultat
- `event: done` — fin du stream

Ne jamais cacher les appels `/api/*` dans le Service Worker.
Rate limit : 10 req/min par IP (`_rate_limiter` dans `main.py`).

---

## ✅ CHECKLIST AVANT TOUTE MODIFICATION JS

- [ ] `node --check <fichier.js>` passe
- [ ] L'ordre de `_getTechnicalGrade()` est préservé (MAWDU → DAIF → SAHIH)
- [ ] Les gardes CSS anti-doublon sont présentes
- [ ] Les fonctions `window.*` sont réassignées explicitement
- [ ] `_mzRegistry.clear()` présent dans `mzRenderIsnadTree()`
- [ ] Tri chronologique `death_year` présent
- [ ] `git diff --stat` présenté à l'architecte avant commit
