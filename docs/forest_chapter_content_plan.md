# Forest Chapter Content Plan

## Objectif du document

Ce document cadre le premier vrai chapitre de contenu du jeu : la Foret.

L'objectif n'est pas encore d'equilibrer les chiffres finement. L'objectif est de structurer le contenu pour obtenir une boucle RPG idle coherente, lisible et satisfaisante.

Le chapitre Foret doit servir de modele pour les futurs chapitres : Caves, Mountains, puis zones plus avancees.

---

## Ton narratif du chapitre

Le chapitre Foret doit suivre les principes de `docs/narrative_tone_guidelines.md` :

```text
humour sarcastique / taquin
fantasy absurde controlee
epique ponctuel
mort des aventuriers traitee comme une memoire du monde
```

La Foret commence avec un ton leger : rats, gobelins maladroits, loups opportunistes, premieres recoltes. Puis elle devient progressivement plus inquietante : ossements, anciens aventuriers, racines anormales, totems, boss Rootcaller.

Exemples de tonalite attendue :

```text
"La lisiere de la foret est infestee de rats, de gobelins et de mauvaises decisions."
"Un autre aventurier est tombe ici. Bonne nouvelle : il avait laisse des ossements exploitables."
"Le camp gobelin est silencieux. Trop silencieux. Ou alors ils dorment. Dans les deux cas, c'est l'occasion de faire une erreur heroique."
"Grubfang leve son totem. La foret repond. Mauvaise nouvelle : elle repond fort."
```

Regle importante : l'humour ne doit jamais masquer les objectifs, les recompenses ou la lisibilite gameplay.

---

## Vision du chapitre Foret

La Foret doit raconter une progression complete :

```text
Town
-> Forest Outskirts
-> Deeper Trails
-> Buried Paths
-> Goblin Camp
-> Buried Grove
-> Forest boss
-> unlock next chapter
```

Le joueur doit progressivement exploiter :

```text
combat
active gathering
offline gathering
craft
sets
professions
quests
achievements
dungeons
boss progression
```

La Foret ne doit pas etre juste une zone de depart. Elle doit devenir un premier chapitre complet, avec une identite claire.

---

## Principes de design retenus

### 1. Ressource specifique par ennemi

Chaque ennemi important doit avoir au moins une ressource specifique.

Exemples :

```text
Young Goblin -> goblin_ear
Goblin Scout -> scout_badge
Forest Wolf -> wolf_fang
Thorn Sprite -> thorn_essence
Lost Adventurer -> broken_adventurer_tag
Goblin Shaman -> shaman_totem
Alpha Wolf -> alpha_fang
```

### 2. Ressources rares selectives

Tous les ennemis ne doivent pas avoir une ressource rare.

Les ressources rares doivent rester excitantes, lisibles et memorables. Elles doivent etre reservees a certains ennemis marquants, mini-boss, boss, ou ennemis de transition narrative.

Bon usage :

```text
Forest Wolf -> wild_heart
Lost Adventurer -> rusted_ring
Goblin Shaman -> ritual_paint
Alpha Wolf -> alpha_fang
Boss -> forest_core
```

Mauvais usage :

```text
chaque rat a un drop rare
chaque gobelin a une relique unique
chaque ennemi a trois composants rares
```

### 3. Certains items de set peuvent dropper directement

Tous les items de set ne doivent pas venir du craft.

Pour rendre le farm plus satisfaisant :

```text
certains items de set peuvent dropper directement sur des ennemis specifiques
certains items de set viennent du craft
certains items de set viennent de quetes
certains items de set viennent de donjons ou boss
```

Priorite : faire dropper des pieces de set sur des ennemis hors donjon, pour donner de l'interet aux zones generiques.

Exemples :

```text
Forest Wolf -> Wolf Stalker Boots
Goblin Scout -> Scavenger Gloves
Lost Adventurer -> Adventurer Relic Ring
Thorn Sprite -> Forest Gatherer Gloves
```

Les donjons doivent plutot donner :

```text
composants rares
pieces plus fortes
recettes
items de fin de set
```

### 4. Certaines pieces viennent des quetes

Les quetes peuvent donner une piece de set ou un composant cible pour guider le joueur sans le forcer a farmer aveuglement.

Exemples :

