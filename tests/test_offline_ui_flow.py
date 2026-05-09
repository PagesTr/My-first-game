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


def test_return_to_main_menu_saves_and_stops_active_gathering(monkeypatch):
    game = Game()
    save_calls = []
    game.player = {"inventory": {}}
    game.active_gathering = {"type": "gathering"}
    monkeypatch.setattr(game, "save_current_game", lambda: save_calls.append(True) or True)

    game.return_to_main_menu()

    assert game.state == "main_menu"
    assert game.active_gathering is None
    assert save_calls == [True]
