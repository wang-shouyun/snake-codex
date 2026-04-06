"""Collision and portal helpers."""

from __future__ import annotations

from utils.helpers import inside_board


def out_of_bounds(position: tuple[int, int]) -> bool:
    """Return True when a position leaves the board."""
    return not inside_board(position)


def resolve_portal(
    position: tuple[int, int], portals: tuple[tuple[int, int], tuple[int, int]] | None
) -> tuple[int, int]:
    """Teleport a position when it lands on one of the portal cells."""
    if portals is None:
        return position

    first, second = portals
    if position == first:
        return second
    if position == second:
        return first
    return position
