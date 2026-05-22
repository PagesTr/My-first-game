# Forest Tileset Pack Specification

## 1. Purpose

This document defines the first validated map asset batch for the game: `forest_tileset_pack`.

The goal is to create a playable, readable and reusable dark fantasy forest tileset for Tiled maps.

This pack must follow `docs/art_direction.md` as the source of truth.

## 2. Asset identity

```yaml
id: forest_tileset_pack
type: tiled_tileset
priority: P0
status: specification_ready
main_output: assets/tilesets/forest_base_16x16.png
optional_tiled_metadata: assets/tilesets/forest_base_16x16.tsx
preview_output: assets/references/previews/forest_base_16x16_preview.png
manifest_output: assets/tilesets/forest_base_16x16_manifest.json
```

## 3. Technical constraints

```yaml
tile_size: 16x16
columns: 8
rows: 8
image_size: 128x128
format: png
background: opaque for ground tiles, transparent only for standalone props if exported separately
perspective: top_down_three_quarter
anti_aliasing: false
rendering: crisp_pixel_art
```

The tileset must be compatible with Tiled and use a regular 16x16 grid.

## 4. Visual direction

The tileset represents the first forest areas of the game.

Mood:
- dark medieval fantasy;
- damp hostile forest;
- moss, mud, roots, bones, broken gear;
- readable before decorative;
- grim but not visually cartoonish.

The ground must stay lower contrast than characters and interactables.

## 5. Directional palette

The palette is directional, not strictly locked.

```yaml
near_black: "#151816"
deep_moss: "#223025"
pine_green: "#2f4632"
sickly_green: "#6f8a4a"
mud_brown: "#4a3527"
bark_brown: "#5b432f"
dead_leaf: "#8a6a3a"
wet_stone: "#4b5250"
bone: "#c7b98b"
dried_blood: "#6b1f1f"
ember: "#b45a2a"
toxic_magic: "#7fae5b"
pale_spirit: "#9fb7aa"
```

Usage:
- low contrast for ground;
- stronger silhouettes for blockers and interactables;
- small accent colors only for readable points of interest.

## 6. Tile layout

The first version uses an 8x8 grid.

### Row 0 — dark grass base

| Tile | Name | Category | Purpose |
|---:|---|---|---|
| 0 | grass_dark_01 | ground | base forest floor |
| 1 | grass_dark_02 | ground | variation |
| 2 | grass_moss_01 | ground | moss patch |
| 3 | grass_moss_02 | ground | moss variation |
| 4 | grass_leaf_litter_01 | ground | dead leaves |
| 5 | grass_leaf_litter_02 | ground | dead leaves variation |
| 6 | grass_sparse_01 | ground | sparse grass |
| 7 | grass_shadow_01 | ground | darker patch |

### Row 1 — mud path base

| Tile | Name | Category | Purpose |
|---:|---|---|---|
| 8 | mud_path_01 | ground | base path |
| 9 | mud_path_02 | ground | variation |
| 10 | mud_path_wet_01 | ground | wet mud |
| 11 | mud_path_stones_01 | ground | small stones |
| 12 | mud_path_leaves_01 | ground | path with leaves |
| 13 | mud_path_roots_01 | ground | roots in path |
| 14 | mud_path_dark_01 | ground | dark path patch |
| 15 | mud_path_edge_noise_01 | ground | noisy edge filler |

### Row 2 — grass to path transitions

| Tile | Name | Category | Purpose |
|---:|---|---|---|
| 16 | grass_path_edge_top | transition | grass to path |
| 17 | grass_path_edge_bottom | transition | grass to path |
| 18 | grass_path_edge_left | transition | grass to path |
| 19 | grass_path_edge_right | transition | grass to path |
| 20 | grass_path_corner_tl | transition | corner |
| 21 | grass_path_corner_tr | transition | corner |
| 22 | grass_path_corner_bl | transition | corner |
| 23 | grass_path_corner_br | transition | corner |

### Row 3 — rocks, roots and stumps

