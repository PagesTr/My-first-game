import json
from pathlib import Path

import pygame


ITEMS_PATH = Path("data/items.json")
ICON_INDEX_PATH = Path("assets/icons/items/index.json")
MAPPING_PATH = Path("data/item_icons.json")
WINDOW_SIZE = (1200, 720)
ITEM_FILTERS = ("All", "Equipment", "Consumable", "Resource", "Quest", "Unmapped")


class IconMapper:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Item Icon Mapper")
        self.clock = pygame.time.Clock()
        self.title_font = pygame.font.Font(None, 28)
        self.font = pygame.font.Font(None, 21)
        self.small_font = pygame.font.Font(None, 17)
        self.items = self._load_items()
        self.icons = self._load_icons()
        self.mapping = self._load_mapping()
        self.selected_item_index = 0
        self.selected_icon_index = None
        self.item_scroll = 0
        self.icon_scroll = 0
        self.active_filter = "All"
        self.dirty = False
        self.running = True
        self.last_icon_click_time = 0
        self.last_icon_click_index = None
        self.item_rects = []
        self.icon_rects = []
        self.filter_rects = []
        self.button_rects = {}
        self.warnings = self._validate_existing_mapping()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self._quit()
            return
        if event.type == pygame.KEYDOWN:
            self._handle_keydown(event.key)
            return
        if event.type == pygame.MOUSEWHEEL:
            mouse_x, _ = pygame.mouse.get_pos()
            if mouse_x < 360:
                self.item_scroll = max(0, self.item_scroll - event.y * 4)
            else:
                self.icon_scroll = max(0, self.icon_scroll - event.y * 3)
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)

    def draw(self):
        self.screen.fill((18, 18, 22))
        self._draw_item_panel()
        self._draw_icon_panel()
        self._draw_detail_panel()

    def _draw_item_panel(self):
        panel = pygame.Rect(0, 0, 360, WINDOW_SIZE[1])
        pygame.draw.rect(self.screen, (28, 29, 34), panel)
        title = self.title_font.render("Items", True, (240, 235, 215))
        self.screen.blit(title, (16, 12))
        self._draw_filters(pygame.Rect(12, 44, 336, 64))

        visible_items = self._get_visible_items()
        row_height = 52
        start_y = 118
        max_rows = (WINDOW_SIZE[1] - start_y - 10) // row_height
        self.item_scroll = min(self.item_scroll, max(0, len(visible_items) - max_rows))
        self.item_rects = []

        for visible_row, item in enumerate(visible_items[self.item_scroll : self.item_scroll + max_rows]):
            item_index = item["index"]
            rect = pygame.Rect(12, start_y + visible_row * row_height, 336, row_height - 6)
            self.item_rects.append((item_index, rect))
            is_selected = item_index == self.selected_item_index
            is_mapped = item["id"] in self.mapping
            pygame.draw.rect(self.screen, (54, 50, 38) if is_selected else (36, 37, 42), rect, border_radius=5)
            pygame.draw.rect(self.screen, (216, 176, 88) if is_selected else (82, 82, 92), rect, 1, border_radius=5)
            marker = "*" if is_mapped else "-"
            item_id = self.font.render(f"{marker} {item['id']}", True, (240, 235, 215))
            meta = self.small_font.render(
                self._shorten(f"{item['name']} | {item['type']} / {item['category']}", 38),
                True,
                (185, 185, 170),
            )
            self.screen.blit(item_id, (rect.x + 8, rect.y + 6))
            self.screen.blit(meta, (rect.x + 8, rect.y + 28))

    def _draw_filters(self, area):
        self.filter_rects = []
        x = area.x
        y = area.y
        for label in ITEM_FILTERS:
            width = max(62, self.small_font.size(label)[0] + 18)
            if x + width > area.right:
                x = area.x
                y += 28
            rect = pygame.Rect(x, y, width, 22)
            self.filter_rects.append((label, rect))
            active = label == self.active_filter
            pygame.draw.rect(self.screen, (74, 58, 36) if active else (39, 40, 45), rect, border_radius=4)
            pygame.draw.rect(self.screen, (210, 166, 82) if active else (80, 82, 92), rect, 1, border_radius=4)
            text = self.small_font.render(label, True, (240, 235, 215) if active else (190, 190, 176))
            self.screen.blit(text, text.get_rect(center=rect.center))
            x += width + 6

    def _draw_icon_panel(self):
        panel = pygame.Rect(360, 0, 600, WINDOW_SIZE[1])
        pygame.draw.rect(self.screen, (22, 23, 28), panel)
        title = self.title_font.render("Icons", True, (240, 235, 215))
        self.screen.blit(title, (376, 12))

        columns = 8
        cell_size = 68
        start_x = 376
        start_y = 50
        max_rows = (WINDOW_SIZE[1] - start_y - 10) // cell_size
        self.icon_scroll = min(self.icon_scroll, max(0, ((len(self.icons) + columns - 1) // columns) - max_rows))
        first_index = self.icon_scroll * columns
        last_index = min(len(self.icons), first_index + max_rows * columns)
        used_paths = set(self.mapping.values())
        self.icon_rects = []

        for index in range(first_index, last_index):
            icon = self.icons[index]
            visible_index = index - first_index
            column = visible_index % columns
            row = visible_index // columns
            rect = pygame.Rect(start_x + column * cell_size, start_y + row * cell_size, cell_size - 8, cell_size - 8)
            self.icon_rects.append((index, rect))
            selected = index == self.selected_icon_index
            used = icon["path"] in used_paths
            pygame.draw.rect(self.screen, (42, 43, 50), rect, border_radius=4)
            pygame.draw.rect(self.screen, (230, 220, 150) if selected else (95, 96, 108), rect, 2 if selected else 1, border_radius=4)
            if used:
                pygame.draw.circle(self.screen, (98, 205, 116), (rect.right - 8, rect.y + 8), 4)
            scaled = pygame.transform.scale(icon["surface"], (32, 32))
            self.screen.blit(scaled, scaled.get_rect(center=(rect.centerx, rect.y + 22)))
            label = self.small_font.render(icon["short_id"], True, (215, 215, 198))
            self.screen.blit(label, label.get_rect(center=(rect.centerx, rect.bottom - 10)))

    def _draw_detail_panel(self):
        panel = pygame.Rect(960, 0, 240, WINDOW_SIZE[1])
        pygame.draw.rect(self.screen, (29, 27, 25), panel)
        title = self.title_font.render("Details", True, (240, 235, 215))
        self.screen.blit(title, (976, 12))

        item = self.items[self.selected_item_index] if self.items else None
        y = 52
        if item:
            lines = [
                f"ID: {item['id']}",
                f"Name: {item['name']}",
                f"Type: {item['type']}",
                f"Category: {item['category']}",
                f"Rarity: {item['rarity']}",
                f"Level: {item['level']}",
                f"Current: {self.mapping.get(item['id'], '-')}",
            ]
            selected_icon = self.icons[self.selected_icon_index]["path"] if self.selected_icon_index is not None else "-"
            lines.append(f"Selected: {selected_icon}")
            for line in lines:
                rendered = self.small_font.render(self._shorten(line, 32), True, (220, 214, 196))
                self.screen.blit(rendered, (976, y))
                y += 22

        mapped_count = sum(1 for item in self.items if item["id"] in self.mapping)
        counter = self.font.render(f"{mapped_count} / {len(self.items)} items mapped", True, (210, 230, 190))
        self.screen.blit(counter, (976, 306))

        instructions = [
            "Click item, click icon",
            "Double-click icon: assign",
            "Enter: assign selected",
            "S: save",
            "C: clear item",
            "Esc: save and quit",
        ]
        y = 342
        for line in instructions:
            rendered = self.small_font.render(line, True, (178, 178, 164))
            self.screen.blit(rendered, (976, y))
            y += 20

        self.button_rects = {
            "save": pygame.Rect(976, 502, 72, 32),
            "clear": pygame.Rect(1058, 502, 72, 32),
            "quit": pygame.Rect(976, 544, 154, 32),
        }
        for action, rect in self.button_rects.items():
            self._draw_button(rect, action.title())

        if self.warnings:
            warning = self.small_font.render(self._shorten(self.warnings[0], 32), True, (235, 160, 90))
            self.screen.blit(warning, (976, 600))

    def _draw_button(self, rect, label):
        pygame.draw.rect(self.screen, (72, 52, 34), rect, border_radius=5)
        pygame.draw.rect(self.screen, (190, 150, 82), rect, 1, border_radius=5)
        text = self.font.render(label, True, (242, 235, 210))
        self.screen.blit(text, text.get_rect(center=rect.center))

    def _handle_click(self, position):
        for label, rect in self.filter_rects:
            if rect.collidepoint(position):
                self.active_filter = label
                self.item_scroll = 0
                return
        for item_index, rect in self.item_rects:
            if rect.collidepoint(position):
                self.selected_item_index = item_index
                return
        for icon_index, rect in self.icon_rects:
            if rect.collidepoint(position):
                now = pygame.time.get_ticks()
                is_double = self.last_icon_click_index == icon_index and now - self.last_icon_click_time <= 400
                self.selected_icon_index = icon_index
                self.last_icon_click_index = icon_index
                self.last_icon_click_time = now
                if is_double:
                    self._assign_selected_icon()
                return
        for action, rect in self.button_rects.items():
            if rect.collidepoint(position):
                if action == "save":
                    self._save_mapping()
                elif action == "clear":
                    self._clear_selected_mapping()
                elif action == "quit":
                    self._quit()
                return

    def _handle_keydown(self, key):
        if key == pygame.K_ESCAPE:
            self._quit()
        elif key == pygame.K_s:
            self._save_mapping()
        elif key == pygame.K_c:
            self._clear_selected_mapping()
        elif key == pygame.K_RETURN:
            self._assign_selected_icon()
        elif key == pygame.K_DOWN:
            self._move_selected_item(1)
        elif key == pygame.K_UP:
            self._move_selected_item(-1)
        elif key == pygame.K_PAGEDOWN:
            self.item_scroll += 8
        elif key == pygame.K_PAGEUP:
            self.item_scroll = max(0, self.item_scroll - 8)

    def _move_selected_item(self, delta):
        visible = self._get_visible_items()
        if not visible:
            return
        current_positions = [item["index"] for item in visible]
        try:
            current = current_positions.index(self.selected_item_index)
        except ValueError:
            current = 0
        current = min(max(current + delta, 0), len(visible) - 1)
        self.selected_item_index = visible[current]["index"]

    def _assign_selected_icon(self):
        if self.selected_icon_index is None or not self.items:
            return
        item_id = self.items[self.selected_item_index]["id"]
        self.mapping[item_id] = self.icons[self.selected_icon_index]["path"]
        self.dirty = True

    def _clear_selected_mapping(self):
        if not self.items:
            return
        item_id = self.items[self.selected_item_index]["id"]
        if item_id in self.mapping:
            del self.mapping[item_id]
            self.dirty = True

    def _save_mapping(self):
        MAPPING_PATH.parent.mkdir(parents=True, exist_ok=True)
        MAPPING_PATH.write_text(
            json.dumps(dict(sorted(self.mapping.items())), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        self.dirty = False

    def _quit(self):
        if self.dirty:
            self._save_mapping()
        self.running = False

    def _get_visible_items(self):
        visible = []
        for item in self.items:
            item_type = item["type"].lower()
            if self.active_filter == "Unmapped" and item["id"] in self.mapping:
                continue
            if self.active_filter not in {"All", "Unmapped"} and item_type != self.active_filter.lower():
                continue
            visible.append(item)
        return visible

    def _load_items(self):
        if not ITEMS_PATH.exists():
            raise SystemExit(f"Missing items file: {ITEMS_PATH}")
        try:
            raw_items = json.loads(ITEMS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid items JSON: {exc}") from exc
        if not isinstance(raw_items, dict):
            raise SystemExit("data/items.json must contain an object.")
        items = []
        for index, (item_id, item_data) in enumerate(sorted(raw_items.items())):
            item_data = item_data if isinstance(item_data, dict) else {}
            items.append(
                {
                    "index": index,
                    "id": item_id,
                    "name": str(item_data.get("name", item_id)),
                    "type": str(item_data.get("type", "unknown")),
                    "category": str(item_data.get("category", "unknown")),
                    "rarity": str(item_data.get("rarity", "-")),
                    "level": str(item_data.get("level", "-")),
                }
            )
        return items

    def _load_icons(self):
        if not ICON_INDEX_PATH.exists():
            raise SystemExit(f"Missing icon index: {ICON_INDEX_PATH}")
        try:
            index_data = json.loads(ICON_INDEX_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid icon index JSON: {exc}") from exc
        icons = []
        for entry in index_data.get("icons", []):
            if not isinstance(entry, dict):
                continue
            path = Path(entry.get("path_all", ""))
            if not path.exists():
                continue
            surface = pygame.image.load(str(path)).convert_alpha()
            icon_id = str(entry.get("id", path.stem))
            icons.append(
                {
                    "id": icon_id,
                    "short_id": icon_id.replace("item_", "").replace("_", ""),
                    "row": int(entry.get("row", 0)),
                    "column": int(entry.get("column", 0)),
                    "path": path.as_posix(),
                    "surface": surface,
                }
            )
        return sorted(icons, key=lambda icon: (icon["row"], icon["column"]))

    def _load_mapping(self):
        if not MAPPING_PATH.exists():
            return {}
        try:
            mapping = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return mapping if isinstance(mapping, dict) else {}

    def _validate_existing_mapping(self):
        warnings = []
        for item_id, icon_path in self.mapping.items():
            if not Path(icon_path).exists():
                warnings.append(f"Missing mapped icon for {item_id}: {icon_path}")
        return warnings

    def _shorten(self, text, max_length):
        text = str(text)
        if len(text) <= max_length:
            return text
        return text[: max(0, max_length - 3)] + "..."


if __name__ == "__main__":
    IconMapper().run()
