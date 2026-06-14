# AI Workflow Guide

Ce document définit une méthode simple pour utiliser l'IA dans le développement du jeu Python / Pygame.

Objectif : utiliser l'IA pour avancer plus vite, sans perdre le contrôle technique du projet, sans salir Git, et sans casser l'architecture existante.

---

## 1. Principes généraux

Le projet doit continuer à évoluer par petites étapes stables, compréhensibles et testables.

Règles de base :

- préserver l'architecture actuelle ;
- éviter les refontes globales ;
- éviter les renommages inutiles ;
- modifier le moins de fichiers possible ;
- garder le code simple et lisible ;
- préserver le comportement existant ;
- ajouter des tests quand une logique importante change ;
- ne jamais merger vers `main` sans validation humaine ;
- ne pas créer, supprimer, renommer ou merger de branches sans demande explicite.

L'IA peut proposer, expliquer, implémenter et reviewer.

L'humain garde la décision finale sur :

- l'architecture ;
- le gameplay ;
- l'équilibrage important ;
- les merges ;
- les branches ;
- les refactorisations ;
- les suppressions ou renommages.

---

## 2. Organisation des agents

L'organisation de départ repose sur quatre agents principaux.

Cette équipe doit rester légère. Les agents ne sont pas des personnes séparées obligatoires : ce sont des rôles que l'IA peut prendre selon la tâche.

---

## 3. Agent Cadrage & Découpage

### Problème résolu

Éviter les tâches trop larges, les demandes vagues et les modifications dispersées.

### Quand l'utiliser

Utiliser cet agent avant :

- une nouvelle feature ;
- un nouveau système ;
- une modification touchant plusieurs fichiers ;
- une tâche d'architecture ;
- une modification gameplay importante ;
- une PR qui semble trop large.

### Quand ne pas l'utiliser

Il n'est pas nécessaire pour :

- une correction très simple ;
- un changement de texte localisé ;
- une petite correction évidente dans un seul fichier.

### Livrable attendu

L'agent doit produire :

```text
Objectif
Contexte
Fichiers probablement concernés
Fichiers interdits
Critères d'acceptation
Tests attendus
Risques
Taille maximale de la modification
```

### Limites strictes

Cet agent ne doit pas :

- coder ;
- créer une branche ;
- merger ;
- supprimer des fichiers ;
- proposer une refonte globale sans justification forte.

### Niveau d'autonomie

Consultatif.

---

## 4. Agent Implémentation Localisée

### Problème résolu

Produire un changement de code limité, lisible et aligné avec l'objectif défini.

### Quand l'utiliser

Utiliser cet agent quand :

- la tâche est cadrée ;
- les fichiers autorisés sont connus ;
- le comportement attendu est clair ;
- le changement peut rester petit.

### Quand ne pas l'utiliser

Ne pas l'utiliser directement si :

- la tâche touche l'architecture ;
- la tâche est vague ;
- la tâche risque de modifier beaucoup de fichiers ;
- la tâche implique un nouveau système complet ;
- la tâche demande un refactor global.

### Livrable attendu

L'agent doit produire :

```text
Résumé du changement
Fichiers modifiés
Patch proposé
Explication simple
Tests à lancer
Risques restants
```

### Limites strictes

Cet agent ne doit pas :

- déplacer de logique métier dans `ui/` ;
- hardcoder du contenu de jeu dans `systems/` ;
- modifier `core/`, `systems/`, `ui/` et `data/` ensemble sans cadrage ;
- renommer des fichiers, classes ou fonctions sans demande explicite ;
- créer une abstraction générique prématurée.

### Niveau d'autonomie

Semi-autonome.

---

## 5. Agent Tests & Stabilité

### Problème résolu

Protéger les systèmes importants contre les régressions.

### Quand l'utiliser

Utiliser cet agent quand une tâche touche :

- `systems/` ;
- `entities/` ;
- `data/` ;
- combat ;
- inventaire ;
- loot ;
- progression ;
- économie ;
- effets temporaires ;
- équilibrage chiffré.

### Quand ne pas l'utiliser

Il peut être ignoré pour :

- un pur changement visuel ;
- une correction de texte ;
- une modification de documentation sans impact code.

### Livrable attendu

L'agent doit produire :

```text
Tests à ajouter ou modifier
Cas nominal
Cas limite
Cas de régression
Commande pytest ciblée
Commande pytest globale
```

### Limites strictes

Cet agent ne doit pas :

