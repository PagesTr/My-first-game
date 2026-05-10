import random

from core.dataManager import DataManager
from entities.enemy import create_enemy
from entities.players import create_player
from systems.active_gathering import (
    advance_active_gathering_tick,
    create_active_gathering_activity,
    get_active_gathering_remaining_ms as get_active_gathering_remaining_time_ms,
    get_node_tick_seconds,
    is_active_gathering_tick_ready,
    resolve_active_gathering_tick,
)
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
from systems.offline import (
    resolve_offline_activity,
    start_offline_gathering,
    stop_offline_activity,
)
from systems.progression import apply_combat_rewards
from systems.quests import ensure_player_quests, record_quest_event
from systems.save_load import load_data_from_file, save_game, validate_save_data
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
        self.last_offline_result = None
        self.active_gathering = None
        self.main_menu_message = ""
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
        self.last_offline_result = None
        self.active_gathering = None
        self.main_menu_message = ""
        self.mailbox = create_mailbox()
        self.state = "class_select"

    def save_current_game(self):
        if self.player is None:
            return False
        save_game(self)
        return True

    def load_saved_game(self):
        save_data = load_data_from_file()
        if not validate_save_data(save_data):
            return False

        self.selected_class = save_data.get("selected_class")
        self.selected_zone = save_data.get("selected_zone")
        self.player = save_data.get("player")
        ensure_player_quests(self.player, self.data.quests)
        self.mailbox = save_data.get("mailbox") or create_mailbox()
        self.combat = None
        self.auto_mode = False
        self.last_combat_result = None
        self.last_instance_result = None
        self.last_gathering_result = None
        self.active_gathering = None
        prepare_player_for_combat(
            self.player,
            self.data.items,
            self.data.classes,
            self.data.skills,
        )
        had_offline_activity = (
            isinstance(self.player, dict)
            and isinstance(self.player.get("offline_activity"), dict)
        )
        offline_result = self.resolve_offline_progress()
        self.last_offline_result = offline_result
        if had_offline_activity:
            self.player["offline_activity"] = None
            self.save_current_game()
        self.state = "town"
        return True

    def return_to_main_menu(self):
        if self.player is not None:
            self.save_current_game()
        self.active_gathering = None
        self.state = "main_menu"

    def select_class(self, class_key):
        if class_key not in self.data.classes:
            return

        self.selected_class = class_key
        self.player = create_player(
            char_class=class_key,
            classes=self.data.classes,
            items=self.data.items,
            professions_data=self.data.professions,
            quests_data=self.data.quests,
        )
        ensure_player_quests(self.player, self.data.quests)
        prepare_player_for_combat(
            self.player,
            self.data.items,
            self.data.classes,
            self.data.skills,
        )
        self.state = "town"
        self.save_current_game()

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
        enemy_pool = zone.get("enemy_pool", [])
        if (
            isinstance(enemy_pool, list)
            and len(enemy_pool) == 1
            and isinstance(self.last_instance_result, dict)
        ):
            self.record_quest_event({
                "type": "kill_enemy",
                "target": enemy_pool[0],
                "amount": int(self.last_instance_result.get("combats_won", 0)),
            })
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
        if result.get("gathered") is True:
            self._record_gathering_quest_progress(result)
            self.save_current_game()
        return result

    def get_available_gathering_professions(self, zone_key):
        gathering_nodes = getattr(self.data, "gathering_nodes", {}) or {}
        if not isinstance(gathering_nodes, dict):
            return {}

        zone_nodes = gathering_nodes.get(zone_key, {})
        if not isinstance(zone_nodes, dict):
            return {}
        return zone_nodes

    def start_active_gathering(self, zone_key, profession_id, current_time_ms):
        if not self.player:
            return {"started": False, "reason": "invalid_player"}
        if zone_key not in self.data.zones:
            return {"started": False, "reason": "invalid_zone"}

        zone = self.data.zones[zone_key]
        if self.player["level"] < zone.get("unlock_level", 1):
            return {"started": False, "reason": "locked_zone"}

        node = self.get_available_gathering_professions(zone_key).get(profession_id)
        if not isinstance(node, dict):
            return {"started": False, "reason": "unknown_node"}
        if self.active_gathering is not None:
            return {"started": False, "reason": "activity_already_active"}

        tick_seconds = get_node_tick_seconds(node)
        self.active_gathering = create_active_gathering_activity(
            zone_key,
            profession_id,
            current_time_ms,
            tick_seconds,
        )
        self.selected_zone = zone_key
        self.state = "zone_actions"
        return {"started": True, "activity": dict(self.active_gathering)}

    def stop_active_gathering(self):
        self.active_gathering = None
        return True

    def update_active_gathering(self, current_time_ms):
        if self.active_gathering is None:
            return None
        if not is_active_gathering_tick_ready(self.active_gathering, current_time_ms):
            return None

        result = resolve_active_gathering_tick(
            self.player,
            self.active_gathering,
            self.data.gathering_nodes,
            self.data.professions,
            self.data.items,
        )
        self.last_gathering_result = result
        if result.get("gathered") is True:
            advance_active_gathering_tick(self.active_gathering, current_time_ms)
            self._record_gathering_quest_progress(result)
            self.save_current_game()
            return result
        if result.get("reason") == "inventory_full":
            self.active_gathering = None
            self.save_current_game()
            return result

        self.active_gathering = None
        return result

    def get_active_gathering_remaining_ms(self, current_time_ms):
        if self.active_gathering is None:
            return 0
        return get_active_gathering_remaining_time_ms(
            self.active_gathering,
            current_time_ms,
        )

    def start_offline_gathering_activity(self, zone_key, profession_id):
        if not self.player:
            return {"started": False, "reason": "invalid_player"}
        if zone_key not in self.data.zones:
            return {"started": False, "reason": "invalid_zone"}

        zone = self.data.zones[zone_key]
        if self.player["level"] < zone.get("unlock_level", 1):
            return {"started": False, "reason": "locked_zone"}

        zone_nodes = self.get_available_gathering_professions(zone_key)
        if profession_id not in zone_nodes:
            return {"started": False, "reason": "unknown_node"}

        result = start_offline_gathering(self.player, zone_key, profession_id)
        if result.get("started") is True:
            self.save_current_game()
        return result

    def resolve_offline_progress(self):
        if not self.player:
            return {"resolved": False, "reason": "no_player"}

        result = resolve_offline_activity(
            self.player,
            self.data.gathering_nodes,
            self.data.professions,
            self.data.items,
        )
        if result.get("resolved") is True or result.get("reason") == "inventory_full":
            if result.get("resolved") is True:
                self._record_gathering_quest_progress(result)
            self.save_current_game()
        return result

    def record_quest_event(self, event):
        if not self.player:
            return {"updated": False, "completed": []}
        result = record_quest_event(self.player, self.data.quests, event)
        if result.get("updated") or result.get("completed"):
            self.save_current_game()
        return result

    def record_craft_quest_progress(self, recipe_id, craft_result):
        if not self.player or not isinstance(craft_result, dict):
            return {"updated": False, "completed": []}
        if craft_result.get("crafted") is not True:
            return {"updated": False, "completed": []}
        return self.record_quest_event({
            "type": "craft_recipe",
            "target": recipe_id,
            "amount": 1,
        })

    def _record_gathering_quest_progress(self, result):
        if not isinstance(result, dict):
            return []
        quest_results = []
        for reward in result.get("rewards", []):
            if not isinstance(reward, dict):
                continue
            item_id = reward.get("item")
            quantity = reward.get("quantity", 1)
            if item_id:
                quest_results.append(self.record_quest_event({
                    "type": "gather_item",
                    "target": item_id,
                    "amount": int(quantity),
                }))
        return quest_results

    def stop_offline_progress(self):
        if not self.player:
            return False

        stopped = stop_offline_activity(self.player)
        if stopped:
            self.save_current_game()
        return stopped

    def send_current_player_offline_gathering(self, zone_key, profession_id):
        self.active_gathering = None
        result = self.start_offline_gathering_activity(zone_key, profession_id)
        if result.get("started") is True:
            self.main_menu_message = "Offline gathering started"
            self.state = "main_menu"
        return result

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
        self.save_current_game()

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
