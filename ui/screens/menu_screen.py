import pygame

try:
    from systems.crafting import can_craft_recipe
except ImportError:
    from systems.crafting import can_craft as can_craft_recipe

from systems.professions import get_profession_mastery
from systems.active_gathering import format_tick_rate
from ui.assets import draw_background, load_image


REGION_LABELS = {
    "forest": "Forest",
    "caves": "Caves",
    "mountains": "Mountains",
}


class MenuButton:
    def __init__(self, rect, title, subtitle="", enabled=True):
        self.rect = pygame.Rect(rect)
        self.title = title
        self.subtitle = subtitle
        self.enabled = enabled

    def draw(self, screen, title_font, body_font):
        bg = (58, 68, 78) if self.enabled else (45, 45, 50)
        border = (210, 220, 225) if self.enabled else (95, 95, 100)
        text_color = (245, 245, 245) if self.enabled else (145, 145, 150)
        sub_color = (190, 200, 205) if self.enabled else (120, 120, 125)

        pygame.draw.rect(screen, bg, self.rect, border_radius=6)
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=6)

        title_y = self.rect.y + (9 if self.rect.h <= 58 and self.subtitle else 14)
        subtitle_y = self.rect.y + (31 if self.rect.h <= 58 else 48)

        title = self._render_fitted_text(title_font, self.title, text_color)
        screen.blit(title, (self.rect.x + 16, title_y))

        if self.subtitle:
            subtitle = self._render_fitted_text(body_font, self.subtitle, sub_color)
            screen.blit(subtitle, (self.rect.x + 16, subtitle_y))

    def is_clicked(self, pos):
        return self.enabled and self.rect.collidepoint(pos)

    def _render_fitted_text(self, font, text, color):
        max_width = max(20, self.rect.w - 32)
        text = str(text)
        if font.size(text)[0] <= max_width:
            return font.render(text, True, color)

        ellipsis = "..."
        while text and font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]
        return font.render(text + ellipsis, True, color)


