# 📋 Plan d'Action Complet - Ressources Salafies (14 Siècles)

**Date**: 19 avril 2026, 02:01 AM  
**Projet**: Al-Mīzān v7.0  
**Objectif**: Intégration exhaustive de toutes les ressources salafies contemporaines et classiques

---

## ✅ RESSOURCES DÉJÀ INTÉGRÉES

### 1. Dorar.net (PRIORITÉ 1)
- **Statut**: ✅ Opérationnel, extraction en cours
- **Script**: `backend/dorar_massive_harvester.py`
- **Contenu**: Kutub al-Sittah, Musnad Ahmad, Muwatta Malik, Riyad al-Salihin, œuvres d'Al-Albani
- **Estimation**: 75,000+ hadiths

### 2. HadeethEnc API
- **Statut**: ✅ Opérationnel, extraction automatisée
- **Script**: `backend/harvester_hadeethenc.py`
- **Contenu**: Corpus authentique, métadonnées complètes
- **Estimation**: 30,000+ hadiths

---

## 🔄 RESSOURCES PRÊTES À INTÉGRER

### 3. Maktabah Shamela (المكتبة الشاملة)
- **Statut**: ⏳ Connecteur prêt, extraction à lancer
- **Script**: `backend/connectors/shamela_connector.py`
- **Action**: Développer `backend/shamela_parser.py`
- **Contenu**: 10,000+ livres, tous recueils majeurs
- **Estimation**: 50,000+ hadiths

### 4. Islamweb.net
- **Statut**: ⏳ Connecteur prêt, extraction à lancer
- **Script**: `backend/connectors/islamweb_connector.py`
- **Contenu**: Bibliothèque de hadiths, fatawa
- **Estimation**: 15,000+ hadiths

### 5. Hadith Gading API
- **Statut**: ⏳ Connecteur prêt, à tester
- **Script**: `backend/connectors/hadith_gading_connector.py`
- **Action**: Tester avec `backend/test_apis_tier3.py`
- **Estimation**: 20,000+ hadiths

### 6. JSDelivr Hadith API (GitHub)
- **Statut**: ⏳ Connecteur prêt, à tester
- **Script**: `backend/connectors/jsdelivr_connector.py`
- **Action**: Tester avec `backend/test_apis_tier3.py`
- **Estimation**: 15,000+ hadiths

---

## 📝 RESSOURCES À DÉVELOPPER

### 7. Université Islamique de Médine
- **Statut**: 🔨 À développer
- **Script à créer**: `backend/medina_library_harvester.py`
- **Contenu**: Manuscrits, thèses, recherches des savants salafis
- **Estimation**: 20,000+ hadiths avec analyses

### 8. Sunnah.com API
- **Statut**: 🔨 À développer
- **Action**: Créer harvester dédié
- **Contenu**: Toutes collections majeures
- **Estimation**: 25,000+ hadiths

### 9. QuranHadith API
- **Statut**: 🔨 À tester et développer
- **Action**: Tester accessibilité et structure
- **Estimation**: 10,000+ hadiths

### 10. Portails salafis (Saaid.net, Alukah.net, Al-Manhaj.net)
- **Statut**: 🔨 À développer
- **Script à créer**: `backend/salafi_aggregator.py`
- **Contenu**: Articles, recherches, bibliothèques salafies
- **Estimation**: 30,000+ hadiths

### 11. Autres sources (Al-Maktaba.org, Waqfeya.net, Archive.org, IslamWay, IEF Pedia)
- **Statut**: 🔨 À développer
- **Action**: Créer harvesters spécifiques
- **Estimation**: 20,000+ hadiths

---

## 🎯 PLAN D'EXÉCUTION

### Phase 1: Tests et Validation (Immédiat)
```bash
# Tester les APIs Tier 3
python backend/test_apis_tier3.py

# Vérifier l'état actuel de la base
python rapport_complet_db.py
```

### Phase 2: Extraction Massive (Court Terme - 7 jours)
```bash
# Lancer Dorar (si pas déjà en cours)
python backend/dorar_massive_harvester.py

# Lancer HadeethEnc
python backend/harvester_hadeethenc.py

# Développer et lancer Shamela
python backend/shamela_parser.py

# Développer et lancer Islamweb
python backend/islamweb_harvester.py
```

### Phase 3: Intégration APIs (Moyen Terme - 14 jours)
```bash
# Tester et intégrer Hadith Gading
python backend/hadith_gading_harvester.py

# Tester et intégrer JSDelivr
python backend/jsdelivr_harvester.py

# Développer et intégrer Sunnah.com
python backend/sunnah_harvester.py
```

