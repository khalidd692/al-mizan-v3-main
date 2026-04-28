# Al-Mīzān v5.0 — Moteur de Takhrīj Scientifique

**Phase 1 : Architecture SSE + 4 agents mockés**

**Déploiement en production :** https://al-mizan-v3.onrender.com (Render)

## Vue d'ensemble

Al-Mīzān v5.0 est un moteur de takhrīj (authentification de hadiths) basé sur une architecture multi-agents orchestrée. Cette phase 1 établit l'infrastructure complète avec des données mockées.

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (SSE)                        │
│  Dashboard 3 colonnes : Isnād | Matn | Preuves         │
└─────────────────────────────────────────────────────────┘
                           ↓ SSE
┌─────────────────────────────────────────────────────────┐
│                   ORCHESTRATEUR                          │
│  Pilote 4 agents en parallèle via queue partagée       │
└─────────────────────────────────────────────────────────┘
                           ↓
┌──────────────┬──────────────┬──────────────┬────────────┐
│  Agent 1     │  Agent 2     │  Agent 3     │  Agent 4   │
│  ISNAD       │  ILAL        │  MATN        │  TARJIH    │
│  Zones 2-3   │  Zones 6-8   │  Zones 9-14  │  Zones 15+ │
└──────────────┴──────────────┴──────────────┴────────────┘
```

### Les 4 Agents Spécialisés

1. **Agent ISNAD** : Chaîne de transmission + Jarḥ wa Taʿdīl
2. **Agent ILAL** : ʿIlal cachées, Tafarrud, Munkar
3. **Agent MATN** : Gharīb, Sabab al-Wurūd, Āthār des Salaf
4. **Agent TARJIH** : Ijmāʿ, Khilāf, Mukhtalif, Tarjīḥ final

## Installation

```bash
# 1. Créer l'environnement virtuel
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env et ajouter votre ANTHROPIC_API_KEY
```

## Lancement

```bash
# Démarrer le serveur
uvicorn backend.main:app --reload --port 8000

# Ouvrir dans le navigateur
http://localhost:8000
```

## Tests

```bash
pytest tests/ -v
```

## Structure du Projet

```
al-mizan-v5/
├── backend/
│   ├── agents/          # 4 agents spécialisés
│   │   ├── prompts/     # Prompts (à rédiger phase 2)
│   │   ├── base.py
│   │   ├── agent_isnad.py
│   │   ├── agent_ilal.py
│   │   ├── agent_matn.py
│   │   └── agent_tarjih.py
│   ├── utils/           # SSE, logging, constitution
│   ├── corpus/          # Chargeur corpus (phase 2)
│   ├── dorar/           # Client Dorar.net (phase 2)
│   ├── orchestrator.py  # Pipeline principal
│   └── main.py          # Point d'entrée Starlette
├── frontend/
│   ├── css/             # Styles (base, dashboard, isnad-tree)
│   ├── js/              # SSE client, dashboard, isnad-tree
│   └── index.html
├── tests/
│   └── test_orchestrator.py
├── requirements.txt
├── .env.example
└── README.md
```

## Phase 1 : Objectifs ✓

- [x] Architecture SSE complète
- [x] 4 agents mockés en parallèle
- [x] Dashboard 3 colonnes fonctionnel
- [x] Arbre d'Isnād vertical
- [x] Pipeline des 32 zones
- [x] Tests de base

## Phase 2 : Prochaines Étapes

1. Intégration du corpus réel (PostgreSQL)
2. Rédaction des prompts des 4 agents
3. Connexion API Anthropic
4. Client Dorar.net
5. Traduction FR→AR
6. Tests d'intégration complets

## Licence

Projet académique — Al-Mīzān Research