```text
The Pack Watches -> Wolf Fang Charm
Smoke Above the Trees -> Scavenger Badge
Bones Under the Roots -> Bone Signet
The Buried Grove -> Rootbound Amulet recipe or component
```

### 5. PNJ a prevoir

Le monde doit contenir des PNJ. Leur implementation n'est pas encore actee, mais le contenu narratif doit les anticiper.

Roles possibles :

```text
Quest giver
merchant specialiste
profession trainer
lore narrator
sarcastic camp attendant
dungeon guide
achievement keeper
```

PNJ Foret potentiels :

| PNJ id propose | Nom visible | Role | Ton |
|---|---|---|---|
| camp_quartermaster | Quartermaster Brindle | Donne les premieres quetes et recompenses | pragmatique, pince-sans-rire |
| old_herbalist | Maela the Herbalist | Introduit Druid et consommables | douce mais sarcastique |
| bone_scribe | Archivist Osric | Introduit Archaeologist et ossements | morbide poli |
| retired_scout | Fen the One-Time Scout | Donne des infos sur loups/gobelins | bravache, peu credible |
| dungeon_warden | Gatekeeper Marn | Introduit donjons | solennel, fatigue |

Note technique future : les PNJ pourront etre ajoutes dans un fichier dedie, par exemple `data/npcs.json`, quand un systeme de quetes/dialogues existera.

---

## Separation claire des sources

| Source | Role | Exemples |
|---|---|---|
| Enemy drops | Identite des monstres | goblin_ear, wolf_fang, scout_badge |
| Rare enemy drops | Objectifs de farm ponctuels | wild_heart, ritual_paint, rusted_ring |
| Gathering resources | Identite des metiers et zones | healing_herb, buried_bones, forest_spore |
| Direct set drops | Surprise et satisfaction de farm | wolf_stalker_boots, scavenger_gloves |
| Quest rewards | Guidage intelligent | bone_signet, wolf_fang_charm |
| Hybrid crafts | Lien combat + metier | wolf_fang + wild_root, goblin_totem + old_charm_fragment |
| Boss resources | Progression majeure | forest_core, rootcaller_totem |

---

## Chronologie du chapitre Foret

| Palier | Zone / contenu | Role gameplay | Role narratif |
|---|---|---|---|
| 1 | Forest Outskirts | Introduction combat, drops simples | La foret semble banale, donc suspecte |
| 2 | Deeper Trails | Builds crit/dodge/loot | La foret devient hostile et se moque un peu du joueur |
| 3 | Buried Paths | Archaeology, traces de morts | Les anciens aventuriers sont enfouis ici, parfois avec leurs affaires |
| 4 | Goblin Camp | Premier donjon simple | Les gobelins organisent la foret, ce qui est inquietant pour tout le monde |
| 5 | Buried Grove | Donjon nature/relique | La corruption est ancienne, les racines ont de la memoire |
| 6 | Forest Boss | Fin de chapitre | La racine du probleme est revelee, litteralement |

---

## Bestiaire Foret propose

### Liste longue d'ennemis

| Ordre | Enemy id propose | Nom visible | Famille | Role gameplay | Drop specifique | Drop rare selectif | Piece de set directe possible |
|---:|---|---|---|---|---|---|---|
| 1 | forest_rat | Forest Rat | beast | Ennemi tres simple | rat_tail | - | - |
| 2 | young_goblin | Young Goblin | goblin | Introduction gobelin | goblin_ear | - | - |
| 3 | stray_wolf | Stray Wolf | wolf | Introduction bete rapide | wolf_pelt | - | - |
| 4 | goblin_scout | Goblin Scout | goblin | Loot/gold/luck | scout_badge | goblin_map_scrap | scavenger_gloves |
| 5 | forest_wolf | Forest Wolf | wolf | Crit/dodge | wolf_fang | wild_heart | wolf_stalker_boots |
| 6 | thorn_sprite | Thorn Sprite | nature | Lien druid/craft nature | thorn_essence | - | forest_gatherer_gloves |
| 7 | bone_gnawer | Bone Gnawer | scavenger | Lien ossements | chewed_bone | cracked_skull | - |
| 8 | lost_adventurer | Lost Adventurer | fallen | Lore boucle de mort | broken_adventurer_tag | rusted_ring | adventurer_relic_ring |
| 9 | goblin_shaman | Goblin Shaman | goblin | Magie primitive/totems | shaman_totem | ritual_paint | - |
| 10 | alpha_wolf | Alpha Wolf | wolf | Mini-boss / pre-boss | alpha_fang | wild_heart | wolf_stalker_hood |
| 11 | goblin_quartermaster | Goblin Quartermaster | goblin | Mini-boss Goblin Camp | scout_badge | goblin_map_scrap | goblin_ritual_amulet |
| 12 | rootbound_remnant | Rootbound Remnant | nature/fallen | Mini-boss Buried Grove | rootbound_relic | briar_sap | rootbound_amulet |
| 13 | grubfang_rootcaller | Grubfang, Rootcaller | boss | Boss Foret | rootcaller_totem | forest_core | forest_remnant_trinket |

