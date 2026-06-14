# Forest Ground Tileset Pack Specification

## 1. Purpose

This document replaces the first mixed `forest_base_16x16` attempt for ground construction.

The goal is to create a terrain-oriented forest ground tileset that is practical in Tiled.

This pack focuses only on buildable ground terrain families. Props, blockers and interactables must be handled in separate tilesets.

## 2. Asset identity

```yaml
id: forest_ground_tileset_pack
type: terrain_tileset
priority: P0
status: specification_ready
main_output: assets/tilesets/forest_ground_16x16.png
optional_tiled_metadata: assets/tilesets/forest_ground_16x16.tsx
preview_output: assets/references/previews/forest_ground_16x16_preview.png
manifest_output: assets/tilesets/forest_ground_16x16_manifest.json
```

## 3. Technical constraints

```yaml
tile_size: 16x16
format: png
rendering: crisp_pixel_art
anti_aliasing: false
map_tile_size: 16x16
perspective: top_down_three_quarter
purpose: Tiled ground construction
```

## 4. Tileset structure

The tileset must be organized by terrain family blocks, not as a random atlas.

Each family block must provide:

- center / full tiles;
- top, bottom, left and right edges;
- outer corners;
- inner corners;
- vertical and horizontal strips;
- isolated island tile;
- fill variations.

## 5. First terrain families

The first version should include three terrain families:

```yaml
families:
  - dark_grass_blob
  - mud_path_blob
  - dead_leaf_ground_blob
```

Optional later additions:

```yaml
future_families:
  - wet_moss_blob
  - root_floor_blob
  - pale_bone_ground_blob
  - cave_floor_blob
```

## 6. Recommended block template

Each terrain family uses a 4x5 block of 16x16 tiles.

```text
row 0: outer_corner_tl, edge_top, edge_top, outer_corner_tr
row 1: edge_left, center_01, center_02, edge_right
row 2: edge_left, center_03, center_04, edge_right
row 3: outer_corner_bl, edge_bottom, edge_bottom, outer_corner_br
row 4: isolated, vertical_strip, horizontal_strip, inner_corner_pack
```

The last tile may be visually used as a compact inner-corner reference tile in prototypes. A final production version may expand inner corners into separate tiles if Tiled terrain painting requires it.

## 7. Output layout

The first prototype uses:

```yaml
columns: 12
rows: 5
image_size: 192x80
tile_count: 60
block_size: 4x5
families_per_row: 3
```

Block positions:

```yaml
dark_grass_blob:
  x_tiles: 0-3
  y_tiles: 0-4

mud_path_blob:
  x_tiles: 4-7
  y_tiles: 0-4

dead_leaf_ground_blob:
  x_tiles: 8-11
  y_tiles: 0-4
```

## 8. Tiled properties

Each tile must include:

```yaml
name: string
category: ground
terrain_family: string
terrain_role: string
collides: false
interactable: false
```

## 9. Acceptance criteria

The asset is accepted only if:

- it is clearly organized by terrain family;
- each family can be used to construct blobs or paths;
- tiles are exactly 16x16;
- the PNG is aligned to a regular grid;
- ground contrast stays lower than characters and interactables;
- no props, trees, rocks, loot or interactables are mixed into the file;
- filenames and tile names use English snake_case;
- a manifest and TSX metadata file are provided.

## 10. Next split after this pack

After this ground pack, create separate packs:

```text
assets/tilesets/forest_props_16x16.png
assets/tilesets/forest_interactables_16x16.png
```

Do not merge props back into the ground tileset.
