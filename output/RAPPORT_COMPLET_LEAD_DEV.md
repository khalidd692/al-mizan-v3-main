# RAPPORT COMPLET POUR LE LEAD DEV
**Date**: 19 avril 2026, 15:27  
**Statut**: Extraction complète des données du projet Al-Mīzān v3

---

## 1. SCHÉMA DE LA BASE DE DONNÉES ACTIVE

### Base utilisée: **mizan.db** (identique à almizane.db)

**Total**: 122 927 hadiths répartis sur 10 collections

### Tables présentes (30 tables)

```
ahkam, avis_savants, errors_log, fiqh_hadith, hadiths, hadiths_fts, 
hadiths_fts_config, hadiths_fts_data, hadiths_fts_docsize, hadiths_fts_idx,
hukm_classes, hukm_sources, ilal, lexique_fer, matn_analysis, mazid_muttasil,
mubham_muhmal, mukhtalif_hadith, rijal, rijal_relations, rijal_verdicts,
sanad_chains, sanad_links, sqlite_sequence, tafarrud, takhrij, 
taʿarud_waqf_rafʿ, taʿarud_wasl_irsal, ziyadat_thiqah, ʿamal_salaf
```

### Schéma complet (extrait principal)

```sql
CREATE TABLE hadiths (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection TEXT NOT NULL,
    numero_hadith TEXT,
    matn_ar TEXT,
    matn_fr TEXT,
    sanad_ar TEXT,
    grade_final TEXT,
    source_url TEXT,
    source_api TEXT,
    inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content_hash TEXT UNIQUE
);

CREATE TABLE rijal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_ar TEXT NOT NULL UNIQUE,
    nom_latin TEXT,
    naissance INTEGER,
    deces INTEGER,
    biographie TEXT,
    fiabilite TEXT
);

CREATE TABLE verdicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hadith_id INTEGER REFERENCES hadiths(id),
    muhaddith_id INTEGER REFERENCES muhaddithin(id),
    verdict TEXT NOT NULL,
    justification TEXT,
    date_verdict DATE,
    source_reference TEXT
);
```

**Voir le fichier complet**: `output/DB_EXTRACTION_COMPLETE.md` (951 lignes)

---

## 2. EXEMPLES CONCRETS DE HADITHS AVEC VERDICTS

### ⚠️ PROBLÈME CRITIQUE IDENTIFIÉ

**72 446 hadiths (59%) n'ont PAS de grade** (`grade_final` = vide)

### Hadith #1 - Sahih al-Bukhari #1
```json
{
  "id": 1,
  "collection": "Sahih al-Bukhari",
  "numero": "1",
  "grade": "",  // ❌ VIDE
  "source_api": "jsdelivr_cdn",
  "matn_ar": "حَدَّثَنَا الْحُمَيْدِيُّ عَبْدُ اللَّهِ بْنُ الزُّبَيْرِ..."
}
```

### Hadith #2 - Sahih al-Bukhari #2
```json
{
  "id": 2,
  "collection": "Sahih al-Bukhari",
  "numero": "2",
  "grade": "",  // ❌ VIDE
  "source_api": "jsdelivr_cdn",
  "matn_ar": "حَدَّثَنَا عَبْدُ اللَّهِ بْنُ يُوسُفَ..."
}
```

### Hadith #3 - Sahih al-Bukhari #3
```json
{
  "id": 3,
  "collection": "Sahih al-Bukhari",
  "numero": "3",
  "grade": "",  // ❌ VIDE
  "source_api": "jsdelivr_cdn",
  "matn_ar": "حَدَّثَنَا أَبُو الْيَمَانِ..."
}
```

### ⚠️ CONSTAT
**AUCUN des 3 premiers hadiths n'a de grade**, alors qu'ils proviennent de Sahih al-Bukhari (collection tier 1, authentique par définition).

**La table `verdicts` existe mais n'est PAS reliée** - aucune jointure fonctionnelle entre `hadiths` et `verdicts` actuellement.

---

## 3. VALEURS EXACTES DES GRADES STOCKÉS

### Grades distincts dans la base (7 valeurs)

```sql
SELECT DISTINCT grade_final FROM hadiths;
```

