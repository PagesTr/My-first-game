# Cahier des charges - Projet de jeu Python / Pygame

## 1. Présentation du projet

Le projet consiste à développer un jeu en Python avec Pygame, avec une architecture simple, modulaire et évolutive.

L’objectif principal est de créer un jeu jouable progressivement, en ajoutant les fonctionnalités étape par étape, sans refonte globale et sans casser les éléments déjà fonctionnels.

Le projet sert aussi de support d’apprentissage pour progresser en Python, Pygame, architecture de projet, tests automatisés avec pytest, Git et GitHub Actions.

## 2. Objectif du jeu

Le jeu doit proposer une expérience orientée RPG, progression et optimisation.

Le joueur doit pouvoir :

- incarner un personnage ;
- choisir une classe ;
- affronter des ennemis ;
- gagner de l’expérience et de l’or ;
- récupérer du loot ;
- gérer un inventaire ;
- améliorer ses statistiques ;
- progresser dans une boucle de jeu simple.

L’objectif final n’est pas encore de produire un jeu complet commercialisable, mais de construire une base solide, compréhensible et évolutive.

## 3. Type de jeu visé

Le jeu s’oriente vers un mélange de :

- RPG simple ;
- jeu de combat ;
- système de loot ;
- progression de personnage ;
- optimisation d’équipement.

Le gameplay doit rester simple au départ, avec une logique testable et peu dépendante de l’interface graphique.

## 4. Boucle de gameplay principale

La boucle de jeu cible est la suivante :

1. Le joueur lance une partie.
2. Il choisit une classe.
3. Il choisit une zone.
4. Il rencontre un ennemi.
5. Un combat se déroule.
6. Le joueur gagne ou perd.
7. En cas de victoire, il reçoit de l’expérience, de l’or et éventuellement du loot.
8. Les objets obtenus peuvent être ajoutés à l’inventaire.
9. Le joueur peut continuer sa progression.

Cette boucle doit être développée progressivement.

## 5. Fonctionnalités prévues

### 5.1 Joueur

Le jeu doit contenir un système de joueur avec au minimum :

- nom ;
- classe ;
- points de vie ;
- attaque ;
- défense ;
- niveau ;
- expérience ;
- or ;
- potions ;
- équipement ;
- inventaire.

Fonctionnalités futures possibles :

- choix de statistiques à améliorer ;
- équipement d’objets uniques ;
- compétences spéciales ;
- sauvegarde de la progression.

### 5.2 Ennemis

Chaque ennemi doit pouvoir avoir :

- nom ;
- niveau ;
- points de vie ;
- attaque ;
- défense ;
- récompense d’expérience ;
- récompense d’or ;
- table de loot.

Les ennemis peuvent être adaptés selon le niveau du joueur, la zone, la difficulté ou la rareté.

### 5.3 Combat

Le système de combat doit gérer :

- les dégâts du joueur vers l’ennemi ;
- les dégâts de l’ennemi vers le joueur ;
- les actions de combat simples ;
- la victoire du joueur ;
- la défaite du joueur ;
- un résultat de combat clair.

Le combat doit rester testable sans lancer Pygame.

### 5.4 Progression

Le joueur doit pouvoir gagner :

- de l’expérience ;
- de l’or ;
- des niveaux.

La montée de niveau peut rester simple au départ, puis évoluer vers un système plus complet avec choix de statistiques.

### 5.5 Inventaire

Le joueur possède un inventaire logique basé sur des slots.

L’inventaire doit permettre :

- d’ajouter des ressources empilables ;
- d’ajouter des équipements uniques ;
- de déplacer des objets entre slots ;
- de préparer une future interface graphique ;
- de préparer le tri, le craft et l’équipement.

Le drag & drop, le tri et le craft doivent être ajoutés progressivement.

### 5.6 Objets et loot

Un objet peut avoir :

- id ;
- nom ;
- type ;
- statistiques ;
- quantité pour les ressources empilables ;
- statistiques aléatoires pour les équipements uniques.

Types possibles :

- arme ;
- armure ;
- accessoire ;
- consommable ;
- ressource ;
- monnaie ;
- matériau.

Le système de loot doit permettre de générer une récompense après un combat gagné.

### 5.7 Interface Pygame

L’interface doit permettre au joueur d’interagir avec le jeu.

Elle doit gérer :

