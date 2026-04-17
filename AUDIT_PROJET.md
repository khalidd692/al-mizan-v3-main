# 🔍 AUDIT COMPLET AL-MĪZĀN v5.0 — État des Lieux

**Date** : 17 avril 2026, 03:44 AM  
**Auditeur** : Kiro AI  
**Objectif** : Analyse avant construction harvester + pipeline agents + SSE auto-insertion

---

## 📊 ÉTAT ACTUEL DU PROJET

### ✅ Ce qui existe (Phase 1 complétée)

#### 1. Architecture Backend (Starlette)
- **Point d'entrée** : `backend/main.py`
  - Application Starlette fonctionnelle
  - Route `/api/health` opérationnelle
  - Route `/api/search` avec SSE streaming
  - Serveur de fichiers statiques pour frontend
  - CORS configuré

- **Orchestrateur** : `backend/orchestrator.py`
  - Pipeline complet des 32 zones
  - Gestion parallèle de 4 agents via `asyncio.Queue`
  - Streaming SSE avec keepalive
  - Timeout global de sécurité (55s)
  - **Mode MOCK actif** : données fictives pour tests

- **4 Agents Spécialisés** (mode mock)
  - `agent_isnad.py` : Zones 2-3 (Isnād + Jarḥ wa Taʿdīl)
  - `agent_ilal.py` : Zones 6-8 (ʿIlal cachées)
  - `agent_matn.py` : Zones 9-14 (Gharīb, Sabab, Āthār)
  - `agent_tarjih.py` : Zones 15+ (Ijmāʿ, Khilāf, Tarjīḥ)

- **Utilitaires**
  - `utils/sse.py` : Formatage événements SSE
  - `utils/logging.py` : Logger structuré
  - `utils/constitution.py` : Chargeur Constitution v4

#### 2. Frontend (HTML/CSS/JS Vanilla)
- Interface 3 colonnes (Isnād | Matn | Evidence)
- Dashboard avec 8 tabs
- Client SSE avec reconnexion automatique
- Arbre d'Isnād vertical interactif
- Formulaire de recherche fonctionnel

#### 3. Tests
- `tests/test_orchestrator.py` : 1 test passant (100%)
- Tests manuels API validés

#### 4. Documentation
- `README.md` : Documentation principale
- `Constitution_v4.md` : Spécification complète (1818 lignes)
- `RAPPORT_FINAL_PHASE1.md` : Rapport détaillé Phase 1
- `.env.example` : Template configuration

---

## ❌ Ce qui manque (à construire)

### 1. Base de Données
- **Statut** : ❌ **INEXISTANTE**
- **Fichier** : `corpus/corpus.db` n'existe pas
- **Impact** : Aucun stockage de hadiths actuellement

### 2. Client Dorar.net
- **Fichier** : `backend/dorar/client.py` (stub vide)
- **Statut** : ❌ **NON IMPLÉMENTÉ**
- **Besoin** : Scraper avec rate limiting pour aspirer hadiths

### 3. Corpus Loader
- **Fichier** : `backend/corpus/loader.py` (stub vide)
- **Statut** : ❌ **NON IMPLÉMENTÉ**
- **Besoin** : Interface pour lire/écrire dans corpus.db

### 4. Pipeline Agents Réels
- **Statut** : ⚠️ **MODE MOCK ACTIF**
- **Fichiers prompts** : Vides (à rédiger)
  - `backend/agents/prompts/isnad.md`
  - `backend/agents/prompts/ilal.md`
  - `backend/agents/prompts/matn.md`
  - `backend/agents/prompts/tarjih.md`
- **Besoin** : Connexion API Anthropic + prompts Constitution v4

### 5. Harvester Script
- **Statut** : ❌ **INEXISTANT**
- **Besoin** : Script autonome pour aspirer 1000 hadiths depuis Dorar.net

---

## 🎯 PLAN D'EXÉCUTION (selon votre mission)

### Phase A : Création Base de Données SQLite

**Fichier** : `corpus/corpus.db`

**Schéma proposé** :
```sql
-- Table principale des hadiths bruts (harvester)
CREATE TABLE hadiths_raw (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dorar_id TEXT UNIQUE NOT NULL,
    matn_ar TEXT NOT NULL,
    source TEXT,
    grade_raw TEXT,
    rawi TEXT,
    harvested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT 0
);

-- Table hadiths validés (après pipeline agents)
CREATE TABLE hadiths_validated (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hadith_raw_id INTEGER REFERENCES hadiths_raw(id),
    matn_ar TEXT NOT NULL,
    translation_fr TEXT,
    grade_normalized TEXT, -- صحيح / حسن / ضعيف / موضوع
    scholar_verdict TEXT, -- Nom du savant validé
    scholar_location TEXT, -- Médine / Arabie Saoudite / TAWAQQUF
    confidence_score REAL, -- 0-100
    agent_isnad_output JSON,
    agent_ilal_output JSON,
    agent_matn_output JSON,
    agent_tarjih_output JSON,
    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(hadith_raw_id)
);

-- Table pour review manuelle (confiance < 85)
CREATE TABLE pending_review (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hadith_raw_id INTEGER REFERENCES hadiths_raw(id),
    reason TEXT,
    confidence_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour performances
CREATE INDEX idx_hadiths_raw_processed ON hadiths_raw(processed);
CREATE INDEX idx_hadiths_validated_grade ON hadiths_validated(grade_normalized);
CREATE INDEX idx_pending_review_confidence ON pending_review(confidence_score);
```

