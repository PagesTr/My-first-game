import pygame


class DungeonButton:
    def __init__(self, rect, label, enabled=True):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.enabled = enabled

    def draw(self, screen, font):
        bg = (58, 68, 78) if self.enabled else (45, 45, 50)
        border = (210, 220, 225) if self.enabled else (95, 95, 100)
        text_color = (245, 245, 245) if self.enabled else (145, 145, 150)
        pygame.draw.rect(screen, bg, self.rect, border_radius=6)
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=6)
        text = font.render(self._truncate(self.label, font, self.rect.w - 24), True, text_color)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)

    def is_clicked(self, pos):
        return self.enabled and self.rect.collidepoint(pos)

    def _truncate(self, text, font, max_width):
        text = str(text or "")
        if max_width <= 0:
            return ""
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        if font.size(ellipsis)[0] > max_width:
            return ""
        while text and font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]
        return text + ellipsis if text else ellipsis


class DungeonScreen:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.Font(None, 46)
        self.option_font = pygame.font.Font(None, 30)
        self.body_font = pygame.font.Font(None, 22)
        self.back_button = DungeonButton((560, 54, 160, 46), "Back to Town")
        self.continue_button = DungeonButton((80, 470, 200, 50), "Continue Combat")
        self.heal_button = DungeonButton((80, 470, 140, 50), "Heal")
        self.loot_button = DungeonButton((230, 470, 140, 50), "Loot")
        self.equipment_button = DungeonButton((380, 470, 160, 50), "Equipment")
        self.boss_button = DungeonButton((80, 470, 200, 50), "Fight Boss")
        self.last_result = None

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        pos = event.pos
        if self.back_button.is_clicked(pos):
            if not isinstance(getattr(self.game, "active_dungeon", None), dict):
                self.game.last_dungeon_result = None
            self.game.active_dungeon = None
            self.game.state = "town"
            return

        step = self._get_current_step()
        if not isinstance(step, dict):
            return

        step_type = step.get("type")
        if step_type == "combat" and self.continue_button.is_clicked(pos):
            self.last_result = self.game.resolve_dungeon_combat_step()
            return

        if step_type == "rest_choice":
            if self.heal_button.is_clicked(pos):
                self.last_result = self.game.apply_dungeon_rest_choice("heal")
                return
            if self.loot_button.is_clicked(pos):
                self.last_result = self.game.apply_dungeon_rest_choice("loot")
                return
            if self.equipment_button.is_clicked(pos):
                self.last_result = {
                    "message": "Equipment opened. Inventory Back returns later.",
                }
                if hasattr(self.game, "open_inventory_from_dungeon"):
                    self.game.open_inventory_from_dungeon()
                return

        if step_type == "boss_loop" and self.boss_button.is_clicked(pos):
            self.last_result = self.game.resolve_dungeon_boss_step()

    def draw(self, screen):
        screen.fill((18, 24, 30))
        title = self.title_font.render("Dungeon", True, (245, 245, 245))
        screen.blit(title, (80, 54))
        self.back_button.draw(screen, self.body_font)

        summary = self.game.get_active_dungeon_summary() if hasattr(
            self.game,
            "get_active_dungeon_summary",
        ) else {"active": False}

        if not summary.get("active"):
            result = self.game.get_last_dungeon_result() if hasattr(
                self.game,
                "get_last_dungeon_result",
            ) else getattr(self.game, "last_dungeon_result", None)
            if isinstance(result, dict):
                self._draw_dungeon_summary(screen, result)
                return

        self._draw_summary_panel(screen, summary)
        self._draw_route_panel(screen, summary)
        self._draw_result_panel(screen)
        self._draw_action_buttons(screen, summary)

    def _draw_dungeon_summary(self, screen, result):
        title = self.title_font.render("Dungeon Summary", True, (245, 245, 245))
        screen.blit(title, (80, 112))

        rect = pygame.Rect(80, 170, 640, 330)
        self._draw_panel(screen, rect, self._get_dungeon_name(result.get("dungeon_id")))
        lines = [
            "Result: Defeated" if result.get("won") is False else "Result: Completed",
            f"Defeated by: {self._get_enemy_name(result.get('defeated_by'))}",
            f"Rooms cleared: {result.get('rooms_cleared', 0)}",
            f"Boss victories: {result.get('boss_victories', 0)}",
            f"Rest choice: {self._format_rest_choice(result.get('rest_choice'))}",
            f"XP gained: {result.get('total_exp', 0)}",
            f"Gold gained: {result.get('total_gold', 0)}",
        ]
        y = rect.y + 48
        for line in lines:
            text = self.body_font.render(
                self._truncate_text(line, self.body_font, 290),
                True,
                (210, 220, 205),
            )
            screen.blit(text, (rect.x + 18, y))
            y += 24

        loot_title = self.body_font.render("Loot added:", True, (245, 245, 245))
        screen.blit(loot_title, (rect.x + 340, rect.y + 48))
        loot_y = rect.y + 74
        for line in self._format_loot_lines(result.get("loot", []))[:4]:
            text = self.body_font.render(
                self._truncate_text(f"- {line}", self.body_font, 250),
                True,
                (190, 200, 210),
            )
            screen.blit(text, (rect.x + 340, loot_y))
            loot_y += 24

        pending_loot = result.get("pending_loot", [])
        if isinstance(pending_loot, list) and pending_loot:
            pending_title = self.body_font.render(
                "Inventory full - pending loot:",
                True,
                (245, 180, 105),
            )
            screen.blit(pending_title, (rect.x + 340, loot_y + 8))
            loot_y += 34
            for line in self._format_loot_lines(pending_loot)[:6]:
                text = self.body_font.render(
                    self._truncate_text(f"- {line}", self.body_font, 250),
                    True,
                    (225, 190, 135),
                )
                screen.blit(text, (rect.x + 340, loot_y))
                loot_y += 22

    def _draw_summary_panel(self, screen, summary):
        rect = pygame.Rect(80, 120, 310, 180)
        self._draw_panel(screen, rect, "Current Run")
        if not summary.get("active"):
            text = self.body_font.render("No active dungeon", True, (150, 155, 160))
            screen.blit(text, (rect.x + 16, rect.y + 52))
            return

        step = summary.get("step") or {}
        lines = [
            summary.get("dungeon_name", "Dungeon"),
            f"Room: {self._format_step_label(step)}",
            f"Step: {summary.get('step_index', 0) + 1}",
            f"Boss victories: {summary.get('boss_victories', 0)}",
        ]
        if step.get("type") == "boss_loop":
            lines.append(f"Boss multiplier: {self._get_boss_multiplier(summary):.2f}x")
        if summary.get("failed"):
            lines.append("Failed")
        elif summary.get("completed"):
            lines.append("Completed")

        y = rect.y + 46
        for line in lines[:6]:
            text = self.body_font.render(
                self._truncate_text(line, self.body_font, rect.w - 32),
                True,
                (210, 220, 205),
            )
            screen.blit(text, (rect.x + 16, y))
            y += 24

    def _draw_route_panel(self, screen, summary):
        rect = pygame.Rect(420, 120, 300, 180)
        self._draw_panel(screen, rect, "Route")
        dungeon = self._get_active_dungeon_data(summary)
        route = dungeon.get("route", []) if isinstance(dungeon, dict) else []
        current_index = summary.get("step_index", 0)
        if not route:
            text = self.body_font.render("No route", True, (150, 155, 160))
            screen.blit(text, (rect.x + 16, rect.y + 52))
            return

        y = rect.y + 44
        for index, step in enumerate(route[:6]):
            marker = ">" if index == current_index else " "
            label = f"{marker} {index + 1}. {self._format_step_label(step)}"
            text = self.body_font.render(
                self._truncate_text(label, self.body_font, rect.w - 32),
                True,
                (235, 225, 150) if index == current_index else (190, 200, 205),
            )
            screen.blit(text, (rect.x + 16, y))
            y += 22

    def _draw_result_panel(self, screen):
        rect = pygame.Rect(80, 328, 640, 112)
        self._draw_panel(screen, rect, "Log")
        lines = self._format_result_lines(self.last_result)
        if not lines:
            lines = ["Choose an action to advance the dungeon."]
        y = rect.y + 42
        for line in lines[:3]:
            text = self.body_font.render(
                self._truncate_text(line, self.body_font, rect.w - 32),
                True,
                (205, 215, 205),
            )
            screen.blit(text, (rect.x + 16, y))
            y += 24

    def _draw_action_buttons(self, screen, summary):
        step = summary.get("step") if isinstance(summary, dict) else None
        if not isinstance(step, dict):
            return

        step_type = step.get("type")
        if step_type == "combat":
            self.continue_button.enabled = True
            self.continue_button.draw(screen, self.option_font)
        elif step_type == "rest_choice":
            self.heal_button.enabled = True
            self.loot_button.enabled = True
            self.equipment_button.enabled = True
            self.heal_button.draw(screen, self.option_font)
            self.loot_button.draw(screen, self.option_font)
            self.equipment_button.draw(screen, self.option_font)
        elif step_type == "boss_loop":
            self.boss_button.enabled = True
            self.boss_button.draw(screen, self.option_font)

    def _get_current_step(self):
        if not hasattr(self.game, "get_active_dungeon_step"):
            return None
        return self.game.get_active_dungeon_step()

    def _draw_panel(self, screen, rect, title):
        pygame.draw.rect(screen, (35, 40, 48), rect, border_radius=6)
        pygame.draw.rect(screen, (120, 130, 140), rect, 2, border_radius=6)
        text = self.option_font.render(title, True, (245, 245, 245))
        screen.blit(text, (rect.x + 16, rect.y + 12))

    def _format_step_label(self, step):
        if not isinstance(step, dict):
            return "Unknown"
        step_type = step.get("type")
        if step_type == "combat":
            enemy_id = step.get("enemy_id")
            enemy = self.game.data.enemies.get(enemy_id, {})
            return f"Combat - {enemy.get('name', enemy_id)}"
        if step_type == "rest_choice":
            return "Preparation"
        if step_type == "boss_loop":
            enemy_id = step.get("enemy_id")
            enemy = self.game.data.enemies.get(enemy_id, {})
            return f"Boss Loop - {enemy.get('name', enemy_id)}"
        return str(step_type or "Unknown").replace("_", " ").title()

    def _format_result_lines(self, result):
        if not isinstance(result, dict):
            return []
        if result.get("message"):
            return [result["message"]]
        if result.get("applied") is True:
            if result.get("choice") == "heal":
                return [f"Healed {result.get('healed', 0)} HP."]
            if result.get("choice") == "loot":
                return ["Loot focus selected. Bonus will be handled later."]
        if result.get("resolved") is True:
            if result.get("won") is True:
                lines = [
                    f"Won against {result.get('enemy_name', result.get('enemy_id', 'enemy'))}.",
                    f"+{result.get('exp', 0)} XP, +{result.get('gold', 0)} gold",
                ]
                if "boss_victories" in result:
                    lines.append(f"Boss victories: {result.get('boss_victories', 0)}")
                return lines
            return [
                f"Defeated by {result.get('enemy_name', result.get('enemy_id', 'enemy'))}.",
                "Dungeon ended.",
            ]
        if result.get("reason"):
            return [str(result.get("reason")).replace("_", " ").title()]
        return []

    def _format_loot_lines(self, loot):
        if not isinstance(loot, list) or not loot:
            return ["No loot found"]
        quantities_by_item = {}
        for drop in loot:
            if not isinstance(drop, dict):
                continue
            item_id = drop.get("item")
            if not item_id:
                continue
            quantity = int(drop.get("quantity", 1))
            quantities_by_item[item_id] = quantities_by_item.get(item_id, 0) + quantity
        if not quantities_by_item:
            return ["No loot found"]
        return [
            f"{self._get_item_name(item_id)} x{quantity}"
            for item_id, quantity in quantities_by_item.items()
        ]

    def _get_dungeon_name(self, dungeon_id):
        dungeons = getattr(self.game.data, "dungeons", {}) or {}
        dungeon = dungeons.get(dungeon_id, {}) if isinstance(dungeons, dict) else {}
        return dungeon.get("name", dungeon_id or "Dungeon")

    def _get_enemy_name(self, enemy_id):
        enemies = getattr(self.game.data, "enemies", {}) or {}
        enemy = enemies.get(enemy_id, {}) if isinstance(enemies, dict) else {}
        return enemy.get("name", enemy_id or "Unknown")

    def _get_item_name(self, item_id):
        items = getattr(self.game.data, "items", {}) or {}
        item = items.get(item_id, {}) if isinstance(items, dict) else {}
        return item.get("name", item_id or "Unknown item")

    def _format_rest_choice(self, choice):
        if not choice:
            return "None"
        return str(choice).replace("_", " ").title()

    def _get_boss_multiplier(self, summary):
        dungeon = self._get_active_dungeon_data(summary)
        victories = summary.get("boss_victories", 0)
        scaling_rate = dungeon.get("scaling_rate", 0) if isinstance(dungeon, dict) else 0
        return 1.0 + victories * scaling_rate

    def _get_active_dungeon_data(self, summary):
        dungeon_id = summary.get("dungeon_id") if isinstance(summary, dict) else None
        dungeons = getattr(self.game.data, "dungeons", {}) or {}
        dungeon = dungeons.get(dungeon_id, {}) if isinstance(dungeons, dict) else {}
        return dungeon if isinstance(dungeon, dict) else {}

    def _truncate_text(self, text, font, max_width):
        text = str(text or "")
        if max_width <= 0:
            return ""
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        if font.size(ellipsis)[0] > max_width:
            return ""
        while text and font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]
        return text + ellipsis if text else ellipsis