- la fenêtre Pygame ;
- les événements clavier et souris ;
- les écrans du jeu ;
- les boutons ;
- l’affichage du combat ;
- l’affichage du résultat ;
- l’affichage de l’inventaire.

L’interface ne doit pas contenir la logique métier principale. Elle doit appeler les systèmes existants au lieu de les remplacer.

## 6. Architecture du projet

La structure actuelle et cible du projet est organisée autour de plusieurs dossiers :

```text
project/
├── main.py
├── core/
├── entities/
├── systems/
├── ui/
├── data/
├── assets/
├── tests/
├── requirements.txt
└── README.md
```

Cette structure peut évoluer, mais sans refonte inutile.

## 7. Rôle des dossiers

### core/

Contient l’orchestration principale du jeu.

Exemples :

- gestion de l’état global ;
- sélection de classe ;
- sélection de zone ;
- démarrage du combat ;
- transition entre les écrans.

### entities/

Contient les entités principales du jeu.

Exemples :

- joueur ;
- ennemis ;
- création des instances de personnages ou d’ennemis.

### systems/

Contient les systèmes de logique de jeu.

Exemples :

- combat ;
- progression ;
- loot ;
- inventaire ;
- équipement ;
- statistiques.

Ces systèmes doivent rester testables avec pytest sans ouvrir de fenêtre Pygame.

### ui/

Contient l’affichage et les interactions Pygame.

Exemples :

- application Pygame ;
- écrans ;
- boutons ;
- barres de vie ;
- événements clavier et souris ;
- affichage du combat, du résultat et de l’inventaire.

Ce dossier ne doit pas contenir la logique métier principale.

### data/

Contient les données du jeu au format JSON.

Exemples :

- classes ;
- ennemis ;
- objets ;
- zones ;
- recettes.

### assets/

Contient les ressources externes du jeu.

Exemples :

- images ;
- sons ;
- polices ;
- musiques.

Ce dossier peut être créé ou complété lorsque les ressources graphiques et audio deviennent nécessaires.

### tests/

Contient les tests automatisés avec pytest.

Les fichiers doivent être nommés :

```text
test_*.py
```

Exemples :

- `test_imports.py` ;
- `test_combat.py` ;
- `test_inventory.py` ;
- `test_loot.py` ;
- `test_progression.py`.

## 8. Contraintes techniques

Le projet doit respecter les contraintes suivantes :

- langage : Python ;
- bibliothèque graphique : Pygame ;
- tests : pytest ;
- versionnement : Git ;
- intégration continue : GitHub Actions ;
- architecture modulaire ;
- modifications progressives ;
- code lisible et simple ;
- aucune dépendance externe inutile.

Le projet doit pouvoir être lancé localement avec :

```bash
python main.py
```

Les tests doivent pouvoir être lancés avec :

```bash
pytest
```

## 9. Règles de développement

Chaque évolution doit respecter ces règles :

- modifier le moins de fichiers possible ;
- éviter les refactorisations globales ;
- préserver le comportement existant ;
- ne pas renommer inutilement les fichiers, classes ou fonctions ;
- ajouter des tests quand une logique importante est ajoutée ;
- vérifier que le jeu se lance encore ;
- vérifier que pytest passe.

Méthode recommandée :

1. Ajouter une petite fonctionnalité.
2. Faire une modification ciblée.
3. Ajouter un test si possible.
4. Lancer `pytest`.
5. Lancer le jeu localement si l’UI est concernée.
6. Faire un commit Git clair.

## 10. Tests attendus avec pytest

Les tests doivent couvrir en priorité la logique hors interface graphique.

### Combat

- un joueur peut infliger des dégâts ;
- un ennemi peut infliger des dégâts ;
- un ennemi meurt quand ses PV atteignent 0 ;
- le joueur meurt quand ses PV atteignent 0 ;
- un combat retourne un résultat clair.

### Inventaire

- création d’un inventaire ;
- ajout d’un objet empilable ;
- ajout d’un objet unique ;
- déplacement entre slots ;
- gestion d’un inventaire plein ;
- gestion d’un inventaire vide.

### Loot

- génération d’un drop empilable ;
- génération d’un équipement unique ;
- génération de statistiques aléatoires ;
- absence de loot si aucun drop n’est défini ;
- ajout des drops dans l’inventaire.

### Progression

- gain d’expérience ;
- gain d’or ;
- montée de niveau ;
- gestion de plusieurs niveaux gagnés en une fois.

