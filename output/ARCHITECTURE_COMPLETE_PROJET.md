# 🏗️ ARCHITECTURE COMPLÈTE DU PROJET AL-MĪZĀN v5.0

**Date**: 18 avril 2026, 23:24  
**Statut**: Documentation complète de l'architecture

---

## 📋 VUE D'ENSEMBLE

**Al-Mīzān** est une plateforme web de takhrīj (authentification) de hadiths basée sur l'IA, avec une architecture moderne Python/JavaScript.

### Objectif Principal
Fournir une analyse scientifique des hadiths selon la méthodologie salafie, avec vérification automatique de l'authenticité et détection des innovations (bid'ah).

---

## 🎯 STACK TECHNIQUE

### Backend
- **Framework**: Starlette (ASGI) + Uvicorn
- **Base de données**: SQLite (`backend/almizane.db`)
- **IA**: Anthropic Claude (API)
- **Langage**: Python 3.x
- **Dépendances principales**:
  - `starlette==0.41.3`
  - `uvicorn[standard]==0.34.0`
  - `anthropic==0.40.0`
  - `aiosqlite==0.19.0`
  - `beautifulsoup4==4.12.2`
  - `aiohttp==3.9.1`

### Frontend
- **Architecture**: SPA (Single Page Application)
- **Technologies**: HTML5, CSS3, JavaScript vanilla
- **Direction**: RTL (Right-to-Left) pour l'arabe
- **Fonts**: Scheherazade New, Cormorant Garamond, Cinzel
- **Communication**: Server-Sent Events (SSE)

---

## 📊 BASE DE DONNÉES

### Schéma Principal (`backend/init_schema_v5.sql`)

#### Table `hadiths` (122,927 entrées)
```sql
- id              INTEGER PRIMARY KEY AUTOINCREMENT
- sha256          TEXT NOT NULL UNIQUE          -- Hash du matn_ar (déduplication)
- collection      TEXT NOT NULL                 -- ex: "Sahih al-Bukhari"
- numero_hadith   TEXT                          -- numéro dans la collection
- livre           TEXT
- chapitre        TEXT
- matn_ar         TEXT NOT NULL                 -- texte arabe brut
- matn_fr         TEXT                          -- traduction française
- isnad_brut      TEXT                          -- chaîne de transmission
- grade_final     TEXT NOT NULL                 -- Sahih, Hasan, Da'if, etc.
- categorie       TEXT NOT NULL                 -- MAQBUL | DAIF | MAWDUU
- badge_alerte    INTEGER DEFAULT 0             -- 1 = Mawdū' (alerte rouge)
- source_url      TEXT
- source_api      TEXT                          -- origine des données
- inserted_at     TEXT DEFAULT (datetime('now'))
```

#### Statistiques Actuelles
- **Total hadiths**: 122,927
- **Collections**: 18 distinctes
- **Top 3 collections**:
  1. Sunan an-Nasa'i: 16,658
  2. Bukhari: 13,913
  3. Muslim: 12,220

#### Répartition par Catégorie
- `hadith`: 63,070
- `Général`: 39,258
- `MAQBUL`: 20,599

#### Répartition par Grade
- Non évalué: 72,446
- Sahih: 23,564
- Non évalué (explicite): 20,557
- Da'if: 4,204
- Hasan: 1,692

#### Sources API
- `jsdelivr_cdn`: 44,838
- `hadith_gading`: 42,457
- `jsdelivr_fawaz`: 35,590
- `github:osamayy/40-hadith-nawawi-db`: 42

#### Table `avis_savants`
Stocke les jugements des savants sur les hadiths avec:
- Référence au hadith (sha256)
- Nom du savant (whitelist)
- Époque (MUTAQADDIMUN | KHALAF | MUASIR)
- Jugement textuel
- Source du jugement

