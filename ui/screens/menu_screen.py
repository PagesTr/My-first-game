import pygame

try:
    from systems.crafting import can_craft_recipe
except ImportError:
    from systems.crafting import can_craft as can_craft_recipe

from systems.professions import get_profession_mastery
from systems.active_gathering import format_tick_rate
from systems.achievements import get_claimable_achievements
from ui.assets import draw_background, load_image


REGION_LABELS = {
    "forest": "Forest",
    "caves": "Caves",
    "mountains": "Mountains",
}

TOWN_PALETTE = {
    "sky_top": (30, 36, 48),
    "sky_bottom": (72, 58, 44),
    "roof_back": (54, 38, 34),
    "roof_front": (72, 48, 38),
    "wall_back": (56, 50, 46),
    "wall_front": (76, 62, 50),
    "street": (34, 32, 32),
    "street_light": (68, 61, 52),
    "panel": (48, 42, 38),
    "panel_dark": (31, 30, 32),
    "panel_light": (94, 78, 58),
    "border": (112, 86, 50),
    "border_light": (226, 188, 98),
    "button": (70, 58, 44),
    "button_disabled": (45, 43, 42),
    "button_border": (214, 174, 92),
    "text": (242, 232, 210),
    "muted": (194, 181, 154),
    "gold": (232, 190, 88),
    "green": (132, 190, 118),
    "shadow": (10, 9, 10),
}


