import json
from pathlib import Path

# Data files are stored in the Examples/data folder.
DATA_DIR = Path(__file__).with_name('data')

class DataManager:
    def __init__(self):
        self.classes = self.load("data/classes.json")
        self.items = self.load("data/items.json")
        self.enemies = self.load("data/enemies.json")
        self.recipes = self.load("data/recipes.json")
        self.zones = self.load("data/zones.json")
        self.skills = self.load("data/skills.json")
        self.professions = self.load("data/professions.json")
        self.gathering_nodes = self.load("data/gathering_nodes.json")
        self.quests = self.load("data/quests.json")
        self.achievements = self.load("data/achievements.json")

    def load(self, path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)

def load_data(filename):
    """Load JSON content from the data folder."""
    path = DATA_DIR / filename
    with path.open(encoding='utf-8') as file:
        return json.load(file)
