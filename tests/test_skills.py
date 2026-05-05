from systems.combat import CombatSystem
from systems.skills import (
    WARRIOR_COMEBACK_STRIKE,
    apply_before_action_skills,
    ensure_equipped_skills,
    ensure_skill_cooldowns,
    ensure_skills,
    enhance_skill,
    equip_skill,
    get_player_skill_state,
    get_passive_skill_stat_modifiers,
    get_available_class_skills,
    get_skill_slot_count,
    get_skill_type,
    get_skill_values,
    is_skill_equipped,
    is_skill_known,
    learn_skill,
    learn_or_upgrade_skill,
    refund_skill_point,
    spend_skill_point,
    tick_skill_cooldowns,
    unequip_skill,
    upgrade_skill,
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


def make_player(
    player_class="warrior",
    current_hp=10,
    max_hp=20,
    level=1,
    enhanced=False,
    equipped_skills=None,
):
    skills = {}
    if level > 0:
        skills[WARRIOR_COMEBACK_STRIKE] = {
            "level": level,
            "enhanced": enhanced,
        }

    return {
        "class": player_class,
        "level": 1,
        "current_hp": current_hp,
        "max_hp": max_hp,
        "attack": 6,
        "defense": 1,
        "skills": skills,
        "equipped_skills": [] if equipped_skills is None else equipped_skills,
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


def test_ensure_equipped_skills_adds_container():
    player = {}

    equipped_skills = ensure_equipped_skills(player)

    assert equipped_skills == []
    assert player["equipped_skills"] is equipped_skills


def test_is_skill_equipped_returns_true_for_equipped_skill():
    player = make_player(equipped_skills=[WARRIOR_COMEBACK_STRIKE])

    assert is_skill_equipped(player, WARRIOR_COMEBACK_STRIKE) is True


def test_is_skill_equipped_returns_false_for_missing_skill():
    player = make_player(equipped_skills=[])

    assert is_skill_equipped(player, WARRIOR_COMEBACK_STRIKE) is False


def test_get_skill_slot_count_returns_one_slot_at_low_level():
    player = {"level": 4}

    assert get_skill_slot_count(player) == 1


def test_get_skill_slot_count_returns_two_slots_at_level_five():
    player = {"level": 5}

    assert get_skill_slot_count(player) == 2


def test_get_skill_slot_count_returns_three_slots_at_level_ten():
    player = {"level": 10}

    assert get_skill_slot_count(player) == 3


def test_get_available_class_skills_returns_only_player_class_skills():
    skills_data = {
        "warrior_skill": {
            "class": "warrior",
            "type": "active",
        },
        "mage_skill": {
            "class": "mage",
            "type": "active",
        },
    }
    player = {"class": "warrior"}

    available_skills = get_available_class_skills(skills_data, player)

    assert available_skills == [("warrior_skill", skills_data["warrior_skill"])]


def test_get_skill_type_defaults_to_active():
    skills_data = {
        "unknown_type_skill": {},
    }

    assert get_skill_type(skills_data, "unknown_type_skill") == "active"


def test_spend_skill_point_returns_true_when_available():
    player = {"skill_points": 1}

    spent = spend_skill_point(player)

    assert spent is True
    assert player["skill_points"] == 0


def test_spend_skill_point_returns_false_when_empty():
    player = {"skill_points": 0}

    spent = spend_skill_point(player)

    assert spent is False
    assert player["skill_points"] == 0


def test_refund_skill_point_adds_one_point():
    player = {"skill_points": 0}

    refunded = refund_skill_point(player)

    assert refunded is True
    assert player["skill_points"] == 1


def test_learn_or_upgrade_skill_learns_unknown_skill():
    player = make_player(level=0)

    progressed = learn_or_upgrade_skill(player, WARRIOR_COMEBACK_STRIKE)

    assert progressed is True
    assert player["skills"][WARRIOR_COMEBACK_STRIKE]["level"] == 1


def test_learn_or_upgrade_skill_upgrades_known_skill():
    player = make_player(level=1)

    progressed = learn_or_upgrade_skill(player, WARRIOR_COMEBACK_STRIKE)

    assert progressed is True
    assert player["skills"][WARRIOR_COMEBACK_STRIKE]["level"] == 2


def test_learn_or_upgrade_skill_returns_false_at_level_four():
    player = make_player(level=4)

    progressed = learn_or_upgrade_skill(player, WARRIOR_COMEBACK_STRIKE)

    assert progressed is False
    assert player["skills"][WARRIOR_COMEBACK_STRIKE]["level"] == 4


def test_learn_skill_adds_level_one_skill():
    player = make_player(level=0)

    learned = learn_skill(player, WARRIOR_COMEBACK_STRIKE)

    assert learned is True
    assert player["skills"][WARRIOR_COMEBACK_STRIKE] == {
        "level": 1,
        "enhanced": False,
    }


def test_learn_skill_returns_false_when_already_known():
    player = make_player(level=1)

    learned = learn_skill(player, WARRIOR_COMEBACK_STRIKE)

    assert learned is False


def test_upgrade_skill_increases_level_until_four():
    player = make_player(level=1)

    assert upgrade_skill(player, WARRIOR_COMEBACK_STRIKE) is True
    assert upgrade_skill(player, WARRIOR_COMEBACK_STRIKE) is True
    assert upgrade_skill(player, WARRIOR_COMEBACK_STRIKE) is True
    assert player["skills"][WARRIOR_COMEBACK_STRIKE]["level"] == 4


def test_upgrade_skill_returns_false_at_level_four():
    player = make_player(level=4)

    upgraded = upgrade_skill(player, WARRIOR_COMEBACK_STRIKE)

    assert upgraded is False


def test_enhance_skill_requires_level_four():
    player = make_player(level=3)

    enhanced = enhance_skill(player, WARRIOR_COMEBACK_STRIKE)

    assert enhanced is False
    assert is_skill_known(player, WARRIOR_COMEBACK_STRIKE) is True
    assert player["skills"][WARRIOR_COMEBACK_STRIKE]["enhanced"] is False


def test_enhance_skill_sets_enhanced_at_level_four():
    player = make_player(level=4)

    enhanced = enhance_skill(player, WARRIOR_COMEBACK_STRIKE)

    assert enhanced is True
    assert player["skills"][WARRIOR_COMEBACK_STRIKE]["enhanced"] is True


def test_equip_skill_requires_known_skill():
    player = make_player(level=0)

    equipped = equip_skill(player, WARRIOR_COMEBACK_STRIKE)

    assert equipped is False
    assert player["equipped_skills"] == []


def test_equip_skill_respects_slot_count():
    player = make_player(level=1)
    other_skill = "other_skill"
    learn_skill(player, other_skill)

    assert equip_skill(player, WARRIOR_COMEBACK_STRIKE) is True
    assert equip_skill(player, other_skill) is False
    assert player["equipped_skills"] == [WARRIOR_COMEBACK_STRIKE]


def test_unequip_skill_removes_equipped_skill():
    player = make_player(level=1)
    equip_skill(player, WARRIOR_COMEBACK_STRIKE)

    unequipped = unequip_skill(player, WARRIOR_COMEBACK_STRIKE)

    assert unequipped is True
    assert player["equipped_skills"] == []


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


def test_get_skill_values_allows_values_without_cooldown():
    skill_id = "active_without_cooldown"
    player = {
        "skills": {
            skill_id: {
                "level": 1,
                "enhanced": False,
            },
        },
    }
    skills_data = {
        skill_id: {
            "levels": {
                "1": {
                    "damage_multiplier": 1.2,
                },
            },
        },
    }

    values = get_skill_values(skills_data, player, skill_id)

    assert values == {"damage_multiplier": 1.2}


def test_get_skill_values_allows_passive_stat_modifiers():
    skill_id = "passive_attack_bonus"
    player = {
        "skills": {
            skill_id: {
                "level": 1,
                "enhanced": False,
            },
        },
    }
    skills_data = {
        skill_id: {
            "type": "passive",
            "levels": {
                "1": {
                    "stat_modifiers": {
                        "attack": 2,
                    },
                },
            },
        },
    }

    values = get_skill_values(skills_data, player, skill_id)

    assert values == {"stat_modifiers": {"attack": 2}}


def test_passive_skill_stat_modifiers_apply_flat_bonus():
    skill_id = "passive_attack_bonus"
    player = {
        "level": 1,
        "skills": {
            skill_id: {
                "level": 1,
                "enhanced": False,
            },
        },
    }
    skills_data = {
        skill_id: {
            "type": "passive",
            "levels": {
                "1": {
                    "stat_modifiers": {
                        "attack": 2,
                    },
                },
            },
        },
    }

    modifiers = get_passive_skill_stat_modifiers(skills_data, player)

    assert modifiers == {"attack": 2}


def test_passive_skill_stat_modifiers_apply_per_character_level_bonus():
    skill_id = "passive_vitality_bonus"
    player = {
        "level": 5,
        "skills": {
            skill_id: {
                "level": 1,
                "enhanced": False,
            },
        },
    }
    skills_data = {
        skill_id: {
            "type": "passive",
            "levels": {
                "1": {
                    "stat_modifiers_per_character_level": {
                        "max_hp": 2,
                    },
                },
            },
        },
    }

    modifiers = get_passive_skill_stat_modifiers(skills_data, player)

    assert modifiers == {"max_hp": 10}


def test_passive_skill_stat_modifiers_ignore_active_skills():
    skill_id = "active_attack_bonus"
    player = {
        "level": 1,
        "skills": {
            skill_id: {
                "level": 1,
                "enhanced": False,
            },
        },
    }
    skills_data = {
        skill_id: {
            "type": "active",
            "levels": {
                "1": {
                    "stat_modifiers": {
                        "attack": 2,
                    },
                },
            },
        },
    }

    modifiers = get_passive_skill_stat_modifiers(skills_data, player)

    assert modifiers == {}


def test_get_skill_values_returns_none_when_level_values_are_missing():
    skill_id = "missing_level_values"
    player = {
        "skills": {
            skill_id: {
                "level": 1,
                "enhanced": False,
            },
        },
    }
    skills_data = {
        skill_id: {
            "levels": {},
        },
    }

    values = get_skill_values(skills_data, player, skill_id)

    assert values is None


def test_get_skill_values_returns_enhanced_values_only_at_level_4():
    player = make_player(level=4, enhanced=True)

    values = get_skill_values(make_skills_data(), player, WARRIOR_COMEBACK_STRIKE)

    assert values == {
        "damage_multiplier": 1.85,
        "cooldown": 2,
    }


def test_warrior_comeback_strike_triggers_after_damage_taken():
    player = make_player(level=0)
    learn_skill(player, WARRIOR_COMEBACK_STRIKE)
    equip_skill(player, WARRIOR_COMEBACK_STRIKE)
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


def test_warrior_comeback_strike_does_not_trigger_when_not_equipped():
    player = make_player(level=1, equipped_skills=[])
    enemy = make_enemy()
    combat = CombatSystem(player, enemy, make_skills_data())
    combat.player_took_damage_since_last_action = True

    apply_before_action_skills(combat, player, enemy, "attack", True)

    assert combat.pending_damage_multiplier == 1.0


def test_warrior_comeback_strike_respects_cooldown():
    player = make_player(level=1)
    equip_skill(player, WARRIOR_COMEBACK_STRIKE)
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
    equip_skill(player, WARRIOR_COMEBACK_STRIKE)
    enemy = make_enemy()
    combat = CombatSystem(player, enemy, make_skills_data())
    combat.player_took_damage_since_last_action = True

    apply_before_action_skills(combat, player, enemy, "attack", True)

    assert combat.pending_damage_multiplier == 1.85
    assert player["skill_cooldowns"][WARRIOR_COMEBACK_STRIKE] == 2