Notes :

- Les ennemis 1 a 3 servent d'introduction.
- Les ennemis 4 a 6 ouvrent les premiers builds et les routes plus profondes.
- Les ennemis 7 a 8 installent le theme des morts et de l'archeologie.
- Les ennemis 9 a 13 structurent les donjons, la corruption et le boss.
- Les pieces de set directes doivent rester rares, mais visibles dans les objectifs du joueur.
- Les ennemis hors donjon doivent recevoir quelques drops de set pour eviter que tout l'interet soit concentre dans les donjons.

---

## Zones et sous-zones Foret

### Zones de combat actuellement implementees

Les zones de combat actuelles de la Foret sont definies dans `data/zones.json`.

Chaque zone de combat correspond a une zone de farm / combat ciblant un ennemi principal, avec son propre niveau de deblocage, sa table de loot, son multiplicateur de difficulte et son rythme de farming.

| Zone id actuelle | Nom visible | Unlock level | Ennemi principal | Loot principal | Role narratif |
|---|---|---:|---|---|---|
| forest_rat_outskirts | Rat Outskirts | 1 | forest_rat | rat_tail | Premiere zone de combat. Sert au demarrage, aux rats et aux premieres quetes de Brindle. |
| forest_young_goblin_trail | Young Goblin Trail | 1 | young_goblin | goblin_ear | Introduit les gobelins maladroits et les premiers problemes de route. |
| forest_stray_wolf_path | Stray Wolf Path | 1 | stray_wolf | wolf_pelt | Introduit les loups opportunistes et les chemins moins surs. |
| forest_goblin_scout_trails | Goblin Scout Trails | 2 | goblin_scout | scout_badge, goblin_map_scrap, scavenger_gloves | Ouvre la progression vers les routes gobelines, Fen et l'approche de Goblin Camp. |
| forest_wolf_hunting_ground | Wolf Hunting Ground | 2 | forest_wolf | wolf_fang, wild_heart, wolf_stalker_boots | Zone de loups plus avancee. Sert aux builds crit/dodge et a la sensation d'ecosysteme hostile. |
| forest_thorn_sprite_grove | Thorn Sprite Grove | 2 | thorn_sprite | thorn_essence, forest_gatherer_gloves | Zone nature/grove. Sert a Maela, au Druid, aux plantes agressives et aux premiers signes de corruption naturelle. |
| forest_bone_gnawer_den | Bone Gnawer Den | 3 | bone_gnawer | chewed_bone, cracked_skull | Zone d'ossements et de charognards. Sert a Osric et a la bascule morbide. |
| forest_lost_adventurer_path | Lost Adventurer Path | 3 | lost_adventurer | broken_adventurer_tag, rusted_ring, adventurer_relic_ring | Zone des anciens aventuriers. Montre que d'autres sont tombes avant le joueur. |
| forest_goblin_shaman_grounds | Goblin Shaman Grounds | 4 | goblin_shaman | shaman_totem, ritual_paint | Zone rituelle gobeline. Prepare les totems, la magie primitive, Goblin Camp et Rootcaller. |
| forest_alpha_wolf_lair | Alpha Wolf Lair | 4 | alpha_wolf | alpha_fang, wild_heart, wolf_stalker_hood | Zone de loups avancee / pre-boss. Renforce la menace de la meute avant les contenus de fin de chapitre. |

### Lecture narrative des zones de combat

Les zones implementees peuvent etre lues comme une progression plus fine que les macro-zones narratives :

