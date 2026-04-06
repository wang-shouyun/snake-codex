"""Strategy-mode helpers: skill cards, random events, and AI adjustments."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from systems.game_modes import BaseGameMode, ModeConfig, build_mode_config


@dataclass(slots=True)
class ControlPoint:
    """Represents a strategic tile or region on the board."""

    position: tuple[int, int]
    owner: str | None = None
    score_value: int = 1


@dataclass(frozen=True, slots=True)
class SkillCard:
    """A reusable tactical skill card."""

    card_id: str
    name: str
    cost: int
    description: str
    effect: str


@dataclass(frozen=True, slots=True)
class EventChoice:
    """A branch choice presented by a random event."""

    label: str
    effect: str
    value: int = 0


@dataclass(frozen=True, slots=True)
class StrategyEvent:
    """A random event with one or more branching choices."""

    event_id: str
    title: str
    description: str
    choices: tuple[EventChoice, ...]


@dataclass(slots=True)
class SnakeStrategyState:
    """Per-snake tactical state tracked by the strategy mode."""

    skill_points: int = 0
    hand: list[SkillCard] = field(default_factory=list)
    active_effects: list[str] = field(default_factory=list)
    personality: str = "balanced"


DEFAULT_SKILL_CARDS: tuple[SkillCard, ...] = (
    SkillCard("dash", "Dash", 2, "Move with tempo for one burst turn.", "extra_turn"),
    SkillCard("shield", "Shield", 3, "Ignore one collision risk.", "shield"),
    SkillCard("magnet", "Magnet", 2, "Pull the next food closer.", "food_pull"),
    SkillCard("jammer", "Jammer", 3, "Slow the opponent AI briefly.", "slow_rival"),
)


DEFAULT_EVENTS: tuple[StrategyEvent, ...] = (
    StrategyEvent(
        "resource_cache",
        "Resource Cache",
        "A cache appears. Take points now or save tempo for later.",
        (
            EventChoice("Take 2 skill points", "gain_skill", 2),
            EventChoice("Spawn bonus food", "spawn_food", 1),
        ),
    ),
    StrategyEvent(
        "storm_front",
        "Storm Front",
        "The map becomes unstable for a moment.",
        (
            EventChoice("Clear one obstacle lane", "clear_obstacle", 1),
            EventChoice("Gain shield", "grant_effect", 1),
        ),
    ),
    StrategyEvent(
        "intel_drop",
        "Intel Drop",
        "A tactical read on the board changes the next few moves.",
        (
            EventChoice("Boost aggressive AI", "ai_shift_aggressive", 1),
            EventChoice("Boost safe AI", "ai_shift_safe", 1),
        ),
    ),
)


class StrategyMode(BaseGameMode):
    """Adds tactical progression, branching events, and AI tuning hooks."""

    def __init__(self, config: ModeConfig | None = None) -> None:
        super().__init__(
            config
            or build_mode_config(
                "strategy_mode",
                "Strategy Mode",
                120,
                objective_score=20,
                event_interval_turns=6,
            )
        )
        self.control_points: list[ControlPoint] = []
        self.objective_score = int(self.config.metadata.get("objective_score", 20))
        self.event_interval_turns = max(2, int(self.config.metadata.get("event_interval_turns", 6)))
        self.turn_counter = 0
        self.snake_states: dict[str, SnakeStrategyState] = {}
        self.skill_deck: tuple[SkillCard, ...] = DEFAULT_SKILL_CARDS
        self.event_pool: tuple[StrategyEvent, ...] = DEFAULT_EVENTS
        self.active_event: StrategyEvent | None = None
        self.last_event_message = "No event yet"
        self.last_choice_label = ""
        self.ai_strategy_bias = "balanced"

    def on_enter(self, game: Any) -> None:
        """Initialize tactical state for all active snakes."""

        self.turn_counter = 0
        self.control_points = []
        self.active_event = None
        self.last_event_message = "Strategy mode online"
        self.last_choice_label = ""
        self.ai_strategy_bias = "balanced"
        self.snake_states = {}
        for snake in getattr(game, "snakes", []):
            personality = "aggressive" if getattr(snake, "is_ai", False) else "balanced"
            self.snake_states[snake.name] = SnakeStrategyState(
                skill_points=1,
                hand=self._draw_cards(2),
                personality=personality,
            )

    def update(self, game: Any, delta_ms: int) -> None:
        """Reserved for timed tactical logic."""

    def on_turn_resolved(self, game: Any) -> None:
        """Advance turn count and trigger branch events on cadence."""

        self.turn_counter += 1
        if self.turn_counter % self.event_interval_turns == 0:
            self.trigger_random_event()

    def add_control_point(self, position: tuple[int, int], score_value: int = 1) -> None:
        """Register a new tactical objective on the board."""

        self.control_points.append(ControlPoint(position=position, score_value=score_value))

    def award_skill_points(self, snake_name: str, amount: int, reason: str = "food") -> int:
        """Add skill points when a snake eats food or triggers an item."""

        state = self._state_for(snake_name)
        state.skill_points = max(0, state.skill_points + amount)
        self.last_event_message = f"{snake_name} gained {amount} skill point(s) from {reason}."
        return state.skill_points

    def trigger_item_bonus(self, snake_name: str, bonus_points: int = 1) -> int:
        """Grant skill points from a map pickup or tactical prop."""

        return self.award_skill_points(snake_name, bonus_points, reason="item")

    def use_skill_card(self, snake_name: str, card_id: str) -> bool:
        """Spend points to activate a card if the snake can afford it."""

        state = self._state_for(snake_name)
        for card in state.hand:
            if card.card_id != card_id:
                continue
            if state.skill_points < card.cost:
                self.last_event_message = f"{snake_name} does not have enough skill points."
                return False
            state.skill_points -= card.cost
            state.active_effects.append(card.effect)
            state.hand.remove(card)
            self.last_event_message = f"{snake_name} used {card.name}."
            return True
        self.last_event_message = f"{snake_name} does not have card {card_id}."
        return False

    def trigger_random_event(self) -> StrategyEvent:
        """Pick a random event and make it the active branch event."""

        self.active_event = random.choice(self.event_pool)
        self.last_choice_label = ""
        self.last_event_message = f"{self.active_event.title}: {self.active_event.description}"
        return self.active_event

    def apply_event_choice(self, choice_index: int, snake_name: str | None = None) -> EventChoice:
        """Resolve one branch choice from the current active event."""

        if self.active_event is None:
            raise RuntimeError("No active strategy event to resolve.")

        choice = self.active_event.choices[choice_index]
        target_name = snake_name or self._first_known_snake()
        state = self._state_for(target_name)

        if choice.effect == "gain_skill":
            state.skill_points += choice.value
        elif choice.effect == "spawn_food":
            state.active_effects.append("bonus_food")
        elif choice.effect == "clear_obstacle":
            state.active_effects.append("clear_lane")
        elif choice.effect == "grant_effect":
            state.active_effects.append("shield")
        elif choice.effect == "ai_shift_aggressive":
            self.ai_strategy_bias = "aggressive"
        elif choice.effect == "ai_shift_safe":
            self.ai_strategy_bias = "safe"

        self.last_choice_label = choice.label
        self.last_event_message = f"{self.active_event.title} -> {choice.label}"
        self.active_event = None
        return choice

    def ai_weights_for(self, snake_name: str) -> dict[str, float]:
        """Return tactical AI weights adjusted for the strategy mode."""

        state = self._state_for(snake_name)
        personality = state.personality
        if self.ai_strategy_bias == "aggressive":
            personality = "aggressive"
        elif self.ai_strategy_bias == "safe":
            personality = "safe"

        if personality == "aggressive":
            return {"food": 1.4, "space": 0.8, "risk": 0.6}
        if personality == "safe":
            return {"food": 0.9, "space": 1.5, "risk": 1.4}
        return {"food": 1.0, "space": 1.0, "risk": 1.0}

    def update_ai_personality(self, snake_name: str, personality: str) -> None:
        """Set the local personality for a specific AI snake."""

        self._state_for(snake_name).personality = personality

    def hud_lines(self, snake_name: str | None = None) -> list[str]:
        """Return compact HUD lines for the global event panel."""

        name = snake_name or self._first_known_snake()
        state = self._state_for(name)
        event_line = self.last_event_message
        if self.active_event is not None:
            event_line = f"{self.active_event.title}: {self.active_event.description}"
        return [
            f"Skill {state.skill_points}",
            f"Cards {len(state.hand)}",
            f"AI {self.ai_strategy_bias}",
            event_line,
        ]

    def snake_hud_summary(self, snake_name: str) -> dict[str, Any]:
        """Return per-snake tactical HUD data."""

        state = self._state_for(snake_name)
        return {
            "skill_points": state.skill_points,
            "hand": [card.name for card in state.hand],
            "effects": list(state.active_effects),
            "personality": state.personality,
        }

    def event_choices(self) -> list[str]:
        """Return the labels for the current branch event."""

        if self.active_event is None:
            return []
        return [choice.label for choice in self.active_event.choices]

    def _draw_cards(self, count: int) -> list[SkillCard]:
        if count <= 0:
            return []
        if count >= len(self.skill_deck):
            return list(self.skill_deck)
        return random.sample(list(self.skill_deck), count)

    def _state_for(self, snake_name: str) -> SnakeStrategyState:
        if snake_name not in self.snake_states:
            self.snake_states[snake_name] = SnakeStrategyState(hand=self._draw_cards(2))
        return self.snake_states[snake_name]

    def _first_known_snake(self) -> str:
        if self.snake_states:
            return next(iter(self.snake_states))
        return "Player One"
