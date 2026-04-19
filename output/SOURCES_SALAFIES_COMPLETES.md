# 📚 Sources Salafies Complètes - Plan d'Extraction

**Date**: 18 avril 2026, 17:54  
**Objectif**: Extraire TOUTES les sources salafies authentiques

## 🎯 Sources Principales

### 1. Dorar.net (PRIORITÉ 1) ✅
**Site**: https://dorar.net  
**Statut**: Accessible et testé  
**Contenu**: Base de données hadith la plus complète en arabe

#### Livres Majeurs Disponibles

**Kutub al-Sittah** (Les Six Livres):
- صحيح البخاري (Sahih Bukhari) - ~7,563 hadiths
- صحيح مسلم (Sahih Muslim) - ~7,500 hadiths
- سنن أبي داود (Sunan Abu Dawud) - ~5,274 hadiths
- جامع الترمذي (Jami' Tirmidhi) - ~3,956 hadiths
- سنن النسائي (Sunan Nasa'i) - ~5,758 hadiths
- سنن ابن ماجه (Sunan Ibn Majah) - ~4,341 hadiths

**Muwatta**:
- موطأ مالك (Muwatta Malik) - ~1,800 hadiths

**Musnad**:
- مسند أحمد (Musnad Ahmad) - ~27,000 hadiths
- مسند الشافعي (Musnad Shafi'i) - ~1,200 hadiths
- مسند أبي حنيفة (Musnad Abu Hanifa) - ~150 hadiths

**Recueils Populaires**:
- رياض الصالحين (Riyad al-Salihin) - ~1,900 hadiths
- بلوغ المرام (Bulugh al-Maram) - ~1,500 hadiths
- الأدب المفرد (Al-Adab al-Mufrad) - ~1,300 hadiths
- الأربعون النووية (40 Nawawi) - 42 hadiths
- شرح السنة (Sharh al-Sunnah) - ~4,000 hadiths

**Œuvres de Sheikh Al-Albani** (Méthodologie salafie):
- صحيح الترغيب والترهيب (Sahih Targhib wa Tarhib)
- صحيح الجامع الصغير (Sahih Jami' al-Saghir)
- السلسلة الصحيحة (Silsilah Sahihah) - Authentiques
- السلسلة الضعيفة (Silsilah Da'ifah) - Faibles
- إرواء الغليل (Irwa al-Ghalil)

**Livres de Fiqh avec Hadiths**:
- نيل الأوطار (Nayl al-Awtar) - Shawkani
- المحلى (Al-Muhalla) - Ibn Hazm
- فتح الباري (Fath al-Bari) - Ibn Hajar

**Total Estimé Dorar.net**: ~75,000+ hadiths

### 2. Bibliothèque Université Islamique de Médine

**Site**: https://iu.edu.sa  
**Bibliothèque numérique**: https://library.iu.edu.sa

#### Collections Disponibles:
- Manuscrits authentifiés
- Thèses de doctorat en sciences du hadith
- Recherches des savants salafis
- Archives audio des cours

#### Savants de Médine (Méthodologie Salafie):
- Sheikh Ibn Baz (رحمه الله)
- Sheikh Al-Albani (رحمه الله)
- Sheikh Ibn Uthaymin (رحمه الله)
- Sheikh Fawzan
- Sheikh Rabi' al-Madkhali

### 3. Autres Sources Salafies

#### A. Maktabah Shamela (المكتبة الشاملة)
**Site**: https://shamela.ws  
**Contenu**: 
- 10,000+ livres islamiques
- Tous les recueils de hadith majeurs
- Commentaires des savants salafis
- Format structuré et recherchable

#### B. Islamweb.net
**Site**: https://islamweb.net  
**Sections**:
- Bibliothèque de hadiths
- Fatawa des savants
- Recherche par thème

#### C. Alukah.net
**Site**: https://alukah.net  
**Focus**: Articles et recherches salafies

#### D. Saaid.net
**Site**: https://saaid.net  
**Contenu**: Bibliothèque salafie complète

## 🌐 Ressources contemporaines additionnelles (APIs, bases de données, open source, etc.)

### APIs et Bases de Données Modernes

| Source | URL | Type | Collections | Statut |
|--------|-----|------|-------------|--------|
| **Sunnah.com API** | https://sunnah.com/api | API REST | Toutes collections majeures | À tester |
| **Hadith Gading API** | https://api.hadith.gading.dev | API REST | Toutes collections majeures | À tester |
| **JSDelivr Hadith API (GitHub)** | https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api | API CDN | Multi-sources | À tester |
| **QuranHadith API** | https://quranhadith.com/api | API REST | Multi-sources | À tester |
| **Random Hadith Generator** | https://random-hadith-generator.vercel.app | API REST | Aléatoire | À tester |

### Bibliothèques et Portails Numériques

| Source | URL | Type | Description | Statut |
|--------|-----|------|-------------|--------|
| **Al-Maktaba.org** | https://al-maktaba.org | Web | Livres de hadith, qualité académique | À tester |
| **Waqfeya.net** | https://waqfeya.net | Web | Manuscrits et livres classiques | À tester |
| **Archive.org** | https://archive.org | Web/Open Data | Manuscrits originaux, OCR possible | À tester |
| **IslamWay** | https://ar.islamway.net | Web | Hadiths, conférences, audio | À tester |
| **Al-Manhaj.net** | https://almanhaj.net | Web | Méthodologie salafie, articles | À tester |
| **IEF Pedia** | https://iefpedia.com | Web | Encyclopédie islamique | À tester |

> Ces ressources contemporaines, issues de la communauté tech musulmane et de projets open source, permettent d'élargir la couverture du corpus hadith authentique, tout en respectant la méthodologie salafie (validation isnad, authenticité, conformité savants reconnus).  
> **Prochaines actions** : tester l'accessibilité, la structure des données (JSON, HTML parsable), la complétude des métadonnées, et intégrer les collections pertinentes dans le pipeline d'extraction.

## 🚀 Plan d'Extraction Massif

### Phase 1: Dorar.net (EN COURS)
```bash
python backend/dorar_massive_harvester.py
```

**Cibles**:
1. Kutub al-Sittah complets
2. Musnad Ahmad
3. Riyad al-Salihin
4. Œuvres Al-Albani
5. Tous les autres recueils disponibles

**Estimation**: 75,000+ hadiths

### Phase 2: Shamela.ws
```bash
python backend/shamela_harvester.py
```

**Méthode**:
- Télécharger les fichiers BOK (format Shamela)
- Parser et extraire les hadiths
- Vérifier authenticité avec chaînes de transmission

**Estimation**: 50,000+ hadiths supplémentaires

### Phase 3: Université de Médine
```bash
python backend/medina_library_harvester.py
```

**Méthode**:
- Accéder à la bibliothèque numérique
- Extraire les thèses et recherches
- Parser les hadiths cités avec références

**Estimation**: 20,000+ hadiths avec analyses

### Phase 4: Sources Complémentaires
- Islamweb.net
- Alukah.net
- Saaid.net

**Estimation**: 30,000+ hadiths

## 📊 Projection Totale

| Source | Hadiths | Statut |
|--------|---------|--------|
| Dorar.net | 75,000+ | ✅ En cours |
| Shamela.ws | 50,000+ | ⏳ À développer |
| Médine | 20,000+ | ⏳ À développer |
| Autres | 30,000+ | ⏳ À développer |
| **TOTAL** | **175,000+** | **117% objectif** |

## 🔧 Outils à Développer

### 1. Dorar Massive Harvester ✅
```python
# Déjà créé
python backend/dorar_massive_harvester.py
```

### 2. Shamela Parser
```python
# À créer
python backend/shamela_parser.py
```

### 3. Medina Library Connector
```python
# À créer
python backend/medina_connector.py
```

### 4. Multi-Source Aggregator
```python
# À créer
python backend/salafi_aggregator.py
```

## 🎯 Critères de Sélection (Méthodologie Salafie)

### Priorité Absolue:
1. ✅ Kutub al-Sittah (Les Six Livres)
2. ✅ Musnad Ahmad
3. ✅ Muwatta Malik
4. ✅ Œuvres authentifiées par Al-Albani
5. ✅ Recherches des savants de Médine

### Critères d'Authenticité:
- Chaîne de transmission (isnad) complète
- Narrateurs authentifiés (thiqat)
- Pas de contradictions avec Coran/Sunnah
- Validation par savants salafis reconnus

### Exclusions:
- ❌ Hadiths faibles sans mention
- ❌ Hadiths inventés (mawdu')
- ❌ Sources non authentifiées
- ❌ Interprétations non salafies

## 📝 Prochaines Actions

### Immédiat (Aujourd'hui):
1. ✅ Lancer dorar_massive_harvester.py
2. ⏳ Extraire Kutub al-Sittah complets
3. ⏳ Extraire Musnad Ahmad

### Court Terme (Cette Semaine):
1. Développer shamela_parser.py
2. Tester accès bibliothèque Médine
3. Créer medina_connector.py

### Moyen Terme (Ce Mois):
1. Agréger toutes les sources
2. Dédupliquer et valider
3. Atteindre 175,000+ hadiths

## 🌟 Avantages de Cette Approche

1. **Exhaustivité**: Toutes les sources salafies majeures
2. **Authenticité**: Focus sur méthodologie salafie
3. **Gratuité**: Toutes les sources sont libres d'accès
4. **Qualité**: Validation par savants reconnus
5. **Complétude**: Dépasse largement l'objectif initial

---

**Script prêt**: `backend/dorar_massive_harvester.py`  
**Lancement**: `python backend/dorar_massive_harvester.py`