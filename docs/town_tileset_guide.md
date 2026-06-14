# Guide du pack Town Tileset

## Role du pack

Ce pack fournit une base de ville medievale / fantasy pour Tiled en tuiles de 32x32 pixels. Il sert a construire un hub lisible pour le projet Python + Pygame : arrivee du joueur, route vers la Foret, marchands, forge, craft, quetes, PNJ et objets interactifs.

Le pack suit la direction pixel-art fantasy lisible du projet : formes simples, couleurs contrastees, objets reconnaissables et organisation en grille reguliere.

## Ouvrir la carte demo dans Tiled

1. Ouvre le projet Tiled `formation.tiled-project` depuis la racine du repo.
2. Ouvre `assets/maps/town_demo.tmx`.
3. Tiled doit charger automatiquement `assets/tilesets/town_tileset.tsx`.
4. Le TSX reference l'image `assets/images/tilesets/town_tileset.png` avec un chemin relatif valide.

## Utiliser le tileset

Le tileset `town_tileset.tsx` decrit une image de 16 colonnes par 9 lignes, soit 144 tuiles. Chaque tuile fait exactement 32x32 pixels.

Les tuiles importantes ont des proprietes Tiled : `name`, `category`, `collides`, `interactable` et parfois `interaction_type`.

## Signification des calques

- `ground` : herbe, sols de place, planchers et bases non bloquantes.
- `paths` : routes, chemins et transitions.
- `buildings` : murs, toits, portes, fenetres et fondations.
- `objects` : mobilier, decors, PNJ statiques et objets interactifs.
- `animated_objects` : objets qui utilisent les animations Tiled du TSX.
- `markers` : calque d'objets Tiled pour les points logiques importants.

## Placer les sols

Commence par remplir la carte avec `grass`, puis ajoute quelques variantes pour casser la repetition. Utilise `plaza_floor` autour de la place centrale, puis connecte les routes avec `horizontal_path`, `vertical_path`, `path_corner_*`, `path_t_junction_*` et `path_crossroad`.

Les transitions `grass_to_path_*` et `plaza_to_path_*` servent a rendre les bords plus lisibles.

## Placer les batiments

Construis les batiments par couches : toits, murs, ouvertures, puis details. Les murs, toits, portes fermees et fenetres ont `collides=true` pour preparer une future collision Pygame.

## Utiliser les markers

Le calque `markers` contient des objets Tiled nommes explicitement : `player_spawn`, `forest_exit`, `merchant_npc`, `blacksmith_npc`, `quest_board`, `crafting_station` et `save_point`.

Ces objets portent des proprietes comme `id`, `type`, `target_map`, `npc_id`, `interaction_type` et `description`. Les tuiles de categorie `marker` sont des aides visuelles, mais la logique finale devrait plutot lire les objets du calque `markers`.

## Interpreter collides

`collides=true` signifie que la tuile doit bloquer le joueur si elle est utilisee dans un futur systeme de collision. C'est le cas des murs, toits, portes fermees, fenetres, comptoirs, coffres, caisses, tonneaux, forge, enclume, fontaine, puits, lampadaires, panneaux, arbres, PNJ statiques et clotures.

`collides=false` signifie que la tuile est traversable : sols, chemins, ombres, marqueurs, fleurs et petits details decoratifs.

## Interpreter interactable

`interactable=true` signale qu'une action joueur peut etre pertinente : parler a un PNJ, ouvrir un coffre, utiliser une forge, consulter un panneau, acceder a une boutique ou sauvegarder.

`interaction_type` permet de differencier ces usages sans deviner depuis le dessin.

## Objets animes

Le TSX declare des animations Tiled pour `fountain`, `lamp_post`, `blacksmith_forge`, `fireplace`, `chest_closed` et `signboard`.

## Chargement futur dans Pygame

Plus tard, le jeu pourra charger le PNG comme spritesheet 32x32, le TMX pour recuperer les calques et les GID, le TSX ou le CSV pour connaitre les proprietes, et le calque `markers` pour placer le joueur, les PNJ, les sorties et les stations d'interaction.

Si le chargeur Pygame ne lit pas encore les fichiers TSX/TMX, `docs/town_tile_index.csv` peut servir de reference simple.

## Limites connues

Le rendu est volontairement lisible et coherent, mais il reste un tileset de production initiale : certains objets complexes sont representes par des formes pixel-art simplifiees. La carte `town_demo.tmx` est pedagogique, pas encore equilibree pour une vraie navigation finale.

## Prochaines etapes recommandees

1. Ouvrir `town_demo.tmx` dans Tiled et verifier le rendu general.
2. Ajuster la carte selon la taille du futur hub jouable.
3. Decider si la logique Pygame lira les collisions depuis le TSX, le CSV ou un calque d'objets dedie.
4. Ajouter plus tard des PNJ reels dans les donnees du jeu quand le systeme de dialogue sera pret.
5. Remplacer progressivement les tuiles reservees si de nouveaux besoins apparaissent.
