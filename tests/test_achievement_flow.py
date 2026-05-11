from core.game import Game
from systems.achievements import get_achievement_progress, is_achievement_unlocked


def create_game(monkeypatch):
    game = Game()
    monkeypatch.setattr(game, "save_current_game", lambda: True)
    class_id = next(iter(game.data.classes))
    game.select_class(class_id)
    return game


def move_active_dungeon_to_boss_loop(game):
    dungeon_id = game.active_dungeon["dungeon_id"]
    dungeon = game.data.dungeons[dungeon_id]
    game.active_dungeon["step_index"] = len(dungeon["route"]) - 1


def test_new_player_has_achievements_state(monkeypatch):
    game = create_game(monkeypatch)

    achievements = game.player.get("achievements")

    assert isinstance(achievements, dict)
    assert isinstance(achievements.get("unlocked"), list)
    assert isinstance(achievements.get("progress"), dict)
    assert isinstance(achievements.get("last_unlocked"), list)


def test_kill_enemy_event_unlocks_achievement(monkeypatch):
    game = create_game(monkeypatch)

    game.record_achievement_event({
        "type": "kill_enemy",
        "target": "forest_rat",
        "amount": 25,
        "metadata": {"chapter": "forest", "family": "beast"},
    })

    assert is_achievement_unlocked(game.player, "forest_rat_cleaner_1")


def test_record_progress_event_updates_quests_and_achievements(monkeypatch):
    game = create_game(monkeypatch)

    result = game.record_progress_event({
        "type": "kill_enemy",
        "target": "forest_rat",
        "amount": 25,
        "metadata": {"chapter": "forest", "family": "beast"},
    })

    assert "quests" in result
    assert "achievements" in result
    assert is_achievement_unlocked(game.player, "forest_rat_cleaner_1")


def test_select_zone_records_single_expedition_kills(monkeypatch):
    game = create_game(monkeypatch)

    monkeypatch.setattr(
        "core.game.run_instant_instance",
        lambda *args, **kwargs: {"combats_won": 10},
    )

    game.select_zone("forest_rat_outskirts")

    assert is_achievement_unlocked(game.player, "forest_rat_outskirts_push_1")


def test_gathering_records_gather_profession_achievement(monkeypatch):
    game = create_game(monkeypatch)

    for _ in range(25):
        game._record_gathering_progress(
            {"gathered": True, "rewards": [{"item": "healing_herb", "quantity": 1}]},
            profession_id="druid",
            zone_key="forest_rat_outskirts",
        )

    assert get_achievement_progress(game.player, "forest_first_harvest") == 25
    assert is_achievement_unlocked(game.player, "forest_first_harvest")


def test_craft_records_craft_chapter_achievement(monkeypatch):
    game = create_game(monkeypatch)

    game.record_craft_quest_progress("craft_wolf_fang_charm", {"crafted": True})

    assert is_achievement_unlocked(game.player, "forest_first_craft")


def test_dungeon_clear_records_achievement(monkeypatch):
    game = create_game(monkeypatch)
    game.player["level"] = 10
    game.start_dungeon("forest_goblin_camp")
    move_active_dungeon_to_boss_loop(game)
    game.active_dungeon["rooms_cleared"] = 5
    monkeypatch.setattr(
        game,
        "_run_single_dungeon_combat",
        lambda enemy_id, multiplier=1.0: {
            "won": False,
            "enemy_id": enemy_id,
            "enemy_name": enemy_id,
        },
    )

    game.resolve_dungeon_boss_step()

    assert is_achievement_unlocked(game.player, "forest_camp_breaker_1")


def test_boss_loop_finished_records_single_boss_victories(monkeypatch):
    game = create_game(monkeypatch)
    game.player["level"] = 10
    game.start_dungeon("forest_rootcaller_lair")
    move_active_dungeon_to_boss_loop(game)
    game.active_dungeon["boss_victories"] = 2
    monkeypatch.setattr(
        game,
        "_run_single_dungeon_combat",
        lambda enemy_id, multiplier=1.0: {
            "won": False,
            "enemy_id": enemy_id,
            "enemy_name": enemy_id,
        },
    )

    game.resolve_dungeon_boss_step()

    assert is_achievement_unlocked(game.player, "forest_rootcaller_loop_1")


def test_defeat_boss_records_rootcaller_defeated(monkeypatch):
    game = create_game(monkeypatch)
    game.player["level"] = 10
    game.start_dungeon("forest_rootcaller_lair")
    move_active_dungeon_to_boss_loop(game)
    monkeypatch.setattr(
        game,
        "_run_single_dungeon_combat",
        lambda enemy_id, multiplier=1.0: {
            "won": True,
            "enemy_id": "grubfang_rootcaller",
            "enemy_name": "Grubfang, Rootcaller",
            "exp": 0,
            "gold": 0,
            "drops": [],
            "inventory_result": {"added": [], "failed": [], "pending": []},
        },
    )

    game.resolve_dungeon_boss_step()

    assert is_achievement_unlocked(game.player, "forest_rootcaller_defeated")
