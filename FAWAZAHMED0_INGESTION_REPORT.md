# FAWAZAHMED0 — Rapport d'ingestion FR

**Date** : 2026-04-27 08:30 UTC  
**Source** : `fawazahmed0_fr_dump.json`  
**Base** : `backend/almizane.db`  

## Résumé global

| Métrique | Valeur |
|----------|--------|
| Hadiths dans le dump | 32,555 |
| Traductions mises à jour (UPDATE matn_fr) | 31,649 |
| Nouveaux hadiths insérés (INSERT) | 122 |
| Ignorés (matn_fr déjà présent) | 600 |
| Sans correspondance en DB | 184 |

## Détail par édition

| Édition | Total dump | Mis à jour | Insérés | Ignorés | Sans match | Flag |
|---------|-----------|-----------|---------|---------|-----------|------|
| `fra-abudawud` | 5,274 | 5,272 | 0 | 0 | 2 | — |
| `fra-bukhari` | 7,589 | 6,987 | 0 | 600 | 2 | — |
| `fra-dehlawi` | 40 | 0 | 40 | 0 | 0 | `methodologie_a_verifier` |
| `fra-ibnmajah` | 4,343 | 4,338 | 0 | 0 | 5 | — |
| `fra-malik` | 1,899 | 1,829 | 0 | 0 | 70 | — |
| `fra-muslim` | 7,563 | 7,484 | 0 | 0 | 79 | — |
| `fra-nasai` | 5,765 | 5,739 | 0 | 0 | 26 | — |
| `fra-nawawi` | 42 | 0 | 42 | 0 | 0 | `methodologie_a_verifier` |
| `fra-qudsi` | 40 | 0 | 40 | 0 | 0 | — |

## Colonne ajoutée

La colonne `statut_import TEXT` a été ajoutée à la table `hadiths` si elle n'existait pas.

- Valeur `methodologie_a_verifier` → hadiths issus de `fra-nawawi` et `fra-dehlawi`
- Valeur `NULL` → hadiths des 7 autres éditions (pas de doute méthodologique)

## Zones Al-Mīzān

Les hadiths ingérés alimentent principalement :

| Zone | Pertinence |
|------|-----------|
| **Zone 2 — Matn** | Texte français disponible pour analyse du contenu |
| **Zone 11 — Grading** | Grades fawazahmed0 importés dans `grade_final` (nouvelles collections) |
| **Zone 13 — Daif / Zone 17 — Mawdu** | Hadiths `methodologie_a_verifier` à traiter en priorité |
| **Zone 4 — Takhrij** | Source `fawazahmed0_raw_github` tracée dans `source_api` |

## Prochaines étapes

1. Vérifier manuellement les 82 hadiths `methodologie_a_verifier` (`fra-nawawi` + `fra-dehlawi`)
2. Croiser les `no_match` avec les doublons de collection (`bukhari` vs `Sahih Bukhari`)
3. Ingérer les `avis_savants` depuis les grades fawazahmed0 (champ `grades[]`)
4. Activer les migrations 001/002 pour `needs_human_review` et table `authorities`
