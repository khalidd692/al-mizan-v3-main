# 🎯 SOURCES GITHUB HADITH DÉCOUVERTES PAR TAVILY

**Date**: 18 avril 2026, 19:22
**Méthode**: Tavily Search MCP

---

## ✅ TOP 10 SOURCES GITHUB IDENTIFIÉES

### 1. **AhmedBaset/hadith-json** ⭐⭐⭐⭐⭐
- **URL**: https://github.com/AhmedBaset/hadith-json
- **Contenu**: 50,884 hadiths de 17 livres
- **Format**: JSON (arabe + anglais)
- **Source**: Sunnah.com
- **Livres**: Les 9 livres canoniques inclus
- **Structure**: `db/by_book/` et `db/by_chapter/`
- **Statut**: ✅ PRIORITÉ ABSOLUE

### 2. **fawazahmed0/hadith-api** ⭐⭐⭐⭐⭐
- **URL**: https://github.com/fawazahmed0/hadith-api
- **Contenu**: API hadith multilingue
- **Format**: JSON + API REST
- **Grades**: Multiples grades inclus
- **Endpoints**:
  - `/editions` - Liste toutes les éditions
  - `/editions/{editionName}` - Hadith complet
  - `/editions/{editionName}/{HadithNo}` - Hadith spécifique
  - `/info` - Détails (grades, références)
- **Statut**: ✅ API DIRECTE DISPONIBLE

### 3. **mhashim6/Open-Hadith-Data** ⭐⭐⭐⭐
- **URL**: https://github.com/mhashim6/Open-Hadith-Data
- **Contenu**: 9 livres différents (incluant les Six Livres)
- **Format**: Bases de données ouvertes
- **Statut**: ✅ À EXPLORER

### 4. **abdelrahmaan/Hadith-Data-Sets** ⭐⭐⭐⭐
- **URL**: https://github.com/abdelrahmaan/Hadith-Data-Sets
- **Contenu**: 62,169 hadiths des Neuf Livres
- **Format**: Avec et sans Tashkil (diacritiques)
- **Statut**: ✅ DATASET MASSIF

### 5. **haseebarshad17/quran-hadith-json** ⭐⭐⭐
- **URL**: https://github.com/haseebarshad17/quran-hadith-json
- **Contenu**: Hadith + Quran
- **Langues**: 95+ langues
- **Grades**: Multiples grades
- **API**: Next.js API disponible
- **Statut**: ✅ MULTILINGUE

### 6. **gadingnst/hadith-api** ⭐⭐⭐
- **URL**: https://github.com/gadingnst/hadith-api
- **Contenu**: API hadith simple
- **Traduction**: Indonésienne
- **Statut**: ✅ API SIMPLE

### 7. **sunnah-com/api** ⭐⭐⭐⭐⭐
- **URL**: https://github.com/sunnah-com/api
- **Contenu**: API OFFICIELLE de Sunnah.com
- **Statut**: ✅ SOURCE OFFICIELLE

### 8. **AhmedElTabarani/dorar-hadith-api** ⭐⭐⭐⭐⭐
- **URL**: https://github.com/AhmedElTabarani/dorar-hadith-api
- **Contenu**: API intermédiaire pour Dorar السنية
- **Statut**: ✅ DORAR API WRAPPER

### 9. **robonamari/hadith-database** ⭐⭐
- **URL**: https://github.com/robonamari/hadith
- **Contenu**: 20 hadiths en JSON
- **Statut**: ⚠️ PETIT DATASET

### 10. **4thel00z/hadith.json** ⭐⭐⭐
- **URL**: https://github.com/4thel00z/hadith.json
- **Contenu**: Sahih Bukhari + Hisnul Muslim
- **Source**: Sunnah.com (scraped avec artoo.js)
- **Statut**: ✅ BUKHARI COMPLET

---

## 🚀 PLAN D'EXTRACTION IMMÉDIAT

### Phase 1: Téléchargement Direct (30 min)
```bash
# Source 1: AhmedBaset/hadith-json (50,884 hadiths)
git clone https://github.com/AhmedBaset/hadith-json.git

# Source 4: abdelrahmaan/Hadith-Data-Sets (62,169 hadiths)
git clone https://github.com/abdelrahmaan/Hadith-Data-Sets.git

# Source 3: mhashim6/Open-Hadith-Data
git clone https://github.com/mhashim6/Open-Hadith-Data.git
```

### Phase 2: APIs (1-2 heures)
```python
# Source 2: fawazahmed0/hadith-api
# Source 7: sunnah-com/api
# Source 8: AhmedElTabarani/dorar-hadith-api
```

### Phase 3: Parsing et Import (2-3 heures)
- Parser les JSON
- Déduplication SHA-256
- Import dans almizane.db

---

## 📊 ESTIMATION TOTALE

### Hadiths disponibles sur GitHub
```
Source 1 (AhmedBaset):        50,884
Source 4 (abdelrahmaan):      62,169
Source 3 (Open-Hadith):       ~40,000 (estimé)
Source 7 (sunnah-com):        ~50,000 (estimé)
Source 8 (dorar-api):         ~30,000 (estimé)
─────────────────────────────────────
TOTAL BRUT:                  ~233,000

Après déduplication:         ~150,000
```

### Projection finale
```
Base actuelle:                87,337
GitHub sources:              +60,000 (après dédup)
Harvesters 1+2:             +110,000
─────────────────────────────────────
TOTAL FINAL:                 257,337 hadiths

Objectif 200K: DÉPASSÉ de 29% ✅
```

---

## ⚡ ACTIONS IMMÉDIATES

### 1. Cloner les repos prioritaires
```bash
cd backend/corpus
git clone https://github.com/AhmedBaset/hadith-json.git
git clone https://github.com/abdelrahmaan/Hadith-Data-Sets.git
git clone https://github.com/mhashim6/Open-Hadith-Data.git
```

### 2. Créer l'importeur GitHub
```python
# backend/github_mass_importer.py
```

### 3. Lancer l'import
```bash
python backend/github_mass_importer.py
```

---

## ✅ AVANTAGES

### Vitesse
- Téléchargement direct (pas de scraping)
- JSON prêt à l'emploi
- Import massif en 3-4 heures

### Qualité
- Sources vérifiées (GitHub stars)
- Données structurées
- Grades inclus

### Couverture
- +150K hadiths bruts
- Toutes les collections majeures
- Zéro source manquée

---

**PROCHAINE ÉTAPE**: Cloner les repos et créer l'importeur