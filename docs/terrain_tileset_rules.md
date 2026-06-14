# Terrain Tileset Rules

## 1. Purpose

This document defines how terrain tilesets must be structured for Tiled maps.

A terrain tileset is not a flat collection of decorative tiles. It must provide all edge and corner variants required to build readable organic shapes directly in Tiled.

## 2. Core rule

Ground tiles must be delivered as terrain blob sets / autotile-compatible groups.

Each terrain family must include:

- full center tile;
- outer edges;
- outer corners;
- inner corners;
- narrow strips when useful;
- isolated patches when useful;
- fill variations.

This is required for:

- grass patches;
- dirt paths;
- mud zones;
- stone floor;
- snow or pale ground;
- sand or dry ground;
- cave floor;
- dungeon floor.

## 3. Expected structure

For a basic terrain family, use a readable block structure similar to RPG Maker / Tiled terrain templates.

The goal is to let the level designer paint a blob of terrain and have correct borders.

Recommended minimum per terrain:

```text
center tiles
edge top
edge bottom
edge left
edge right
outer corner top-left
outer corner top-right
outer corner bottom-left
outer corner bottom-right
inner corner top-left
inner corner top-right
inner corner bottom-left
inner corner bottom-right
vertical strip
horizontal strip
single isolated patch
fill variations
```

## 4. Separation between terrain and props

Do not mix too many props into the same terrain block.

Recommended split:

```text
assets/tilesets/forest_ground_16x16.png
assets/tilesets/forest_props_16x16.png
assets/tilesets/forest_interactables_16x16.png
```

`forest_ground_16x16.png` is for map construction.

`forest_props_16x16.png` is for decoration and blockers.

`forest_interactables_16x16.png` is for gather nodes, exits, dungeon entrances and scripted objects.

## 5. Forest ground pack v2 structure

The first forest ground pack should prioritize buildable terrain over decorative diversity.

Recommended contents:

```yaml
main_output: assets/tilesets/forest_ground_16x16.png
tile_size: 16x16
purpose: terrain construction in Tiled
```

Terrain families:

```text
dark_grass_blob
mud_path_blob
pale_dead_ground_blob
```

Optional later families:

```text
wet_moss_blob
root_floor_blob
leaf_litter_blob
```

## 6. Tiled terrain metadata

For each terrain tile, properties should include:

```yaml
name: string
category: ground
terrain_family: string
collides: false
interactable: false
```

For transition tiles:

```yaml
name: string
category: terrain_transition
terrain_family: string
collides: false
interactable: false
```

## 7. Props remain separate

Props should not interrupt terrain usability.

Props include:

- rocks;
- roots;
- stumps;
- bushes;
- trees;
- bones;
- skulls;
- broken gear;
- gathering nodes;
- dungeon entrances;
- markers.

These belong in separate prop or interactable tilesets unless there is a strong reason to combine them.

## 8. Acceptance criteria

A ground tileset is accepted only if:

- it can build organic patches without manual pixel editing;
- it includes center, edges, outer corners and inner corners;
- it is easy to use in Tiled;
- terrain families are visually grouped;
- decorative props do not pollute the terrain workflow;
- all tiles are 16x16;
- the grid is regular;
- ground remains lower contrast than sprites and interactables.
