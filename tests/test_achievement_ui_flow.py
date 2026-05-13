import pygame

from core.game import Game
from ui.pygame_app import PygameApp
from ui.screens.achievements_screen import AchievementsScreen
from ui.screens.menu_screen import MenuScreen


def setup_module(module):
    pygame.init()
    pygame.font.init()


def test_achievements_state_can_be_selected_from_town():
    game = Game()
    game.state = "town"
    menu = MenuScreen(game)

    event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"pos": menu.achievements_button.rect.center, "button": 1},
    )
    menu.handle_event(event)

    assert game.state == "achievements"


def test_achievements_screen_imports():
    game = Game()
    screen = AchievementsScreen(game)

    assert screen.selected_category == "all"


def test_achievements_screen_filters_category():
    game = Game()
    screen = AchievementsScreen(game)
    screen.selected_category = "combat"

    achievements = screen._get_filtered_achievements()

    assert achievements
    assert all(achievement.get("category") == "combat" for _, achievement in achievements)


def test_achievement_progress_summary_handles_missing_player():
    game = Game()
    screen = AchievementsScreen(game)
    achievement = game.data.achievements["forest_rat_cleaner_1"]

    current, required = screen._get_progress_summary("forest_rat_cleaner_1", achievement)

    assert current == 0
    assert required == 25


def test_achievement_reward_formatting():
    game = Game()
    screen = AchievementsScreen(game)

    assert screen._format_reward({"type": "gold", "amount": 50}) == "+50 gold"
    assert screen._format_reward({"type": "stat_bonus", "stat": "luck", "amount": 1}) == "+1 luck"
    assert screen._format_reward({"type": "percent_bonus", "stat": "xp_bonus", "amount": 0.02}) == "+2% xp_bonus"
    assert screen._format_reward({"type": "item", "item": "field_dressing", "quantity": 2}) == "+2 Field Dressing"


def test_claimable_filter_does_not_crash():
    game = Game()
    screen = AchievementsScreen(game)
    screen.selected_category = "claimable"

    achievements = screen._get_filtered_achievements()

    assert achievements == []


def test_claim_reward_button_claims_selected_achievement(monkeypatch):
    game = Game()
    monkeypatch.setattr(game, "save_current_game", lambda: True)
    class_id = next(iter(game.data.classes))
    game.select_class(class_id)
    game.player["achievements"]["unlocked"].append("forest_rat_cleaner_1")
    screen = AchievementsScreen(game)
    screen.selected_achievement_id = "forest_rat_cleaner_1"

    result = screen._claim_selected_achievement()

    assert result["claimed"] is True
    assert "forest_rat_cleaner_1" in game.player["achievements"]["claimed"]


def test_claim_selected_achievement_handles_locked(monkeypatch):
    game = Game()
    monkeypatch.setattr(game, "save_current_game", lambda: True)
    class_id = next(iter(game.data.classes))
    game.select_class(class_id)
    screen = AchievementsScreen(game)
    screen.selected_achievement_id = "forest_rat_cleaner_1"

    result = screen._claim_selected_achievement()

    assert result["claimed"] is False
    assert result["reason"] == "not_unlocked"


def test_claimable_filter_returns_only_claimable(monkeypatch):
    game = Game()
    monkeypatch.setattr(game, "save_current_game", lambda: True)
    class_id = next(iter(game.data.classes))
    game.select_class(class_id)
    game.player["achievements"]["unlocked"].extend([
        "forest_rat_cleaner_1",
        "forest_bad_decision_manager",
    ])
    game.player["achievements"]["claimed"].append("forest_bad_decision_manager")
    screen = AchievementsScreen(game)
    screen.selected_category = "claimable"

    achievement_ids = [achievement_id for achievement_id, _ in screen._get_filtered_achievements()]

    assert achievement_ids == ["forest_rat_cleaner_1"]
    assert all(screen._get_claim_status(achievement_id) == "claimable" for achievement_id in achievement_ids)


def test_claimed_filter_returns_only_claimed(monkeypatch):
    game = Game()
    monkeypatch.setattr(game, "save_current_game", lambda: True)
    class_id = next(iter(game.data.classes))
    game.select_class(class_id)
    game.player["achievements"]["unlocked"].extend([
        "forest_rat_cleaner_1",
        "forest_bad_decision_manager",
    ])
    game.player["achievements"]["claimed"].append("forest_bad_decision_manager")
    screen = AchievementsScreen(game)
    screen.selected_category = "claimed"

    achievement_ids = [achievement_id for achievement_id, _ in screen._get_filtered_achievements()]

    assert achievement_ids == ["forest_bad_decision_manager"]
    assert all(screen._get_claim_status(achievement_id) == "claimed" for achievement_id in achievement_ids)