```text
Rat Outskirts
-> Young Goblin Trail / Stray Wolf Path
-> Goblin Scout Trails / Wolf Hunting Ground / Thorn Sprite Grove
-> Bone Gnawer Den / Lost Adventurer Path
-> Goblin Shaman Grounds / Alpha Wolf Lair
-> Goblin Camp / Buried Grove
-> Grubfang, Rootcaller
```

Cette progression permet de distribuer les PNJ sans doublon :

| PNJ | Couverture principale | Zones associees |
|---|---|---|
| Quartermaster Brindle | Combat de base, logistique, premieres recompenses | Rat Outskirts, Young Goblin Trail, Stray Wolf Path |
| Maela the Herbalist | Recolte, soins, craft, nature anormale | Thorn Sprite Grove, ressources Druid, zones de racines et de sap |
| Fen the One-Time Scout | Exploration plus profonde, routes secondaires, combats de chemin | Goblin Scout Trails, Wolf Hunting Ground, routes profondes, approche de Goblin Camp |
| Archivist Osric | Ossements, anciens aventuriers, memoire des morts | Bone Gnawer Den, Lost Adventurer Path, Buried Grove |
| Gatekeeper Marn | Donjons, boss, seuils dangereux | Goblin Camp, Buried Grove, Grubfang, Rootcaller |

Fen prolonge donc Brindle sans le copier : Brindle donne des missions de combat officielles, tandis que Fen pousse le joueur vers des routes plus profondes ou les combats arrivent parce que le joueur explore des chemins moins surs.

### Macro-zones narratives

Les macro-zones ci-dessous servent de lecture narrative globale. Elles peuvent regrouper plusieurs zones de combat actuelles.

| Macro-zone narrative | Zones de combat associees | Ennemis principaux | Metiers lies | Role |
|---|---|---|---|---|
| Forest Outskirts | Rat Outskirts, Young Goblin Trail, Stray Wolf Path | forest_rat, young_goblin, stray_wolf | druid, archaeologist | Introduction combat, drops simples, premieres quetes |
| Deeper Trails | Goblin Scout Trails, Wolf Hunting Ground, Thorn Sprite Grove | goblin_scout, forest_wolf, thorn_sprite | druid | Routes plus profondes, builds rapides, nature hostile, Fen et Maela |
| Buried Paths | Bone Gnawer Den, Lost Adventurer Path | bone_gnawer, lost_adventurer | archaeologist, druid | Lore, ossements, anciens aventuriers, Osric |
| Ritual Grounds | Goblin Shaman Grounds, Alpha Wolf Lair | goblin_shaman, alpha_wolf | druid, archaeologist | Pre-boss, totems, loups avances, racines et tension finale |
| Dungeon Thresholds | Goblin Camp, Buried Grove | goblin_quartermaster, rootbound_remnant | druid, archaeologist | Donjons, mini-boss, acces boss, Marn |
| Forest Boss | Rootcaller encounter | grubfang_rootcaller | all forest systems | Fin du chapitre Foret et transition vers le chapitre suivant |

Recommandation technique : garder les zones de combat actuelles tant qu'elles sont fonctionnelles. Les macro-zones doivent servir au plan narratif, a la future carte top-down / up-down et a la repartition des PNJ, sans forcer une refonte technique immediate.

---

## Donjons Foret

### Donjon 1 — Goblin Camp

| Champ | Proposition |
|---|---|
| Dungeon id | forest_goblin_camp |
| Nom visible | Goblin Camp |
| Theme | camp gobelin, vol, bricolage, totems, economie |
| Role gameplay | premier donjon oriente loot/gold/luck |
| Ennemis | young_goblin, goblin_scout, goblin_shaman |
| Mini-boss | goblin_quartermaster |
| Set lie | Goblin Scavenger |
| Ressources cles | goblin_ear, scout_badge, shaman_totem, goblin_map_scrap |
| Ton | sarcastique, gobelins trop organises pour etre rassurants |

#### Route fixe V1

```text
Room 1: Young Goblin
Room 2: Goblin Scout
Room 3: Young Goblin + Goblin Scout
Room 4: Goblin Shaman
Room 5: Goblin Quartermaster
```

V1 technique possible : une route fixe de combats successifs, sans carte visuelle.

Exemple d'intro :

```text
De la fumee monte entre les arbres. Quelque part, un gobelin a decouvert le feu, l'organisation et probablement la fraude fiscale.
```

