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
        self.collision_polygons = []
        self.spawns = {}
        self.triggers = []
        self.warnings = []
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
        try:
            first_gid = int(tileset_node.attrib["firstgid"])
            source = tileset_node.attrib.get("source")
            if source:
                if source.startswith(":/"):
                    self.warnings.append(f"Ignored special Tiled tileset source: {source}")
                    return
                tileset_path = (self.tmx_path.parent / source).resolve()
                if not tileset_path.exists():
                    self.warnings.append(f"Ignored missing tileset file: {tileset_path}")
                    return
                tileset_root = ET.parse(tileset_path).getroot()
            else:
                tileset_path = self.tmx_path
                tileset_root = tileset_node

            image_node = tileset_root.find("image")
            if image_node is None:
                self.warnings.append(f"Ignored tileset without image: {tileset_path}")
                return

            tile_width = int(tileset_root.attrib.get("tilewidth", self.tile_width))
            tile_height = int(tileset_root.attrib.get("tileheight", self.tile_height))
            columns = int(tileset_root.attrib.get("columns", 0))
            tile_count = int(tileset_root.attrib.get("tilecount", 0))
            image_path = (tileset_path.parent / image_node.attrib["source"]).resolve()
            if not image_path.exists():
                self.warnings.append(f"Ignored missing tileset image: {image_path}")
                return
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
        except Exception as exc:
            source = tileset_node.attrib.get("source", "<inline tileset>")
            self.warnings.append(f"Ignored tileset {source}: {exc}")

    def _load_object_groups(self, root):
        for object_group in root.findall("objectgroup"):
            if object_group.attrib.get("name") == "94_spawns":
                self._load_spawns(object_group)
                continue
            if object_group.attrib.get("name") == "93_triggers":
                self._load_triggers(object_group)
                continue
            if object_group.attrib.get("name") != "90_collisions":
                continue
            for object_node in object_group.findall("object"):
                rect = self._build_collision_rect(object_node)
                if rect is not None:
                    self.collision_rects.append(rect)
                polygon = self._build_collision_polygon(object_node)
                if polygon is not None:
                    self.collision_polygons.append(polygon)

    def _load_spawns(self, object_group):
        for object_node in object_group.findall("object"):
            spawn = self._build_spawn(object_node)
            if spawn is not None:
                self.spawns[spawn["spawn_id"]] = spawn

    def _load_triggers(self, object_group):
        for object_node in object_group.findall("object"):
            trigger = self._build_trigger(object_node)
            if trigger is not None:
                self.triggers.append(trigger)

    def _build_trigger(self, object_node):
        object_type = object_node.attrib.get("type") or object_node.attrib.get("class")
        if object_type and object_type != "trigger":
            return None
        if not self._is_object_enabled(object_node):
            return None

        trigger_id = self._get_object_property(object_node, "trigger_id") or object_node.attrib.get("name")
        if not trigger_id:
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

        return {
            "trigger_id": trigger_id,
            "trigger_type": self._get_object_property(object_node, "trigger_type"),
            "prompt": self._get_object_property(object_node, "prompt"),
            "requires_interact": self._get_object_bool_property(object_node, "requires_interact"),
            "target_state": self._get_object_property(object_node, "target_state"),
            "target_map": self._get_object_property(object_node, "target_map"),
            "target_spawn_id": self._get_object_property(object_node, "target_spawn_id"),
            "once": self._get_object_bool_property(object_node, "once"),
            "rect": pygame.Rect(x, y, width, height),
        }

    def _build_spawn(self, object_node):
        object_type = object_node.attrib.get("type") or object_node.attrib.get("class")
        if object_type and object_type != "spawn":
            return None
        if not self._is_object_enabled(object_node):
            return None

        spawn_id = self._get_object_property(object_node, "spawn_id")
        if not spawn_id:
            return None

        try:
            x = float(object_node.attrib["x"])
            y = float(object_node.attrib["y"])
            width = float(object_node.attrib.get("width", 0))
            height = float(object_node.attrib.get("height", 0))
        except (KeyError, TypeError, ValueError):
            return None

        if width > 0 and height > 0:
            x += width / 2
            y += height / 2

        return {
            "spawn_id": spawn_id,
            "spawn_type": self._get_object_property(object_node, "spawn_type"),
            "map_id": self._get_object_property(object_node, "map_id"),
            "facing": self._get_object_property(object_node, "facing") or "down",
            "x": x,
            "y": y,
        }

    def _is_object_enabled(self, object_node):
        value = self._get_object_property(object_node, "enabled")
        if value is None:
            return True
        return str(value).strip() not in {"false", "False", "0", "Off"}

    def _build_collision_rect(self, object_node):
        if object_node.attrib.get("type") != "collision":
            return None
        if not self._get_object_bool_property(object_node, "solid"):
            return None
        if object_node.find("ellipse") is not None:
            return None
        if object_node.find("polyline") is not None:
            return None

        polygon_node = object_node.find("polygon")
        if polygon_node is not None:
            if self._get_object_property(object_node, "collision_mode") == "bounds":
                return self._build_polygon_bounds_rect(object_node, polygon_node)
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

    def _build_collision_polygon(self, object_node):
        if object_node.attrib.get("type") != "collision":
            return None
        if not self._get_object_bool_property(object_node, "solid"):
            return None
        if object_node.find("ellipse") is not None or object_node.find("polyline") is not None:
            return None
        if self._get_object_property(object_node, "collision_mode") == "bounds":
            return None

        polygon_node = object_node.find("polygon")
        if polygon_node is None:
            return None
        return self._parse_polygon_points(object_node, polygon_node)

    def _build_polygon_bounds_rect(self, object_node, polygon_node):
        points = self._parse_polygon_points(object_node, polygon_node)
        if not points:
            return None

        left = min(point[0] for point in points)
        top = min(point[1] for point in points)
        right = max(point[0] for point in points)
        bottom = max(point[1] for point in points)
        width = int(round(right - left))
        height = int(round(bottom - top))
        if width <= 0 or height <= 0:
            return None
        return pygame.Rect(int(round(left)), int(round(top)), width, height)

    def _parse_polygon_points(self, object_node, polygon_node):
        points_text = polygon_node.attrib.get("points", "")
        if not points_text:
            return None

        try:
            origin_x = float(object_node.attrib["x"])
            origin_y = float(object_node.attrib["y"])
        except (KeyError, TypeError, ValueError):
            return None

        points = []
        for point_text in points_text.split():
            try:
                raw_x, raw_y = point_text.split(",", 1)
                points.append((origin_x + float(raw_x), origin_y + float(raw_y)))
            except ValueError:
                return None
        return points if len(points) >= 3 else None

    def _get_object_bool_property(self, object_node, property_name):
        value = self._get_object_property(object_node, property_name)
        return str(value).strip() in {"true", "True", "1", "On"}

    def _get_object_property(self, object_node, property_name):
        properties_node = object_node.find("properties")
        if properties_node is None:
            return None

        for property_node in properties_node.findall("property"):
            if property_node.attrib.get("name") != property_name:
                continue
            value = property_node.attrib.get("value")
            if value is None:
                value = property_node.text
            value = str(value).strip()
            return value if value else None
        return None

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
        self.active_spawn_id = None
        self.spawn_debug_message = ""
        self.player_position = self._get_initial_player_position()
        player_spawn = self.map.spawns.get("player_start") if self.map.is_loaded else None
        self.player_facing = player_spawn.get("facing") if player_spawn is not None else "down"
        self.player_rect = pygame.Rect(0, 0, int(self.player_hitbox_size.x), int(self.player_hitbox_size.y))
        self._sync_player_rect_from_position()
        self.player_walk_speed = 2
        self.player_run_speed = 4
        self.npc_rect = pygame.Rect(self.player_rect.x + 112, self.player_rect.y - 64, 28, 34)
        self.default_message = "Explore la clairiere. Fleches ou ZQSD pour bouger. Shift pour courir. E pres d'un point. Echap pour rentrer."
        self.message = self.spawn_debug_message or self.default_message
        self.message_until_ms = pygame.time.get_ticks() + 4000 if self.spawn_debug_message else 0
        self.obstacles = list(self.map.collision_rects) if self.map.is_loaded else []
        self.collision_polygons = list(self.map.collision_polygons) if self.map.is_loaded else []
        self.triggers = list(self.map.triggers) if self.map.is_loaded else []
        self.quick_actions = [
            {"id": "inventory", "label": "Inventory", "target_state": "inventory", "shortcut": pygame.K_i, "rect": pygame.Rect(0, 0, 0, 0)},
            {"id": "quests", "label": "Quests", "target_state": "quests", "shortcut": pygame.K_q, "rect": pygame.Rect(0, 0, 0, 0)},
            {"id": "skills", "label": "Skills", "target_state": "skills", "shortcut": pygame.K_k, "rect": pygame.Rect(0, 0, 0, 0)},
            {"id": "achievements", "label": "Achievements", "target_state": "achievements", "shortcut": pygame.K_a, "rect": pygame.Rect(0, 0, 0, 0)},
            {"id": "professions", "label": "Professions", "target_state": "professions", "shortcut": pygame.K_p, "rect": pygame.Rect(0, 0, 0, 0)},
            {"id": "mailbox", "label": "Mailbox", "target_state": "mailbox", "shortcut": pygame.K_m, "rect": pygame.Rect(0, 0, 0, 0)},
            {"id": "recipes", "label": "Recipes", "target_state": "crafting", "shortcut": pygame.K_r, "rect": pygame.Rect(0, 0, 0, 0)},
            {"id": "town", "label": "Town", "action": "return_to_town", "shortcut": pygame.K_t, "rect": pygame.Rect(0, 0, 0, 0)},
        ]
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
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            action = self._get_quick_action_at(event.pos)
            if action is not None:
                self._activate_quick_action(action)
            return

        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self.game.return_to_town()
            return

        shortcut_action = self._get_quick_action_for_key(event.key)
        if shortcut_action is not None:
            self._activate_quick_action(shortcut_action)
            return

        if event.key == pygame.K_e:
            trigger = self._get_active_trigger()
            if trigger is not None:
                self._activate_trigger(trigger)
                return

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
        self._draw_quick_action_bar(screen)

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
        if any(candidate.colliderect(obstacle) for obstacle in self.obstacles):
            return True
        return any(self._rect_collides_with_polygon(candidate, polygon) for polygon in self.collision_polygons)

    def _rect_collides_with_polygon(self, rect, polygon_points):
        rect_points = [rect.topleft, rect.topright, rect.bottomright, rect.bottomleft]
        if any(self._point_in_polygon(point, polygon_points) for point in rect_points):
            return True
        if any(rect.collidepoint(point) for point in polygon_points):
            return True

        rect_edges = self._rect_edges(rect)
        polygon_edges = list(zip(polygon_points, polygon_points[1:] + polygon_points[:1]))
        for rect_start, rect_end in rect_edges:
            for polygon_start, polygon_end in polygon_edges:
                if self._segments_intersect(rect_start, rect_end, polygon_start, polygon_end):
                    return True
        return False

    def _point_in_polygon(self, point, polygon_points):
        x, y = point
        is_inside = False
        previous_x, previous_y = polygon_points[-1]
        for current_x, current_y in polygon_points:
            if ((current_y > y) != (previous_y > y)):
                intersect_x = (previous_x - current_x) * (y - current_y) / (previous_y - current_y) + current_x
                if x < intersect_x:
                    is_inside = not is_inside
            previous_x, previous_y = current_x, current_y
        return is_inside

    def _segments_intersect(self, a, b, c, d):
        def orientation(first, second, third):
            value = (
                (second[1] - first[1]) * (third[0] - second[0])
                - (second[0] - first[0]) * (third[1] - second[1])
            )
            if abs(value) < 0.000001:
                return 0
            return 1 if value > 0 else 2

        def on_segment(first, second, third):
            return (
                min(first[0], third[0]) <= second[0] <= max(first[0], third[0])
                and min(first[1], third[1]) <= second[1] <= max(first[1], third[1])
            )

        first_orientation = orientation(a, b, c)
        second_orientation = orientation(a, b, d)
        third_orientation = orientation(c, d, a)
        fourth_orientation = orientation(c, d, b)

        if first_orientation != second_orientation and third_orientation != fourth_orientation:
            return True
        if first_orientation == 0 and on_segment(a, c, b):
            return True
        if second_orientation == 0 and on_segment(a, d, b):
            return True
        if third_orientation == 0 and on_segment(c, a, d):
            return True
        if fourth_orientation == 0 and on_segment(c, b, d):
            return True
        return False

    def _rect_edges(self, rect):
        top_left = rect.topleft
        top_right = rect.topright
        bottom_right = rect.bottomright
        bottom_left = rect.bottomleft
        return [
            (top_left, top_right),
            (top_right, bottom_right),
            (bottom_right, bottom_left),
            (bottom_left, top_left),
        ]

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

    def _get_active_trigger(self):
        for trigger in self.triggers:
            if self.player_rect.colliderect(trigger["rect"]):
                return trigger
        return None

    def _activate_trigger(self, trigger):
        trigger_type = trigger.get("trigger_type")
        if trigger_type == "state_transition":
            target_state = trigger.get("target_state")
            if target_state:
                self.game.state = target_state
                return

        self.message = "Trigger non configure."
        self.message_until_ms = pygame.time.get_ticks() + 2200

    def _get_quick_action_for_key(self, key):
        for action in self.quick_actions:
            if action.get("shortcut") == key:
                return action
        return None

    def _get_quick_action_at(self, position):
        for action in self.quick_actions:
            if action["rect"].collidepoint(position):
                return action
        return None

    def _get_hovered_quick_action(self):
        mouse_position = pygame.mouse.get_pos()
        return self._get_quick_action_at(mouse_position)

    def _activate_quick_action(self, action):
        if action.get("action") == "return_to_town":
            self.game.return_to_town()
            return

        target_state = action.get("target_state")
        if target_state:
            self.game.state = target_state

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

    def _get_initial_player_position(self):
        spawn = self.map.spawns.get("player_start") if self.map.is_loaded else None
        if spawn is not None:
            self.active_spawn_id = "player_start"
            self.spawn_debug_message = f"Spawn player_start loaded at x={spawn['x']:.1f}, y={spawn['y']:.1f}"
            return pygame.Vector2(spawn["x"], spawn["y"])

        self.active_spawn_id = None
        spawn_ids = sorted(self.map.spawns.keys()) if self.map.is_loaded else []
        if spawn_ids:
            self.spawn_debug_message = f"player_start not found. Found: {', '.join(spawn_ids)}"
        else:
            self.spawn_debug_message = "No Tiled spawns found"
        return pygame.Vector2(self.map_width / 2, self.map_height / 2)

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
        for polygon in self.collision_polygons:
            screen_points = [self._to_screen_point(point) for point in polygon]
            if len(screen_points) >= 3:
                pygame.draw.lines(screen, (220, 160, 80), True, screen_points, 1)
        for trigger in self.triggers:
            pygame.draw.rect(screen, (80, 160, 230), self._to_screen_rect(trigger["rect"]), 1)

    def _layout_quick_action_bar(self, screen):
        bar_height = 52
        button_size = 44
        spacing = 10
        total_width = len(self.quick_actions) * button_size + (len(self.quick_actions) - 1) * spacing
        start_x = (screen.get_width() - total_width) // 2
        y = screen.get_height() - bar_height + (bar_height - button_size) // 2

        for index, action in enumerate(self.quick_actions):
            x = start_x + index * (button_size + spacing)
            action["rect"] = pygame.Rect(x, y, button_size, button_size)

        return pygame.Rect(0, screen.get_height() - bar_height, screen.get_width(), bar_height)

    def _draw_quick_action_bar(self, screen):
        bar_rect = self._layout_quick_action_bar(screen)
        pygame.draw.rect(screen, (14, 17, 19), bar_rect)
        pygame.draw.line(screen, (72, 88, 80), bar_rect.topleft, bar_rect.topright, 2)

        hovered_action = self._get_hovered_quick_action()
        for action in self.quick_actions:
            rect = action["rect"]
            is_hovered = action is hovered_action
            fill_color = (42, 50, 50) if is_hovered else (26, 31, 32)
            outline_color = (184, 202, 150) if is_hovered else (82, 96, 88)
            pygame.draw.rect(screen, fill_color, rect, border_radius=6)
            pygame.draw.rect(screen, outline_color, rect, 2, border_radius=6)
            self._draw_quick_action_icon(screen, action, rect, is_hovered)

        if hovered_action is not None and self._get_active_trigger() is None:
            self._draw_quick_action_tooltip(screen, hovered_action, bar_rect)

    def _draw_quick_action_icon(self, screen, action, rect, is_hovered):
        color = (236, 226, 178) if is_hovered else (204, 214, 190)
        shadow = (12, 14, 15)
        center = rect.center
        action_id = action["id"]

        if action_id == "inventory":
            bag = pygame.Rect(rect.x + 13, rect.y + 18, 18, 15)
            pygame.draw.arc(screen, color, (rect.x + 15, rect.y + 10, 14, 16), 3.35, 6.05, 2)
            pygame.draw.rect(screen, color, bag, border_radius=4)
            pygame.draw.rect(screen, shadow, bag.inflate(-8, -8))
        elif action_id == "quests":
            page = pygame.Rect(rect.x + 14, rect.y + 11, 16, 23)
            pygame.draw.rect(screen, color, page, border_radius=2)
            pygame.draw.line(screen, shadow, (page.x + 4, page.y + 7), (page.right - 4, page.y + 7), 1)
            pygame.draw.line(screen, shadow, (page.x + 4, page.y + 13), (page.right - 5, page.y + 13), 1)
        elif action_id == "skills":
            points = [
                (center[0], rect.y + 9),
                (center[0] + 4, center[1] - 2),
                (rect.right - 9, center[1] - 2),
                (center[0] + 6, center[1] + 4),
                (center[0] + 9, rect.bottom - 9),
                (center[0], center[1] + 7),
                (center[0] - 9, rect.bottom - 9),
                (center[0] - 6, center[1] + 4),
                (rect.x + 9, center[1] - 2),
                (center[0] - 4, center[1] - 2),
            ]
            pygame.draw.polygon(screen, color, points)
        elif action_id == "achievements":
            cup = pygame.Rect(rect.x + 15, rect.y + 12, 14, 14)
            pygame.draw.rect(screen, color, cup, border_radius=3)
            pygame.draw.arc(screen, color, (rect.x + 7, rect.y + 13, 13, 12), 4.6, 1.6, 2)
            pygame.draw.arc(screen, color, (rect.right - 20, rect.y + 13, 13, 12), 1.5, 4.8, 2)
            pygame.draw.rect(screen, color, (center[0] - 2, rect.y + 26, 4, 7))
            pygame.draw.rect(screen, color, (center[0] - 8, rect.y + 33, 16, 3), border_radius=2)
        elif action_id == "professions":
            pygame.draw.line(screen, color, (rect.x + 14, rect.y + 30), (rect.x + 30, rect.y + 14), 4)
            pygame.draw.rect(screen, color, (rect.x + 24, rect.y + 10, 10, 8), border_radius=2)
            pygame.draw.line(screen, shadow, (rect.x + 16, rect.y + 28), (rect.x + 20, rect.y + 32), 2)
        elif action_id == "mailbox":
            envelope = pygame.Rect(rect.x + 11, rect.y + 15, 22, 16)
            pygame.draw.rect(screen, color, envelope, border_radius=3)
            pygame.draw.line(screen, shadow, envelope.topleft, center, 1)
            pygame.draw.line(screen, shadow, envelope.topright, center, 1)
        elif action_id == "recipes":
            left_page = pygame.Rect(rect.x + 11, rect.y + 12, 11, 22)
            right_page = pygame.Rect(rect.x + 22, rect.y + 12, 11, 22)
            pygame.draw.rect(screen, color, left_page, border_radius=2)
            pygame.draw.rect(screen, color, right_page, border_radius=2)
            pygame.draw.line(screen, shadow, (rect.x + 22, rect.y + 13), (rect.x + 22, rect.y + 34), 1)
            pygame.draw.line(screen, shadow, (rect.x + 14, rect.y + 19), (rect.x + 19, rect.y + 19), 1)
            pygame.draw.line(screen, shadow, (rect.x + 25, rect.y + 24), (rect.x + 30, rect.y + 24), 1)
        elif action_id == "town":
            roof = [(center[0], rect.y + 10), (rect.x + 11, rect.y + 22), (rect.right - 11, rect.y + 22)]
            house = pygame.Rect(rect.x + 14, rect.y + 21, 16, 14)
            pygame.draw.polygon(screen, color, roof)
            pygame.draw.rect(screen, color, house, border_radius=2)
            pygame.draw.rect(screen, shadow, (center[0] - 3, rect.y + 27, 6, 8))

        shortcut_text = pygame.key.name(action["shortcut"]).upper()
        text = self.small_font.render(shortcut_text[:1], True, (18, 22, 22))
        text_rect = text.get_rect(center=(rect.right - 8, rect.bottom - 8))
        screen.blit(text, text_rect)

    def _draw_quick_action_tooltip(self, screen, action, bar_rect):
        shortcut = pygame.key.name(action["shortcut"]).upper()
        label = f"{action['label']} ({shortcut})"
        text = self.small_font.render(label, True, (236, 235, 210))
        tooltip = text.get_rect()
        tooltip.inflate_ip(16, 8)
        tooltip.midbottom = (action["rect"].centerx, bar_rect.y - 6)
        tooltip.clamp_ip(screen.get_rect())
        pygame.draw.rect(screen, (16, 18, 18), tooltip, border_radius=5)
        pygame.draw.rect(screen, (104, 139, 90), tooltip, 1, border_radius=5)
        screen.blit(text, text.get_rect(center=tooltip.center))

    def _draw_help_panel(self, screen, current_time_ms):
        bar_height = 52
        panel = pygame.Rect(24, screen.get_height() - bar_height - 48, screen.get_width() - 48, 42)
        pygame.draw.rect(screen, (18, 21, 18), panel, border_radius=8)
        pygame.draw.rect(screen, (104, 139, 90), panel, 2, border_radius=8)

        if self.message_until_ms and current_time_ms > self.message_until_ms:
            self.message = self.default_message
            self.message_until_ms = 0
        active_trigger = self._get_active_trigger()
        active_interaction = self._get_active_interaction()
        hovered_action = self._get_hovered_quick_action()
        if active_trigger is not None and active_trigger.get("requires_interact"):
            text = active_trigger.get("prompt") or "E - Interagir"
        elif hovered_action is not None:
            shortcut = pygame.key.name(hovered_action["shortcut"]).upper()
            text = f"{hovered_action['label']} ({shortcut})"
        elif active_interaction is not None:
            text = active_interaction["prompt"]
        else:
            text = self.message

        title = self.title_font.render("Exploration", True, (220, 232, 190))
        screen.blit(title, (panel.x + 14, panel.y + 7))
        if not self.map.is_loaded and active_trigger is None and active_interaction is None:
            text = "Map Tiled indisponible. Affichage de secours actif."
        body_width = max(180, panel.width - 154)
        body = self.body_font.render(self._fit_panel_text(text, body_width), True, (220, 220, 205))
        screen.blit(body, (panel.x + 154, panel.y + 12))

    def _to_screen_rect(self, rect):
        return rect.move(-int(self.camera_offset.x), -int(self.camera_offset.y))

    def _to_screen_point(self, point):
        return (
            int(round(point[0] - self.camera_offset.x)),
            int(round(point[1] - self.camera_offset.y)),
        )

    def _fit_panel_text(self, text, max_width):
        text = str(text)
        if self.body_font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        while text and self.body_font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]
        return text + ellipsis if text else ellipsis
