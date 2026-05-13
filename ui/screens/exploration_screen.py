import pygame


class ExplorationScreen:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.Font(None, 34)
        self.body_font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.player_rect = pygame.Rect(382, 308, 24, 30)
        self.player_speed = 6
        self.npc_rect = pygame.Rect(548, 250, 28, 34)
        self.message = "Explore la clairiere. Fleches ou ZQSD pour bouger. E pres du PNJ. Echap pour rentrer."
        self.message_until_ms = 0
        self.obstacles = [
            pygame.Rect(180, 214, 74, 34),
            pygame.Rect(468, 178, 92, 30),
            pygame.Rect(308, 414, 112, 32),
            pygame.Rect(612, 382, 70, 38),
        ]
        self.trees = [
            (96, 132, 30),
            (158, 332, 36),
            (266, 118, 28),
            (648, 122, 34),
            (704, 302, 32),
            (88, 486, 34),
            (566, 474, 30),
        ]

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self.game.return_to_town()
            return

        if event.key == pygame.K_e and self.player_rect.colliderect(self.npc_rect.inflate(58, 58)):
            self.message = "Le garde forestier hoche la tete. Rien de dangereux a signaler. Pour l'instant."
            self.message_until_ms = pygame.time.get_ticks() + 2800
            return

    def update(self):
        keys = pygame.key.get_pressed()
        movement = pygame.Vector2(0, 0)
        if keys[pygame.K_LEFT] or keys[pygame.K_q]:
            movement.x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            movement.x += 1
        if keys[pygame.K_UP] or keys[pygame.K_z]:
            movement.y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            movement.y += 1

        if movement.length_squared() > 0:
            self._move_player(movement)

    def draw(self, screen):
        current_time_ms = pygame.time.get_ticks()
        self._draw_background(screen)
        self._draw_path(screen)
        self._draw_trees(screen)
        self._draw_obstacles(screen)
        self._draw_npc(screen)
        self._draw_player(screen)
        self._draw_help_panel(screen, current_time_ms)

    def _move_player(self, movement):
        movement = movement.normalize() * self.player_speed
        bounds = pygame.Rect(14, 14, 772, 518)
        candidate = self.player_rect.move(int(movement.x), int(movement.y))
        candidate.clamp_ip(bounds)

        if not self._collides_with_obstacle(candidate):
            self.player_rect = candidate
            return

        horizontal = self.player_rect.move(int(movement.x), 0)
        horizontal.clamp_ip(bounds)
        if not self._collides_with_obstacle(horizontal):
            self.player_rect = horizontal

        vertical = self.player_rect.move(0, int(movement.y))
        vertical.clamp_ip(bounds)
        if not self._collides_with_obstacle(vertical):
            self.player_rect = vertical

    def _collides_with_obstacle(self, candidate):
        return any(candidate.colliderect(obstacle) for obstacle in self.obstacles)

    def _draw_background(self, screen):
        screen.fill((23, 54, 35))
        for y in range(0, 548, 8):
            shade = 28 + int(y * 0.025)
            pygame.draw.rect(screen, (18, min(72, shade + 28), 35), (0, y, 800, 8))

    def _draw_path(self, screen):
        path_points = [
            (0, 362),
            (168, 326),
            (314, 342),
            (484, 294),
            (800, 318),
            (800, 452),
            (510, 424),
            (324, 458),
            (140, 430),
            (0, 470),
        ]
        pygame.draw.polygon(screen, (91, 78, 55), path_points)
        pygame.draw.lines(screen, (130, 112, 78), False, path_points[:5], 3)
        pygame.draw.lines(screen, (60, 52, 41), False, path_points[5:], 2)

    def _draw_trees(self, screen):
        for x, y, radius in self.trees:
            trunk = pygame.Rect(x - 6, y + radius - 8, 12, 34)
            pygame.draw.rect(screen, (74, 45, 28), trunk, border_radius=3)
            pygame.draw.circle(screen, (17, 77, 40), (x, y), radius)
            pygame.draw.circle(screen, (24, 96, 48), (x - 10, y - 8), max(10, radius - 10))
            pygame.draw.circle(screen, (12, 48, 30), (x + 12, y + 8), max(10, radius - 12))

    def _draw_obstacles(self, screen):
        for rect in self.obstacles:
            pygame.draw.rect(screen, (71, 58, 42), rect, border_radius=4)
            pygame.draw.rect(screen, (134, 112, 76), rect, 2, border_radius=4)
            pygame.draw.line(screen, (45, 36, 28), (rect.x + 8, rect.centery), (rect.right - 8, rect.centery), 2)

    def _draw_npc(self, screen):
        pygame.draw.ellipse(screen, (16, 33, 24), self.npc_rect.move(3, 8))
        pygame.draw.rect(screen, (79, 90, 58), self.npc_rect, border_radius=6)
        pygame.draw.circle(screen, (202, 171, 126), self.npc_rect.midtop, 9)
        label = self.small_font.render("PNJ", True, (230, 220, 185))
        screen.blit(label, (self.npc_rect.x - 5, self.npc_rect.y - 24))

    def _draw_player(self, screen):
        pygame.draw.ellipse(screen, (10, 25, 18), self.player_rect.move(3, 8))
        pygame.draw.rect(screen, (66, 122, 166), self.player_rect, border_radius=6)
        pygame.draw.circle(screen, (226, 188, 140), self.player_rect.midtop, 8)

    def _draw_help_panel(self, screen, current_time_ms):
        panel = pygame.Rect(24, 546, 752, 42)
        pygame.draw.rect(screen, (18, 21, 18), panel, border_radius=8)
        pygame.draw.rect(screen, (104, 139, 90), panel, 2, border_radius=8)

        text = self.message
        if self.message_until_ms and current_time_ms > self.message_until_ms:
            text = "Explore la clairiere. Fleches ou ZQSD pour bouger. E pres du PNJ. Echap pour rentrer."
            self.message = text
            self.message_until_ms = 0

        title = self.title_font.render("Exploration", True, (220, 232, 190))
        screen.blit(title, (38, 553))
        body = self.body_font.render(text, True, (220, 220, 205))
        screen.blit(body, (178, 558))