---

### Donjon 2 — Buried Grove

| Champ | Proposition |
|---|---|
| Dungeon id | forest_buried_grove |
| Nom visible | Buried Grove |
| Theme | ossements, racines, anciens aventuriers, memoire de la mort |
| Role gameplay | donjon hybride druid + archaeologist + lore |
| Ennemis | thorn_sprite, bone_gnawer, lost_adventurer |
| Mini-boss | rootbound_remnant |
| Set lie | Forest Remnant |
| Ressources cles | buried_bones, cracked_skull, broken_adventurer_tag, rootbound_relic |
| Ton | plus epique, sarcastique noir leger |

#### Route fixe V1

```text
Room 1: Thorn Sprite
Room 2: Bone Gnawer
Room 3: Lost Adventurer
Room 4: Thorn Sprite + Bone Gnawer
Room 5: Rootbound Remnant
```

Ce donjon est important pour raconter que les personnages qui meurent laissent des traces exploitables par l'archeologue.

Exemple d'intro :

```text
Sous les racines, les noms des anciens heros murmurent encore. Certains murmurent surtout qu'ils auraient du rester en ville.
```

---

## Boss Foret

### Boss propose — Grubfang, Rootcaller

| Champ | Proposition |
|---|---|
| Enemy id | grubfang_rootcaller |
| Nom visible | Grubfang, Rootcaller |
| Type | boss |
| Theme | gobelin chaman corrompu par les racines |
| Role gameplay | fin de chapitre Foret |
| Drops principaux | rootcaller_totem, corrupted_root |
| Drop rare | forest_core |
| Piece de set directe | forest_remnant_trinket |
| Unlock | Caves / prochain chapitre |

Exemple d'intro :

```text
Les racines se tordent sous ses pieds. Son totem pulse d'une energie ancienne. Il va probablement crier quelque chose de dramatique.
```

### Idee a garder : boss qui tue le joueur en fin de donjon

Piste de design a conserver :

```text
Le boss de fin de donjon fonctionne comme une boucle de fin.
Le joueur affronte une version du boss.
S'il gagne, le boss revient plus fort.
Chaque victoire augmente le loot.
La sequence continue jusqu'a la defaite du joueur.
```

Avantages :

```text
coherent avec le concept du jeu
raconte la mort inevitable du personnage
rend les donjons plus intenses
permet un scaling de recompenses
```

A ne pas implementer tout de suite sans cadrage technique.

Issue / future bloc possible :

```text
Dev jeu — boss scaling et fin de donjon par defaite
```

---

## Ressources metier Foret

### Druid

| Ressource | Palier | Source | Usage principal |
|---|---:|---|---|
| healing_herb | 1 | Forest Outskirts | consommables |
| wild_root | 1-2 | Forest Outskirts / Deep Trails | craft nature, bijoux |
| forest_spore | 2 | Deep Trails | consommables avances, nature gear |
| briar_sap | 3 | Buried Grove / Ritual Grounds | craft hybride, mini-boss |
| corrupted_root | boss | Grubfang / boss content | boss gear, unlock craft |

### Archaeologist

| Ressource | Palier | Source | Usage principal |
|---|---:|---|---|
| buried_bones | 1 | Buried paths | craft basique relique |
| cracked_skull | 2 | Bone Gnawer / gathering | anneaux, talismans |
| old_charm_fragment | 2 | Buried Grove | loot/gold/relic craft |
| broken_adventurer_tag | 3 | Lost Adventurer | lore, quetes, relic set |
| rootbound_relic | dungeon | Rootbound Remnant | set hybride / boss key |

### Prospector

Le prospector doit rester secondaire en Foret. Il brillera surtout dans les Caves et Mountains.

| Ressource | Palier | Source | Usage principal |
|---|---:|---|---|
| river_stone | 1 | Forest Outskirts | petit composant secondaire |
| greenstone_chip | 2 | Deep Trails | bijoux simples |
| mossy_geode | rare | Rare gathering | craft hybride rare |

---

## Sets Foret

### Set 1 — Wolf Stalker

| Champ | Proposition |
|---|---|
| Orientation | dexterity, crit_chance, dodge_chance |
| Source | loups + ressources druid |
| Fantaisie | chasseur rapide, predateur |
| Pieces possibles | hood, gloves, boots, ring |

