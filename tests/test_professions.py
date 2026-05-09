from systems.professions import (
    add_profession_xp,
    create_player_professions,
    ensure_player_professions,
    get_profession_level,
    get_profession_mastery,
)


PROFESSIONS_DATA = {
    "prospector": {
        "primary_stat": "strength",
        "mastery_bonus_stat": "prospector_mastery",
        "xp_bonus_stat": "prospector_xp_bonus",
    },
    "druid": {
        "primary_stat": "intelligence",
        "mastery_bonus_stat": "druid_mastery",
        "xp_bonus_stat": "druid_xp_bonus",
    },
}


def test_create_player_professions_initializes_all_professions():
    professions = create_player_professions(PROFESSIONS_DATA)

    assert professions == {
        "prospector": {"level": 1, "xp": 0, "next_xp": 20},
        "druid": {"level": 1, "xp": 0, "next_xp": 20},
    }


def test_ensure_player_professions_adds_missing_profession_without_resetting_existing():
    player = {
        "professions": {
            "prospector": {"level": 3, "xp": 7, "next_xp": 45},
        }
    }

    professions = ensure_player_professions(player, PROFESSIONS_DATA)

    assert professions["prospector"] == {"level": 3, "xp": 7, "next_xp": 45}
    assert professions["druid"] == {"level": 1, "xp": 0, "next_xp": 20}


def test_get_profession_level_returns_zero_for_missing_profession():
    player = {"professions": {}}

    assert get_profession_level(player, "prospector") == 0


def test_add_profession_xp_adds_xp_without_level_up():
    player = {
        "professions": {
            "prospector": {"level": 1, "xp": 0, "next_xp": 20},
        }
    }

    result = add_profession_xp(player, "prospector", 5)

    assert result == {
        "leveled_up": False,
        "level": 1,
        "xp": 5,
        "next_xp": 20,
    }


def test_add_profession_xp_levels_up_when_threshold_is_reached():
    player = {
        "professions": {
            "prospector": {"level": 1, "xp": 0, "next_xp": 20},
        }
    }

    result = add_profession_xp(player, "prospector", 20)

    assert result == {
        "leveled_up": True,
        "level": 2,
        "xp": 0,
        "next_xp": 30,
    }


def test_get_profession_mastery_uses_level_primary_stat_and_bonus():
    player = {
        "strength": 8,
        "prospector_mastery": 3,
        "gathering_mastery": 2,
        "professions": {
            "prospector": {"level": 4, "xp": 0, "next_xp": 20},
        },
    }

    mastery = get_profession_mastery(player, "prospector", PROFESSIONS_DATA)

    assert mastery == 13


def test_get_profession_mastery_returns_zero_for_unknown_profession():
    player = {
        "strength": 8,
        "professions": {
            "prospector": {"level": 4, "xp": 0, "next_xp": 20},
        },
    }

    assert get_profession_mastery(player, "unknown", PROFESSIONS_DATA) == 0
