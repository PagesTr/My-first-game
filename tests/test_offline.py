import systems.gathering as gathering
from core.game import Game
from systems.inventory import create_inventory
from systems.offline import (
    calculate_offline_ticks,
    create_offline_gathering_activity,
    get_offline_elapsed_seconds,
    resolve_offline_activity,
    start_offline_gathering,
    stop_offline_activity,
)


PROFESSIONS_DATA = {
    "druid": {
        "primary_stat": "intelligence",
        "mastery_bonus_stat": "druid_mastery",
        "xp_bonus_stat": "druid_xp_bonus",
    }
}

GATHERING_NODES = {
    "forest_goblin": {
        "druid": {
            "name": "Forest Herbs",
            "xp": 4,
            "rewards": [
                {
                    "item": "healing_herb",
                    "chance": 1.0,
                    "min_quantity": 1,
                    "max_quantity": 1,
                }
            ],
        }
    }
}


def make_player(activity=None, inventory_size=10):
    return {
        "intelligence": 0,
        "inventory": create_inventory(size=inventory_size),
        "professions": {
            "druid": {"level": 1, "xp": 0, "next_xp": 20},
        },
        "offline_activity": activity,
    }


def test_create_offline_gathering_activity_contains_expected_fields():
    activity = create_offline_gathering_activity(
        "forest_goblin",
        "druid",
        current_time=1000,
    )

    assert activity == {
        "type": "gathering",
        "zone_id": "forest_goblin",
        "profession_id": "druid",
        "started_at": 1000,
        "last_claimed_at": 1000,
    }


def test_start_offline_gathering_sets_player_activity():
    player = {"offline_activity": None}

    result = start_offline_gathering(
        player,
        "forest_goblin",
        "druid",
        current_time=1000,
    )

    assert result["started"] is True
    assert isinstance(player["offline_activity"], dict)


def test_start_offline_gathering_rejects_existing_activity():
    player = {
        "offline_activity": create_offline_gathering_activity(
            "forest_goblin",
            "druid",
            current_time=1000,
        )
    }

    result = start_offline_gathering(player, "forest_goblin", "druid")

    assert result == {"started": False, "reason": "activity_already_active"}


def test_stop_offline_activity_clears_activity():
    player = {
        "offline_activity": create_offline_gathering_activity(
            "forest_goblin",
            "druid",
            current_time=1000,
        )
    }

    stopped = stop_offline_activity(player)

    assert stopped is True
    assert player["offline_activity"] is None


def test_calculate_offline_ticks_caps_ticks():
    result = calculate_offline_ticks(600 * 20, max_ticks=12)

    assert result["ticks"] == 12
    assert result["capped"] is True


def test_calculate_offline_ticks_returns_zero_when_not_enough_time():
    result = calculate_offline_ticks(599)

    assert result["ticks"] == 0


def test_get_offline_elapsed_seconds_uses_last_claimed_at():
    player = {
        "offline_activity": create_offline_gathering_activity(
            "forest_goblin",
            "druid",
            current_time=1000,
        )
    }

    assert get_offline_elapsed_seconds(player, current_time=1600) == 600


def test_resolve_offline_activity_returns_no_activity():
    player = {"offline_activity": None}

    result = resolve_offline_activity(player, {}, {}, {})

    assert result == {"resolved": False, "reason": "no_activity"}


def test_resolve_offline_activity_returns_not_enough_time():
    activity = create_offline_gathering_activity(
        "forest_goblin",
        "druid",
        current_time=1000,
    )
    player = make_player(activity)

    result = resolve_offline_activity(
        player,
        GATHERING_NODES,
        PROFESSIONS_DATA,
        {},
        current_time=1500,
    )

    assert result == {
        "resolved": False,
        "reason": "not_enough_time",
        "elapsed_seconds": 500,
        "ticks": 0,
    }


def test_resolve_offline_activity_runs_gathering_ticks(monkeypatch):
    activity = create_offline_gathering_activity(
        "forest_goblin",
        "druid",
        current_time=1000,
    )
    player = make_player(activity)
    monkeypatch.setattr(gathering.random, "random", lambda: 1.0)
    monkeypatch.setattr(gathering.random, "randint", lambda minimum, maximum: minimum)

    result = resolve_offline_activity(
        player,
        GATHERING_NODES,
        PROFESSIONS_DATA,
        {},
        current_time=2200,
    )

    assert result["resolved"] is True
    assert result["ticks"] == 2
    assert result["rewards"] == [
        {"kind": "stackable", "item": "healing_herb", "quantity": 2}
    ]
    assert result["profession_xp"] == 8
    assert player["inventory"]["slots"][0] == {
        "kind": "stackable",
        "item": "healing_herb",
        "quantity": 2,
    }
    assert player["offline_activity"]["last_claimed_at"] == 2200


def test_resolve_offline_activity_keeps_activity_active_after_resolution(monkeypatch):
    activity = create_offline_gathering_activity(
        "forest_goblin",
        "druid",
        current_time=1000,
    )
    player = make_player(activity)
    monkeypatch.setattr(gathering.random, "random", lambda: 1.0)
    monkeypatch.setattr(gathering.random, "randint", lambda minimum, maximum: minimum)

    resolve_offline_activity(
        player,
        GATHERING_NODES,
        PROFESSIONS_DATA,
        {},
        current_time=1600,
    )

    assert player["offline_activity"] is not None


def test_resolve_offline_activity_returns_inventory_full_when_no_rewards_can_be_added(monkeypatch):
    activity = create_offline_gathering_activity(
        "forest_goblin",
        "druid",
        current_time=1000,
    )
    player = make_player(activity, inventory_size=1)
    player["inventory"]["slots"][0] = {
        "kind": "stackable",
        "item": "iron_ore",
        "quantity": 1,
    }
    monkeypatch.setattr(gathering.random, "random", lambda: 1.0)
    monkeypatch.setattr(gathering.random, "randint", lambda minimum, maximum: minimum)

    result = resolve_offline_activity(
        player,
        GATHERING_NODES,
        PROFESSIONS_DATA,
        {},
        current_time=1600,
    )

    assert result["resolved"] is False
    assert result["reason"] == "inventory_full"
    assert player["offline_activity"]["last_claimed_at"] == 1600


def select_first_class(game, monkeypatch):
    monkeypatch.setattr(game, "save_current_game", lambda: True)
    class_id = next(iter(game.data.classes))
    game.select_class(class_id)


def test_game_start_offline_gathering_activity_rejects_unknown_node(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)

    result = game.start_offline_gathering_activity("forest_goblin", "prospector")

    assert result == {"started": False, "reason": "unknown_node"}


def test_game_start_offline_gathering_activity_stores_activity(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)

    result = game.start_offline_gathering_activity("forest_goblin", "druid")

    assert result["started"] is True
    assert isinstance(game.player["offline_activity"], dict)