### Phase B : Harvester Dorar.net

**Fichier** : `backend/harvester.py`

**Spécifications** :
- Aspirer 1000 hadiths depuis API JSON Dorar.net
- Rate limiting : 2 secondes entre chaque requête
- Checkpoint de reprise (en cas d'interruption)
- Stockage brut dans `hadiths_raw`
- Logging détaillé
- Gestion d'erreurs robuste

**Endpoints Dorar.net à explorer** :
- API JSON (si disponible)
- Sinon : scraping HTML avec BeautifulSoup

### Phase C : Pipeline 4 Agents Claude

**Architecture** :
```
Hadith brut → Agent 1 (Haiku) → Normalisation grade
           → Agent 2 (Haiku) → Traduction Lexique de Fer
           → Agent 3 (Haiku) → Validation savant (hiérarchie Médine)
           → Agent 4 (Sonnet si confiance < 80) → Vérification finale
           → Insertion auto si confiance >= 85
           → Sinon → pending_review
```

**Règles strictes** :
1. **Jamais de texte hadith généré par le modèle**
2. **Hiérarchie savants** : Médine > Arabie Saoudite > TAWAQQUF si inconnu/déviant
3. **Terme "Salafi" interdit** → "Salaf as-Salih" uniquement
4. **Confiance >= 85** : insertion automatique
5. **Confiance < 85** : table `pending_review`

### Phase D : Endpoint SSE Auto-Insertion

**Route** : `/api/harvest-and-process`

**Fonctionnement** :
1. Client SSE se connecte
2. Backend lance harvester (1000 hadiths)
3. Pour chaque hadith :
   - Aspiration depuis Dorar.net
   - Passage dans pipeline 4 agents
   - Insertion en base si confiance >= 85
   - Événement SSE envoyé au client (progression)
4. Rapport final : X insérés / Y en review

---

## 🔧 DÉPENDANCES À AJOUTER

**Fichier** : `requirements.txt`

```txt
# Existant
starlette==0.41.3
uvicorn[standard]==0.34.0
anthropic==0.40.0
python-dotenv==1.0.1

# À ajouter
aiohttp==3.9.1          # Client HTTP async pour Dorar.net
beautifulsoup4==4.12.2  # Parsing HTML si pas d'API JSON
aiosqlite==0.19.0       # SQLite async
```

---

## 📋 CHECKLIST AVANT DÉMARRAGE

- [x] Audit structure projet
- [x] Vérification base de données (inexistante)
- [x] Analyse Constitution v4 (1818 lignes)
- [x] Lecture rapport Phase 1
- [ ] Création schéma SQLite
- [ ] Implémentation harvester
- [ ] Rédaction prompts agents
- [ ] Pipeline agents avec Claude
- [ ] Endpoint SSE auto-insertion
- [ ] Tests avec 500 hadiths réels
- [ ] Validation avant merge

---

## ⚠️ POINTS D'ATTENTION

### 1. Constitution v4 (1818 lignes)
- Document extrêmement détaillé
- 22 interdits absolus (Section Zéro)
- Hiérarchie chronologique stricte (Mutaqaddimūn > Khalaf > Contemporains)
- Système d'alertes colorées obligatoires
- **À intégrer dans les prompts agents**

### 2. Règles Strictes Mission
- ❌ Jamais de texte hadith généré par IA
- ❌ Jamais merger sans 500 entrées réelles
- ❌ Jamais utiliser terme "Salafi" (uniquement "Salaf as-Salih")
- ✅ Hiérarchie savants : Médine > Arabie Saoudite > TAWAQQUF
- ✅ Tests unitaires à 100%

### 3. Performance
- Rate limiting Dorar.net : 2s entre requêtes
- 1000 hadiths = ~33 minutes minimum (2s × 1000)
- Pipeline agents : ~5-10s par hadith avec Claude
- Total estimé : **2-3 heures** pour 1000 hadiths

---

## 🚀 PROCHAINE ÉTAPE

**Attente de votre validation avant de commencer le code.**

Questions à confirmer :
1. Schéma SQLite proposé OK ?
2. Architecture pipeline 4 agents OK ?
3. Seuil confiance 85% OK ?
4. Commencer par harvester ou par base de données ?

**Recommandation** : Commencer par la base de données (Phase A), puis harvester (Phase B), puis agents (Phase C), puis SSE (Phase D).