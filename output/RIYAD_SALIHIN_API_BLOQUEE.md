# 🚫 API Sunnah.com Bloquée pour Riyad al-Salihin

**Date**: 18 avril 2026, 17:51  
**Statut**: ❌ Erreur 403 Forbidden

## 🔍 Problème Identifié

L'API sunnah.com retourne des erreurs **403 Forbidden** pour Riyad al-Salihin, indiquant que :
- Une clé API est requise pour ce recueil
- L'accès gratuit est limité aux 40 Hadiths de Nawawi uniquement

```
Erreur 403 pour hadith 1
Erreur 403 pour hadith 2
Erreur 403 pour hadith 3
...
```

## 📊 Collections Testées

| Collection | Statut | Hadiths | Accès |
|------------|--------|---------|-------|
| 40 Nawawi | ✅ OK | 42 | Gratuit |
| Riyad al-Salihin | ❌ 403 | 1,896 | Clé API requise |
| Bulugh al-Maram | ❓ Non testé | 1,358 | Probablement bloqué |
| Al-Adab al-Mufrad | ❓ Non testé | 1,322 | Probablement bloqué |

## 🔄 Solutions Alternatives

### Option 1: Utiliser hadith-gading.com
```python
# Déjà testé et fonctionnel
from connectors.hadith_gading_connector import HadithGadingConnector

connector = HadithGadingConnector()
# Vérifier si Riyad al-Salihin est disponible
```

### Option 2: Utiliser jsdelivr (GitHub datasets)
```python
# Datasets JSON disponibles sur GitHub
from connectors.jsdelivr_connector import JsDelivrConnector

connector = JsDelivrConnector()
# Chercher des datasets de Riyad al-Salihin
```

### Option 3: Scraping dorar.net
```python
# Parser HTML de dorar.net
from dorar_html_parser import DorarHTMLParser

parser = DorarHTMLParser()
# Extraire Riyad al-Salihin depuis dorar.net
```

### Option 4: Obtenir une clé API sunnah.com
- Site: https://sunnah.com/api
- Coût: Probablement payant
- Délai: Inscription et validation

## 📝 Recommandations Immédiates

### 1. Tester hadith-gading.com
```bash
python -c "
from backend.connectors.hadith_gading_connector import HadithGadingConnector
connector = HadithGadingConnector()
print('Collections disponibles:', connector.list_collections())
"
```

### 2. Chercher sur GitHub
```bash
# Rechercher des datasets JSON de Riyad al-Salihin
python -c "
from backend.connectors.jsdelivr_connector import JsDelivrConnector
connector = JsDelivrConnector()
results = connector.search_hadith_datasets('riyad salihin')
print(results)
"
```

### 3. Vérifier dorar.net
```bash
# Tester l'accès à dorar.net
python backend/test_dorar_api.py
```

## 🎯 Plan d'Action Révisé

### Phase 1: Sources Gratuites Confirmées ✅
- [x] 40 Hadiths de Nawawi (42 hadiths) - sunnah.com
- [x] Kutub al-Sittah (7,563 hadiths) - hadith-gading.com

### Phase 2: Recueils Populaires (EN COURS)
- [ ] Riyad al-Salihin (1,896 hadiths) - **BLOQUÉ**
- [ ] Bulugh al-Maram (1,358 hadiths) - À tester
- [ ] Al-Adab al-Mufrad (1,322 hadiths) - À tester

### Phase 3: Sources Alternatives
1. **hadith-gading.com** - Tester disponibilité
2. **GitHub datasets** - Chercher JSON
3. **dorar.net** - Scraping HTML
4. **hadeethenc.com** - API multilingue

## 💡 Stratégie Optimale

1. **Immédiat**: Tester hadith-gading.com pour Riyad al-Salihin
2. **Court terme**: Chercher datasets GitHub
3. **Moyen terme**: Développer scraper dorar.net si nécessaire
4. **Long terme**: Considérer clé API sunnah.com si budget disponible

## 📈 État Actuel du Projet

```
Total hadiths en base: ~7,605
Collections: 7
Progression: 5% de l'objectif (150,000 hadiths)
```

### Collections Disponibles
1. Sahih Bukhari: 7,563 hadiths ✅
2. 40 Nawawi: 42 hadiths ✅
3. Riyad al-Salihin: 0 hadiths ❌ (bloqué)

## 🔧 Actions Requises

1. Tester hadith-gading.com pour recueils populaires
2. Explorer GitHub pour datasets JSON
3. Évaluer faisabilité scraping dorar.net
4. Documenter toutes les sources accessibles gratuitement

---

**Prochaine étape**: Tester hadith-gading.com pour Riyad al-Salihin