import json
from pathlib import Path

import pygame


INDEX_PATH = Path("assets/icons/items/index.json")
CATALOG_PATH = Path("assets/icons/items/icon_catalog.png")
ICON_SCALE = 2
CELL_WIDTH = 72
CELL_HEIGHT = 58
PADDING = 14
COLUMNS = 12
BACKGROUND_COLOR = (18, 18, 22)
CELL_COLOR = (30, 31, 36)
TEXT_COLOR = (225, 225, 210)


def load_index():
    if not INDEX_PATH.exists():
        raise FileNotFoundError(f"Missing icon index: {INDEX_PATH}")
    try:
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid icon index JSON: {INDEX_PATH}: {exc}") from exc


def short_icon_id(icon_id):
    return icon_id.replace("item_", "").replace("_", "")


def load_icons(index_data):
    icons = []
    for entry in index_data.get("icons", []):
        if not isinstance(entry, dict):
            continue
        path = Path(entry.get("path_all", ""))
        icon_id = entry.get("id")
        if not icon_id or not path.exists():
            continue
        try:
            surface = pygame.image.load(str(path)).convert_alpha()
        except pygame.error:
            continue
        icons.append((entry, surface))
    return sorted(icons, key=lambda item: (item[0].get("row", 0), item[0].get("column", 0)))


def build_catalog():
    pygame.init()
    pygame.display.set_mode((1, 1), flags=pygame.HIDDEN)
    font = pygame.font.Font(None, 16)

    index_data = load_index()
    icons = load_icons(index_data)
    if not icons:
        raise RuntimeError("No valid icons found in index.")

    rows = (len(icons) + COLUMNS - 1) // COLUMNS
    width = PADDING * 2 + COLUMNS * CELL_WIDTH
    height = PADDING * 2 + rows * CELL_HEIGHT
    catalog = pygame.Surface((width, height), pygame.SRCALPHA)
    catalog.fill(BACKGROUND_COLOR)

    scaled_size = index_data.get("tile_size", 16) * ICON_SCALE
    for index, (entry, icon) in enumerate(icons):
        column = index % COLUMNS
        row = index // COLUMNS
        x = PADDING + column * CELL_WIDTH
        y = PADDING + row * CELL_HEIGHT
        cell_rect = pygame.Rect(x, y, CELL_WIDTH - 5, CELL_HEIGHT - 5)
        pygame.draw.rect(catalog, CELL_COLOR, cell_rect, border_radius=4)
        pygame.draw.rect(catalog, (72, 72, 82), cell_rect, 1, border_radius=4)

        scaled_icon = pygame.transform.scale(icon, (scaled_size, scaled_size))
        icon_rect = scaled_icon.get_rect(center=(cell_rect.centerx, cell_rect.y + 20))
        catalog.blit(scaled_icon, icon_rect)

        label = font.render(short_icon_id(entry["id"]), True, TEXT_COLOR)
        label_rect = label.get_rect(center=(cell_rect.centerx, cell_rect.bottom - 12))
        catalog.blit(label, label_rect)

    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(catalog, str(CATALOG_PATH))
    pygame.quit()

    print(f"Loaded icons: {len(icons)}")
    print(f"Catalog generated: {CATALOG_PATH.as_posix()}")


if __name__ == "__main__":
    try:
        build_catalog()
    except Exception as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)
