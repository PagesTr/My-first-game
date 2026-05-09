import json
import time
from copy import deepcopy
from pathlib import Path


DEFAULT_SAVE_PATH = Path("saves/save_slot_1.json")


def get_default_save_path():
    return DEFAULT_SAVE_PATH


def has_save_file(path=None):
    save_path = Path(path) if path is not None else DEFAULT_SAVE_PATH
    return save_path.is_file()


def ensure_save_directory(path=None):
    save_path = Path(path) if path is not None else DEFAULT_SAVE_PATH
    save_path.parent.mkdir(parents=True, exist_ok=True)
    return save_path.parent


def build_save_data(game, current_time=None):
    if current_time is None:
        current_time = int(time.time())

    return {
        "version": 1,
        "saved_at": current_time,
        "selected_class": game.selected_class,
        "selected_zone": game.selected_zone,
        "player": deepcopy(game.player),
        "mailbox": deepcopy(game.mailbox),
    }


def save_data_to_file(save_data, path=None):
    save_path = Path(path) if path is not None else DEFAULT_SAVE_PATH
    ensure_save_directory(save_path)
    with save_path.open("w", encoding="utf-8") as save_file:
        json.dump(save_data, save_file, indent=2)
    return True


def load_data_from_file(path=None):
    save_path = Path(path) if path is not None else DEFAULT_SAVE_PATH
    if not save_path.is_file():
        return None

    with save_path.open("r", encoding="utf-8") as save_file:
        save_data = json.load(save_file)
    if not isinstance(save_data, dict):
        return None
    return save_data


def save_game(game, path=None, current_time=None):
    save_data = build_save_data(game, current_time)
    save_data_to_file(save_data, path)
    return True


def validate_save_data(save_data):
    if not isinstance(save_data, dict):
        return False
    if save_data.get("version") != 1:
        return False
    if save_data.get("player") is None:
        return False
    if save_data.get("selected_class") is None:
        return False
    return True
