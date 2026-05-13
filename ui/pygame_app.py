import pygame
from core.game import Game
from ui.screens.achievements_screen import AchievementsScreen
from ui.screens.combat_screen import CombatScreen
from ui.screens.crafting_screen import CraftingScreen
from ui.screens.dungeon_screen import DungeonScreen
from ui.screens.exploration_screen import ExplorationScreen
from ui.screens.inventory_screen import InventoryScreen
from ui.screens.mailbox_screen import MailboxScreen
from ui.screens.main_menu_screen import MainMenuScreen
from ui.screens.merchant_screen import MerchantScreen
from ui.screens.menu_screen import MenuScreen
from ui.screens.professions_screen import ProfessionsScreen
from ui.screens.quests_screen import QuestScreen
from ui.screens.result_screen import ResultScreen
from ui.screens.skills_screen import SkillsScreen


class PygameApp:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("My First Game")

        self.clock = pygame.time.Clock()
        self.running = True

        self.game = Game()
        self.main_menu_screen = MainMenuScreen(self.game, self)
        self.menu_screen = MenuScreen(self.game)
        self.combat_screen = CombatScreen(self.game)
        self.result_screen = ResultScreen(self.game)
        self.inventory_screen = InventoryScreen(self.game)
        self.crafting_screen = CraftingScreen(self.game)
        self.dungeon_screen = DungeonScreen(self.game)
        self.exploration_screen = ExplorationScreen(self.game)
        self.merchant_screen = MerchantScreen(self.game)
        self.skills_screen = SkillsScreen(self.game)
        self.mailbox_screen = MailboxScreen(self.game)
        self.professions_screen = ProfessionsScreen(self.game)
        self.quests_screen = QuestScreen(self.game)
        self.achievements_screen = AchievementsScreen(self.game)
        self.achievement_toast_ids = []
        self.achievement_toast_started_at = 0
        self.achievement_toast_duration_ms = 3800
        self.achievement_toast_font = pygame.font.Font(None, 22)
        self.achievement_toast_title_font = pygame.font.Font(None, 24)

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)

        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if self.game.state == "main_menu":
                self.main_menu_screen.handle_event(event)
            elif self.game.state in ("class_select", "town", "zone_select", "zone_actions"):
                self.menu_screen.handle_event(event)
            elif self.game.state == "combat":
                self.combat_screen.handle_event(event)
            elif self.game.state == "combat_result":
                self.result_screen.handle_event(event)
            elif self.game.state == "inventory":
                self.inventory_screen.handle_event(event)
            elif self.game.state == "crafting":
                self.crafting_screen.handle_event(event)
            elif self.game.state == "dungeon":
                self.dungeon_screen.handle_event(event)
            elif self.game.state == "exploration":
                self.exploration_screen.handle_event(event)
            elif self.game.state == "merchant":
                self.merchant_screen.handle_event(event)
            elif self.game.state == "skills":
                self.skills_screen.handle_event(event)
            elif self.game.state == "professions":
                self.professions_screen.handle_event(event)
            elif self.game.state == "quests":
                self.quests_screen.handle_event(event)
            elif self.game.state == "achievements":
                self.achievements_screen.handle_event(event)
            elif self.game.state == "mailbox":
                self.mailbox_screen.handle_event(event)

    def update(self):
        if self.game.state == "combat":
            self.combat_screen.update()
        if self.game.state == "zone_actions":
            current_time_ms = pygame.time.get_ticks()
            result = self.game.update_active_gathering(current_time_ms)
            if result is not None and hasattr(self.menu_screen, "add_gathering_popup"):
                self.menu_screen.add_gathering_popup(result)

    def render(self):
        current_time_ms = pygame.time.get_ticks()
        if self.game.state == "main_menu":
            self.main_menu_screen.draw(self.screen)
        elif self.game.state in ("class_select", "town", "zone_select", "zone_actions"):
            self.menu_screen.draw(self.screen)
        elif self.game.state == "combat":
            self.combat_screen.draw(self.screen)
        elif self.game.state == "combat_result":
            self.result_screen.draw(self.screen)
        elif self.game.state == "inventory":
            self.inventory_screen.draw(self.screen)
        elif self.game.state == "crafting":
            self.crafting_screen.draw(self.screen)
        elif self.game.state == "dungeon":
            self.dungeon_screen.draw(self.screen)
        elif self.game.state == "exploration":
            self.exploration_screen.draw(self.screen)
        elif self.game.state == "merchant":
            self.merchant_screen.draw(self.screen)
        elif self.game.state == "skills":
            self.skills_screen.draw(self.screen)
        elif self.game.state == "professions":
            self.professions_screen.draw(self.screen)
        elif self.game.state == "quests":
            self.quests_screen.draw(self.screen)
        elif self.game.state == "achievements":
            self.achievements_screen.draw(self.screen)
        elif self.game.state == "mailbox":
            self.mailbox_screen.draw(self.screen)

        self._sync_achievement_toast(current_time_ms)
        self._draw_achievement_toast(self.screen, current_time_ms)
        pygame.display.flip()

    def _sync_achievement_toast(self, current_time_ms):
        player = getattr(self.game, "player", None)
        if not isinstance(player, dict):
            return
        achievements = player.get("achievements")
        if not isinstance(achievements, dict):
            return
        last_unlocked = achievements.get("last_unlocked")
        if not isinstance(last_unlocked, list) or not last_unlocked:
            return

        self.achievement_toast_ids = list(last_unlocked)
        self.achievement_toast_started_at = current_time_ms
        achievements["last_unlocked"] = []
        if hasattr(self.game, "save_current_game"):
            self.game.save_current_game()

    def _draw_achievement_toast(self, screen, current_time_ms):
        if not self.achievement_toast_ids:
            return
        elapsed = current_time_ms - self.achievement_toast_started_at
        if elapsed > self.achievement_toast_duration_ms:
            self.achievement_toast_ids = []
            return

        achievement_id = self.achievement_toast_ids[0]
        achievement_name = self._get_achievement_name(achievement_id)
        rect = pygame.Rect(470, 112, 280, 76)
        pygame.draw.rect(screen, (46, 39, 30), rect, border_radius=8)
        pygame.draw.rect(screen, (228, 196, 105), rect, 2, border_radius=8)

        icon_center = (rect.x + 24, rect.y + 26)
        pygame.draw.circle(screen, (255, 218, 96), icon_center, 10)
        pygame.draw.circle(screen, (255, 244, 190), icon_center, 4)

        title = self.achievement_toast_title_font.render(
            "Achievement unlocked",
            True,
            (255, 240, 190),
        )
        screen.blit(title, (rect.x + 44, rect.y + 14))

        name = self.achievement_toast_font.render(
            self._truncate_text(achievement_name, self.achievement_toast_font, rect.w - 58),
            True,
            (242, 242, 232),
        )
        screen.blit(name, (rect.x + 44, rect.y + 38))

        remaining_count = len(self.achievement_toast_ids) - 1
        if remaining_count > 0:
            more = self.achievement_toast_font.render(
                f"+{remaining_count} more",
                True,
                (205, 214, 205),
            )
            screen.blit(more, (rect.x + 44, rect.y + 56))

    def _get_achievement_name(self, achievement_id):
        achievements = getattr(getattr(self.game, "data", None), "achievements", {})
        achievement = achievements.get(achievement_id, {}) if isinstance(achievements, dict) else {}
        if isinstance(achievement, dict) and achievement.get("name"):
            return achievement["name"]
        return str(achievement_id or "unknown").replace("_", " ").title()

    def _truncate_text(self, text, font, max_width):
        text = str(text or "")
        if max_width <= 0:
            return ""
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        while text and font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]
        return text + ellipsis if text else ellipsis
