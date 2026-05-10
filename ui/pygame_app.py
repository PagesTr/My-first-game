import pygame
from core.game import Game
from ui.screens.combat_screen import CombatScreen
from ui.screens.crafting_screen import CraftingScreen
from ui.screens.dungeon_screen import DungeonScreen
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
        self.merchant_screen = MerchantScreen(self.game)
        self.skills_screen = SkillsScreen(self.game)
        self.mailbox_screen = MailboxScreen(self.game)
        self.professions_screen = ProfessionsScreen(self.game)
        self.quests_screen = QuestScreen(self.game)

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
            elif self.game.state == "merchant":
                self.merchant_screen.handle_event(event)
            elif self.game.state == "skills":
                self.skills_screen.handle_event(event)
            elif self.game.state == "professions":
                self.professions_screen.handle_event(event)
            elif self.game.state == "quests":
                self.quests_screen.handle_event(event)
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
        elif self.game.state == "merchant":
            self.merchant_screen.draw(self.screen)
        elif self.game.state == "skills":
            self.skills_screen.draw(self.screen)
        elif self.game.state == "professions":
            self.professions_screen.draw(self.screen)
        elif self.game.state == "quests":
            self.quests_screen.draw(self.screen)
        elif self.game.state == "mailbox":
            self.mailbox_screen.draw(self.screen)

        pygame.display.flip()
