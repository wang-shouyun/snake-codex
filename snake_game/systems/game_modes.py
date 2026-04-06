"""Shared helpers, mode scaffolding, and difficulty presets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ModeConfig:
    """Configuration shared by a mode instance."""

    mode_id: str
    display_name: str
    default_duration_seconds: int = 60
    allow_ai_demo: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DifficultyProfile:
    """Tunable gameplay values used by the main snake loop."""

    difficulty_id: str
    display_name: str
    move_delay_offset_ms: int
    apple_respawn_delay_ms: int
    special_respawn_delay_ms: int
    special_spawn_chance: float
    extra_obstacle_cells: tuple[tuple[int, int], ...] = ()


DIFFICULTY_PRESETS: dict[str, DifficultyProfile] = {
    "easy": DifficultyProfile(
        difficulty_id="easy",
        display_name="Simple",
        move_delay_offset_ms=45,
        apple_respawn_delay_ms=850,
        special_respawn_delay_ms=2200,
        special_spawn_chance=0.10,
        extra_obstacle_cells=(),
    ),
    "normal": DifficultyProfile(
        difficulty_id="normal",
        display_name="Normal",
        move_delay_offset_ms=0,
        apple_respawn_delay_ms=350,
        special_respawn_delay_ms=1200,
        special_spawn_chance=0.20,
        extra_obstacle_cells=(
            (12, 11),
            (12, 12),
            (12, 13),
            (13, 11),
            (13, 13),
            (13, 14),
        ),
    ),
    "hard": DifficultyProfile(
        difficulty_id="hard",
        display_name="Hard",
        move_delay_offset_ms=-28,
        apple_respawn_delay_ms=50,
        special_respawn_delay_ms=350,
        special_spawn_chance=0.38,
        extra_obstacle_cells=(
            (11, 10),
            (11, 11),
            (11, 12),
            (11, 13),
            (12, 11),
            (12, 12),
            (12, 13),
            (13, 10),
            (13, 11),
            (13, 13),
            (13, 14),
            (14, 12),
            (14, 13),
            (14, 14),
        ),
    ),
}

DEFAULT_DIFFICULTY_ID = "normal"


class BaseGameMode:
    """Common interface for future custom game modes."""

    def __init__(self, config: ModeConfig) -> None:
        self.config = config

    def on_enter(self, game: Any) -> None:
        """Run setup logic when the mode starts."""

    def update(self, game: Any, delta_ms: int) -> None:
        """Update custom mode logic every frame."""

    def on_turn_resolved(self, game: Any) -> None:
        """Hook called after one snake movement step is resolved."""

    def on_exit(self, game: Any) -> None:
        """Clean up mode state before leaving the mode."""


def build_mode_config(
    mode_id: str,
    display_name: str,
    default_duration_seconds: int,
    *,
    allow_ai_demo: bool = True,
    **metadata: Any,
) -> ModeConfig:
    """Convenience helper for creating mode configs."""

    return ModeConfig(
        mode_id=mode_id,
        display_name=display_name,
        default_duration_seconds=default_duration_seconds,
        allow_ai_demo=allow_ai_demo,
        metadata=metadata,
    )


def get_difficulty_profile(difficulty_id: str) -> DifficultyProfile:
    """Return a difficulty profile, falling back to the default profile."""

    return DIFFICULTY_PRESETS.get(difficulty_id, DIFFICULTY_PRESETS[DEFAULT_DIFFICULTY_ID])


def difficulty_ids() -> tuple[str, ...]:
    """Return the stable difficulty order used by the menu."""

    return tuple(DIFFICULTY_PRESETS.keys())