def test_in_progress_filter_returns_progress_only(monkeypatch):
    game = Game()
    monkeypatch.setattr(game, "save_current_game", lambda: True)
    class_id = next(iter(game.data.classes))
    game.select_class(class_id)
    game.player["achievements"]["progress"]["forest_rat_cleaner_1"] = 12
    screen = AchievementsScreen(game)
    screen.selected_category = "in_progress"

    achievement_ids = [achievement_id for achievement_id, _ in screen._get_filtered_achievements()]

    assert "forest_rat_cleaner_1" in achievement_ids
    assert all(screen._get_claim_status(achievement_id) == "locked" for achievement_id in achievement_ids)


def test_claim_selected_achievement_stores_result(monkeypatch):
    game = Game()
    monkeypatch.setattr(game, "save_current_game", lambda: True)
    class_id = next(iter(game.data.classes))
    game.select_class(class_id)
    game.player["achievements"]["unlocked"].append("forest_rat_cleaner_1")
    screen = AchievementsScreen(game)
    screen.selected_achievement_id = "forest_rat_cleaner_1"

    result = screen._claim_selected_achievement()

    assert result["claimed"] is True
    assert screen.last_claim_result == result
    assert screen.last_claim_achievement_id == "forest_rat_cleaner_1"
    assert "forest_rat_cleaner_1" in game.player["achievements"]["claimed"]


def test_empty_filter_does_not_crash():
    game = Game()
    screen = AchievementsScreen(game)
    screen.selected_category = "claimable"

    assert screen._get_filtered_achievements() == []


def test_claim_status_helper_handles_missing_player():
    game = Game()
    screen = AchievementsScreen(game)

    assert screen._get_claim_status("some_id") == "locked"


def test_town_claimable_achievement_count_returns_zero_without_player():
    game = Game()
    menu = MenuScreen(game)

    assert menu._get_claimable_achievement_count() == 0


def test_town_claimable_achievement_count_detects_unclaimed_unlocked():
    game = Game()
    game.player = {
        "achievements": {
            "unlocked": ["forest_rat_cleaner_1"],
            "claimed": [],
            "progress": {},
            "last_unlocked": [],
        }
    }
    menu = MenuScreen(game)

    assert menu._get_claimable_achievement_count() == 1


def test_town_claimable_achievement_count_ignores_claimed():
    game = Game()
    game.player = {
        "achievements": {
            "unlocked": ["forest_rat_cleaner_1"],
            "claimed": ["forest_rat_cleaner_1"],
            "progress": {},
            "last_unlocked": [],
        }
    }
    menu = MenuScreen(game)

    assert menu._get_claimable_achievement_count() == 0


def test_draw_achievements_claim_badge_does_not_crash():
    game = Game()
    menu = MenuScreen(game)
    surface = pygame.Surface((800, 600))

    menu._draw_achievements_claim_badge(surface, 3)


def test_achievement_toast_sync_captures_last_unlocked(monkeypatch):
    app = PygameApp()
    monkeypatch.setattr(app.game, "save_current_game", lambda: True)
    app.game.player = {
        "achievements": {
            "unlocked": ["forest_rat_cleaner_1"],
            "claimed": [],
            "progress": {},
            "last_unlocked": ["forest_rat_cleaner_1"],
        }
    }

    app._sync_achievement_toast(1000)

    assert app.achievement_toast_ids == ["forest_rat_cleaner_1"]
    assert app.game.player["achievements"]["last_unlocked"] == []


def test_achievement_toast_sync_handles_missing_player():
    app = PygameApp()
    app.game.player = None

    app._sync_achievement_toast(1000)

    assert app.achievement_toast_ids == []


def test_achievement_toast_expires_after_duration():
    app = PygameApp()
    app.achievement_toast_ids = ["forest_rat_cleaner_1"]
    app.achievement_toast_started_at = 0
    surface = pygame.Surface((800, 600))

    app._draw_achievement_toast(surface, app.achievement_toast_duration_ms + 1)

    assert app.achievement_toast_ids == []


def test_achievement_toast_draw_does_not_crash():
    app = PygameApp()
    app.achievement_toast_ids = ["forest_rat_cleaner_1"]
    app.achievement_toast_started_at = 1000
    surface = pygame.Surface((800, 600))

    app._draw_achievement_toast(surface, 1000)
