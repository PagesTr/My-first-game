# Dev jeu — boucle d’instance auto

## Objectif du bloc

Ce document formalise les décisions de gameplay prises pour transformer le combat isolé actuel en une boucle d’instance automatique.

L’objectif n’est pas simplement d’enchaîner plusieurs combats visibles, mais de créer une vraie boucle de gameplay orientée :

- expédition automatique ;
- mort inévitable du joueur ;
- récapitulatif global ;
- loot cumulé ;
- optimisation progressive du build.

Le joueur doit partir en expédition, aller le plus loin possible, mourir, récupérer ses gains, améliorer son personnage, puis repartir.

---

## Vision gameplay validée

La boucle cible est :

```text
Ville
→ choix d’une zone
→ départ en expédition
→ combats automatiques instantanés
→ mort du joueur
→ récapitulatif global
→ gestion du loot et du build
→ nouvelle expédition
```

Le principe central est le suivant :

```text
Le joueur ne termine jamais une instance vivant.
Il cherche à mourir plus loin que lors de l’expédition précédente.
```

Le score naturel d’une expédition devient donc le nombre de combats gagnés avant la mort.

Exemple de récapitulatif attendu :

```text
Expédition terminée
Zone : Mystic Forest
Combats gagnés : 17
Mort contre : Wolf renforcé
XP gagnée : 142
Gold gagné : 87
Objets trouvés : 23
Meilleur drop : Iron Sword rare
```

---

## Décisions validées

### 1. Condition de fin d’instance

Une instance s’arrête uniquement quand le joueur meurt.

Conséquences :

- pas de limite fixe de combats ;
- pas d’arrêt volontaire ;
- pas de retour vivant ;
- pas de bouton pour quitter l’expédition ;
- l’équilibrage doit garantir que le joueur finit par mourir.

Cette règle définit l’identité du jeu.

---

### 2. Simulation instantanée

En V1, les instances doivent être simulées instantanément.

Le joueur clique sur une zone, le jeu simule tous les combats jusqu’à la mort, puis affiche directement le récapitulatif final.

À terme, il sera possible d’ajouter une version visuelle ou déroulante pour expliquer ce qu’il se passe, mais ce n’est pas nécessaire pour la première version.

Objectif V1 :

```text
Clic sur une zone → simulation complète → écran de résultat global.
```

---

### 3. Suppression du heal actif

Le système de soin actif doit être supprimé du combat de base.

Le comportement attendu est simple :

```text
Le joueur attaque.
L’ennemi attaque.
Le combat continue jusqu’à la mort d’un des deux.
```

Raisons :

- le heal ralentit artificiellement les combats ;
- il peut créer des boucles trop longues ;
- il rend la durée d’instance moins lisible ;
- il contredit l’idée que le joueur finit forcément par mourir.

Les mécaniques de survie pourront revenir plus tard sous une forme plus intéressante :

- vol de vie ;
- régénération très limitée ;
- bouclier temporaire ;
- potion automatique ;
- récupération partielle après victoire ;
- passifs de classe ou de compétence.

Mais elles ne doivent pas faire partie du socle V1.

---

### 4. Points de vie pendant l’expédition

Le joueur commence l’expédition avec ses points de vie au maximum.

Ensuite :

```text
Le joueur ne récupère pas ses PV entre les combats.
```

Sa barre de vie devient une ressource d’expédition.

Chaque combat gagné entame potentiellement cette ressource, jusqu’à ce qu’un ennemi finisse par tuer le joueur.

Cette règle rend la progression lisible :

- meilleur équipement = plus de combats gagnés ;
- meilleure défense = dégâts ralentis ;
- meilleure attaque = ennemis tués plus vite ;
- meilleurs PV = plus grande profondeur d’expédition.

---

### 5. Scaling des ennemis

Les ennemis doivent devenir progressivement plus forts pendant l’expédition.

Objectif : éviter qu’un joueur trop fort puisse survivre indéfiniment dans une zone.

Principe recommandé pour la V1 :

```text
Chaque combat gagné augmente légèrement la puissance du prochain ennemi.
```

Exemple de formule simple :

```text
enemy_power_multiplier = zone_difficulty_multiplier * (1 + completed_combats * 0.06)
```

Avec cette logique :

| Combat | Multiplicateur ajouté |
| ---: | ---: |
| 1 | x1.00 |
| 2 | x1.06 |
| 3 | x1.12 |
| 4 | x1.18 |
| 5 | x1.24 |
| 10 | x1.54 |
| 20 | x2.14 |

La valeur de 6 % est une base prudente.

Elle pourra être ajustée après observation des premières simulations.

---

### 6. Loot cumulé à la fin