### Phase 4: Sources Académiques (Long Terme - 30 jours)
```bash
# Développer et lancer Médine
python backend/medina_library_harvester.py

# Développer et lancer agrégateur salafi
python backend/salafi_aggregator.py
```

### Phase 5: Validation et Déduplication (Continu)
```bash
# Éviter les doublons
python backend/smart_import_no_duplicates.py

# Valider conformité salafie
python backend/corpus_validator.py

# Consolider les grades
python backend/scripts/consolidate_grades.py

# Rapport final
python audit_complet_122k.py
```

---

## 📊 PROJECTION TOTALE

| Source | Hadiths | Statut | Priorité |
|--------|---------|--------|----------|
| Dorar.net | 75,000+ | ✅ En cours | 1 |
| HadeethEnc | 30,000+ | ✅ Opérationnel | 1 |
| Shamela.ws | 50,000+ | ⏳ À développer | 2 |
| Islamweb.net | 15,000+ | ⏳ À développer | 2 |
| Hadith Gading | 20,000+ | ⏳ À tester | 2 |
| JSDelivr | 15,000+ | ⏳ À tester | 2 |
| Médine | 20,000+ | 🔨 À développer | 3 |
| Sunnah.com | 25,000+ | 🔨 À développer | 3 |
| QuranHadith | 10,000+ | 🔨 À développer | 3 |
| Portails salafis | 30,000+ | 🔨 À développer | 4 |
| Autres sources | 20,000+ | 🔨 À développer | 4 |
| **TOTAL** | **310,000+** | **207% objectif** | - |

---

## 🔧 OUTILS ET SCRIPTS

### Déjà Créés ✅
- `backend/dorar_massive_harvester.py`
- `backend/harvester_hadeethenc.py`
- `backend/connectors/shamela_connector.py`
- `backend/connectors/islamweb_connector.py`
- `backend/connectors/hadith_gading_connector.py`
- `backend/connectors/jsdelivr_connector.py`
- `backend/smart_import_no_duplicates.py`
- `backend/corpus_validator.py`
- `backend/scripts/consolidate_grades.py`

### À Créer 🔨
- `backend/shamela_parser.py`
- `backend/medina_library_harvester.py`
- `backend/salafi_aggregator.py`
- `backend/sunnah_harvester.py`
- `backend/quranhadith_harvester.py`

---

## 🎯 CRITÈRES DE SUCCÈS

### Authenticité (Méthodologie Salafie)
- ✅ Chaîne de transmission (isnad) complète
- ✅ Narrateurs authentifiés (thiqat)
- ✅ Pas de contradictions avec Coran/Sunnah
- ✅ Validation par savants salafis reconnus

### Qualité
- ✅ Métadonnées complètes (>90%)
- ✅ Taux Sahih élevé (>80%)
- ✅ Conformité salafie (100%)
- ✅ Zéro doublons

### Exhaustivité
- ✅ Kutub al-Sittah complets
- ✅ Musnad Ahmad complet
- ✅ Œuvres d'Al-Albani complètes
- ✅ Recherches des savants de Médine
- ✅ Couverture 14 siècles

---

## 📝 PROCHAINES ACTIONS IMMÉDIATES

1. **Tester les APIs Tier 3** (aujourd'hui)
   ```bash
   python backend/test_apis_tier3.py
   ```

2. **Vérifier l'état de la base** (aujourd'hui)
   ```bash
   python rapport_complet_db.py
   ```

3. **Développer shamela_parser.py** (cette semaine)

4. **Lancer extraction massive** (cette semaine)

5. **Valider et dédupliquer** (continu)

---

## 🌟 AVANTAGES DE CETTE APPROCHE

1. **Exhaustivité**: Toutes les sources salafies majeures (14 siècles)
2. **Authenticité**: Focus strict sur méthodologie salafie
3. **Gratuité**: Toutes les sources sont libres d'accès
4. **Qualité**: Validation par savants reconnus
5. **Complétude**: Dépasse largement l'objectif initial (207%)
6. **Modernité**: Intégration des APIs et bases de données contemporaines
7. **Académique**: Inclusion des recherches universitaires (Médine)

---

**Document sauvegardé**: `output/PLAN_ACTION_RESSOURCES_SALAFIES_COMPLETE.md`  
**Dernière mise à jour**: 19 avril 2026, 02:01 AM