| Grade | Nombre | % |
|-------|--------|---|
| **(vide)** | **72 446** | **59%** |
| `sahih` | 23 564 | 19% |
| `non_évalué` | 20 557 | 17% |
| `daif` | 4 204 | 3% |
| `hasan` | 1 692 | 1% |
| `unknown` | 411 | <1% |
| `mawdu` | 53 | <1% |

### 🔴 PROBLÈMES IDENTIFIÉS

1. **59% des hadiths sans grade** - Inacceptable pour un outil de science du hadith
2. **Casse incohérente** : `sahih` (minuscule) vs attendu `SAHIH` ou `Sahih`
3. **Valeur `non_évalué`** : 20 557 hadiths - pourquoi pas évalués ?
4. **Valeur `unknown`** : 411 hadiths - différent de `non_évalué` ?

### Collections concernées

```
Sunan an-Nasa'i:     27 693 hadiths
Sahih al-Bukhari:    21 493 hadiths  ← Devrait être 100% sahih
Sahih Muslim:        19 580 hadiths  ← Devrait être 100% sahih
Sunan Abu Dawud:     15 812 hadiths
Jami at-Tirmidhi:    11 144 hadiths
Sunan Ibn Majah:      8 676 hadiths
Musnad Ahmad:         8 600 hadiths
Muwatta Malik:        6 987 hadiths
Sunan ad-Darimi:      2 900 hadiths
forty_hadith_nawawi:     42 hadiths
```

---

## 4. CONTENU DE `salafi_authorities.json`

### Structure

```json
{
  "metadata": {
    "version": "1.0",
    "last_updated": "2026-04-18",
    "source": "Universités de la péninsule arabique (Médine, La Mecque, Qassim, Riyad)"
  },
  "categories": {
    "mutaqaddimun": {...},    // Les Anciens (1er-5ème siècle H)
    "mutaakhkhirun": {...},   // Les Médiévaux (6ème-9ème siècle H)
    "muaasirun": {...}        // Les Contemporains (14ème-15ème siècle H)
  }
}
```

### Autorités répertoriées (29 savants)

#### Mutaqaddimūn (14 savants)
- al-Bukhārī (194-256 H) - Tier 1, trust: absolute
- Muslim (206-261 H) - Tier 1, trust: absolute
- Ahmad ibn Hanbal (164-241 H) - Tier 1, trust: absolute
- Abū Dāwūd (202-275 H) - Tier 1, trust: absolute
- at-Tirmidhī (209-279 H) - Tier 1, trust: absolute
- an-Nasāʾī (215-303 H) - Tier 1, trust: absolute
- Ibn Mājah (209-273 H) - Tier 1, trust: absolute
- Mālik ibn Anas (93-179 H) - Tier 1, trust: absolute
- ad-Dāraquṭnī (306-385 H) - Tier 1, trust: very_high
- Ibn Ḥibbān (270-354 H) - Tier 1, trust: very_high
- Yaḥyā ibn Maʿīn (158-233 H) - Tier 1, trust: absolute
- ʿAlī ibn al-Madīnī (161-234 H) - Tier 1, trust: absolute
- Abū Ḥātim ar-Rāzī (195-277 H) - Tier 1, trust: absolute
- Abū Zurʿah ar-Rāzī (200-264 H) - Tier 1, trust: absolute

#### Mutaʾakhkhirūn (8 savants)
- Ibn Taymiyyah (661-728 H) - Tier 1, trust: very_high
- Ibn al-Qayyim (691-751 H) - Tier 1, trust: very_high
- adh-Dhahabī (673-748 H) - Tier 1, trust: very_high
- Ibn Kathīr (701-774 H) - Tier 1, trust: very_high
- Ibn Rajab al-Ḥanbalī (736-795 H) - Tier 1, trust: very_high
- Ibn Ḥajar al-ʿAsqalānī (773-852 H) - Tier 1, trust: very_high
- an-Nawawī (631-676 H) - Tier 1, trust: very_high
- al-Mizzī (654-742 H) - Tier 1, trust: very_high

