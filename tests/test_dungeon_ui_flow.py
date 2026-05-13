from core.game import Game


def select_first_class(game, monkeypatch, level=5):
    monkeypatch.setattr(game, "save_current_game", lambda: True)
    class_id = next(iter(game.data.classes))
    game.select_class(class_id)
    game.player["level"] = level


def test_get_available_dungeons_filters_by_region():
    game = Game()

    dungeon_ids = {
        entry["dungeon_id"]
        for entry in game.get_available_dungeons("forest")
    }

    assert "forest_goblin_camp" in dungeon_ids
    assert "forest_buried_grove" in dungeon_ids


def test_get_active_dungeon_summary_without_active_dungeon():
    game = Game()

    assert game.get_active_dungeon_summary() == {"active": False}


def test_get_active_dungeon_summary_with_active_dungeon(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)

    game.start_dungeon("forest_goblin_camp")
    summary = game.get_active_dungeon_summary()

    assert summary["active"] is True
    assert summary["dungeon_id"] == "forest_goblin_camp"
    assert summary["dungeon_name"] == "Goblin Camp"
    assert summary["step"]["type"] == "combat"


def test_open_inventory_from_dungeon_sets_return_state():
    game = Game()

    game.open_inventory_from_dungeon()

    assert game.state == "inventory"
    assert game.return_state_after_inventory == "dungeon"


def test_return_from_inventory_if_needed_restores_dungeon_state():
    game = Game()
    game.return_state_after_inventory = "dungeon"
    game.state = "inventory"

    returned = game.return_from_inventory_if_needed()

    assert returned is True
    assert game.state == "dungeon"
    assert game.return_state_after_inventory is None


def test_inventory_back_returns_to_dungeon_when_requested():
    game = Game()
    game.state = "inventory"
    game.return_state_after_inventory = "dungeon"

    returned = game.return_from_inventory_if_needed()

    assert returned is True
    assert game.state == "dungeon"
    assert game.return_state_after_inventory is None


def test_inventory_back_without_return_state_goes_town():
    game = Game()
    game.state = "inventory"

    returned = game.return_from_inventory_if_needed()

    assert returned is False
    assert game.state == "inventory"


def test_last_dungeon_result_summary_available_after_boss_loss(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)
    game.start_dungeon("forest_buried_grove")
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
            "enemy_id": enemy_id,
            "drops": [],
            "exp": 0,
            "gold": 0,
        },
    )

    game.resolve_dungeon_boss_step()
    result = game.get_last_dungeon_result()

    assert isinstance(result, dict)
    assert result["completed"] is True
    assert result["reason"] == "boss_defeat"
    assert result["dungeon_id"] == "forest_buried_grove"
