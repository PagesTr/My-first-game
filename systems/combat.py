import random


class CombatSystem:
    def __init__(self, player, enemy):
        self.player = player
        self.enemy = enemy

        self.turn_count = 0
        self.is_over = False
        self.winner = None

        self.log = []  # utile pour UI plus tard

    # ======================
    # PUBLIC API
    # ======================

    def step(self, player_action):
        """
        Execute un tour complet :
        - action joueur
        - action ennemi
        """

        if self.is_over:
            return

        self.turn_count += 1
        self.log.clear()

        # --- joueur joue ---
        self._apply_action(self.player, self.enemy, player_action, is_player=True)

        if self._check_end():
            return

        # --- ennemi joue (IA simple pour l'instant) ---
        enemy_action = self._enemy_ai()

        self._apply_action(self.enemy, self.player, enemy_action, is_player=False)

        self._check_end()

    # ======================
    # ACTIONS
    # ======================

    def _apply_action(self, attacker, defender, action, is_player):
        actor_name = "Player" if is_player else "Enemy"

        if action == "attack":
            dmg = self._compute_damage(attacker, defender)
            if dmg > 0:
                defender["current_hp"] = max(0, defender["current_hp"] - dmg)

            self.log.append(f"{actor_name} attaque -> {dmg} degats")

        elif action == "heal":
            heal = int(attacker.get("healing_power", 10))
            attacker["current_hp"] = min(
                attacker["max_hp"], attacker["current_hp"] + heal
            )

            self.log.append(f"{actor_name} se soigne -> +{heal} HP")

        # Extensible ici (skills, items, etc.)

    # ======================
    # IA ENNEMI (simple)
    # ======================

    def _enemy_ai(self):
        # Tres basique pour l'instant
        if self.enemy["current_hp"] < 5:
            return "heal"
        return "attack"

    # ======================
    # CALCULS
    # ======================

    def _compute_damage(self, attacker, defender):
        accuracy = attacker.get("accuracy", 1.0)
        dodge_chance = defender.get("dodge_chance", 0.0)
        hit_chance = accuracy - dodge_chance
        hit_chance = max(0.05, min(0.95, hit_chance))

        if random.random() > hit_chance:
            self.log.append("Attaque esquivee !")
            return 0

        base = attacker["attack"] - defender["defense"]
        base = max(1, base)

        block_chance = defender.get("block_chance", 0.0)
        if random.random() < block_chance:
            base = max(1, int(base / 2))
            self.log.append("Attaque bloquee !")

        crit_chance = attacker.get("crit_chance", 0.1)
        crit_damage = attacker.get("crit_damage", 2.0)
        if random.random() < crit_chance:
            base = max(1, int(base * crit_damage))
            self.log.append("Coup critique !")

        return base

    # ======================
    # FIN DE COMBAT
    # ======================

    def _check_end(self):
        if self.player["current_hp"] <= 0:
            self.is_over = True
            self.winner = "enemy"
            self.log.append("Defaite")
            return True

        if self.enemy["current_hp"] <= 0:
            self.is_over = True
            self.winner = "player"
            self.log.append("Victoire")
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
