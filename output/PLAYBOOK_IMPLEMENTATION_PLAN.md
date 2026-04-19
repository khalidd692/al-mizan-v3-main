# 📋 PLAN D'IMPLÉMENTATION — PLAYBOOK FINAL REMPLISSAGE 40 ZONES

> **Date**: 19 avril 2026, 00:58
> **Statut**: Analyse du playbook et création du plan d'action
> **Base actuelle**: mizan.db avec 80 imams seedés, structure complète

---

## 🎯 OBJECTIF GLOBAL

Passer de "structure vide" à "base entièrement peuplée" selon la méthodologie complète des muḥaddithīn classiques et contemporains pour les **122 927 hadiths** actuellement en base.

---

## 📊 ÉTAT ACTUEL DE LA BASE

### Base de données: `backend/mizan.db`

**Tables existantes:**
- ✅ `hadiths` - Structure complète avec colonnes vérificateur
- ✅ `hukm_sources` - 80 imams seedés (classiques + contemporains)
- ✅ `ahkam` - Prête pour verdicts
- ✅ `rijal` - Prête pour narrateurs
- ✅ `rijal_verdicts` - Prête pour jarḥ/taʿdīl
- ✅ `sanad_chains` - Prête pour chaînes
- ✅ `sanad_links` - Prête pour maillons
- ✅ `takhrij` - Prête pour références croisées
- ✅ `ilal` - Prête pour défauts
- ✅ `matn_analysis` - Prête pour analyse textuelle
- ✅ `fiqh_hadith` - Prête pour fiqh
- ✅ `ziyadat_thiqah` - Prête pour ajouts de narrateurs fiables
- ✅ `taʿarud_wasl_irsal` - Prête pour contradictions waṣl/irsāl
- ✅ `taʿarud_waqf_rafʿ` - Prête pour contradictions waqf/rafʿ
- ✅ `mubham_muhmal` - Prête pour narrateurs ambigus
- ✅ `mazid_muttasil` - Prête pour maillons ajoutés
- ✅ `tafarrud` - Prête pour isolements
- ✅ `ʿamal_salaf` - Prête pour pratique des prédécesseurs
- ✅ `mukhtalif_hadith` - Prête pour contradictions apparentes

**Imams disponibles:** 80 (40 classiques + 40 contemporains)

---

## 🚀 PLAN D'EXÉCUTION EN 6 PHASES

### ⚠️ PHASE 0 — TAXONOMIE COMPLÈTE (CRITIQUE)

**Durée**: 1 jour  
**Priorité**: BLOQUANTE

#### Actions:
1. ✅ Créer `backend/migrations/004_complete_hukm_enum.sql`
2. ✅ Implémenter les 25 classes de ḥukm (pas seulement 3!)
3. ✅ Créer table `hukm_classes` avec métadonnées complètes
4. ✅ Ajouter contraintes et index

**Classes à implémenter:**

**MAQBŪL (Acceptés):**
- sahih_li_dhatihi, sahih_li_ghayrihi
- hasan_li_dhatihi, hasan_li_ghayrihi
- hasan_sahih, maskut_ʿanh_abu_dawud

**MARDŪD (Rejetés):**
- daif, daif_jiddan
- munqatiʿ, mursal, muʿallaq, muʿdal, mudallas
- munkar, shadhdh, matruk, mawduʿ, la_asla_lah, batil
- muʿallal, mudraj, maqlub, mudtarib, musahhaf, muharraf, mazid_muttasil
- majhul_al_ʿayn, majhul_al_hal

**TYPOLOGIE:**
- mutawatir, mashhur, ʿaziz, gharib

**META:**
- mukhtalaf_fih, tawaqquf, lam_yuhaqqaq

---

### 📈 PHASE 1 — RAPPORT DE COUVERTURE INITIAL

**Durée**: 1 jour  
**Priorité**: HAUTE

#### Actions:
1. ✅ Créer `backend/scripts/coverage_report.py`
2. ✅ Mesurer l'état actuel des 40 zones
3. ✅ Générer rapport baseline
4. ✅ Archiver dans `output/coverage_baseline_$(date).txt`

**Métriques à mesurer:**
- Hadiths couverts par zone (0-40)
- Pourcentage de couverture
- Nombre de verdicts par imam
- Distribution des classes de ḥukm

---

### 🌐 PHASE 2 — HARVESTER DORAR.NET COMPLET

**Durée**: 8-15 jours (automatisé)  
**Priorité**: CRITIQUE (source principale)

#### Étapes:

**2.1 Inspection API** (1 jour)
```bash
curl -H "User-Agent: Mizan-Research/1.0" \
     "https://dorar.net/dorar_api.json?skey=..." \
     | python -m json.tool
```

