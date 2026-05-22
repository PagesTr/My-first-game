# Complete Blob Terrain Tileset Rules

## 1. Purpose

Terrain tilesets used for Tiled automapping must not use a reduced 4x5 template when the terrain needs organic construction.

A reduced template misses important configurations such as U-shapes, three-sided tiles, almost-full tiles, inverse corners and mixed corner cases.

## 2. Rule

Ground terrain must be produced as a complete blob terrain set based on neighbor masks.

For each terrain family, provide at minimum:

- center tile;
- 4 single-edge tiles;
- 4 outer-corner tiles;
- 4 inner-corner tiles;
- 4 two-opposite-edge tiles;
- 4 two-adjacent-edge tiles;
- 4 three-edge tiles;
- 4 almost-full tiles with one missing corner/edge configuration;
- isolated tile;
- vertical strip;
- horizontal strip;
- multiple center variations.

## 3. Seam rule

Never draw a dark outline on all four sides of every tile.

Contours may appear only on exposed terrain borders. Adjacent terrain tiles must connect without visible grid seams.

Internal center tiles must be seamless or near-seamless.

## 4. Separation rule

Ground terrain tilesets are for painting terrain only.

Do not include:

- trees;
- rocks;
- roots;
- bones;
- props;
- interactables;
- markers;
- loot;
- dungeon entrances.

These belong in separate prop and interactable tilesets.

## 5. Recommended family file split

For practical Tiled work, prefer one file per terrain family when the terrain uses a full blob set.

Examples:

```text
assets/tilesets/terrain/forest_grass_blob_16x16.png
assets/tilesets/terrain/forest_mud_blob_16x16.png
assets/tilesets/terrain/forest_dead_leaves_blob_16x16.png
```

Combined sheets may be used for preview, but individual files are easier to configure in Tiled.

## 6. Acceptance criteria

A blob terrain set is accepted only if:

- it includes enough masks to avoid automap gaps;
- it includes three-edge / three-corner configurations;
- connected tiles do not show square seams;
- center tiles are visually tileable;
- exposed borders are readable but not over-outlined;
- the terrain is usable in Tiled without manual patching;
- every tile is 16x16;
- filenames and metadata use English snake_case.
