import random

from core.dataManager import DataManager
from entities.enemy import create_enemy
from entities.players import create_player
from systems.combat import CombatSystem
from systems.inventory import add_drops_to_inventory
from systems.loot import generate_combat_loot
from systems.progression import apply_combat_rewards
from systems.stats import prepare_player_for_combat


class Game:
    def __init__(self):
        self.data = DataManager()

        self.player = None
        self.selected_class = None
        self.selected_zone = None
        self.state = "class_select"
        self.auto_mode = False
        self.combat = None
        self.last_combat_result = None

    def select_class(self, class_key):
        if class_key not in self.data.classes:
            return

        self.selected_class = class_key
        self.player = create_player(
            char_class=class_key,
            classes=self.data.classes,
            items=self.data.items,
        )
        self.state = "zone_select"

    def select_zone(self, zone_key):
        if not self.player or zone_key not in self.data.zones:
            return

        zone = self.data.zones[zone_key]
        if self.player["level"] < zone["unlock_level"]:
            return

        self.selected_zone = zone_key
        self.start_combat()

    def start_combat(self):
        enemy = self.spawn_enemy()

        prepare_player_for_combat(self.player, self.data.items, self.data.classes)
        self.combat = CombatSystem(self.player, enemy)
        self.state = "combat"

    def update_combat(self, action=None):
        if self.auto_mode:
            action = "attack"

        if action and self.combat:
            self.combat.step(action)

        if self.combat and self.combat.is_over:
            print("Combat termine")
            if self.combat.winner == "player":
                self.last_combat_result = apply_combat_rewards(
                    self.player,
                    self.combat.enemy,
                )
                drops = generate_combat_loot(self.combat.enemy)
                self.last_combat_result["drops"] = drops
                self.last_combat_result["inventory_result"] = add_drops_to_inventory(
                    self.player["inventory"],
                    drops,
                )
            else:
                self.last_combat_result = {
                    "exp_gained": 0,
                    "gold_gained": 0,
                    "leveled_up": False,
                    "drops": [],
                    "inventory_result": {"added": [], "failed": []},
                }
            self.state = "combat_result"
            self.auto_mode = False

    def continue_after_combat_result(self):
        self.state = "zone_select"
        self.combat = None
        self.auto_mode = False

    def spawn_enemy(self):
        if self.selected_zone:
            zone = self.data.zones[self.selected_zone]
            enemy_key = random.choice(zone["enemy_pool"])
            enemy_template = self.data.enemies[enemy_key]
            enemy = create_enemy(enemy_template, self.player["level"])
            multiplier = zone.get("difficulty_multiplier", 1.0)
            enemy["max_hp"] = int(enemy["max_hp"] * multiplier)
            enemy["current_hp"] = enemy["max_hp"]
            enemy["attack"] = int(enemy["attack"] * multiplier)
            enemy["defense"] = int(enemy["defense"] * multiplier)
            return enemy

        enemy_template = random.choice(list(self.data.enemies.values()))
        return create_enemy(enemy_template, self.player["level"])