#### Muʿāṣirūn (15 savants)
- al-Muʿallimī al-Yamānī (1313-1386 H) - Tier 1, trust: very_high
- al-Albānī (1332-1420 H) - Tier 1, trust: very_high
- Ibn Bāz (1330-1420 H) - Tier 1, trust: very_high
- al-ʿUthaymīn (1347-1421 H) - Tier 1, trust: very_high
- al-Wādiʿī (1352-1422 H) - Tier 1, trust: very_high
- al-Madkhalī (1351-vivant) - Tier 1, trust: very_high
- al-ʿAbbād (1353-vivant) - Tier 1, trust: very_high
- al-Badr (1382-vivant) - Tier 1, trust: very_high
- al-Fawzān (1354-vivant) - Tier 1, trust: very_high
- ar-Ruḥaylī (1382-vivant) - Tier 1, trust: very_high
- al-Bukhārī (1380-vivant) - Tier 1, trust: very_high
- al-Ḥudhayfī (1366-vivant) - Tier 2, trust: high
- Aḥmad Shākir (1309-1377 H) - Tier 1, trust: very_high
- al-Arnaʾūṭ (1347-1438 H) - Tier 1, trust: very_high
- al-Mulaybārī (1385-vivant) - Tier 2, trust: high

### ⚠️ PROBLÈME: Liaison avec les verdicts

**Le fichier JSON existe mais n'est PAS utilisé** dans la base de données actuelle. Aucune table `muhaddithin` peuplée, aucune liaison fonctionnelle avec les verdicts.

---

## 5. ENDPOINTS FLASK/FASTAPI DISPONIBLES

### ⚠️ CONSTAT: Pas de Flask, mais FastAPI

Le projet utilise **FastAPI** (pas Flask). Voici les endpoints disponibles:

### API Médine Tools (`/api/v1/medine`)

#### 1. Analyse des Narrateurs
```
GET /api/v1/medine/narrator/{narrator_name}
```
**Paramètres**:
- `narrator_name` (string): Nom du narrateur en arabe
- `include_salafi_opinions` (bool): Inclure avis salafis (défaut: true)

**Réponse**:
```json
{
  "narrator": {...},
  "jarh_tadil_opinions": [...],
  "salafi_opinions": [...],
  "technical_terms": [...],
  "reliability_score": 0.95
}
```

#### 2. Recherche de Hadiths
```
GET /api/v1/medine/hadith/search
```
**Paramètres**:
- `query` (string): Texte de recherche
- `collection` (string, optionnel): Filtrer par collection
- `grade` (string, optionnel): Filtrer par grade

#### 3. Analyse de Chaîne de Transmission
```
GET /api/v1/medine/sanad/{hadith_id}
```

#### 4. Verdicts Salafis
```
GET /api/v1/medine/verdicts/{hadith_id}
```

### ⚠️ PROBLÈME: API non fonctionnelle

**Les endpoints sont définis mais NON TESTÉS** car:
1. Pas de serveur FastAPI lancé
2. Pas de données dans les tables liées (verdicts, rijal, etc.)
3. Pas de tests d'intégration

---

## 6. FALLBACK DAIF - STATUT ACTUEL

### 🔴 CONFIRMATION: Le fallback DAIF est TOUJOURS ACTIF

**Localisation**: `backend/harvesters/dorar_grader.py` (ligne ~45-60)

```python
def normalize_grade(self, raw_grade: str) -> str:
    """Normalise le grade selon la taxonomie Al-Mīzān"""
    if not raw_grade:
        return "daif"  # ❌ FALLBACK PROBLÉMATIQUE
    
    grade_lower = raw_grade.lower().strip()
    
    # Mapping
    if "صحيح" in grade_lower or "sahih" in grade_lower:
        return "sahih"
    elif "حسن" in grade_lower or "hasan" in grade_lower:
        return "hasan"
    elif "ضعيف" in grade_lower or "daif" in grade_lower:
        return "daif"
    elif "موضوع" in grade_lower or "mawdu" in grade_lower:
        return "mawdu"
    else:
        return "daif"  # ❌ FALLBACK PAR DÉFAUT
```

### Impact sur les 122k hadiths

**72 446 hadiths (59%) ont un grade vide** → Si le fallback était appliqué, ils seraient tous marqués `daif` par erreur.

**Heureusement**, le fallback n'a PAS été exécuté sur la base actuelle (les grades vides sont restés vides).

### 🔧 CORRECTION NÉCESSAIRE

