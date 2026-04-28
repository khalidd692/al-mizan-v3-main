# 🕋 SOURCES HADITH - RÉFÉRENTIEL COMPLET

**Date:** 18 avril 2026, 05:00 AM  
**Projet:** Al-Mīzān v7.0  
**Objectif:** Harvesting massif corpus hadith authentique

---

## 📊 TIER 1 — SOURCES OFFICIELLES DE MÉDINE

### 🟢 Priorité Maximale (Méthodologie Salaf)

| Source | URL | Type | Statut |
|--------|-----|------|--------|
| **Dorar.net** | https://dorar.net/dorar_api.json | API JSONP | ✅ Testé |
| **HadeethEnc** | https://hadeethenc.com/api/v1 | API REST | ✅ Testé |
| **IslamWeb Hadith** | https://library.islamweb.net/hadith | Web | 🔄 À tester |
| **IslamWeb Hadith 2** | https://hadith.islamweb.net | Web | 🔄 À tester |
| **Université Oum Al-Qura** | https://uqu.edu.sa | Bibliothèque | 🔄 À tester |
| **Université Islamique Médine** | https://iu.edu.sa | Maktaba | 🔄 À tester |
| **Bibliothèque IUM** | https://lib.iu.edu.sa | Numérique | 🔄 À tester |

### 📝 Notes Tier 1
- **Dorar.net:** API JSONP fonctionnelle, mais retourne HTML (60% métadonnées manquantes)
- **HadeethEnc:** API REST JSON structuré, 100% métadonnées, recommandé pour production
- **IslamWeb:** Sources officielles, à explorer pour APIs
- **Universités:** Sources académiques de référence, authentification possible

---

## 📚 TIER 2 — BIBLIOTHÈQUES NUMÉRIQUES SALAFI

### 🟡 Haute Priorité (Corpus Complet)

| Source | URL | Description | Statut |
|--------|-----|-------------|--------|
| **Shamela** | https://shamela.ws | المكتبة الشاملة - TOUT le corpus | 🔄 À tester |
| **Al-Maktaba** | https://al-maktaba.org | Tous livres hadith | 🔄 À tester |
| **Waqfeya** | https://waqfeya.net | مكتبة الوقفية | 🔄 À tester |
| **Archive.org** | https://archive.org | Manuscrits Médine | 🔄 À tester |
| **IEF Pedia** | https://iefpedia.com | Encyclopédie | 🔄 À tester |
| **Saaid.net** | https://saaid.net | Bibliothèque salafi | 🔄 À tester |
| **Al-Manhaj** | https://almanhaj.net | Méthodologie salafi | 🔄 À tester |
| **IslamWay** | https://ar.islamway.net | Hadiths uniquement | 🔄 À tester |

### 📝 Notes Tier 2
- **Shamela:** Bibliothèque la plus complète, potentiel énorme
- **Al-Maktaba:** Spécialisée livres hadith, qualité académique
- **Archive.org:** Manuscrits originaux, nécessite OCR/parsing
- **Sources salafi:** Conformité méthodologique garantie

---

## 🔌 TIER 3 — APIs ET SOURCES STRUCTURÉES

### 🟢 APIs REST Disponibles

| Source | URL | Collections | Statut |
|--------|-----|-------------|--------|
| **Sunnah.com** | https://sunnah.com/api | Toutes collections | 🔄 À tester |
| **Sunnah Intranet** | https://hadith.intranet.sunnah.com/api | Toutes collections | 🔄 À tester |
| **QuranHadith** | https://quranhadith.com/api | Multi-sources | 🔄 À tester |
| **Hadith Gading** | https://api.hadith.gading.dev | Toutes collections | 🔄 À tester |
| **Random Hadith** | https://random-hadith-generator.vercel.app | Aléatoire | 🔄 À tester |
| **CDN JSDelivr** | https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api | GitHub API | 🔄 À tester |

### 📝 Notes Tier 3
- **Sunnah.com:** API officielle, documentation complète
- **APIs GitHub:** Open source, facilement intégrables
- **CDN:** Haute disponibilité, pas de rate limiting

---

## 🎯 STRATÉGIE DE HARVESTING

### Phase 1: Validation des Sources (En cours)
- ✅ Dorar.net: Parser HTML créé
- ✅ HadeethEnc: API testée et validée
- 🔄 Tester les 5 APIs Tier 3 les plus prometteuses
- 🔄 Explorer Shamela.ws (corpus complet)

### Phase 2: Sélection des Sources Primaires
**Critères de sélection:**
1. Format JSON structuré (priorité)
2. Métadonnées complètes (narrateur, grade, source)
3. Conformité méthodologie Salaf
4. Disponibilité et stabilité API
5. Rate limiting acceptable

