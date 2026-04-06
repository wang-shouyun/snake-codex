"""UI bootstrap helpers for menu registration and app launch."""

from __future__ import annotations

import pygame

import settings
from game import SnakeGame

EXTRA_MODE_DEFINITIONS = [
    {
        "id": "rhythm_mode",
        "label": "Rhythm Mode",
        "description": "Beat-synced snake with combo timing and music-driven pacing.",
        "humans": 1,
        "ais": 0,
        "hazards": True,
        "coop": False,
        "category": "mode",
        "default_duration": (0, 1, 30),
    },
    {
        "id": "strategy_mode",
        "label": "Strategy Mode",
        "description": "Tactical snake with skill points, branching events, and AI roles.",
        "humans": 1,
        "ais": 1,
        "hazards": True,
        "coop": False,
        "category": "mode",
        "default_duration": (0, 2, 0),
    },
]


def register_menu_modes() -> None:
    """Ensure advanced modes exist in the shared mode list exactly once."""

    existing_ids = {mode["id"] for mode in settings.MODE_DEFINITIONS}
    for mode in EXTRA_MODE_DEFINITIONS:
        if mode["id"] not in existing_ids:
            settings.MODE_DEFINITIONS.append(mode.copy())
            existing_ids.add(mode["id"])


def create_game() -> SnakeGame:
    """Create a game instance after registering UI-visible modes."""

    register_menu_modes()
    return SnakeGame()


def run_app() -> None:
    """Launch the game using the current menu registration."""

    pygame.init()
    game = create_game()
    game.run()
    pygame.quit()