Le loot n’est pas géré après chaque combat.

Pendant l’expédition :

- chaque victoire génère du loot ;
- les drops sont ajoutés à un résultat temporaire d’instance ;
- rien n’est ajouté immédiatement à l’inventaire.

À la mort du joueur :

- le récapitulatif global affiche le loot total ;
- le joueur peut récupérer les objets ;
- si l’inventaire est plein, la logique existante de loot temporaire peut être réutilisée ou adaptée.

---

### 7. Pas de cap arbitraire sur les équipements

Il ne faut pas limiter artificiellement le résultat à un nombre fixe d’équipements, par exemple “garder seulement les 20 meilleurs”.

Cette solution est trop directive pour le design du jeu.

Décision validée :

```text
On adapte les sources de drop plutôt que de couper arbitrairement le résultat final.
```

Cela laisse de la place pour de futures mécaniques :

- sacrifice d’objets ;
- recyclage ;
- vente automatique ;
- essence magique ;
- craft ;
- forge ;
- filtres de rareté ;
- auto-salvage ;
- collection ;
- transformation des doublons.

L’abondance d’items peut devenir une mécanique de progression plus tard.

---

### 8. Adaptation des drops

Comme le loot est cumulé à la fin, les tables de drop doivent être adaptées pour éviter un overflow permanent dès la V1.

Approche recommandée :

- fusionner les objets stackables identiques ;
- réduire les chances de drop absurdes si nécessaire ;
- conserver les équipements comme objets individuels ;
- ne pas encore créer de système de sacrifice ou recyclage.

Le réglage des drops doit rester simple au départ.

Objectif : éviter que chaque expédition génère une quantité ingérable d’équipements, sans bloquer les futures mécaniques d’abondance.

---

## Récapitulatif global attendu

L’écran de résultat doit devenir le cœur de la boucle.

Il doit afficher un résultat d’expédition, pas seulement un résultat de combat.

Informations utiles en V1 :

- nom de la zone ;
- nombre de combats gagnés ;
- ennemi fatal ;
- XP totale gagnée ;
- gold total gagné ;
- nombre total d’objets trouvés ;
- liste du loot ;
- niveau actuel du joueur ;
- indication de level up si applicable.

Exemple :

```text
Expédition terminée

Zone : Mystic Forest
Combats gagnés : 17
Mort contre : Wolf

XP gagnée : 142
Gold gagné : 87
Objets trouvés : 23
Niveau actuel : 4

Butin d’expédition
[loot]
```

---

## Architecture recommandée

### Fichier recommandé à créer

```text
systems/instance.py
```

Responsabilité : contenir la logique métier de simulation d’une expédition.

Raisons :

- la simulation complète d’une instance est de la logique métier ;
- `core/game.py` doit rester un orchestrateur ;
- cela facilite les tests unitaires ;
- cela évite de surcharger `Game` avec une boucle complexe.

Fonctions possibles :

```python
run_instant_instance(...)
create_empty_instance_result(...)
merge_instance_drops(...)
apply_instance_enemy_scaling(...)
```

Le code devra rester simple, sans grosse classe au départ.

---

### Rôle de `core/game.py`

`core/game.py` doit seulement :

- recevoir le choix de zone ;
- lancer la simulation d’instance ;
- stocker le résultat final ;
- passer à l’état d’écran de résultat.

Exemple logique :

```python
self.last_instance_result = run_instant_instance(...)
self.last_combat_result = self.last_instance_result
self.state = "combat_result"
```

La compatibilité avec `last_combat_result` peut être conservée temporairement pour limiter les modifications UI.

---

### Rôle de `systems/combat.py`

`systems/combat.py` doit rester responsable d’un combat individuel.

Modification attendue :

- supprimer l’action `heal` ;
- faire en sorte que l’action automatique du joueur soit `attack` ;
- conserver les mécaniques existantes de dégâts, critique, esquive, blocage et fin de combat.

---

### Rôle de `systems/loot.py`

`systems/loot.py` reste responsable de la génération de loot d’un combat.

Il n’a pas besoin de connaître la notion d’instance.

La fusion des drops d’instance peut être faite dans `systems/instance.py`.

---

### Rôle de `systems/progression.py`

`systems/progression.py` reste responsable de l’application des récompenses XP/gold.

Chaque combat gagné peut continuer à appeler `apply_combat_rewards()`.

Le résultat d’instance cumulera ensuite les valeurs retournées.

---

### Rôle de `ui/screens/result_screen.py`

L’écran de résultat doit être adapté pour afficher une expédition complète.

Modification minimale recommandée :

- remplacer le titre combat par un titre d’expédition ;
- afficher les champs globaux de l’instance ;
- conserver autant que possible la logique de loot existante ;
- éviter de créer un nouvel écran en V1.

