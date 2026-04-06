"""Small reusable helper functions."""

from __future__ import annotations

import random

import settings

DIRECTIONS = [(0, -1), (0, 1), (-1, 0), (1, 0)]


def inside_board(position: tuple[int, int]) -> bool:
    """Return True when a cell is inside the visible grid."""
    x, y = position
    return 0 <= x < settings.BOARD_COLS and 0 <= y < settings.BOARD_ROWS


def random_grid_position(blocked_positions: set[tuple[int, int]]) -> tuple[int, int]:
    """Return a free position on the board."""
    available_positions = [
        (x, y)
        for x in range(settings.BOARD_COLS)
        for y in range(settings.BOARD_ROWS)
        if (x, y) not in blocked_positions
    ]
    if not available_positions:
        raise ValueError("No available positions remain on the board.")
    return random.choice(available_positions)


def manhattan_distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Return the Manhattan distance between two cells."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def weighted_choice(weighted_values: list[tuple[str, float]]) -> str:
    """Choose one value from a weighted list."""
    total_weight = sum(weight for _, weight in weighted_values)
    roll = random.uniform(0, total_weight)
    cursor = 0.0
    for value, weight in weighted_values:
        cursor += weight
        if roll <= cursor:
            return value
    return weighted_values[-1][0]
