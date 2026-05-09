def create_player_professions(professions_data):
    if not isinstance(professions_data, dict):
        return {}

    return {
        profession_id: {
            "level": 1,
            "xp": 0,
            "next_xp": 20,
        }
        for profession_id in professions_data
    }


def ensure_player_professions(player, professions_data):
    if "professions" not in player or not isinstance(player["professions"], dict):
        player["professions"] = {}

    for profession_id, profession_progress in create_player_professions(professions_data).items():
        player["professions"].setdefault(profession_id, profession_progress)

    return player["professions"]


def get_profession_level(player, profession_id):
    professions = player.get("professions")
    if not isinstance(professions, dict):
        return 0

    profession = professions.get(profession_id)
    if not isinstance(profession, dict):
        return 0

    level = profession.get("level", 0)
    if not isinstance(level, int):
        return 0
    return level


def get_profession_progress(player, profession_id):
    professions = player.get("professions")
    if not isinstance(professions, dict):
        return {"level": 0, "xp": 0, "next_xp": 0}

    profession = professions.get(profession_id)
    if not isinstance(profession, dict):
        return {"level": 0, "xp": 0, "next_xp": 0}

    return {
        "level": profession.get("level", 0),
        "xp": profession.get("xp", 0),
        "next_xp": profession.get("next_xp", 0),
    }


def add_profession_xp(player, profession_id, amount):
    progress = get_profession_progress(player, profession_id)
    if progress["level"] <= 0:
        return {
            "leveled_up": False,
            "level": 0,
            "xp": 0,
            "next_xp": 0,
        }

    if not isinstance(amount, (int, float)) or amount <= 0:
        return {
            "leveled_up": False,
            "level": progress["level"],
            "xp": progress["xp"],
            "next_xp": progress["next_xp"],
        }

    profession = player["professions"][profession_id]
    profession["xp"] = profession.get("xp", 0) + int(amount)
    profession.setdefault("next_xp", 20)
    leveled_up = False

    while profession["xp"] >= profession["next_xp"]:
        profession["xp"] -= profession["next_xp"]
        profession["level"] = profession.get("level", 1) + 1
        profession["next_xp"] = int(profession["next_xp"] * 1.5)
        leveled_up = True

    return {
        "leveled_up": leveled_up,
        "level": profession["level"],
        "xp": profession["xp"],
        "next_xp": profession["next_xp"],
    }


def get_profession_mastery(player, profession_id, professions_data):
    if not isinstance(professions_data, dict):
        return 0

    profession_data = professions_data.get(profession_id)
    if not isinstance(profession_data, dict):
        return 0

    level = get_profession_level(player, profession_id)
    primary_stat = profession_data.get("primary_stat")
    mastery_bonus_stat = profession_data.get("mastery_bonus_stat")

    primary_stat_value = player.get(primary_stat, 0)
    mastery_bonus = player.get(mastery_bonus_stat, 0)
    global_gathering_mastery = player.get("gathering_mastery", 0)

    mastery = (
        level
        + int(primary_stat_value / 2)
        + mastery_bonus
        + global_gathering_mastery
    )
    return max(0, mastery)