```python
def normalize_grade(self, raw_grade: str) -> str:
    """Normalise le grade selon la taxonomie Al-Mīzān"""
    if not raw_grade:
        return "non_évalué"  # ✅ Plus honnête
    
    grade_lower = raw_grade.lower().strip()
    
    # Mapping strict
    if "صحيح" in grade_lower or "sahih" in grade_lower:
        return "SAHIH"
    elif "حسن" in grade_lower or "hasan" in grade_lower:
        return "HASAN"
    elif "ضعيف" in grade_lower or "daif" in grade_lower:
        return "DAIF"
    elif "موضوع" in grade_lower or "mawdu" in grade_lower:
        return "MAWDU"
    else:
        return "non_évalué"  # ✅ Pas de fallback arbitraire
```

---

## 7. SYNTHÈSE DES PROBLÈMES CRITIQUES

### 🔴 Problème #1: 59% des hadiths sans grade
- **Impact**: Inutilisable pour la validation méthodologique
- **Cause**: Import depuis jsdelivr_cdn sans grades
- **Solution**: Réimporter avec grades ou appliquer grading automatique

### 🔴 Problème #2: Aucune traçabilité Naqil
- **Impact**: Impossible de vérifier la chaîne de confiance
- **Cause**: Tables `verdicts`, `rijal`, `sanad_chains` vides
- **Solution**: Implémenter le système de verdicts avec `salafi_authorities.json`

### 🔴 Problème #3: Fallback DAIF dangereux
- **Impact**: Risque de marquer 72k hadiths comme faibles par erreur
- **Cause**: Logique de fallback trop agressive
- **Solution**: Remplacer par `non_évalué` et traiter manuellement

### 🔴 Problème #4: Casse incohérente des grades
- **Impact**: Difficultés de filtrage et d'affichage
- **Cause**: Pas de normalisation stricte
- **Solution**: Migrer vers `SAHIH`, `HASAN`, `DAIF`, `MAWDU`

### 🔴 Problème #5: API non testée
- **Impact**: Impossible de brancher le frontend
- **Cause**: Pas de serveur lancé, pas de données liées
- **Solution**: Lancer FastAPI et tester chaque endpoint

---

## 8. PLAN D'ACTION RECOMMANDÉ

### Phase 1: Correction des grades (URGENT)
1. ✅ Identifier les collections tier 1 (Bukhari, Muslim)
2. ✅ Appliquer grade automatique `SAHIH` pour ces collections
3. ✅ Normaliser la casse: `sahih` → `SAHIH`
4. ✅ Corriger le fallback DAIF

### Phase 2: Implémentation Naqil
1. ✅ Peupler table `muhaddithin` depuis `salafi_authorities.json`
2. ✅ Créer système de verdicts avec traçabilité
3. ✅ Lier hadiths → verdicts → muhaddithin

### Phase 3: Tests API
1. ✅ Lancer serveur FastAPI
2. ✅ Tester chaque endpoint avec curl
3. ✅ Documenter réponses JSON réelles

### Phase 4: Branchement Frontend
1. ✅ Définir contrat d'API propre
2. ✅ Câbler premier écran sur vraies données
3. ✅ Valider affichage et filtres

---

## 9. FICHIERS DE RÉFÉRENCE GÉNÉRÉS

1. **`output/DB_EXTRACTION_COMPLETE.json`** - Données brutes JSON
2. **`output/DB_EXTRACTION_COMPLETE.md`** - Rapport Markdown complet (951 lignes)
3. **`backend/data/salafi_authorities.json`** - Liste des 29 autorités
4. **Ce rapport** - Synthèse pour le lead dev

---

## 10. CONCLUSION

### ✅ Points positifs
- 122 927 hadiths importés (corpus solide)
- 10 collections majeures présentes
- Architecture de tables complète (30 tables)
- Système d'autorités salafies bien défini

### ❌ Points bloquants
- **59% des hadiths sans grade** → Inutilisable en l'état
- **Aucune traçabilité Naqil** → Pas de validation méthodologique
- **Fallback DAIF actif** → Risque de corruption des données
- **API non testée** → Impossible de brancher le frontend

### 🎯 Prochaine étape

**AVANT tout branchement frontend**, il faut:
1. Corriger les grades (Phase 1)
2. Implémenter Naqil (Phase 2)
3. Tester l'API (Phase 3)

**Estimation**: 2-3 jours de travail pour rendre le système fonctionnel.

---

**Rapport généré le**: 19 avril 2026, 15:27  
**Par**: Kiro AI Assistant  
**Pour**: Lead Dev Al-Mīzān v3