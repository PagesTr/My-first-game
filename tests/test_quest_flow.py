import core.game as game_module
from core.game import Game
from systems.quests import get_quest_progress


def select_first_class(game, monkeypatch):
    monkeypatch.setattr(game, "save_current_game", lambda: True)
    class_id = next(iter(game.data.classes))
    game.select_class(class_id)


def test_new_player_has_quest_state(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)

    assert "quests" in game.player
    assert game.player["quests"]["active"] == ["forest_secure_outskirts"]


def test_instance_progresses_kill_quest_for_single_enemy_zone(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)

    monkeypatch.setattr(
        game_module,
        "run_instant_instance",
        lambda *args, **kwargs: {
            "combats_won": 5,
            "is_instance_result": True,
            "drops": [],
            "inventory_result": {"added": [], "failed": [], "pending": []},
        },
    )

    game.select_zone("forest_rat_outskirts")

    assert get_quest_progress(game.player, "forest_secure_outskirts", 0) >= 5


def test_gathering_progresses_gather_quest(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)
    game.player["quests"]["active"] = ["forest_first_harvest"]

    monkeypatch.setattr(
        game_module,
        "gather_from_zone",
        lambda *args, **kwargs: {
            "gathered": True,
            "rewards": [
                {"kind": "stackable", "item": "healing_herb", "quantity": 3}
            ],
        },
    )

    game.gather_in_zone("forest_rat_outskirts", "druid")

    assert get_quest_progress(game.player, "forest_first_harvest", 0) == 3


def test_record_craft_quest_progress_updates_craft_objective(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)
    game.player["quests"]["active"] = ["forest_pack_watches"]

    game.record_craft_quest_progress(
        "craft_wolf_fang_charm",
        {"crafted": True},
    )

    assert get_quest_progress(game.player, "forest_pack_watches", 1) == 1


def test_dungeon_completion_records_clear_dungeon_quest(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)
    game.player["level"] = 5
    game.player["quests"]["active"] = ["forest_clear_goblin_camp"]
    game.start_dungeon("forest_goblin_camp")
    dungeon = game.data.dungeons[game.active_dungeon["dungeon_id"]]
    boss_index = next(
        index
        for index, step in enumerate(dungeon["route"])
        if step.get("type") == "boss_loop"
    )
    game.active_dungeon["step_index"] = boss_index
    monkeypatch.setattr(
        game,
        "_run_single_dungeon_combat",
        lambda enemy_id, multiplier=1.0: {
            "won": False,
            "enemy_id": "goblin_quartermaster",
            "drops": [],
            "exp": 0,
            "gold": 0,
        },
    )

    game.resolve_dungeon_boss_step()

    assert get_quest_progress(game.player, "forest_clear_goblin_camp", 0) == 1
    assert "forest_clear_goblin_camp" in game.player["quests"]["completed"]
