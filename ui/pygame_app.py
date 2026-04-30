import pygame
from core.game import Game
from ui.screens.combat_screen import CombatScreen
from ui.screens.crafting_screen import CraftingScreen
from ui.screens.inventory_screen import InventoryScreen
from ui.screens.merchant_screen import MerchantScreen
from ui.screens.menu_screen import MenuScreen
from ui.screens.result_screen import ResultScreen


class PygameApp:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("My First Game")

        self.clock = pygame.time.Clock()
        self.running = True

        self.game = Game()
        self.menu_screen = MenuScreen(self.game)
        self.combat_screen = CombatScreen(self.game)
        self.result_screen = ResultScreen(self.game)
        self.inventory_screen = InventoryScreen(self.game)
        self.crafting_screen = CraftingScreen(self.game)
        self.merchant_screen = MerchantScreen(self.game)

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

            if self.game.state in ("class_select", "zone_select"):
                self.menu_screen.handle_event(event)
            elif self.game.state == "combat":
                self.combat_screen.handle_event(event)
            elif self.game.state == "combat_result":
                self.result_screen.handle_event(event)
            elif self.game.state == "inventory":
                self.inventory_screen.handle_event(event)
            elif self.game.state == "crafting":
                self.crafting_screen.handle_event(event)
            elif self.game.state == "merchant":
                self.merchant_screen.handle_event(event)

    def update(self):
        if self.game.state == "combat":
            self.combat_screen.update()

    def render(self):
        if self.game.state in ("class_select", "zone_select"):
            self.menu_screen.draw(self.screen)
        elif self.game.state == "combat":
            self.combat_screen.draw(self.screen)
        elif self.game.state == "combat_result":
            self.result_screen.draw(self.screen)
        elif self.game.state == "inventory":
            self.inventory_screen.draw(self.screen)
        elif self.game.state == "crafting":
            self.crafting_screen.draw(self.screen)
        elif self.game.state == "merchant":
            self.merchant_screen.draw(self.screen)

        pygame.display.flip()
