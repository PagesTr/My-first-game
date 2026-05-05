import random

from systems.skills import apply_before_action_skills, tick_skill_cooldowns


class CombatSystem:
    def __init__(self, player, enemy, skills_data=None):
        self.player = player
        self.enemy = enemy
        self.skills_data = skills_data or {}

        self.turn_count = 0
        self.is_over = False
        self.winner = None

        self.log = []  # Useful for the UI later
        self.history = []
        self.pending_damage_multiplier = 1.0
        self.player_took_damage_since_last_action = False

    # ======================
    # PUBLIC API
    # ======================

    def step(self, player_action=None):
        """
        Execute a full combat turn:
        - player action
        - enemy action
        """

        if self.is_over:
            return

        if player_action is None:
            player_action = self._player_auto_action()

        self.turn_count += 1
        self.log.clear()
        self._on_turn_start()

        # --- Player turn ---
        self._on_before_action(self.player, self.enemy, player_action, True)
        self._apply_action(self.player, self.enemy, player_action, is_player=True)
        self._on_after_action(self.player, self.enemy, player_action, True)

        if self._check_end():
            self._on_turn_end()
            return

        # --- Enemy turn (simple AI for now) ---
        enemy_action = self._enemy_ai()

        self._on_before_action(self.enemy, self.player, enemy_action, False)
        self._apply_action(self.enemy, self.player, enemy_action, is_player=False)
        self._on_after_action(self.enemy, self.player, enemy_action, False)

        self._check_end()
        self._on_turn_end()

    # ======================
    # ACTIONS
    # ======================

    def _add_log(self, message):
        self.log.append(message)
        self.history.append(f"Turn {self.turn_count}: {message}")

    def _apply_action(self, attacker, defender, action, is_player):
        actor_name = "Player" if is_player else "Enemy"

        if action == "attack":
            dmg = self._compute_damage(attacker, defender)
            if dmg > 0:
                defender["current_hp"] = max(0, defender["current_hp"] - dmg)
                if is_player is False and defender is self.player:
                    self.player_took_damage_since_last_action = True
                self._add_log(f"{actor_name} attacks -> {dmg} damage")

        elif action == "heal":
            heal = int(attacker.get("healing_power", 10))
            attacker["current_hp"] = min(
                attacker["max_hp"], attacker["current_hp"] + heal
            )

            self._add_log(f"{actor_name} heals -> +{heal} HP")

        # Extensible here (skills, items, etc.)

    def _player_auto_action(self):
        if self.player["current_hp"] <= self.player["max_hp"] * 0.30:
            return "heal"
        return "attack"

    def _on_turn_start(self):
        return

    def _on_before_action(self, actor, target, action, is_player):
        log_start = len(self.log)
        apply_before_action_skills(self, actor, target, action, is_player)
        for message in self.log[log_start:]:
            self.history.append(f"Turn {self.turn_count}: {message}")
        return

    def _on_after_action(self, actor, target, action, is_player):
        if is_player is True:
            self.player_took_damage_since_last_action = False
        return

    def _on_turn_end(self):
        tick_skill_cooldowns(self.player)
        return

    # ======================
    # ENEMY AI (simple)
    # ======================

    def _enemy_ai(self):
        behavior = self.enemy.get("behavior", "balanced")

        if behavior == "aggressive":
            return "attack"

        heal_threshold = 0.30 if behavior == "defensive" else 0.25
        if self.enemy["current_hp"] <= self.enemy["max_hp"] * heal_threshold:
            return "heal"
        return "attack"

    # ======================
    # CALCULATIONS
    # ======================

    def _compute_damage(self, attacker, defender):
        accuracy = attacker.get("accuracy", 1.0)
        dodge_chance = defender.get("dodge_chance", 0.0)
        hit_chance = accuracy - dodge_chance
        hit_chance = max(0.05, min(0.95, hit_chance))

        if random.random() > hit_chance:
            self._add_log("Attack dodged!")
            self.pending_damage_multiplier = 1.0
            return 0

        base = attacker["attack"] - defender["defense"]
        base = max(1, base)

        block_chance = defender.get("block_chance", 0.0)
        if random.random() < block_chance:
            base = max(1, int(base / 2))
            self._add_log("Attack blocked!")

        crit_chance = attacker.get("crit_chance", 0.1)
        crit_damage = attacker.get("crit_damage", 2.0)
        if random.random() < crit_chance:
            base = max(1, int(base * crit_damage))
            self._add_log("Critical hit!")

        base = max(1, int(base * self.pending_damage_multiplier))
        self.pending_damage_multiplier = 1.0

        return base

    # ======================
    # END OF COMBAT
    # ======================

    def _check_end(self):
        if self.player["current_hp"] <= 0:
            self.is_over = True
            self.winner = "enemy"
            self._add_log("Defeat")
            return True

        if self.enemy["current_hp"] <= 0:
            self.is_over = True
            self.winner = "player"
            self._add_log("Victory")
            return True

        return False

    # ======================
    # UTILS
    # ======================

    def get_state(self):
        return {
            "player_hp": self.player["current_hp"],
            "enemy_hp": self.enemy["current_hp"],
            "turn": self.turn_count,
            "log": self.log,
            "is_over": self.is_over,
            "winner": self.winner,
        }

    def get_combat_report(self):
        return {
            "enemy_name": self.enemy.get("name", "Unknown Enemy"),
            "turns": self.turn_count,
            "winner": self.winner,
            "history": list(self.history),
        }
