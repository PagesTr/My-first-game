import systems.gathering as gathering
from core.game import Game
from systems.active_gathering import (
    DEFAULT_ACTIVE_GATHERING_TICK_SECONDS,
    advance_active_gathering_tick,
    create_active_gathering_activity,
    format_tick_rate,
    get_active_gathering_remaining_ms,
    get_node_tick_seconds,
    is_active_gathering_tick_ready,
    resolve_active_gathering_tick,
)
from systems.inventory import create_inventory


PROFESSIONS_DATA = {
    "druid": {
        "primary_stat": "intelligence",
        "mastery_bonus_stat": "druid_mastery",
        "xp_bonus_stat": "druid_xp_bonus",
    }
}

GATHERING_NODES = {
    "forest_rat_outskirts": {
        "druid": {
            "name": "Forest Herbs",
            "tick_seconds": 3,
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


def make_player():
    return {
        "intelligence": 0,
        "inventory": create_inventory(),
        "professions": {
            "druid": {"level": 1, "xp": 0, "next_xp": 20},
        },
    }


def select_first_class(game, monkeypatch):
    monkeypatch.setattr(game, "save_current_game", lambda: True)
    game.select_class(next(iter(game.data.classes)))


def test_create_active_gathering_activity_contains_expected_fields():
    activity = create_active_gathering_activity(
        "forest_rat_outskirts",
        "druid",
        current_time_ms=1000,
        tick_seconds=3,
    )

    assert activity == {
        "type": "gathering",
        "zone_id": "forest_rat_outskirts",
        "profession_id": "druid",
        "started_at_ms": 1000,
        "last_tick_at_ms": 1000,
        "tick_seconds": 3.0,
    }


def test_get_node_tick_seconds_returns_data_value():
    assert get_node_tick_seconds({"tick_seconds": 4}) == 4.0


def test_get_node_tick_seconds_uses_default_for_invalid_value():
    assert get_node_tick_seconds({"tick_seconds": -1}) == DEFAULT_ACTIVE_GATHERING_TICK_SECONDS
    assert get_node_tick_seconds({"tick_seconds": "bad"}) == DEFAULT_ACTIVE_GATHERING_TICK_SECONDS
    assert get_node_tick_seconds({"tick_seconds": None}) == DEFAULT_ACTIVE_GATHERING_TICK_SECONDS


def test_is_active_gathering_tick_ready_returns_false_before_tick():
    activity = create_active_gathering_activity("forest_rat_outskirts", "druid", 1000, 3)

    assert is_active_gathering_tick_ready(activity, 3999) is False


def test_is_active_gathering_tick_ready_returns_true_at_tick():
    activity = create_active_gathering_activity("forest_rat_outskirts", "druid", 1000, 3)

    assert is_active_gathering_tick_ready(activity, 4000) is True


def test_get_active_gathering_remaining_ms_returns_remaining_time():
    activity = create_active_gathering_activity("forest_rat_outskirts", "druid", 1000, 3)

    assert get_active_gathering_remaining_ms(activity, 2500) == 1500


def test_advance_active_gathering_tick_updates_last_tick_time():
    activity = create_active_gathering_activity("forest_rat_outskirts", "druid", 1000, 3)

    assert advance_active_gathering_tick(activity, 4000)["last_tick_at_ms"] == 4000


def test_format_tick_rate_displays_seconds_per_tick():
    assert format_tick_rate(3) == "1 tick / 3s"
    assert format_tick_rate(3.5) == "1 tick / 3.5s"


def test_format_tick_rate_displays_ticks_per_second_below_one_second():
    assert format_tick_rate(0.5) == "2 ticks/s"
    assert format_tick_rate(0.025) == "40 ticks/s"


def test_resolve_active_gathering_tick_uses_gather_from_zone(monkeypatch):
    player = make_player()
    activity = create_active_gathering_activity("forest_rat_outskirts", "druid", 1000, 3)
    monkeypatch.setattr(gathering.random, "random", lambda: 1.0)
    monkeypatch.setattr(gathering.random, "randint", lambda minimum, maximum: minimum)

    result = resolve_active_gathering_tick(
        player,
        activity,
        GATHERING_NODES,
        PROFESSIONS_DATA,
        {},
    )

    assert result["gathered"] is True
    assert result["rewards"] == [
        {"kind": "stackable", "item": "healing_herb", "quantity": 1}
    ]


def test_game_start_active_gathering_rejects_unknown_node(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)

    result = game.start_active_gathering("forest_rat_outskirts", "prospector", 1000)

    assert result == {"started": False, "reason": "unknown_node"}


def test_game_start_active_gathering_stores_activity(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)

    result = game.start_active_gathering("forest_rat_outskirts", "druid", 1000)

    assert result["started"] is True
    assert game.active_gathering is not None


def test_game_update_active_gathering_resolves_tick(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)
    game.start_active_gathering("forest_rat_outskirts", "druid", 1000)
    monkeypatch.setattr(gathering.random, "random", lambda: 1.0)
    monkeypatch.setattr(gathering.random, "randint", lambda minimum, maximum: minimum)

    result = game.update_active_gathering(5000)

    assert result is not None
    assert result == game.last_gathering_result
    assert game.active_gathering is not None


def test_game_update_active_gathering_stops_on_inventory_full(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)
    game.start_active_gathering("forest_rat_outskirts", "druid", 1000)

    def fake_resolve(*args, **kwargs):
        return {"gathered": False, "reason": "inventory_full"}

    monkeypatch.setattr("core.game.resolve_active_gathering_tick", fake_resolve)

    result = game.update_active_gathering(5000)

    assert result == {"gathered": False, "reason": "inventory_full"}
    assert game.active_gathering is None