class MenuScreen:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.Font(None, 46)
        self.option_font = pygame.font.Font(None, 30)
        self.body_font = pygame.font.Font(None, 24)
        self.town_background = load_image("assets/backgrounds/town.png", (800, 600))
        self.zone_background = load_image(
            "assets/backgrounds/zone_select.png", (800, 600)
        )
        self.class_background = load_image(
            "assets/backgrounds/class_select.png", (800, 600)
        )

        self.class_buttons = self._build_class_buttons()
        self.zone_buttons = self._build_zone_buttons()
        self.expedition_button = MenuButton(
            (80, 150, 300, 72),
            "Expedition",
            "Choose a combat zone",
        )
        self.inventory_button = MenuButton(
            (80, 238, 300, 72),
            "Inventory",
            "Manage gear and items",
        )
        self.merchant_button = MenuButton(
            (80, 326, 300, 72),
            "Merchant",
            "Sell items",
        )
        self.crafting_button = MenuButton(
            (80, 414, 300, 72),
            "Craft",
            "Use resources",
        )
        self.skills_button = MenuButton(
            (80, 502, 300, 72),
            "Skills",
            "Learn and equip skills",
        )
        self.mailbox_button = MenuButton(
            (400, 474, 300, 72),
            "Mailbox",
            "View combat reports",
        )
        self.professions_button = MenuButton(
            (400, 386, 300, 72),
            "Professions",
            "View gathering progress",
        )
        self.zone_back_button = MenuButton((560, 54, 160, 52), "Back")
        self.selected_region = None
        self.region_buttons = []
        self.combat_action_buttons = []
        self.gathering_action_buttons = []
        self.gathering_popups = []

    def _build_class_buttons(self):
        buttons = []
        y = 140
        for class_key, class_data in self.game.data.classes.items():
            stats = class_data["base_stats"]
            subtitle = (
                f"STR {stats.get('strength', 0)}  "
                f"DEX {stats.get('dexterity', 0)}  "
                f"INT {stats.get('intelligence', 0)}  "
                f"VIT {stats.get('vitality', 0)}  "
                f"WIS {stats.get('wisdom', 0)}  "
                f"LUCK {stats.get('luck', 0)}"
            )
            buttons.append(
                (class_key, MenuButton((80, y, 640, 80), class_data["name"], subtitle))
            )
            y += 100
        return buttons

    def _build_zone_buttons(self):
        buttons = []
        y = 128
        for zone_key, zone_data in self.game.data.zones.items():
            subtitle = (
                f"Niveau {zone_data['unlock_level']} - "
                f"Difficulte x{zone_data['difficulty_multiplier']}"
            )
            buttons.append(
                (zone_key, MenuButton((80, y, 640, 64), zone_data["name"], subtitle))
            )
            y += 72
        return buttons

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        pos = event.pos
        if self.game.state == "class_select":
            for class_key, button in self.class_buttons:
                if button.is_clicked(pos):
                    self.game.select_class(class_key)
                    self.zone_buttons = self._build_zone_buttons()
                    return

        if self.game.state == "town":
            if self.expedition_button.is_clicked(pos):
                self.game.state = "zone_select"
                self.selected_region = None
                return

            if self.inventory_button.is_clicked(pos):
                self.game.state = "inventory"
                return

            if self.merchant_button.is_clicked(pos):
                self.game.state = "merchant"
                return

            if self.crafting_button.is_clicked(pos):
                self.game.state = "crafting"
                return

            if self.skills_button.is_clicked(pos):
                self.game.state = "skills"
                return

            if self.professions_button.is_clicked(pos):
                self.game.state = "professions"
                return

            if self.mailbox_button.is_clicked(pos):
                self.game.state = "mailbox"
                return

        if self.game.state == "zone_select":
            self._handle_region_select_click(pos)
            return

        if self.game.state == "zone_actions":
            self._handle_region_actions_click(pos)
            return

    def draw(self, screen):
        if self.game.state == "class_select":
            draw_background(screen, self.class_background, (18, 24, 30))
            self._draw_class_select(screen)
        elif self.game.state == "town":
            draw_background(screen, self.town_background, (18, 24, 30))
            self._draw_town(screen)
        elif self.game.state in ("zone_select", "zone_actions"):
            draw_background(screen, self.zone_background, (18, 24, 30))
            if self.game.state == "zone_select":
                self._draw_region_select(screen)
            else:
                self._draw_region_actions(screen)

    def _draw_class_select(self, screen):
        title = self.title_font.render("Choisis ta classe", True, (245, 245, 245))
        screen.blit(title, (80, 64))

        for _, button in self.class_buttons:
            button.draw(screen, self.option_font, self.body_font)

    def _draw_town(self, screen):
        player_level = self.game.player["level"] if self.game.player else 1

        title = self.title_font.render("Town", True, (245, 245, 245))
        screen.blit(title, (80, 64))

        if self.game.selected_class:
            class_name = self.game.data.classes[self.game.selected_class]["name"]
        else:
            class_name = "Adventurer"
        subtitle = self.body_font.render(
            f"{class_name} - Level {player_level}", True, (190, 200, 205)
        )
        screen.blit(subtitle, (82, 105))

        self.expedition_button.draw(screen, self.option_font, self.body_font)
        self.inventory_button.draw(screen, self.option_font, self.body_font)
        self.merchant_button.draw(screen, self.option_font, self.body_font)
        has_available_recipe = self._has_available_crafting_recipe()
        if has_available_recipe:
            self.crafting_button.subtitle = "Recipes available"
        else:
            self.crafting_button.subtitle = "Use resources"
        self.crafting_button.draw(screen, self.option_font, self.body_font)
        if has_available_recipe:
            self._draw_crafting_ready_badge(screen)
        self.skills_button.draw(screen, self.option_font, self.body_font)
        self.professions_button.draw(screen, self.option_font, self.body_font)
        self.mailbox_button.draw(screen, self.option_font, self.body_font)
        self._draw_town_player_panel(screen)

    def _has_available_crafting_recipe(self):
        if not self.game.player:
            return False

        recipes = getattr(self.game.data, "recipes", {}) or {}
        if not isinstance(recipes, dict):
            return False

        inventory = self.game.player.get("inventory")
        for recipe in recipes.values():
            if not isinstance(recipe, dict):
                continue
            if can_craft_recipe(inventory, recipe):
                return True
        return False

    def _draw_crafting_ready_badge(self, screen):
        badge_rect = pygame.Rect(
            self.crafting_button.rect.right - 76,
            self.crafting_button.rect.y + 14,
            58,
            24,
        )
        pygame.draw.rect(screen, (78, 104, 50), badge_rect, border_radius=10)
        pygame.draw.rect(screen, (220, 220, 120), badge_rect, 2, border_radius=10)

        label = self.body_font.render("Ready", True, (245, 245, 245))
        screen.blit(label, (badge_rect.x + 8, badge_rect.y + 3))

    def _draw_town_player_panel(self, screen):
        rect = pygame.Rect(470, 150, 250, 220)
        pygame.draw.rect(screen, (35, 40, 48), rect, border_radius=6)
        pygame.draw.rect(screen, (120, 130, 140), rect, 2, border_radius=6)

        title = self.option_font.render("Player", True, (245, 245, 245))
        screen.blit(title, (rect.x + 18, rect.y + 18))

        player = self.game.player or {}
        if self.game.selected_class:
            class_name = self.game.data.classes[self.game.selected_class]["name"]
        else:
            class_name = "Adventurer"

        lines = [
            f"Class: {class_name}",
            f"Level: {player.get('level', 1)}",
            f"HP: {player.get('current_hp', 0)} / {player.get('max_hp', 0)}",
            f"Gold: {player.get('gold', 0)}",
        ]

        y = rect.y + 62
        for line in lines:
            text = self.body_font.render(line, True, (190, 200, 205))
            screen.blit(text, (rect.x + 18, y))
            y += 34

    def _get_zone_region_id(self, zone_key):
        if not isinstance(zone_key, str) or "_" not in zone_key:
            return None
        return zone_key.split("_", 1)[0]

    def _get_available_regions(self):
        regions = []
        for region_id in REGION_LABELS:
            if self._get_zones_for_region(region_id):
                regions.append(region_id)
        return regions

    def _get_zones_for_region(self, region_id):
        zones = getattr(self.game.data, "zones", {}) or {}
        return [
            zone_key
            for zone_key in zones
            if self._get_zone_region_id(zone_key) == region_id
        ]

    def _build_region_buttons(self):
        buttons = []
        y = 150
        for region_id in self._get_available_regions():
            region_zones = self._get_zones_for_region(region_id)
            zone_names = [self._get_zone_enemy_label(zone_key) for zone_key in region_zones]
            has_gathering = any(
                self.game.get_available_gathering_professions(zone_key)
                for zone_key in region_zones
            )
            if has_gathering:
                zone_names.append("gathering")
            subtitle = ", ".join(zone_names[:4])
            buttons.append(
                (
                    region_id,
                    MenuButton(
                        (80, y, 640, 72),
                        REGION_LABELS.get(region_id, region_id.title()),
                        subtitle,
                    ),
                )
            )
            y += 88
        return buttons

    def _draw_region_select(self, screen):
        player_level = self.game.player["level"] if self.game.player else 1
        title = self.title_font.render("Expedition", True, (245, 245, 245))
        screen.blit(title, (80, 64))

        subtitle = self.body_font.render(
            "Choose a region", True, (190, 200, 205)
        )
        screen.blit(subtitle, (82, 105))
        self.zone_back_button.draw(screen, self.option_font, self.body_font)

        self.region_buttons = self._build_region_buttons()
        for region_id, button in self.region_buttons:
            region_zones = self._get_zones_for_region(region_id)
            button.enabled = any(
                self.game.data.zones[zone_key].get("unlock_level", 1) <= player_level
                for zone_key in region_zones
            )
            button.draw(screen, self.option_font, self.body_font)

    def _draw_region_actions(self, screen):
        region_id = self.selected_region
        if region_id is None and self.game.selected_zone:
            region_id = self._get_zone_region_id(self.game.selected_zone)
        region_label = REGION_LABELS.get(region_id, "Region")
        region_zones = self._get_zones_for_region(region_id)

        title = self.title_font.render(f"Expedition > {region_label}", True, (245, 245, 245))
        screen.blit(title, (60, 54))
        self.zone_back_button.draw(screen, self.option_font, self.body_font)

        self._draw_combat_actions(screen, region_zones, 60, 130)
        self._draw_gathering_actions(screen, region_zones, 410, 130)
        self._draw_last_gathering_result(screen, region_zones, 410, 438)
        self._draw_gathering_popups(screen, 60, 438)

    def _handle_region_select_click(self, pos):
        if self.zone_back_button.is_clicked(pos):
            self.game.state = "town"
            return True

        if not self.region_buttons:
            self.region_buttons = self._build_region_buttons()

        for region_id, button in self.region_buttons:
            if button.is_clicked(pos):
                self.selected_region = region_id
                self.game.state = "zone_actions"
                return True
        return False

    def _handle_region_actions_click(self, pos):
        if self.zone_back_button.is_clicked(pos):
            self.game.state = "zone_select"
            self.selected_region = None
            return True

        for zone_key, button in self.combat_action_buttons:
            if button.is_clicked(pos):
                self.game.select_zone(zone_key)
                return True

        for zone_key, profession_id, button in self.gathering_action_buttons:
            if button.is_clicked(pos):
                if self._is_active_gathering_action(zone_key, profession_id):
                    self.game.stop_active_gathering()
                else:
                    self.game.start_active_gathering(
                        zone_key,
                        profession_id,
                        pygame.time.get_ticks(),
                    )
                return True
        return False

    def _draw_combat_actions(self, screen, region_zones, x, y):
        heading = self.option_font.render("Combat", True, (245, 245, 245))
        screen.blit(heading, (x, y))
        self.combat_action_buttons = []

        player_level = self.game.player["level"] if self.game.player else 0
        button_y = y + 42
        for zone_key in region_zones[:4]:
            zone = self.game.data.zones.get(zone_key, {})
            unlock_level = zone.get("unlock_level", 1)
            button = MenuButton(
                (x, button_y, 300, 54),
                zone.get("name", zone_key),
                f"Level {unlock_level}",
                enabled=player_level >= unlock_level,
            )
            self.combat_action_buttons.append((zone_key, button))
            button.draw(screen, self.body_font, self.body_font)
            button_y += 64

    def _draw_gathering_actions(self, screen, region_zones, x, y):
        heading = self.option_font.render("Gathering", True, (245, 245, 245))
        screen.blit(heading, (x, y))
        self.gathering_action_buttons = []

        button_y = y + 42
        visible_count = 0
        for zone_key in region_zones:
            zone = self.game.data.zones.get(zone_key, {})
            for profession_id, node_data in self.game.get_available_gathering_professions(zone_key).items():
                if visible_count >= 4:
                    return
                profession_name = self._get_profession_name(profession_id)
                node_name = node_data.get("name", "Gathering node")
                reward_preview = self._get_node_reward_preview(node_data)
                zone_name = zone.get("name", zone_key)
                mastery = 0
                if self.game.player:
                    mastery = get_profession_mastery(
                        self.game.player,
                        profession_id,
                        self.game.data.professions,
                    )
                is_active = self._is_active_gathering_action(zone_key, profession_id)
                action_label = "Stop" if is_active else "Start"
                title = f"{action_label} {profession_name} - {node_name}"
                rate = format_tick_rate(node_data.get("tick_seconds", 5))
                if is_active:
                    remaining_ms = self.game.get_active_gathering_remaining_ms(
                        pygame.time.get_ticks(),
                    )
                    rate = f"Active | Next: {self._format_remaining_time(remaining_ms)}"
                subtitle = f"{zone_name} | {reward_preview} | M:{mastery} | {rate}"
                button = MenuButton((x, button_y, 320, 54), title, subtitle)
                self.gathering_action_buttons.append((zone_key, profession_id, button))
                button.draw(screen, self.body_font, self.body_font)
                button_y += 64
                visible_count += 1

        if visible_count == 0:
            empty_text = self.body_font.render("No gathering node", True, (145, 145, 150))
            screen.blit(empty_text, (x, button_y))

    def _draw_last_gathering_result(self, screen, region_zones, x, y):
        result = self.game.last_gathering_result
        if not isinstance(result, dict):
            return

        result_zone = result.get("zone_id")
        if result_zone is not None and result_zone not in region_zones:
            return

        panel = pygame.Rect(x, y, 320, 112)
        pygame.draw.rect(screen, (35, 40, 48), panel, border_radius=6)
        pygame.draw.rect(screen, (120, 130, 140), panel, 2, border_radius=6)
        heading = self.body_font.render("Last gathering result", True, (245, 245, 245))
        screen.blit(heading, (panel.x + 12, panel.y + 10))

        line_y = panel.y + 36
        for line in self._format_gathering_result(result)[:4]:
            text = self.body_font.render(line, True, (210, 220, 205))
            screen.blit(text, (panel.x + 12, line_y))
            line_y += 20

    def _is_active_gathering_action(self, zone_key, profession_id):
        activity = getattr(self.game, "active_gathering", None)
        return (
            isinstance(activity, dict)
            and activity.get("zone_id") == zone_key
            and activity.get("profession_id") == profession_id
        )

    def _format_remaining_time(self, remaining_ms):
        if remaining_ms <= 0:
            return "Ready"
        if remaining_ms >= 1000:
            return f"{int((remaining_ms + 999) / 1000)}s"
        return f"{int(remaining_ms)}ms"

    def add_gathering_popup(self, result):
        if not isinstance(result, dict):
            return

        popup_type = "success" if result.get("gathered") is True else "failure"
        texts = []
        if result.get("gathered") is True:
            for reward in result.get("rewards", []):
                item_name = self._get_item_name(reward.get("item"))
                quantity = reward.get("quantity", 1)
                texts.append(f"+{quantity} {item_name}")
            profession_xp = result.get("profession_xp", 0)
            if profession_xp > 0:
                profession_name = self._get_profession_name(result.get("profession_id"))
                texts.append(f"+{profession_xp} {profession_name} XP")
        elif result.get("reason") == "inventory_full":
            texts.append("Inventory full. Gathering stopped.")
        else:
            texts.append(self._get_gathering_failure_message(result.get("reason")))

        created_at = pygame.time.get_ticks()
        for text in texts:
            self.gathering_popups.append({
                "text": text,
                "type": popup_type,
                "created_at": created_at,
                "duration_ms": 1800,
            })

    def _draw_gathering_popups(self, screen, x, y):
        current_time = pygame.time.get_ticks()
        self.gathering_popups = [
            popup
            for popup in self.gathering_popups
            if current_time - popup.get("created_at", 0) <= popup.get("duration_ms", 0)
        ]

        for index, popup in enumerate(self.gathering_popups[-4:]):
            color = (125, 220, 145) if popup.get("type") == "success" else (230, 160, 90)
            text = self.body_font.render(popup.get("text", ""), True, color)
            screen.blit(text, (x, y + index * 22))

    def _get_zone_enemy_label(self, zone_key):
        zone = self.game.data.zones.get(zone_key, {})
        zone_name = zone.get("name", zone_key)
        region_id = self._get_zone_region_id(zone_key)
        region_label = REGION_LABELS.get(region_id, "")
        return zone_name.replace(region_label, "").strip() or zone_name

    def _get_node_reward_preview(self, node_data):
        rewards = []
        for reward in node_data.get("rewards", [])[:2]:
            rewards.append(self._get_item_name(reward.get("item")))
        return ", ".join(rewards) if rewards else "Rewards"

    def _format_gathering_result(self, result):
        if result.get("gathered") is not True:
            return [self._get_gathering_failure_message(result.get("reason"))]

        lines = ["Gathered:"]
        for reward in result.get("rewards", []):
            item_name = self._get_item_name(reward.get("item"))
            quantity = reward.get("quantity", 1)
            lines.append(f"+{quantity} {item_name}")

        profession_id = result.get("profession_id")
        profession_name = self._get_profession_name(profession_id)
        xp_gain = result.get("profession_xp", 0)
        if xp_gain:
            lines.append(f"+{xp_gain} {profession_name} XP")
        if result.get("leveled_up"):
            lines.append("Level up!")
        return lines[:6]

    def _get_item_name(self, item_id):
        items = getattr(self.game.data, "items", {}) or {}
        item_data = items.get(item_id, {})
        return item_data.get("name", item_id or "Unknown item")

    def _get_profession_name(self, profession_id):
        professions = getattr(self.game.data, "professions", {}) or {}
        profession_data = professions.get(profession_id, {})
        return profession_data.get("name", profession_id or "Unknown profession")

    def _get_gathering_failure_message(self, reason):
        messages = {
            "unknown_node": "No gathering node",
            "inventory_full": "Inventory full",
            "invalid_zone": "Invalid zone",
            "locked_zone": "Zone locked",
        }
        return messages.get(reason, "Gathering failed")