**2.2 Développement harvester** (2 jours)
- ✅ Créer `backend/harvesters/dorar_complete.py`
- ✅ Implémenter normalisation des 25 classes
- ✅ Système de cache intelligent
- ✅ Rate limiting (1.5s entre requêtes)
- ✅ Gestion des erreurs et reprise

**2.3 Exécution par lots** (8-15 jours)
```bash
# Test sur 10 hadiths
BATCH_SIZE=10 python backend/harvesters/dorar_complete.py

# Production avec boucle automatique
while true; do
  python backend/harvesters/dorar_complete.py
  REMAINING=$(sqlite3 backend/mizan.db "SELECT COUNT(*) FROM hadiths h LEFT JOIN ahkam a ON a.hadith_id=h.id WHERE a.id IS NULL;")
  [ "$REMAINING" = "0" ] && break
  sleep 30
done
```

**Résultat attendu:**
- ≥80% des 122K hadiths avec verdicts
- Distribution: ~50% sahih/hasan, ~40% daif, ~10% mawduʿ/matruk

---

### 📚 PHASE 3 — IMPORT RIJĀL (NARRATEURS)

**Durée**: 5-7 jours  
**Priorité**: HAUTE

#### Sources:
1. **Tahdhīb al-Kamāl** (al-Mizzī) - 8000 rāwī
2. **Taqrīb al-Tahdhīb** (Ibn Ḥajar) - grades résumés
3. **Mīzān al-Iʿtidāl** (al-Dhahabī) - narrateurs faibles
4. **al-Kāmil fī al-Ḍuʿafāʾ** (Ibn ʿAdī)

#### Actions:
1. ✅ Créer `backend/harvesters/shamela_rijal.py`
2. ✅ Parser les biographies depuis Shamela
3. ✅ Extraire: nom, kunyah, dates, jarḥ/taʿdīl
4. ✅ Peupler `rijal` et `rijal_verdicts`

**Résultat attendu:**
- ≥8000 rāwī dans `rijal`
- ≥40000 verdicts dans `rijal_verdicts`

---

### ⛓️ PHASE 4 — EXTRACTION ET CHAÎNAGE DES SANADS

**Durée**: 3-5 jours  
**Priorité**: HAUTE

#### Actions:
1. ✅ Créer `backend/scripts/extract_sanads.py`
2. ✅ Parser les `isnad_ar` de chaque hadith
3. ✅ Détecter les ṣīghāt al-adāʾ (حدثنا، أخبرنا، عن...)
4. ✅ Fuzzy matching avec table `rijal`
5. ✅ Peupler `sanad_chains` et `sanad_links`

**Résultat attendu:**
- ≥50% des hadiths avec sanad complet
- Chaque maillon relié à un rāwī identifié

---

### 🧩 PHASE 5 — TAKHRĪJ CROISÉ

**Durée**: 2-3 jours  
**Priorité**: MOYENNE

#### Actions:
1. ✅ Créer `backend/scripts/build_takhrij.py`
2. ✅ Utiliser FTS5 pour similarité textuelle
3. ✅ Classifier: same / riwāyah / mutābaʿah / shāhid
4. ✅ Peupler table `takhrij`

**Résultat attendu:**
- ≥40% des hadiths avec références croisées
- Identification des mutābaʿāt et shawāhid

---

### 🔬 PHASE 6 — DÉTECTION ʿILAL ET ENRICHISSEMENTS

**Durée**: 5-7 jours  
**Priorité**: MOYENNE-HAUTE

#### 6.1 ʿIlal ẓāhirah (défauts évidents)
```python
# backend/scripts/detect_ilal_zahirah.py
- Détecter ittiṣāl (continuité)
- Détecter tadlīs (mudallisīn connus)
- Détecter ikhtilāṭ (confusion mentale)
- Détecter majhūl (inconnus)
```

#### 6.2 Silsilas d'al-Albānī
```python
# backend/harvesters/albani_silsilas.py
- Silsilat al-Ṣaḥīḥah (4035 hadiths)
- al-Ḍaʿīfah wa al-Mawḍūʿah (7153 hadiths)
```

#### 6.3 ʿIlal al-Dāraqutnī
```python
# backend/harvesters/daraqutni_ilal.py
- Parser les ʿilal khafiyyah
- Extraire taʿāruḍ waṣl/irsāl
- Extraire taʿāruḍ waqf/rafʿ
```

#### 6.4 Mawḍūʿāt (forgeries)
```python
# backend/harvesters/mawduaat.py
Sources:
- al-Mawḍūʿāt (Ibn al-Jawzī)
- Tanzīh al-Sharīʿah (Ibn ʿArrāq)
- al-Laʾāliʾ al-Maṣnūʿah (al-Suyūṭī)
```

#### 6.5 ʿAmal al-Salaf
```python
# backend/harvesters/amal_salaf.py
Sources:
- Muṣannaf Ibn Abī Shaybah
- Muṣannaf ʿAbd al-Razzāq
```

