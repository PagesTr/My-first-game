import core.game as game_module
from core.game import Game


def select_first_class(game, monkeypatch):
    monkeypatch.setattr(game, "save_current_game", lambda: True)
    class_id = next(iter(game.data.classes))
    game.select_class(class_id)


def test_send_current_player_offline_gathering_starts_activity_and_goes_main_menu(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)

    result = game.send_current_player_offline_gathering("forest_goblin", "druid")

    assert result["started"] is True
    assert isinstance(game.player["offline_activity"], dict)
    assert game.state == "main_menu"
    assert game.main_menu_message == "Offline gathering started"


def test_send_current_player_offline_gathering_rejects_unknown_node(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)

    result = game.send_current_player_offline_gathering(
        "forest_goblin",
        "prospector",
    )

    assert result == {"started": False, "reason": "unknown_node"}


def test_load_saved_game_resolves_offline_progress(monkeypatch):
    game = Game()
    save_data = {
        "version": 1,
        "selected_class": "warrior",
        "selected_zone": "forest_goblin",
        "player": {"offline_activity": None},
        "mailbox": {"mails": []},
    }
    offline_result = {"resolved": True, "ticks": 2}

    monkeypatch.setattr(game_module, "load_data_from_file", lambda: save_data)
    monkeypatch.setattr(game_module, "validate_save_data", lambda data: True)
    monkeypatch.setattr(game_module, "prepare_player_for_combat", lambda *args: None)
    monkeypatch.setattr(game, "resolve_offline_progress", lambda: offline_result)

    loaded = game.load_saved_game()

    assert loaded is True
    assert game.last_offline_result == offline_result
    assert game.state == "town"


def test_load_saved_game_resolves_and_clears_offline_activity(monkeypatch):
    game = Game()
    save_calls = []
    offline_activity = {
        "type": "gathering",
        "zone_id": "forest_goblin",
        "profession_id": "druid",
        "started_at": 1000,
        "last_claimed_at": 1000,
    }
    save_data = {
        "version": 1,
        "selected_class": "warrior",
        "selected_zone": "forest_goblin",
        "player": {"offline_activity": offline_activity},
        "mailbox": {"mails": []},
    }
    offline_result = {"resolved": True, "ticks": 2}

    monkeypatch.setattr(game_module, "load_data_from_file", lambda: save_data)
    monkeypatch.setattr(game_module, "validate_save_data", lambda data: True)
    monkeypatch.setattr(game_module, "prepare_player_for_combat", lambda *args: None)
    monkeypatch.setattr(game, "resolve_offline_progress", lambda: offline_result)
    monkeypatch.setattr(game, "save_current_game", lambda: save_calls.append(True) or True)

    loaded = game.load_saved_game()

    assert loaded is True
    assert game.state == "town"
    assert game.last_offline_result == offline_result
    assert game.player["offline_activity"] is None
    assert save_calls == [True]


def test_load_saved_game_clears_offline_activity_even_when_not_enough_time(monkeypatch):
    game = Game()
    save_calls = []
    offline_activity = {
        "type": "gathering",
        "zone_id": "forest_goblin",
        "profession_id": "druid",
        "started_at": 1000,
        "last_claimed_at": 1000,
    }
    save_data = {
        "version": 1,
        "selected_class": "warrior",
        "selected_zone": "forest_goblin",
        "player": {"offline_activity": offline_activity},
        "mailbox": {"mails": []},
    }
    offline_result = {"resolved": False, "reason": "not_enough_time"}

    monkeypatch.setattr(game_module, "load_data_from_file", lambda: save_data)
    monkeypatch.setattr(game_module, "validate_save_data", lambda data: True)
    monkeypatch.setattr(game_module, "prepare_player_for_combat", lambda *args: None)
    monkeypatch.setattr(game, "resolve_offline_progress", lambda: offline_result)
    monkeypatch.setattr(game, "save_current_game", lambda: save_calls.append(True) or True)

    loaded = game.load_saved_game()

    assert loaded is True
    assert game.state == "town"
    assert game.last_offline_result == offline_result
    assert game.player["offline_activity"] is None
    assert save_calls == [True]


def test_return_to_main_menu_saves_and_stops_active_gathering(monkeypatch):
    game = Game()
    save_calls = []
    game.player = {"inventory": {}, "offline_activity": None}
    game.active_gathering = {"type": "gathering"}
    monkeypatch.setattr(game, "save_current_game", lambda: save_calls.append(True) or True)

    game.return_to_main_menu()

    assert game.state == "main_menu"
    assert game.active_gathering is None
    assert game.player["offline_activity"] is None
    assert save_calls == [True]


def test_return_to_main_menu_does_not_create_offline_activity(monkeypatch):
    game = Game()
    game.player = {"inventory": {}, "offline_activity": None}
    monkeypatch.setattr(game, "save_current_game", lambda: True)

    game.return_to_main_menu()

    assert game.state == "main_menu"
    assert game.player["offline_activity"] is None


def test_return_to_main_menu_stops_active_gathering(monkeypatch):
    game = Game()
    game.player = {"inventory": {}, "offline_activity": None}
    game.active_gathering = {"type": "gathering"}
    monkeypatch.setattr(game, "save_current_game", lambda: True)

    game.return_to_main_menu()

    assert game.state == "main_menu"
    assert game.active_gathering is None


def test_send_current_player_offline_gathering_is_only_way_to_start_offline(monkeypatch):
    game = Game()
    select_first_class(game, monkeypatch)

    assert game.player["offline_activity"] is None

    result = game.send_current_player_offline_gathering("forest_goblin", "druid")

    assert result["started"] is True
    assert isinstance(game.player["offline_activity"], dict)
