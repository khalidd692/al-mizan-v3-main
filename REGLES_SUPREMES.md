Ce fichier est la référence absolue — tout agent doit le lire avant toute action. En cas de conflit avec un autre fichier, REGLES_SUPREMES.md prime.

# REGLES SUPREMES — Référence Unique Agents

## 1) Autorité et résolution de conflits

- G est l'unique décideur du projet.
- Si une règle bloque une tâche concrète, l'agent signale immédiatement:

1. quelle règle bloque,
2. pourquoi elle bloque,
3. une proposition de modification.

- Aucun blocage silencieux n'est autorisé.
- En cas de conflit entre fichiers d'instructions, ce document prime.

## 2) Contrainte absolue non négociable

- Conformité au manhaj Salaf as-Salih dans le traitement du hadith.
- Références imposées: al-Albani, Ibn Baz, Ibn Uthaymin.

## 3) Zero génération religieuse non sourcée

- Interdiction de fabriquer un texte religieux (hadith, attribution, verdict).
- Interdiction de produire un grade (sahih/daif/mawdu...) sans source explicite.
- Interdiction de ta'wil figuratif sans preuve textuelle des Salaf.
- Si le contexte ne permet pas de conclure: tawaqquf explicite.

## 4) Sanctuaire technique frontend (verrou doctrinal)

- Ne pas modifier les fonctions protégées d'evaluation des grades sans déverrou explicite.
- Conserver l'ordre doctrinal de classification dans la logique des verdicts.
- Ne pas modifier les regex doctrinales ni whitelist de référence sans validation explicite.

## 5) Integrité JS et ordre de chargement

- Avant push, validation syntaxe JS obligatoire sur les fichiers critiques.
- Conserver l'ordre de chargement des scripts dépendants dans index.html.
- Ne pas renommer/supprimer les fonctions globales window.\* utilisées par le HTML.

## 6) Gardes anti-régression UI

- Conserver les gardes CSS anti-doublon existantes.
- Conserver la logique d'annulation/listeners dans le rendu d'arbre isnad.
- Conserver le tri chronologique death_year dans les traitements de chaîne.
- Ajouter des gardes d'existence DOM après nettoyage par innerHTML.

## 7) Anti-refactoring hors périmètre

- Interdiction de refactorer du code non visé par la tâche.
- Pas de nettoyage cosmétique non demandé (renommage, réordonnancement, extraction).

## 8) Backend, API et base de données

- Respecter l'architecture agents 1 fichier = 1 responsabilité.
- Ne pas déplacer le frontend root serving configuré côté backend sans validation explicite.
- Ne pas DROP/ALTER des tables sans migration versionnée.
- Utiliser sqlite3 pour la DB; ne jamais traiter un .db comme texte brut.

## 9) SSE et cache

- Respecter le contrat SSE (zone, done) et l'ordre d'emission attendu.
- Ne jamais cacher /api/\* dans le service worker.
- Toute modification index.html doit gérer le versionnement de cache.

## 10) Règle commit/push

- Avant commit, vérifier précisément les fichiers impactés et le contenu du diff.
- Ne commit que le périmètre demandé; exclure les changements non liés.
- Un seul commit/push pour une demande unifiée, sauf instruction contraire.

## 11) Règle opérationnelle agents

- Avant toute action: lire ce fichier en priorité.
- Appliquer les règles existantes des fichiers locaux uniquement si elles ne contredisent pas ce document.
