from systems.loot import generate_randomized_stats


def test_percentage_stats_receive_small_randomized_bonus(monkeypatch):
    monkeypatch.setattr("systems.loot.random.randint", lambda _start, _end: 2)

    stats = generate_randomized_stats(
        {
            "loot_bonus": 0.05,
            "gold_bonus": 0.03,
            "crit_chance": 0.04,
            "dodge_chance": 0.03,
        },
        rarity="legendary",
    )

    for value in stats.values():
        assert value < 0.20


def test_multiplier_stats_receive_small_randomized_bonus(monkeypatch):
    monkeypatch.setattr("systems.loot.random.randint", lambda _start, _end: 2)

    stats = generate_randomized_stats({"crit_damage": 0.10}, rarity="legendary")

    assert stats["crit_damage"] <= 0.50


def test_flat_stats_keep_existing_integer_randomization(monkeypatch):
    monkeypatch.setattr("systems.loot.random.randint", lambda _start, _end: 0)

    stats = generate_randomized_stats(
        {
            "attack": 4,
            "defense": 2,
            "vitality": 1,
        },
        rarity="rare",
    )

    assert stats["attack"] >= 6
    assert stats["defense"] >= 4
    assert stats["vitality"] >= 3


def test_non_numeric_stats_are_preserved():
    stats = generate_randomized_stats({"tag": "sharp"}, rarity="legendary")

    assert stats["tag"] == "sharp"
