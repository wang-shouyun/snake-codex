"""Keyboard input helpers."""

from __future__ import annotations

import pygame

PLAYER_ONE_KEYS = {
    pygame.K_UP: (0, -1),
    pygame.K_DOWN: (0, 1),
    pygame.K_LEFT: (-1, 0),
    pygame.K_RIGHT: (1, 0),
}

PLAYER_TWO_KEYS = {
    pygame.K_w: (0, -1),
    pygame.K_s: (0, 1),
    pygame.K_a: (-1, 0),
    pygame.K_d: (1, 0),
}

MENU_UP_KEYS = {pygame.K_UP, pygame.K_w}
MENU_DOWN_KEYS = {pygame.K_DOWN, pygame.K_s}
CONFIRM_KEYS = {pygame.K_RETURN, pygame.K_SPACE}


def direction_for_key(key: int, controls: dict[int, tuple[int, int]]) -> tuple[int, int] | None:
    """Translate a key into a direction for a given control map."""
    return controls.get(key)
