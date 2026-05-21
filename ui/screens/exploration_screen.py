from pathlib import Path
import xml.etree.ElementTree as ET

import pygame


TILED_FLIP_FLAGS = 0xE0000000


class TiledMap:
    def __init__(self, tmx_path):
        self.tmx_path = Path(tmx_path)
        self.width = 0
        self.height = 0
        self.tile_width = 16
        self.tile_height = 16
        self.pixel_width = 0
        self.pixel_height = 0
        self.layers = []
        self.tiles = {}
        self.collision_rects = []
        self.error_message = None
        self.is_loaded = False
        self._load()

    def _load(self):
        try:
            root = ET.parse(self.tmx_path).getroot()
            self.width = int(root.attrib["width"])
            self.height = int(root.attrib["height"])
            self.tile_width = int(root.attrib["tilewidth"])
            self.tile_height = int(root.attrib["tileheight"])
            self.pixel_width = self.width * self.tile_width
            self.pixel_height = self.height * self.tile_height

            for tileset_node in root.findall("tileset"):
                self._load_tileset(tileset_node)

            for layer_node in root.findall("layer"):
                data_node = layer_node.find("data")
                if data_node is None or data_node.attrib.get("encoding") != "csv":
                    continue
                self.layers.append(self._parse_csv_layer(layer_node, data_node))

            self._load_object_groups(root)
            self.is_loaded = bool(self.layers and self.tiles)
            if not self.is_loaded:
                self.error_message = "Aucun calque Tiled lisible."
        except Exception as exc:
            self.error_message = f"Map Tiled indisponible: {exc}"
            self.is_loaded = False

    def _load_tileset(self, tileset_node):
        first_gid = int(tileset_node.attrib["firstgid"])
        source = tileset_node.attrib.get("source")
        if source:
            tileset_path = (self.tmx_path.parent / source).resolve()
            tileset_root = ET.parse(tileset_path).getroot()
        else:
            tileset_path = self.tmx_path
            tileset_root = tileset_node

        image_node = tileset_root.find("image")
        if image_node is None:
            return

        tile_width = int(tileset_root.attrib.get("tilewidth", self.tile_width))
        tile_height = int(tileset_root.attrib.get("tileheight", self.tile_height))
        columns = int(tileset_root.attrib.get("columns", 0))
        tile_count = int(tileset_root.attrib.get("tilecount", 0))
        image_path = (tileset_path.parent / image_node.attrib["source"]).resolve()
        image = pygame.image.load(str(image_path)).convert_alpha()

        if columns <= 0:
            columns = image.get_width() // tile_width
        rows = image.get_height() // tile_height
        max_tiles = tile_count if tile_count > 0 else columns * rows

        for local_id in range(max_tiles):
            column = local_id % columns
            row = local_id // columns
            tile_rect = pygame.Rect(column * tile_width, row * tile_height, tile_width, tile_height)
            self.tiles[first_gid + local_id] = image.subsurface(tile_rect).copy()

    def _load_object_groups(self, root):
        for object_group in root.findall("objectgroup"):
            if object_group.attrib.get("name") != "90_collisions":
                continue
            for object_node in object_group.findall("object"):
                rect = self._build_collision_rect(object_node)
                if rect is not None:
                    self.collision_rects.append(rect)

    def _build_collision_rect(self, object_node):
        if object_node.attrib.get("type") != "collision":
            return None
        if not self._get_object_bool_property(object_node, "solid"):
            return None
        if object_node.find("ellipse") is not None:
            return None
        if object_node.find("polygon") is not None or object_node.find("polyline") is not None:
            return None

        try:
            x = int(float(object_node.attrib["x"]))
            y = int(float(object_node.attrib["y"]))
            width = int(float(object_node.attrib["width"]))
            height = int(float(object_node.attrib["height"]))
        except (KeyError, TypeError, ValueError):
            return None

        if width <= 0 or height <= 0:
            return None
        return pygame.Rect(x, y, width, height)

    def _get_object_bool_property(self, object_node, property_name):
        properties_node = object_node.find("properties")
        if properties_node is None:
            return False

        for property_node in properties_node.findall("property"):
            if property_node.attrib.get("name") != property_name:
                continue
            value = property_node.attrib.get("value")
            if value is None:
                value = property_node.text
            return str(value).strip() in {"true", "True", "1", "On"}
        return False

    def _parse_csv_layer(self, layer_node, data_node):
        layer_width = int(layer_node.attrib.get("width", self.width))
        values = []
        for raw_value in (data_node.text or "").replace("\n", "").split(","):
            raw_value = raw_value.strip()
            if raw_value:
                values.append(int(raw_value) & ~TILED_FLIP_FLAGS)
        return [values[index:index + layer_width] for index in range(0, len(values), layer_width)]

    def draw(self, screen, camera_offset):
        offset_x, offset_y = camera_offset
        first_column = max(0, offset_x // self.tile_width)
        first_row = max(0, offset_y // self.tile_height)
        last_column = min(self.width, (offset_x + screen.get_width()) // self.tile_width + 2)
        last_row = min(self.height, (offset_y + screen.get_height()) // self.tile_height + 2)

        for layer in self.layers:
            for row_index in range(first_row, last_row):
                if row_index >= len(layer):
                    continue
                row = layer[row_index]
                for column_index in range(first_column, min(last_column, len(row))):
                    gid = row[column_index]
                    if gid == 0:
                        continue
                    tile = self.tiles.get(gid)
                    if tile is not None:
                        screen.blit(
                            tile,
                            (
                                column_index * self.tile_width - offset_x,
                                row_index * self.tile_height - offset_y,
                            ),
                        )


class ExplorationScreen:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.Font(None, 34)
        self.body_font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.map = TiledMap(Path("assets/maps/town_01.tmx"))
        self.map_width = self.map.pixel_width if self.map.is_loaded else 800
        self.map_height = self.map.pixel_height if self.map.is_loaded else 600
        self.camera_offset = pygame.Vector2(0, 0)
        self.tile_size = 16
        self.player_visual_size = pygame.Vector2(16, 24)
        self.player_hitbox_size = pygame.Vector2(10, 8)
        self.player_sprite = self._load_player_sprite()
        self.player_position = pygame.Vector2(self.map_width / 2, self.map_height / 2)
        self.player_rect = pygame.Rect(0, 0, int(self.player_hitbox_size.x), int(self.player_hitbox_size.y))
        self._sync_player_rect_from_position()
        self.player_walk_speed = 2
        self.player_run_speed = 4
        self.npc_rect = pygame.Rect(self.player_rect.x + 112, self.player_rect.y - 64, 28, 34)
        self.default_message = "Explore la clairiere. Fleches ou ZQSD pour bouger. Shift pour courir. E pres d'un point. Echap pour rentrer."
        self.message = self.default_message
        self.message_until_ms = 0
        self.obstacles = list(self.map.collision_rects) if self.map.is_loaded else []
        self.show_collision_debug = False
        self.interactions = [
            {
                "id": "quests",
                "label": "Quetes",
                "rect": pygame.Rect(self.player_rect.x + 96, self.player_rect.y - 16, 88, 56),
                "prompt": "E - Voir les quetes",
                "target_state": "quests",
            },
            {
                "id": "forest_path",
                "label": "Foret",
                "rect": pygame.Rect(self.map_width - 132, max(48, self.map_height // 2 - 40), 88, 72),
                "prompt": "E - Aller vers la foret",
                "target_state": "zone_select",
            },
            {
                "id": "dungeon_gate",
                "label": "Donjons",
                "rect": pygame.Rect(46, max(48, self.map_height // 2 - 48), 96, 86),
                "prompt": "E - Entrer dans les donjons",
                "target_state": "dungeon",
            },
            {
                "id": "craft_bench",
                "label": "Craft",
                "rect": pygame.Rect(self.player_rect.x - 168, self.player_rect.y + 96, 112, 54),
                "prompt": "E - Ouvrir le craft",
                "target_state": "crafting",
            },
            {
                "id": "town_exit",
                "label": "Town",
                "rect": pygame.Rect(self.map_width // 2 - 52, self.map_height - 84, 104, 34),
                "prompt": "E - Retourner en ville",
                "action": "return_to_town",
            },
        ]

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self.game.return_to_town()
            return

        if event.key == pygame.K_e:
            interaction = self._get_active_interaction()
            if interaction is not None:
                self._activate_interaction(interaction)
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
            speed = self.player_run_speed if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else self.player_walk_speed
            self._move_player(movement, speed)

    def draw(self, screen):
        current_time_ms = pygame.time.get_ticks()
        self._update_camera(screen)
        self._draw_map(screen)
        self._draw_interactions(screen)
        self._draw_npc(screen)
        self._draw_player(screen)
        self._draw_collision_debug(screen)
        self._draw_help_panel(screen, current_time_ms)

    def _move_player(self, movement, speed):
        movement = movement.normalize() * speed
        bounds = pygame.Rect(0, 0, self.map_width, self.map_height)
        candidate_position = self._clamp_player_position(self.player_position + movement, bounds)
        candidate = self._build_player_rect(candidate_position)

        if not self._collides_with_obstacle(candidate):
            self.player_position = candidate_position
            self._sync_player_rect_from_position()
            return

        horizontal_position = self._clamp_player_position(
            pygame.Vector2(self.player_position.x + movement.x, self.player_position.y),
            bounds,
        )
        horizontal = self._build_player_rect(horizontal_position)
        if not self._collides_with_obstacle(horizontal):
            self.player_position = horizontal_position

        vertical_position = self._clamp_player_position(
            pygame.Vector2(self.player_position.x, self.player_position.y + movement.y),
            bounds,
        )
        vertical = self._build_player_rect(vertical_position)
        if not self._collides_with_obstacle(vertical):
            self.player_position = vertical_position

        self._sync_player_rect_from_position()

    def _collides_with_obstacle(self, candidate):
        return any(candidate.colliderect(obstacle) for obstacle in self.obstacles)

    def _build_player_rect(self, position):
        rect = pygame.Rect(0, 0, int(self.player_hitbox_size.x), int(self.player_hitbox_size.y))
        rect.center = (round(position.x), round(position.y))
        return rect

    def _sync_player_rect_from_position(self):
        self.player_rect = self._build_player_rect(self.player_position)

    def _clamp_player_position(self, position, bounds):
        half_width = self.player_hitbox_size.x / 2
        half_height = self.player_hitbox_size.y / 2
        return pygame.Vector2(
            min(max(position.x, bounds.left + half_width), bounds.right - half_width),
            min(max(position.y, bounds.top + half_height), bounds.bottom - half_height),
        )

    def _get_active_interaction(self):
        reach_rect = self.player_rect.inflate(46, 46)
        for interaction in self.interactions:
            if reach_rect.colliderect(interaction["rect"]):
                return interaction
        return None

    def _activate_interaction(self, interaction):
        action = interaction.get("action")
        if action == "return_to_town":
            self.game.return_to_town()
            return

        target_state = interaction.get("target_state")
        if target_state:
            self.game.state = target_state

    def _update_camera(self, screen):
        max_x = max(0, self.map_width - screen.get_width())
        max_y = max(0, self.map_height - screen.get_height())
        self.camera_offset.x = min(max(self.player_rect.centerx - screen.get_width() // 2, 0), max_x)
        self.camera_offset.y = min(max(self.player_rect.centery - screen.get_height() // 2, 0), max_y)

    def _draw_map(self, screen):
        if self.map.is_loaded:
            screen.fill((18, 28, 22))
            self.map.draw(screen, (int(self.camera_offset.x), int(self.camera_offset.y)))
            return

        screen.fill((23, 54, 35))
        for y in range(0, screen.get_height(), 8):
            shade = 28 + int(y * 0.025)
            pygame.draw.rect(screen, (18, min(72, shade + 28), 35), (0, y, screen.get_width(), 8))

    def _draw_interactions(self, screen):
        active = self._get_active_interaction()
        for interaction in self.interactions:
            rect = self._to_screen_rect(interaction["rect"])
            is_active = interaction is active
            if interaction["id"] == "quests":
                self._draw_quest_post(screen, rect, is_active)
            elif interaction["id"] == "forest_path":
                self._draw_forest_exit(screen, rect, is_active)
            elif interaction["id"] == "dungeon_gate":
                self._draw_dungeon_gate(screen, rect, is_active)
            elif interaction["id"] == "craft_bench":
                self._draw_craft_bench(screen, rect, is_active)
            elif interaction["id"] == "town_exit":
                self._draw_town_exit(screen, rect, is_active)

    def _draw_interaction_marker(self, screen, rect, label, is_active):
        color = (238, 214, 126) if is_active else (168, 148, 90)
        pygame.draw.circle(screen, color, (rect.centerx, rect.y - 10), 5)
        text = self.small_font.render(label, True, (235, 226, 190))
        text_rect = text.get_rect(center=(rect.centerx, rect.y - 24))
        screen.blit(text, text_rect)

    def _draw_quest_post(self, screen, rect, is_active):
        pygame.draw.rect(screen, (83, 58, 38), (rect.x + 12, rect.y + 10, 14, rect.h - 10))
        board = pygame.Rect(rect.x + 24, rect.y + 4, rect.w - 30, 34)
        pygame.draw.rect(screen, (118, 84, 50), board, border_radius=4)
        pygame.draw.rect(screen, (224, 190, 104), board, 2, border_radius=4)
        pygame.draw.line(screen, (60, 42, 30), (board.x + 10, board.y + 12), (board.right - 10, board.y + 12), 2)
        pygame.draw.line(screen, (60, 42, 30), (board.x + 10, board.y + 22), (board.right - 18, board.y + 22), 2)
        self._draw_interaction_marker(screen, rect, "Quetes", is_active)

    def _draw_forest_exit(self, screen, rect, is_active):
        pygame.draw.ellipse(screen, (54, 82, 38), rect)
        pygame.draw.arc(screen, (151, 124, 76), rect.inflate(-10, -8), 3.3, 6.1, 4)
        pygame.draw.polygon(screen, (28, 94, 44), [(rect.x + 24, rect.y + 46), (rect.x + 44, rect.y + 10), (rect.x + 66, rect.y + 46)])
        self._draw_interaction_marker(screen, rect, "Foret", is_active)

    def _draw_dungeon_gate(self, screen, rect, is_active):
        pygame.draw.ellipse(screen, (13, 17, 18), rect)
        pygame.draw.arc(screen, (93, 86, 78), rect, 3.2, 6.2, 6)
        inner = rect.inflate(-26, -18)
        pygame.draw.ellipse(screen, (4, 8, 10), inner)
        self._draw_interaction_marker(screen, rect, "Donjons", is_active)

    def _draw_craft_bench(self, screen, rect, is_active):
        top = pygame.Rect(rect.x + 8, rect.y + 12, rect.w - 16, 18)
        pygame.draw.rect(screen, (103, 69, 42), top, border_radius=4)
        pygame.draw.rect(screen, (196, 151, 84), top, 2, border_radius=4)
        pygame.draw.rect(screen, (72, 48, 31), (rect.x + 20, rect.y + 30, 10, 22))
        pygame.draw.rect(screen, (72, 48, 31), (rect.right - 30, rect.y + 30, 10, 22))
        pygame.draw.circle(screen, (156, 158, 146), (rect.centerx + 20, rect.y + 8), 7)
        self._draw_interaction_marker(screen, rect, "Craft", is_active)

    def _draw_town_exit(self, screen, rect, is_active):
        pygame.draw.rect(screen, (86, 72, 48), rect, border_radius=5)
        pygame.draw.rect(screen, (209, 177, 95), rect, 2, border_radius=5)
        label = self.small_font.render("Town", True, (245, 230, 180))
        label_rect = label.get_rect(center=rect.center)
        screen.blit(label, label_rect)
        self._draw_interaction_marker(screen, rect, "Ville", is_active)

    def _draw_npc(self, screen):
        rect = self._to_screen_rect(self.npc_rect)
        pygame.draw.ellipse(screen, (16, 33, 24), rect.move(3, 8))
        pygame.draw.rect(screen, (79, 90, 58), rect, border_radius=6)
        pygame.draw.circle(screen, (202, 171, 126), rect.midtop, 9)
        label = self.small_font.render("PNJ", True, (230, 220, 185))
        screen.blit(label, (rect.x - 5, rect.y - 24))

    def _draw_player(self, screen):
        hitbox_rect = self._to_screen_rect(self.player_rect)
        draw_rect = self._to_screen_rect(self._get_player_draw_rect())
        pygame.draw.ellipse(screen, (10, 25, 18), hitbox_rect.inflate(8, 2))

        if self.player_sprite is not None:
            screen.blit(self.player_sprite, draw_rect)
            return

        pygame.draw.rect(screen, (66, 122, 166), draw_rect, border_radius=3)
        pygame.draw.circle(screen, (226, 188, 140), (draw_rect.centerx, draw_rect.y + 5), 5)

    def _load_player_sprite(self):
        sprite_path = Path("assets/sprites/player/base/idle/idle_down_sheet.png")
        try:
            sheet = pygame.image.load(str(sprite_path)).convert_alpha()
            frame_size = sheet.get_height()
            frame = sheet.subsurface(pygame.Rect(0, 0, frame_size, frame_size)).copy()
            content_rect = frame.get_bounding_rect(min_alpha=1)
            if content_rect.width > 0 and content_rect.height > 0:
                frame = frame.subsurface(content_rect).copy()
            return pygame.transform.scale(
                frame,
                (int(self.player_visual_size.x), int(self.player_visual_size.y)),
            )
        except (OSError, pygame.error, ValueError):
            return None

    def _get_player_draw_rect(self):
        draw_rect = pygame.Rect(
            0,
            0,
            int(self.player_visual_size.x),
            int(self.player_visual_size.y),
        )
        draw_rect.midbottom = self.player_rect.midbottom
        return draw_rect

    def _draw_collision_debug(self, screen):
        if not self.show_collision_debug:
            return
        for obstacle in self.obstacles:
            pygame.draw.rect(screen, (220, 80, 80), self._to_screen_rect(obstacle), 1)

    def _draw_help_panel(self, screen, current_time_ms):
        panel = pygame.Rect(24, 546, 752, 42)
        pygame.draw.rect(screen, (18, 21, 18), panel, border_radius=8)
        pygame.draw.rect(screen, (104, 139, 90), panel, 2, border_radius=8)

        if self.message_until_ms and current_time_ms > self.message_until_ms:
            self.message = self.default_message
            self.message_until_ms = 0
        active_interaction = self._get_active_interaction()
        text = active_interaction["prompt"] if active_interaction is not None else self.message

        title = self.title_font.render("Exploration", True, (220, 232, 190))
        screen.blit(title, (38, 553))
        if not self.map.is_loaded and active_interaction is None:
            text = "Map Tiled indisponible. Affichage de secours actif."
        body = self.body_font.render(self._fit_panel_text(text, 570), True, (220, 220, 205))
        screen.blit(body, (178, 558))

    def _to_screen_rect(self, rect):
        return rect.move(-int(self.camera_offset.x), -int(self.camera_offset.y))

    def _fit_panel_text(self, text, max_width):
        text = str(text)
        if self.body_font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        while text and self.body_font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]
        return text + ellipsis if text else ellipsis
