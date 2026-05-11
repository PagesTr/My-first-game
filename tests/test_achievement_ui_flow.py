import pygame

from core.game import Game
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
