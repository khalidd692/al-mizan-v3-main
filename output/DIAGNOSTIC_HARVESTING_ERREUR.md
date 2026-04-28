# 🚨 DIAGNOSTIC HARVESTING — ERREUR CRITIQUE

**Date:** 2026-04-18 04:46 AM  
**Statut:** ❌ PROCESSUS ARRÊTÉ

---

## 🔍 PROBLÈME IDENTIFIÉ

### Erreur Principale
```
'str' object has no attribute 'get'
```

### Cause Racine
1. **Incompatibilité de schéma**
   - `massive_corpus_harvester.py` utilise table `hadiths` (v5)
   - Base de données actuelle utilise table `entries` (v7)

2. **Erreur de parsing API**
   - La réponse de l'API Dorar retourne probablement une string d'erreur
   - Le code tente d'appeler `.get()` sur cette string au lieu d'un dict

3. **Boucle infinie d'erreurs**
   - Le harvester retry sans fin sur la même erreur
   - Logs montrent erreurs répétées toutes les 2-3 secondes

---

## 📊 ÉTAT ACTUEL DE LA BASE

### Données Existantes
- **Total entries:** 1,900 hadiths
- **Sahih:** 1,744 (91.8%)
- **Hasan:** 156 (8.2%)
- **Source:** Probablement extraction précédente réussie

### Architecture v7
```sql
Table: entries
- entry_id (PRIMARY KEY)
- entry_type (hadith/fatwa/aqida)
- matn_ar, matn_fr
- grade_primary, grade_secondary
- source_id (FK vers sources)
- created_at, updated_at
```

---

## ✅ SOLUTION REQUISE

### 1. Créer Nouveau Harvester v7
- Compatible avec table `entries`
- Gestion d'erreurs robuste
- Validation des réponses API avant parsing

### 2. Améliorer Connecteur Dorar
- Vérifier type de réponse (dict vs string)
- Logging détaillé des erreurs API
- Fallback gracieux en cas d'échec

### 3. Tests Avant Production
- Test sur 10 hadiths
- Validation insertion dans `entries`
- Vérification grades et sources

---

## 🎯 PROCHAINES ÉTAPES

1. ✅ Arrêter processus en erreur (FAIT)
2. ⏳ Créer `harvester_v7.py` compatible
3. ⏳ Tester sur petit échantillon
4. ⏳ Lancer production si tests OK

---

**🕋 Bismillah - Correction en cours...**