- changer le comportement du jeu seulement pour faire passer les tests ;
- lancer Pygame dans les tests si la logique peut être testée hors UI ;
- remplacer une review humaine ;
- ignorer les cas limites.

### Niveau d'autonomie

Semi-autonome.

---

## 6. Agent Review Architecture & Git

### Problème résolu

Détecter les dérives avant commit, PR ou merge.

### Quand l'utiliser

Utiliser cet agent :

- avant un commit important ;
- avant une PR ;
- avant un merge vers `main` ;
- après une modification touchant plusieurs dossiers ;
- après une modification proposée par l'IA.

### Quand ne pas l'utiliser

Il peut être ignoré pour une micro-correction évidente et déjà comprise.

### Livrable attendu

L'agent doit produire :

```text
Résumé de la review
Respect de l'architecture
Fichiers suspects
Tests manquants
Risque de régression
Proposition de découpage en commits
Verdict : OK / OK avec réserves / à reprendre
```

### Limites strictes

Cet agent ne doit pas :

- merger ;
- créer une branche ;
- supprimer une branche ;
- réécrire l'historique Git ;
- reformater tout le projet ;
- valider seul une décision d'architecture.

### Niveau d'autonomie

Consultatif.

---

## 7. Agents optionnels

Ces agents ne sont pas nécessaires en permanence.

### Agent Gameplay / Balance Data

À utiliser pour :

- XP ;
- or ;
- loot ;
- ennemis ;
- objets ;
- zones ;
- raretés ;
- données JSON.

Il peut proposer des valeurs, comparer des options ou identifier des risques de déséquilibre.

Il ne doit pas modifier les règles métier ou inventer une économie complète sans cadrage.

### Agent UI / UX / Narration

À utiliser pour :

- lisibilité des écrans ;
- textes de combat ;
- messages de résultat ;
- tooltips ;
- dialogues ;
- quêtes simples ;
- feedback joueur.

Il ne doit pas placer de logique métier dans `ui/`.

---

## 8. Workflows recommandés

### 8.1 Correction très simple

Ordre :

```text
Implémentation Localisée
Tests & Stabilité si logique concernée
Review Architecture & Git
```

Règles :

- 1 objectif ;
- 1 à 2 fichiers ;
- pas de refactor ;
- test de non-régression si possible.

---

### 8.2 Nouvelle feature locale

Ordre :

```text
Cadrage & Découpage
Implémentation Localisée
Tests & Stabilité
Review Architecture & Git
```

Règles :

- feature limitée ;
- fichiers autorisés définis avant code ;
- critères d'acceptation explicites ;
- test si logique métier.

---

### 8.3 Nouveau système

Ordre :

```text
Cadrage & Découpage
Validation humaine
Tests & Stabilité
Implémentation Localisée par tranche
Review Architecture & Git
Validation humaine avant merge
```

Règles :

- pas de système complet en une seule PR ;
- commencer par une V1 minimale ;
- documenter la décision si elle change l'architecture ;
- éviter les abstractions génériques trop tôt.

---

### 8.4 Sujet UI / UX / narration

Ordre :

```text
UI / UX / Narration
Cadrage & Découpage si plusieurs écrans sont touchés
Implémentation Localisée
Review Architecture & Git
```

Règles :

- l'UI affiche et collecte les entrées ;
- la logique métier reste dans `systems/` ;
- les données statiques restent dans `data/` ;
- les décisions narratives importantes peuvent être notées dans `docs/`.

---

### 8.5 Sujet architecture sensible

Ordre :

```text
Cadrage & Découpage
Review Architecture & Git
Validation humaine
Implémentation seulement si validée
```

Règles :

- pas de code avant accord ;
- pas de déplacement massif ;
- pas de renommage sans raison forte ;
- priorité à la stabilité.

---

### 8.6 Bug critique

Ordre :

```text
Cadrage rapide
Implémentation Localisée
Tests & Stabilité
Review Architecture & Git
```

Règles :

- corriger minimalement ;
- ne pas profiter du bugfix pour refactorer ;
- ajouter un test de non-régression si possible ;
- reporter les améliorations dans une autre issue.

---

### 8.7 Review de PR

Ordre :

```text
Review Architecture & Git
Tests & Stabilité
Décision humaine
```

Règles :

- vérifier la taille de la PR ;
- vérifier les fichiers modifiés ;
- vérifier les tests ;
- vérifier que la PR respecte son objectif ;
- demander un split si la PR mélange trop de sujets.

---

## 9. Matrice de décision

