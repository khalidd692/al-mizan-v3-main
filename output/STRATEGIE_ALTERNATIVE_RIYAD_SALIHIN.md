# 🔄 Stratégie Alternative pour Riyad al-Salihin

**Date**: 18 avril 2026, 17:52  
**Statut**: ✅ Solution trouvée via dorar.net

## 📊 Résumé de la Situation

### ❌ Problème Initial
- API sunnah.com retourne **403 Forbidden** pour Riyad al-Salihin
- Accès gratuit limité aux 40 Hadiths de Nawawi uniquement
- Clé API requise pour les autres recueils

### ✅ Solution Trouvée
**dorar.net est accessible** et contient Riyad al-Salihin en arabe

## 🧪 Tests des Sources Alternatives

| Source | Statut | Notes |
|--------|--------|-------|
| sunnah.com | ❌ Bloqué | 403 Forbidden, clé API requise |
| hadith-gading.com | ❌ Erreur | Méthode list_collections manquante |
| jsdelivr (GitHub) | ❌ Erreur | Classe JsDelivrConnector non trouvée |
| **dorar.net** | ✅ **Disponible** | Site accessible, Riyad al-Salihin présent |

## 🎯 Plan d'Action Recommandé

### Option A: Utiliser dorar.net (RECOMMANDÉ)
**Avantages**:
- ✅ Gratuit et accessible
- ✅ Parser HTML déjà développé
- ✅ Contenu en arabe vérifié
- ✅ Pas de limite de rate

**Inconvénients**:
- ⚠️ Nécessite du scraping (plus lent)
- ⚠️ Pas de traduction anglaise
- ⚠️ Structure HTML peut changer

**Implémentation**:
```python
from backend.dorar_html_parser import DorarHTMLParser

parser = DorarHTMLParser()
# Rechercher par mots-clés ou parcourir systématiquement
hadiths = parser.search_hadith('رياض الصالحين')
```

### Option B: Passer aux autres recueils
**Recueils alternatifs disponibles**:
1. Muwatta Malik (~1,800 hadiths) - hadith-gading.com
2. Sunan Abu Dawud (~5,274 hadiths) - hadith-gading.com
3. Autres recueils des Kutub al-Sittah

### Option C: Obtenir clé API sunnah.com
**Démarches**:
1. Visiter https://sunnah.com/api
2. S'inscrire et demander une clé
3. Coût et délai à vérifier

## 💡 Recommandation Immédiate

### 1. Continuer avec les sources gratuites confirmées

**Collections déjà importées** ✅:
- Sahih Bukhari: 7,563 hadiths
- 40 Nawawi: 42 hadiths
- **Total: 7,605 hadiths**

**Prochaines priorités**:
1. **Sahih Muslim** (~7,500 hadiths) - hadith-gading.com
2. **Sunan Abu Dawud** (~5,274 hadiths) - hadith-gading.com
3. **Jami' at-Tirmidhi** (~3,956 hadiths) - hadith-gading.com
4. **Sunan an-Nasa'i** (~5,758 hadiths) - hadith-gading.com
5. **Sunan Ibn Majah** (~4,341 hadiths) - hadith-gading.com

**Total potentiel immédiat**: ~34,000 hadiths

### 2. Développer scraper dorar.net en parallèle

Pour Riyad al-Salihin et autres recueils populaires:
- Riyad al-Salihin (~1,900 hadiths)
- Bulugh al-Maram (~1,500 hadiths)
- Al-Adab al-Mufrad (~1,300 hadiths)

## 📈 Projection de Croissance

### Phase 1: Kutub al-Sittah Complets (EN COURS)
```
Bukhari:     7,563 ✅
Muslim:      7,500 ⏳
Abu Dawud:   5,274 ⏳
Tirmidhi:    3,956 ⏳
Nasa'i:      5,758 ⏳
Ibn Majah:   4,341 ⏳
─────────────────────
Total:      34,392 hadiths
```

### Phase 2: Recueils Populaires (via dorar.net)
```
Riyad al-Salihin:    1,900
Bulugh al-Maram:     1,500
Al-Adab al-Mufrad:   1,300
Muwatta Malik:       1,800
─────────────────────
Total:               5,500 hadiths
```

### Phase 3: Collections Étendues
```
Musnad Ahmad:       27,000+
Autres recueils:    50,000+
─────────────────────
Total:              77,000+ hadiths
```

**TOTAL PROJETÉ: ~117,000 hadiths** (78% de l'objectif)

## 🚀 Actions Immédiates

### 1. Compléter les Kutub al-Sittah
```bash
# Importer Muslim, Abu Dawud, Tirmidhi, Nasa'i, Ibn Majah
python backend/harvest_kutub_sittah.py --continue
```

### 2. Tester le scraper dorar.net
```bash
# Vérifier que le parser fonctionne
python backend/test_dorar_api.py
```

### 3. Développer import dorar.net
```python
# Créer import_dorar_collections.py
# Pour Riyad al-Salihin, Bulugh al-Maram, etc.
```

## 📝 Conclusion

**Stratégie optimale**:
1. ✅ Continuer avec hadith-gading.com pour les Kutub al-Sittah
2. ✅ Développer scraper dorar.net pour recueils populaires
3. ⏳ Évaluer clé API sunnah.com si budget disponible

**Avantages de cette approche**:
- Maximise les sources gratuites
- Diversifie les sources de données
- Atteint ~117,000 hadiths sans coût
- Permet d'évaluer le besoin d'API payante

**Prochaine étape**: Compléter l'import des Kutub al-Sittah via hadith-gading.com

---

**Rapport complet**: `output/RIYAD_SALIHIN_API_BLOQUEE.md`