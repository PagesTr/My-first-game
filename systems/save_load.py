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