| Tile | Name | Category | Purpose |
|---:|---|---|---|
| 24 | small_rock_01 | prop | decorative rock |
| 25 | small_rock_02 | prop | decorative rock variation |
| 26 | mossy_rock_01 | obstacle | blocker |
| 27 | root_blocker_01 | obstacle | blocker |
| 28 | root_blocker_02 | obstacle | blocker variation |
| 29 | stump_01 | obstacle | blocker |
| 30 | stump_rotten_01 | obstacle | blocker variation |
| 31 | fallen_branch_01 | obstacle | low blocker |

### Row 4 — vegetation and thorn props

| Tile | Name | Category | Purpose |
|---:|---|---|---|
| 32 | bush_dark_01 | vegetation | blocker |
| 33 | bush_dark_02 | vegetation | blocker variation |
| 34 | thorn_bush_01 | vegetation | blocker, hostile forest tone |
| 35 | thorn_bush_02 | vegetation | blocker variation |
| 36 | tall_grass_01 | vegetation | decorative or light cover |
| 37 | tall_grass_02 | vegetation | variation |
| 38 | dead_shrub_01 | vegetation | decorative |
| 39 | mushroom_cluster_01 | vegetation | decorative, possible gather node later |

### Row 5 — tree blockers

| Tile | Name | Category | Purpose |
|---:|---|---|---|
| 40 | tree_trunk_01 | vegetation | blocker |
| 41 | tree_trunk_02 | vegetation | blocker variation |
| 42 | tree_base_roots_01 | vegetation | blocker |
| 43 | tree_base_roots_02 | vegetation | blocker variation |
| 44 | pine_shadow_01 | vegetation | dark tree mass |
| 45 | pine_shadow_02 | vegetation | dark tree mass variation |
| 46 | broken_tree_01 | vegetation | blocker |
| 47 | hollow_tree_01 | vegetation | blocker or interactable later |

### Row 6 — bones and forest story props

| Tile | Name | Category | Purpose |
|---:|---|---|---|
| 48 | bone_pile_01 | prop | quest or gathering prop |
| 49 | skull_01 | prop | grim detail |
| 50 | buried_bones_01 | gathering | archaeology node |
| 51 | old_backpack_01 | prop | fallen adventurer hint |
| 52 | broken_sword_01 | prop | fallen adventurer hint |
| 53 | cracked_shield_01 | prop | fallen adventurer hint |
| 54 | warning_sign_01 | prop | sarcastic forest warning |
| 55 | tiny_grave_01 | prop | death theme |

### Row 7 — interactables and markers

| Tile | Name | Category | Purpose |
|---:|---|---|---|
| 56 | healing_herb_node | gathering | druid gathering node |
| 57 | wild_root_node | gathering | druid gathering node |
| 58 | forest_spore_node | gathering | rare druid node |
| 59 | iron_ore_node_forest | gathering | prospector node |
| 60 | fossil_fragment_node | gathering | archaeology node |
| 61 | forest_exit_marker | interactable | map travel marker |
| 62 | dungeon_entrance_roots | interactable | dungeon entrance |
| 63 | camp_smoke_marker | interactable | goblin camp direction marker |

## 7. Tiled properties

Suggested default properties by category.

### Ground

```yaml
category: ground
collides: false
interactable: false
```

### Transition

```yaml
category: transition
collides: false
interactable: false
```

### Prop

```yaml
category: prop
collides: false
interactable: false
```

### Obstacle

```yaml
category: obstacle
collides: true
interactable: false
```

### Vegetation blocker

```yaml
category: vegetation
collides: true
interactable: false
```

### Gathering node

```yaml
category: gathering
collides: false
interactable: true
interaction_type: gather
item_id: null
station_id: null
```

### Travel marker

```yaml
category: travel
collides: false
interactable: true
interaction_type: travel
target_map: null
```

### Dungeon entrance

```yaml
category: dungeon_entrance
collides: false
interactable: true
interaction_type: dungeon
target_map: null
```

## 8. Specific tile properties

