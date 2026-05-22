# Art Direction

## 1. Visual identity

The game uses readable dark medieval fantasy pixel art.

The world should feel dangerous, damp, old, hostile and slightly sarcastic. Death, loot, forest monsters, dungeon progression and repeated failure are central themes.

The tone must avoid:
- cheerful cartoon fantasy;
- realistic dark rendering that hurts readability;
- painterly or 3D-looking assets;
- over-detailed sprites that become unreadable at gameplay scale.

The priority order is:
1. gameplay readability;
2. visual consistency;
3. mood;
4. detail.

## 2. Core mood

Keywords:
- dark medieval fantasy;
- hostile forest;
- damp caves;
- crude goblin camps;
- bones, roots, moss, mud, broken gear;
- dangerous but readable;
- sarcastic grim humor.

Humor should appear through asset descriptions, item concepts and small visual jokes, not through bright cartoon styling.

## 3. Perspective

Use a top-down RPG perspective compatible with Pygame and Tiled.

Recommended perspective:
- top-down / three-quarter top-down hybrid;
- visible object tops;
- visible front-facing silhouettes for characters;
- consistent light from upper-left.

Avoid:
- side-scroller perspective;
- isometric projection;
- realistic perspective;
- inconsistent camera angle between tiles and sprites.

## 4. Tile rules

Map tiles are 16x16 pixels.

All Tiled map tiles must:
- align to a regular 16x16 grid;
- be exported as PNG;
- avoid anti-aliasing;
- use limited contrast so characters remain readable;
- support modular placement;
- use seamless or semi-seamless transitions where useful.

Recommended tile categories:
- ground;
- path;
- wall;
- water;
- vegetation;
- props;
- interactables;
- dungeon entrance;
- crafting station;
- collision objects.

Tiled properties may include:
- name;
- category;
- collides;
- interactable;
- interaction_type;
- animated;
- target_map;
- npc_id;
- item_id;
- station_id.

## 5. Sprite rules

Sprites must use transparent backgrounds.

Recommended sizes:
- small enemies: 16x16 or 24x24;
- player and NPCs: 24x24 or 32x32;
- bosses: 32x32 or larger;
- large monsters: 32x32;
- dropped items: 16x16;
- interactable props: 16x16 or 32x32.

Sprites must:
- use strong readable silhouettes;
- use dark outlines for important entities;
- keep frame dimensions identical;
- keep feet/contact point stable;
- include simple ground shadow when useful;
- avoid excessive internal detail.

## 6. Animation rules

Default directional order:

row 0 = down  
row 1 = left  
row 2 = right  
row 3 = up  

Recommended base animations:
- idle;
- walk;
- attack;
- hurt;
- death.

For early production, small enemies may start with:
- idle;
- walk.

Bosses may require:
- idle;
- walk or root movement;
- attack;
- summon/cast;
- hurt;
- death.

## 7. Icon rules

Icons should be 16x16 or 32x32 depending on UI usage.

Icons must:
- have transparent backgrounds;
- use clear silhouettes;
- use readable contrast;
- avoid tiny decorative details;
- support rarity overlays or frames if needed.

Recommended icon categories:
- weapons;
- armor;
- helmets;
- gloves;
- boots;
- rings;
- amulets;
- trinkets;
- potions;
- monster drops;
- gathering resources;
- currencies;
- recipes;
- professions;
- achievements.

## 8. UI and overlay rules

UI must remain readable before decorative.

The UI style should use:
- dark stone;
- worn parchment;
- tarnished metal;
- muted leather;
- bone or root ornaments;
- subtle blood or moss accents.

Buttons must support:
- normal;
- hover;
- pressed;
- disabled;
- selected.

Recommended UI assets:
- modular panels;
- inventory slots;
- item rarity frames;
- quest panels;
- combat panels;
- tooltip background;
- health/mana/xp bars;
- death screen overlay;
- dungeon progress overlay;
- achievement notification.

## 9. Palette direction

Use a limited muted palette.

Recommended families:
- forest greens: dark moss, pine, sickly green;
- earth tones: mud brown, bark brown, dead leaf ochre;
- metal: cold grey, iron, dull silver;
- danger accents: dark red, dried blood, ember orange;
- magic accents: toxic green, pale blue, violet, bone white;
- UI: charcoal, parchment beige, tarnished bronze.

Avoid:
- saturated primary colors;
- neon colors except controlled magic highlights;
- large bright surfaces.

## 10. Outlines and contrast

Important gameplay objects require stronger outlines:
- player;
- enemies;
- pickups;
- interactables;
- doors;
- quest objects.

Background tiles should have lower contrast than sprites.

Interactable elements may use:
- outline;
- small highlight;
- subtle animation;
- icon marker.

## 11. Shadows

Use simple pixel shadows.

Recommended:
- small oval shadow under characters;
- darker contact shadows under props;
- no soft blur;
- no gradient blur.

## 12. Visual effects

Effects must be short, readable and restrained.

Allowed:
- slash arcs;
- hit sparks;
- poison clouds;
- root snare;
- small smoke puffs;
- death burst;
- loot sparkle;
- level-up flash.

Avoid:
- particle overload;
- blurred glow;
- realistic lighting;
- unreadable spell clutter.

## 13. Asset acceptance criteria

An asset is accepted only if:
- it matches the dark medieval fantasy direction;
- it remains readable at in-game scale;
- it uses the correct dimensions;
- it has transparent background when required;
- it aligns to the expected grid or frame layout;
- it avoids blur, anti-aliasing and 3D rendering;
- it uses snake_case English filenames;
- it fits the existing asset folder structure;
- it can be integrated without manual cleanup.
