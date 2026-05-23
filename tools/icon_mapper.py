import json
from pathlib import Path

import pygame


ITEMS_PATH = Path("data/items.json")
ICON_INDEX_PATH = Path("assets/icons/items/index.json")
MAPPING_PATH = Path("data/item_icons.json")
WINDOW_SIZE = (1200, 720)
ITEM_FILTERS = ("All", "Equipment", "Consumable", "Resource", "Quest", "Unmapped")
ICON_FILTERS = ("All", "weapons", "armor", "accessories", "consumables", "materials", "tools", "magic", "misc")


class IconMapper:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Item Icon Mapper")
        self.clock = pygame.time.Clock()
        self.title_font = pygame.font.Font(None, 28)
        self.font = pygame.font.Font(None, 21)
        self.small_font = pygame.font.Font(None, 17)
        self.duplicate_icon_count = 0
        self.items = self._load_items()
        self.icons = self._load_icons()
        self.mapping = self._load_mapping()
        self.selected_item_index = 0
        self.selected_icon_index = None
        self.item_scroll = 0
        self.icon_scroll = 0
        self.active_filter = "All"
        self.active_icon_filter = "All"
        self.item_search_text = ""
        self.icon_grid_size = 32
        self.status_message = ""
        self.dirty = False
        self.running = True
        self.last_icon_click_time = 0
        self.last_icon_click_index = None
        self.item_rects = []
        self.icon_rects = []
        self.filter_rects = []
        self.icon_filter_rects = []
        self.button_rects = {}
        self.warnings = self._validate_existing_mapping()
        if self.duplicate_icon_count:
            self.status_message = f"Ignored {self.duplicate_icon_count} duplicate icon entries"

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
            self._handle_keydown(event)
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
        search_text = f"Search: {self.item_search_text or '-'}"
        search_surface = self.small_font.render(self._shorten(search_text, 44), True, (210, 205, 188))
        self.screen.blit(search_surface, (16, 102))

        visible_items = self._get_visible_items()
        row_height = 52
        start_y = 124
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

        self._draw_icon_filters(pygame.Rect(376, 42, 568, 50))
        visible_icons = self._get_visible_icons()
        columns = max(1, 568 // (self.icon_grid_size + 36))
        cell_size = self.icon_grid_size + 36
        start_x = 376
        start_y = 98
        max_rows = (WINDOW_SIZE[1] - start_y - 10) // cell_size
        self.icon_scroll = min(self.icon_scroll, max(0, ((len(visible_icons) + columns - 1) // columns) - max_rows))
        first_index = self.icon_scroll * columns
        last_index = min(len(visible_icons), first_index + max_rows * columns)
        used_paths = set(self.mapping.values())
        self.icon_rects = []

        for index in range(first_index, last_index):
            icon = visible_icons[index]
            visible_index = index - first_index
            column = visible_index % columns
            row = visible_index // columns
            rect = pygame.Rect(start_x + column * cell_size, start_y + row * cell_size, cell_size - 8, cell_size - 8)
            icon_index = icon["index"]
            self.icon_rects.append((icon_index, rect))
            selected = icon_index == self.selected_icon_index
            used = icon["path"] in used_paths
            pygame.draw.rect(self.screen, (42, 43, 50), rect, border_radius=4)
            pygame.draw.rect(self.screen, (230, 220, 150) if selected else (95, 96, 108), rect, 2 if selected else 1, border_radius=4)
            if used:
                pygame.draw.circle(self.screen, (98, 205, 116), (rect.right - 8, rect.y + 8), 4)
            scaled = pygame.transform.scale(icon["surface"], (self.icon_grid_size, self.icon_grid_size))
            self.screen.blit(scaled, scaled.get_rect(center=(rect.centerx, rect.y + 22)))
            label = self.small_font.render(icon["short_id"], True, (215, 215, 198))
            self.screen.blit(label, label.get_rect(center=(rect.centerx, rect.bottom - 10)))

    def _draw_icon_filters(self, area):
        self.icon_filter_rects = []
        x = area.x
        y = area.y
        for label in ICON_FILTERS:
            width = max(54, self.small_font.size(label)[0] + 14)
            if x + width > area.right:
                x = area.x
                y += 24
            rect = pygame.Rect(x, y, width, 20)
            self.icon_filter_rects.append((label, rect))
            active = label == self.active_icon_filter
            pygame.draw.rect(self.screen, (58, 54, 38) if active else (34, 35, 40), rect, border_radius=4)
            pygame.draw.rect(self.screen, (205, 170, 86) if active else (78, 80, 90), rect, 1, border_radius=4)
            text = self.small_font.render(label, True, (240, 235, 215) if active else (188, 188, 174))
            self.screen.blit(text, text.get_rect(center=rect.center))
            x += width + 5

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
            y += 6
            self._draw_icon_preview("Current", self.mapping.get(item["id"]), pygame.Rect(976, y, 96, 56))
            selected_path = self.icons[self.selected_icon_index]["path"] if self.selected_icon_index is not None else None
            self._draw_icon_preview("Selected", selected_path, pygame.Rect(1086, y, 96, 56))
            y += 68
            if selected_path:
                used_by = self._get_items_using_icon(selected_path)
                used_text = f"Used by: {self._format_used_by(used_by)}" if used_by else "Used by: -"
                used_surface = self.small_font.render(self._shorten(used_text, 32), True, (190, 190, 176))
                self.screen.blit(used_surface, (976, y))

        mapped_count = sum(1 for item in self.items if item["id"] in self.mapping)
        counter = self.font.render(f"{mapped_count} / {len(self.items)} items mapped", True, (210, 230, 190))
        self.screen.blit(counter, (976, 336))
        status = self.status_message or f"Ignored {self.duplicate_icon_count} duplicate icon entries"
        status_surface = self.small_font.render(self._shorten(status, 32), True, (210, 205, 160))
        self.screen.blit(status_surface, (976, 364))

        instructions = [
            "Click item, click icon",
            "Double-click icon: assign",
            "Enter: assign selected",
            "A: assign + next",
            "N: next unmapped",
            "+/-: icon zoom",
            "S: save",
            "C: clear item",
            "Esc: save and quit",
        ]
        y = 392
        for line in instructions:
            rendered = self.small_font.render(line, True, (178, 178, 164))
            self.screen.blit(rendered, (976, y))
            y += 20

        self.button_rects = {
            "save": pygame.Rect(976, 578, 72, 30),
            "clear": pygame.Rect(1058, 578, 72, 30),
            "next_unmapped": pygame.Rect(976, 616, 154, 28),
            "assign_next": pygame.Rect(976, 652, 154, 28),
            "quit": pygame.Rect(976, 688, 154, 28),
        }
        for action, rect in self.button_rects.items():
            labels = {
                "next_unmapped": "Next Unmapped",
                "assign_next": "Assign + Next",
            }
            self._draw_button(rect, labels.get(action, action.title()))

        if self.warnings:
            warning = self.small_font.render(self._shorten(self.warnings[0], 32), True, (235, 160, 90))
            self.screen.blit(warning, (976, 600))

    def _draw_icon_preview(self, label, icon_path, rect):
        title = self.small_font.render(label, True, (220, 214, 196))
        self.screen.blit(title, (rect.x, rect.y))
        box = pygame.Rect(rect.x, rect.y + 16, 42, 42)
        pygame.draw.rect(self.screen, (38, 39, 45), box, border_radius=4)
        pygame.draw.rect(self.screen, (92, 94, 106), box, 1, border_radius=4)
        if icon_path:
            icon = self._get_icon_by_path(icon_path)
            if icon is not None:
                scaled = pygame.transform.scale(icon["surface"], (32, 32))
                self.screen.blit(scaled, scaled.get_rect(center=box.center))
        path_text = self.small_font.render(self._shorten(icon_path or "-", 15), True, (178, 178, 164))
        self.screen.blit(path_text, (rect.x + 46, rect.y + 27))

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
        for label, rect in self.icon_filter_rects:
            if rect.collidepoint(position):
                self.active_icon_filter = label
                self.icon_scroll = 0
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
                elif action == "next_unmapped":
                    self._select_next_unmapped()
                elif action == "assign_next":
                    self._assign_selected_icon(assign_next=True)
                elif action == "quit":
                    self._quit()
                return

    def _handle_keydown(self, event):
        key = event.key
        if key == pygame.K_ESCAPE:
            if self.item_search_text:
                self.item_search_text = ""
                self.item_scroll = 0
                self.status_message = "Search cleared"
            else:
                self._quit()
        elif key == pygame.K_s:
            self._save_mapping()
        elif key == pygame.K_c:
            self._clear_selected_mapping()
        elif key == pygame.K_n:
            self._select_next_unmapped()
        elif key == pygame.K_a:
            self._assign_selected_icon(assign_next=True)
        elif key == pygame.K_RETURN:
            self._assign_selected_icon()
        elif key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
            self._change_icon_grid_size(4)
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self._change_icon_grid_size(-4)
        elif key == pygame.K_BACKSPACE:
            self.item_search_text = self.item_search_text[:-1]
            self.item_scroll = 0
        elif key == pygame.K_f and (event.mod & pygame.KMOD_CTRL):
            self.item_search_text = ""
            self.item_scroll = 0
            self.status_message = "Search ready"
        elif key == pygame.K_SLASH:
            self.item_search_text = ""
            self.item_scroll = 0
            self.status_message = "Search ready"
        elif key == pygame.K_DOWN:
            self._move_selected_item(1)
        elif key == pygame.K_UP:
            self._move_selected_item(-1)
        elif key == pygame.K_PAGEDOWN:
            self.item_scroll += 8
        elif key == pygame.K_PAGEUP:
            self.item_scroll = max(0, self.item_scroll - 8)
        elif event.unicode and self._is_search_character(event.unicode):
            self.item_search_text += event.unicode.lower()
            self.item_scroll = 0

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

    def _assign_selected_icon(self, assign_next=False):
        if self.selected_icon_index is None or not self.items:
            self.status_message = "Select an item and an icon first"
            return
        item_id = self.items[self.selected_item_index]["id"]
        self.mapping[item_id] = self.icons[self.selected_icon_index]["path"]
        self.dirty = True
        self.status_message = f"Assigned {item_id} -> {self.icons[self.selected_icon_index]['short_id']}"
        if assign_next:
            self._select_next_unmapped(start_after_current=True)

    def _clear_selected_mapping(self):
        if not self.items:
            return
        item_id = self.items[self.selected_item_index]["id"]
        if item_id in self.mapping:
            del self.mapping[item_id]
            self.dirty = True
            self.status_message = f"Cleared mapping for {item_id}"
        else:
            self.status_message = f"No mapping to clear for {item_id}"

    def _save_mapping(self):
        MAPPING_PATH.parent.mkdir(parents=True, exist_ok=True)
        MAPPING_PATH.write_text(
            json.dumps(dict(sorted(self.mapping.items())), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        self.dirty = False
        self.status_message = f"Saved {len(self.mapping)} mappings"

    def _quit(self):
        if self.dirty:
            self._save_mapping()
        self.running = False

    def _get_visible_items(self):
        visible = []
        search = self.item_search_text.strip().lower()
        for item in self.items:
            item_type = item["type"].lower()
            if self.active_filter == "Unmapped" and item["id"] in self.mapping:
                continue
            if self.active_filter not in {"All", "Unmapped"} and item_type != self.active_filter.lower():
                continue
            if search and not self._item_matches_search(item, search):
                continue
            visible.append(item)
        return visible

    def _get_visible_icons(self):
        if self.active_icon_filter == "All":
            return self.icons
        return [icon for icon in self.icons if icon.get("category") == self.active_icon_filter]

    def _item_matches_search(self, item, search):
        haystack = " ".join(
            [
                item["id"],
                item["name"],
                item["type"],
                item["category"],
            ]
        ).lower()
        return search in haystack

    def _select_next_unmapped(self, start_after_current=False):
        if not self.items:
            return
        start = self.selected_item_index + 1 if start_after_current else self.selected_item_index
        ordered_indexes = list(range(start, len(self.items))) + list(range(0, start))
        for index in ordered_indexes:
            item_id = self.items[index]["id"]
            if item_id not in self.mapping:
                self.selected_item_index = index
                self._ensure_selected_item_visible()
                self.status_message = f"Selected next unmapped: {item_id}"
                return
        self.status_message = "All items are mapped"

    def _ensure_selected_item_visible(self):
        visible = self._get_visible_items()
        visible_indexes = [item["index"] for item in visible]
        if self.selected_item_index not in visible_indexes:
            self.active_filter = "All"
            self.item_search_text = ""
            visible = self._get_visible_items()
            visible_indexes = [item["index"] for item in visible]
        if self.selected_item_index in visible_indexes:
            position = visible_indexes.index(self.selected_item_index)
            max_rows = (WINDOW_SIZE[1] - 124 - 10) // 52
            if position < self.item_scroll:
                self.item_scroll = position
            elif position >= self.item_scroll + max_rows:
                self.item_scroll = max(0, position - max_rows + 1)

    def _change_icon_grid_size(self, delta):
        self.icon_grid_size = min(48, max(24, self.icon_grid_size + delta))
        self.icon_scroll = 0
        self.status_message = f"Icon size: {self.icon_grid_size}px"

    def _is_search_character(self, text):
        return len(text) == 1 and (text.isalnum() or text in {" ", "_", "-"})

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
        seen_keys = set()
        for entry in index_data.get("icons", []):
            if not isinstance(entry, dict):
                continue
            icon_id = str(entry.get("id", ""))
            path_value = entry.get("path_all")
            dedupe_key = str(path_value or icon_id)
            if not dedupe_key:
                continue
            if dedupe_key in seen_keys:
                self.duplicate_icon_count += 1
                continue
            seen_keys.add(dedupe_key)

            path = Path(path_value or "")
            if not path.exists():
                continue
            surface = pygame.image.load(str(path)).convert_alpha()
            if not icon_id:
                icon_id = path.stem
            icons.append(
                {
                    "index": 0,
                    "id": icon_id,
                    "short_id": icon_id.replace("item_", "").replace("_", ""),
                    "row": int(entry.get("row", 0)),
                    "column": int(entry.get("column", 0)),
                    "category": str(entry.get("category", "misc")),
                    "path": path.as_posix(),
                    "surface": surface,
                }
            )
        sorted_icons = sorted(icons, key=lambda icon: (icon["row"], icon["column"]))
        for index, icon in enumerate(sorted_icons):
            icon["index"] = index
        return sorted_icons

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

    def _get_icon_by_path(self, icon_path):
        for icon in self.icons:
            if icon["path"] == icon_path:
                return icon
        return None

    def _get_items_using_icon(self, icon_path):
        return sorted(item_id for item_id, mapped_path in self.mapping.items() if mapped_path == icon_path)

    def _format_used_by(self, item_ids):
        if not item_ids:
            return "-"
        shown = item_ids[:3]
        suffix = f" +{len(item_ids) - len(shown)}" if len(item_ids) > len(shown) else ""
        return ", ".join(shown) + suffix

    def _shorten(self, text, max_length):
        text = str(text)
        if len(text) <= max_length:
            return text
        return text[: max(0, max_length - 3)] + "..."


if __name__ == "__main__":
    IconMapper().run()
