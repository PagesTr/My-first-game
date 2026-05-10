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
from systems.dungeons import (
    apply_rest_choice,
    calculate_boss_multiplier,
    calculate_boss_reward_multiplier,
    create_dungeon_state,
    get_dungeon,
    get_next_dungeon_step,
    is_boss_loop_step,
    is_rest_choice_step,
)
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
        self.data.dungeons = self.data.load("data/dungeons.json")

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
        self.last_dungeon_result = None
        self.active_gathering = None
        self.active_dungeon = None
        self.return_state_after_inventory = None
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
        self.last_dungeon_result = None
        self.active_gathering = None
        self.active_dungeon = None
        self.return_state_after_inventory = None
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

    def get_available_dungeons(self, region_id=None):
        dungeons = getattr(self.data, "dungeons", {}) or {}
        if not isinstance(dungeons, dict):
            return []
        available = []
        for dungeon_id, dungeon in dungeons.items():
            if not isinstance(dungeon, dict):
                continue
            if region_id is not None and dungeon.get("chapter") != region_id:
                continue
            available.append({
                "dungeon_id": dungeon_id,
                "dungeon": dungeon,
            })
        return available

    def get_active_dungeon_summary(self):
        if not isinstance(self.active_dungeon, dict):
            return {"active": False}

        dungeon_id = self.active_dungeon.get("dungeon_id")
        dungeon = get_dungeon(getattr(self.data, "dungeons", {}), dungeon_id) or {}
        return {
            "active": True,
            "dungeon_id": dungeon_id,
            "dungeon_name": dungeon.get("name", dungeon_id),
            "step": self.get_active_dungeon_step(),
            "step_index": self.active_dungeon.get("step_index", 0),
            "boss_victories": self.active_dungeon.get("boss_victories", 0),
            "completed": self.active_dungeon.get("completed", False),
            "failed": self.active_dungeon.get("failed", False),
        }

    def open_inventory_from_dungeon(self):
        self.return_state_after_inventory = "dungeon"
        self.state = "inventory"

    def return_from_inventory_if_needed(self):
        if getattr(self, "return_state_after_inventory", None) == "dungeon":
            self.state = "dungeon"
            self.return_state_after_inventory = None
            return True
        return False

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

    def start_dungeon(self, dungeon_id):
        if not self.player:
            return {"started": False, "reason": "invalid_player"}

        dungeon = get_dungeon(getattr(self.data, "dungeons", {}), dungeon_id)
        if dungeon is None:
            return {"started": False, "reason": "unknown_dungeon"}
        if self.player.get("level", 1) < dungeon.get("unlock_level", 1):
            return {"started": False, "reason": "locked_dungeon"}

        self.last_dungeon_result = None
        self.active_dungeon = create_dungeon_state(dungeon_id)
        self._ensure_active_dungeon_run_counters()
        self.player["current_hp"] = self.player.get("max_hp", self.player.get("current_hp", 0))
        if hasattr(self, "save_current_game"):
            self.save_current_game()
        if self.state == "dungeon":
            self.state = "dungeon"
        else:
            self.state = "town"
        return {"started": True, "dungeon_id": dungeon_id}

    def get_active_dungeon_step(self):
        if not isinstance(self.active_dungeon, dict):
            return None
        dungeon = get_dungeon(
            getattr(self.data, "dungeons", {}),
            self.active_dungeon.get("dungeon_id"),
        )
        if dungeon is None:
            return None
        return get_next_dungeon_step(
            dungeon,
            self.active_dungeon.get("step_index", 0),
        )

    def resolve_dungeon_combat_step(self):
        if not isinstance(self.active_dungeon, dict):
            return {"resolved": False, "reason": "no_active_dungeon"}

        step = self.get_active_dungeon_step()
        if not isinstance(step, dict) or step.get("type") != "combat":
            return {"resolved": False, "reason": "not_combat_step"}

        enemy_id = step.get("enemy_id")
        result = self._run_single_dungeon_combat(enemy_id)
        result["resolved"] = True
        if result.get("won") is True:
            self._record_dungeon_victory(result, enemy_id)
            self.active_dungeon["step_index"] += 1
            self.record_quest_event({
                "type": "kill_enemy",
                "target": enemy_id,
                "amount": 1,
            })
        else:
            self.active_dungeon["failed"] = True
            self.last_dungeon_result = self._build_dungeon_result(
                "combat_defeat",
                enemy_id,
                won=False,
            )

        if result.get("won") is True:
            self.last_dungeon_result = result
        if hasattr(self, "save_current_game"):
            self.save_current_game()
        return result

    def apply_dungeon_rest_choice(self, choice):
        if not isinstance(self.active_dungeon, dict):
            return {"applied": False, "choice": choice, "reason": "no_active_dungeon"}

        step = self.get_active_dungeon_step()
        if not is_rest_choice_step(step):
            return {
                "applied": False,
                "choice": choice,
                "healed": 0,
                "loot_bonus": False,
                "reason": "not_rest_choice_step",
            }

        result = apply_rest_choice(self.player, choice)
        if result.get("applied") is True:
            self.active_dungeon["rest_choice_used"] = True
            self.active_dungeon["rest_choice"] = choice
            self.active_dungeon["step_index"] += 1
            if hasattr(self, "save_current_game"):
                self.save_current_game()
        return result

    def resolve_dungeon_boss_step(self):
        if not isinstance(self.active_dungeon, dict):
            return {"resolved": False, "reason": "no_active_dungeon"}

        dungeon = get_dungeon(
            getattr(self.data, "dungeons", {}),
            self.active_dungeon.get("dungeon_id"),
        )
        step = self.get_active_dungeon_step()
        if dungeon is None or not is_boss_loop_step(step):
            return {"resolved": False, "reason": "not_boss_loop_step"}

        boss_enemy_id = step.get("enemy_id") or dungeon.get("boss_enemy_id")
        victories = self.active_dungeon.get("boss_victories", 0)
        boss_multiplier = calculate_boss_multiplier(
            victories,
            dungeon.get("scaling_rate", 0),
        )
        result = self._run_single_dungeon_combat(boss_enemy_id, boss_multiplier)
        result["resolved"] = True
        result["boss_multiplier"] = boss_multiplier

        if result.get("won") is True:
            reward_multiplier = calculate_boss_reward_multiplier(
                victories,
                dungeon.get("reward_multiplier_per_victory", 0),
            )
            self._apply_extra_dungeon_reward_multiplier(result, reward_multiplier)
            self._record_dungeon_victory(result, boss_enemy_id)
            self.active_dungeon["boss_victories"] = victories + 1
            result["boss_victories"] = self.active_dungeon["boss_victories"]
            result["reward_multiplier"] = reward_multiplier
            self.last_dungeon_result = result
            if boss_enemy_id == "grubfang_rootcaller":
                self.record_quest_event({
                    "type": "defeat_boss",
                    "target": "grubfang_rootcaller",
                    "amount": 1,
                })
            if hasattr(self, "save_current_game"):
                self.save_current_game()
            return result

        self.active_dungeon["failed"] = True
        self.active_dungeon["completed"] = True
        result["completed"] = True
        result["boss_victories"] = victories
        dungeon_id = self.active_dungeon.get("dungeon_id")
        self.last_dungeon_result = self._build_dungeon_result(
            "boss_defeat",
            boss_enemy_id,
            won=False,
        )
        self.last_dungeon_result.update({
            "resolved": True,
            "enemy_id": result.get("enemy_id"),
            "enemy_name": result.get("enemy_name"),
        })
        self.record_quest_event({
            "type": "clear_dungeon",
            "target": dungeon_id,
            "amount": 1,
        })
        self.active_dungeon = None
        self.state = "dungeon"
        if hasattr(self, "save_current_game"):
            self.save_current_game()
        return result

    def get_last_dungeon_result(self):
        return self.last_dungeon_result

    def _ensure_active_dungeon_run_counters(self):
        if not isinstance(self.active_dungeon, dict):
            return
        self.active_dungeon.setdefault("rooms_cleared", 0)
        self.active_dungeon.setdefault("total_gold", 0)
        self.active_dungeon.setdefault("total_exp", 0)
        self.active_dungeon.setdefault("loot", [])
        self.active_dungeon.setdefault("rest_choice", None)
        self.active_dungeon.setdefault("last_enemy", None)

    def _record_dungeon_victory(self, result, enemy_id):
        if not isinstance(self.active_dungeon, dict) or not isinstance(result, dict):
            return
        self._ensure_active_dungeon_run_counters()
        self.active_dungeon["rooms_cleared"] += 1
        self.active_dungeon["total_gold"] += int(result.get("gold", 0))
        self.active_dungeon["total_exp"] += int(result.get("exp", 0))
        self.active_dungeon["loot"].extend(list(result.get("drops", [])))
        self.active_dungeon["last_enemy"] = enemy_id

    def _build_dungeon_result(self, reason, defeated_by, won=False):
        dungeon = self.active_dungeon if isinstance(self.active_dungeon, dict) else {}
        return {
            "completed": True,
            "won": won,
            "reason": reason,
            "dungeon_id": dungeon.get("dungeon_id"),
            "defeated_by": defeated_by,
            "rooms_cleared": dungeon.get("rooms_cleared", 0),
            "boss_victories": dungeon.get("boss_victories", 0),
            "total_gold": dungeon.get("total_gold", 0),
            "total_exp": dungeon.get("total_exp", 0),
            "loot": list(dungeon.get("loot", [])),
            "rest_choice": dungeon.get("rest_choice"),
        }

    def _run_single_dungeon_combat(self, enemy_id, multiplier=1.0):
        if not self.player or enemy_id not in self.data.enemies:
            return {
                "won": False,
                "enemy_id": enemy_id,
                "enemy_name": enemy_id or "Unknown Enemy",
                "exp": 0,
                "gold": 0,
                "drops": [],
                "reason": "unknown_enemy",
            }

        enemy = create_enemy(self.data.enemies[enemy_id], self.player.get("level", 1))
        self._scale_dungeon_enemy(enemy, multiplier)
        prepare_player_for_combat(
            self.player,
            self.data.items,
            self.data.classes,
            self.data.skills,
        )
        combat = CombatSystem(self.player, enemy, self.data.skills)
        turns = 0
        while not combat.is_over and turns < 300:
            combat.step()
            turns += 1

        if not combat.is_over:
            self.player["current_hp"] = 0
            return {
                "won": False,
                "enemy_id": enemy_id,
                "enemy_name": enemy.get("name", enemy_id),
                "exp": 0,
                "gold": 0,
                "drops": [],
                "reason": "turn_limit",
            }
        if combat.winner != "player":
            return {
                "won": False,
                "enemy_id": enemy_id,
                "enemy_name": enemy.get("name", enemy_id),
                "exp": 0,
                "gold": 0,
                "drops": [],
            }

        reward_result = apply_combat_rewards(self.player, enemy)
        drops = generate_combat_loot(enemy, self.data.items, self.player)
        return {
            "won": True,
            "enemy_id": enemy_id,
            "enemy_name": enemy.get("name", enemy_id),
            "exp": reward_result.get("exp_gained", 0),
            "gold": reward_result.get("gold_gained", 0),
            "drops": drops,
            "inventory_result": {
                "added": [],
                "failed": [],
                "pending": list(drops),
            },
        }

    def _scale_dungeon_enemy(self, enemy, multiplier):
        if not isinstance(multiplier, (int, float)) or multiplier <= 0:
            multiplier = 1.0
        for stat in ("max_hp", "attack", "defense", "exp", "gold"):
            enemy[stat] = max(1, int(enemy.get(stat, 1) * multiplier))
        enemy["current_hp"] = enemy["max_hp"]

    def _apply_extra_dungeon_reward_multiplier(self, result, reward_multiplier):
        if not isinstance(reward_multiplier, (int, float)) or reward_multiplier <= 1:
            return
        base_exp = int(result.get("exp", 0))
        base_gold = int(result.get("gold", 0))
        total_exp = int(base_exp * reward_multiplier)
        total_gold = int(base_gold * reward_multiplier)
        bonus_exp = max(0, total_exp - base_exp)
        bonus_gold = max(0, total_gold - base_gold)
        self.player["exp"] = self.player.get("exp", 0) + bonus_exp
        self.player["gold"] = self.player.get("gold", 0) + bonus_gold
        result["exp"] = total_exp
        result["gold"] = total_gold

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
