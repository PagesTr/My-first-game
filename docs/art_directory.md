# Art Direction

## 1. Visual identity

The game uses a **semi-dark fantasy pixel art direction inspired by the Game Boy Advance era**.

The main references are:

- clear and readable RPG screens inspired by games like Pokemon Emerald;
- warm fantasy environments inspired by games like Zelda: The Minish Cap;
- darker fantasy accents for dangerous zones, combat results, enemies and progression moments.

The game should not look permanently dark. The visual goal is to keep the interface readable, colorful and adventurous, while using darker moods only where they support the gameplay.

## 2. Core visual direction

Reference sentence:

> GBA-inspired fantasy pixel art, readable and adventurous, with semi-dark accents for danger, combat and rewards.

The visual style should feel:

- readable;
- compact;
- retro;
- fantasy-oriented;
- slightly mysterious;
- rewarding after combat;
- simple enough to integrate in Pygame.

Avoid:

- realistic HD assets;
- blurry graphics;
- modern glossy mobile UI;
- mixing pixel art with realistic illustrations;
- overly dark screens that reduce readability;
- assets with inconsistent resolutions or styles.

## 3. Gameplay context

Combat is intended to be **calculated instantly**.

The player should not interact with a live combat screen by choosing actions such as attack or heal.

The main visual combat-related screen should be a **combat result report**, showing:

- victory or defeat;
- enemy or zone context when available;
- XP gained;
- gold gained;
- current level;
- level up information;
- loot gained;
- a clear continue action.

This means the priority UI screen for the art direction is:

```text
ui/screens/result_screen.py
```

## 4. Color palette

### Main colors

| Usage | Name | Hex |
|---|---|---|
| Very dark background | Night blue | `#121820` |
| Dark forest background | Forest dark | `#142A23` |
| Main panel | Blue gray | `#252D36` |
| Secondary panel | Slate dark | `#1B222A` |
| Fantasy border | Soft gold | `#C0AC69` |
| Dark border | Brown gray | `#5C523A` |
| Main text | Warm white | `#EEEAD6` |
| Secondary text | Muted green gray | `#AEB8AE` |

### Functional colors

| Usage | Name | Hex |
|---|---|---|
| Victory / healing | Soft green | `#69C675` |
| Defeat / danger | Brick red | `#C2524C` |
| Gold | Warm gold | `#E4BC56` |
| XP / magic | Soft blue | `#7092CD` |
| Level up | Bright green | `#78D98A` |

### Item rarity colors

| Rarity | Hex |
|---|---|
| Common | `#AAAAAA` |
| Uncommon | `#64DC78` |
| Rare | `#649EFF` |
| Epic | `#B478FF` |
| Legendary | `#FFC850` |
| Unique | `#F05A5A` |

These rarity colors are close to the current inventory and result screen colors, so they should preserve visual continuity.

## 5. UI principles

### Panels

Panels should be drawn with simple pixel-friendly shapes.

Recommended style:

- dark blue-gray fill;
- soft gold or muted light border;
- optional inner darker border;
- clear padding;
- title in gold or warm white;
- secondary text in muted gray-green.

Panels should be used for:

- combat result summary;
- loot section;
- inventory sections;
- equipment panels;
- tooltips;
- future map or zone information.

### Buttons

Buttons should remain simple and readable.

Recommended style:

- dark green-gray or blue-gray fill;
- soft gold border;
- warm white text;
- subtle lighter top edge if needed;
- disabled state in gray;
- no glossy modern effect.

The first important button style is the combat result button:

```text
Continuer
```

### Text

Text must stay readable at 800x600.

Rules:

- use high contrast against the background;
- keep labels short;
- keep reward values visually distinct;
- avoid long paragraphs in gameplay screens;
- use French for visible player-facing text when the rest of the screen is French.

Code names, function names and variable names should remain in English.

## 6. Asset file rules

### Format

Use:

```text
.png
```

Avoid for pixel art:

```text
.jpg
.jpeg
.webp
```

