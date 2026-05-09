import json

from systems.save_load import (
    build_save_data,
    ensure_save_directory,
    get_default_save_path,
    has_save_file,
    load_data_from_file,
    save_data_to_file,
    save_game,
    validate_save_data,
)


class DummyGame:
    def __init__(self):
        self.selected_class = "warrior"
        self.selected_zone = "forest_goblin"
        self.player = {"name": "Hero", "level": 2}
        self.mailbox = {"mails": []}
        self.state = "town"
        self.combat = {"temporary": True}
        self.auto_mode = True
        self.last_combat_result = {"exp_gained": 1}
        self.last_instance_result = {"zone": "forest_goblin"}
        self.last_gathering_result = {"gathered": True}
        self.data = {"not": "saved"}


def test_has_save_file_returns_false_when_file_does_not_exist(tmp_path):
    save_path = tmp_path / "missing_save.json"

    assert has_save_file(save_path) is False


def test_has_save_file_returns_true_when_file_exists(tmp_path):
    save_path = tmp_path / "save.json"
    save_path.write_text("{}", encoding="utf-8")

    assert has_save_file(save_path) is True


def test_ensure_save_directory_creates_parent_directory(tmp_path):
    save_path = tmp_path / "nested" / "save.json"
    assert save_path.parent.exists() is False

    save_directory = ensure_save_directory(save_path)

    assert save_directory == save_path.parent
    assert save_path.parent.exists() is True
    assert save_path.exists() is False


def test_get_default_save_path_returns_save_slot_path():
    save_path = get_default_save_path()

    assert "saves" in str(save_path)
    assert save_path.name == "save_slot_1.json"


def test_build_save_data_contains_expected_keys():
    save_data = build_save_data(DummyGame(), current_time=123)

    assert save_data["version"] == 1
    assert save_data["saved_at"] == 123
    assert save_data["selected_class"] == "warrior"
    assert save_data["selected_zone"] == "forest_goblin"
    assert save_data["player"] == {"name": "Hero", "level": 2}
    assert save_data["mailbox"] == {"mails": []}
    assert "state" not in save_data
    assert "combat" not in save_data
    assert "last_combat_result" not in save_data


def test_save_data_to_file_writes_json(tmp_path):
    save_path = tmp_path / "save.json"
    save_data = {"version": 1, "selected_class": "warrior", "player": {}}

    assert save_data_to_file(save_data, save_path) is True

    with save_path.open("r", encoding="utf-8") as save_file:
        loaded = json.load(save_file)
    assert loaded == save_data


def test_load_data_from_file_returns_none_when_missing(tmp_path):
    save_path = tmp_path / "missing.json"

    assert load_data_from_file(save_path) is None


def test_load_data_from_file_reads_dict(tmp_path):
    save_path = tmp_path / "save.json"
    save_path.write_text('{"version": 1}', encoding="utf-8")

    assert load_data_from_file(save_path) == {"version": 1}


def test_load_data_from_file_returns_none_for_non_dict_json(tmp_path):
    save_path = tmp_path / "save.json"
    save_path.write_text("[1, 2, 3]", encoding="utf-8")

    assert load_data_from_file(save_path) is None


def test_validate_save_data_accepts_valid_v1_save():
    save_data = {
        "version": 1,
        "selected_class": "warrior",
        "player": {"name": "Hero"},
    }

    assert validate_save_data(save_data) is True


def test_validate_save_data_rejects_missing_player():
    save_data = {"version": 1, "selected_class": "warrior"}

    assert validate_save_data(save_data) is False


def test_validate_save_data_rejects_wrong_version():
    save_data = {
        "version": 2,
        "selected_class": "warrior",
        "player": {"name": "Hero"},
    }

    assert validate_save_data(save_data) is False


def test_save_game_writes_current_game(tmp_path):
    save_path = tmp_path / "save.json"

    assert save_game(DummyGame(), path=save_path, current_time=123) is True

    with save_path.open("r", encoding="utf-8") as save_file:
        loaded = json.load(save_file)
    assert loaded["version"] == 1
    assert loaded["saved_at"] == 123
    assert loaded["selected_class"] == "warrior"
    assert loaded["player"] == {"name": "Hero", "level": 2}
