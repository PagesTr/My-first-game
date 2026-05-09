from systems.save_load import (
    ensure_save_directory,
    get_default_save_path,
    has_save_file,
)


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
