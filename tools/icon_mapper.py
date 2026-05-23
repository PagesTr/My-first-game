import json
from pathlib import Path

import pygame


ITEMS_PATH = Path("data/items.json")
ICON_INDEX_PATH = Path("assets/icons/items/index.json")
ICON_TAGS_PATH = Path("assets/icons/items/icon_tags.json")
MAPPING_PATH = Path("data/item_icons.json")
WINDOW_SIZE = (1600, 900)
ITEM_PANEL_RECT = pygame.Rect(0, 0, 380, 900)
ICON_PANEL_RECT = pygame.Rect(380, 0, 820, 900)
DETAIL_PANEL_RECT = pygame.Rect(1200, 0, 400, 900)
RIGHT_INSET = 16
RIGHT_PANEL_WIDTH = 368
ITEM_FILTERS = ("All", "Equipment", "Consumable", "Resource", "Quest", "Unmapped")
FAMILIES = (
    "equipment",
    "weapon",
    "armor",
    "accessory",
    "consumable",
    "material",
    "monster_part",
    "profession_tool",
    "crafting_component",
    "quest_item",
    "currency",
    "magic",
    "food",
    "misc",
)
SUBCATEGORIES = {
    "weapon": ("sword", "axe", "dagger", "bow", "staff", "mace", "spear", "shield", "wand", "offhand"),
    "armor": ("helmet", "chest", "pants", "gloves", "boots", "cloak", "belt"),
    "accessory": ("ring", "amulet", "trinket", "charm"),
    "profession_tool": (
        "woodcutting_axe",
        "mining_pickaxe",
        "herbalism_sickle",
        "fishing_rod",
        "skinning_knife",
        "blacksmith_hammer",
        "alchemy_tool",
        "cooking_tool",
        "tailoring_needle",
        "crafting_tool",
    ),
    "material": ("wood", "ore", "ingot", "stone", "herb", "plant", "cloth", "leather", "bone", "gem", "essence", "mushroom"),
    "monster_part": ("goblin_part", "beast_part", "insect_part", "undead_part", "plant_monster_part", "fang", "claw", "eye", "ear", "bone", "hide"),
    "consumable": ("health_potion", "mana_potion", "buff_potion", "antidote", "elixir", "scroll", "food", "drink"),
    "quest_item": ("quest_document", "quest_relic", "key", "token", "coin", "book", "unknown"),
    "equipment": ("unknown",),
    "crafting_component": ("unknown",),
    "currency": ("coin", "token"),
    "magic": ("scroll", "essence", "relic"),
    "food": ("food", "drink"),
    "misc": ("unknown",),
}
ICON_FILTERS = ("All", "Suggested", "Uncategorized", "Favorites", "Used", "Unused", *FAMILIES)
FAMILY_SHORTCUTS = {
    pygame.K_1: "weapon",
    pygame.K_2: "armor",
    pygame.K_3: "accessory",
    pygame.K_4: "consumable",
    pygame.K_5: "material",
    pygame.K_6: "monster_part",
    pygame.K_7: "profession_tool",
    pygame.K_8: "quest_item",
    pygame.K_9: "magic",
    pygame.K_0: "misc",
}
CATEGORY_COLORS = {
    "equipment": (160, 160, 170),
    "weapon": (203, 111, 92),
    "armor": (130, 151, 178),
    "accessory": (201, 166, 85),
    "consumable": (104, 181, 148),
    "material": (126, 184, 106),
    "monster_part": (171, 119, 82),
    "profession_tool": (180, 144, 90),
    "crafting_component": (184, 132, 76),
    "quest_item": (212, 190, 132),
    "magic": (156, 112, 216),
    "tools": (174, 150, 112),
    "currency": (225, 186, 78),
    "food": (198, 142, 90),
    "misc": (140, 140, 150),
    "uncategorized": (88, 90, 102),
}


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
        self.icon_tags = self._load_icon_tags()
        self.items = self._load_items()
        self.icons = self._load_icons()
        self.mapping = self._load_mapping()
        self.selected_item_index = 0
        self.selected_icon_index = None
        self.item_scroll = 0
        self.icon_scroll = 0
        self.active_filter = "All"
        self.active_icon_filter = "All"
        self.active_family = "weapon"
        self.active_subcategory = "sword"
        self.only_active_subcategory = False
        self.paint_mode = False
        self.item_search_text = ""
        self.icon_search_text = ""
        self.search_target = "item"
        self.tag_input_active = False
        self.tag_input_text = ""
        self.apply_tags_to_selection = False
        self.icon_grid_size = 32
        self.status_message = ""
        self.dirty = False
        self.dirty_tags = False
        self.running = True
        self.last_icon_click_time = 0
        self.last_icon_click_index = None
        self.selected_icon_indexes = set()
        self.last_selected_icon_index = None
        self.item_rects = []
        self.icon_rects = []
        self.filter_rects = []
        self.icon_filter_rects = []
        self.family_rects = []
        self.subcategory_rects = []
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
            if mouse_x < ITEM_PANEL_RECT.right:
                self.item_scroll = max(0, self.item_scroll - event.y * 4)
            elif mouse_x < ICON_PANEL_RECT.right:
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
        panel = ITEM_PANEL_RECT
        pygame.draw.rect(self.screen, (28, 29, 34), panel)
        title = self.title_font.render("Items", True, (240, 235, 215))
        self.screen.blit(title, (16, 12))
        self._draw_filters(pygame.Rect(12, 44, panel.width - 24, 64))
        search_text = f"Item search: {self.item_search_text or '-'}"
        search_color = (236, 222, 150) if self.search_target == "item" else (210, 205, 188)
        search_surface = self.small_font.render(self._shorten_middle(search_text, 48), True, search_color)
        self.screen.blit(search_surface, (16, 102))

        visible_items = self._get_visible_items()
        row_height = 52
        start_y = 124
        max_rows = (WINDOW_SIZE[1] - start_y - 10) // row_height
        self.item_scroll = min(self.item_scroll, max(0, len(visible_items) - max_rows))
        self.item_rects = []

        for visible_row, item in enumerate(visible_items[self.item_scroll : self.item_scroll + max_rows]):
            item_index = item["index"]
            rect = pygame.Rect(12, start_y + visible_row * row_height, panel.width - 24, row_height - 6)
            self.item_rects.append((item_index, rect))
            is_selected = item_index == self.selected_item_index
            is_mapped = item["id"] in self.mapping
            pygame.draw.rect(self.screen, (54, 50, 38) if is_selected else (36, 37, 42), rect, border_radius=5)
            pygame.draw.rect(self.screen, (216, 176, 88) if is_selected else (82, 82, 92), rect, 1, border_radius=5)
            marker = "*" if is_mapped else "-"
            item_id = self.font.render(f"{marker} {item['id']}", True, (240, 235, 215))
            meta = self.small_font.render(
                self._shorten_middle(f"{item['name']} | {item['type']} / {item['category']}", 44),
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
        panel = ICON_PANEL_RECT
        pygame.draw.rect(self.screen, (22, 23, 28), panel)
        title = self.title_font.render("Icons", True, (240, 235, 215))
        self.screen.blit(title, (panel.x + 16, 12))
        icon_search = f"Icon search: {self.icon_search_text or '-'}"
        search_color = (236, 222, 150) if self.search_target == "icon" else (190, 190, 176)
        self.screen.blit(self.small_font.render(self._shorten_middle(icon_search, 80), True, search_color), (panel.x + 112, 18))

        filter_bottom = self._draw_icon_filters(pygame.Rect(panel.x + 16, 42, panel.width - 32, 110))
        visible_icons = self._get_visible_icons()
        grid_width = panel.width - 32
        columns = max(1, grid_width // (self.icon_grid_size + 36))
        cell_size = self.icon_grid_size + 36
        start_x = panel.x + 16
        start_y = filter_bottom + 12
        max_rows = (WINDOW_SIZE[1] - start_y - 10) // cell_size
        self.icon_scroll = min(self.icon_scroll, max(0, ((len(visible_icons) + columns - 1) // columns) - max_rows))
        first_index = self.icon_scroll * columns
        last_index = min(len(visible_icons), first_index + max_rows * columns)
        used_paths = set(self.mapping.values())
        self.icon_rects = []

        if not visible_icons:
            message = self.font.render("No icons for this filter", True, (190, 190, 176))
            self.screen.blit(message, message.get_rect(center=(panel.centerx, start_y + 80)))
            return

        for index in range(first_index, last_index):
            icon = visible_icons[index]
            visible_index = index - first_index
            column = visible_index % columns
            row = visible_index // columns
            rect = pygame.Rect(start_x + column * cell_size, start_y + row * cell_size, cell_size - 8, cell_size - 8)
            icon_index = icon["index"]
            self.icon_rects.append((icon_index, rect))
            selected = icon_index == self.selected_icon_index
            multi_selected = icon_index in self.selected_icon_indexes
            used = icon["path"] in used_paths
            favorite = self._is_icon_favorite(icon["id"])
            family = self._get_icon_family(icon["id"])
            border_color = (230, 220, 150) if selected else (86, 150, 232) if multi_selected else CATEGORY_COLORS.get(family, CATEGORY_COLORS["uncategorized"])
            fill_color = (48, 42, 32) if self.paint_mode else (42, 43, 50)
            pygame.draw.rect(self.screen, fill_color, rect, border_radius=4)
            pygame.draw.rect(self.screen, border_color, rect, 2 if selected else 1, border_radius=4)
            if used:
                pygame.draw.circle(self.screen, (98, 205, 116), (rect.right - 8, rect.y + 8), 4)
            if favorite:
                star = self.small_font.render("*", True, (245, 210, 80))
                self.screen.blit(star, (rect.x + 5, rect.y + 1))
            icon_center_y = rect.y + 8 + self.icon_grid_size // 2
            self._draw_scaled_icon(icon["surface"], (rect.centerx, icon_center_y), self.icon_grid_size)
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
        return y + 20

    def _draw_detail_panel(self):
        pygame.draw.rect(self.screen, (29, 27, 25), DETAIL_PANEL_RECT)
        self._draw_item_details_panel()
        self._draw_icon_preview_panel()
        self._draw_icon_taxonomy_panel()
        self._draw_active_tagging_panel()
        self._draw_action_panel()
        self._draw_help_status_panel()

    def _draw_item_details_panel(self):
        rect = pygame.Rect(1216, 16, RIGHT_PANEL_WIDTH, 150)
        content = self._draw_panel(rect, "Item Details")
        item = self.items[self.selected_item_index] if self.items else None
        if not item:
            self._draw_text_lines(["No item selected"], content.x, content.y, 18, content.bottom, self.small_font, (220, 214, 196))
            return
        lines = [
            f"ID: {item['id']}",
            f"Name: {item['name']}",
            f"Type: {item['type']}",
            f"Category: {item['category']}",
            f"Current: {self.mapping.get(item['id'], '-')}",
        ]
        self._draw_text_lines(lines, content.x, content.y, 18, content.bottom, self.small_font, (220, 214, 196))

    def _draw_icon_preview_panel(self):
        rect = pygame.Rect(1216, 176, RIGHT_PANEL_WIDTH, 140)
        content = self._draw_panel(rect, "Icon Preview")
        item = self.items[self.selected_item_index] if self.items else None
        selected_path = self.icons[self.selected_icon_index]["path"] if self.selected_icon_index is not None else None
        current_path = self.mapping.get(item["id"]) if item else None
        self._draw_icon_preview("Current", current_path, pygame.Rect(content.x, content.y, 168, 58))
        self._draw_icon_preview("Selected", selected_path, pygame.Rect(content.x + 184, content.y, 168, 58))
        used_by = self._get_items_using_icon(selected_path) if selected_path else []
        used_text = f"Used by: {self._format_used_by(used_by)}" if used_by else "Used by: -"
        self._draw_text_lines([used_text], content.x, content.y + 74, 18, content.bottom, self.small_font, (190, 190, 176))

    def _draw_icon_taxonomy_panel(self):
        rect = pygame.Rect(1216, 326, RIGHT_PANEL_WIDTH, 170)
        content = self._draw_panel(rect, "Icon Taxonomy")
        icon = self.icons[self.selected_icon_index] if self.selected_icon_index is not None else None
        if not icon:
            self._draw_text_lines(["Icon: -"], content.x, content.y, 18, content.bottom, self.small_font, (210, 205, 188))
            return
        metadata = self._get_icon_metadata(icon["id"])
        lines = [
            f"Icon: {icon['id']}",
            f"Family: {metadata.get('family', 'uncategorized')}",
            f"Subcategory: {metadata.get('subcategory', 'unknown')}",
            f"Favorite: {bool(metadata.get('favorite', False))}",
            f"Tags: {', '.join(metadata.get('tags', [])) or '-'}",
            f"Selected: {len(self._get_target_icon_indexes())}",
        ]
        if self.tag_input_active:
            lines.append(f"Input: {self.tag_input_text}")
        self._draw_text_lines(lines, content.x, content.y, 18, content.bottom, self.small_font, (210, 205, 188))

    def _draw_active_tagging_panel(self):
        rect = pygame.Rect(1216, 506, RIGHT_PANEL_WIDTH, 150)
        content = self._draw_panel(rect, "Active Tagging")
        paint = "on" if self.paint_mode else "off"
        sub_filter = "on" if self.only_active_subcategory else "off"
        lines = [
            f"Family: {self.active_family}",
            f"Subcategory: {self.active_subcategory}",
            f"Paint mode: {paint}",
            f"Only active subcategory: {sub_filter}",
            "1-0 family | Tab subcategory",
            "G apply | P paint | O filter",
        ]
        self._draw_text_lines(lines, content.x, content.y, 18, content.bottom, self.small_font, (220, 214, 196))

    def _draw_action_panel(self):
        rect = pygame.Rect(1216, 666, RIGHT_PANEL_WIDTH, 110)
        content = self._draw_panel(rect, "Actions")
        self.button_rects = {
            "save": pygame.Rect(content.x, content.y, 104, 30),
            "clear": pygame.Rect(content.x + 116, content.y, 104, 30),
            "quit": pygame.Rect(content.x + 232, content.y, 104, 30),
            "next_unmapped": pygame.Rect(content.x, content.y + 42, 104, 30),
            "assign_next": pygame.Rect(content.x + 116, content.y + 42, 104, 30),
            "apply_tags": pygame.Rect(content.x + 232, content.y + 42, 104, 30),
        }
        labels = {
            "next_unmapped": "Next",
            "assign_next": "Assign +",
            "apply_tags": "Apply Tags",
        }
        for action, button_rect in self.button_rects.items():
            self._draw_button(button_rect, labels.get(action, action.title()))

    def _draw_help_status_panel(self):
        rect = pygame.Rect(1216, 786, RIGHT_PANEL_WIDTH, 100)
        content = self._draw_panel(rect, "Help / Status")
        mapped_count = sum(1 for item in self.items if item["id"] in self.mapping)
        status = self.status_message or f"Ignored {self.duplicate_icon_count} duplicate icon entries"
        lines = [
            f"{mapped_count} / {len(self.items)} mapped",
            status,
            "1-0 family | Tab subcategory | G apply",
            "P paint | T tags | A assign+next | S save",
            "Esc clear/quit",
        ]
        if self.warnings:
            lines.insert(2, self.warnings[0])
        self._draw_text_lines(lines, content.x, content.y, 17, content.bottom, self.small_font, (210, 205, 160))

    def _draw_icon_preview(self, label, icon_path, rect):
        title = self.small_font.render(label, True, (220, 214, 196))
        self.screen.blit(title, (rect.x, rect.y))
        box = pygame.Rect(rect.x, rect.y + 18, 48, 48)
        pygame.draw.rect(self.screen, (38, 39, 45), box, border_radius=4)
        pygame.draw.rect(self.screen, (92, 94, 106), box, 1, border_radius=4)
        if icon_path:
            icon = self._get_icon_by_path(icon_path)
            if icon is not None:
                self._draw_scaled_icon(icon["surface"], box.center, 36)
        path_text = self.small_font.render(self._shorten_middle(icon_path or "-", 20), True, (178, 178, 164))
        self.screen.blit(path_text, (rect.x + 56, rect.y + 32))

    def _draw_button(self, rect, label):
        pygame.draw.rect(self.screen, (72, 52, 34), rect, border_radius=5)
        pygame.draw.rect(self.screen, (190, 150, 82), rect, 1, border_radius=5)
        text = self.font.render(label, True, (242, 235, 210))
        self.screen.blit(text, text.get_rect(center=rect.center))

    def _draw_panel(self, rect, title):
        pygame.draw.rect(self.screen, (36, 33, 30), rect, border_radius=6)
        pygame.draw.rect(self.screen, (126, 101, 58), rect, 1, border_radius=6)
        title_surface = self.font.render(title, True, (240, 235, 215))
        self.screen.blit(title_surface, (rect.x + 10, rect.y + 8))
        return pygame.Rect(rect.x + 10, rect.y + 34, rect.width - 20, rect.height - 44)

    def _draw_text_lines(self, lines, start_x, start_y, line_height, max_y, font, color):
        y = start_y
        for index, line in enumerate(lines):
            if y + line_height > max_y:
                ellipsis = font.render("...", True, color)
                self.screen.blit(ellipsis, (start_x, max_y - line_height))
                return
            rendered = font.render(self._shorten_middle(line, 54), True, color)
            self.screen.blit(rendered, (start_x, y))
            y += line_height

    def _draw_scaled_icon(self, surface, center, size):
        scaled = pygame.transform.scale(surface, (size, size))
        self.screen.blit(scaled, scaled.get_rect(center=center))

    def _draw_taxonomy_controls(self, x, y):
        self.family_rects = []
        self.subcategory_rects = []
        paint = "PAINT MODE" if self.paint_mode else "Paint off"
        active = f"Active: {self.active_family}/{self.active_subcategory}"
        self.screen.blit(self.small_font.render(paint, True, (245, 190, 90) if self.paint_mode else (160, 155, 142)), (x, y))
        self.screen.blit(self.small_font.render(self._shorten(active, 32), True, (220, 214, 196)), (x, y + 18))
        family_y = y + 40
        for index, family in enumerate(FAMILIES):
            rect = pygame.Rect(x + (index % 2) * 82, family_y + (index // 2) * 18, 78, 16)
            self.family_rects.append((family, rect))
            is_active = family == self.active_family
            pygame.draw.rect(self.screen, (74, 58, 36) if is_active else (37, 38, 43), rect, border_radius=3)
            text = self.small_font.render(self._shorten(family, 11), True, (240, 235, 215) if is_active else (178, 178, 164))
            self.screen.blit(text, (rect.x + 3, rect.y + 1))
        family_rows = (len(FAMILIES) + 1) // 2
        sub_y = family_y + family_rows * 18 + 8
        for index, subcategory in enumerate(self._get_active_subcategories()[:8]):
            rect = pygame.Rect(x + (index % 2) * 82, sub_y + (index // 2) * 18, 78, 16)
            self.subcategory_rects.append((subcategory, rect))
            is_active = subcategory == self.active_subcategory
            pygame.draw.rect(self.screen, (56, 60, 78) if is_active else (37, 38, 43), rect, border_radius=3)
            text = self.small_font.render(self._shorten(subcategory, 11), True, (235, 235, 220) if is_active else (178, 178, 164))
            self.screen.blit(text, (rect.x + 3, rect.y + 1))

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
        for family, rect in self.family_rects:
            if rect.collidepoint(position):
                self._set_active_family(family)
                return
        for subcategory, rect in self.subcategory_rects:
            if rect.collidepoint(position):
                self.active_subcategory = subcategory
                self.status_message = f"Active subcategory: {subcategory}"
                return
        for item_index, rect in self.item_rects:
            if rect.collidepoint(position):
                self.selected_item_index = item_index
                return
        for icon_index, rect in self.icon_rects:
            if rect.collidepoint(position):
                self._select_icon(icon_index, pygame.key.get_mods())
                return
        for action, rect in self.button_rects.items():
            if rect.collidepoint(position):
                if action == "save":
                    self._save_all()
                elif action == "clear":
                    self._clear_selected_mapping()
                elif action == "next_unmapped":
                    self._select_next_unmapped()
                elif action == "assign_next":
                    self._assign_selected_icon(assign_next=True)
                elif action == "apply_tags":
                    self._apply_active_taxonomy()
                elif action == "quit":
                    self._quit()
                return

    def _handle_keydown(self, event):
        key = event.key
        if self.tag_input_active:
            self._handle_tag_input_key(event)
            return
        if key == pygame.K_ESCAPE:
            if self.icon_search_text:
                self.icon_search_text = ""
                self.icon_scroll = 0
                self.status_message = "Icon search cleared"
            elif self.item_search_text:
                self.item_search_text = ""
                self.item_scroll = 0
                self.status_message = "Item search cleared"
            elif len(self.selected_icon_indexes) > 1:
                self.selected_icon_indexes.clear()
                self.status_message = "Cleared icon selection"
            else:
                self._quit()
        elif key == pygame.K_s:
            self._save_all()
        elif key == pygame.K_c:
            self._clear_selected_mapping()
        elif key == pygame.K_n:
            self._select_next_unmapped()
        elif key == pygame.K_a:
            self._assign_selected_icon(assign_next=True)
        elif key == pygame.K_f and (event.mod & pygame.KMOD_CTRL):
            self._cycle_search_target(reset=True)
        elif key == pygame.K_f:
            self._toggle_selected_icon_favorite()
        elif key == pygame.K_t:
            self.apply_tags_to_selection = bool(event.mod & pygame.KMOD_SHIFT)
            self._start_tag_input()
        elif key == pygame.K_g:
            self._apply_active_taxonomy()
        elif key == pygame.K_p:
            self.paint_mode = not self.paint_mode
            self.status_message = "Paint mode on" if self.paint_mode else "Paint mode off"
        elif key == pygame.K_o:
            self.only_active_subcategory = not self.only_active_subcategory
            self.icon_scroll = 0
            self.status_message = "Only active subcategory on" if self.only_active_subcategory else "Only active subcategory off"
        elif key == pygame.K_TAB:
            self._cycle_active_subcategory(-1 if event.mod & pygame.KMOD_SHIFT else 1)
        elif key in FAMILY_SHORTCUTS:
            self._set_active_family(FAMILY_SHORTCUTS[key])
        elif key == pygame.K_RETURN:
            self._assign_selected_icon()
        elif key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
            self._change_icon_grid_size(4)
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self._change_icon_grid_size(-4)
        elif key == pygame.K_BACKSPACE:
            self._append_search_text(backspace=True)
        elif key == pygame.K_SLASH:
            self._cycle_search_target(reset=True)
        elif key == pygame.K_DOWN:
            self._move_selected_item(1)
        elif key == pygame.K_UP:
            self._move_selected_item(-1)
        elif key == pygame.K_PAGEDOWN:
            self.item_scroll += 8
        elif key == pygame.K_PAGEUP:
            self.item_scroll = max(0, self.item_scroll - 8)
        elif event.unicode and self._is_search_character(event.unicode):
            self._append_search_text(event.unicode.lower())

    def _handle_tag_input_key(self, event):
        if event.key == pygame.K_ESCAPE:
            self.tag_input_active = False
            self.tag_input_text = ""
            self.status_message = "Tag input cancelled"
        elif event.key == pygame.K_RETURN:
            self._commit_tag_input()
        elif event.key == pygame.K_BACKSPACE:
            self.tag_input_text = self.tag_input_text[:-1]
        elif event.unicode and self._is_tag_character(event.unicode):
            self.tag_input_text += event.unicode.lower()

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

    def _select_icon(self, icon_index, modifiers):
        now = pygame.time.get_ticks()
        is_double = self.last_icon_click_index == icon_index and now - self.last_icon_click_time <= 400
        if modifiers & pygame.KMOD_SHIFT and self.last_selected_icon_index is not None:
            start = min(self.last_selected_icon_index, icon_index)
            end = max(self.last_selected_icon_index, icon_index)
            self.selected_icon_indexes.update(range(start, end + 1))
        elif modifiers & pygame.KMOD_CTRL:
            if icon_index in self.selected_icon_indexes:
                self.selected_icon_indexes.remove(icon_index)
            else:
                self.selected_icon_indexes.add(icon_index)
        else:
            self.selected_icon_indexes = {icon_index}

        self.selected_icon_index = icon_index
        self.last_selected_icon_index = icon_index
        self.last_icon_click_index = icon_index
        self.last_icon_click_time = now
        if self.paint_mode:
            self._apply_taxonomy_to_icon(icon_index)
        elif is_double:
            self._assign_selected_icon()

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

    def _save_icon_tags(self):
        ICON_TAGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        cleaned_tags = {
            icon_id: self._normalize_icon_metadata(metadata)
            for icon_id, metadata in sorted(self.icon_tags.items())
            if isinstance(metadata, dict)
        }
        ICON_TAGS_PATH.write_text(
            json.dumps(cleaned_tags, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.icon_tags = cleaned_tags
        self.dirty_tags = False

    def _save_all(self):
        if self.dirty:
            self._save_mapping()
        if self.dirty_tags:
            self._save_icon_tags()
        if not self.dirty and not self.dirty_tags:
            self.status_message = f"Saved {len(self.mapping)} mappings and icon tags"

    def _quit(self):
        if self.dirty or self.dirty_tags:
            self._save_all()
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
        used_paths = set(self.mapping.values())
        search = self.icon_search_text.strip().lower()
        suggested_family, suggested_subcategory = self._guess_taxonomy_for_item(self.items[self.selected_item_index]) if self.items else (None, None)
        visible = []
        for icon in self.icons:
            family = self._get_icon_family(icon["id"])
            subcategory = self._get_icon_subcategory(icon["id"])
            is_used = icon["path"] in used_paths
            if self.active_icon_filter == "Uncategorized" and family != "uncategorized":
                continue
            if self.active_icon_filter == "Favorites" and not self._is_icon_favorite(icon["id"]):
                continue
            if self.active_icon_filter == "Used" and not is_used:
                continue
            if self.active_icon_filter == "Unused" and is_used:
                continue
            if self.active_icon_filter == "Suggested" and not self._icon_matches_suggestion(icon, suggested_family, suggested_subcategory):
                continue
            if self.active_icon_filter in FAMILIES and family != self.active_icon_filter:
                continue
            if self.only_active_subcategory and (family != self.active_family or subcategory != self.active_subcategory):
                continue
            if search and not self._icon_matches_search(icon, search):
                continue
            visible.append(icon)
        if self.active_icon_filter == "Suggested" and suggested_subcategory and not visible:
            for icon in self.icons:
                if self._get_icon_family(icon["id"]) == suggested_family:
                    visible.append(icon)
        return visible

    def _item_matches_search(self, item, search):
        haystack = " ".join([item["id"], item["name"], item["type"], item["category"]]).lower()
        return search in haystack

    def _icon_matches_search(self, icon, search):
        metadata = self._get_icon_metadata(icon["id"])
        haystack = " ".join(
            [
                icon["id"],
                metadata.get("family", "uncategorized"),
                metadata.get("subcategory", "unknown"),
                *metadata.get("tags", []),
            ]
        ).lower()
        return search in haystack

    def _icon_matches_suggestion(self, icon, suggested_family, suggested_subcategory):
        if not suggested_family:
            return True
        metadata = self._get_icon_metadata(icon["id"])
        if metadata.get("family") != suggested_family:
            return False
        if not suggested_subcategory:
            return True
        return metadata.get("subcategory") == suggested_subcategory or suggested_subcategory in metadata.get("tags", [])

    def _guess_taxonomy_for_item(self, item):
        item_id = item["id"].lower()
        item_type = item["type"].lower()
        category = item["category"].lower()
        if category == "weapon":
            return "weapon", self._guess_weapon_subcategory(item_id)
        if category in {"armor", "helmet", "chest", "pants", "gloves", "boots"}:
            return "armor", category if category != "armor" else "chest"
        if category in {"ring", "amulet", "trinket", "accessory"}:
            return "accessory", category if category != "accessory" else "trinket"
        if item_type == "consumable":
            return "consumable", self._guess_consumable_subcategory(item_id)
        if item_type == "resource":
            monster_keywords = {"goblin", "ear", "fang", "claw", "hide", "bone"}
            if any(keyword in item_id for keyword in monster_keywords):
                return "monster_part", self._guess_monster_part_subcategory(item_id)
            return "material", self._guess_material_subcategory(item_id)
        if item_type == "quest":
            return "quest_item", "unknown"
        if "pickaxe" in item_id:
            return "profession_tool", "mining_pickaxe"
        if "fishing" in item_id:
            return "profession_tool", "fishing_rod"
        if "sickle" in item_id or "herb" in item_id:
            return "profession_tool", "herbalism_sickle"
        if "hammer" in item_id:
            return "profession_tool", "blacksmith_hammer"
        return None, None

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

    def _set_active_family(self, family):
        if family not in FAMILIES:
            return
        self.active_family = family
        subcategories = self._get_active_subcategories()
        if self.active_subcategory not in subcategories:
            self.active_subcategory = subcategories[0]
        self.status_message = f"Active taxonomy: {self.active_family}/{self.active_subcategory}"

    def _get_active_subcategories(self):
        return SUBCATEGORIES.get(self.active_family, ("unknown",))

    def _cycle_active_subcategory(self, direction):
        subcategories = self._get_active_subcategories()
        if not subcategories:
            self.active_subcategory = "unknown"
            return
        try:
            current_index = subcategories.index(self.active_subcategory)
        except ValueError:
            current_index = 0
        self.active_subcategory = subcategories[(current_index + direction) % len(subcategories)]
        self.status_message = f"Active subcategory: {self.active_subcategory}"

    def _guess_weapon_subcategory(self, item_id):
        for keyword in ("sword", "axe", "dagger", "bow", "staff", "mace", "spear", "shield", "wand"):
            if keyword in item_id:
                return keyword
        if "offhand" in item_id:
            return "offhand"
        return "sword"

    def _guess_consumable_subcategory(self, item_id):
        if "mana" in item_id:
            return "mana_potion"
        if "health" in item_id or "heal" in item_id or "potion" in item_id:
            return "health_potion"
        if "antidote" in item_id:
            return "antidote"
        if "elixir" in item_id:
            return "elixir"
        if "scroll" in item_id:
            return "scroll"
        if "drink" in item_id:
            return "drink"
        if "food" in item_id or "meal" in item_id:
            return "food"
        return "buff_potion"

    def _guess_monster_part_subcategory(self, item_id):
        if "goblin" in item_id:
            return "goblin_part"
        if "beast" in item_id:
            return "beast_part"
        if "insect" in item_id or "spider" in item_id:
            return "insect_part"
        if "undead" in item_id:
            return "undead_part"
        if "plant" in item_id:
            return "plant_monster_part"
        for keyword in ("fang", "claw", "eye", "ear", "bone", "hide"):
            if keyword in item_id:
                return keyword
        return "beast_part"

    def _guess_material_subcategory(self, item_id):
        for keyword in ("ore", "ingot", "wood", "stone", "herb", "plant", "cloth", "leather", "bone", "gem", "essence", "mushroom"):
            if keyword in item_id:
                return keyword
        return "wood"

    def _append_search_text(self, text="", backspace=False):
        if self.search_target == "icon":
            self.icon_search_text = self.icon_search_text[:-1] if backspace else self.icon_search_text + text
            self.icon_scroll = 0
        else:
            self.item_search_text = self.item_search_text[:-1] if backspace else self.item_search_text + text
            self.item_scroll = 0

    def _cycle_search_target(self, reset=False):
        self.search_target = "icon" if self.search_target == "item" else "item"
        if reset:
            if self.search_target == "icon":
                self.icon_search_text = ""
                self.icon_scroll = 0
            else:
                self.item_search_text = ""
                self.item_scroll = 0
        self.status_message = f"Search target: {self.search_target}"

    def _apply_active_taxonomy(self):
        target_indexes = self._get_target_icon_indexes()
        if not target_indexes:
            self.status_message = "Select an icon first"
            return
        tagged_count = 0
        for icon_index in target_indexes:
            if self._apply_taxonomy_to_icon(icon_index, update_status=False):
                tagged_count += 1
        self.status_message = f"Tagged {tagged_count} icons as {self.active_family}/{self.active_subcategory}"

    def _apply_taxonomy_to_icon(self, icon_index, update_status=True):
        if icon_index is None or icon_index < 0 or icon_index >= len(self.icons):
            return False
        icon = self.icons[icon_index]
        metadata = self._ensure_icon_metadata(icon["id"])
        metadata["family"] = self.active_family
        metadata["subcategory"] = self.active_subcategory
        self.dirty_tags = True
        if update_status:
            self.status_message = f"Painted {icon['id']} as {self.active_family}/{self.active_subcategory}"
        return True

    def _assign_selected_icon_category(self, category):
        icon = self._get_selected_icon()
        if icon is None:
            self.status_message = "Select an icon first"
            return
        metadata = self._ensure_icon_metadata(icon["id"])
        metadata["family"] = category
        metadata["subcategory"] = self._get_active_subcategories()[0]
        self.dirty_tags = True
        self.status_message = f"Tagged {icon['id']} as {category}"

    def _toggle_selected_icon_favorite(self):
        icon = self._get_selected_icon()
        if icon is None:
            self.status_message = "Select an icon first"
            return
        metadata = self._ensure_icon_metadata(icon["id"])
        metadata["favorite"] = not bool(metadata.get("favorite", False))
        self.dirty_tags = True
        state = "favorite" if metadata["favorite"] else "not favorite"
        self.status_message = f"Marked {icon['id']} as {state}"

    def _start_tag_input(self):
        icon = self._get_selected_icon()
        if icon is None:
            self.status_message = "Select an icon first"
            return
        metadata = self._get_icon_metadata(icon["id"])
        self.tag_input_text = ", ".join(metadata.get("tags", []))
        self.tag_input_active = True
        self.status_message = f"Editing tags for {icon['id']}"

    def _commit_tag_input(self):
        target_indexes = self._get_target_icon_indexes() if self.apply_tags_to_selection else {self.selected_icon_index}
        if not target_indexes:
            self.tag_input_active = False
            return
        tags = []
        for raw_tag in self.tag_input_text.split(","):
            tag = "_".join(raw_tag.strip().lower().split())
            if tag and tag not in tags:
                tags.append(tag)
        for icon_index in target_indexes:
            if icon_index is None or icon_index < 0 or icon_index >= len(self.icons):
                continue
            metadata = self._ensure_icon_metadata(self.icons[icon_index]["id"])
            metadata["tags"] = sorted(tags)
        self.dirty_tags = True
        self.tag_input_active = False
        self.tag_input_text = ""
        self.apply_tags_to_selection = False
        self.status_message = f"Saved tags for {len(target_indexes)} icon(s)"

    def _get_selected_icon(self):
        if self.selected_icon_index is None or self.selected_icon_index < 0 or self.selected_icon_index >= len(self.icons):
            return None
        return self.icons[self.selected_icon_index]

    def _get_target_icon_indexes(self):
        valid_indexes = {
            index
            for index in self.selected_icon_indexes
            if isinstance(index, int) and 0 <= index < len(self.icons)
        }
        if valid_indexes:
            return valid_indexes
        if self.selected_icon_index is not None and 0 <= self.selected_icon_index < len(self.icons):
            return {self.selected_icon_index}
        return set()

    def _get_icon_metadata(self, icon_id):
        metadata = self.icon_tags.get(icon_id, {})
        return self._normalize_icon_metadata(metadata)

    def _ensure_icon_metadata(self, icon_id):
        metadata = self._normalize_icon_metadata(self.icon_tags.get(icon_id, {}))
        self.icon_tags[icon_id] = metadata
        return metadata

    def _normalize_icon_metadata(self, metadata):
        metadata = metadata if isinstance(metadata, dict) else {}
        family = metadata.get("family", metadata.get("category", "uncategorized"))
        if family in {"weapons", "materials", "consumables", "accessories", "monster_parts"}:
            family = {
                "weapons": "weapon",
                "materials": "material",
                "consumables": "consumable",
                "accessories": "accessory",
                "monster_parts": "monster_part",
            }[family]
        if family not in FAMILIES and family != "uncategorized":
            family = "uncategorized"
        subcategory = metadata.get("subcategory", "unknown")
        if not subcategory:
            subcategory = "unknown"
        tags = metadata.get("tags", [])
        if not isinstance(tags, list):
            tags = []
        cleaned_tags = []
        for tag in tags:
            cleaned = "_".join(str(tag).strip().lower().split())
            if cleaned and cleaned not in cleaned_tags:
                cleaned_tags.append(cleaned)
        return {
            "family": family,
            "subcategory": str(subcategory),
            "tags": sorted(cleaned_tags),
            "favorite": bool(metadata.get("favorite", False)),
        }

    def _get_icon_family(self, icon_id):
        return self._get_icon_metadata(icon_id).get("family", "uncategorized")

    def _get_icon_subcategory(self, icon_id):
        return self._get_icon_metadata(icon_id).get("subcategory", "unknown")

    def _is_icon_favorite(self, icon_id):
        return bool(self._get_icon_metadata(icon_id).get("favorite", False))

    def _is_search_character(self, text):
        return len(text) == 1 and (text.isalnum() or text in {" ", "_", "-"})

    def _is_tag_character(self, text):
        return len(text) == 1 and (text.isalnum() or text in {" ", "_", "-", ","})

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
                    "auto_category": str(entry.get("category", "misc")),
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

    def _load_icon_tags(self):
        if not ICON_TAGS_PATH.exists():
            ICON_TAGS_PATH.parent.mkdir(parents=True, exist_ok=True)
            ICON_TAGS_PATH.write_text("{}\n", encoding="utf-8")
            return {}
        try:
            icon_tags = json.loads(ICON_TAGS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        if not isinstance(icon_tags, dict):
            return {}
        return {
            str(icon_id): self._normalize_icon_metadata(metadata)
            for icon_id, metadata in icon_tags.items()
            if icon_id
        }

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

    def _shorten_middle(self, text, max_length):
        text = str(text)
        if len(text) <= max_length:
            return text
        if max_length <= 3:
            return "." * max_length
        left_length = (max_length - 3) // 2
        right_length = max_length - 3 - left_length
        return f"{text[:left_length]}...{text[-right_length:]}"


if __name__ == "__main__":
    IconMapper().run()
