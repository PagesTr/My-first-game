import pygame
from core.game import Game
from ui.screens.combat_screen import CombatScreen
from ui.screens.menu_screen import MenuScreen


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

    def update(self):
        if self.game.state == "combat":
            self.combat_screen.update()

    def render(self):
        if self.game.state in ("class_select", "zone_select"):
            self.menu_screen.draw(self.screen)
        elif self.game.state == "combat":
            self.combat_screen.draw(self.screen)

        pygame.display.flip()