Distribution recommandee :

| Piece | Source recommandee |
|---|---|
| wolf_stalker_boots | drop Forest Wolf hors donjon |
| wolf_stalker_gloves | craft wolf_fang + forest_spore |
| wolf_stalker_hood | drop Alpha Wolf |
| alpha_stalker_ring | craft alpha_fang + wild_heart |

Bonus possibles :

```text
2 pieces: +dexterity
3 pieces: +crit_chance
4 pieces: +dodge_chance or initiative
```

---

### Set 2 — Goblin Scavenger

| Champ | Proposition |
|---|---|
| Orientation | loot_bonus, gold_bonus, luck |
| Source | gobelins + archaeology fragments |
| Fantaisie | recup, vol, butin |
| Pieces possibles | trinket, gloves, boots, amulet |

Distribution recommandee :

| Piece | Source recommandee |
|---|---|
| scavenger_gloves | drop Goblin Scout hors donjon |
| scavenger_badge | recompense de quete Smoke Above the Trees ou craft scout_badge + old_charm_fragment |
| lucky_goblin_totem | craft goblin_totem + cracked_skull |
| goblin_ritual_amulet | donjon Goblin Camp / Goblin Shaman |

Bonus possibles :

```text
2 pieces: +luck
3 pieces: +gold_bonus
4 pieces: +loot_bonus
```

---

### Set 3 — Forest Remnant

| Champ | Proposition |
|---|---|
| Orientation | archaeologist_mastery, druid_mastery, xp_bonus, wisdom |
| Source | Buried Grove + ressources metier |
| Fantaisie | traces des anciens personnages morts |
| Pieces possibles | ring, amulet, trinket, pants |

Distribution recommandee :

| Piece | Source recommandee |
|---|---|
| adventurer_relic_ring | drop Lost Adventurer hors donjon |
| bone_signet | recompense de quete Bones Under the Roots ou craft buried_bones + cracked_skull |
| rootbound_amulet | donjon Buried Grove |
| forest_remnant_trinket | boss Grubfang, Rootcaller |

Bonus possibles :

```text
2 pieces: +archaeologist_mastery
3 pieces: +gathering_xp_bonus
4 pieces: +wisdom or xp_bonus
```

---

## Crafts Foret proposes

| Recipe id propose | Resultat | Ingredients | Role | Source principale |
|---|---|---|---|---|
| craft_herbal_poultice | Herbal Poultice | healing_herb + forest_spore | consommable soin | Druid |
| craft_wolf_fang_charm | Wolf Fang Charm | wolf_fang + wild_root | crit/dodge early | Wolf + Druid |
| craft_scavenger_badge | Scavenger Badge | scout_badge + old_charm_fragment | loot/gold | Goblin + Archaeologist |
| craft_bone_signet | Bone Signet | buried_bones + cracked_skull | relic ring | Archaeologist |
| craft_forest_gatherer_gloves | Forest Gatherer Gloves | wild_root + forest_spore | druid mastery | Druid |
| craft_goblin_lucky_totem | Lucky Goblin Totem | goblin_totem + cracked_skull | luck/loot | Goblin + Archaeologist |
| craft_rootbound_amulet | Rootbound Amulet | rootbound_relic + briar_sap | dungeon reward | Buried Grove |
| craft_forest_core_trinket | Forest Core Trinket | forest_core + rootcaller_totem | boss craft | Boss |

Note : certaines recettes peuvent produire des alternatives craftables a des items de set droppables. Cela permet de limiter la frustration du joueur.

### Temporary legacy overlap

- `wolf_fang_charm` is currently both craftable and dropped by legacy enemies `wolf` / `troll`.
- This is accepted temporarily because old forest content has not been migrated yet.
- When the forest transition is implemented, old generic `wolf` / `troll` drops should be reviewed.
- New Forest narrative enemies should avoid crafting/drop overlaps unless explicitly designed.

---

## Quetes Foret V1

### Chaine principale