class MenuButton:
    def __init__(self, rect, title, subtitle="", enabled=True):
        self.rect = pygame.Rect(rect)
        self.title = title
        self.subtitle = subtitle
        self.enabled = enabled

    def draw(self, screen, title_font, body_font):
        bg = TOWN_PALETTE["button"] if self.enabled else TOWN_PALETTE["button_disabled"]
        border = TOWN_PALETTE["button_border"] if self.enabled else (95, 88, 78)
        text_color = TOWN_PALETTE["text"] if self.enabled else (145, 140, 132)
        sub_color = TOWN_PALETTE["muted"] if self.enabled else (120, 116, 108)

        pygame.draw.rect(screen, TOWN_PALETTE["shadow"], self.rect.move(4, 4), border_radius=6)
        pygame.draw.rect(screen, bg, self.rect, border_radius=6)
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=6)
        pygame.draw.rect(screen, TOWN_PALETTE["panel_light"], self.rect.inflate(-10, -10), 1, border_radius=4)

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
            (80, 170, 300, 72),
            "Expedition",
            "Choose a combat zone",
        )
        self.inventory_button = MenuButton(
            (80, 252, 300, 72),
            "Inventory",
            "Manage gear and items",
        )
        self.merchant_button = MenuButton(
            (80, 334, 300, 72),
            "Merchant",
            "Sell items",
        )
        self.crafting_button = MenuButton(
            (80, 416, 300, 72),
            "Craft",
            "Use resources",
        )
        self.skills_button = MenuButton(
            (80, 498, 300, 72),
            "Skills",
            "Learn and equip skills",
        )
        self.mailbox_button = MenuButton(
            (400, 490, 300, 54),
            "Notice Board",
            "Dev notes and letters",
        )
        self.professions_button = MenuButton(
            (400, 426, 300, 54),
            "Professions",
            "View gathering progress",
        )
        self.quests_button = MenuButton(
            (400, 298, 300, 54),
            "Quests",
            "Track forest objectives",
        )
        self.achievements_button = MenuButton(
            (400, 362, 300, 54),
            "Achievements",
            "View progress records",
        )
        self.zone_back_button = MenuButton((560, 54, 160, 52), "Back")
        self.selected_region = None
        self.region_buttons = []
        self.combat_action_buttons = []
        self.gathering_action_buttons = []
        self.gathering_popups = []
        self.selected_gathering_action = None
        self.selected_dungeon_id = None
        self.zone_action_tab = "combat"
        self.combat_page = 0
        self.gathering_page = 0
        self.selected_combat_zone = None
        self.dungeon_action_buttons = []
        self.dungeon_message = ""
        self.combat_tab_rect = pygame.Rect(60, 104, 150, 38)
        self.gathering_tab_rect = pygame.Rect(218, 104, 150, 38)
        self.dungeons_tab_rect = pygame.Rect(376, 104, 150, 38)
        self.combat_page_prev_rect = pygame.Rect(60, 500, 44, 38)
        self.combat_page_next_rect = pygame.Rect(346, 500, 44, 38)
        self.combat_start_button = MenuButton(
            (420, 430, 310, 54),
            "Start Expedition",
        )
        self.gathering_page_prev_rect = pygame.Rect(60, 500, 44, 38)
        self.gathering_page_next_rect = pygame.Rect(346, 500, 44, 38)
        self.gathering_online_button = MenuButton(
            (420, 470, 150, 50),
            "Start Online",
        )
        self.gathering_offline_button = MenuButton(
            (580, 470, 150, 50),
            "Send Offline",
        )
        self.dungeon_start_button = MenuButton(
            (420, 470, 310, 50),
            "Start Dungeon",
        )

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
        if event.type == pygame.KEYDOWN and self.game.state == "zone_actions":
            if event.key == pygame.K_o:
                self._start_selected_gathering_offline()
            return

        if event.type == pygame.KEYDOWN and self.game.state == "town":
            if event.key == pygame.K_e:
                self._clear_offline_result()
                self.game.open_exploration()
            return

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
                self._clear_offline_result()
                self.game.state = "zone_select"
                self.selected_region = None
                return

            if self.inventory_button.is_clicked(pos):
                self._clear_offline_result()
                self.game.state = "inventory"
                return

            if self.merchant_button.is_clicked(pos):
                self._clear_offline_result()
                self.game.state = "merchant"
                return

            if self.crafting_button.is_clicked(pos):
                self._clear_offline_result()
                self.game.state = "crafting"
                return

            if self.skills_button.is_clicked(pos):
                self._clear_offline_result()
                self.game.state = "skills"
                return

            if self.professions_button.is_clicked(pos):
                self._clear_offline_result()
                self.game.state = "professions"
                return

            if self.quests_button.is_clicked(pos):
                self._clear_offline_result()
                self.game.state = "quests"
                return

            if self.achievements_button.is_clicked(pos):
                self._clear_offline_result()
                self.game.state = "achievements"
                return

            if self.mailbox_button.is_clicked(pos):
                self._clear_offline_result()
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
            self._draw_town_background(screen)
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

        if self.game.selected_class:
            class_name = self.game.data.classes[self.game.selected_class]["name"]
        else:
            class_name = "Adventurer"
        self._draw_town_title(screen, class_name, player_level)
        self._draw_town_action_panels(screen)

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
        self.quests_button.draw(screen, self.option_font, self.body_font)
        claimable_count = self._get_claimable_achievement_count()
        if claimable_count > 0:
            self.achievements_button.subtitle = "Rewards to claim"
        else:
            self.achievements_button.subtitle = "View progress records"
        self.achievements_button.draw(screen, self.option_font, self.body_font)
        if claimable_count > 0:
            self._draw_claimable_button_highlight(screen, self.achievements_button.rect)
            self._draw_achievements_claim_badge(screen, claimable_count)
        self.professions_button.draw(screen, self.option_font, self.body_font)
        self.mailbox_button.draw(screen, self.option_font, self.body_font)
        self._draw_town_player_panel(screen)
        self._draw_offline_result_panel(screen)

    def _draw_town_background(self, screen):
        if self.town_background is not None:
            screen.blit(self.town_background, (0, 0))
            overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
            overlay.fill((20, 16, 12, 74))
            screen.blit(overlay, (0, 0))
        else:
            for y in range(0, 600, 4):
                blend = y / 600
                color = (
                    int(TOWN_PALETTE["sky_top"][0] * (1 - blend) + TOWN_PALETTE["sky_bottom"][0] * blend),
                    int(TOWN_PALETTE["sky_top"][1] * (1 - blend) + TOWN_PALETTE["sky_bottom"][1] * blend),
                    int(TOWN_PALETTE["sky_top"][2] * (1 - blend) + TOWN_PALETTE["sky_bottom"][2] * blend),
                )
                pygame.draw.rect(screen, color, (0, y, 800, 4))
            self._draw_town_silhouette(screen)

        self._draw_town_street(screen)

    def _draw_town_silhouette(self, screen):
        for x in range(-30, 850, 132):
            wall = pygame.Rect(x + 14, 278, 92, 154)
            roof = [(x, 278), (x + 60, 218), (x + 120, 278)]
            pygame.draw.rect(screen, TOWN_PALETTE["wall_back"], wall)
            pygame.draw.polygon(screen, TOWN_PALETTE["roof_back"], roof)
            pygame.draw.rect(screen, (32, 30, 30), (x + 44, 336, 28, 96))
            pygame.draw.rect(screen, (224, 172, 84), (x + 30, 306, 18, 24))

        for x in range(28, 850, 156):
            wall = pygame.Rect(x + 8, 318, 112, 116)
            roof = [(x - 8, 318), (x + 64, 250), (x + 136, 318)]
            pygame.draw.rect(screen, TOWN_PALETTE["wall_front"], wall)
            pygame.draw.polygon(screen, TOWN_PALETTE["roof_front"], roof)
            pygame.draw.rect(screen, (36, 31, 28), (x + 46, 360, 32, 74))
            pygame.draw.rect(screen, (238, 184, 90), (x + 22, 340, 20, 22))
            pygame.draw.rect(screen, (238, 184, 90), (x + 84, 340, 20, 22))

    def _draw_town_street(self, screen):
        pygame.draw.rect(screen, TOWN_PALETTE["street"], (0, 430, 800, 170))
        pygame.draw.rect(screen, TOWN_PALETTE["street_light"], (0, 430, 800, 4))
        for y in range(454, 600, 28):
            offset = 0 if (y // 28) % 2 == 0 else 34
            for x in range(-offset, 800, 68):
                pygame.draw.rect(screen, (44, 41, 40), (x, y, 52, 18), border_radius=3)
                pygame.draw.rect(screen, (26, 25, 25), (x, y, 52, 18), 1, border_radius=3)

    def _draw_town_title(self, screen, class_name, player_level):
        sign_rect = pygame.Rect(60, 46, 332, 78)
        pygame.draw.rect(screen, TOWN_PALETTE["shadow"], sign_rect.move(4, 4), border_radius=6)
        pygame.draw.rect(screen, TOWN_PALETTE["panel_dark"], sign_rect, border_radius=6)
        pygame.draw.rect(screen, TOWN_PALETTE["border_light"], sign_rect, 3, border_radius=6)
        pygame.draw.rect(screen, TOWN_PALETTE["panel_light"], sign_rect.inflate(-12, -12), 1, border_radius=4)

        title_shadow = self.title_font.render("Town", True, TOWN_PALETTE["shadow"])
        title = self.title_font.render("Town", True, TOWN_PALETTE["gold"])
        screen.blit(title_shadow, (sign_rect.x + 20 + 2, sign_rect.y + 10 + 2))
        screen.blit(title, (sign_rect.x + 20, sign_rect.y + 10))

        subtitle = self.body_font.render(
            f"{class_name} - Level {player_level}",
            True,
            TOWN_PALETTE["muted"],
        )
        screen.blit(subtitle, (sign_rect.x + 22, sign_rect.y + 50))

    def _draw_town_action_panels(self, screen):
        left_panel = pygame.Rect(56, 132, 348, 462)
        right_panel = pygame.Rect(384, 132, 356, 434)
        self._draw_town_panel(screen, left_panel, "Town Services")
        self._draw_town_panel(screen, right_panel, "Records & Guilds")

    def _draw_town_panel(self, screen, rect, title):
        pygame.draw.rect(screen, TOWN_PALETTE["shadow"], rect.move(5, 5), border_radius=8)
        pygame.draw.rect(screen, TOWN_PALETTE["panel"], rect, border_radius=8)
        pygame.draw.rect(screen, TOWN_PALETTE["border"], rect, 3, border_radius=8)
        pygame.draw.rect(screen, TOWN_PALETTE["panel_light"], rect.inflate(-14, -14), 1, border_radius=5)
        pygame.draw.line(
            screen,
            TOWN_PALETTE["border_light"],
            (rect.x + 14, rect.y + 14),
            (rect.right - 14, rect.y + 14),
            2,
        )
        label_rect = pygame.Rect(rect.x + 18, rect.y + 8, rect.w - 36, 22)
        pygame.draw.rect(screen, TOWN_PALETTE["panel_dark"], label_rect, border_radius=5)
        pygame.draw.rect(screen, TOWN_PALETTE["border_light"], label_rect, 1, border_radius=5)
        label = self.body_font.render(title, True, TOWN_PALETTE["text"])
        screen.blit(label, (label_rect.x + 12, label_rect.y + 2))

    def _get_claimable_achievement_count(self):
        player = getattr(self.game, "player", None)
        if not isinstance(player, dict):
            return 0
        achievements = player.get("achievements")
        if not isinstance(achievements, dict):
            return 0
        try:
            return len(get_claimable_achievements(player))
        except (TypeError, AttributeError):
            return 0

    def _draw_achievements_claim_badge(self, screen, count):
        rect = self.achievements_button.rect
        badge_width = 92
        badge_height = 26
        badge = pygame.Rect(
            rect.right - badge_width - 12,
            rect.y + 12,
            badge_width,
            badge_height,
        )
        pygame.draw.rect(screen, (105, 82, 36), badge, border_radius=10)
        pygame.draw.rect(screen, TOWN_PALETTE["border_light"], badge, 2, border_radius=10)

        dot_center = (badge.x + 13, badge.centery)
        pygame.draw.circle(screen, (255, 220, 100), dot_center, 5)
        pygame.draw.circle(screen, (255, 245, 200), dot_center, 2)

        count_label = "99+" if count > 99 else str(count)
        label = self.body_font.render(f"CLAIM x{count_label}", True, (255, 245, 200))
        label_rect = label.get_rect()
        label_rect.centery = badge.centery
        label_rect.x = badge.x + 24
        screen.blit(label, label_rect)

    def _draw_claimable_button_highlight(self, screen, rect):
        highlight = pygame.Rect(rect)
        highlight.inflate_ip(4, 4)
        pygame.draw.rect(screen, TOWN_PALETTE["border_light"], highlight, 2, border_radius=8)

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

        label = self.body_font.render("Ready", True, TOWN_PALETTE["text"])
        screen.blit(label, (badge_rect.x + 8, badge_rect.y + 3))

    def _draw_town_player_panel(self, screen):
        rect = pygame.Rect(470, 150, 250, 132)
        pygame.draw.rect(screen, TOWN_PALETTE["shadow"], rect.move(4, 4), border_radius=6)
        pygame.draw.rect(screen, TOWN_PALETTE["panel_dark"], rect, border_radius=6)
        pygame.draw.rect(screen, TOWN_PALETTE["border_light"], rect, 2, border_radius=6)
        pygame.draw.rect(screen, TOWN_PALETTE["panel_light"], rect.inflate(-10, -10), 1, border_radius=4)

        title = self.option_font.render("Player", True, TOWN_PALETTE["gold"])
        screen.blit(title, (rect.x + 18, rect.y + 18))

        player = self.game.player or {}
        if self.game.selected_class:
            class_name = self.game.data.classes[self.game.selected_class]["name"]
        else:
            class_name = "Adventurer"

        lines = [
            f"Class: {class_name}",
            f"Level: {player.get('level', 1)}",
            f"Gold: {player.get('gold', 0)}",
            "E: Explorer la clairiere",
        ]

        y = rect.y + 52
        for line in lines:
            text = self.body_font.render(line, True, TOWN_PALETTE["muted"])
            screen.blit(text, (rect.x + 18, y))
            y += 24

    def _draw_offline_result_panel(self, screen):
        result = getattr(self.game, "last_offline_result", None)
        lines = self._format_offline_result_lines(result)
        if not lines:
            return

        rect = pygame.Rect(400, 64, 320, 78)
        pygame.draw.rect(screen, TOWN_PALETTE["shadow"], rect.move(4, 4), border_radius=6)
        pygame.draw.rect(screen, TOWN_PALETTE["panel_dark"], rect, border_radius=6)
        pygame.draw.rect(screen, TOWN_PALETTE["border_light"], rect, 2, border_radius=6)

        title = self.body_font.render("Offline Progress", True, TOWN_PALETTE["gold"])
        screen.blit(title, (rect.x + 14, rect.y + 10))

        y = rect.y + 30
        for line in lines[:3]:
            text = self.body_font.render(
                self._truncate_text(line, self.body_font, rect.w - 28),
                True,
                TOWN_PALETTE["muted"],
            )
            screen.blit(text, (rect.x + 14, y))
            y += 18

    def _format_offline_result_lines(self, result):
        if not isinstance(result, dict):
            return []
        reason = result.get("reason")
        if reason in (None, "no_activity", "not_enough_time"):
            if result.get("resolved") is not True:
                return []
        if reason == "inventory_full":
            return ["Inventory full", "Gathering stopped"]
        if result.get("resolved") is not True:
            return []

        profession_name = self._get_profession_name(result.get("profession_id"))
        lines = [f"{profession_name} returned", f"Ticks: {result.get('ticks', 0)}"]
        rewards = result.get("rewards", [])
        if isinstance(rewards, list):
            for reward in rewards[:2]:
                item_name = self._get_item_name(reward.get("item"))
                quantity = reward.get("quantity", 1)
                lines.append(f"+{quantity} {item_name}")
            if len(rewards) > 2:
                lines.append(f"+{len(rewards) - 2} more")

        xp_gain = result.get("profession_xp", 0)
        if xp_gain:
            lines.append(f"+{xp_gain} {profession_name} XP")
        return lines[:4]

    def _clear_offline_result(self):
        if hasattr(self.game, "last_offline_result"):
            self.game.last_offline_result = None

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

    def _get_region_combat_zones(self, region_id):
        zones = getattr(self.game.data, "zones", {}) or {}
        return [
            zone_key
            for zone_key in self._get_zones_for_region(region_id)
            if zones.get(zone_key, {}).get("enemy_pool")
        ]

    def _get_region_gathering_actions(self, region_id):
        actions = []
        if not hasattr(self.game, "get_available_gathering_professions"):
            return actions
        for zone_key in self._get_zones_for_region(region_id):
            zone_nodes = self.game.get_available_gathering_professions(zone_key)
            if not isinstance(zone_nodes, dict):
                continue
            for profession_id, node_data in zone_nodes.items():
                actions.append({
                    "zone_key": zone_key,
                    "profession_id": profession_id,
                    "node_data": node_data if isinstance(node_data, dict) else {},
                })
        return actions

    def _paginate_items(self, items, page, page_size):
        total_pages = max(1, (len(items) + page_size - 1) // page_size)
        page = self._clamp_page(page, total_pages)
        start = page * page_size
        return items[start:start + page_size], total_pages

    def _clamp_page(self, page, total_pages):
        total_pages = max(1, total_pages)
        return max(0, min(page, total_pages - 1))

    def _draw_tab_button(self, screen, rect, label, is_active):
        bg = (78, 92, 72) if is_active else (45, 52, 60)
        border = (210, 220, 145) if is_active else (105, 115, 125)
        pygame.draw.rect(screen, bg, rect, border_radius=6)
        pygame.draw.rect(screen, border, rect, 2, border_radius=6)
        text = self.body_font.render(label, True, (245, 245, 245))
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)

    def _draw_small_nav_button(self, screen, rect, label, enabled=True):
        bg = (58, 68, 78) if enabled else (42, 42, 46)
        border = (180, 190, 195) if enabled else (85, 85, 90)
        color = (245, 245, 245) if enabled else (120, 120, 125)
        pygame.draw.rect(screen, bg, rect, border_radius=6)
        pygame.draw.rect(screen, border, rect, 2, border_radius=6)
        text = self.option_font.render(label, True, color)
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)

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

        title = self.title_font.render(f"Expedition > {region_label}", True, (245, 245, 245))
        screen.blit(title, (60, 54))
        self.zone_back_button.draw(screen, self.option_font, self.body_font)

        self._draw_tab_button(
            screen,
            self.combat_tab_rect,
            "Combat",
            self.zone_action_tab == "combat",
        )
        self._draw_tab_button(
            screen,
            self.gathering_tab_rect,
            "Gathering",
            self.zone_action_tab == "gathering",
        )
        self._draw_tab_button(
            screen,
            self.dungeons_tab_rect,
            "Dungeons",
            self.zone_action_tab == "dungeons",
        )

        if self.zone_action_tab == "combat":
            self._draw_combat_tab(screen, region_id)
        elif self.zone_action_tab == "gathering":
            self._draw_gathering_tab(screen, region_id)
        else:
            self._draw_dungeons_tab(screen, region_id)

    def _handle_region_select_click(self, pos):
        if self.zone_back_button.is_clicked(pos):
            self.game.state = "exploration"
            return True

        if not self.region_buttons:
            self.region_buttons = self._build_region_buttons()

        for region_id, button in self.region_buttons:
            if button.is_clicked(pos):
                self.selected_region = region_id
                self.zone_action_tab = "combat"
                self.combat_page = 0
                self.gathering_page = 0
                self.selected_combat_zone = None
                self.selected_gathering_action = None
                self.selected_dungeon_id = None
                self.dungeon_message = ""
                self.game.state = "zone_actions"
                return True
        return False

    def _handle_region_actions_click(self, pos):
        if self.zone_back_button.is_clicked(pos):
            self.game.state = "zone_select"
            self.selected_region = None
            return True

        if self.combat_tab_rect.collidepoint(pos):
            self.zone_action_tab = "combat"
            return True

        if self.gathering_tab_rect.collidepoint(pos):
            self.zone_action_tab = "gathering"
            return True

        if self.dungeons_tab_rect.collidepoint(pos):
            self.zone_action_tab = "dungeons"
            return True

        region_id = self.selected_region
        if region_id is None and self.game.selected_zone:
            region_id = self._get_zone_region_id(self.game.selected_zone)

        if self.zone_action_tab == "combat":
            combat_zones = self._get_region_combat_zones(region_id)
            _, total_pages = self._paginate_items(combat_zones, self.combat_page, 6)
            if self.combat_page_prev_rect.collidepoint(pos) and self.combat_page > 0:
                self.combat_page -= 1
                return True
            if self.combat_page_next_rect.collidepoint(pos) and self.combat_page < total_pages - 1:
                self.combat_page += 1
                return True

            for zone_key, button in self.combat_action_buttons:
                if button.rect.collidepoint(pos):
                    self.selected_combat_zone = zone_key
                    return True

            selected_zone = self.selected_combat_zone
            if self.combat_start_button.is_clicked(pos) and selected_zone:
                self.game.select_zone(selected_zone)
                return True
            return False

        if self.zone_action_tab == "dungeons":
            for dungeon_id, button in self.dungeon_action_buttons:
                if button.rect.collidepoint(pos):
                    self.selected_dungeon_id = dungeon_id
                    self.dungeon_message = ""
                    return True
            if self.dungeon_start_button.is_clicked(pos) and self.selected_dungeon_id:
                if not hasattr(self.game, "start_dungeon"):
                    self.dungeon_message = "Dungeons unavailable"
                    return True
                result = self.game.start_dungeon(self.selected_dungeon_id)
                if result.get("started") is True:
                    self.game.state = "dungeon"
                    self.dungeon_message = ""
                else:
                    self.dungeon_message = self._get_dungeon_start_failure_message(
                        result.get("reason"),
                    )
                return True
            return False

        gathering_actions = self._get_region_gathering_actions(region_id)
        _, total_pages = self._paginate_items(gathering_actions, self.gathering_page, 6)
        if self.gathering_page_prev_rect.collidepoint(pos) and self.gathering_page > 0:
            self.gathering_page -= 1
            return True
        if self.gathering_page_next_rect.collidepoint(pos) and self.gathering_page < total_pages - 1:
            self.gathering_page += 1
            return True

        for action, button in self.gathering_action_buttons:
            if button.rect.collidepoint(pos):
                self.selected_gathering_action = {
                    "zone_key": action["zone_key"],
                    "profession_id": action["profession_id"],
                }
                return True

        zone_key, profession_id = self._get_displayed_gathering_action(
            self._get_zones_for_region(region_id),
        )
        if self.gathering_online_button.is_clicked(pos) and zone_key and profession_id:
            if self._is_active_gathering_action(zone_key, profession_id):
                self.game.stop_active_gathering()
            else:
                self.game.start_active_gathering(
                    zone_key,
                    profession_id,
                    pygame.time.get_ticks(),
                )
            return True

        if self.gathering_offline_button.is_clicked(pos):
            self._start_selected_gathering_offline()
            return True
        return False

    def _draw_combat_tab(self, screen, region_id):
        combat_zones = self._get_region_combat_zones(region_id)
        self.combat_page = self._clamp_page(
            self.combat_page,
            max(1, (len(combat_zones) + 5) // 6),
        )
        visible_zones, total_pages = self._paginate_items(
            combat_zones,
            self.combat_page,
            6,
        )
        player_level = self.game.player.get("level", 0) if self.game.player else 0
        if self.selected_combat_zone not in combat_zones:
            self.selected_combat_zone = None
        if self.selected_combat_zone is None:
            for zone_key in visible_zones:
                if self.game.data.zones[zone_key].get("unlock_level", 1) <= player_level:
                    self.selected_combat_zone = zone_key
                    break
            if self.selected_combat_zone is None and visible_zones:
                self.selected_combat_zone = visible_zones[0]

        self.combat_action_buttons = []
        x, y = 60, 150
        for index, zone_key in enumerate(visible_zones):
            zone = self.game.data.zones.get(zone_key, {})
            unlock_level = zone.get("unlock_level", 1)
            button = MenuButton(
                (x, y + index * 60, 330, 52),
                zone.get("name", zone_key),
                f"Level {unlock_level}",
                enabled=player_level >= unlock_level,
            )
            self.combat_action_buttons.append((zone_key, button))
            button.draw(screen, self.body_font, self.body_font)
            if zone_key == self.selected_combat_zone:
                pygame.draw.rect(screen, (210, 220, 145), button.rect, 3, border_radius=6)

        self._draw_combat_detail_panel(screen, self.selected_combat_zone)
        can_start = self._can_start_selected_combat_zone()
        self.combat_start_button.enabled = can_start
        self.combat_start_button.draw(screen, self.option_font, self.body_font)

        self._draw_small_nav_button(
            screen,
            self.combat_page_prev_rect,
            "<",
            self.combat_page > 0,
        )
        self._draw_small_nav_button(
            screen,
            self.combat_page_next_rect,
            ">",
            self.combat_page < total_pages - 1,
        )
        page_text = self.body_font.render(
            f"Page {self.combat_page + 1} / {total_pages}",
            True,
            (190, 200, 205),
        )
        screen.blit(page_text, (120, 508))

    def _draw_combat_detail_panel(self, screen, zone_key):
        rect = pygame.Rect(420, 150, 310, 260)
        pygame.draw.rect(screen, (35, 40, 48), rect, border_radius=6)
        pygame.draw.rect(screen, (120, 130, 140), rect, 2, border_radius=6)
        title = self.option_font.render("Zone Details", True, (245, 245, 245))
        screen.blit(title, (rect.x + 14, rect.y + 14))
        if not zone_key:
            text = self.body_font.render("Select a combat zone", True, (150, 155, 160))
            screen.blit(text, (rect.x + 14, rect.y + 58))
            return

        zone = self.game.data.zones.get(zone_key, {})
        enemy_id = (zone.get("enemy_pool") or [""])[0]
        enemy = self.game.data.enemies.get(enemy_id, {})
        loot_names = [self._get_item_name(item_id) for item_id in zone.get("loot_table", [])[:3]]
        lines = [
            zone.get("name", zone_key),
            f"Unlock: Level {zone.get('unlock_level', 1)}",
            f"Enemy: {enemy.get('name', enemy_id or 'Unknown')}",
            f"Difficulty: x{zone.get('difficulty_multiplier', 1.0)}",
            f"Loot: {', '.join(loot_names) if loot_names else '-'}",
            zone.get("description", ""),
        ]
        line_y = rect.y + 54
        for line in lines:
            text = self.body_font.render(
                self._truncate_text(line, self.body_font, rect.w - 28),
                True,
                (210, 220, 205),
            )
            screen.blit(text, (rect.x + 14, line_y))
            line_y += 28

    def _can_start_selected_combat_zone(self):
        zone_key = self.selected_combat_zone
        if not zone_key or not self.game.player:
            return False
        zone = self.game.data.zones.get(zone_key)
        if not isinstance(zone, dict):
            return False
        return self.game.player.get("level", 0) >= zone.get("unlock_level", 1)

    def _draw_dungeons_tab(self, screen, region_id):
        dungeon_entries = []
        if hasattr(self.game, "get_available_dungeons"):
            dungeon_entries = self.game.get_available_dungeons(region_id)
        player_level = self.game.player.get("level", 0) if self.game.player else 0

        dungeon_ids = [entry["dungeon_id"] for entry in dungeon_entries]
        if self.selected_dungeon_id not in dungeon_ids:
            self.selected_dungeon_id = None
        if self.selected_dungeon_id is None:
            for entry in dungeon_entries:
                dungeon = entry.get("dungeon", {})
                if player_level >= dungeon.get("unlock_level", 1):
                    self.selected_dungeon_id = entry["dungeon_id"]
                    break
            if self.selected_dungeon_id is None and dungeon_entries:
                self.selected_dungeon_id = dungeon_entries[0]["dungeon_id"]

        self.dungeon_action_buttons = []
        x, y = 60, 150
        for index, entry in enumerate(dungeon_entries[:6]):
            dungeon_id = entry["dungeon_id"]
            dungeon = entry.get("dungeon", {})
            unlock_level = dungeon.get("unlock_level", 1)
            locked = player_level < unlock_level
            subtitle = f"Level {unlock_level}" + (" - Locked" if locked else "")
            button = MenuButton(
                (x, y + index * 60, 330, 52),
                dungeon.get("name", dungeon_id),
                subtitle,
                enabled=not locked,
            )
            self.dungeon_action_buttons.append((dungeon_id, button))
            button.draw(screen, self.body_font, self.body_font)
            if dungeon_id == self.selected_dungeon_id:
                pygame.draw.rect(screen, (210, 220, 145), button.rect, 3, border_radius=6)

        if not dungeon_entries:
            empty_text = self.body_font.render("No dungeons available", True, (145, 145, 150))
            screen.blit(empty_text, (x, y))

        self._draw_dungeon_detail_panel(screen, self.selected_dungeon_id)
        self.dungeon_start_button.enabled = self._can_start_selected_dungeon()
        self.dungeon_start_button.draw(screen, self.option_font, self.body_font)
        if self.dungeon_message:
            message = self.body_font.render(
                self._truncate_text(self.dungeon_message, self.body_font, 310),
                True,
                (230, 160, 90),
            )
            screen.blit(message, (420, 532))

    def _draw_dungeon_detail_panel(self, screen, dungeon_id):
        rect = pygame.Rect(420, 150, 310, 300)
        pygame.draw.rect(screen, (35, 40, 48), rect, border_radius=6)
        pygame.draw.rect(screen, (120, 130, 140), rect, 2, border_radius=6)
        title = self.option_font.render("Dungeon Details", True, (245, 245, 245))
        screen.blit(title, (rect.x + 14, rect.y + 14))

        dungeon = self._get_dungeon_data(dungeon_id)
        if not dungeon:
            text = self.body_font.render("Select a dungeon", True, (150, 155, 160))
            screen.blit(text, (rect.x + 14, rect.y + 58))
            return

        boss_id = dungeon.get("boss_enemy_id", "")
        boss_name = self.game.data.enemies.get(boss_id, {}).get("name", boss_id)
        player_level = self.game.player.get("level", 0) if self.game.player else 0
        unlock_level = dungeon.get("unlock_level", 1)
        status = "Locked" if player_level < unlock_level else "Ready"
        lines = [
            dungeon.get("name", dungeon_id),
            f"Unlock: Level {unlock_level}",
            dungeon.get("description", ""),
            f"Boss: {boss_name}",
            f"Boss scaling: +{dungeon.get('scaling_rate', 0) * 100:.0f}%",
            f"Reward scaling: +{dungeon.get('reward_multiplier_per_victory', 0) * 100:.0f}%",
            f"Route length: {len(dungeon.get('route', []))}",
            f"Status: {status}",
        ]
        line_y = rect.y + 52
        for line in lines:
            text = self.body_font.render(
                self._truncate_text(line, self.body_font, rect.w - 28),
                True,
                (210, 220, 205),
            )
            screen.blit(text, (rect.x + 14, line_y))
            line_y += 28

    def _can_start_selected_dungeon(self):
        if not self.selected_dungeon_id or not self.game.player:
            return False
        dungeon = self._get_dungeon_data(self.selected_dungeon_id)
        if not dungeon:
            return False
        return self.game.player.get("level", 0) >= dungeon.get("unlock_level", 1)

    def _get_dungeon_data(self, dungeon_id):
        dungeons = getattr(self.game.data, "dungeons", {}) or {}
        if not dungeon_id or not isinstance(dungeons, dict):
            return {}
        dungeon = dungeons.get(dungeon_id, {})
        return dungeon if isinstance(dungeon, dict) else {}

    def _get_dungeon_start_failure_message(self, reason):
        messages = {
            "invalid_player": "No player",
            "unknown_dungeon": "Unknown dungeon",
            "locked_dungeon": "Dungeon locked",
        }
        return messages.get(reason, "Could not start dungeon")

    def _draw_gathering_tab(self, screen, region_id):
        actions = self._get_region_gathering_actions(region_id)
        self.gathering_page = self._clamp_page(
            self.gathering_page,
            max(1, (len(actions) + 5) // 6),
        )
        visible_actions, total_pages = self._paginate_items(
            actions,
            self.gathering_page,
            6,
        )
        if not self._selected_gathering_action_exists(actions):
            self.selected_gathering_action = None
        if self.selected_gathering_action is None and visible_actions:
            first = visible_actions[0]
            self.selected_gathering_action = {
                "zone_key": first["zone_key"],
                "profession_id": first["profession_id"],
            }

        self.gathering_action_buttons = []
        x, y = 60, 150
        for index, action in enumerate(visible_actions):
            profession_name = self._get_profession_name(action["profession_id"])
            zone_name = self._get_zone_name(action["zone_key"])
            rate = format_tick_rate(action["node_data"].get("tick_seconds", 5))
            title = profession_name
            subtitle = f"{zone_name} | {rate}"
            button = MenuButton((x, y + index * 60, 330, 52), title, subtitle)
            self.gathering_action_buttons.append((action, button))
            button.draw(screen, self.body_font, self.body_font)
            if self._is_selected_gathering_action(action):
                pygame.draw.rect(screen, (210, 220, 145), button.rect, 3, border_radius=6)
            if self._is_active_gathering_action(action["zone_key"], action["profession_id"]):
                pygame.draw.rect(screen, (120, 210, 120), button.rect, 2, border_radius=6)

        self._draw_gathering_tab_detail(screen, self._get_zones_for_region(region_id))
        zone_key, profession_id = self._get_displayed_gathering_action(
            self._get_zones_for_region(region_id),
        )
        is_active = bool(zone_key and profession_id and self._is_active_gathering_action(zone_key, profession_id))
        self.gathering_online_button.title = "Stop Online" if is_active else "Start Online"
        self.gathering_online_button.enabled = bool(zone_key and profession_id)
        self.gathering_offline_button.enabled = bool(zone_key and profession_id)
        self.gathering_online_button.draw(screen, self.body_font, self.body_font)
        self.gathering_offline_button.draw(screen, self.body_font, self.body_font)

        self._draw_small_nav_button(
            screen,
            self.gathering_page_prev_rect,
            "<",
            self.gathering_page > 0,
        )
        self._draw_small_nav_button(
            screen,
            self.gathering_page_next_rect,
            ">",
            self.gathering_page < total_pages - 1,
        )
        page_text = self.body_font.render(
            f"Page {self.gathering_page + 1} / {total_pages}",
            True,
            (190, 200, 205),
        )
        screen.blit(page_text, (120, 508))
        self._draw_gathering_popups(screen, 420, 532)

    def _draw_gathering_tab_detail(self, screen, region_zones):
        rect = pygame.Rect(420, 150, 310, 300)
        pygame.draw.rect(screen, (35, 40, 48), rect, border_radius=6)
        pygame.draw.rect(screen, (120, 130, 140), rect, 2, border_radius=6)
        title = self.option_font.render("Gathering", True, (245, 245, 245))
        screen.blit(title, (rect.x + 14, rect.y + 14))

        zone_key, profession_id = self._get_displayed_gathering_action(region_zones)
        if not zone_key or not profession_id:
            text = self.body_font.render("Select a gathering action", True, (150, 155, 160))
            screen.blit(text, (rect.x + 14, rect.y + 58))
            return

        node_data = self._get_gathering_node_data(zone_key, profession_id)
        profession_name = self._get_profession_name(profession_id)
        node_name = node_data.get("name", "Gathering node")
        rate = format_tick_rate(node_data.get("tick_seconds", 5))
        mastery = 0
        if self.game.player:
            mastery = get_profession_mastery(
                self.game.player,
                profession_id,
                self.game.data.professions,
            )
        lines = [
            f"{profession_name} - {node_name}",
            f"Zone: {self._get_zone_name(zone_key)}",
            f"Rate: {rate}",
            f"Mastery: {mastery}",
            f"Rewards: {self._get_node_reward_preview(node_data)}",
            self._format_recent_gathering_summary(getattr(self.game, "last_gathering_result", None)),
            "Offline: already active" if self._has_offline_activity() else "Press O: send offline",
        ]
        if self._is_active_gathering_action(zone_key, profession_id):
            remaining_ms = 0
            if hasattr(self.game, "get_active_gathering_remaining_ms"):
                remaining_ms = self.game.get_active_gathering_remaining_ms(
                    pygame.time.get_ticks(),
                )
            lines.insert(4, f"Next: {self._format_remaining_time(remaining_ms)}")

        line_y = rect.y + 54
        for line in lines[:9]:
            text = self.body_font.render(
                self._truncate_text(line, self.body_font, rect.w - 28),
                True,
                (210, 220, 205),
            )
            screen.blit(text, (rect.x + 14, line_y))
            line_y += 25

    def _selected_gathering_action_exists(self, actions):
        action = self.selected_gathering_action
        if not isinstance(action, dict):
            return False
        return any(
            candidate["zone_key"] == action.get("zone_key")
            and candidate["profession_id"] == action.get("profession_id")
            for candidate in actions
        )

    def _is_selected_gathering_action(self, action):
        selected = self.selected_gathering_action
        return (
            isinstance(selected, dict)
            and selected.get("zone_key") == action.get("zone_key")
            and selected.get("profession_id") == action.get("profession_id")
        )

    def _start_selected_gathering_offline(self):
        activity = getattr(self.game, "active_gathering", None)
        if isinstance(activity, dict):
            zone_key = activity.get("zone_id")
            profession_id = activity.get("profession_id")
        else:
            action = self.selected_gathering_action
            if not isinstance(action, dict):
                self._add_gathering_popup_text(
                    "Select a gathering action first",
                    "failure",
                )
                return False
            zone_key = action.get("zone_key")
            profession_id = action.get("profession_id")

        if not hasattr(self.game, "send_current_player_offline_gathering"):
            self._add_gathering_popup_text("Offline unavailable", "failure")
            return False

        result = self.game.send_current_player_offline_gathering(
            zone_key,
            profession_id,
        )
        if result.get("started") is True:
            self._add_gathering_popup_text("Offline gathering started", "success")
            return True

        messages = {
            "activity_already_active": "Offline activity already active",
            "unknown_node": "No gathering node",
            "locked_zone": "Zone locked",
            "invalid_zone": "Invalid zone",
            "invalid_player": "No player",
        }
        self._add_gathering_popup_text(
            messages.get(result.get("reason"), "Offline gathering failed"),
            "failure",
        )
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
            for profession_id, node_data in self.game.get_available_gathering_professions(zone_key).items():
                if visible_count >= 4:
                    return
                profession_name = self._get_profession_name(profession_id)
                node_name = node_data.get("name", "Gathering node")
                mastery = 0
                if self.game.player:
                    mastery = get_profession_mastery(
                        self.game.player,
                        profession_id,
                        self.game.data.professions,
                    )
                is_active = self._is_active_gathering_action(zone_key, profession_id)
                action_label = "Stop" if is_active else "Start"
                title = f"{action_label} {profession_name}"
                rate = format_tick_rate(node_data.get("tick_seconds", 5))
                subtitle = f"{node_name} | {rate} | M:{mastery}"
                button = MenuButton((x, button_y, 320, 44), title, subtitle)
                self.gathering_action_buttons.append((zone_key, profession_id, button))
                button.draw(screen, self.body_font, self.body_font)
                if is_active:
                    pygame.draw.rect(screen, (170, 210, 120), button.rect, 3, border_radius=6)
                button_y += 50
                visible_count += 1

        if visible_count == 0:
            empty_text = self.body_font.render("No gathering node", True, (145, 145, 150))
            screen.blit(empty_text, (x, button_y))

    def _draw_gathering_detail_panel(self, screen, region_zones, x, y, width, height):
        panel = pygame.Rect(x, y, width, height)
        activity = getattr(self.game, "active_gathering", None)
        is_active = isinstance(activity, dict)
        border = (170, 210, 120) if is_active else (120, 130, 140)
        pygame.draw.rect(screen, (35, 40, 48), panel, border_radius=6)
        pygame.draw.rect(screen, border, panel, 2, border_radius=6)

        zone_key, profession_id = self._get_displayed_gathering_action(region_zones)
        title = "Active Gathering" if is_active else "Gathering Preview"
        title_text = self.body_font.render(title, True, (245, 245, 245))
        screen.blit(title_text, (panel.x + 14, panel.y + 12))

        if zone_key is None or profession_id is None:
            empty_text = self.body_font.render("Select a gathering action", True, (150, 155, 160))
            screen.blit(empty_text, (panel.x + 14, panel.y + 46))
            return

        node_data = self._get_gathering_node_data(zone_key, profession_id)
        profession_name = self._get_profession_name(profession_id)
        node_name = node_data.get("name", "Gathering node")
        zone_name = self._get_zone_name(zone_key)
        rate = format_tick_rate(node_data.get("tick_seconds", 5))
        mastery = 0
        if self.game.player:
            mastery = get_profession_mastery(
                self.game.player,
                profession_id,
                self.game.data.professions,
            )

        left_lines = [
            f"{profession_name} - {node_name}",
            f"Zone: {zone_name}",
            f"Rate: {rate}",
            f"Mastery: {mastery}",
        ]
        if is_active:
            remaining_ms = 0
            if hasattr(self.game, "get_active_gathering_remaining_ms"):
                remaining_ms = self.game.get_active_gathering_remaining_ms(
                    pygame.time.get_ticks(),
                )
            left_lines[2] = f"Rate: {rate} | Next: {self._format_remaining_time(remaining_ms)}"

        right_lines = [
            f"Rewards: {self._get_node_reward_preview(node_data)}",
            self._format_recent_gathering_summary(self.game.last_gathering_result),
            "Offline: already active" if self._has_offline_activity() else "Press O: send offline",
        ]

        line_y = panel.y + 42
        for line in left_lines:
            text = self.body_font.render(
                self._truncate_text(line, self.body_font, 320),
                True,
                (210, 220, 205),
            )
            screen.blit(text, (panel.x + 14, line_y))
            line_y += 22

        line_y = panel.y + 42
        for line in right_lines:
            text = self.body_font.render(
                self._truncate_text(line, self.body_font, 300),
                True,
                (210, 220, 205),
            )
            screen.blit(text, (panel.x + 350, line_y))
            line_y += 24

    def _is_active_gathering_action(self, zone_key, profession_id):
        activity = getattr(self.game, "active_gathering", None)
        return (
            isinstance(activity, dict)
            and activity.get("zone_id") == zone_key
            and activity.get("profession_id") == profession_id
        )

    def _has_offline_activity(self):
        player = getattr(self.game, "player", None)
        return isinstance(player, dict) and isinstance(
            player.get("offline_activity"),
            dict,
        )

    def _format_remaining_time(self, remaining_ms):
        if remaining_ms <= 0:
            return "Ready"
        seconds = max(1, int((remaining_ms + 999) / 1000))
        return f"{seconds}s"

    def _get_displayed_gathering_action(self, region_zones):
        activity = getattr(self.game, "active_gathering", None)
        if isinstance(activity, dict):
            return activity.get("zone_id"), activity.get("profession_id")

        action = self.selected_gathering_action
        if isinstance(action, dict) and action.get("zone_key") in region_zones:
            return action.get("zone_key"), action.get("profession_id")
        return None, None

    def _get_gathering_node_data(self, zone_key, profession_id):
        if not hasattr(self.game, "get_available_gathering_professions"):
            return {}
        zone_nodes = self.game.get_available_gathering_professions(zone_key)
        if not isinstance(zone_nodes, dict):
            return {}
        node_data = zone_nodes.get(profession_id, {})
        return node_data if isinstance(node_data, dict) else {}

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
                "duration_ms": 1200,
            })

    def _add_gathering_popup_text(self, text, popup_type="failure"):
        self.gathering_popups.append({
            "text": text,
            "type": popup_type,
            "created_at": pygame.time.get_ticks(),
            "duration_ms": 1200,
        })

    def _draw_gathering_popups(self, screen, x, y):
        current_time = pygame.time.get_ticks()
        self.gathering_popups = [
            popup
            for popup in self.gathering_popups
            if current_time - popup.get("created_at", 0) <= popup.get("duration_ms", 0)
        ]

        for index, popup in enumerate(self.gathering_popups[-3:]):
            popup_y = y + index * 18
            if popup_y > 575:
                break
            color = (125, 220, 145) if popup.get("type") == "success" else (230, 160, 90)
            popup_text = self._truncate_text(popup.get("text", ""), self.body_font, 310)
            text = self.body_font.render(popup_text, True, color)
            screen.blit(text, (x, popup_y))

    def _get_zone_name(self, zone_key):
        zone = self.game.data.zones.get(zone_key, {})
        if isinstance(zone, dict):
            return zone.get("name", zone_key or "Unknown zone")
        return zone_key or "Unknown zone"

    def _get_zone_enemy_label(self, zone_key):
        zone = self.game.data.zones.get(zone_key, {})
        zone_name = zone.get("name", zone_key)
        region_id = self._get_zone_region_id(zone_key)
        region_label = REGION_LABELS.get(region_id, "")
        return zone_name.replace(region_label, "").strip() or zone_name

    def _get_node_reward_preview(self, node_data):
        rewards = []
        if not isinstance(node_data, dict):
            return "Unknown rewards"
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

    def _format_recent_gathering_summary(self, result):
        if not isinstance(result, dict):
            return "Recent: -"
        if result.get("gathered") is not True:
            if result.get("reason") == "inventory_full":
                return "Recent: Inventory full. Stopped."
            return f"Recent: {self._get_gathering_failure_message(result.get('reason'))}"

        parts = []
        for reward in result.get("rewards", []):
            item_name = self._get_item_name(reward.get("item"))
            quantity = reward.get("quantity", 1)
            parts.append(f"+{quantity} {item_name}")
        xp_gain = result.get("profession_xp", 0)
        if xp_gain:
            profession_name = self._get_profession_name(result.get("profession_id"))
            parts.append(f"+{xp_gain} {profession_name} XP")
        if result.get("leveled_up"):
            parts.append("Level up!")
        if not parts:
            return "Recent: -"
        visible_parts = parts[:2]
        if len(parts) > 2:
            visible_parts.append(f"+{len(parts) - 2} more")
        return f"Recent: {', '.join(visible_parts)}"

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

    def _short_line(self, text, max_length):
        text = str(text)
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

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