#### Table `lexique_fer`
Dictionnaire des attributs divins avec traductions interdites (ta'wil):
- استوى (S'est établi) ≠ "s'est installé"
- يد (Main réelle) ≠ "puissance"
- نزول (Descend) ≠ "Sa miséricorde descend"
- وجه (Visage réel) ≠ "essence"
- ساق (Jambe réelle) ≠ "sévérité"
- عين (Œil réel) ≠ "connaissance"

#### Table `errors_log`
Journal des erreurs de collecte et validation.

---

## 🔧 ARCHITECTURE BACKEND

### Point d'Entrée (`backend/main.py`)

#### Endpoints API

1. **`GET /api/health`**
   - Statut du service
   - Version actuelle
   - Mode démo activé/désactivé

2. **`GET /api/search?q={query}`**
   - Recherche de hadiths avec analyse IA
   - Streaming SSE (Server-Sent Events)
   - Rate limiting: 10 requêtes/min par IP
   - Headers:
     - `X-Mizan-Demo`: Mode démonstration
     - `X-Mizan-Version`: Version de l'API

3. **`GET /api/harvest-and-process`**
   - Harvesting automatique + validation
   - Paramètres:
     - `start_id`: ID de départ
     - `count`: Nombre de hadiths
     - `rate_limit`: Limite de requêtes/sec

#### Middleware
- **CORS**: Configurable via `MIZAN_ALLOWED_ORIGINS`
- **Rate Limiting**: Protection contre les abus
- **Static Files**: Serveur de fichiers statiques

### Modules Backend

#### `backend/orchestrator.py`
Orchestrateur principal qui coordonne:
- Recherche dans la base de données
- Analyse IA via Claude
- Génération de réponses structurées

#### `backend/pipeline.py`
Pipeline de validation:
- Harvesting des sources externes
- Validation automatique
- Insertion en base de données

#### Connecteurs (`backend/connectors/`)
- `hadith_gading_connector.py`: API Hadith Gading
- `jsdelivr_connector.py`: CDN jsDelivr
- `dorar_connector.py`: Dorar.net
- `sunnah_connector.py`: Sunnah.com
- `shamela_connector.py`: Shamela

#### Harvesters
Multiples scripts de collecte massive:
- `production_harvester_v8.py`
- `mega_harvester_v9.py`
- `ultimate_harvester_v11.py`
- Etc.

---

## 🎨 ARCHITECTURE FRONTEND

### Structure (`frontend/`)

```
frontend/
├── index.html              # Page principale
├── timeline-demo.html      # Module de confrontation temporelle
├── css/
│   ├── base.css           # Styles de base
│   ├── dashboard.css      # Dashboard principal
│   ├── isnad-tree.css     # Arbre d'isnād
│   └── timeline-module.css # Module timeline
└── js/
    ├── cache-manager.js   # Gestion du cache
    ├── sse-client.js      # Client SSE
    ├── isnad-tree.js      # Visualisation isnād
    ├── dashboard.js       # Logique principale
    └── timeline-module.js # Module confrontation
```

### Interface Utilisateur

#### Layout Principal (3 colonnes)

1. **Colonne Gauche**: Arbre d'Isnād (سلسلة الإسناد)
   - Visualisation de la chaîne de transmission
   - Arbre hiérarchique des narrateurs

2. **Colonne Centrale**: Matn et Analyse
   - Bannière de verdict (Sahih/Da'if/Mawdū')
   - Texte arabe (matn_ar)
   - Traduction française (matn_fr)
   - Sources
   - **12 onglets d'analyse**:
     - الإسناد (Isnād)
     - العلل (Défauts)
     - الغريب (Termes rares)
     - سبب الورود (Contexte)
     - الشروح (Commentaires)
     - الآثار (Effets)
     - الإجماع (Consensus)
     - المختلف (Divergences)
     - النسخ (Abrogation)
     - الفوائد (Bénéfices)
     - العقيدة (Croyance)
     - الترجيح (Préférence)

3. **Colonne Droite**: Registre des Preuves (سجل الأدلة)
   - Journal des arguments
   - Preuves scripturaires

#### Fonctionnalités
- Recherche en temps réel
- Cache local (localStorage)
- Bouton de vidage du cache
- Barre de progression
- Statut en temps réel

---

## 🔄 FLUX DE DONNÉES

### Recherche de Hadith

```
1. Utilisateur saisit une requête
   ↓
2. Frontend envoie GET /api/search?q={query}
   ↓
3. Backend (Orchestrator):
   - Recherche dans SQLite
   - Analyse avec Claude AI
   - Génère réponse structurée
   ↓
4. Streaming SSE vers Frontend
   ↓
5. Frontend met à jour l'interface progressivement
   ↓
6. Cache la réponse localement
```

### Harvesting de Hadiths

```
1. Script harvester démarre
   ↓
2. Connexion aux sources externes (APIs)
   ↓
3. Extraction des données brutes
   ↓
4. Validation et normalisation
   ↓
5. Calcul du SHA256 (déduplication)
   ↓
6. Insertion dans SQLite
   ↓
7. Logging des erreurs
```

---

## 🔐 SÉCURITÉ

### Mesures Implémentées

1. **Rate Limiting**
   - 10 requêtes/min par IP
   - Protection contre les abus

2. **CORS**
   - Configurable via environnement
   - Restriction des origines

3. **Déduplication**
   - Hash SHA256 du matn_ar
   - Contrainte UNIQUE en base

4. **Validation des Entrées**
   - Paramètres de requête validés
   - Protection contre les injections

5. **Lexique de Fer**
   - Détection automatique des ta'wil
   - Alerte sur les innovations

---

## 📦 DÉPLOIEMENT

### Configuration Requise

#### Variables d'Environnement (`.env`)
```bash
ANTHROPIC_API_KEY=sk-ant-...
MIZAN_DEMO_MODE=1
MIZAN_ALLOWED_ORIGINS=*
```

#### Fichiers de Configuration
- `render.yaml`: Configuration Render.com
- `vercel.json`: Configuration Vercel
- `requirements.txt`: Dépendances Python

### Commandes de Démarrage

#### Développement
```bash
# Installer les dépendances
pip install -r requirements.txt

# Lancer le serveur
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

#### Production
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 📈 MÉTRIQUES ET MONITORING

### Scripts de Monitoring

- `check_db_structure.py`: Analyse de la base
- `rapport_db_final.py`: Rapport complet
- `stats_simples.py`: Statistiques rapides
- `monitor_*.py`: Surveillance des harvesters

### Logs

- `backend/*.log`: Logs des harvesters
- `errors_log` (table): Erreurs en base
- Console Uvicorn: Logs serveur

---

## 🔮 MODULES AVANCÉS

### Module Timeline (`frontend/timeline-demo.html`)
- Confrontation temporelle des avis
- Visualisation chronologique
- Comparaison des époques (Mutaqaddimun/Khalaf/Muasir)

### Module API Timeline (`backend/api_timeline.py`)
- Endpoint dédié pour la timeline
- Agrégation des avis par époque

---

## 🎯 POINTS CLÉS

### Forces
✅ Base de données riche (122K+ hadiths)  
✅ Architecture moderne et scalable  
✅ Interface bilingue (arabe/français)  
✅ Analyse IA avancée  
✅ Déduplication automatique  
✅ Rate limiting intégré  
✅ Support SSE pour temps réel  

### Axes d'Amélioration
⚠️ Catégorisation incohérente (3 systèmes différents)  
⚠️ 72K hadiths sans grade  
⚠️ Manque de tests automatisés  
⚠️ Documentation API limitée  
⚠️ Pas de système d'authentification  

---

## 📚 RESSOURCES

### Documentation Interne
- `Constitution_v4.md`: Spécifications méthodologiques
- `KIRO_SETUP_COMPLETE.md`: Guide d'installation
- `output/*.md`: Rapports de progression

### APIs Externes Utilisées
- Hadith Gading API
- jsDelivr CDN
- Dorar.net
- Sunnah.com
- Shamela

---

## 🏁 CONCLUSION

Al-Mīzān v5.0 est une plateforme robuste et moderne pour l'authentification de hadiths, combinant:
- Une base de données SQLite riche et bien structurée
- Un backend Python asynchrone performant
- Une interface web réactive et bilingue
- Une intégration IA pour l'analyse avancée
- Des mécanismes de sécurité et de rate limiting

Le projet est prêt pour la production avec quelques améliorations recommandées sur la normalisation des données et l'ajout de tests.

---

**Généré le**: 18 avril 2026, 23:24  
**Version**: 5.0.0-dev  
**Auteur**: Analyse automatique Kiro