Reason:

- PNG preserves sharp pixels;
- PNG supports transparency;
- JPG compression damages pixel art readability.

### Transparency

Use transparent backgrounds for:

```text
icons/
enemies/
items/
ui/
tiles/
```

Background images do not need transparency.

### Scaling

For pixel art, prefer nearest-neighbor scaling.

In Pygame, prefer:

```python
pygame.transform.scale()
```

Avoid:

```python
pygame.transform.smoothscale()
```

Reason:

- `smoothscale` creates blur;
- `scale` keeps a sharper retro look.

## 7. Recommended asset sizes

| Asset type | Recommended size |
|---|---:|
| Full screen background | `800x600` |
| Retro background upscaled x2 | `400x300` |
| UI icons | `16x16` or `32x32` |
| Item icons | `32x32` |
| Simple enemy sprites | `64x64` |
| Important enemy or boss sprites | `96x96` |
| Tiles | `16x16` or `32x32` |

Recommended first approach:

> UI panels and buttons should be drawn in Pygame first. PNG assets should be added later for backgrounds, icons, enemies and map elements.

## 8. Recommended asset folders

Target structure:

```text
assets/
  backgrounds/
    result_forest.png
    result_defeat_forest.png
    world_map.png

  icons/
    xp.png
    gold.png
    loot_bag.png
    level_up.png
    sword.png
    shield.png
    potion.png

  enemies/
    goblin.png
    wolf.png
    slime.png

  items/
    potion.png
    rusty_sword.png
    leather_armor.png

  tiles/
    grass.png
    path.png
    tree.png
    water.png
    rock.png

  ui/
    button_primary.png
    button_secondary.png
    panel.png
```

This is a target structure, not a requirement to create all assets immediately.

The first useful asset set should be limited to:

```text
assets/backgrounds/result_forest.png
assets/icons/xp.png
assets/icons/gold.png
assets/icons/loot_bag.png
assets/icons/level_up.png
```

## 9. Asset naming rules

Use:

- English;
- lowercase;
- snake_case;
- no spaces;
- no accents;
- descriptive names.

Good examples:

```text
result_forest.png
loot_bag.png
level_up.png
forest_goblin.png
```

Bad examples:

```text
Fond forêt.png
Icone Or Final.png
gobelinRareV2.png
```

## 10. Screen priorities

### Priority 1: combat result report

Main file:

```text
ui/screens/result_screen.py
```

Goal:

- make the combat result screen the first visual reference for the game;
- use the validated GBA semi-dark fantasy direction;
- improve layout without changing combat logic;
- keep the result screen readable and rewarding.

### Priority 2: visual world map

Future file candidate:

```text
ui/screens/world_map_screen.py
```

Goal:

- replace or improve the current zone selection experience;
- create a stronger sense of adventure;
- keep the first version clickable and simple before adding real tile-based movement.

### Priority 3: inventory readability

Main file:

```text
ui/screens/inventory_screen.py
```

Goal:

- improve item readability;
- add icons later;
- preserve current inventory logic;
- keep rarity colors consistent.

### Priority 4: enemies and zone identity

Future assets:

```text
assets/enemies/goblin.png
assets/enemies/wolf.png
assets/enemies/slime.png
```

Goal:

- give more identity to combat reports;
- display the defeated enemy when useful;
- improve zone personality.

## 11. Production rule

Do not create a large asset pack all at once.

Use this rule:

> Create or import an asset only when a screen actually needs it.

Examples:

- do not create a full tileset before a map system exists;
- do not create twenty enemy sprites before enemies are displayed;
- do not create every item icon before the inventory supports icons;
- start with the result screen, then expand progressively.

## 12. Current recommended roadmap

1. Improve `ui/screens/result_screen.py` without external assets, using the mockup direction.
2. Add a few targeted PNG assets for the result screen.
3. Improve the zone selection experience or create a first visual world map.
4. Later, consider a tile-based exploration system if the project is ready for a dedicated exploration block.