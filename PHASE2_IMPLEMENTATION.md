# Al-Mīzān v5.0 — Phase 2 : Implémentation Harvester + Pipeline Agents

**Date** : 17 avril 2026, 03:51 AM  
**Statut** : ✅ INFRASTRUCTURE COMPLÈTE — PRÊT POUR TESTS RÉELS

---

## 📦 Ce qui a été construit

### 1. Base de Données SQLite ✅

**Fichiers** :
- `backend/corpus/schema.sql` : Schéma complet avec 3 tables
- `backend/corpus/db.py` : Gestionnaire async avec aiosqlite

**Tables** :
- `hadiths_raw` : Hadiths bruts depuis Dorar.net
- `hadiths_validated` : Hadiths validés (confiance >= 85%)
- `pending_review` : Hadiths en attente de review manuelle (confiance < 85%)

**Vues** :
- `v_hadiths_unprocessed` : Hadiths non traités
- `v_stats` : Statistiques globales

**Tests** : ✅ 5/5 passants (`tests/test_db.py`)

### 2. Client Dorar.net ✅

**Fichier** : `backend/dorar/client.py`

**Fonctionnalités** :
- Rate limiting configurable (défaut: 2s entre requêtes)
- Récupération hadith par ID
- Parsing HTML avec BeautifulSoup
- Gestion d'erreurs robuste
- Context manager async

**Note** : Les sélecteurs CSS sont des PLACEHOLDERS et devront être ajustés selon la structure réelle de Dorar.net lors des tests.

### 3. Harvester avec Checkpoint ✅

**Fichier** : `backend/harvester.py`

**Fonctionnalités** :
- Aspiration 1000 hadiths (configurable)
- Rate limiting 2s (configurable)
- Checkpoint de reprise automatique (`corpus/harvester_checkpoint.json`)
- Sauvegarde tous les 10 hadiths
- Statistiques détaillées
- Mode CLI et mode callback pour SSE

**Usage CLI** :
```bash
python -m backend.harvester --start-id 1 --count 1000 --rate-limit 2.0
```

### 4. Agent Validateur Unifié ✅

**Fichier** : `backend/agents/agent_validator.py`

**Architecture** :
1. **Normalisation grade** (Haiku) : صحيح / حسن / ضعيف / موضوع
2. **Traduction** (Haiku) : Lexique de Fer (termes techniques en arabe)
3. **Validation savant** (Haiku) : Hiérarchie Médine > Arabie Saoudite > TAWAQQUF
4. **Vérification finale** (Sonnet si confiance < 80)

**Règles strictes respectées** :
- ❌ Jamais de texte hadith généré par IA
- ❌ Terme "Salafi" interdit → "Salaf as-Salih" uniquement
- ✅ Hiérarchie savants : Médine (priorité 1) > Arabie Saoudite (2) > TAWAQQUF (3)
- ✅ TAWAQQUF si savant inconnu ou déviant
- ✅ Mode mock pour tests sans API key

### 5. Pipeline Complet ✅

**Fichier** : `backend/pipeline.py`

**Flux** :
```
Dorar.net → Harvester → DB (hadiths_raw)
                ↓
         Agent Validator
                ↓
    Confiance >= 85% ? ──YES→ hadiths_validated
                ↓
               NO
                ↓
         pending_review
```

**Modes** :
- `process_stream()` : Streaming SSE temps réel
- `process_batch()` : Mode batch sans streaming

**Seuil confiance** : 85% (configurable via `CONFIDENCE_THRESHOLD`)

### 6. Endpoint SSE ✅

**Route** : `/api/harvest-and-process`

**Paramètres** :
- `start_id` : ID de départ (défaut: 1)
- `count` : Nombre de hadiths (défaut: 1000)
- `rate_limit` : Secondes entre requêtes (défaut: 2.0)

**Événements SSE** :
- `pipeline_start` : Démarrage
- `phase` : Changement de phase (HARVESTING / VALIDATION)
- `harvest_progress` : Progression harvesting
- `validation_progress` : Progression validation
- `hadith_inserted` : Hadith inséré (confiance >= 85%)
- `hadith_pending_review` : Hadith en review (confiance < 85%)
- `hadith_failed` : Erreur traitement
- `pipeline_complete` : Fin avec statistiques

**Usage** :
```bash
curl -N "http://localhost:8000/api/harvest-and-process?start_id=1&count=100&rate_limit=2.0"
```

---

## 🧪 Tests Réalisés

### Tests Unitaires ✅
```bash
pytest tests/test_db.py -v
# Résultat: 5/5 passants
```

**Couverture** :
- Création base de données
- Insertion hadiths bruts
- Insertion hadiths validés
- Insertion pending review
- Récupération statistiques

### Tests d'Intégration ⏳
**À faire** : Tests avec Dorar.net réel

---

## ⚠️ Points d'Attention

### 1. Sélecteurs CSS Dorar.net
**Fichier** : `backend/dorar/client.py` ligne 90-105

Les sélecteurs CSS sont des PLACEHOLDERS :
```python
matn_elem = soup.select_one('.hadith-text, .matn, [class*="hadith"]')
source_elem = soup.select_one('.hadith-source, .source, [class*="source"]')
grade_elem = soup.select_one('.hadith-grade, .grade, [class*="grade"]')
rawi_elem = soup.select_one('.hadith-rawi, .rawi, [class*="rawi"]')
```

**Action requise** : Inspecter une page Dorar.net réelle et ajuster les sélecteurs.

