from pathlib import Path
import xml.etree.ElementTree as ET

import pygame

from ui.overlays.achievement_overlay import AchievementOverlay
from ui.overlays.craft_book_overlay import CraftBookOverlay
from ui.overlays.inventory_overlay import InventoryOverlay
from ui.overlays.profession_overlay import ProfessionOverlay
from ui.overlays.quest_overlay import QuestOverlay
from ui.overlays.skill_overlay import SkillOverlay
from ui.overlays.trials_overlay import TrialsOverlay


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
        self.tile_animations = {}
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

            self._load_tile_animations(tileset_root, first_gid)
        except Exception as exc:
            source = tileset_node.attrib.get("source", "<inline tileset>")
            self.warnings.append(f"Ignored tileset {source}: {exc}")

    def _load_tile_animations(self, tileset_root, first_gid):
        for tile_node in tileset_root.findall("tile"):
            animation_node = tile_node.find("animation")
            if animation_node is None:
                continue

            try:
                animated_gid = first_gid + int(tile_node.attrib["id"])
            except (KeyError, TypeError, ValueError):
                continue

            if animated_gid not in self.tiles:
                continue

            frames = []
            total_duration = 0
            for frame_node in animation_node.findall("frame"):
                try:
                    frame_gid = first_gid + int(frame_node.attrib["tileid"])
                    duration_ms = int(frame_node.attrib["duration"])
                except (KeyError, TypeError, ValueError):
                    continue

                if duration_ms <= 0 or frame_gid not in self.tiles:
                    continue

                frames.append((frame_gid, duration_ms))
                total_duration += duration_ms

            if frames and total_duration > 0:
                self.tile_animations[animated_gid] = {
                    "frames": frames,
                    "total_duration": total_duration,
                }

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

    def _get_animated_gid(self, gid, current_time_ms):
        animation = self.tile_animations.get(gid)
        if not animation:
            return gid

        frames = animation.get("frames")
        total_duration = animation.get("total_duration")
        if not frames or not total_duration:
            return gid

        elapsed_ms = current_time_ms % total_duration
        frame_start_ms = 0
        for frame_gid, duration_ms in frames:
            frame_start_ms += duration_ms
            if elapsed_ms < frame_start_ms:
                return frame_gid
        return gid

    def draw(self, screen, camera_offset):
        current_time_ms = pygame.time.get_ticks()
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
                    display_gid = self._get_animated_gid(gid, current_time_ms)
                    tile = self.tiles.get(display_gid)
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
        self.default_message = "Explore la clairiere. Fleches ou ZQSD pour bouger. Shift pour courir. E pres d'un point. Echap pour rentrer."
        self.message = self.default_message
        self.message_until_ms = 0
        self.map_directory = Path("assets/maps")
        self.current_map_id = "town_01"
        self.map = None
        self.map_width = 800
        self.map_height = 600
        self.camera_offset = pygame.Vector2(0, 0)
        self.tile_size = 16
        self.player_visual_size = pygame.Vector2(16, 24)
        self.player_hitbox_size = pygame.Vector2(10, 8)
        self.player_animations = self._load_player_animations()
        self.player_animation_state = "idle"
        self.player_animation_frame_duration_ms = 140
        self.player_is_moving = False
        self.active_spawn_id = None
        self.spawn_debug_message = ""
        self.player_position = pygame.Vector2(self.map_width / 2, self.map_height / 2)
        self.player_facing = "down"
        self.player_rect = pygame.Rect(0, 0, int(self.player_hitbox_size.x), int(self.player_hitbox_size.y))
        self.player_walk_speed = 2
        self.player_run_speed = 4
        self.obstacles = []
        self.collision_polygons = []
        self.triggers = []
        self._load_map(self.current_map_id)
        self.active_overlay = None
        self.achievement_overlay = AchievementOverlay(self.game)
        self.craft_book_overlay = CraftBookOverlay(self.game)
        self.inventory_overlay = InventoryOverlay(self.game)
        self.profession_overlay = ProfessionOverlay(self.game)
        self.quest_overlay = QuestOverlay(self.game)
        self.skill_overlay = SkillOverlay(self.game)
        self.trials_overlay = TrialsOverlay(self.game)
        self.quick_actions = [
            {"id": "inventory", "label": "Inventory", "overlay": "inventory", "shortcut": pygame.K_i, "rect": pygame.Rect(0, 0, 0, 0)},
            {"id": "quests", "label": "Quests", "overlay": "quests", "shortcut": pygame.K_j, "rect": pygame.Rect(0, 0, 0, 0)},
            {"id": "skills", "label": "Skills", "overlay": "skills", "shortcut": pygame.K_k, "rect": pygame.Rect(0, 0, 0, 0)},
            {"id": "achievements", "label": "Achievements", "overlay": "achievements", "shortcut": pygame.K_a, "rect": pygame.Rect(0, 0, 0, 0)},
            {"id": "professions", "label": "Professions", "overlay": "professions", "shortcut": pygame.K_p, "rect": pygame.Rect(0, 0, 0, 0)},
            {"id": "trials", "label": "Trials", "overlay": "trials", "shortcut": pygame.K_t, "rect": pygame.Rect(0, 0, 0, 0)},
            {"id": "recipes", "label": "Recipes", "overlay": "craft_book", "shortcut": pygame.K_r, "rect": pygame.Rect(0, 0, 0, 0)},
            {"id": "menu", "label": "Menu", "action": "main_menu", "shortcut": pygame.K_m, "rect": pygame.Rect(0, 0, 0, 0)},
        ]
        self.show_collision_debug = False

    def handle_event(self, event):
        if self.active_overlay is not None:
            self._handle_overlay_event(event)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            action = self._get_quick_action_at(event.pos)
            if action is not None:
                self._activate_quick_action(action)
            return

        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self.game.state = "main_menu"
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

    def _handle_overlay_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            action = self._get_quick_action_at(event.pos)
            if action is not None:
                self._activate_quick_action(action)
                return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._close_active_overlay()
                return
            shortcut_action = self._get_quick_action_for_key(event.key)
            if shortcut_action is not None and shortcut_action.get("overlay"):
                self._activate_quick_action(shortcut_action)
                return

        overlay = self._get_active_overlay()
        if overlay is not None:
            overlay.handle_event(event)
            if not overlay.is_open():
                self.active_overlay = None
        else:
            self.active_overlay = None

    def update(self):
        if self.active_overlay is not None:
            return

        self.player_is_moving = False
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
            self.player_is_moving = True
            speed = self.player_run_speed if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else self.player_walk_speed
            self._move_player(movement, speed)

    def draw(self, screen):
        current_time_ms = pygame.time.get_ticks()
        self._update_camera(screen)
        self._draw_map(screen)
        self._draw_player(screen)
        self._draw_collision_debug(screen)
        if not self._is_overlay_open():
            self._draw_help_panel(screen, current_time_ms)
        self._draw_quick_action_bar(screen)
        overlay = self._get_active_overlay()
        if overlay is not None:
            overlay.draw(screen)

    def _move_player(self, movement, speed):
        if abs(movement.x) > abs(movement.y):
            self.player_facing = "right" if movement.x > 0 else "left"
        elif movement.y != 0:
            self.player_facing = "down" if movement.y > 0 else "up"

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

    def _load_map(self, map_id, spawn_id=None):
        map_id = self._clean_tiled_value(map_id)
        spawn_id = self._clean_tiled_value(spawn_id)
        if map_id is None:
            self.spawn_debug_message = "Map id missing."
            self._show_temporary_message(self.spawn_debug_message)
            return False

        loaded_map = TiledMap(self.map_directory / f"{map_id}.tmx")
        self.map = loaded_map
        self.current_map_id = map_id
        self.map_width = loaded_map.pixel_width if loaded_map.is_loaded else 800
        self.map_height = loaded_map.pixel_height if loaded_map.is_loaded else 600
        self.obstacles = list(loaded_map.collision_rects) if loaded_map.is_loaded else []
        self.collision_polygons = list(loaded_map.collision_polygons) if loaded_map.is_loaded else []
        self.triggers = list(loaded_map.triggers) if loaded_map.is_loaded else []

        self.player_position, spawn = self._get_spawn_position(spawn_id)
        self.active_spawn_id = spawn.get("spawn_id") if spawn is not None else None
        if spawn is not None:
            self.player_facing = self._normalize_player_facing(spawn.get("facing"))
        self._sync_player_rect_from_position()
        self.camera_offset.update(0, 0)

        if not loaded_map.is_loaded:
            self.spawn_debug_message = loaded_map.error_message or f"Map {map_id} unavailable."
            self._show_temporary_message(self.spawn_debug_message)
            return False

        self._show_temporary_message(self.spawn_debug_message)
        return True

    def _get_spawn_position(self, spawn_id=None):
        spawn_id = self._clean_tiled_value(spawn_id)
        spawn = None
        if self.map is not None and self.map.is_loaded:
            if spawn_id is not None:
                spawn = self.map.spawns.get(spawn_id)
                if spawn is None:
                    self.spawn_debug_message = f"Spawn {spawn_id} not found. Using fallback."
            if spawn is None:
                spawn = self.map.spawns.get("player_start")
                if spawn is not None and spawn_id is None:
                    self.spawn_debug_message = "Spawn player_start loaded."

        if spawn is not None:
            if spawn_id is not None and spawn.get("spawn_id") == spawn_id:
                self.spawn_debug_message = f"Spawn {spawn_id} loaded."
            return pygame.Vector2(spawn["x"], spawn["y"]), spawn

        spawn_ids = sorted(self.map.spawns.keys()) if self.map is not None and self.map.is_loaded else []
        if spawn_id is None:
            if spawn_ids:
                self.spawn_debug_message = f"player_start not found. Found: {', '.join(spawn_ids)}"
            else:
                self.spawn_debug_message = "No Tiled spawns found."
        return pygame.Vector2(self.map_width / 2, self.map_height / 2), None

    def _clean_tiled_value(self, value):
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    def _normalize_player_facing(self, facing):
        facing = self._clean_tiled_value(facing)
        if facing is None:
            return "down"

        directions = {
            "north": "up",
            "south": "down",
            "west": "left",
            "east": "right",
            "up": "up",
            "down": "down",
            "left": "left",
            "right": "right",
        }
        return directions.get(facing.lower(), "down")

    def _show_temporary_message(self, message, duration_ms=2200):
        message = self._clean_tiled_value(message)
        if message is None:
            return
        self.message = message
        self.message_until_ms = pygame.time.get_ticks() + duration_ms

    def _clamp_player_position(self, position, bounds):
        half_width = self.player_hitbox_size.x / 2
        half_height = self.player_hitbox_size.y / 2
        return pygame.Vector2(
            min(max(position.x, bounds.left + half_width), bounds.right - half_width),
            min(max(position.y, bounds.top + half_height), bounds.bottom - half_height),
        )

    def _get_active_trigger(self):
        reach_rect = self._get_trigger_reach_rect()
        reachable_trigger = None
        for trigger in self.triggers:
            trigger_rect = trigger["rect"]
            if self.player_rect.colliderect(trigger_rect):
                return trigger
            if trigger.get("requires_interact") and reachable_trigger is None and reach_rect.colliderect(trigger_rect):
                reachable_trigger = trigger
        return reachable_trigger

    def _get_trigger_reach_rect(self):
        return self.player_rect.inflate(24, 24)

    def _activate_trigger(self, trigger):
        trigger_type = self._clean_tiled_value(trigger.get("trigger_type"))
        if trigger_type == "state_transition":
            target_map = self._clean_tiled_value(trigger.get("target_map"))
            if target_map:
                self._load_map(target_map, trigger.get("target_spawn_id"))
                return

            target_state = self._clean_tiled_value(trigger.get("target_state"))
            if target_state == "crafting":
                self._open_craft_book_overlay(allow_craft=True)
                return
            if target_state:
                self.game.state = target_state
                return

        prompt = self._clean_tiled_value(trigger.get("prompt"))
        if prompt:
            self._show_temporary_message(prompt)
            return

        self._show_temporary_message("Trigger non configure.")

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
        overlay = action.get("overlay")
        if overlay:
            self._toggle_overlay(overlay)
            return

        if action.get("action") == "main_menu":
            self.game.state = "main_menu"
            return

        if action.get("action") == "return_to_town":
            self.game.return_to_town()
            return

        target_state = action.get("target_state")
        if target_state:
            self.game.state = target_state

    def _toggle_overlay(self, overlay_id):
        if overlay_id not in {"inventory", "quests", "achievements", "skills", "professions", "craft_book", "trials"}:
            return
        if self.active_overlay == overlay_id:
            self._close_active_overlay()
            return
        self._open_overlay(overlay_id)

    def _open_overlay(self, overlay_id):
        if overlay_id == "craft_book":
            self._open_craft_book_overlay(allow_craft=False)
            return
        overlay = self._get_overlay(overlay_id)
        if overlay is None:
            return
        self._close_active_overlay()
        overlay.open()
        self.active_overlay = overlay_id

    def _open_craft_book_overlay(self, allow_craft=False):
        self._close_active_overlay()
        self.craft_book_overlay.open(allow_craft=allow_craft)
        self.active_overlay = "craft_book"

    def _close_overlay(self):
        self._close_active_overlay()

    def _close_active_overlay(self):
        overlay = self._get_active_overlay()
        if overlay is not None:
            overlay.close()
        self.active_overlay = None

    def _is_overlay_open(self):
        overlay = self._get_active_overlay()
        return overlay is not None and overlay.is_open()

    def _get_active_overlay(self):
        return self._get_overlay(self.active_overlay)

    def _get_overlay(self, overlay_id):
        overlays = {
            "inventory": self.inventory_overlay,
            "quests": self.quest_overlay,
            "achievements": self.achievement_overlay,
            "skills": self.skill_overlay,
            "professions": self.profession_overlay,
            "craft_book": self.craft_book_overlay,
            "trials": self.trials_overlay,
        }
        return overlays.get(overlay_id)

    def _update_camera(self, screen):
        max_x = max(0, self.map_width - screen.get_width())
        gameplay_height = max(1, screen.get_height() - self._get_bottom_bar_height())
        max_y = max(0, self.map_height - gameplay_height)
        self.camera_offset.x = min(max(self.player_rect.centerx - screen.get_width() // 2, 0), max_x)
        self.camera_offset.y = min(max(self.player_rect.centery - gameplay_height // 2, 0), max_y)

    def _get_bottom_bar_height(self):
        return 52

    def _draw_map(self, screen):
        if self.map.is_loaded:
            screen.fill((18, 28, 22))
            self.map.draw(screen, (int(self.camera_offset.x), int(self.camera_offset.y)))
            return

        screen.fill((23, 54, 35))
        for y in range(0, screen.get_height(), 8):
            shade = 28 + int(y * 0.025)
            pygame.draw.rect(screen, (18, min(72, shade + 28), 35), (0, y, screen.get_width(), 8))

    def _draw_player(self, screen):
        hitbox_rect = self._to_screen_rect(self.player_rect)
        draw_rect = self._to_screen_rect(self._get_player_draw_rect())
        pygame.draw.ellipse(screen, (10, 25, 18), hitbox_rect.inflate(8, 2))

        player_frame = self._get_player_frame()
        if player_frame is not None:
            screen.blit(player_frame, draw_rect)
            return

        pygame.draw.rect(screen, (66, 122, 166), draw_rect, border_radius=3)
        pygame.draw.circle(screen, (226, 188, 140), (draw_rect.centerx, draw_rect.y + 5), 5)

    def _load_player_animations(self):
        animations = {}
        for state in ("idle", "walk"):
            animations[state] = {}
            loaded_frames = {}
            for direction in ("down", "up", "side", "right", "left"):
                sheet_path = Path(f"assets/sprites/player/base/{state}/{state}_{direction}_sheet.png")
                frames = self._load_player_animation_sheet(sheet_path)
                if frames:
                    loaded_frames[direction] = frames

            for direction in ("down", "up"):
                if direction in loaded_frames:
                    animations[state][direction] = loaded_frames[direction]
            if "right" in loaded_frames:
                animations[state]["right"] = loaded_frames["right"]
            elif "side" in loaded_frames:
                animations[state]["right"] = loaded_frames["side"]
            if "left" in loaded_frames:
                animations[state]["left"] = loaded_frames["left"]
            elif "side" in loaded_frames:
                animations[state]["left"] = self._flip_frames_horizontally(loaded_frames["side"])
        return animations

    def _load_player_animation_sheet(self, path):
        try:
            sheet = pygame.image.load(str(path)).convert_alpha()
            frame_size = sheet.get_height()
            if frame_size <= 0:
                return []

            frame_count = sheet.get_width() // frame_size
            frames = []
            for frame_index in range(frame_count):
                frame_rect = pygame.Rect(frame_index * frame_size, 0, frame_size, frame_size)
                frame = sheet.subsurface(frame_rect).copy()
                content_rect = frame.get_bounding_rect(min_alpha=1)
                if content_rect.width > 0 and content_rect.height > 0:
                    frame = frame.subsurface(content_rect).copy()
                frames.append(
                    pygame.transform.scale(
                        frame,
                        (int(self.player_visual_size.x), int(self.player_visual_size.y)),
                    )
                )
            return frames
        except (OSError, pygame.error, ValueError):
            return []

    def _flip_frames_horizontally(self, frames):
        return [pygame.transform.flip(frame, True, False) for frame in frames]

    def _get_player_frame(self):
        state = "walk" if self.player_is_moving else "idle"
        self.player_animation_state = state
        self.player_facing = self._normalize_player_facing(self.player_facing)

        frames = self.player_animations.get(state, {}).get(self.player_facing)
        if not frames:
            frames = self.player_animations.get("idle", {}).get("down")
        if not frames:
            return None

        frame_index = (pygame.time.get_ticks() // self.player_animation_frame_duration_ms) % len(frames)
        return frames[frame_index]

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
        bar_height = self._get_bottom_bar_height()
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
            is_active = action.get("overlay") == self.active_overlay
            fill_color = (52, 65, 58) if is_active else (42, 50, 50) if is_hovered else (26, 31, 32)
            outline_color = (220, 214, 132) if is_active else (184, 202, 150) if is_hovered else (82, 96, 88)
            pygame.draw.rect(screen, fill_color, rect, border_radius=6)
            pygame.draw.rect(screen, outline_color, rect, 2, border_radius=6)
            self._draw_quick_action_icon(screen, action, rect, is_hovered or is_active)

        if hovered_action is not None and self._get_active_trigger() is None:
            self._draw_quick_action_tooltip(screen, hovered_action, bar_rect)

    def _draw_quick_action_icon(self, screen, action, rect, is_hovered):
        icon_colors = {
            "inventory": (229, 181, 82),
            "quests": (223, 196, 139),
            "skills": (102, 170, 232),
            "achievements": (240, 199, 78),
            "professions": (184, 152, 104),
            "trials": (218, 176, 72),
            "recipes": (134, 193, 119),
            "menu": (158, 151, 134),
        }
        base_color = icon_colors.get(action["id"], (204, 214, 190))
        color = tuple(min(255, component + 24) for component in base_color) if is_hovered else base_color
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
        elif action_id == "trials":
            base = pygame.Rect(rect.x + 12, rect.y + 30, 20, 4)
            pygame.draw.rect(screen, color, base, border_radius=2)
            pygame.draw.rect(screen, color, (center[0] - 3, rect.y + 18, 6, 12), border_radius=2)
            pygame.draw.polygon(screen, color, [(center[0], rect.y + 9), (center[0] + 10, rect.y + 16), (center[0] + 6, rect.y + 28), (center[0] - 6, rect.y + 28), (center[0] - 10, rect.y + 16)])
            pygame.draw.polygon(screen, shadow, [(center[0], rect.y + 14), (center[0] + 4, rect.y + 18), (center[0], rect.y + 22), (center[0] - 4, rect.y + 18)])
        elif action_id == "recipes":
            left_page = pygame.Rect(rect.x + 11, rect.y + 12, 11, 22)
            right_page = pygame.Rect(rect.x + 22, rect.y + 12, 11, 22)
            pygame.draw.rect(screen, color, left_page, border_radius=2)
            pygame.draw.rect(screen, color, right_page, border_radius=2)
            pygame.draw.line(screen, shadow, (rect.x + 22, rect.y + 13), (rect.x + 22, rect.y + 34), 1)
            pygame.draw.line(screen, shadow, (rect.x + 14, rect.y + 19), (rect.x + 19, rect.y + 19), 1)
            pygame.draw.line(screen, shadow, (rect.x + 25, rect.y + 24), (rect.x + 30, rect.y + 24), 1)
        elif action_id == "menu":
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
        if self.message_until_ms and current_time_ms > self.message_until_ms:
            self.message = self.default_message
            self.message_until_ms = 0
        active_trigger = self._get_active_trigger()
        hovered_action = self._get_hovered_quick_action()
        if active_trigger is not None and self._clean_tiled_value(active_trigger.get("prompt")):
            text = self._clean_tiled_value(active_trigger.get("prompt"))
        elif active_trigger is not None and active_trigger.get("requires_interact"):
            text = "E - Interagir"
        elif hovered_action is not None:
            shortcut = pygame.key.name(hovered_action["shortcut"]).upper()
            text = f"{hovered_action['label']} ({shortcut})"
        elif not self.map.is_loaded:
            text = "Map Tiled indisponible. Affichage de secours actif."
        else:
            return

        bar_height = self._get_bottom_bar_height()
        body_width = min(screen.get_width() - 48, max(260, self.body_font.size(text)[0] + 24))
        panel = pygame.Rect(24, screen.get_height() - bar_height - 36, body_width, 28)
        pygame.draw.rect(screen, (18, 21, 18), panel, border_radius=7)
        pygame.draw.rect(screen, (104, 139, 90), panel, 1, border_radius=7)
        body = self.body_font.render(self._fit_panel_text(text, panel.width - 18), True, (220, 220, 205))
        screen.blit(body, (panel.x + 9, panel.y + 6))

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
