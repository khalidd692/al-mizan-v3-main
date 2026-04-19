# 🎯 API OFFICIELLE DORAR.NET DÉCOUVERTE

**Date**: 18 avril 2026, 19:24
**Source**: Tavily Search + Documentation officielle

---

## ✅ API OFFICIELLE DORAR.NET

### URL Documentation
**https://dorar.net/article/389/خدمة-واجهة-الموسوعة-الحديثية-API**

### Description
Service API officiel de la موسوعة الحديثية (Encyclopédie Hadith) de Dorar السنية

---

## 🔧 ENDPOINTS DÉCOUVERTS

### Format de base
```
https://dorar.net/dorar_api.json?skey={terme_recherche}&callback=?
```

### Méthodes d'utilisation

#### 1. JSONP (JavaScript)
```javascript
$.getJSON("https://dorar.net/dorar_api.json?skey=" + $("#skey").val() + "&callback=?", 
  function(data) {
    $.each(data, function(i, item) {
      $("#dorar").append("<div>" + item.th + "</div>");
    });
  }
);
```

#### 2. PHP
```php
$url = "https://dorar.net/dorar_api.json?skey=" . urlencode($search_term);
$json = file_get_contents($url);
$data = json_decode($json, true);
```

---

## 📦 REPOS GITHUB CONNEXES

### 1. MoathCodes/dorar_hadith ⭐⭐⭐⭐
- **URL**: https://github.com/MoathCodes/dorar_hadith
- **Type**: Package Dart
- **Fonction**: Wrapper pour API Dorar
- **Statut**: ✅ ACTIF

### 2. AhmedElTabarani/dorar-hadith-api ⭐⭐⭐⭐⭐
- **URL**: https://github.com/AhmedElTabarani/dorar-hadith-api
- **Type**: API intermédiaire
- **Fonction**: Wrapper PHP pour Dorar
- **Statut**: ✅ PRIORITÉ

---

## 🚀 PLAN D'EXPLOITATION

### Phase 1: Tester l'API (15 min)
```python
import requests

def test_dorar_api(search_term):
    url = f"https://dorar.net/dorar_api.json?skey={search_term}"
    response = requests.get(url)
    return response.json()

# Test
results = test_dorar_api("صحيح")
print(f"{len(results)} hadiths trouvés")
```

### Phase 2: Harvester API Dorar (1-2 heures)
```python
# backend/dorar_api_harvester.py
- Recherches par termes clés
- Pagination automatique
- Extraction massive
- Déduplication SHA-256
```

### Phase 3: Import massif (2-3 heures)
- Parser les résultats JSON
- Extraire métadonnées (grades, narrateurs)
- Import dans almizane.db

---

## 📊 ESTIMATION CONTENU

### Dorar.net contient
```
Livres de hadith:           +400 livres
Jugements de savants:       200 savants
Période couverte:           13 siècles
Hadiths estimés:            ~500,000+
```

### Extraction réaliste
```
Via API directe:            ~100,000 hadiths
Via repos GitHub:           ~30,000 hadiths
─────────────────────────────────────
TOTAL DORAR:                ~130,000 hadiths
```

---

## ✅ AVANTAGES API OFFICIELLE

### Légitimité
- ✅ API officielle (pas de scraping)
- ✅ Documentée publiquement
- ✅ Autorisée pour usage

### Qualité
- ✅ Données authentifiées
- ✅ Grades inclus
- ✅ Métadonnées complètes

### Performance
- ✅ Réponses JSON rapides
- ✅ Pas de rate limiting mentionné
- ✅ JSONP supporté

---

## 🎯 INTÉGRATION IMMÉDIATE

### Créer le harvester
```bash
# backend/dorar_official_api_harvester.py
python backend/dorar_official_api_harvester.py
```

### Termes de recherche prioritaires
```python
search_terms = [
    "صحيح",      # Sahih
    "حسن",       # Hasan
    "البخاري",   # Bukhari
    "مسلم",      # Muslim
    "الترمذي",   # Tirmidhi
    "أبو داود",  # Abu Dawud
    "النسائي",   # Nasa'i
    "ابن ماجه",  # Ibn Majah
    # ... 100+ termes
]
```

---

## 📈 PROJECTION FINALE AVEC DORAR API

```
Base actuelle:              87,337
GitHub import:             +60,000
Dorar API:                +100,000
Harvesters 1+2:           +110,000
─────────────────────────────────────
TOTAL FINAL:               357,337 hadiths

Objectif 200K: DÉPASSÉ de 79% ✅✅✅
```

---

**PROCHAINE ÉTAPE**: Créer dorar_official_api_harvester.py