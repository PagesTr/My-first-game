import random

from core.dataManager import DataManager
from entities.enemy import create_enemy
from entities.players import create_player
from systems.combat import CombatSystem
from systems.effects import tick_combat_effects
from systems.inventory import add_stackable_item, add_unique_item
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
        self.state = "class_select"
        self.auto_mode = False
        self.combat = None
        self.last_combat_result = None
        self.mailbox = create_mailbox()

    def select_class(self, class_key):
        if class_key not in self.data.classes:
            return

        self.selected_class = class_key
        self.player = create_player(
            char_class=class_key,
            classes=self.data.classes,
            items=self.data.items,
        )
        prepare_player_for_combat(
            self.player,
            self.data.items,
            self.data.classes,
            self.data.skills,
        )
        self.state = "town"

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

        inventory_result = self.last_combat_result.get("inventory_result")
        if not isinstance(inventory_result, dict):
            return False

        pending = inventory_result.get("pending")
        if not isinstance(pending, list):
            return False
        if not isinstance(drop_index, int) or drop_index < 0 or drop_index >= len(pending):
            return False

        drop = pending[drop_index]
        kind = drop.get("kind")
        item_id = drop["item"]
        if kind == "stackable":
            added = add_stackable_item(
                self.player["inventory"],
                item_id,
                drop.get("quantity", 1),
            )
        elif kind == "unique":
            added = add_unique_item(self.player["inventory"], drop.copy())
        else:
            added = False

        if added:
            claimed_drop = pending.pop(drop_index)
            inventory_result.setdefault("added", []).append(claimed_drop)
            return True

        failed = inventory_result.setdefault("failed", [])
        if drop not in failed:
            failed.append(drop)
        return False

    def try_claim_all_combat_drops(self):
        if self.last_combat_result is None or self.player is None:
            return False

        inventory_result = self.last_combat_result.get("inventory_result")
        if not isinstance(inventory_result, dict):
            return False

        pending = inventory_result.get("pending")
        if not isinstance(pending, list):
            return True

        index = 0
        while index < len(pending):
            if self.try_claim_combat_drop(index):
                continue
            index += 1

        return len(pending) == 0

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
