"""Snake entity."""

from __future__ import annotations


class Snake:
    """Stores snake state, score, and status effects."""

    def __init__(
        self,
        name: str,
        segments: list[tuple[int, int]],
        direction: tuple[int, int],
        colors: dict[str, tuple[int, int, int]],
        controls: dict[int, tuple[int, int]] | None = None,
        is_ai: bool = False,
    ) -> None:
        self.name = name
        self.segments = list(segments)
        self.direction = direction
        self.next_direction = direction
        self.colors = colors
        self.controls = controls or {}
        self.is_ai = is_ai
        self.alive = True
        self.score = 0
        self.food_eaten = 0
        self.phase_ticks = 0
        self.slow_ticks = 0
        self.haste_ticks = 0
        self.bounce_ticks = 0
        self.magnet_ticks = 0
        self.last_path: list[tuple[int, int]] = []
        self.ai_status: dict[str, object] = {}
        self.death_reason = ""

    @property
    def head_position(self) -> tuple[int, int]:
        return self.segments[0]

    def set_direction(self, direction: tuple[int, int]) -> None:
        """Queue a direction change if it is not a direct reverse."""
        if not self.alive:
            return

        opposite = (-self.direction[0], -self.direction[1])
        if len(self.segments) > 1 and direction == opposite:
            return
        self.next_direction = direction

    def preview_next_head(self) -> tuple[int, int]:
        """Return the next position based on the queued direction."""
        dir_x, dir_y = self.next_direction
        head_x, head_y = self.head_position
        return head_x + dir_x, head_y + dir_y

    def apply_movement(self, new_segments: list[tuple[int, int]]) -> None:
        """Commit a precomputed movement result."""
        self.direction = self.next_direction
        self.segments = list(new_segments)

    def grow(self, amount: int = 1) -> None:
        """Increase the snake length after eating food."""
        for _ in range(amount):
            self.segments.append(self.segments[-1])

    def apply_effect(self, effect: str | None) -> None:
        """Activate temporary effects granted by special food."""
        if effect == "phase":
            self.phase_ticks = max(self.phase_ticks, 7)
        elif effect == "haste":
            self.haste_ticks = max(self.haste_ticks, 8)
        elif effect == "bounce":
            self.bounce_ticks = max(self.bounce_ticks, 3)
        elif effect == "magnet":
            self.magnet_ticks = max(self.magnet_ticks, 10)

    def advance_status(self) -> None:
        """Decrease temporary status timers after a turn."""
        if self.phase_ticks > 0:
            self.phase_ticks -= 1
        if self.slow_ticks > 0:
            self.slow_ticks -= 1
        if self.haste_ticks > 0:
            self.haste_ticks -= 1
        if self.bounce_ticks > 0:
            self.bounce_ticks -= 1
        if self.magnet_ticks > 0:
            self.magnet_ticks -= 1

    def can_phase(self) -> bool:
        """Return True when this snake can pass through hazards."""
        return self.phase_ticks > 0

    def has_haste(self) -> bool:
        """Return True when this snake currently has a speed boost."""
        return self.haste_ticks > 0

    def can_bounce(self) -> bool:
        """Return True when this snake can rebound from a wall."""
        return self.bounce_ticks > 0

    def has_magnet(self) -> bool:
        """Return True when this snake can pull nearby food."""
        return self.magnet_ticks > 0