---

## 🎯 CONSOLIDATION FINALE

**Durée**: 1 jour  
**Priorité**: CRITIQUE

```bash
python backend/scripts/consolidate_grades_v2.py
```

**Algorithme:**
1. Pour chaque hadith
2. Collecter tous les verdicts (ahkam)
3. Appliquer pondération par imam (tabaqah, manhaj)
4. Calculer grade_synthese
5. Calculer grade_confidence
6. Mettre à jour hadiths.grade_synthese

---

## 🧪 TESTS CLASSIQUES (T1-T8)

**Durée**: 1 jour  
**Priorité**: HAUTE

```python
# backend/tests/test_classical_hadiths.py

T1: "إنما الأعمال بالنيات" → mashhur/sahih
T2: "من كذب علي متعمدا" → mutawatir/sahih
T3: "طلب العلم فريضة" → mukhtalaf_fih
T4: "حب الوطن من الإيمان" → mawduʿ
T5-T8: Cas techniques (tadlīs, iḍṭirāb, etc.)
```

---

## 📊 CRITÈRES DE SUCCÈS

### Couverture minimale par zone:

| Zone | Nom | Objectif |
|------|-----|----------|
| 28 | Ḥukm Mīzān | ≥80% |
| 29 | Verdicts classiques | ≥60% (3+ verdicts) |
| 30 | Verdicts contemporains | ≥70% (1+ verdict) |
| 13 | Rijāl | ≥8000 rāwī |
| 6-12 | Sanad | ≥50% chaînés |
| 1-5 | Takhrīj | ≥40% références |
| 19-23 | ʿIlal | ≥15000 défauts |

### Distribution des 25 classes:
- Toutes les classes avec ≥100 hadiths
- Distribution réaliste (pas 100% sahih!)

### Tests:
- 8/8 tests classiques passés

---

## ⚠️ RÈGLES ABSOLUES

### ❌ NE JAMAIS:
1. Supprimer des hadiths (même mawḍūʿ)
2. Réduire à 3 classes (sahih/hasan/daif)
3. Inventer des verdicts
4. Confondre les ṭabaqāt
5. Écraser les verdicts contradictoires
6. Appliquer jarḥ sur les ṣaḥābah
7. Fusionner les riwāyāt différentes

### ✅ TOUJOURS:
1. Tracer chaque verdict à sa source
2. Afficher toutes les divergences
3. Utiliser la terminologie classique exacte
4. Respecter la chronologie des imams
5. Conserver tous les avis (même minoritaires)

---

## 📅 PLANNING GLOBAL

```
Semaine 1: Phase 0, 1, 2 (début)
  → Taxonomie + Dorar lancé

Semaine 2: Phase 2 (suite)
  → Dorar continue (~10K/jour)

Semaine 3: Phase 3, 4
  → Rijāl + Sanads

Semaine 4: Phase 5, 6
  → Takhrīj + ʿIlal + Enrichissements

Semaine 5: Consolidation + Tests
  → Grade final + Validation

Semaine 6: Frontend (brief séparé)
  → Interface utilisateur
```

---

## 🔄 PROCHAINES ACTIONS IMMÉDIATES

### Action 1: Migration taxonomie (BLOQUANT)
```bash
python backend/migrations/004_complete_hukm_enum.sql
```

### Action 2: Rapport baseline
```bash
python backend/scripts/coverage_report.py > output/coverage_baseline.txt
```

### Action 3: Test Dorar API
```bash
curl -H "User-Agent: Mizan-Research/1.0" \
     "https://dorar.net/dorar_api.json?skey=إنما+الأعمال+بالنيات" \
     | python -m json.tool
```

### Action 4: Développer harvester Dorar
```bash
# Créer backend/harvesters/dorar_complete.py
# Test sur 10 hadiths
# Validation structure
```

---

## 📝 NOTES IMPORTANTES

1. **Respect du serveur**: Rate limiting strict (1.5s entre requêtes)
2. **Cache intelligent**: Éviter requêtes dupliquées
3. **Reprise automatique**: En cas d'interruption
4. **Logs détaillés**: Pour debugging et audit
5. **Validation continue**: Quality gates après chaque lot

---

## 🤲 PHILOSOPHIE

> *Que ferait Yaḥyā ibn Maʿīn ?*  
> *Que dirait l'imam al-Dāraqutnī ?*  
> *Al-Albānī mettrait-il son nom en bas de cette sortie ?*

Si la réponse est "non" ou "je ne sais pas", **s'arrêter et vérifier**.

---

**Wa-llāhu al-muwaffiq li-mā yuḥibbu wa yarḍā, wa ʿalayhi al-tuklān.**

---

*Généré le: 19 avril 2026, 00:58*  
*Base: mizan.db (122 927 hadiths, 80 imams)*  
*Statut: Plan d'action prêt pour exécution*