| Ordre | Quest id | Nom | Objectifs | Recompenses | Debloque |
|---:|---|---|---|---|---|
| 1 | forest_secure_outskirts | Secure the Outskirts | Kill forest_rat x5, young_goblin x3 | gold, recipe herbal_poultice | Deep Trails |
| 2 | forest_first_harvest | First Forest Harvest | Gather healing_herb x5, wild_root x2 | druid XP, forest_spore | basic druid crafts |
| 3 | forest_pack_watches | The Pack Watches | Kill forest_wolf x5, craft wolf_fang_charm | Wolf Fang Charm or wolf_fang bundle | Wolf Stalker craft |
| 4 | forest_bones_under_roots | Bones Under the Roots | Gather buried_bones x5, kill bone_gnawer x2 | Bone Signet or old_charm_fragment | Buried Grove |
| 5 | forest_smoke_above_trees | Smoke Above the Trees | Kill goblin_scout x8, collect scout_badge x3 | Scavenger Badge or recipe | Goblin Camp |
| 6 | forest_clear_goblin_camp | Break the Goblin Camp | Clear Goblin Camp once | shaman_totem, Goblin Scavenger recipe | Ritual Grounds |
| 7 | forest_buried_grove | The Buried Grove | Clear Buried Grove once, find rootbound_relic | rootbound craft | Boss access |
| 8 | forest_silence_rootcaller | Silence the Rootcaller | Defeat Grubfang, Rootcaller | forest_core, permanent bonus | Caves |

### Exemple de ton de quete

```text
Secure the Outskirts
La lisiere de la foret est infestee de rats, de gobelins et de mauvaises decisions.

Bones Under the Roots
Quelqu'un a enterre beaucoup trop d'aventuriers ici. L'archeologue appelle ca une opportunite.

Silence the Rootcaller
La foret a trouve une voix. Mauvaise nouvelle : elle chante faux et invoque des racines.
```

### Recompenses permanentes legeres possibles

A utiliser avec moderation :

```text
+1 inventory slot
+1 druid_mastery
+1 archaeologist_mastery
+1 luck
+2% gathering_xp_bonus
+1% loot_bonus
```

---

## Succes Foret V1

### Combat

| Achievement id | Nom | Objectif | Recompense |
|---|---|---|---|
| forest_rat_cleaner_1 | Rat Cleaner I | Kill forest_rat x25 | +gold |
| forest_wolf_hunter_1 | Wolf Hunter I | Kill wolf-family x25 | +1 dexterity |
| forest_goblin_problem_1 | Goblin Problem I | Kill goblin-family x50 | +1% loot_bonus |
| forest_shaman_breaker_1 | Shaman Breaker I | Kill goblin_shaman x10 | +1 luck |

### Gathering

| Achievement id | Nom | Objectif | Recompense |
|---|---|---|---|
| forest_first_harvest | First Harvest | Gather 25 druid resources | +1 druid_mastery |
| forest_bone_reader | Bone Reader | Gather 25 archaeology resources | +1 archaeologist_mastery |
| forest_worker | Forest Worker | Complete 100 gathering ticks in forest | +2% gathering_xp_bonus |

### Craft / sets

| Achievement id | Nom | Objectif | Recompense |
|---|---|---|---|
| forest_first_craft | First Forest Craft | Craft 1 forest item | gold |
| forest_set_apprentice | Set Apprentice | Equip 2 pieces from same forest set | +1 luck |
| forest_crafter | Forest Crafter | Craft 5 forest-tier items | material bundle |

### Donjons / boss

| Achievement id | Nom | Objectif | Recompense |
|---|---|---|---|
| forest_camp_breaker | Camp Breaker | Clear Goblin Camp x5 | +2% gold_bonus |
| forest_rootbound | Rootbound | Clear Buried Grove x5 | +1 wisdom |
| forest_rootcaller_defeated | Rootcaller Defeated | Defeat Grubfang once | unlock Caves / permanent bonus |

---

## Architecture systeme a prevoir plus tard

### NPCs V1

Fichiers probables :

```text
data/npcs.json
systems/dialogues.py or systems/npcs.py
tests/test_npcs.py
```

Structure simple possible :

```json
{
  "bone_scribe": {
    "name": "Archivist Osric",
    "role": "archaeologist_trainer",
    "location": "town",
    "intro_text": "Les os parlent, si on sait ecouter. Et si on accepte l'odeur.",
    "related_quests": ["forest_bones_under_roots"]
  }
}
```

Ne pas implementer maintenant, mais prevoir les hooks narratifs dans les quetes.

---

### Quests V1

Fichiers probables :

```text
data/quests.json
systems/quests.py
core/game.py
tests/test_quests.py
```

