from systems.combat import CombatSystem
from systems.skills import (
    WARRIOR_COMEBACK_STRIKE,
    apply_before_action_skills,
    ensure_skill_cooldowns,
    tick_skill_cooldowns,
)


def make_player(player_class="warrior", current_hp=10, max_hp=20):
    return {
        "class": player_class,
        "current_hp": current_hp,
        "max_hp": max_hp,
        "attack": 6,
        "defense": 1,
    }


def make_enemy():
    return {
        "behavior": "aggressive",
        "current_hp": 20,
        "max_hp": 20,
        "attack": 4,
        "defense": 1,
    }


def test_ensure_skill_cooldowns_adds_container():
    player = {}

    cooldowns = ensure_skill_cooldowns(player)

    assert cooldowns == {}
    assert player["skill_cooldowns"] is cooldowns


def test_warrior_comeback_strike_triggers_when_damaged():
    player = make_player(current_hp=10, max_hp=20)
    enemy = make_enemy()
    combat = CombatSystem(player, enemy)

    apply_before_action_skills(combat, player, enemy, "attack", True)

    assert combat.pending_damage_multiplier == 1.5
    assert player["skill_cooldowns"][WARRIOR_COMEBACK_STRIKE] == 3


def test_warrior_comeback_strike_does_not_trigger_when_full_hp():
    player = make_player(current_hp=20, max_hp=20)
    enemy = make_enemy()
    combat = CombatSystem(player, enemy)

    apply_before_action_skills(combat, player, enemy, "attack", True)

    assert combat.pending_damage_multiplier == 1.0


def test_warrior_comeback_strike_respects_cooldown():
    player = make_player(current_hp=10, max_hp=20)
    player["skill_cooldowns"] = {WARRIOR_COMEBACK_STRIKE: 2}
    enemy = make_enemy()
    combat = CombatSystem(player, enemy)

    apply_before_action_skills(combat, player, enemy, "attack", True)

    assert combat.pending_damage_multiplier == 1.0


def test_tick_skill_cooldowns_decreases_active_cooldown():
    player = {
        "skill_cooldowns": {
            WARRIOR_COMEBACK_STRIKE: 3,
        },
    }

    tick_skill_cooldowns(player)

    assert player["skill_cooldowns"][WARRIOR_COMEBACK_STRIKE] == 2
