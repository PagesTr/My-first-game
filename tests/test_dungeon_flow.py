from core.game import Game


def select_first_class(game, monkeypatch, level=5):
    monkeypatch.setattr(game, "save_current_game", lambda: True)
    class_id = next(iter(game.data.classes))
    game.select_class(class_id)
    game.player["level"] = level
    game.player["current_hp"] = game.player["max_hp"]


def set_rest_step(game):
    dungeon = game.data.dungeons[game.active_dungeon["dungeon_id"]]
    rest_index = next(
        index
        for index, step in enumerate(dungeon["route"])
        if step.get("type") == "rest_choice"
    )
    game.active_dungeon["step_index"] = rest_index


def set_boss_step(game):
    dungeon = game.data.dungeons[game.active_dungeon["dungeon_id"]]
    boss_index = next(
        index
        for index, step in enumerate(dungeon["route"])
        if step.get("type") == "boss_loop"
    )
    game.active_dungeon["step_index"] = boss_index


def test_start_dungeon_creates_active_dungeon(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)

    result = game.start_dungeon("forest_goblin_camp")

    assert result == {"started": True, "dungeon_id": "forest_goblin_camp"}
    assert game.active_dungeon["dungeon_id"] == "forest_goblin_camp"
    assert game.active_dungeon["step_index"] == 0


def test_start_unknown_dungeon_returns_reason(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)

    result = game.start_dungeon("unknown")

    assert result == {"started": False, "reason": "unknown_dungeon"}


def test_get_active_dungeon_step_returns_first_step(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)
    game.start_dungeon("forest_goblin_camp")

    step = game.get_active_dungeon_step()

    assert step["type"] == "combat"
    assert step["enemy_id"] == "young_goblin"


def test_apply_rest_choice_requires_rest_step(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)
    game.start_dungeon("forest_goblin_camp")

    result = game.apply_dungeon_rest_choice("heal")

    assert result["applied"] is False
    assert result["reason"] == "not_rest_choice_step"


def test_apply_rest_choice_advances_after_heal(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)
    game.start_dungeon("forest_goblin_camp")
    set_rest_step(game)
    previous_step_index = game.active_dungeon["step_index"]
    game.player["current_hp"] = 10

    result = game.apply_dungeon_rest_choice("heal")

    assert result["applied"] is True
    assert game.player["current_hp"] > 10
    assert game.active_dungeon["rest_choice_used"] is True
    assert game.active_dungeon["step_index"] == previous_step_index + 1


def test_resolve_dungeon_combat_step_advances_on_win(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)
    game.start_dungeon("forest_goblin_camp")
    monkeypatch.setattr(
        game,
        "_run_single_dungeon_combat",
        lambda enemy_id, multiplier=1.0: {
            "won": True,
            "enemy_id": enemy_id,
            "drops": [],
            "exp": 1,
            "gold": 1,
        },
    )

    result = game.resolve_dungeon_combat_step()

    assert result["resolved"] is True
    assert result["won"] is True
    assert game.active_dungeon["step_index"] == 1


def test_dungeon_tracks_room_rewards_on_combat_win(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)
    game.start_dungeon("forest_goblin_camp")
    drops = [{"kind": "stackable", "item": "goblin_ear", "quantity": 2}]
    monkeypatch.setattr(
        game,
        "_run_single_dungeon_combat",
        lambda enemy_id, multiplier=1.0: {
            "won": True,
            "enemy_id": enemy_id,
            "drops": drops,
            "exp": 7,
            "gold": 3,
        },
    )

    game.resolve_dungeon_combat_step()

    assert game.active_dungeon["rooms_cleared"] == 1
    assert game.active_dungeon["total_gold"] == 3
    assert game.active_dungeon["total_exp"] == 7
    assert game.active_dungeon["loot"] == drops


def test_dungeon_combat_adds_drops_to_inventory(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)
    drop = {"kind": "stackable", "item": "goblin_ear", "quantity": 2}

    result = game._add_dungeon_drops_to_inventory([drop])

    assert result["added"] == [drop]
    assert result["pending"] == []
    assert any(
        slot
        and slot.get("kind") == "stackable"
        and slot.get("item") == "goblin_ear"
        and slot.get("quantity") == 2
        for slot in game.player["inventory"]["slots"]
    )


