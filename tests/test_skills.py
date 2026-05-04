from systems.combat import CombatSystem
from systems.skills import (
    WARRIOR_COMEBACK_STRIKE,
    apply_before_action_skills,
    ensure_skill_cooldowns,
    ensure_skills,
    get_player_skill_state,
    get_skill_values,
    tick_skill_cooldowns,
)


def make_skills_data():
    return {
        WARRIOR_COMEBACK_STRIKE: {
            "levels": {
                "1": {
                    "damage_multiplier": 1.25,
                    "cooldown": 4,
                },
                "4": {
                    "damage_multiplier": 1.60,
                    "cooldown": 3,
                },
            },
            "enhanced": {
                "damage_multiplier": 1.85,
                "cooldown": 2,
            },
        },
    }


def make_player(player_class="warrior", current_hp=10, max_hp=20, level=1, enhanced=False):
    return {
        "class": player_class,
        "current_hp": current_hp,
        "max_hp": max_hp,
        "attack": 6,
        "defense": 1,
        "skills": {
            WARRIOR_COMEBACK_STRIKE: {
                "level": level,
                "enhanced": enhanced,
            },
        },
        "skill_cooldowns": {},
    }


def make_enemy():
    return {
        "behavior": "aggressive",
        "current_hp": 20,
        "max_hp": 20,
        "attack": 4,
        "defense": 1,
    }


def test_ensure_skills_adds_container():
    player = {}

    skills = ensure_skills(player)

    assert skills == {}
    assert player["skills"] is skills


def test_ensure_skill_cooldowns_adds_container():
    player = {}

    cooldowns = ensure_skill_cooldowns(player)

    assert cooldowns == {}
    assert player["skill_cooldowns"] is cooldowns


def test_get_player_skill_state_returns_default_when_missing():
    player = {}

    skill_state = get_player_skill_state(player, WARRIOR_COMEBACK_STRIKE)

    assert skill_state == {"level": 0, "enhanced": False}


def test_get_player_skill_state_rejects_enhanced_before_level_4():
    player = make_player(level=3, enhanced=True)

    skill_state = get_player_skill_state(player, WARRIOR_COMEBACK_STRIKE)

    assert skill_state == {"level": 3, "enhanced": False}


def test_get_skill_values_returns_none_when_skill_is_missing():
    player = make_player()

    values = get_skill_values({}, player, WARRIOR_COMEBACK_STRIKE)

    assert values is None


def test_get_skill_values_returns_level_values():
    player = make_player(level=1)

    values = get_skill_values(make_skills_data(), player, WARRIOR_COMEBACK_STRIKE)

    assert values == {
        "damage_multiplier": 1.25,
        "cooldown": 4,
    }


def test_get_skill_values_returns_enhanced_values_only_at_level_4():
    player = make_player(level=4, enhanced=True)

    values = get_skill_values(make_skills_data(), player, WARRIOR_COMEBACK_STRIKE)

    assert values == {
        "damage_multiplier": 1.85,
        "cooldown": 2,
    }


def test_warrior_comeback_strike_triggers_after_damage_taken():
    player = make_player(level=1)
    enemy = make_enemy()
    combat = CombatSystem(player, enemy, make_skills_data())
    combat.player_took_damage_since_last_action = True

    apply_before_action_skills(combat, player, enemy, "attack", True)

    assert combat.pending_damage_multiplier == 1.25
    assert player["skill_cooldowns"][WARRIOR_COMEBACK_STRIKE] == 4


def test_warrior_comeback_strike_does_not_trigger_without_damage_taken():
    player = make_player(level=1)
    enemy = make_enemy()
    combat = CombatSystem(player, enemy, make_skills_data())

    apply_before_action_skills(combat, player, enemy, "attack", True)

    assert combat.pending_damage_multiplier == 1.0


def test_warrior_comeback_strike_respects_cooldown():
    player = make_player(level=1)
    player["skill_cooldowns"] = {WARRIOR_COMEBACK_STRIKE: 2}
    enemy = make_enemy()
    combat = CombatSystem(player, enemy, make_skills_data())
    combat.player_took_damage_since_last_action = True

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


def test_enhanced_skill_uses_enhanced_values_at_level_4():
    player = make_player(level=4, enhanced=True)
    enemy = make_enemy()
    combat = CombatSystem(player, enemy, make_skills_data())
    combat.player_took_damage_since_last_action = True

    apply_before_action_skills(combat, player, enemy, "attack", True)

    assert combat.pending_damage_multiplier == 1.85
    assert player["skill_cooldowns"][WARRIOR_COMEBACK_STRIKE] == 2
