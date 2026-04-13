# ميزان السنة — Mîzân as-Sunnah

**La Balance de Précision pour la Vérification des Narrations Prophétiques**

Application web de Takhrîj (vérification) des hadiths selon la méthodologie des Salaf as-Sâlih. Le moteur interroge l'API Dorar.net puis soumet chaque narration à une analyse IA structurée couvrant 14 siècles de science du Hadith.

> *« Cette science est la religion — faites attention à qui vous prenez votre religion. »*
> — Muhammad ibn Sîrîne (m. 110H)

---

## Architecture

```
mizannnnew/
├── index.html              ← Frontend intégral (11 000+ lignes)
├── api/
│   ├── search.js           ← Moteur principal — Takhrîj 9 champs
│   ├── dorar.js            ← Proxy Dorar.net
│   └── translate.js        ← Traduction FR → AR
├── server.js               ← Serveur local (Railway / dev) — IGNORÉ par Vercel
├── package.json            ← CommonJS strict — ZÉRO "type": "module"
├── vercel.json             ← Configuration Serverless Functions
└── .vercelignore           ← Exclut server.js du build Vercel
```

---

## 📚 Pilier 1 — La Science (Manhaj des Salaf et 14 Siècles d'Héritage)

### Continuité Absolue

Il est **formellement interdit** de limiter les commentaires à trois savants contemporains. Le système mobilise la chaîne complète de la science :

| Couche | Siècle | Savants |
|--------|--------|---------|
| **Sahâba** | 7e s. H | 'Umar ibn al-Khattâb, 'Alî ibn Abî Tâlib, 'Â'isha, Ibn 'Abbâs, Abû Hurayra, Anas ibn Mâlik |
| **Tâbi'în** | 8e s. H | Sa'îd ibn al-Musayyab, al-Hasan al-Basrî, Muhammad ibn Sîrîne, Mujâhid ibn Jabr |
| **Imams Fondateurs** | 8e–9e s. H | Mâlik, ash-Shâfi'î, Ahmad ibn Hanbal, al-Bukhârî, Muslim, Abû Dâwûd, at-Tirmidhî, an-Nasâ'î, Ibn Mâjah |
| **Huffâdh Médiévaux** | 13e–15e s. H | Ibn Taymiyyah, Ibn al-Qayyim, adh-Dhahabî, an-Nawawî, Ibn Hajar al-'Asqalânî, Ibn Kathîr |
| **Filtres Contemporains** | 20e–21e s. | Al-Albânî (SS/SD), Ibn Bâz, Ibn 'Uthaymîne |

### Terminologie Pure

Utilisation **exclusive** du vocabulaire authentique du Jarh wa at-Ta'dîl :

- **Ta'dîl** : 'Adl bi-l-Ijmâ', Thiqah Thabt, Thiqah Hâfidh, Thiqah, Sadûq, Maqbûl
- **Jarh** : Layyin al-Hadîth, Da'îf, Da'îf Jiddan, Munkar al-Hadîth, Matrûk, Kadhdhâb
- **'Ilal** : Inqitâ', Tadlîs, Irsâl, Idtirâb, Shudhûdh, Ikhtilât, Jahâlah

L'utilisation de termes inventés (tels que « Lexique de Fer ») est interdite.

### Attributs Divins — Ithbât Strict

Aucun Ta'wîl (interprétation allégorique). Les Sifât sont établis tels qu'ils apparaissent dans le texte :

- **Istawâ** : S'est établi sur [le Trône]
- **Yad Allâh** : La Main d'Allâh
- **Nuzûl** : La Descente
- **Wajh Allâh** : Le Visage d'Allâh

---

## 🚨 Pilier 2 — Le Cauchemar Vercel (Infrastructure Backend)

> **Ces règles sont des lois de survie. Leur violation provoque un crash immédiat du build.**

### 2.1 Le Bouclier d'Aveuglement (`.vercelignore`)

Le fichier `server.js` à la racine sert au développement local et à Railway. Mais Vercel, en détectant un `server.js`, passe en mode « custom server » et **ignore totalement** le dossier `api/`.

**Solution** : un fichier `.vercelignore` à la racine contenant :

```
server.js
```

Sans ce fichier, le build Vercel échouera systématiquement avec :

```
Error: The pattern "api/search.js" defined in `functions` doesn't match
any Serverless Functions inside the `api` directory.
```

### 2.2 La Guerre ESM / CommonJS

`server.js` charge les routes API avec `require()` (CommonJS). Si `api/search.js` utilise `import`/`export` (ESM), Node.js lance :

```
SyntaxError: Cannot use import statement in a module
```