### 2. API Anthropic
**Mode actuel** : MOCK (pas d'appels API réels)

**Pour activer** :
1. Ajouter `ANTHROPIC_API_KEY` dans `.env`
2. Les agents passeront automatiquement en mode réel

**Coût estimé** :
- Haiku : ~$0.25 / 1M tokens input, ~$1.25 / 1M tokens output
- Sonnet : ~$3 / 1M tokens input, ~$15 / 1M tokens output
- Pour 1000 hadiths : ~$5-10 (estimation)

### 3. Rate Limiting Dorar.net
**Actuel** : 2 secondes entre requêtes

**Temps estimé** :
- 1000 hadiths = 2000 secondes = ~33 minutes (harvesting seul)
- + validation = ~1-2 heures total

**Recommandation** : Tester d'abord avec 10-50 hadiths.

---

## 🚀 Prochaines Étapes

### Étape 1 : Test Dorar.net (CRITIQUE)
```bash
# Test avec 1 hadith
python -c "
import asyncio
from backend.dorar.client import DorarClient

async def test():
    async with DorarClient() as client:
        hadith = await client.fetch_hadith_by_id('1')
        print(hadith)

asyncio.run(test())
"
```

**Si échec** : Ajuster les sélecteurs CSS dans `backend/dorar/client.py`

### Étape 2 : Test Harvester (10 hadiths)
```bash
python -m backend.harvester --start-id 1 --count 10 --rate-limit 2.0
```

**Vérifier** :
- Checkpoint créé dans `corpus/harvester_checkpoint.json`
- Base de données créée dans `corpus/corpus.db`
- Hadiths insérés dans `hadiths_raw`

### Étape 3 : Test Pipeline (mode mock)
```bash
# Lancer serveur
uvicorn backend.main:app --reload

# Dans autre terminal
curl -N "http://localhost:8000/api/harvest-and-process?start_id=1&count=10&rate_limit=2.0"
```

**Vérifier** :
- Événements SSE reçus
- Hadiths validés en mode mock
- Insertion dans `hadiths_validated`

### Étape 4 : Test avec API Anthropic (5 hadiths)
```bash
# Ajouter dans .env
ANTHROPIC_API_KEY=sk-ant-...

# Relancer pipeline
curl -N "http://localhost:8000/api/harvest-and-process?start_id=1&count=5&rate_limit=2.0"
```

**Vérifier** :
- Appels API Haiku réussis
- Grades normalisés corrects
- Traductions françaises cohérentes
- Savants validés selon hiérarchie

### Étape 5 : Production (500 hadiths minimum)
**Règle absolue** : Jamais merger sans 500 entrées réelles validées

```bash
# Production run
curl -N "http://localhost:8000/api/harvest-and-process?start_id=1&count=500&rate_limit=2.0"
```

**Durée estimée** : 2-3 heures

**Vérifier** :
- Au moins 500 hadiths dans `hadiths_validated`
- Taux de confiance >= 85% pour insertions auto
- Statistiques cohérentes

---

## 📊 Métriques de Succès

### Critères de Validation Phase 2

- [ ] Dorar.net : 100% des requêtes réussies (sur échantillon 50)
- [ ] Harvester : Checkpoint fonctionne (test interruption + reprise)
- [ ] Agent Validator : Grades normalisés corrects (100%)
- [ ] Agent Validator : Traductions cohérentes (vérification manuelle 10 hadiths)
- [ ] Agent Validator : Hiérarchie savants respectée (100%)
- [ ] Pipeline : >= 500 hadiths validés
- [ ] Pipeline : Taux insertion auto >= 70% (confiance >= 85%)
- [ ] Pipeline : Aucun hadith généré par IA (vérification manuelle)
- [ ] Tests : 100% passants

---

## 📝 Fichiers Créés

```
backend/
├── corpus/
│   ├── schema.sql          ✅ Schéma SQLite
│   └── db.py               ✅ Gestionnaire DB async
├── dorar/
│   └── client.py           ✅ Client Dorar.net
├── agents/
│   └── agent_validator.py  ✅ Agent validateur unifié
├── harvester.py            ✅ Harvester avec checkpoint
├── pipeline.py             ✅ Pipeline complet
└── main.py                 ✅ Endpoint SSE ajouté

tests/
└── test_db.py              ✅ Tests DB (5/5 passants)

requirements.txt            ✅ Dépendances ajoutées
```

---

## 🎯 Commandes Utiles

### Vérifier base de données
```bash
python check_db.py
```

### Lancer tests
```bash
pytest tests/ -v
```

### Lancer serveur
```bash
uvicorn backend.main:app --reload --port 8000
```

### Harvester CLI
```bash
python -m backend.harvester --count 10
```

### Statistiques DB
```bash
python -c "
import asyncio
from backend.corpus.db import CorpusDB

async def stats():
    db = CorpusDB()
    print(await db.get_stats())

asyncio.run(stats())
"
```

---

## ✅ Checklist Finale

- [x] Base de données SQLite créée
- [x] Client Dorar.net implémenté
- [x] Harvester avec checkpoint
- [x] Agent validateur unifié
- [x] Pipeline complet
- [x] Endpoint SSE `/api/harvest-and-process`
- [x] Tests unitaires DB (5/5)
- [x] Dépendances installées
- [ ] Tests Dorar.net réel
- [ ] Tests pipeline avec 10 hadiths
- [ ] Tests API Anthropic avec 5 hadiths
- [ ] Production run 500 hadiths
- [ ] Validation manuelle échantillon
- [ ] Merge vers main

---

**Prochaine action** : Tester avec Dorar.net réel et ajuster les sélecteurs CSS si nécessaire.