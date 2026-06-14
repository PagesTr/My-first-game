import json
import re
from pathlib import Path

import pygame


TILE_SIZE = 16
SOURCE_PATH = Path("assets/icons/items_sheet.png")
OUTPUT_ROOT = Path("assets/icons/items")
CATEGORIES = (
    "all",
    "weapons",
    "armor",
    "accessories",
    "consumables",
    "materials",
    "tools",
    "magic",
    "misc",
)
GENERATED_ICON_PATTERN = re.compile(r"^item_r\d{2}_c\d{2}\.png$")


def get_category_for_row(row):
    if 0 <= row <= 4:
        return "weapons"
    if 5 <= row <= 8:
        return "armor"
    if 9 <= row <= 13:
        return "consumables"
    if 14 <= row <= 20:
        return "materials"
    if 21 <= row <= 24:
        return "tools"
    if 25 <= row <= 29:
        return "magic"
    if 30 <= row <= 34:
        return "accessories"
    return "misc"


def create_output_directories():
    for category in CATEGORIES:
        (OUTPUT_ROOT / category).mkdir(parents=True, exist_ok=True)


def remove_generated_icons():
    for category in CATEGORIES:
        category_path = OUTPUT_ROOT / category
        if not category_path.exists():
            continue
        for icon_path in category_path.glob("*.png"):
            if GENERATED_ICON_PATTERN.match(icon_path.name):
                icon_path.unlink()


def is_tile_empty(tile):
    width, height = tile.get_size()
    for y in range(height):
        for x in range(width):
            if tile.get_at((x, y)).a != 0:
                return False
    return True


def save_tile(tile, destination):
    pygame.image.save(tile, str(destination))


def relative_path(path):
    return path.as_posix()


def extract_icons():
    if not SOURCE_PATH.exists():
        print(f"Source spritesheet not found: {SOURCE_PATH}")
        return 1

    pygame.init()
    sheet = pygame.image.load(str(SOURCE_PATH))
    sheet_width, sheet_height = sheet.get_size()
    columns = sheet_width // TILE_SIZE
    rows = sheet_height // TILE_SIZE
    total_cells = columns * rows
    warnings = []

    if sheet_width % TILE_SIZE != 0 or sheet_height % TILE_SIZE != 0:
        warnings.append(
            f"Warning: source size {sheet_width}x{sheet_height} is not a multiple of {TILE_SIZE}; extracting complete tiles only."
        )

    create_output_directories()
    remove_generated_icons()

    icons = []
    skipped_cells = 0

    for row in range(rows):
        for column in range(columns):
            tile_rect = pygame.Rect(column * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            tile = sheet.subsurface(tile_rect).copy()
            if is_tile_empty(tile):
                skipped_cells += 1
                continue

            icon_id = f"item_r{row:02d}_c{column:02d}"
            file_name = f"{icon_id}.png"
            category = get_category_for_row(row)
            all_path = OUTPUT_ROOT / "all" / file_name
            category_path = OUTPUT_ROOT / category / file_name

            save_tile(tile, all_path)
            save_tile(tile, category_path)

            icons.append(
                {
                    "id": icon_id,
                    "source": relative_path(SOURCE_PATH),
                    "row": row,
                    "column": column,
                    "category": category,
                    "path_all": relative_path(all_path),
                    "path_category": relative_path(category_path),
                    "tile_size": TILE_SIZE,
                }
            )

    manifest = {
        "source": relative_path(SOURCE_PATH),
        "tile_size": TILE_SIZE,
        "columns": columns,
        "rows": rows,
        "icons": icons,
    }
    manifest_path = OUTPUT_ROOT / "index.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Total cells: {total_cells}")
    print(f"Extracted icons: {len(icons)}")
    print(f"Skipped cells: {skipped_cells}")
    print(f"Manifest: {manifest_path.as_posix()}")
    for warning in warnings:
        print(warning)

    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(extract_icons())