```yaml
bone_pile_01:
  name: bone_pile_01
  category: prop
  collides: false
  interactable: false

buried_bones_01:
  name: buried_bones_01
  category: gathering
  collides: false
  interactable: true
  interaction_type: gather
  item_id: buried_bones

healing_herb_node:
  name: healing_herb_node
  category: gathering
  collides: false
  interactable: true
  interaction_type: gather
  item_id: healing_herb

wild_root_node:
  name: wild_root_node
  category: gathering
  collides: false
  interactable: true
  interaction_type: gather
  item_id: wild_root

forest_spore_node:
  name: forest_spore_node
  category: gathering
  collides: false
  interactable: true
  interaction_type: gather
  item_id: forest_spore

iron_ore_node_forest:
  name: iron_ore_node_forest
  category: gathering
  collides: false
  interactable: true
  interaction_type: gather
  item_id: iron_ore

fossil_fragment_node:
  name: fossil_fragment_node
  category: gathering
  collides: false
  interactable: true
  interaction_type: gather
  item_id: fossil_fragment

forest_exit_marker:
  name: forest_exit_marker
  category: travel
  collides: false
  interactable: true
  interaction_type: travel
  target_map: null

dungeon_entrance_roots:
  name: dungeon_entrance_roots
  category: dungeon_entrance
  collides: false
  interactable: true
  interaction_type: dungeon
  target_map: null

camp_smoke_marker:
  name: camp_smoke_marker
  category: marker
  collides: false
  interactable: true
  interaction_type: inspect
```

## 9. Image prompt

Use this prompt for image generation only after validation.

```text
Create a 128x128 pixel art tileset for a dark medieval fantasy top-down RPG forest, arranged as a strict 8 by 8 grid of 16x16 tiles. The style is crisp readable pixel art, dark hostile forest, damp moss, mud paths, roots, bones, broken adventurer gear, crude grim atmosphere, subtle sarcastic dark fantasy mood. Top-down / three-quarter RPG perspective, consistent upper-left light, limited muted palette with dark moss greens, mud browns, bark browns, dead leaf ochre, wet stone grey, bone beige, dried blood accents, and small toxic green magical accents. The tiles must include: dark grass variations, moss patches, dead leaves, mud path variations, grass-to-path transition edges and corners, small rocks, mossy rocks, root blockers, rotten stumps, fallen branches, dark bushes, thorn bushes, tall grass, dead shrubs, mushroom cluster, tree trunks, tree base roots, broken tree, hollow tree, bone pile, skull, buried bones, old backpack, broken sword, cracked shield, warning sign, tiny grave, healing herb node, wild root node, forest spore node, iron ore node, fossil fragment node, forest exit marker, root-covered dungeon entrance, and small camp smoke marker. Keep ground tiles lower contrast than props and interactables. Make silhouettes readable at 16x16. No text labels inside the image.
```

## 10. Negative prompt

```text
no blur, no anti-aliasing, no realistic rendering, no 3D render, no painterly style, no excessive detail, no inconsistent perspective, no text, no watermark, no background outside the tileset, no cropped tiles, no random objects, no bright cartoon colors, no isometric perspective, no side-view perspective
```

## 11. Acceptance criteria

The generated asset is accepted only if:

- the PNG is exactly 128x128 pixels;
- the grid is exactly 8 columns by 8 rows;
- every tile is 16x16 pixels;
- the asset is readable at 1x zoom;
- the style matches `docs/art_direction.md`;
- the perspective is top-down / three-quarter RPG, not isometric;
- ground tiles are lower contrast than props and interactables;
- blockers are visually identifiable;
- gather nodes are visually identifiable without being too bright;
- no text or watermark is present;
- no blur, anti-aliasing, 3D or painterly rendering is present;
- tile edges are usable in Tiled;
- names and metadata use English snake_case.

## 12. Follow-up outputs

After visual validation, produce:

```text
assets/tilesets/forest_base_16x16.png
assets/tilesets/forest_base_16x16_manifest.json
assets/references/previews/forest_base_16x16_preview.png
```

Optional:

```text
assets/tilesets/forest_base_16x16.tsx
```

## 13. Integration note

Do not upscale this tileset to 32x32 for maps.

The current locked direction is:

```yaml
map_tiles: 16x16
player_sprite: 24x24
player_collision_box: 14x14_or_16x16
small_enemy_sprites: 16x16_or_24x24
inventory_icons: 32x32
world_pickups: 16x16
palette_status: directional_not_strict
```