| Fichier | Format | Raison |
|---------|--------|--------|
| `server.js` | CommonJS (`require`) | Serveur HTTP classique |
| `api/search.js` | CommonJS (`require` / `module.exports`) | Chargé par server.js via require() |
| `api/dorar.js` | CommonJS (`module.exports`) | Idem |
| `package.json` | **JAMAIS** `"type": "module"` | Forcerait l'ESM sur tous les fichiers `.js` |

### 2.3 Le Verrou Node

```json
"engines": { "node": "20.x" }
```

**Interdit** : `">=20"` — Vercel interprète cette directive comme « utiliser la dernière version disponible » et migre automatiquement vers Node 24.x, introduisant des incompatibilités non testées.

### 2.4 Le Timeout Vercel

Vercel coupe les Serverless Functions après 10 secondes par défaut. L'analyse Claude nécessite 30 à 50 secondes. Il faut exporter explicitement :

```js
module.exports.maxDuration = 60;
```

Et déclarer dans `vercel.json` :

```json
{ "functions": { "api/search.js": { "maxDuration": 60 } } }
```

---

## ⚙️ Pilier 3 — Les Pièges du Moteur API (`api/search.js`)

### 3.1 Le Tueur Silencieux (Double `module.exports`)

Si le fichier contient deux assignations `module.exports = ...`, la seconde **écrase** la première. Le handler principal disparaît et l'API retourne des résultats statiques.

```js
// ❌ INTERDIT — le debug écrase le handler
module.exports = async (req, res) => { /* handler principal */ };
module.exports = async (req, res) => { /* debug — ÉCRASE TOUT */ };

// ✅ CORRECT — un seul export, propriétés ajoutées après
module.exports = async function handler(req, res) { /* ... */ };
module.exports.maxDuration = 60;  // ajoute une propriété, n'écrase rien
```

### 3.2 Les Modèles Fantômes

Utiliser **exclusivement** des IDs de modèle confirmés et stables :

| Rôle | ID exact | Interdit |
|------|----------|----------|
| Analyse (Takhrîj) | `claude-3-5-sonnet-20240620` | `claude-sonnet-4-6`, `claude-3-5-sonnet-latest` |
| Traduction | `claude-3-haiku-20240307` | `claude-haiku-4-5-20251001` |

Les IDs « futurs » ou les alias `latest` ne sont pas résolus par toutes les versions du SDK `@anthropic-ai/sdk`. Le résultat est une erreur 404 invisible côté serveur.

### 3.3 Le Contrat JSON (9 Champs Obligatoires)

L'API doit livrer un tableau d'objets contenant **exactement** ces 9 champs :

| # | Champ | Zone Frontend | Rôle |
|---|-------|---------------|------|
| 1 | `french_text` | Zone 1 | Traduction littérale du matn |
| 2 | `grade_explique` | Zone 1 | Verdict détaillé (4 lignes HTML) |
| 3 | `isnad_chain` | Zone 2 | Chaîne pipe-delimited (Arbre de Lumière) |
| 4 | `jarh_tadil` | Zone 2 | Verdicts des Imams sur les rawis |
| 5 | `sanad_conditions` | Zone 2 | 5 conditions d'Ibn as-Salâh |
| 6 | `mutabaat` | Zone 2 | Voies de renfort et shawâhid |
| 7 | `avis_savants` | Zone 3 | 7 paragraphes (14 siècles) |
| 8 | `grille_albani` | Zone 3 | Rapport complet al-Albânî |
| 9 | `pertinence` | Badge | `OUI` / `PARTIEL` / `NON` |

**L'absence de `isnad_chain` plonge le frontend dans un « Analyse en cours... » infini.** Le champ doit suivre le format pipe strict :

```
Maillon 1 | Nom complet (m.XXH) | Titre | Verdict | Siecle\n
Maillon 2 | Nom complet (m.XXH) | Titre | Verdict | Siecle\n
```

### 3.4 La Clôture du Flux (SSE)

Si le backend utilise le streaming SSE, le flux doit impérativement se terminer par :

```
event: done
data: {"done": true}

```

Sans ce signal, la barre de chargement du frontend ne se ferme jamais.

### 3.5 Compatibilité URL

```js
// ❌ INTERDIT — déprécié, génère des warnings Vercel
const parsed = url.parse(req.url, true);

// ✅ CORRECT — standard Node.js 20+
const parsedUrl = new URL(req.url || "/", "http://localhost");
const q = parsedUrl.searchParams.get("q");
```

---

## 🛡️ Pilier 4 — Le Frontend et l'Intégrité (Triple Bouclier v18.6)

### 4.1 La Prison du Scope (Bug Safari)

Les fonctions `nodeVis`, `parseSiecle` et `goTo` sont appelées par `_mzIsnadFromPipe` pour dessiner l'Arbre de Lumière. Si elles sont déclarées à l'intérieur d'un bloc `try { ... }`, Safari iOS et certains moteurs en mode strict ne les hissent pas.

