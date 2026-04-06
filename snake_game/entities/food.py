"""Food entity."""

from __future__ import annotations

import settings
from utils.helpers import random_grid_position


class Food:
    """Represents a food item with optional special effects."""

    def __init__(self, kind: str = "apple") -> None:
        self.kind = kind
        self.position = (0, 0)
        self.remaining_ms: int | None = None
        self.configure(kind)

    def configure(self, kind: str) -> None:
        """Update food properties from the settings library."""
        self.kind = kind
        spec = settings.FOOD_LIBRARY[kind]
        ttl = spec["ttl"]
        self.remaining_ms = int(ttl) if ttl is not None else None

    def respawn(
        self,
        blocked_positions: set[tuple[int, int]],
        forbidden_positions: set[tuple[int, int]],
    ) -> None:
        """Pick a new grid position that is not occupied."""
        all_blocked = blocked_positions | forbidden_positions
        self.position = random_grid_position(all_blocked)

    def tick(self, delta_ms: int) -> bool:
        """Advance the lifetime timer. Return True when expired."""
        if self.remaining_ms is None:
            return False

        self.remaining_ms -= delta_ms
        return self.remaining_ms <= 0

    @property
    def score_value(self) -> int:
        return int(settings.FOOD_LIBRARY[self.kind]["score"])

    @property
    def growth_value(self) -> int:
        return int(settings.FOOD_LIBRARY[self.kind]["growth"])

    @property
    def effect(self) -> str | None:
        return settings.FOOD_LIBRARY[self.kind]["effect"]

    @property
    def color(self) -> tuple[int, int, int]:
        return settings.FOOD_LIBRARY[self.kind]["color"]

    @property
    def label(self) -> str:
        return settings.FOOD_LIBRARY[self.kind]["label"]
