from systems.mailbox import (
    add_mail,
    create_combat_report_mail,
    create_mailbox,
    format_drop,
    format_drops,
)


def make_combat_report():
    return {
        "enemy_name": "Goblin",
        "turns": 3,
        "winner": "player",
        "history": [
            "Turn 1: Player attacks -> 4 damage",
            "Turn 2: Enemy attacks -> 2 damage",
        ],
    }


def test_create_mailbox_returns_empty_list():
    assert create_mailbox() == []


def test_add_mail_inserts_newest_first():
    mailbox = create_mailbox()

    add_mail(mailbox, {"title": "First"})
    add_mail(mailbox, {"title": "Second"})

    assert mailbox == [{"title": "Second"}, {"title": "First"}]


def test_add_mail_respects_limit():
    mailbox = create_mailbox()

    add_mail(mailbox, {"title": "First"}, limit=2)
    add_mail(mailbox, {"title": "Second"}, limit=2)
    add_mail(mailbox, {"title": "Third"}, limit=2)

    assert mailbox == [{"title": "Third"}, {"title": "Second"}]


def test_format_drop_handles_string():
    assert format_drop("wolf_pelt") == "wolf_pelt"


def test_format_drop_handles_dict_with_quantity():
    drop = {"item": "wolf_pelt", "quantity": 3}

    assert format_drop(drop) == "wolf_pelt x3"


def test_format_drops_returns_none_for_empty_list():
    assert format_drops([]) == "None"


def test_create_combat_report_mail_contains_expected_fields():
    mail = create_combat_report_mail(make_combat_report())

    assert mail["type"] == "combat_report"
    assert mail["title"] == "Victory vs Goblin"
    assert "Turns: 3" in mail["summary"]
    assert "Combat log:" in mail["body"]
    assert mail["read"] is False
    assert mail["payload"] == make_combat_report()


def test_create_combat_report_mail_includes_rewards():
    rewards = {
        "exp_gained": 5,
        "gold_gained": 3,
        "drops": [{"item": "wolf_pelt", "quantity": 2}],
    }

    mail = create_combat_report_mail(make_combat_report(), rewards)

    assert "EXP: 5" in mail["summary"]
    assert "Gold: 3" in mail["summary"]
    assert "Drops: wolf_pelt x2" in mail["body"]