def test_dungeon_equipment_drop_added_as_individual(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)
    drop = {"kind": "individual", "item": "scavenger_gloves", "quantity": 1}

    result = game._add_dungeon_drops_to_inventory([drop])

    assert result["added"] == [drop]
    assert any(
        slot
        and slot.get("kind") == "individual"
        and slot.get("item") == "scavenger_gloves"
        for slot in game.player["inventory"]["slots"]
    )


def test_dungeon_drops_go_pending_when_inventory_full(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)
    inventory = game.player["inventory"]
    inventory["slots"] = [
        {"kind": "individual", "item": "scavenger_gloves", "rarity": "common", "stats": {}}
        for _ in range(inventory["size"])
    ]
    drop = {"kind": "individual", "item": "scavenger_gloves", "quantity": 1}

    result = game._add_dungeon_drops_to_inventory([drop])

    assert result["added"] == []
    assert result["pending"] == [drop]


def test_dungeon_result_contains_pending_loot(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)
    game.start_dungeon("forest_goblin_camp")
    pending_drop = {"kind": "individual", "item": "scavenger_gloves", "quantity": 1}
    game.active_dungeon["pending_loot"] = [pending_drop]

    result = game._build_dungeon_result("boss_defeat", "goblin_quartermaster")

    assert result["pending_loot"] == [pending_drop]


def test_resolve_dungeon_combat_step_marks_failed_on_loss(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)
    game.start_dungeon("forest_goblin_camp")
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

    result = game.resolve_dungeon_combat_step()

    assert result["resolved"] is True
    assert result["won"] is False
    assert game.active_dungeon["failed"] is True


def test_resolve_dungeon_boss_step_increases_boss_victories_on_win(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)
    game.start_dungeon("forest_buried_grove")
    set_boss_step(game)
    monkeypatch.setattr(
        game,
        "_run_single_dungeon_combat",
        lambda enemy_id, multiplier=1.0: {
            "won": True,
            "enemy_id": enemy_id,
            "drops": [],
            "exp": 1,
            "gold": 1,
        },
    )

    result = game.resolve_dungeon_boss_step()

    assert result["resolved"] is True
    assert result["won"] is True
    assert result["boss_victories"] == 1
    assert game.active_dungeon is not None


def test_resolve_dungeon_boss_step_completes_on_loss(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)
    game.start_dungeon("forest_buried_grove")
    set_boss_step(game)
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

    result = game.resolve_dungeon_boss_step()

    assert result["resolved"] is True
    assert result["won"] is False
    assert result["completed"] is True
    assert game.active_dungeon is None


def test_dungeon_result_created_on_boss_loss(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)
    game.start_dungeon("forest_buried_grove")
    set_boss_step(game)
    game.active_dungeon["boss_victories"] = 2
    game.active_dungeon["rooms_cleared"] = 4
    game.active_dungeon["total_gold"] = 30
    game.active_dungeon["total_exp"] = 42
    game.active_dungeon["loot"] = [
        {"kind": "stackable", "item": "chewed_bone", "quantity": 1}
    ]
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

    result = game.resolve_dungeon_boss_step()

    assert result["completed"] is True
    assert game.last_dungeon_result["completed"] is True
    assert game.last_dungeon_result["reason"] == "boss_defeat"
    assert game.last_dungeon_result["boss_victories"] == 2
    assert game.last_dungeon_result["rooms_cleared"] == 4
    assert game.last_dungeon_result["total_gold"] == 30
    assert game.last_dungeon_result["total_exp"] == 42
    assert game.active_dungeon is None


def test_rest_choice_is_stored_for_summary(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)
    game.start_dungeon("forest_goblin_camp")
    set_rest_step(game)

    result = game.apply_dungeon_rest_choice("heal")

    assert result["applied"] is True
    assert game.active_dungeon["rest_choice"] == "heal"


def test_boss_multiplier_increases_between_victories(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)
    game.start_dungeon("forest_buried_grove")
    set_boss_step(game)
    captured_multipliers = []

    def fake_combat(enemy_id, multiplier=1.0):
        captured_multipliers.append(multiplier)
        return {
            "won": True,
            "enemy_id": enemy_id,
            "drops": [],
            "exp": 1,
            "gold": 1,
        }

    monkeypatch.setattr(game, "_run_single_dungeon_combat", fake_combat)

    game.resolve_dungeon_boss_step()
    game.resolve_dungeon_boss_step()

    assert captured_multipliers[1] > captured_multipliers[0]