### Imports

- les modules principaux peuvent être importés sans erreur ;
- les tests n’exécutent pas directement la boucle Pygame.

## 11. Git et GitHub Actions

Le projet doit utiliser Git pour suivre les modifications.

Chaque commit doit être clair et ciblé.

Exemples :

- `Add basic combat rewards`
- `Add inventory slot model`
- `Fix enemy drops propagation`
- `Add pytest import smoke test`

GitHub Actions doit permettre de vérifier automatiquement que les tests passent.

Le workflow doit au minimum :

1. récupérer le projet ;
2. installer Python ;
3. installer les dépendances ;
4. lancer pytest.

## 12. Roadmap progressive

### Étape 1 - Base technique stable

Objectif : avoir un projet qui se lance et se teste.

À faire :

- vérifier la structure des dossiers ;
- vérifier `main.py` ;
- vérifier les dépendances ;
- vérifier pytest ;
- vérifier GitHub Actions.

Résultat attendu :

- `python main.py` fonctionne ;
- pytest trouve au moins un test ;
- GitHub Actions passe au vert.

### Étape 2 - Base gameplay

Objectif : créer une première boucle jouable.

À faire :

- joueur ;
- classes ;
- ennemis ;
- zones ;
- combat simple ;
- victoire et défaite ;
- affichage minimal.

Résultat attendu :

- le joueur peut combattre un ennemi ;
- le combat a une issue claire.

### Étape 3 - Récompenses et progression

Objectif : donner une première sensation de progression.

À faire :

- expérience ;
- or ;
- montée de niveau ;
- écran de résultat.

Résultat attendu :

- le joueur reçoit une récompense après une victoire ;
- le résultat du combat est visible.

### Étape 4 - Inventaire et objets

Objectif : commencer la progression RPG par les objets.

À faire :

- inventaire à slots ;
- ressources empilables ;
- équipements uniques ;
- ajout d’objets après combat ;
- affichage de l’inventaire.

Résultat attendu :

- le joueur peut gagner un objet ;
- l’objet est stocké dans l’inventaire ;
- le contenu est visible dans l’interface.

### Étape 5 - Loot et raretés

Objectif : rendre les récompenses plus intéressantes.

À faire :

- raretés ;
- tables de loot plus riches ;
- bonus de statistiques ;
- équipements plus ou moins rares.

Résultat attendu :

- chaque victoire peut donner une récompense intéressante ;
- les objets ont des valeurs différentes.

### Étape 6 - Interface plus propre

Objectif : rendre le jeu plus agréable à jouer.

À faire :

- écran principal ;
- écran de combat plus lisible ;
- écran d’inventaire plus complet ;
- boutons cohérents ;
- messages de combat ;
- affichage des statistiques.

Résultat attendu :

- le joueur comprend clairement ce qui se passe à l’écran.

### Étape 7 - Craft et équipement

Objectif : enrichir la gestion d’objets.

À faire :

- recettes ;
- craft ;
- équipement d’objets ;
- comparaison de statistiques.

Résultat attendu :

- le joueur peut transformer des ressources et optimiser son personnage.

### Étape 8 - Sauvegarde

Objectif : conserver la progression.

À faire :

- sauvegarder le joueur ;
- sauvegarder l’inventaire ;
- charger une partie existante.

Résultat attendu :

- le joueur peut reprendre sa progression.

## 13. Version jouable minimale

La première version jouable minimale doit contenir :

- une fenêtre Pygame fonctionnelle ;
- un joueur ;
- une classe sélectionnable ;
- une zone sélectionnable ;
- un ennemi ;
- un combat simple ;
- une condition de victoire ou de défaite ;
- un écran de résultat ;
- un inventaire visible ;
- au moins quelques tests pytest.

Cette version ne doit pas forcément contenir :

- graphismes avancés ;
- animations ;
- musique ;
- sauvegarde ;
- équilibrage complexe ;
- génération procédurale ;
- interface complète ;
- craft complet ;
- drag & drop avancé.

## 14. Principes de qualité

Le projet doit rester :

- simple ;
- lisible ;
- stable ;
- pédagogique ;
- évolutif.

Un code simple qui fonctionne est préférable à une architecture complexe difficile à comprendre.

La priorité est :

```text
stabilité > lisibilité > évolutivité > optimisation
```