**Sources recommandées:**
1. **HadeethEnc** (production principale)
2. **Sunnah.com API** (complément)
3. **Hadith Gading API** (backup)
4. **Dorar.net** (validation croisée)

### Phase 3: Harvesting Massif
**Objectif:** 50,000+ hadiths authentiques

**Répartition:**
- HadeethEnc: 30,000 hadiths (base)
- Sunnah.com: 15,000 hadiths (complément)
- Autres APIs: 5,000 hadiths (diversification)
- Validation: Dorar.net (croisement)

### Phase 4: Validation et Déduplication
1. Détection des doublons (texte + chaîne)
2. Validation grades (conformité Salaf)
3. Vérification chaînes de transmission
4. Enrichissement métadonnées

---

## 🔍 TESTS À EFFECTUER

### Tests Prioritaires (Tier 3 APIs)

#### 1. Sunnah.com API
```bash
curl https://sunnah.com/api/v1/collections
curl https://sunnah.com/api/v1/hadiths/bukhari/1
```

#### 2. Hadith Gading API
```bash
curl https://api.hadith.gading.dev/books
curl https://api.hadith.gading.dev/books/bukhari?range=1-10
```

#### 3. CDN JSDelivr (GitHub)
```bash
curl https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions.json
curl https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/ara-bukhari.json
```

#### 4. QuranHadith API
```bash
curl https://quranhadith.com/api/hadith
```

#### 5. Random Hadith Generator
```bash
curl https://random-hadith-generator.vercel.app/api/hadiths
```

### Tests Secondaires (Tier 2 Web)

#### 1. Shamela.ws
- Explorer structure du site
- Identifier endpoints API potentiels
- Tester scraping si nécessaire

#### 2. IslamWeb
```bash
curl https://library.islamweb.net/hadith/api
curl https://hadith.islamweb.net/api
```

---

## 📋 CHECKLIST VALIDATION SOURCE

Pour chaque source testée, valider:

- [ ] **Accessibilité:** API/site accessible sans authentification
- [ ] **Format:** JSON structuré ou HTML parsable
- [ ] **Métadonnées:** Texte, narrateur, grade, source, chaîne
- [ ] **Volume:** Nombre de hadiths disponibles
- [ ] **Qualité:** Conformité méthodologie Salaf
- [ ] **Performance:** Temps de réponse < 2s
- [ ] **Rate Limiting:** Limite acceptable (>100 req/min)
- [ ] **Documentation:** API documentée
- [ ] **Stabilité:** Disponibilité >99%
- [ ] **Licence:** Utilisation autorisée

---

## 🎯 OBJECTIFS FINAUX

### Court Terme (7 jours)
- ✅ Dorar.net: Parser HTML opérationnel
- ✅ HadeethEnc: API validée
- 🔄 Tester 5 APIs Tier 3
- 🔄 Sélectionner 3 sources primaires
- 🔄 Extraction test 1,000 hadiths

### Moyen Terme (30 jours)
- 🔄 Harvesting 10,000 hadiths (sources multiples)
- 🔄 Validation croisée Dorar/HadeethEnc
- 🔄 Déduplication et enrichissement
- 🔄 Intégration base v7

### Long Terme (90 jours)
- 🔄 Harvesting 50,000+ hadiths
- 🔄 Couverture Kutub Sittah complète
- 🔄 Validation méthodologie Salaf
- 🔄 Production Al-Mīzān v7.0

---

## 📊 MÉTRIQUES DE SUCCÈS

| Métrique | Objectif | Actuel | Statut |
|----------|----------|--------|--------|
| **Sources testées** | 10 | 2 | 🔄 20% |
| **APIs validées** | 5 | 1 | 🔄 20% |
| **Hadiths base** | 50,000 | 1,900 | 🔄 4% |
| **Taux Sahih** | >80% | 91.8% | ✅ 115% |
| **Métadonnées complètes** | >90% | 100% | ✅ 111% |
| **Conformité Salaf** | 100% | 100% | ✅ 100% |

---

## 🔗 RESSOURCES

### Documentation APIs
- HadeethEnc: https://documenter.getpostman.com/view/5211979/TVev3j7q
- Sunnah.com: https://sunnah.com/about
- Hadith Gading: https://github.com/gadingnst/hadith-api

### Outils Développés
- `backend/dorar_html_parser.py` - Parser Dorar.net
- `backend/test_hadeethenc_api.py` - Tests HadeethEnc
- `backend/test_dorar_jsonp.py` - Tests Dorar JSONP
- `backend/harvester_hadeethenc.py` - Harvester HadeethEnc

---

**Prochaine étape:** Tester les 5 APIs Tier 3 prioritaires et sélectionner les 3 sources primaires pour le harvesting massif.