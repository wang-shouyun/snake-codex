"""Rhythm-driven gameplay helpers for a beat-synced snake mode."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pygame

import settings
from systems.game_modes import BaseGameMode, ModeConfig, build_mode_config

SUPPORTED_AUDIO_SUFFIXES = (".ogg", ".mp3", ".wav")


@dataclass(slots=True)
class RhythmWindow:
    """Timing windows used to score beat accuracy."""

    perfect_ms: int = 90
    good_ms: int = 180
    miss_ms: int = 300


@dataclass(slots=True)
class BeatHudState:
    """Simple payload for HUD rendering."""

    beat_index: int
    beat_in_bar: int
    bars_completed: int
    combo: int
    streak_best: int
    accuracy_label: str


class RhythmMode(BaseGameMode):
    """Beat-synced helper for movement, food refresh, combo, and music playback."""

    def __init__(self, config: ModeConfig | None = None) -> None:
        super().__init__(
            config
            or build_mode_config(
                "rhythm_mode",
                "Rhythm Mode",
                90,
                bpm=110,
                beats_per_bar=4,
                food_refresh_every_beats=2,
                autoplay_music=True,
            )
        )
        self.timing = RhythmWindow()
        self.music_dir = settings.ROOT_DIR / "assets" / "music"
        self.bpm = max(40, int(self.config.metadata.get("bpm", 110)))
        self.beats_per_bar = max(1, int(self.config.metadata.get("beats_per_bar", 4)))
        self.food_refresh_every_beats = max(
            1,
            int(self.config.metadata.get("food_refresh_every_beats", 2)),
        )
        self.autoplay_music = bool(self.config.metadata.get("autoplay_music", True))
        self.beat_interval_ms = int(round(60000 / self.bpm))
        self.elapsed_since_beat = 0
        self.total_beats = 0
        self.pending_move_beats = 0
        self.pending_food_beats = 0
        self.combo = 0
        self.best_combo = 0
        self.last_accuracy_label = "Ready"
        self.active_track: Path | None = None

    def on_enter(self, game: Any) -> None:
        """Reset beat state and optionally start the first music track."""

        self.elapsed_since_beat = 0
        self.total_beats = 0
        self.pending_move_beats = 0
        self.pending_food_beats = 0
        self.combo = 0
        self.best_combo = 0
        self.last_accuracy_label = "Ready"

        if self.autoplay_music:
            tracks = self.available_tracks()
            if tracks:
                self.load_track(tracks[0], autoplay=True)

    def update(self, game: Any, delta_ms: int) -> None:
        """Advance the beat clock and queue synced movement / food events."""

        if self.beat_interval_ms <= 0:
            return

        self.elapsed_since_beat += delta_ms
        while self.elapsed_since_beat >= self.beat_interval_ms:
            self.elapsed_since_beat -= self.beat_interval_ms
            self.total_beats += 1
            self.pending_move_beats += 1
            if self.total_beats % self.food_refresh_every_beats == 0:
                self.pending_food_beats += 1

    def on_turn_resolved(self, game: Any) -> None:
        """Mark one queued beat movement as consumed."""

        if self.pending_move_beats > 0:
            self.pending_move_beats -= 1

    def on_exit(self, game: Any) -> None:
        """Stop playback when leaving the rhythm mode."""

        if pygame.mixer.get_init():
            pygame.mixer.music.stop()

    def should_move_this_beat(self) -> bool:
        """Return True when the snake is allowed to advance on the current beat."""

        return self.pending_move_beats > 0

    def should_refresh_food(self) -> bool:
        """Return True when a beat-triggered food refresh is pending."""

        return self.pending_food_beats > 0

    def consume_food_refresh(self) -> None:
        """Mark one queued food refresh event as consumed."""

        if self.pending_food_beats > 0:
            self.pending_food_beats -= 1

    def register_food_capture(self) -> str:
        """Score beat accuracy for a food capture and update combo state."""

        distance = self.distance_to_nearest_beat()
        if distance <= self.timing.perfect_ms:
            self.combo += 1
            self.best_combo = max(self.best_combo, self.combo)
            self.last_accuracy_label = "Perfect"
        elif distance <= self.timing.good_ms:
            self.combo += 1
            self.best_combo = max(self.best_combo, self.combo)
            self.last_accuracy_label = "Good"
        else:
            self.combo = 0
            self.last_accuracy_label = "Miss"
        return self.last_accuracy_label

    def register_missed_beat(self) -> None:
        """Break combo when the player misses a beat-sensitive action."""

        self.combo = 0
        self.last_accuracy_label = "Miss"

    def distance_to_nearest_beat(self) -> int:
        """Return the nearest timing distance in milliseconds."""

        forward = self.elapsed_since_beat
        backward = self.beat_interval_ms - self.elapsed_since_beat
        return int(min(forward, backward))

    def beat_progress(self) -> float:
        """Return current beat progress in the 0.0 to 1.0 range."""

        if self.beat_interval_ms <= 0:
            return 0.0
        return self.elapsed_since_beat / self.beat_interval_ms

    def hud_state(self) -> BeatHudState:
        """Return current beat and combo information for HUD rendering."""

        beat_in_bar = (self.total_beats % self.beats_per_bar) + 1
        bars_completed = self.total_beats // self.beats_per_bar
        return BeatHudState(
            beat_index=self.total_beats + 1,
            beat_in_bar=beat_in_bar,
            bars_completed=bars_completed,
            combo=self.combo,
            streak_best=self.best_combo,
            accuracy_label=self.last_accuracy_label,
        )

    def hud_lines(self) -> list[str]:
        """Return compact HUD strings for existing sidebars."""

        state = self.hud_state()
        return [
            f"Beat {state.beat_in_bar}/{self.beats_per_bar}",
            f"Combo x{state.combo}",
            f"Best x{state.streak_best}",
            state.accuracy_label,
        ]

    def available_tracks(self) -> list[Path]:
        """Return supported audio files from assets/music/."""

        if not self.music_dir.exists():
            return []
        return sorted(
            path
            for path in self.music_dir.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_SUFFIXES
        )

    def load_track(self, track: str | Path, autoplay: bool = False) -> Path:
        """Load a music file from assets/music/ and optionally start playback."""

        track_path = Path(track)
        if not track_path.is_absolute():
            track_path = self.music_dir / track_path
        if not track_path.exists():
            raise FileNotFoundError(f"Music file not found: {track_path}")
        if track_path.suffix.lower() not in SUPPORTED_AUDIO_SUFFIXES:
            raise ValueError(f"Unsupported music format: {track_path.suffix}")

        self._ensure_mixer()
        pygame.mixer.music.load(track_path.as_posix())
        self.active_track = track_path
        if autoplay:
            pygame.mixer.music.play(-1)
        return track_path

    def music_summary(self) -> dict[str, Any]:
        """Return a compact summary for menus or debugging tools."""

        tracks = self.available_tracks()
        return {
            "music_dir": str(self.music_dir),
            "track_count": len(tracks),
            "tracks": [track.name for track in tracks],
            "active_track": self.active_track.name if self.active_track else None,
            "bpm": self.bpm,
            "beat_interval_ms": self.beat_interval_ms,
        }

    def _ensure_mixer(self) -> None:
        """Initialize pygame.mixer on demand."""

        if pygame.mixer.get_init():
            return
        pygame.mixer.init()