| Type de tâche | Agents à utiliser |
| --- | --- |
| Bug localisé | Implémentation Localisée -> Tests si logique -> Review |
| Petite UI | UI / UX / Narration -> Implémentation -> Review |
| Amélioration combat | Cadrage -> Implémentation -> Tests -> Review |
| Nouveau comportement ennemi | Cadrage -> Tests -> Implémentation -> Review |
| Modification JSON | Gameplay / Balance Data -> Review -> Tests si possible |
| Nouveau système | Cadrage -> Validation humaine -> Tests -> Implémentation par tranche -> Review |
| Refactorisation | Cadrage -> Review Architecture -> Validation humaine |
| GitHub Actions | Cadrage court -> Implémentation -> Review Git |
| PR avant merge | Review Architecture & Git -> Tests & Stabilité -> Décision humaine |
| Map Tiled | Cadrage -> Avis consultatif -> Validation humaine |
| Narration / dialogue | UI / UX / Narration -> Review cohérence docs/data |
| Équilibrage | Gameplay / Balance Data -> Tests ou simulation -> Décision humaine |

---

## 10. Garde-fous

### Fichiers généralement autorisés par type de tâche

| Type | Fichiers généralement concernés |
| --- | --- |
| Combat | `systems/combat.py`, `entities/enemy.py`, tests associés |
| Inventaire | `systems/inventory.py`, `data/items.json`, tests associés |
| Loot | `systems/loot.py`, `data/items.json`, tests associés |
| Progression | `systems/progression.py`, tests associés |
| UI | `ui/`, `ui/screens/` |
| Données | `data/*.json` |
| Documentation | `docs/*.md` |
| CI | `.github/workflows/*.yml` |

### Fichiers sensibles

À modifier seulement après cadrage explicite :

```text
main.py
core/*
systems/* si plusieurs systèmes sont touchés
data/*.json en masse
.github/workflows/*
```

### Actions interdites sans demande explicite

```text
Créer une branche
Supprimer une branche
Renommer une branche
Merger une branche
Réécrire l'historique Git
Supprimer des fichiers
Renommer des fichiers
Faire une refonte globale
Modifier beaucoup de fichiers sans cadrage
```

### Taille maximale recommandée

```text
1 objectif
1 comportement observable
1 à 3 fichiers modifiés si possible
1 test si logique métier
1 commit clair
```

Si une tâche dépasse 5 fichiers, elle doit repasser par l'Agent Cadrage & Découpage.

---

## 11. Checklist avant commit

Avant de commit, vérifier :

```text
La tâche correspond à l'objectif initial.
Les fichiers modifiés sont cohérents.
Aucun renommage inutile n'a été fait.
Aucune logique métier n'a été déplacée dans ui/.
Aucune donnée statique n'a été hardcodée dans systems/.
Les tests pertinents ont été ajoutés ou mis à jour.
pytest a été lancé si possible.
python main.py a été testé si l'UI est concernée.
Le commit peut être résumé en une phrase claire.
```

Exemples de commits :

```text
Add defensive enemy behavior
Fix combat reward propagation
Add combat behavior tests
Improve inventory tooltip text
```

---

## 12. Checklist avant PR

Avant d'ouvrir ou de merger une PR, vérifier :

```text
La PR a un objectif unique.
La description explique le changement.
Les fichiers modifiés sont listés ou faciles à comprendre.
Les tests lancés sont indiqués.
Les risques connus sont indiqués.
Ce qui n'est pas inclus est explicite.
La PR ne mélange pas bugfix, feature, refactor et équilibrage.
La PR ne doit pas être mergée vers main sans validation humaine.
```

---

## 13. Template d'issue AI-ready

Utiliser ce template pour donner une tâche claire à l'IA :

```text
## Objectif

Décrire le résultat attendu en une phrase.

## Contexte

Expliquer pourquoi la tâche existe et où elle s'inscrit dans la roadmap.

## Fichiers autorisés

- ...

## Fichiers interdits

- ...

## Comportement attendu

- ...

## Critères d'acceptation

- ...

## Tests attendus

- ...

## Contraintes

- Pas de refactor global.
- Pas de renommage inutile.
- Préserver le comportement existant.
- Modifier le moins de fichiers possible.

## Livrable attendu de l'IA

- Résumé du changement.
- Fichiers modifiés.
- Patch ou proposition.
- Tests à lancer.
- Risques restants.
```

---

## 14. Règle finale

L'IA doit aider à avancer par petits pas.

Elle ne doit pas remplacer la compréhension du projet.

Quand une tâche devient floue, large ou risquée, il faut revenir au cadrage avant de coder.
