import pygame


PALETTE = {
    "sky_top": (18, 24, 32),
    "sky_bottom": (20, 42, 35),
    "forest_back": (18, 46, 37),
    "forest_front": (12, 28, 24),
    "ground": (17, 20, 22),
    "ground_light": (36, 41, 34),
    "panel": (37, 45, 54),
    "panel_dark": (27, 34, 42),
    "panel_light": (64, 73, 78),
    "border": (92, 82, 58),
    "border_light": (192, 172, 105),
    "text": (238, 232, 214),
    "muted": (174, 184, 174),
    "gold": (228, 188, 86),
    "xp": (112, 146, 205),
    "victory": (105, 198, 117),
    "defeat": (194, 82, 76),
    "level_up": (120, 217, 138),
    "button": (42, 58, 54),
    "button_border": (192, 172, 105),
    "shadow": (8, 10, 13),
}


class Button:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.text = text

    def draw(self, screen, font):
        pygame.draw.rect(screen, PALETTE["shadow"], self.rect.move(4, 4))
        pygame.draw.rect(screen, PALETTE["button"], self.rect)
        pygame.draw.rect(screen, PALETTE["button_border"], self.rect, 3)
        pygame.draw.rect(screen, PALETTE["panel_light"], self.rect.inflate(-10, -10), 1)

        label = font.render(self.text, True, PALETTE["text"])
        label_rect = label.get_rect(center=self.rect.center)
        screen.blit(label, label_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class ResultScreen:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.Font(None, 58)
        self.header_font = pygame.font.Font(None, 34)
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)
        self.continue_btn = Button((190, 530, 200, 50), "Continuer")
        self.discard_btn = Button((420, 530, 220, 50), "Abandonner le reste")
        self.loot_page = 0
        self.loot_items_per_page = 10
        self.loot_prev_btn = Button((0, 0, 28, 24), "<")
        self.loot_next_btn = Button((0, 0, 28, 24), ">")
        self.inventory_page = 0
        self.inventory_items_per_page = 24
        self.inventory_prev_btn = Button((0, 0, 28, 24), "<")
        self.inventory_next_btn = Button((0, 0, 28, 24), ">")
        self.loot_rows = []
        self.loot_cards = []
        self.loot_message = ""
        self.selected_pending_drop_index = None
        self.inventory_slot_rects = []
        self.replacement_mode = False
        self.icons = {
            "unknown": self._load_icon("assets/icons/item_unknown.png"),
            "equipment": self._load_icon("assets/icons/equipment.png"),
            "material": self._load_icon("assets/icons/material.png"),
            "consumable": self._load_icon("assets/icons/consumable.png"),
        }

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            result = self.game.last_combat_result or {}
            if self._has_pending_drops(result) and self.discard_btn.is_clicked(event.pos):
                if self.game.discard_pending_combat_loot():
                    self.replacement_mode = False
                    self.selected_pending_drop_index = None
                    self.loot_message = "Butin abandonné."
                    self.game.continue_after_combat_result()
                return

            if self.continue_btn.is_clicked(event.pos):
                if self._has_pending_drops(result):
                    if self.game.try_claim_all_combat_drops():
                        self.game.continue_after_combat_result()
                    else:
                        self.replacement_mode = True
                        self.loot_message = (
                            "Inventaire plein : libère une place."
                        )
                else:
                    self.game.continue_after_combat_result()
                return

            if event.button == 1:
                if self._handle_pagination_click(event.pos):
                    return

                if self.replacement_mode:
                    for slot_rect, slot_index, _slot in self.inventory_slot_rects:
                        if slot_rect.collidepoint(event.pos):
                            if self.selected_pending_drop_index is None:
                                moved = self.game.move_inventory_item_to_pending_loot(
                                    slot_index
                                )
                                if moved:
                                    self.loot_message = (
                                        "Objet déplacé vers le butin temporaire."
                                    )
                                else:
                                    self.loot_message = "Déplacement impossible."
                                return

                            replaced = self.game.replace_inventory_item_with_pending_drop(
                                self.selected_pending_drop_index,
                                slot_index,
                            )
                            if replaced:
                                self.selected_pending_drop_index = None
                                result = self.game.last_combat_result or {}
                                if self._has_pending_drops(result):
                                    self.loot_message = "Échange effectué."
                                else:
                                    self.replacement_mode = False
                                    self.loot_message = "Échange effectué."
                            else:
                                self.loot_message = "Déplacement impossible."
                            return

                for card_rect, drop_index, _drop in self.loot_cards:
                    if card_rect.collidepoint(event.pos):
                        if self.replacement_mode:
                            if self.game.try_claim_combat_drop(drop_index):
                                self.selected_pending_drop_index = None
                                self.loot_message = "Objet récupéré."
                                result = self.game.last_combat_result or {}
                                if not self._has_pending_drops(result):
                                    self.replacement_mode = False
                                self._clamp_pages(self._get_pending_drops(result))
                            else:
                                self.selected_pending_drop_index = drop_index
                                self.loot_message = (
                                    "Inventaire plein : choisis un slot à échanger."
                                )
                            return
                        if self.game.try_claim_combat_drop(drop_index):
                            self.loot_message = ""
                            result = self.game.last_combat_result or {}
                            self._clamp_pages(self._get_pending_drops(result))
                        else:
                            self.replacement_mode = True
                            self.selected_pending_drop_index = drop_index
                            self.loot_message = (
                                "Inventaire plein : libère une place."
                            )
                        return

    def draw(self, screen):
        self._draw_background(screen)

        combat = self.game.combat
        victory = combat is not None and combat.winner == "player"
        title_text = "Victoire !" if victory else "Défaite..."
        title_color = PALETTE["victory"] if victory else PALETTE["defeat"]

        result = self.game.last_combat_result or {}
        exp_gained = result.get("exp_gained", 0)
        gold_gained = result.get("gold_gained", 0)
        drops = self._get_pending_drops(result)
        current_level = self.game.player.get("level", 1) if self.game.player else 1
        self._clamp_pages(drops)
        self.continue_btn.text = (
            "Tout récupérer" if self._has_pending_drops(result) else "Continuer"
        )

        if self.replacement_mode:
            self._draw_replacement_layout(
                screen,
                result,
                drops,
                exp_gained,
                gold_gained,
                current_level,
                title_text,
                title_color,
            )
            return

        self._draw_title(screen, title_text, title_color)

        summary_rect = pygame.Rect(64, 138, 322, 318)
        loot_rect = pygame.Rect(414, 138, 322, 318)
        self._draw_panel(screen, summary_rect, "Résumé")
        self._draw_panel(screen, loot_rect, "Butin")

        y = summary_rect.y + 66
        y = self._draw_summary_line(screen, "XP gagnée", exp_gained, y, PALETTE["xp"])
        y = self._draw_summary_line(
            screen, "Gold gagné", gold_gained, y, PALETTE["gold"]
        )
        y = self._draw_summary_line(screen, "Niveau actuel", current_level, y)

        if result.get("leveled_up", False):
            y += 10
            y = self._draw_summary_line(
                screen, "Level up", "Oui", y, PALETTE["level_up"]
            )
            self._draw_summary_line(
                screen,
                "Nouveau niveau",
                result.get("new_level", current_level),
                y,
                PALETTE["level_up"],
            )

        self._draw_loot_section(screen, loot_rect, drops)
        self._draw_loot_tooltip(screen)
        self._draw_inventory_tooltip(screen)
        self._draw_loot_message(screen)
        self._draw_combat_report_mail(screen, result)
        self._draw_result_buttons(screen, result)

    def _draw_replacement_layout(
        self,
        screen,
        result,
        drops,
        exp_gained,
        gold_gained,
        current_level,
        title_text,
        title_color,
    ):
        self._draw_title(screen, title_text, title_color)

        subtitle = self.header_font.render("Inventaire plein", True, PALETTE["gold"])
        subtitle_rect = subtitle.get_rect(center=(400, 124))
        screen.blit(subtitle, subtitle_rect)

        self._draw_replacement_instructions(screen)

        self._draw_compact_summary(screen, exp_gained, gold_gained, current_level)

        loot_rect = pygame.Rect(42, 210, 328, 242)
        inventory_rect = pygame.Rect(400, 210, 358, 242)
        self._draw_panel(screen, loot_rect, "Butin temporaire")
        self._draw_panel(screen, inventory_rect, "Inventaire")

        self._draw_loot_section(screen, loot_rect, drops)
        self._draw_inventory_panel(screen, inventory_rect)
        self._draw_selection_feedback(screen)
        self._draw_loot_tooltip(screen)
        self._draw_inventory_tooltip(screen)
        self._draw_loot_message(screen)
        self._draw_result_buttons(screen, result)

    def _draw_compact_summary(self, screen, exp_gained, gold_gained, current_level):
        rect = pygame.Rect(220, 180, 360, 26)
        pygame.draw.rect(screen, PALETTE["panel_dark"], rect)
        pygame.draw.rect(screen, PALETTE["border"], rect, 1)

        summary = self.small_font.render(
            f"XP +{exp_gained}   Gold +{gold_gained}   Niveau {current_level}",
            True,
            PALETTE["text"],
        )
        summary_rect = summary.get_rect(center=rect.center)
        screen.blit(summary, summary_rect)

    def _draw_inventory_panel(self, screen, rect):
        self._draw_inventory_replacement_grid(screen, rect)

    def _draw_background(self, screen):
        for y in range(0, 600, 4):
            blend = y / 600
            color = (
                int(
                    PALETTE["sky_top"][0] * (1 - blend)
                    + PALETTE["sky_bottom"][0] * blend
                ),
                int(
                    PALETTE["sky_top"][1] * (1 - blend)
                    + PALETTE["sky_bottom"][1] * blend
                ),
                int(
                    PALETTE["sky_top"][2] * (1 - blend)
                    + PALETTE["sky_bottom"][2] * blend
                ),
            )
            pygame.draw.rect(screen, color, (0, y, 800, 4))

        moon_color = (216, 211, 172)
        pygame.draw.rect(screen, moon_color, (620, 48, 44, 44))
        pygame.draw.rect(screen, PALETTE["sky_top"], (610, 42, 22, 54))

        back_points = [(0, 354), (70, 286), (140, 354)]
        for x in range(-40, 840, 110):
            points = [(px + x, py) for px, py in back_points]
            pygame.draw.polygon(screen, PALETTE["forest_back"], points)
            pygame.draw.rect(screen, PALETTE["forest_back"], (x + 54, 320, 30, 96))

        front_points = [(0, 420), (52, 318), (104, 420)]
        for x in range(-30, 850, 86):
            points = [(px + x, py) for px, py in front_points]
            pygame.draw.polygon(screen, PALETTE["forest_front"], points)
            pygame.draw.rect(screen, PALETTE["forest_front"], (x + 43, 374, 18, 86))

        pygame.draw.rect(screen, PALETTE["ground"], (0, 430, 800, 170))
        pygame.draw.rect(screen, PALETTE["ground_light"], (0, 430, 800, 4))
        for x in range(0, 800, 24):
            pygame.draw.rect(screen, (12, 15, 15), (x, 468 + (x % 48), 16, 4))

    def _draw_title(self, screen, title_text, title_color):
        banner_rect = pygame.Rect(250, 36, 300, 72)
        pygame.draw.rect(screen, PALETTE["shadow"], banner_rect.move(4, 4))
        pygame.draw.rect(screen, PALETTE["panel_dark"], banner_rect)
        pygame.draw.rect(screen, PALETTE["border_light"], banner_rect, 3)

        shadow = self.title_font.render(title_text, True, PALETTE["shadow"])
        title = self.title_font.render(title_text, True, title_color)
        title_rect = title.get_rect(center=(400, 72))
        shadow_rect = shadow.get_rect(center=(403, 75))
        screen.blit(shadow, shadow_rect)
        screen.blit(title, title_rect)

    def _draw_panel(self, screen, rect, title):
        pygame.draw.rect(screen, PALETTE["shadow"], rect.move(5, 5))
        pygame.draw.rect(screen, PALETTE["panel"], rect)
        pygame.draw.rect(screen, PALETTE["border"], rect, 3)
        pygame.draw.rect(screen, PALETTE["panel_light"], rect.inflate(-14, -14), 1)
        pygame.draw.line(
            screen,
            PALETTE["border_light"],
            (rect.x + 10, rect.y + 10),
            (rect.right - 10, rect.y + 10),
            2,
        )

        title_bg = pygame.Rect(rect.x + 18, rect.y + 14, rect.width - 36, 34)
        pygame.draw.rect(screen, PALETTE["panel_dark"], title_bg)
        pygame.draw.rect(screen, PALETTE["border_light"], title_bg, 2)
        title_text = self.header_font.render(title, True, PALETTE["text"])
        screen.blit(title_text, (title_bg.x + 12, title_bg.y + 5))

    def _draw_button(self, screen, button):
        pygame.draw.rect(screen, PALETTE["shadow"], button.rect.move(4, 4))
        pygame.draw.rect(screen, PALETTE["button"], button.rect)
        pygame.draw.rect(screen, PALETTE["button_border"], button.rect, 3)
        pygame.draw.rect(
            screen, PALETTE["panel_light"], button.rect.inflate(-10, -10), 1
        )

        label = self.font.render(button.text, True, PALETTE["text"])
        label_rect = label.get_rect(center=button.rect.center)
        screen.blit(label, label_rect)

    def _draw_result_buttons(self, screen, result):
        if self._has_pending_drops(result):
            self.continue_btn.rect = pygame.Rect(150, 530, 220, 50)
            self.discard_btn.rect = pygame.Rect(420, 530, 240, 50)
            self._draw_button(screen, self.continue_btn)
            self._draw_button(screen, self.discard_btn)
            return

        self.continue_btn.rect = pygame.Rect(300, 530, 200, 50)
        self._draw_button(screen, self.continue_btn)

    def _draw_summary_line(self, screen, label, value, y, value_color=None):
        row_rect = pygame.Rect(92, y - 5, 250, 31)
        pygame.draw.rect(screen, PALETTE["panel_dark"], row_rect)
        pygame.draw.rect(screen, (58, 66, 66), row_rect, 1)
        label_text = self.font.render(f"{label} :", True, PALETTE["muted"])
        value_text = self.font.render(str(value), True, value_color or PALETTE["text"])
        screen.blit(label_text, (row_rect.x + 10, y))
        screen.blit(value_text, (row_rect.right - value_text.get_width() - 10, y))
        return y + 38

    def _draw_loot_section(self, screen, rect, drops):
        self.loot_rows = []
        self.loot_cards = []
        if drops:
            card_width = 48
            card_height = 48
            gap = 10
            columns = 5
            start_x = rect.x + 20
            start_y = rect.y + 72
            start_index = self.loot_page * self.loot_items_per_page
            visible_drops = drops[start_index:start_index + self.loot_items_per_page]

            for visible_index, drop in enumerate(visible_drops):
                real_drop_index = start_index + visible_index
                column = visible_index % columns
                row = visible_index // columns
                card_rect = pygame.Rect(
                    start_x + column * (card_width + gap),
                    start_y + row * (card_height + gap),
                    card_width,
                    card_height,
                )
                pygame.draw.rect(
                    screen,
                    PALETTE["panel_dark"],
                    card_rect,
                )
                pygame.draw.rect(screen, self._get_drop_color(drop), card_rect, 2)
                if real_drop_index == self.selected_pending_drop_index:
                    pygame.draw.rect(screen, PALETTE["border_light"], card_rect, 4)
                pygame.draw.rect(
                    screen, PALETTE["panel_light"], card_rect.inflate(-8, -8), 1
                )
                self.loot_cards.append((card_rect, real_drop_index, drop))
                self.loot_rows.append((card_rect, drop))

                icon = self._get_drop_icon(drop)
                icon_rect = pygame.Rect(0, 0, 32, 32)
                icon_rect.center = card_rect.center
                if icon is not None:
                    screen.blit(icon, icon_rect)
                else:
                    self._draw_icon_fallback(screen, icon_rect)

                if drop.get("kind") == "stackable" and drop.get("quantity", 1) > 1:
                    quantity_text = self.small_font.render(
                        f"x{drop.get('quantity', 1)}", True, PALETTE["text"]
                    )
                    badge_rect = pygame.Rect(
                        card_rect.right - quantity_text.get_width() - 8,
                        card_rect.bottom - 18,
                        quantity_text.get_width() + 6,
                        16,
                    )
                    pygame.draw.rect(screen, PALETTE["shadow"], badge_rect)
                    pygame.draw.rect(screen, PALETTE["border"], badge_rect, 1)
                    screen.blit(quantity_text, (badge_rect.x + 3, badge_rect.y + 1))
        else:
            y = rect.y + 72
            row_rect = pygame.Rect(rect.x + 20, y - 4, rect.width - 40, 42)
            pygame.draw.rect(screen, PALETTE["panel_dark"], row_rect)
            pygame.draw.rect(screen, (70, 66, 70), row_rect, 1)
            message = (
                "Tout le butin est récupéré."
                if self.replacement_mode
                else "Aucun loot"
            )
            no_loot_text = self.font.render(message, True, PALETTE["muted"])
            screen.blit(no_loot_text, (row_rect.x + 10, row_rect.y + 10))

        self._draw_page_controls(
            screen,
            rect,
            len(drops),
            self.loot_page,
            self.loot_items_per_page,
            self.loot_prev_btn,
            self.loot_next_btn,
        )

    def _draw_inventory_replacement_grid(self, screen, rect):
        self.inventory_slot_rects = []
        if self.game.player is None:
            return

        inventory = self.game.player.get("inventory", {})
        slots = inventory.get("slots", [])
        if not isinstance(slots, list):
            return

        slot_size = 30
        gap = 4
        columns = 6
        start_x = rect.x + 24
        start_y = rect.y + 68
        mouse_pos = pygame.mouse.get_pos()
        start_index = self.inventory_page * self.inventory_items_per_page
        visible_slots = slots[start_index:start_index + self.inventory_items_per_page]

        for visible_index, slot in enumerate(visible_slots):
            real_slot_index = start_index + visible_index
            column = visible_index % columns
            row = visible_index // columns
            slot_rect = pygame.Rect(
                start_x + column * (slot_size + gap),
                start_y + row * (slot_size + gap),
                slot_size,
                slot_size,
            )
            pygame.draw.rect(screen, PALETTE["panel_dark"], slot_rect)
            pygame.draw.rect(screen, PALETTE["border"], slot_rect, 1)
            self.inventory_slot_rects.append((slot_rect, real_slot_index, slot))

            if slot is None:
                if (
                    self.selected_pending_drop_index is not None
                    and slot_rect.collidepoint(mouse_pos)
                ):
                    pygame.draw.rect(screen, PALETTE["gold"], slot_rect, 3)
                continue

            icon = self._get_slot_icon(slot)
            icon_rect = pygame.Rect(0, 0, 24, 24)
            icon_rect.center = slot_rect.center
            if icon is not None:
                screen.blit(pygame.transform.scale(icon, (24, 24)), icon_rect)
            else:
                self._draw_small_icon_fallback(screen, icon_rect)

            if slot_rect.collidepoint(mouse_pos):
                if self.selected_pending_drop_index is not None:
                    pygame.draw.rect(screen, PALETTE["gold"], slot_rect, 3)
                elif slot is not None:
                    pygame.draw.rect(screen, PALETTE["level_up"], slot_rect, 3)

        self._draw_page_controls(
            screen,
            rect,
            len(slots),
            self.inventory_page,
            self.inventory_items_per_page,
            self.inventory_prev_btn,
            self.inventory_next_btn,
        )

    def _draw_replacement_instructions(self, screen):
        rect = pygame.Rect(128, 136, 544, 42)
        pygame.draw.rect(screen, PALETTE["shadow"], rect.move(3, 3))
        pygame.draw.rect(screen, PALETTE["panel_dark"], rect)
        pygame.draw.rect(screen, PALETTE["border"], rect, 1)

        lines = [
            "Clique un butin pour le récupérer.",
            "Clique un item d'inventaire pour libérer une place.",
        ]
        y = rect.y + 5
        for line in lines:
            text = self.small_font.render(line, True, PALETTE["muted"])
            text_rect = text.get_rect(center=(400, y))
            screen.blit(text, text_rect)
            y += 20

    def _draw_selection_feedback(self, screen):
        if self.selected_pending_drop_index is None:
            message = "Clique un item de l'inventaire pour l'envoyer vers le butin."
            color = PALETTE["muted"]
        else:
            message = "Butin sélectionné : choisis un slot d'inventaire."
            color = PALETTE["gold"]
            arrow = self.small_font.render("Butin -> Inventaire", True, PALETTE["gold"])
            arrow_rect = arrow.get_rect(center=(385, 330))
            screen.blit(arrow, arrow_rect)

        rect = pygame.Rect(176, 456, 448, 28)
        pygame.draw.rect(screen, PALETTE["panel_dark"], rect)
        pygame.draw.rect(screen, PALETTE["border"], rect, 1)
        text = self.small_font.render(message, True, color)
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)

    def _get_page_count(self, item_count, items_per_page):
        if item_count <= 0:
            return 1
        return max(1, (item_count + items_per_page - 1) // items_per_page)

    def _clamp_pages(self, drops):
        loot_page_count = self._get_page_count(len(drops), self.loot_items_per_page)
        self.loot_page = max(0, min(self.loot_page, loot_page_count - 1))

        if self.game.player is None:
            self.inventory_page = 0
            return

        inventory = self.game.player.get("inventory", {})
        slots = inventory.get("slots", [])
        slot_count = len(slots) if isinstance(slots, list) else 0
        inventory_page_count = self._get_page_count(
            slot_count,
            self.inventory_items_per_page,
        )
        self.inventory_page = max(0, min(self.inventory_page, inventory_page_count - 1))

    def _handle_pagination_click(self, pos):
        result = self.game.last_combat_result or {}
        drops = self._get_pending_drops(result)
        loot_page_count = self._get_page_count(len(drops), self.loot_items_per_page)
        if loot_page_count > 1:
            if self.loot_prev_btn.is_clicked(pos):
                self.loot_page = max(0, self.loot_page - 1)
                return True
            if self.loot_next_btn.is_clicked(pos):
                self.loot_page = min(loot_page_count - 1, self.loot_page + 1)
                return True

        if self.replacement_mode:
            slot_count = 0
            if self.game.player is not None:
                inventory = self.game.player.get("inventory", {})
                slots = inventory.get("slots", [])
                if isinstance(slots, list):
                    slot_count = len(slots)
            inventory_page_count = self._get_page_count(
                slot_count,
                self.inventory_items_per_page,
            )
            if inventory_page_count > 1:
                if self.inventory_prev_btn.is_clicked(pos):
                    self.inventory_page = max(0, self.inventory_page - 1)
                    return True
                if self.inventory_next_btn.is_clicked(pos):
                    self.inventory_page = min(
                        inventory_page_count - 1,
                        self.inventory_page + 1,
                    )
                    return True

        return False

    def _draw_page_controls(
        self,
        screen,
        rect,
        item_count,
        current_page,
        items_per_page,
        prev_btn,
        next_btn,
    ):
        page_count = self._get_page_count(item_count, items_per_page)
        if page_count <= 1:
            return

        prev_btn.rect = pygame.Rect(rect.right - 104, rect.y + 16, 28, 24)
        next_btn.rect = pygame.Rect(rect.right - 34, rect.y + 16, 28, 24)
        page_text = self.small_font.render(
            f"{current_page + 1}/{page_count}", True, PALETTE["muted"]
        )
        page_rect = page_text.get_rect(center=(rect.right - 55, rect.y + 28))

        self._draw_button(screen, prev_btn)
        screen.blit(page_text, page_rect)
        self._draw_button(screen, next_btn)

    def _draw_inventory_tooltip(self, screen):
        if not self.replacement_mode:
            return

        mouse_pos = pygame.mouse.get_pos()
        hovered_slot = None
        for slot_rect, _slot_index, slot in self.inventory_slot_rects:
            if slot is not None and slot_rect.collidepoint(mouse_pos):
                hovered_slot = slot
                break

        if hovered_slot is None:
            return

        self._draw_tooltip(screen, self._get_slot_tooltip_lines(hovered_slot), mouse_pos)

    def _draw_loot_tooltip(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        hovered_drop = None
        for card_rect, _drop_index, drop in self.loot_cards:
            if card_rect.collidepoint(mouse_pos):
                hovered_drop = drop
                break

        if hovered_drop is None:
            return

        self._draw_tooltip(screen, self._get_drop_tooltip_lines(hovered_drop), mouse_pos)

    def _draw_tooltip(self, screen, lines, mouse_pos):
        rendered_lines = [
            self.small_font.render(line, True, self._get_tooltip_line_color(index))
            for index, line in enumerate(lines)
        ]
        width = max(line.get_width() for line in rendered_lines) + 24
        height = len(rendered_lines) * 22 + 18

        x = mouse_pos[0] + 16
        y = mouse_pos[1] + 16
        if x + width > 790:
            x = 790 - width
        if y + height > 590:
            y = 590 - height
        x = max(10, x)
        y = max(10, y)

        tooltip_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, PALETTE["shadow"], tooltip_rect.move(4, 4))
        pygame.draw.rect(screen, PALETTE["panel_dark"], tooltip_rect)
        pygame.draw.rect(screen, PALETTE["border_light"], tooltip_rect, 2)
        pygame.draw.rect(screen, PALETTE["panel_light"], tooltip_rect.inflate(-8, -8), 1)

        line_y = tooltip_rect.y + 10
        for line in rendered_lines:
            screen.blit(line, (tooltip_rect.x + 12, line_y))
            line_y += 22

    def _draw_loot_message(self, screen):
        if not self.loot_message:
            return

        color = (
            PALETTE["defeat"]
            if "impossible" in self.loot_message or "plein" in self.loot_message
            else PALETTE["level_up"]
        )
        message = self.small_font.render(self.loot_message, True, color)
        center = (400, 488) if self.replacement_mode else (575, 430)
        message_rect = message.get_rect(center=center)
        screen.blit(message, message_rect)

    def _get_pending_drops(self, result):
        inventory_result = result.get("inventory_result", {})
        if isinstance(inventory_result, dict) and "pending" in inventory_result:
            return inventory_result.get("pending", [])
        return result.get("drops", [])

    def _has_pending_drops(self, result):
        inventory_result = result.get("inventory_result", {})
        if not isinstance(inventory_result, dict):
            return False

        pending = inventory_result.get("pending", [])
        return isinstance(pending, list) and len(pending) > 0

    def _load_icon(self, path):
        try:
            icon = pygame.image.load(path).convert_alpha()
        except (pygame.error, FileNotFoundError, OSError):
            return None
        return pygame.transform.scale(icon, (32, 32))

    def _get_drop_icon(self, drop):
        item_id = drop["item"]
        item_data = self.game.data.items.get(item_id, {})
        item_type = item_data.get("type", "")
        if not item_type:
            item_type = item_data.get("category", "")
        item_type = str(item_type).lower()

        if item_type == "equipment":
            return self.icons.get("equipment")
        if item_type == "consumable":
            return self.icons.get("consumable")
        if item_type in ("material", "resource"):
            return self.icons.get("material")
        return self.icons.get("unknown")

    def _get_slot_icon(self, slot):
        if slot is None:
            return None
        return self._get_drop_icon({"item": slot.get("item", "")})

    def _draw_icon_fallback(self, screen, rect):
        pygame.draw.rect(screen, PALETTE["panel"], rect)
        pygame.draw.rect(screen, PALETTE["border_light"], rect, 2)
        question = self.font.render("?", True, PALETTE["text"])
        question_rect = question.get_rect(center=rect.center)
        screen.blit(question, question_rect)

    def _draw_small_icon_fallback(self, screen, rect):
        pygame.draw.rect(screen, PALETTE["panel"], rect)
        pygame.draw.rect(screen, PALETTE["border_light"], rect, 1)
        question = self.small_font.render("?", True, PALETTE["text"])
        question_rect = question.get_rect(center=rect.center)
        screen.blit(question, question_rect)

    def _format_drop_short(self, drop):
        item_id = drop["item"]
        item_data = self.game.data.items.get(item_id, {})
        item_name = item_data.get("name", item_id)
        kind = drop.get("kind")

        if kind == "stackable":
            return f"- {item_name} x {drop.get('quantity', 1)}"

        if kind == "unique":
            rarity = self._get_rarity_label(drop)
            display_name = f"[{rarity}] {item_name}" if rarity else item_name
            return f"- {display_name}"

        return f"- {item_name}"

    def _short_text(self, text, max_length):
        if len(text) <= max_length:
            return text
        if max_length <= 3:
            return "." * max_length
        return f"{text[:max_length - 3]}..."

    def _get_drop_tooltip_lines(self, drop):
        item_id = drop["item"]
        item_data = self.game.data.items.get(item_id, {})
        item_name = item_data.get("name", item_id)
        lines = [item_name]

        kind = drop.get("kind")
        if kind:
            lines.append(f"Type: {kind}")
        if "quantity" in drop:
            lines.append(f"Quantity: {drop.get('quantity')}")

        rarity = self._get_rarity_label(drop)
        if rarity:
            lines.append(f"Rarity: {rarity}")

        stats_text = self._format_stats(drop.get("stats", {}))
        if stats_text:
            lines.append(f"Stats: {stats_text}")

        if len(lines) == 1:
            lines.append(self._format_drop(drop))
        return lines

    def _get_slot_tooltip_lines(self, slot):
        item_id = slot.get("item", "")
        item_data = self.game.data.items.get(item_id, {})
        item_name = item_data.get("name", item_id)
        lines = [item_name]

        kind = slot.get("kind")
        if kind:
            lines.append(f"Type: {kind}")
        if "quantity" in slot:
            lines.append(f"Quantity: {slot.get('quantity')}")

        rarity = self._get_rarity_label(slot)
        if rarity:
            lines.append(f"Rarity: {rarity}")

        stats_text = self._format_stats(slot.get("stats", {}))
        if stats_text:
            lines.append(f"Stats: {stats_text}")
        return lines

    def _get_tooltip_line_color(self, index):
        if index == 0:
            return PALETTE["text"]
        return PALETTE["muted"]

    def _draw_combat_report_mail(self, screen, result):
        mail = result.get("combat_report_mail")
        if not mail:
            return

        text = self.small_font.render(
            "Rapport archivé dans la boîte aux lettres", True, PALETTE["muted"]
        )
        text_rect = text.get_rect(center=(400, 490))
        screen.blit(text, text_rect)

    def _format_drop(self, drop):
        item_id = drop["item"]
        item_data = self.game.data.items.get(item_id, {})
        item_name = item_data.get("name", item_id)
        kind = drop.get("kind")

        if kind == "stackable":
            return f"- {item_name} x {drop.get('quantity', 1)}"

        if kind == "unique":
            rarity = self._get_rarity_label(drop)
            display_name = f"[{rarity}] {item_name}" if rarity else item_name
            stats_text = self._format_stats(drop.get("stats", {}))
            if stats_text:
                return f"- {display_name} ({stats_text})"
            return f"- {display_name}"

        return f"- {item_name}"

    def _get_rarity_label(self, drop):
        if drop is None:
            return ""
        rarity = drop.get("rarity")
        if not rarity:
            return ""
        return rarity.capitalize()

    def _get_rarity_color(self, drop):
        if drop is None:
            return (200, 200, 200)
        colors = {
            "common": (170, 170, 170),
            "uncommon": (100, 220, 120),
            "rare": (100, 160, 255),
            "epic": (180, 120, 255),
            "legendary": (255, 200, 80),
            "unique": (240, 90, 90),
        }
        return colors.get(drop.get("rarity"), (200, 200, 200))

    def _get_drop_color(self, drop):
        if drop.get("kind") == "unique":
            return self._get_rarity_color(drop)
        return (200, 200, 200)

    def _format_stats(self, stats):
        parts = []
        for stat, value in stats.items():
            parts.append(f"{self._get_stat_label(stat)} +{value}")
        return ", ".join(parts)

    def _get_stat_label(self, stat):
        labels = {
            "attack": "Attack",
            "defense": "Defense",
            "hp": "HP",
            "max_hp": "Max HP",
            "force": "Strength",
            "agility": "Agility",
            "intelligence": "Intelligence",
        }
        return labels.get(stat, stat)
