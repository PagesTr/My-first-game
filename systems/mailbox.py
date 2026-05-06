def create_mailbox():
    return []


def add_mail(mailbox, mail, limit=20):
    mailbox.insert(0, mail)
    del mailbox[limit:]
    return mailbox


def format_drop(drop):
    if isinstance(drop, str):
        return drop
    if isinstance(drop, dict):
        item = drop.get("item", "unknown_item")
        quantity = drop.get("quantity")
        if quantity is not None and quantity > 1:
            return f"{item} x{quantity}"
        return item
    return str(drop)


def format_drops(drops):
    if not drops:
        return "None"
    return ", ".join(format_drop(drop) for drop in drops)


def create_combat_report_mail(combat_report, rewards=None):
    rewards = rewards or {}
    enemy_name = combat_report.get("enemy_name", "Unknown Enemy")
    winner = combat_report.get("winner") or "unknown"
    result_label = "Victory" if winner == "player" else "Defeat"
    title = f"{result_label} vs {enemy_name}"
    turns = combat_report.get("turns", 0)
    exp_gained = rewards.get("exp_gained", 0)
    gold_gained = rewards.get("gold_gained", 0)
    drops = rewards.get("drops", [])
    history = combat_report.get("history", [])

    summary = f"Turns: {turns} | EXP: {exp_gained} | Gold: {gold_gained}"
    body_lines = [
        f"Winner: {winner}",
        f"Enemy: {enemy_name}",
        f"Turns: {turns}",
        f"EXP: {exp_gained}",
        f"Gold: {gold_gained}",
        f"Drops: {format_drops(drops)}",
        "",
        "Combat log:",
    ]
    body_lines.extend(history)

    return {
        "type": "combat_report",
        "title": title,
        "summary": summary,
        "body": "\n".join(body_lines),
        "read": False,
        "payload": combat_report,
    }
