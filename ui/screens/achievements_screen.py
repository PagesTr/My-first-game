import pygame


CATEGORIES = [
    ("all", "All"),
    ("combat", "Combat"),
    ("gathering", "Gathering"),
    ("craft", "Craft"),
    ("sets", "Sets"),
    ("dungeons", "Dungeons"),
    ("boss", "Boss"),
    ("run", "Run"),
]


class AchievementsScreen:
    def __init__(self, game):
        if not pygame.font.get_init():
            pygame.font.init()

        self.game = game
        self.selected_category = "all"
        self.selected_achievement_id = None
        self.page = 0
        self.title_font = pygame.font.Font(None, 42)
        self.header_font = pygame.font.Font(None, 28)
        self.body_font = pygame.font.Font(None, 22)
        self.small_font = pygame.font.Font(None, 19)
        self.back_rect = pygame.Rect(650, 30, 100, 42)
        self.list_rect = pygame.Rect(40, 140, 330, 370)
        self.detail_rect = pygame.Rect(390, 140, 360, 370)
        self.prev_rect = pygame.Rect(40, 525, 44, 34)
        self.next_rect = pygame.Rect(326, 525, 44, 34)
        self.category_rects = []
        self.row_rects = []

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        pos = event.pos
        if self.back_rect.collidepoint(pos):
            self.game.state = "town"
            return

        for category_id, rect in self.category_rects:
            if rect.collidepoint(pos):
                self.selected_category = category_id
                self.selected_achievement_id = None
                self.page = 0
                return

        achievements = self._get_filtered_achievements()
        total_pages = self._get_total_pages(achievements)
        if self.prev_rect.collidepoint(pos) and self.page > 0:
            self.page -= 1
            self.selected_achievement_id = None
            return
        if self.next_rect.collidepoint(pos) and self.page < total_pages - 1:
            self.page += 1
            self.selected_achievement_id = None
            return

        for achievement_id, rect in self.row_rects:
            if rect.collidepoint(pos):
                self.selected_achievement_id = achievement_id
                return

    def draw(self, screen):
        screen.fill((18, 24, 30))
        title = self.title_font.render("Achievements", True, (245, 245, 245))
        screen.blit(title, (40, 30))

        self._draw_button(screen, self.back_rect, "Back", False)
        self._draw_category_tabs(screen)
        self._draw_achievement_list(screen)
        self._draw_selected_achievement(screen)

    def _get_player_achievements(self):
        player = getattr(self.game, "player", None)
        if not isinstance(player, dict):
            return {"unlocked": [], "progress": {}, "last_unlocked": []}
        achievements = player.get("achievements")
        if not isinstance(achievements, dict):
            return {"unlocked": [], "progress": {}, "last_unlocked": []}
        return {
            "unlocked": achievements.get("unlocked", [])
            if isinstance(achievements.get("unlocked"), list)
            else [],
            "progress": achievements.get("progress", {})
            if isinstance(achievements.get("progress"), dict)
            else {},
            "last_unlocked": achievements.get("last_unlocked", [])
            if isinstance(achievements.get("last_unlocked"), list)
            else [],
        }

    def _get_filtered_achievements(self):
        data = getattr(getattr(self.game, "data", None), "achievements", {})
        if not isinstance(data, dict):
            return []

        achievements = []
        for achievement_id, achievement in data.items():
            if not isinstance(achievement, dict):
                continue
            category = achievement.get("category", "")
            if self.selected_category != "all" and category != self.selected_category:
                continue
            achievements.append((achievement_id, achievement))

        achievements.sort(
            key=lambda item: (
                item[1].get("chapter", ""),
                item[1].get("category", ""),
                item[1].get("tier", 0),
                item[0],
            )
        )
        return achievements

    def _get_achievement_progress(self, achievement_id):
        progress = self._get_player_achievements().get("progress", {})
        value = progress.get(achievement_id, 0)
        return value if isinstance(value, int) else 0

    def _is_unlocked(self, achievement_id):
        return achievement_id in self._get_player_achievements().get("unlocked", [])

    def _get_progress_summary(self, achievement_id, achievement):
        objective = achievement.get("objective", {}) if isinstance(achievement, dict) else {}
        required = objective.get("required", 0)
        if not isinstance(required, int) or required < 0:
            required = 0
        current = required if self._is_unlocked(achievement_id) else self._get_achievement_progress(achievement_id)
        current = max(0, min(current, required))
        return current, required

    def _draw_category_tabs(self, screen):
        self.category_rects = []
        x = 40
        y = 85
        for category_id, label in CATEGORIES:
            width = max(64, self.body_font.size(label)[0] + 22)
            if x + width > 750:
                x = 40
                y += 42
            rect = pygame.Rect(x, y, width, 32)
            self.category_rects.append((category_id, rect))
            self._draw_button(screen, rect, label, category_id == self.selected_category)
            x += width + 8

    def _draw_achievement_list(self, screen):
        pygame.draw.rect(screen, (31, 38, 46), self.list_rect, border_radius=6)
        pygame.draw.rect(screen, (100, 112, 124), self.list_rect, 2, border_radius=6)

        achievements = self._get_filtered_achievements()
        total_pages = self._get_total_pages(achievements)
        self.page = max(0, min(self.page, total_pages - 1))
        page_items = achievements[self.page * 8:(self.page + 1) * 8]

        valid_ids = {achievement_id for achievement_id, _ in achievements}
        if self.selected_achievement_id not in valid_ids:
            self.selected_achievement_id = page_items[0][0] if page_items else None

        self.row_rects = []
        y = self.list_rect.y + 12
        for achievement_id, achievement in page_items:
            row = pygame.Rect(self.list_rect.x + 10, y, self.list_rect.w - 20, 40)
            self.row_rects.append((achievement_id, row))
            selected = achievement_id == self.selected_achievement_id
            pygame.draw.rect(screen, (58, 70, 84) if selected else (38, 46, 55), row, border_radius=5)

            unlocked = self._is_unlocked(achievement_id)
            hidden = achievement.get("hidden", False) and not unlocked
            marker = "✓" if unlocked else "○"
            name = "Hidden achievement" if hidden else achievement.get("name", achievement_id)
            current, required = self._get_progress_summary(achievement_id, achievement)
            line = f"{marker} {name}"
            progress = f"{current}/{required}"

            text = self.body_font.render(
                self._truncate_text(line, self.body_font, row.w - 78),
                True,
                (235, 240, 235) if unlocked else (205, 212, 218),
            )
            screen.blit(text, (row.x + 8, row.y + 8))
            progress_text = self.small_font.render(progress, True, (170, 185, 195))
            screen.blit(progress_text, (row.right - progress_text.get_width() - 8, row.y + 11))
            y += 44

        page_label = self.body_font.render(f"Page {self.page + 1} / {total_pages}", True, (190, 200, 205))
        screen.blit(page_label, (96, 532))
        self._draw_button(screen, self.prev_rect, "<", False, self.page > 0)
        self._draw_button(screen, self.next_rect, ">", False, self.page < total_pages - 1)

    def _draw_selected_achievement(self, screen):
        pygame.draw.rect(screen, (31, 38, 46), self.detail_rect, border_radius=6)
        pygame.draw.rect(screen, (100, 112, 124), self.detail_rect, 2, border_radius=6)

        achievements = dict(self._get_filtered_achievements())
        achievement = achievements.get(self.selected_achievement_id)
        if not isinstance(achievement, dict):
            text = self.body_font.render("No achievement selected", True, (160, 168, 176))
            screen.blit(text, (self.detail_rect.x + 16, self.detail_rect.y + 18))
            return

        unlocked = self._is_unlocked(self.selected_achievement_id)
        hidden = achievement.get("hidden", False) and not unlocked
        current, required = self._get_progress_summary(self.selected_achievement_id, achievement)
        status = "Unlocked" if unlocked else "Hidden" if hidden else "In progress"
        mood = "Claimed. The forest is pretending not to care."
        if hidden:
            mood = "This one is still lurking behind the bushes."
        elif not unlocked:
            mood = "Progress is being made. Allegedly."

        x = self.detail_rect.x + 16
        y = self.detail_rect.y + 16
        name = "Hidden achievement" if hidden else achievement.get("name", self.selected_achievement_id)
        title = self.header_font.render(self._truncate_text(name, self.header_font, self.detail_rect.w - 32), True, (245, 245, 245))
        screen.blit(title, (x, y))
        y += 34

        meta = f"{status} | {achievement.get('category', 'unknown').title()} | Tier {achievement.get('tier', 0)}"
        self._draw_line(screen, meta, x, y, (190, 202, 210))
        y += 28

        if hidden:
            detail_lines = ["Description: Hidden", "Objective: Hidden"]
        else:
            detail_lines = [
                achievement.get("description", ""),
                self._format_objective(achievement),
            ]
        for line in detail_lines:
            y = self._draw_wrapped_text(screen, line, x, y, self.detail_rect.w - 32, (210, 218, 220))
            y += 4

        progress_text = f"Progress: {current} / {required}"
        self._draw_line(screen, progress_text, x, y, (220, 220, 170))
        y += 24
        self._draw_progress_bar(screen, pygame.Rect(x, y, self.detail_rect.w - 32, 16), current, required)
        y += 30

        rewards_title = self.body_font.render("Rewards", True, (245, 245, 245))
        screen.blit(rewards_title, (x, y))
        y += 24
        rewards = achievement.get("rewards", [])
        if not isinstance(rewards, list):
            rewards = []
        for reward in rewards[:4]:
            self._draw_line(screen, self._format_reward(reward), x, y, (205, 220, 190))
            y += 22

        y = max(y + 6, self.detail_rect.bottom - 52)
        self._draw_wrapped_text(screen, mood, x, y, self.detail_rect.w - 32, (165, 178, 188))

    def _draw_progress_bar(self, screen, rect, current, required):
        pygame.draw.rect(screen, (20, 24, 28), rect, border_radius=5)
        ratio = 0 if required <= 0 else max(0, min(current / required, 1))
        fill = pygame.Rect(rect.x, rect.y, int(rect.w * ratio), rect.h)
        if fill.w > 0:
            pygame.draw.rect(screen, (120, 178, 104), fill, border_radius=5)
        pygame.draw.rect(screen, (130, 140, 148), rect, 1, border_radius=5)

    def _format_objective(self, achievement):
        objective = achievement.get("objective", {}) if isinstance(achievement, dict) else {}
        objective_type = objective.get("type", "unknown")
        target = objective.get("target", "unknown")
        required = objective.get("required", 0)
        name = self._resolve_target_name(objective_type, target)
        formats = {
            "kill_enemy": f"Kill {name}: {required}",
            "kill_family": f"Kill {name} family: {required}",
            "gather_profession": f"Gather with {name}: {required}",
            "gather_item": f"Gather {name}: {required}",
            "craft_recipe": f"Craft {name}: {required}",
            "craft_chapter": f"Craft {name.title()} recipes: {required}",
            "clear_dungeon": f"Clear {name}: {required}",
            "defeat_boss": f"Defeat {name}: {required}",
            "boss_victory_count": f"Boss victories against {name}: {required}",
            "equip_set_pieces": f"Equip set pieces: {required}",
            "single_expedition_kills": f"Best expedition in {name}: {required} kills",
            "single_dungeon_kills": f"Best dungeon run in {name}: {required} kills",
            "single_boss_victories": f"Best boss loop against {name}: {required} victories",
        }
        return formats.get(objective_type, f"{objective_type}: {name} {required}")

    def _format_reward(self, reward):
        if not isinstance(reward, dict):
            return "Unknown reward"
        reward_type = reward.get("type")
        amount = reward.get("amount", reward.get("quantity", 1))
        if reward_type == "gold":
            return f"+{amount} gold"
        if reward_type == "item":
            return f"+{reward.get('quantity', 1)} {self._get_item_name(reward.get('item'))}"
        if reward_type == "stat_bonus":
            return f"+{amount} {reward.get('stat', 'stat')}"
        if reward_type == "percent_bonus":
            percent = int(round(float(amount) * 100)) if isinstance(amount, (int, float)) else amount
            return f"+{percent}% {reward.get('stat', 'bonus')}"
        return "Unknown reward"

    def _truncate_text(self, text, font, max_width):
        text = str(text or "")
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        while text and font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]
        return text + ellipsis if text else ellipsis

    def _draw_button(self, screen, rect, label, active=False, enabled=True):
        bg = (78, 92, 72) if active else (58, 68, 78) if enabled else (42, 46, 50)
        border = (210, 220, 145) if active else (180, 190, 195) if enabled else (90, 96, 102)
        color = (245, 245, 245) if enabled else (130, 136, 142)
        pygame.draw.rect(screen, bg, rect, border_radius=6)
        pygame.draw.rect(screen, border, rect, 2, border_radius=6)
        text = self.body_font.render(label, True, color)
        screen.blit(text, text.get_rect(center=rect.center))

    def _draw_line(self, screen, text, x, y, color):
        line = self.body_font.render(
            self._truncate_text(text, self.body_font, self.detail_rect.w - 32),
            True,
            color,
        )
        screen.blit(line, (x, y))

    def _draw_wrapped_text(self, screen, text, x, y, max_width, color):
        words = str(text or "").split()
        if not words:
            return y
        line = ""
        for word in words:
            candidate = word if not line else f"{line} {word}"
            if self.body_font.size(candidate)[0] <= max_width:
                line = candidate
                continue
            rendered = self.body_font.render(line, True, color)
            screen.blit(rendered, (x, y))
            y += 21
            line = word
        if line:
            rendered = self.body_font.render(self._truncate_text(line, self.body_font, max_width), True, color)
            screen.blit(rendered, (x, y))
            y += 21
        return y

    def _get_total_pages(self, achievements):
        return max(1, (len(achievements) + 7) // 8)

    def _resolve_target_name(self, objective_type, target):
        data = getattr(self.game, "data", None)
        if data is None:
            return self._humanize_id(target)
        maps = {
            "kill_enemy": getattr(data, "enemies", {}),
            "defeat_boss": getattr(data, "enemies", {}),
            "boss_victory_count": getattr(data, "enemies", {}),
            "single_boss_victories": getattr(data, "enemies", {}),
            "gather_item": getattr(data, "items", {}),
            "craft_recipe": getattr(data, "recipes", {}),
            "clear_dungeon": getattr(data, "dungeons", {}),
            "single_dungeon_kills": getattr(data, "dungeons", {}),
            "single_expedition_kills": getattr(data, "zones", {}),
            "equip_set_pieces": getattr(data, "equipment_sets", {}),
        }
        source = maps.get(objective_type, {})
        entry = source.get(target, {}) if isinstance(source, dict) else {}
        if isinstance(entry, dict) and entry.get("name"):
            return entry["name"]
        return self._humanize_id(target)

    def _get_item_name(self, item_id):
        items = getattr(getattr(self.game, "data", None), "items", {})
        item = items.get(item_id, {}) if isinstance(items, dict) else {}
        if isinstance(item, dict):
            return item.get("name", self._humanize_id(item_id))
        return self._humanize_id(item_id)

    def _humanize_id(self, value):
        return str(value or "unknown").replace("_", " ").title()