Objectifs supportes en V1 :

```text
kill_enemy
gather_item
craft_item
equip_set_pieces
clear_dungeon
defeat_boss
profession_level
```

Recompenses supportees en V1 :

```text
gold
xp
item
unlock_recipe
unlock_zone
stat_bonus
profession_xp
```

---

### Achievements V1

Fichiers probables :

```text
data/achievements.json
systems/achievements.py
tests/test_achievements.py
```

Objectifs supportes en V1 :

```text
kill_count
gather_count
craft_count
dungeon_clear_count
boss_kill_count
set_equipped
```

Recompenses supportees en V1 :

```text
small_stat_bonus
small_percent_bonus
item_bundle
gold
```

---

### Dungeons V1

Fichiers probables :

```text
data/dungeons.json
systems/dungeons.py
tests/test_dungeons.py
```

Structure simple recommandee :

```json
{
  "forest_goblin_camp": {
    "name": "Goblin Camp",
    "unlock_level": 3,
    "route": [
      {"type": "combat", "enemy": "young_goblin"},
      {"type": "combat", "enemy": "goblin_scout"},
      {"type": "combat", "enemy": "goblin_shaman"},
      {"type": "boss", "enemy": "goblin_quartermaster"}
    ],
    "rewards": [
      {"type": "item", "item": "scout_badge", "quantity": 1}
    ]
  }
}
```

---

## Idee gameplay a garder : combats plus animes

Piste future : rendre les combats plus lisibles et plus vivants.

Vision :

```text
Le premier combat est joue lentement pour montrer le build.
Ensuite la vitesse augmente progressivement.
Les combats repetitifs s'accelerent jusqu'a la defaite.
Les donjons peuvent etre joues plus lentement car ce sont des instances uniques.
Les boss de fin peuvent repeter une boucle plus forte jusqu'a tuer le joueur.
```

Impact potentiel :

```text
core/instance.py
systems/combat.py
ui/screens/combat_screen.py
ui/screens/result_screen.py
systems/dungeons.py
```

A ne pas implementer maintenant.

Issue future possible :

```text
Dev jeu — combat visual pacing and dungeon boss loop
```

---

## Roadmap proposee pour implementation

### Bloc 1 — Data Foret et taxonomie

Objectif : poser les ennemis, ressources, drops et categories sans gros nouveau systeme.

Fichiers probables :

```text
data/enemies.json
data/items.json
data/gathering_nodes.json
tests/test_forest_content_data.py
```

### Bloc 2 — Crafts et sets Foret

Objectif : connecter drops + ressources metier a des items utiles.

Fichiers probables :

```text
data/items.json
data/recipes.json
data/equipment_sets.json
tests/test_forest_crafting_data.py
tests/test_equipment_sets.py
```

### Bloc 3 — Quests V1

Objectif : guider le joueur dans la Foret.

Fichiers probables :

```text
data/quests.json
systems/quests.py
core/game.py
tests/test_quests.py
```

### Bloc 4 — Dungeons V1

Objectif : ajouter Goblin Camp et Buried Grove comme routes fixes.

Fichiers probables :

```text
data/dungeons.json
systems/dungeons.py
core/game.py
ui/screens/menu_screen.py
tests/test_dungeons.py
```

### Bloc 5 — Achievements V1

Objectif : recompenses optionnelles et bonus permanents legers.

Fichiers probables :

```text
data/achievements.json
systems/achievements.py
tests/test_achievements.py
```

### Bloc 6 — NPCs V1

Objectif : ajouter des personnages du monde pour porter quetes, ton et lore.

Fichiers probables :

```text
data/npcs.json
systems/npcs.py or systems/dialogues.py
ui/screens/dialogue_panel.py or simple town panel later
tests/test_npcs.py
```

---

## Decision recommandee pour le prochain bloc

Commencer par :

```text
Dev jeu — contenu narratif T1 Foret
```

Premiere etape recommandee :

```text
Data Foret et taxonomie
```

Pourquoi :

```text
pas de nouveau gros systeme
pose la chronologie du monde
alimente les futurs crafts, sets, quetes, donjons et PNJ
permet de tester les incoherences de data
```

Ne pas commencer par les quetes, donjons ou PNJ tant que les ennemis, drops et ressources de Foret ne sont pas propres.
