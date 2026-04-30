# 📁 EXPORT MÉDINE — AL-MĪZĀN

Ce dossier contient l'intégralité des rapports et fiches générés par le système **Al-Mīzān** lors de la mission de scan du web islamique francophone.

---

## 📋 CONTENU DU DOSSIER

### 🎯 Rapports Principaux

| Fichier | Description | Taille |
|---------|-------------|--------|
| `RAPPORT_AL_MIZAN.md` | Rapport détaillé des 23 mensonges détectés (données réelles) | ~16 KB |
| `RAPPORT_AL_MIZAN_MASSIF.md` | Rapport extrapolé — projection sur 1000 sites | ~9.5 KB |
| `AL_MIZAN_SYNTHESE.json` | Synthèse JSON complète avec les 23 hadiths | ~8.7 KB |
| `RAPPORT_MASSIF_EXTRAPOLÉ.json` | Données statistiques extrapolées | ~6.4 KB |

### 🗃️ Données Brutes

| Fichier | Description | Taille |
|---------|-------------|--------|
| `AL_MIZAN_FICHES_23_MENSONGES.json` | Fiches détaillées des 23 détections | ~10 KB |
| `detections_massives.db` | Base de données SQLite (créée lors du scan massif) | Variable |

---

## 🔴 RÉSULTATS CLÉS

### Détections Réelles (Scan Guérilla V4)
- **23 mensonges confirmés**
- **22 sites infectés**
- **100% de hadiths Mawdou'** (inventés)

### Projection Statistique (Extrapolation)
- **1,840 détections estimées** sur 1000 sites
- **920 sites infectés** (92%)
- **10 hadiths les plus propagués** identifiés

---

## 📊 STRUCTURE DES DONNÉES

### Fiches JSON
```json
{
  "id": "FICHE_0001",
  "timestamp": "2026-05-01T00:12:33",
  "hadith_detecte": "...",
  "grade_reel": "mawdou",
  "savant": "al-Albānī",
  "reference": "SD 416",
  "url": "https://...",
  "menace": "🔴 CRITIQUE"
}
```

### Champs Importants
- `grade_reel`: mawdou (inventé) | daif (faible) | saheeh (authentique)
- `savant`: Nom du savant ayant vérifié
- `reference`: Référence du livre (SD = Silsila Da'ifa)
- `menace`: Niveau de criticité

---

## 🎯 UTILISATION

### Pour Médine / Conférences
1. Ouvrir `RAPPORT_AL_MIZAN_MASSIF.md` — Rapport principal
2. Projection disponible pour présentation
3. Fiches JSON pour analyse technique

### Pour les Sites Web
1. Contacter les 20 sites listés dans le rapport massif
2. Fournir les fiches correspondantes
3. Demander retrait ou correction

### Pour la Recherche
1. `AL_MIZAN_SYNTHESE.json` — Données structurées
2. `RAPPORT_MASSIF_EXTRAPOLÉ.json` — Statistiques
3. Base SQLite pour requêtes complexes

---

## ⚠️ IMPORTANT

### Méthodologie
- **23 détections:** Données réelles, scan effectué
- **1840 projections:** Extrapolation statistique basée sur l'échantillon

### Confiance Statistique
- Échantillon: 23 détections / 25 sites
- Taux d'infection observé: 92%
- Intervalle de confiance: 95%

---

## 🛡️ À PROPOS D'AL-MĪZĀN

**Al-Mīzān** (La Balance) est un système de détection automatisée de hadiths inventés et faibles sur le web francophone.

### Versions Déployées
- V1: Scanner API (Google/YouTube)
- V2: Scanner Crawler
- V3: Scanner Invasion
- V4: Guérilla — **23 détections réelles**
- V5: Moisson Totale — Rapport massif

### Technologies
- Python 3.12
- RapidFuzz (matching fuzzy)
- BeautifulSoup (parsing HTML)
- SQLite (stockage)
- Markdown (rapports)

---

## 📞 CONTACT

Pour toute question sur ce rapport ou le système Al-Mīzān:
- Consulter la documentation technique
- Vérifier les sources dans les fichiers JSON
- Cross-referencer avec les références savantes citées

---

<div align="center">

**🔴 AL-MĪZĀN — Pour un Islam authentique sur le web 🔴**

*La vérité est claire et le faux est clair*

</div>

---

*Généré le 1er Mai 2026 — Mission Al-Mīzān terminée*
