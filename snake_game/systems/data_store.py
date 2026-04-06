"""Persistent stats and best score storage."""

from __future__ import annotations

import json
from pathlib import Path

import settings
from entities.snake import Snake


class StatsStore:
    """Loads and saves lightweight player progression data."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings.STATS_FILE
        self.data = self._load()

    def _default_data(self) -> dict:
        return {
            "games_played": 0,
            "total_food_eaten": 0,
            "high_score": 0,
            "best_by_mode": {},
            "mode_games": {},
            "wins": {
                "player_one": 0,
                "player_two": 0,
                "ai": 0,
                "coop_clears": 0,
            },
            "item_usage": {
                "phase": 0,
                "freeze_others": 0,
                "haste": 0,
                "bounce": 0,
                "magnet": 0,
            },
        }

    def _load(self) -> dict:
        if not self.path.exists():
            bundled_path = settings.BUNDLED_DATA_DIR / self.path.name
            if bundled_path.exists():
                try:
                    loaded = json.loads(bundled_path.read_text(encoding="utf-8"))
                    return self._merge_defaults(loaded, self._default_data())
                except (json.JSONDecodeError, OSError):
                    pass
            return self._default_data()

        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            return self._merge_defaults(loaded, self._default_data())
        except (json.JSONDecodeError, OSError):
            return self._default_data()

    def _merge_defaults(self, loaded: dict, default: dict) -> dict:
        merged = dict(default)
        for key, value in loaded.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_defaults(value, merged[key])
            else:
                merged[key] = value
        return merged

    def save(self) -> None:
        settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def record_match(
        self,
        mode_id: str,
        snakes: list[Snake],
        winner_key: str | None,
        team_score: int,
    ) -> None:
        """Persist the outcome of a finished round."""
        self.data["games_played"] += 1
        self.data["total_food_eaten"] += sum(snake.food_eaten for snake in snakes)
        self.data["high_score"] = max(
            self.data["high_score"],
            max((snake.score for snake in snakes), default=0),
            team_score,
        )
        self.data["mode_games"][mode_id] = self.data["mode_games"].get(mode_id, 0) + 1

        mode_scores = self.data["best_by_mode"]
        mode_scores[mode_id] = max(mode_scores.get(mode_id, 0), team_score)

        if winner_key is not None:
            self.data["wins"][winner_key] = self.data["wins"].get(winner_key, 0) + 1

        self.save()

    def record_item_use(self, effect: str | None) -> None:
        """Persist the usage count of a tactical item or power-up."""

        if not effect:
            return
        usage = self.data.setdefault("item_usage", {})
        usage[effect] = usage.get(effect, 0) + 1
        self.save()

    def wins_total(self) -> int:
        """Return the total number of recorded wins or clears."""

        return sum(self.data.get("wins", {}).values())

    def win_rate(self, key: str) -> float:
        """Return a 0.0-1.0 win rate for a specific winner bucket."""

        games_played = max(1, int(self.data.get("games_played", 0)))
        wins = int(self.data.get("wins", {}).get(key, 0))
        return wins / games_played

    def hud_summary(self, mode_id: str, lan_live: dict | None = None) -> dict:
        """Return compact stats for the HUD, including LAN live data when present."""

        item_usage = self.data.get("item_usage", {})
        top_item = max(item_usage.items(), key=lambda item: item[1], default=("none", 0))
        summary = {
            "games_played": self.data.get("games_played", 0),
            "high_score": self.data.get("high_score", 0),
            "food_eaten": self.data.get("total_food_eaten", 0),
            "best_mode": self.data.get("best_by_mode", {}).get(mode_id, 0),
            "win_rates": {
                "player_one": self.win_rate("player_one"),
                "player_two": self.win_rate("player_two"),
                "ai": self.win_rate("ai"),
                "coop_clears": self.win_rate("coop_clears"),
            },
            "item_usage": item_usage,
            "top_item": {"effect": top_item[0], "count": top_item[1]},
            "lan_live": lan_live or {},
        }
        return summary