---

### Rôle de `ui/screens/combat_screen.py`

À court terme, l’écran de combat peut rester dans le projet.

Il peut servir :

- pour debug ;
- pour une future visualisation déroulante ;
- pour expliquer le combat au joueur dans une V2.

Mais il ne doit plus être le chemin principal de gameplay si l’instance instantanée est activée depuis le choix de zone.

---

## Tests recommandés

Les tests doivent éviter l’UI Pygame et viser la logique métier.

Tests prioritaires pour `systems/instance.py` :

1. Une instance se termine par la mort du joueur.
2. Le résultat contient un nombre de combats gagnés.
3. XP et gold sont cumulés.
4. Les drops stackables identiques sont fusionnés.
5. Les équipements restent individuels.
6. Le scaling ennemi augmente avec la profondeur d’expédition.
7. Le heal n’est plus utilisé dans le combat automatique.
8. Le résultat contient l’ennemi fatal.

Tests complémentaires possibles :

- vérifier qu’une zone vide ou invalide est ignorée proprement ;
- vérifier que le joueur commence full HP ;
- vérifier que les PV restants ne sont pas restaurés entre deux combats ;
- vérifier que le résultat final reste compatible avec `ResultScreen`.

---

## Proposition de V1

La première version stable du bloc doit viser ceci :

```text
Quand le joueur choisit une zone, le jeu lance une expédition instantanée.
Le joueur démarre full HP.
Les combats sont simulés automatiquement avec attaque uniquement.
Après chaque victoire, XP, gold et loot sont cumulés.
Les ennemis deviennent progressivement plus forts.
Le joueur ne récupère pas ses PV entre les combats.
L’expédition s’arrête uniquement quand le joueur meurt.
Le résultat final affiche le nombre de combats gagnés, les gains et le loot cumulé.
Les objets stackables sont fusionnés.
Les équipements restent individuels.
```

---

## Hors périmètre V1

À ne pas faire immédiatement :

- créer une carte d’instance ;
- ajouter des événements aléatoires ;
- ajouter des boss ;
- créer un écran complet de déroulement d’expédition ;
- ajouter un bouton d’arrêt volontaire ;
- ajouter un retour vivant ;
- ajouter un système de sacrifice d’objets ;
- ajouter un système de recyclage ;
- refondre tout l’équilibrage ;
- refondre l’inventaire ;
- modifier profondément l’UI de combat.

---

## Propositions pour les versions suivantes

### V2 — Lisibilité de l’expédition

Ajouter une visualisation optionnelle :

- log résumé des combats ;
- affichage combat par combat rapide ;
- bouton “skip” ;
- vitesse de simulation ;
- mise en avant de l’ennemi fatal.

Objectif : aider le joueur à comprendre pourquoi il est mort.

---

### V3 — Gestion de l’abondance d’items

Introduire des mécaniques pour valoriser les objets en trop :

- sacrifice d’équipements ;
- recyclage en ressources ;
- vente automatique ;
- extraction d’essence ;
- craft ;
- forge ;
- filtres automatiques selon rareté.

Objectif : transformer l’abondance en ressource de progression.

---

### V4 — Profondeur de build

Ajouter des mécaniques qui rendent les builds plus distincts :

- vol de vie ;
- boucliers ;
- dégâts sur la durée ;
- récupération partielle après combat ;
- passifs de classe ;
- effets d’équipement ;
- synergies entre stats.

Objectif : permettre plusieurs façons de tenir plus longtemps.

---

### V5 — Identité des zones

Donner une identité mécanique à chaque zone :

- ennemis plus rapides ;
- ennemis plus résistants ;
- meilleur loot mais scaling plus violent ;
- zones orientées ressources ;
- zones orientées équipements ;
- zones avec boss fatal plus probable.

Objectif : rendre le choix de zone intéressant, pas seulement linéaire.

---

## Branche conseillée pour l’implémentation

Branche de départ :

```text
integ
```

Nom conseillé :

```text
auto-instance-loop
```

Objectif :

```text
Créer la première version de la boucle d’expédition automatique sacrificielle.
```

PR cible :

```text
integ
```

---

## Résumé final

La boucle d’instance validée est une boucle sacrificielle.

Le joueur ne cherche pas à survivre à une expédition, mais à mourir plus loin que la fois précédente.

Le gameplay repose sur :

- combat automatique ;
- mort inévitable ;
- loot cumulé ;
- récapitulatif global ;
- optimisation du build ;
- relance rapide d’une nouvelle expédition.

C’est ce bloc qui doit devenir le cœur du gameplay du jeu.
