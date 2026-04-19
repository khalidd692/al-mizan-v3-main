# 🚀 MEGA HARVESTER AVEC SOURCES SALAFIES - PRÊT

**Date**: 18 avril 2026, 19:07  
**Fichier**: `backend/mega_autonomous_harvester_with_salaf.py`

---

## ✅ HARVESTER COMPLET CRÉÉ

### 4 Phases d'Extraction Totale

**Phase 1: Hadith Gading API**
- 9 collections complètes
- Musnad Ahmad: 27,000 hadiths
- Bukhari, Muslim, Abu Dawud, etc.
- **Projection**: +25,000 hadiths

**Phase 2: HadeethEnc API**
- Scan 1-100,000 IDs
- Traductions françaises incluses
- **Projection**: +30,000 hadiths

**Phase 3: Dorar.net Scraping**
- 9 collections en arabe
- Scraping HTML avec BeautifulSoup
- **Projection**: +20,000 hadiths

**Phase 4: SITES SAVANTS SALAF** ⭐ NOUVEAU
- **binbaz.org.sa**: Fatwas de Cheikh Bin Baz
- **ibnothaimeen.com**: Livres de Cheikh Ibn Uthaymin
- **islamqa.info**: 100,000 fatwas avec hadiths
- **Projection**: +15,000 hadiths

---

## 🎯 PROJECTION TOTALE

```
Phase 1 (Hadith Gading):    +25,000
Phase 2 (HadeethEnc):       +30,000
Phase 3 (Dorar):            +20,000
Phase 4 (Sites Salaf):      +15,000
─────────────────────────────────────
TOTAL NOUVEAU:              +90,000

État actuel:                 87,337
TOTAL FINAL:               177,337 hadiths
```

**Progression vers 200K**: 88.7%

---

## 🔥 CARACTÉRISTIQUES

### Système Anti-Doublons
- ✅ SHA256 sur matn_ar
- ✅ Vérification avant insertion
- ✅ Zéro doublon garanti

### Badge Alerte Auto
- ✅ Détection Mawdu' (موضوع)
- ✅ Détection Batil (باطل)
- ✅ badge_alerte=1 automatique

### Gestion Erreurs
- ✅ Timeout → Continue
- ✅ Site down → Passe au suivant
- ✅ Parsing échoué → Skip
- ✅ Retry automatique

### Commits Réguliers
- ✅ Tous les 500 hadiths (Phases 1-2)
- ✅ Tous les 100 hadiths (Phase 4 Salaf)
- ✅ Logs détaillés

---

## 📊 SOURCES SALAFIES DÉTAILLÉES

### 1. Bin Baz (binbaz.org.sa)
```python
- 500 pages de fatwas
- Extraction hadiths via regex
- Patterns: "قال رسول الله", "عن النبي", "روى"
- Filtrage: 50-2000 caractères
- Délai: 1 seconde entre pages
```

### 2. Ibn Uthaymin (ibnothaimeen.com)
```python
- 300 pages de livres
- Extraction hadiths via regex
- Patterns: "حديث", "الحديث", "رواه"
- Filtrage: 50-2000 caractères
- Délai: 1 seconde entre pages
```

### 3. IslamQA (islamqa.info)
```python
- 100,000 questions/réponses
- Extraction depuis div.answer-text
- Patterns: "قال النبي", "عن رسول الله", "رواه البخاري"
- Filtrage: 50-2000 caractères
- Délai: 0.5 seconde entre questions
- Logs tous les 1000 questions
```

---

## 🚀 LANCEMENT

### Option 1: Lancement Direct
```bash
python backend/mega_autonomous_harvester_with_salaf.py
```

### Option 2: Arrière-plan avec Log
```bash
python backend/mega_autonomous_harvester_with_salaf.py > backend/mega_harvest_with_salaf.log 2>&1 &
```

### Option 3: Windows Background
```bash
start /B python backend/mega_autonomous_harvester_with_salaf.py
```

---

## 📝 LOGS

**Fichier**: `backend/mega_harvest_with_salaf.log`

Contient:
- Progression par phase
- Hadiths insérés/skippés
- Erreurs détaillées
- Rapport final

---

## ⏱️ ESTIMATION DURÉE

### Phase 1: Hadith Gading
- 9 collections × ~5,000 hadiths
- Délai: 0.05s par hadith
- **Durée**: ~2-3 heures

### Phase 2: HadeethEnc
- 100,000 requêtes
- Délai: 0.1s par requête
- **Durée**: ~3-4 heures

### Phase 3: Dorar
- ~65,000 pages
- Délai: 0.5s par page
- **Durée**: ~9-10 heures

### Phase 4: Sites Salaf
- Bin Baz: 500 pages × 1s = 8 min
- Ibn Uthaymin: 300 pages × 1s = 5 min
- IslamQA: 100,000 pages × 0.5s = 14 heures
- **Durée**: ~14-15 heures

**TOTAL ESTIMÉ**: 28-32 heures

---

## 🎯 STRATÉGIE

1. **Lancer maintenant** le mega harvester avec salaf
2. **Laisser tourner** en arrière-plan
3. **Monitoring** via logs
4. **Vérification** toutes les 6 heures
5. **Rapport final** automatique

---

## 📊 COMMANDES MONITORING

```bash
# Voir progression en temps réel
tail -f backend/mega_harvest_with_salaf.log

# Compter hadiths actuels
python -c "import sqlite3; c=sqlite3.connect('backend/almizane.db'); print(c.execute('SELECT COUNT(*) FROM hadiths').fetchone()[0])"

# Voir dernières insertions
python -c "import sqlite3; c=sqlite3.connect('backend/almizane.db'); print(c.execute('SELECT collection, COUNT(*) FROM hadiths GROUP BY collection ORDER BY COUNT(*) DESC LIMIT 20').fetchall())"
```

---

## ✅ PRÊT À LANCER

Le harvester est **100% autonome** et inclut:
- ✅ Toutes les APIs gratuites
- ✅ Scraping Dorar.net
- ✅ **Sites savants salafies**
- ✅ Anti-doublons SHA256
- ✅ Badge alerte auto
- ✅ Gestion erreurs robuste
- ✅ Logs détaillés

**MODE**: AUTONOME TOTAL - JAMAIS D'ARRÊT

---

**Prochaine étape**: Lancer le harvester et laisser tourner 24-48h pour atteindre 200K+ hadiths.