```js
// ❌ INTERDIT — fonctions piégées dans un try
try {
  function parseSiecle(s) { ... }  // invisible en dehors du try
  function nodeVis(t,v,i,n) { ... }
}

// ✅ CORRECT — portée globale absolue
window.parseSiecle = function(s) { ... };
window.nodeVis = function(t,v,i,n) { ... };
window.goTo = function(view) { ... };
```

Ces déclarations doivent être dans le **premier bloc `<script>`** du fichier, avant tout le HTML.

### 4.2 Bug Cormorant (Syntaxe des Chaînes)

La police Cormorant Garamond contient une apostrophe dans son nom CSS. Quand on construit du HTML avec des apostrophes simples (`'`), cela casse la chaîne :

```js
// ❌ CRASH — l'apostrophe de Garamond ferme la chaîne
h += '<p style="font-family:\'Cormorant Garamond\',serif;">texte</p>';

// ✅ CORRECT — backticks (template literals)
h += `<p style="font-family:Cormorant Garamond,serif;">texte</p>`;
```

Règle : tout HTML injecté via JavaScript doit utiliser des backticks.

### 4.3 Design Impérial

- **Zone 1** : les noms des 18 Savants Piliers doivent être entourés de `<span class="scholar-glow">Nom</span>` (effet Noûr doré)
- **Zone 2 (Isnad)** : conteneur avec `min-height: 40px`, titre doré, fond dégradé profond, cartes glassmorphism (`backdrop-filter: blur(8px)`)
- **Séparateurs Isnad** : le parser doit accepter `|` (pipe), `—` (em-dash), `–` (en-dash) et ` - ` (tiret simple)

---

## ⚖️ Pilier 5 — Protocole d'Intervention

### One-Shot Secured

Toute modification future de ce projet (par un humain ou une IA) doit consister en la **livraison du fichier intégral**. Aucune modification par bloc, aucune rustine partielle. Un fichier modifié est un fichier livré en entier.

### Mouchard de Vérité

Le frontend doit s'amorcer avec ce log dans la console :

```js
console.log("%c ✅ Mîzân : Prêt pour Production", "color: #00ff00; font-weight: bold;");
```

Si ce log n'apparaît pas au démarrage, le script principal n'a pas chargé correctement.

### Checklist de Déploiement

Avant chaque push sur GitHub, vérifier :

- [ ] `package.json` ne contient PAS `"type": "module"`
- [ ] `package.json` contient `"node": "20.x"`
- [ ] `.vercelignore` existe et contient `server.js`
- [ ] `api/search.js` utilise `require()` et `module.exports` (pas `import`/`export`)
- [ ] `api/search.js` a un seul `module.exports = handler`
- [ ] Les modèles sont `claude-3-5-sonnet-20240620` et `claude-3-haiku-20240307`
- [ ] Les 9 champs JSON sont présents (dont `isnad_chain`)
- [ ] Le mouchard `console.log` apparaît dans la console du navigateur

---

## Variables d'Environnement

| Variable | Requise | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Oui | Clé API Anthropic pour les appels Claude |

À configurer dans le dashboard Vercel : Settings → Environment Variables.

---

## Déploiement

```bash
git add .
git commit -m "Mîzân v18.6 — CommonJS, 9 champs, Loi d'Airain"
git push origin main
```

Vercel déploie automatiquement depuis la branche `main`. Le build doit afficher un statut vert (✅) sans warning de Node.js.

---

## Crédits et Sources Académiques

Ce projet s'appuie sur les ouvrages suivants pour la méthodologie du Hadith :

- **Muqaddimah fî 'Ulûm al-Hadîth** — Ibn as-Salâh (m. 643H)
- **Nuzhah an-Nadhar fî Tawdîh Nukhbah al-Fikar** — Ibn Hajar al-'Asqalânî (m. 852H)
- **Mîzân al-I'tidâl fî Naqd ar-Rijâl** — Shams ad-Dîn adh-Dhahabî (m. 748H)
- **Silsilah al-Ahâdîth as-Sahîhah** — Muhammad Nâsir ad-Dîn al-Albânî (m. 1420H)
- **Silsilah al-Ahâdîth ad-Da'îfah** — Muhammad Nâsir ad-Dîn al-Albânî (m. 1420H)
- **Taqrîb at-Tahdhîb** — Ibn Hajar al-'Asqalânî (m. 852H)

Les données brutes des hadiths proviennent de [Dorar.net](https://dorar.net), la plus grande encyclopédie numérique du Hadith.

---

*Mîzân as-Sunnah — بسم الله الرحمن الرحيم*
