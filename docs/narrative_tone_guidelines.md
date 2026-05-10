# Narrative Tone Guidelines

## Objectif

Ce document cadre le ton narratif du jeu, notamment pour les dialogues, quetes, succes, descriptions d'objets, rapports d'expedition et textes d'ambiance.

Le jeu doit rester coherent avec son theme central :

```text
les expeditions finissent souvent mal,
les personnages meurent,
le monde garde leurs traces,
et la progression continue malgre tout.
```

Le ton doit melanger :

```text
humour sarcastique
humour taquin
fantasy absurde controlee
epique ponctuel
melancolie legere autour des personnages tombes
```

Reference d'ambiance : esprit Donjon de Naheulbeuk, mais adapte au theme du jeu et sans copier de personnages, phrases ou situations existantes.

---

## Intention generale

Le jeu ne doit pas etre trop serieux, meme si son concept tourne autour de la mort des aventuriers.

La bonne tonalite :

```text
Le monde est dangereux.
Les personnages sont courageux.
Le narrateur sait tres bien qu'ils vont probablement finir dans un buisson.
```

Le joueur doit ressentir :

```text
curiosite
sourire
satisfaction de progression
envie de lire les quetes et descriptions
attachement au monde malgre l'absurde
```

---

## Ton des dialogues

### Sarcastique / taquin

A utiliser pour :

```text
rapports d'echec
quetes de depart
objets mediocres
gobelins
petites recompenses
commentaires de retour d'expedition
```

Exemples de style :

```text
"Vous avez trouve trois herbes medicinales. Deux etaient probablement medicinales."
"Le gobelin avait l'air confiant. C'est important, la confiance. Surtout avant de perdre."
"Un autre aventurier est tombe ici. Bonne nouvelle : il avait laisse des ossements exploitables."
"La foret vous observe. Elle juge surtout votre equipement."
```

### Epique ponctuel

A utiliser pour :

```text
boss
fin de chapitre
donjons
sets complets
quetes majeures
succes importants
```

Exemples de style :

```text
"Sous les racines, les noms des anciens heros murmurent encore."
"Grubfang leve son totem. La foret repond. Mauvaise nouvelle : elle repond fort."
"Vous ne quittez pas le Bosquet Enfoui indemne. Personne ne le fait vraiment."
```

### Humour + menace

Le meilleur ton du jeu doit souvent melanger les deux :

```text
"Le camp gobelin est silencieux. Trop silencieux. Ou alors ils dorment. Dans les deux cas, c'est l'occasion de faire une erreur heroique."
```

---

## Ton par type de texte

### Quetes

Les quetes doivent guider le joueur avec une phrase d'ambiance courte, puis un objectif clair.

Structure recommandee :

```text
Titre de quete
Phrase d'ambiance sarcastique ou epique courte.
Objectifs lisibles.
Recompense claire.
```

Exemple :

```text
Secure the Outskirts
La lisiere de la foret est infestee de rats, de gobelins et de mauvaises decisions.
- Defeat 5 Forest Rats
- Defeat 3 Young Goblins
Reward: 25 gold, Herbal Poultice recipe
```

### Succes

Les succes peuvent etre plus taquins.

Exemples :

```text
Rat Cleaner I
Vous avez vaincu 25 rats. La foret ne vous respecte pas encore, mais les rats commencent a s'organiser.

Set Apprentice
Deux pieces du meme set equipees. C'est presque une strategie.
```

### Objets

Les objets doivent avoir une description courte qui raconte leur origine.

Exemples :

```text
Wolf Fang Charm
Une dent de loup attachee a une racine sechee. Peu elegant, mais les loups n'ont jamais ete connus pour leur joaillerie.

Broken Adventurer Tag
Le nom est illisible. Le destin, lui, est assez clair.

Goblin Lucky Totem
Chanceux selon les gobelins. Les statistiques de survie restent discutables.
```

### Donjons

Les donjons doivent avoir une introduction plus marquee.

Exemple :

```text
Goblin Camp
De la fumee monte entre les arbres. Quelque part, un gobelin a decouvert le feu, l'organisation et probablement la fraude fiscale.
```

### Boss

Les boss peuvent etre plus epiques, avec une chute sarcastique occasionnelle.

Exemple :

```text
Grubfang, Rootcaller
Les racines se tordent sous ses pieds. Son totem pulse d'une energie ancienne. Il va probablement crier quelque chose de dramatique.
```

---

## Regles d'ecriture

### A faire

```text
phrases courtes
images fantasy simples
humour discret mais frequent
objectifs toujours clairs
recompenses lisibles
sarcasme sans casser la comprehension
moments epiques reserves aux jalons importants
```

### A eviter

```text
blagues trop longues
references modernes trop presentes
parodies directes d'oeuvres existantes
murs de texte
humour qui masque les objectifs
sarcasme permanent qui retire tout enjeu
lore trop dense trop tot
```

---

## Intensite du ton

| Contexte | Humour | Epique | Clarite gameplay |
|---|---:|---:|---:|
| Item commun | eleve | faible | moyenne |
| Item rare | moyen | moyen | moyenne |
| Set complet | moyen | eleve | elevee |
| Quete principale | moyen | moyen/eleve | tres elevee |
| Succes | eleve | faible/moyen | elevee |
| Donjon | moyen | eleve | tres elevee |
| Boss | faible/moyen | tres eleve | tres elevee |
| Resultat d'echec | eleve | faible | elevee |

---

## Lien avec le theme central

Le theme des aventuriers morts doit rester present, mais pas morbide gratuitement.

Bon angle :

```text
Les morts precedents servent de memoire du monde.
Les ossements, reliques et traces racontent les echecs passes.
Le joueur transforme ces echecs en progression.
```

Exemples :

```text
"Quelqu'un a perdu cette amulette ici. Puis le bras qui allait avec."
"Les ossements sont anciens, mais l'archeologue assure qu'ils sont encore utiles. C'est important, l'optimisme."
"Chaque expedition ajoute une ligne a l'histoire. Parfois une ligne tres courte."
```

---

## Application au chapitre Foret

La Foret doit commencer presque ridicule :

```text
rats
gobelins maladroits
loups opportunistes
premieres herbes
premiers ossements
```

Puis devenir progressivement plus inquietante :

```text
traces d'anciens aventuriers
racines anormales
totems gobelins
bosquet enfoui
boss rootcaller
```

Progression de ton :

```text
Palier 1: leger, taquin, initiation
Palier 2: aventure, danger modere
Palier 3: morts anciennes, sarcasme noir leger
Palier 4: donjons, tension fantasy
Palier 5: boss, epique avec une pointe d'absurde
```

---

## Note technique future

Les textes narratifs pourront etre ajoutes progressivement dans :

```text
data/items.json
data/enemies.json
data/quests.json
data/achievements.json
data/dungeons.json
```

Champs possibles plus tard :

```text
description
flavor_text
intro_text
completion_text
failure_text
sarcastic_note
```

Ne pas ajouter tous ces champs tant que le systeme qui les lit n'existe pas.
Commencer par description et flavor_text suffit.
