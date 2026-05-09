import random

from core.dataManager import DataManager
from entities.enemy import create_enemy
from entities.players import create_player
from systems.combat import CombatSystem
from systems.effects import tick_combat_effects
from systems.gathering import gather_from_zone
from systems.inventory import (
    claim_all_pending_drops,
    claim_pending_drop,
    move_inventory_slot_to_pending,
    swap_pending_drop_with_inventory_slot,
)
from systems.instance import run_instant_instance
from systems.loot import generate_combat_loot
from systems.mailbox import add_mail, create_combat_report_mail, create_mailbox
from systems.progression import apply_combat_rewards
from systems.stats import prepare_player_for_combat


class Game:
    def __init__(self):
        self.data = DataManager()

        self.player = None
        self.selected_class = None
        self.selected_zone = None
        self.state = "main_menu"
        self.auto_mode = False
        self.combat = None
        self.last_combat_result = None
        self.last_instance_result = None
        self.last_gathering_result = None
        self.mailbox = create_mailbox()

    def start_new_game(self):
        self.player = None
        self.selected_class = None
        self.selected_zone = None
        self.auto_mode = False
        self.combat = None
        self.last_combat_result = None
        self.last_instance_result = None
        self.last_gathering_result = None
        self.mailbox = create_mailbox()
        self.state = "class_select"

    def select_class(self, class_key):
        if class_key not in self.data.classes:
            return

        self.selected_class = class_key
        self.player = create_player(
            char_class=class_key,
            classes=self.data.classes,
            items=self.data.items,
            professions_data=self.data.professions,
        )
        prepare_player_for_combat(
            self.player,
            self.data.items,
            self.data.classes,
            self.data.skills,
        )
        self.state = "town"

    def select_zone_for_actions(self, zone_key):
        if not self.player or zone_key not in self.data.zones:
            return False

        zone = self.data.zones[zone_key]
        if self.player["level"] < zone.get("unlock_level", 1):
            return False

        self.selected_zone = zone_key
        self.state = "zone_actions"
        return True

    def select_zone(self, zone_key):
        if not self.player or zone_key not in self.data.zones:
            return

        zone = self.data.zones[zone_key]
        if self.player["level"] < zone["unlock_level"]:
            return

        self.selected_zone = zone_key
        prepare_player_for_combat(
            self.player,
            self.data.items,
            self.data.classes,
            self.data.skills,
        )
        self.last_instance_result = run_instant_instance(
            self.player,
            zone_key,
            self.data.zones,
            self.data.enemies,
            self.data.items,
            self.data.skills,
        )
        self.last_combat_result = self.last_instance_result
        self.combat = None
        self.auto_mode = False
        self.state = "combat_result"

    def gather_in_zone(self, zone_key, profession_id):
        if not self.player or zone_key not in self.data.zones:
            result = {"gathered": False, "reason": "invalid_zone"}
            self.last_gathering_result = result
            return result

        zone = self.data.zones[zone_key]
        if self.player["level"] < zone.get("unlock_level", 1):
            result = {"gathered": False, "reason": "locked_zone"}
            self.last_gathering_result = result
            return result

        result = gather_from_zone(
            self.player,
            self.player["inventory"],
            zone_key,
            profession_id,
            self.data.gathering_nodes,
            self.data.professions,
            self.data.items,
        )
        self.last_gathering_result = result
        self.selected_zone = zone_key
        self.state = "zone_actions"
        return result

    def get_available_gathering_professions(self, zone_key):
        gathering_nodes = getattr(self.data, "gathering_nodes", {}) or {}
        if not isinstance(gathering_nodes, dict):
            return {}

        zone_nodes = gathering_nodes.get(zone_key, {})
        if not isinstance(zone_nodes, dict):
            return {}
        return zone_nodes

    def start_combat(self):
        enemy = self.spawn_enemy()

        prepare_player_for_combat(
            self.player,
            self.data.items,
            self.data.classes,
            self.data.skills,
        )
        self.combat = CombatSystem(self.player, enemy, self.data.skills)
        self.state = "combat"

    def update_combat(self, action=None):
        if self.combat and (action is not None or self.auto_mode):
            self.combat.step(action)

        if self.combat and self.combat.is_over:
            print("Combat termine")
            if self.combat.winner == "player":
                self.last_combat_result = apply_combat_rewards(
                    self.player,
                    self.combat.enemy,
                )
                drops = generate_combat_loot(
                    self.combat.enemy,
                    self.data.items,
                    self.player,
                )
                self.last_combat_result["drops"] = drops
                self.last_combat_result["inventory_result"] = {
                    "added": [],
                    "failed": [],
                    "pending": list(drops),
                }
            else:
                self.last_combat_result = {
                    "exp_gained": 0,
                    "gold_gained": 0,
                    "leveled_up": False,
                    "drops": [],
                    "inventory_result": {"added": [], "failed": [], "pending": []},
                }
            combat_report = self.combat.get_combat_report()
            mail = create_combat_report_mail(combat_report, self.last_combat_result)
            add_mail(self.mailbox, mail)
            self.last_combat_result["combat_report_mail"] = mail
            self.state = "combat_result"
            self.auto_mode = False

    def continue_after_combat_result(self):
        if self.player is not None:
            tick_combat_effects(self.player)
            prepare_player_for_combat(
                self.player,
                self.data.items,
                self.data.classes,
                self.data.skills,
            )
        self.state = "town"
        self.combat = None
        self.auto_mode = False

    def try_claim_combat_drop(self, drop_index):
        if self.last_combat_result is None or self.player is None:
            return False

        inventory = self.player.get("inventory")
        if not isinstance(inventory, dict):
            return False

        inventory_result = self.last_combat_result.get("inventory_result")
        if not isinstance(inventory_result, dict):
            return False

        return claim_pending_drop(inventory, inventory_result, drop_index)

    def try_claim_all_combat_drops(self):
        if self.last_combat_result is None or self.player is None:
            return False

        inventory = self.player.get("inventory")
        if not isinstance(inventory, dict):
            return False

        inventory_result = self.last_combat_result.get("inventory_result")
        if not isinstance(inventory_result, dict):
            return False

        return claim_all_pending_drops(inventory, inventory_result)

    def replace_inventory_item_with_pending_drop(self, drop_index, inventory_slot_index):
        if self.player is None or self.last_combat_result is None:
            return False

        inventory = self.player.get("inventory")
        if not isinstance(inventory, dict):
            return False

        slots = inventory.get("slots")
        if not isinstance(slots, list):
            return False

        if (
            not isinstance(inventory_slot_index, int)
            or inventory_slot_index < 0
            or inventory_slot_index >= len(slots)
        ):
            return False

        inventory_result = self.last_combat_result.get("inventory_result")
        if not isinstance(inventory_result, dict):
            return False

        return swap_pending_drop_with_inventory_slot(
            inventory,
            inventory_result,
            drop_index,
            inventory_slot_index,
        )

    def move_inventory_item_to_pending_loot(self, slot_index):
        if self.player is None or self.last_combat_result is None:
            return False

        inventory = self.player.get("inventory")
        if not isinstance(inventory, dict):
            return False

        inventory_result = self.last_combat_result.get("inventory_result")
        if not isinstance(inventory_result, dict):
            return False

        return move_inventory_slot_to_pending(inventory, inventory_result, slot_index)

    def discard_pending_combat_loot(self):
        if self.last_combat_result is None:
            return False

        inventory_result = self.last_combat_result.get("inventory_result")
        if not isinstance(inventory_result, dict):
            return False

        pending = inventory_result.get("pending")
        if not isinstance(pending, list):
            return False

        inventory_result.setdefault("discarded", []).extend(list(pending))
        pending.clear()
        return True

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
