"""Main game controller."""

from __future__ import annotations

import random

import pygame

import settings
from entities.food import Food
from entities.snake import Snake
from systems.ai_controller import SnakeAI
from systems.collision import out_of_bounds, resolve_portal
from systems.data_store import StatsStore
from systems.input_handler import (
    CONFIRM_KEYS,
    MENU_DOWN_KEYS,
    MENU_UP_KEYS,
    PLAYER_ONE_KEYS,
    PLAYER_TWO_KEYS,
    direction_for_key,
)
from systems.localization import Localizer
from systems.game_modes import (
    DEFAULT_DIFFICULTY_ID,
    difficulty_ids,
    get_difficulty_profile,
)
from systems.network_session import (
    ClientSession,
    DiscoveryBrowser,
    HostSession,
    local_ip_address,
)
from systems.renderer import Renderer
from systems.rhythm_mode import RhythmMode
from systems.strategy_mode import StrategyMode
from utils.helpers import manhattan_distance, weighted_choice


class SnakeGame:
    """Owns the game loop and high-level state transitions."""

    def __init__(self) -> None:
        self.screen = pygame.display.set_mode(
            (settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT)
        )
        pygame.display.set_caption(settings.WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.renderer = Renderer(self.screen)
        self.ai = SnakeAI()
        self.stats_store = StatsStore()
        self.localizer = Localizer("zh")
        self.rhythm_mode = None
        self.strategy_mode = None
        self.is_running = True
        self.menu_index = 0
        self.setup_index = 0
        self.setup_action = "play"
        self.setup_duration = [0, 1, 0]
        self.difficulty_order = list(difficulty_ids())
        self.difficulty_index = self.difficulty_order.index(DEFAULT_DIFFICULTY_ID)
        self.current_difficulty_id = self.difficulty_order[self.difficulty_index]
        self.difficulty_profile = get_difficulty_profile(self.current_difficulty_id)
        self.language_index = settings.SUPPORTED_LANGUAGES.index(self.localizer.language)
        self.current_mode_id = settings.MODE_DEFINITIONS[0]["id"]
        self.show_ai_paths = True
        self.menu_message = self.t("msg_choose_mode")
        self.network_role: str | None = None
        self.network_session: HostSession | ClientSession | None = None
        self.discovery_browser: DiscoveryBrowser | None = None
        self.host_ip = local_ip_address()
        self.room_code = ""
        self.join_ip_text = self.host_ip
        self.discovered_rooms: list[dict] = []
        self.discovery_index = 0
        self.snapshot_view: dict = {}
        self.state = "language_select"
        self.result_title = ""
        self.result_lines = []
        self.result_actions = []
        self.result_action_index = 0
        self.round_message = self.t("startup_subtitle")
        now = pygame.time.get_ticks()
        self.last_move_time = now
        self.last_update_time = now

    def t(self, key: str, **kwargs) -> str:
        return self.localizer.t(key, **kwargs)

    def _food_name(self, kind: str) -> str:
        key = f"food_{kind}"
        value = self.t(key)
        return value if value != key else kind

    def _can_toggle_pause(self) -> bool:
        return self.state in {"playing", "paused"} and self.network_role != "client"

    def _toggle_pause(self) -> None:
        self.state = "paused" if self.state == "playing" else "playing"
        now = pygame.time.get_ticks()
        self.last_update_time = now
        self.last_move_time = now
        self.round_message = (
            self.t("msg_paused") if self.state == "paused" else self.t("msg_resume")
        )

    def _can_interrupt_current_view(self) -> bool:
        return self.state not in {"language_select", "menu"}

    def _handle_global_shortcuts(self, key: int) -> bool:
        if key == pygame.K_p and self._can_toggle_pause():
            self._toggle_pause()
            return True

        if not self._can_interrupt_current_view():
            return False

        if key == pygame.K_r:
            self.start_mode(self.current_mode_id)
            return True

        if key in {pygame.K_m, pygame.K_ESCAPE}:
            self.enter_menu()
            return True

        return False

    def _resolve_mode_info(self, mode_id: str) -> dict:
        for mode in settings.MODE_DEFINITIONS:
            if mode["id"] == mode_id:
                return mode
        if mode_id == "lan_duel":
            return {
                "id": "lan_duel",
                "label": "LAN Duel",
                "description": "Remote local-area duel with host-authoritative state sync.",
                "humans": 2,
                "ais": 0,
                "hazards": True,
                "coop": False,
                "category": "hidden",
                "default_duration": (0, 2, 0),
            }
        raise KeyError(f"Unknown mode: {mode_id}")

    def enter_menu(self) -> None:
        """Return to the main menu."""
        self._close_network()
        self._close_discovery()
        self.state = "menu"
        self.network_role = None
        self.result_title = ""
        self.result_lines: list[str] = []
        self.result_actions = []
        self.result_action_index = 0
        self.menu_message = self.t("msg_choose_mode")
        self.round_message = self.menu_message
        self.snapshot_view = {}
        self.difficulty_profile = get_difficulty_profile(self.current_difficulty_id)

    def start_mode(self, mode_id: str) -> None:
        """Create a fresh round for the selected mode."""
        self.current_mode_id = mode_id
        self.mode_info = self._resolve_mode_info(mode_id)

        if self.mode_info["category"] in {"mode", "network_host"}:
            self._open_mode_setup(mode_id)
            return
        if self.mode_info["category"] == "network_join":
            self._open_join_prompt()
            return

        self._setup_local_match(mode_id)

    def _open_mode_setup(self, mode_id: str) -> None:
        self.current_mode_id = mode_id
        self.mode_info = self._resolve_mode_info(mode_id)
        self.setup_action = "play"
        default_duration = self.mode_info.get("default_duration", (0, 1, 0))
        self.setup_duration = [default_duration[0], default_duration[1], default_duration[2]]
        self.setup_index = 0
        self.state = "mode_setup"
        self.round_message = self.t("setup_guide_title")

    def _setup_local_match(self, mode_id: str, networked: bool = False, demo: bool = False) -> None:
        self.network_role = "host" if networked else None
        self.mode_info = self._resolve_mode_info(mode_id)
        self.current_mode_id = mode_id
        self.rhythm_mode = None
        self.strategy_mode = None
        self.snakes = self._build_snakes(mode_id, demo=demo)
        self.obstacles = self._build_obstacles(mode_id)
        self.portals = self._build_portals(mode_id)
        self.foods: list[Food] = []
        self.tick_count = 0
        now = pygame.time.get_ticks()
        self.last_move_time = now
        self.last_update_time = now
        self.difficulty_profile = get_difficulty_profile(self.current_difficulty_id)
        self.pending_apple_spawn_ms = 0
        self.pending_special_spawn_ms = 0
        self.obstacle_level = 0
        hours, minutes, seconds = self.setup_duration
        duration_seconds = hours * 3600 + minutes * 60 + seconds
        if duration_seconds <= 0:
            duration_seconds = 60
        self.time_remaining_ms = int(duration_seconds * 1000)
        self.demo_enabled = demo
        self.round_message = self.t("msg_collect")
        self.state = "playing"
        if mode_id == "rhythm_mode":
            self.rhythm_mode = RhythmMode()
            self.rhythm_mode.on_enter(self)
        elif mode_id == "strategy_mode":
            self.strategy_mode = StrategyMode()
            self.strategy_mode.on_enter(self)
        self._spawn_food("apple")
        self._maybe_spawn_special_food(force=True)

    def _open_host_wait(self) -> None:
        self._close_network()
        try:
            self.network_session = HostSession(self.host_ip)
            self.room_code = self.network_session.room_code
            self.network_role = "host"
            self.state = "network_wait_host"
            self.network_session.update_live_status(
                players=1,
                host_score=0,
                remote_score=0,
                mode_id="lan_duel",
                winner="",
            )
            self.round_message = self.t(
                "msg_hosting", ip=self.host_ip, port=settings.NETWORK_PORT
            )
        except OSError as exc:
            self.state = "menu"
            self.round_message = self.t("msg_host_failed", error=exc)

    def _open_join_prompt(self) -> None:
        self._close_network()
        self.network_role = "client"
        self.state = "network_join_input"
        self.discovery_index = 0
        self._open_discovery()
        self.round_message = self.t("msg_join_input")

    def _connect_to_host(self) -> None:
        self._close_network()
        self._close_discovery()
        try:
            self.network_session = ClientSession(self.join_ip_text.strip())
            self.network_role = "client"
            self.state = "network_client_playing"
            self.round_message = self.t("msg_connected_wait")
            self.snapshot_view = {}
        except OSError as exc:
            self.state = "network_join_input"
            self._open_discovery()
            self.round_message = self.t("msg_connect_failed", error=exc)

    def _close_network(self) -> None:
        if self.network_session is not None:
            self.network_session.close()
        self.network_session = None

    def _open_discovery(self) -> None:
        self._close_discovery()
        try:
            self.discovery_browser = DiscoveryBrowser()
        except OSError:
            self.discovery_browser = None

    def _close_discovery(self) -> None:
        if self.discovery_browser is not None:
            self.discovery_browser.close()
        self.discovery_browser = None
        self.discovered_rooms = []

    def _build_snakes(self, mode_id: str, demo: bool = False) -> list[Snake]:
        if mode_id == "timed_solo":
            return [
                Snake(
                    "Player One",
                    [(6, 13), (5, 13), (4, 13)],
                    (1, 0),
                    settings.AI_COLORS if demo else settings.PLAYER_ONE_COLORS,
                    PLAYER_ONE_KEYS,
                    is_ai=demo,
                )
            ]
        if mode_id == "versus_ai":
            return [
                Snake(
                    "Player One",
                    [(5, 10), (4, 10), (3, 10)],
                    (1, 0),
                    settings.AI_COLORS if demo else settings.PLAYER_ONE_COLORS,
                    PLAYER_ONE_KEYS,
                    is_ai=demo,
                ),
                Snake(
                    "AI Rival",
                    [(20, 15), (21, 15), (22, 15)],
                    (-1, 0),
                    settings.AI_COLORS,
                    is_ai=True,
                ),
            ]
        if mode_id in {"local_duel", "lan_duel"}:
            return [
                Snake(
                    "Player One",
                    [(5, 10), (4, 10), (3, 10)],
                    (1, 0),
                    settings.AI_COLORS if demo else settings.PLAYER_ONE_COLORS,
                    PLAYER_ONE_KEYS,
                    is_ai=demo,
                ),
                Snake(
                    "Player Two",
                    [(20, 15), (21, 15), (22, 15)],
                    (-1, 0),
                    settings.AI_COLORS if demo else settings.PLAYER_TWO_COLORS,
                    PLAYER_TWO_KEYS,
                    is_ai=demo,
                ),
            ]
        return [
            Snake(
                "Player One",
                [(5, 9), (4, 9), (3, 9)],
                (1, 0),
                settings.AI_COLORS if demo else settings.PLAYER_ONE_COLORS,
                PLAYER_ONE_KEYS,
                is_ai=demo,
            ),
            Snake(
                "Player Two",
                [(20, 16), (21, 16), (22, 16)],
                (-1, 0),
                settings.AI_COLORS if demo else settings.PLAYER_TWO_COLORS,
                PLAYER_TWO_KEYS,
                is_ai=demo,
            ),
        ]

    def _build_obstacles(self, mode_id: str) -> set[tuple[int, int]]:
        return set(self.difficulty_profile.extra_obstacle_cells)

    def _build_portals(
        self, mode_id: str
    ) -> tuple[tuple[int, int], tuple[int, int]] | None:
        if mode_id in {"local_duel", "lan_duel"}:
            return ((2, 13), (23, 13))
        return ((3, 4), (22, 21))

    def _blocked_positions(self) -> set[tuple[int, int]]:
        blocked = set(self.obstacles)
        for snake in self.snakes:
            if snake.alive:
                blocked.update(snake.segments)
        for food in self.foods:
            blocked.add(food.position)
        return blocked

    def _forbidden_positions(self) -> set[tuple[int, int]]:
        if self.portals is None:
            return set()
        return set(self.portals)

    def _spawn_food(self, kind: str) -> None:
        food = Food(kind)
        food.respawn(self._blocked_positions(), self._forbidden_positions())
        self.foods.append(food)

    def _maybe_spawn_special_food(self, force: bool = False) -> None:
        special_exists = any(food.kind != "apple" for food in self.foods)
        if special_exists:
            return

        if not force and random.random() > self.difficulty_profile.special_spawn_chance:
            return

        kind = weighted_choice(
            [
                (name, spec["weight"])
                for name, spec in settings.FOOD_LIBRARY.items()
                if name != "apple"
            ]
        )
        self._spawn_food(kind)

    def _move_delay(self) -> int:
        longest = max((len(snake.segments) for snake in getattr(self, "snakes", [])), default=3)
        delay = (
            settings.BASE_MOVE_DELAY
            + self.difficulty_profile.move_delay_offset_ms
            - max(0, longest - 3) * 4
        )
        if any(snake.alive and snake.has_haste() for snake in getattr(self, "snakes", [])):
            delay -= 22
        return max(settings.MIN_MOVE_DELAY, delay)

    def run(self) -> None:
        """Start the main loop."""
        while self.is_running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(settings.FPS)

    def handle_events(self) -> None:
        """Handle window and keyboard events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
                self._close_network()
                return

            if event.type != pygame.KEYDOWN:
                if self.state == "network_join_input":
                    self._handle_join_text_input(event)
                continue

            if self._handle_global_shortcuts(event.key):
                continue

            if self.state == "network_join_input":
                self._handle_join_text_input(event)
                continue

            if self.state == "language_select":
                self._handle_language_input(event.key)
                continue
            if self.state == "mode_setup":
                self._handle_setup_input(event.key)
                continue

            if event.key == pygame.K_TAB and self.state not in {
                "network_wait_host",
                "network_client_playing",
            }:
                self.show_ai_paths = not self.show_ai_paths
                continue

            if self.state == "menu":
                self._handle_menu_input(event.key)
                continue

            if self.state == "network_wait_host":
                if event.key == pygame.K_r:
                    self._open_host_wait()
                continue

            if self.state == "network_client_playing":
                self._handle_client_input(event.key)
                continue

            if self.state == "game_over":
                if event.key in MENU_UP_KEYS or event.key in {pygame.K_LEFT, pygame.K_a}:
                    self.result_action_index = (self.result_action_index - 1) % max(1, len(self.result_actions))
                elif event.key in MENU_DOWN_KEYS or event.key in {pygame.K_RIGHT, pygame.K_d}:
                    self.result_action_index = (self.result_action_index + 1) % max(1, len(self.result_actions))
                elif event.key in CONFIRM_KEYS:
                    self._handle_result_action()
                continue

            if self.state == "playing":
                self._handle_player_input(event.key)

    def _handle_join_text_input(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.enter_menu()
            return
        if event.key in {pygame.K_UP, pygame.K_w} and self.discovered_rooms:
            self.discovery_index = (self.discovery_index - 1) % len(self.discovered_rooms)
            self.join_ip_text = self.discovered_rooms[self.discovery_index]["host_ip"]
            return
        if event.key in {pygame.K_DOWN, pygame.K_s} and self.discovered_rooms:
            self.discovery_index = (self.discovery_index + 1) % len(self.discovered_rooms)
            self.join_ip_text = self.discovered_rooms[self.discovery_index]["host_ip"]
            return
        if event.key == pygame.K_TAB and self.discovered_rooms:
            self.join_ip_text = self.discovered_rooms[self.discovery_index]["host_ip"]
            return
        if event.key == pygame.K_RETURN:
            self._connect_to_host()
            return
        if event.key == pygame.K_BACKSPACE:
            self.join_ip_text = self.join_ip_text[:-1]
            return

        if event.unicode and event.unicode in "0123456789.:":
            self.join_ip_text += event.unicode

    def _handle_language_input(self, key: int) -> None:
        if key in {pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w}:
            self.language_index = (self.language_index - 1) % len(settings.SUPPORTED_LANGUAGES)
        elif key in {pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s}:
            self.language_index = (self.language_index + 1) % len(settings.SUPPORTED_LANGUAGES)
        elif key in CONFIRM_KEYS:
            language = settings.SUPPORTED_LANGUAGES[self.language_index]
            self.localizer.set_language(language)
            self.enter_menu()
            return

        language = settings.SUPPORTED_LANGUAGES[self.language_index]
        self.localizer.set_language(language)
        self.round_message = self.t("startup_subtitle")

    def _handle_menu_input(self, key: int) -> None:
        if key in MENU_UP_KEYS:
            self.menu_index = (self.menu_index - 1) % len(settings.MODE_DEFINITIONS)
        elif key in MENU_DOWN_KEYS:
            self.menu_index = (self.menu_index + 1) % len(settings.MODE_DEFINITIONS)
        elif key in {pygame.K_LEFT, pygame.K_a}:
            self.difficulty_index = (self.difficulty_index - 1) % len(self.difficulty_order)
            self.current_difficulty_id = self.difficulty_order[self.difficulty_index]
            self.difficulty_profile = get_difficulty_profile(self.current_difficulty_id)
        elif key in {pygame.K_RIGHT, pygame.K_d}:
            self.difficulty_index = (self.difficulty_index + 1) % len(self.difficulty_order)
            self.current_difficulty_id = self.difficulty_order[self.difficulty_index]
            self.difficulty_profile = get_difficulty_profile(self.current_difficulty_id)
        elif key in CONFIRM_KEYS:
            selected_mode = settings.MODE_DEFINITIONS[self.menu_index]["id"]
            self.start_mode(selected_mode)

    def _handle_setup_input(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            self.enter_menu()
            return
        fields = ["action", "hours", "minutes", "seconds", "confirm"]
        if key in MENU_UP_KEYS:
            self.setup_index = (self.setup_index - 1) % len(fields)
            return
        if key in MENU_DOWN_KEYS:
            self.setup_index = (self.setup_index + 1) % len(fields)
            return
        current = fields[self.setup_index]
        if current == "action" and key in {pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d}:
            self.setup_action = "demo" if self.setup_action == "play" else "play"
            return
        if current in {"hours", "minutes", "seconds"}:
            index_map = {"hours": 0, "minutes": 1, "seconds": 2}
            idx = index_map[current]
            max_value = 23 if current == "hours" else 59
            if key in {pygame.K_LEFT, pygame.K_a}:
                self.setup_duration[idx] = (self.setup_duration[idx] - 1) % (max_value + 1)
                return
            if key in {pygame.K_RIGHT, pygame.K_d}:
                self.setup_duration[idx] = (self.setup_duration[idx] + 1) % (max_value + 1)
                return
        if key in CONFIRM_KEYS:
            if current == "confirm":
                demo = self.setup_action == "demo"
                if self.current_mode_id == "lan_host":
                    if demo:
                        self._setup_local_match("local_duel", demo=True)
                    else:
                        self._open_host_wait()
                else:
                    self._setup_local_match(self.current_mode_id, demo=demo)
            elif current == "action":
                self.setup_action = "demo" if self.setup_action == "play" else "play"

    def _handle_player_input(self, key: int) -> None:
        for snake in self.snakes:
            if snake.is_ai or not snake.alive:
                continue
            direction = direction_for_key(key, snake.controls)
            if direction is not None:
                snake.set_direction(direction)

    def _handle_client_input(self, key: int) -> None:
        if not isinstance(self.network_session, ClientSession):
            return
        direction = direction_for_key(key, PLAYER_ONE_KEYS)
        if direction is not None:
            self.network_session.send_direction(direction)

    def update(self) -> None:
        """Advance the game while in the active state."""
        current_time = pygame.time.get_ticks()
        self._update_network()

        if self.state != "playing":
            self.last_update_time = current_time
            return

        delta_ms = current_time - self.last_update_time
        self.last_update_time = current_time

        if self.rhythm_mode is not None:
            self.rhythm_mode.update(self, delta_ms)
        if self.strategy_mode is not None:
            self.strategy_mode.update(self, delta_ms)

        if self.time_remaining_ms is not None:
            self.time_remaining_ms = max(0, self.time_remaining_ms - delta_ms)
            if self.time_remaining_ms == 0:
                team_score = sum(snake.score for snake in self.snakes)
                self._finish_round(
                    self.t("game_over"),
                    [
                        self.t("game_over_score", score=team_score),
                        self.t("retry_hint"),
                        self.t("menu_hint"),
                    ],
                    None,
                    team_score,
                )
                return
        self._update_food_timers(delta_ms)
        self._update_spawn_timers(delta_ms)

        if self.rhythm_mode is not None:
            if not self.rhythm_mode.should_move_this_beat():
                return
        else:
            elapsed = current_time - self.last_move_time
            if elapsed < self._move_delay():
                return
            self.last_move_time = current_time

        self.last_move_time = current_time
        self.tick_count += 1
        self._update_ai()
        self._advance_turn()
        self._ensure_foods()
        self._update_dynamic_hazards()
        self._check_end_conditions()
        self._broadcast_snapshot_if_needed()

    def _update_network(self) -> None:
        if self.network_session is None:
            if self.state == "network_join_input" and self.discovery_browser is not None:
                self.discovered_rooms = self.discovery_browser.poll()
                if self.discovered_rooms:
                    self.discovery_index %= len(self.discovered_rooms)
            return

        if isinstance(self.network_session, HostSession):
            messages = self.network_session.poll()
            if not self.network_session.connected:
                if self.state == "network_wait_host":
                    return
                self.round_message = self.t("msg_remote_lost")
                self.enter_menu()
                return

            if self.state == "network_wait_host":
                self.current_mode_id = "lan_duel"
                self._setup_local_match("lan_duel", networked=True)
                self.round_message = self.t("msg_remote_joined")
                self.network_session.update_live_status(players=2, mode_id="lan_duel")
                self._broadcast_snapshot_if_needed()

            for message in messages:
                if message.get("type") == "input":
                    direction_list = message.get("direction", [])
                    if len(direction_list) == 2 and len(self.snakes) > 1:
                        self.snakes[1].set_direction((direction_list[0], direction_list[1]))
            return

        if isinstance(self.network_session, ClientSession):
            messages = self.network_session.poll()
            if not self.network_session.connected:
                self.round_message = self.t("msg_disconnected")
                return

            for message in messages:
                if message.get("type") == "snapshot":
                    self.snapshot_view = message.get("payload", {})
                    self.round_message = self.snapshot_view.get("round_message", self.round_message)
                    snapshot_difficulty = self.snapshot_view.get("difficulty_id")
                    if snapshot_difficulty in self.difficulty_order:
                        self.current_difficulty_id = snapshot_difficulty
                        self.difficulty_index = self.difficulty_order.index(snapshot_difficulty)
                        self.difficulty_profile = get_difficulty_profile(snapshot_difficulty)

    def _update_ai(self) -> None:
        for snake in self.snakes:
            if snake.is_ai and snake.alive:
                strategy_weights = None
                if self.strategy_mode is not None:
                    strategy_weights = self.strategy_mode.ai_weights_for(snake.name)
                direction = self.ai.choose_direction(
                    snake,
                    self.snakes,
                    self.foods,
                    self.obstacles,
                    self.portals,
                    strategy_weights=strategy_weights,
                )
                snake.set_direction(direction)

    def _advance_turn(self) -> None:
        active_snakes = [snake for snake in self.snakes if snake.alive]
        planned_segments: dict[str, list[tuple[int, int]]] = {}
        planned_heads: dict[str, tuple[int, int]] = {}
        skipped_names: set[str] = set()
        death_reasons: dict[str, str] = {}

        for snake in active_snakes:
            if snake.slow_ticks > 0 and self.tick_count % 2 == 0:
                planned_segments[snake.name] = list(snake.segments)
                planned_heads[snake.name] = snake.head_position
                skipped_names.add(snake.name)
                continue

            next_head = snake.preview_next_head()
            if out_of_bounds(next_head) and snake.can_bounce():
                bounced_direction = (-snake.next_direction[0], -snake.next_direction[1])
                snake.next_direction = bounced_direction
                next_head = (
                    snake.head_position[0] + bounced_direction[0],
                    snake.head_position[1] + bounced_direction[1],
                )
                self.round_message = self.t("msg_bounce_used", name=snake.name)
            next_head = resolve_portal(next_head, self.portals)
            planned_heads[snake.name] = next_head
            planned_segments[snake.name] = [next_head] + snake.segments[:-1]

        dead_names: set[str] = set()
        head_counts: dict[tuple[int, int], int] = {}
        for head in planned_heads.values():
            head_counts[head] = head_counts.get(head, 0) + 1

        for snake in active_snakes:
            head = planned_heads[snake.name]
            if head_counts[head] > 1:
                dead_names.add(snake.name)
                death_reasons[snake.name] = self.t("reason_head_on")
                continue
            if out_of_bounds(head):
                dead_names.add(snake.name)
                death_reasons[snake.name] = self.t("reason_wall")
                continue
            if head in self.obstacles and not snake.can_phase():
                dead_names.add(snake.name)
                death_reasons[snake.name] = self.t("reason_obstacle")

        for snake in active_snakes:
            if snake.name in dead_names or snake.can_phase():
                continue

            head = planned_heads[snake.name]
            own_segments = planned_segments[snake.name]
            if head in own_segments[1:]:
                dead_names.add(snake.name)
                death_reasons[snake.name] = self.t("reason_self")
                continue

            for other in active_snakes:
                if other is snake:
                    continue
                if head in planned_segments[other.name]:
                    dead_names.add(snake.name)
                    death_reasons[snake.name] = self.t("reason_other", name=other.name)
                    break

        for snake in active_snakes:
            if snake.name in dead_names:
                snake.alive = False
                snake.death_reason = death_reasons.get(snake.name, "")
                continue
            if snake.name not in skipped_names:
                snake.apply_movement(planned_segments[snake.name])
            snake.advance_status()

        if self.rhythm_mode is not None:
            self.rhythm_mode.on_turn_resolved(self)
        if self.strategy_mode is not None:
            self.strategy_mode.on_turn_resolved(self)
        self._resolve_food_collection()

    def _resolve_food_collection(self) -> None:
        consumed_foods: list[Food] = []

        for food in self.foods:
            eaters = [
                snake
                for snake in self.snakes
                if snake.alive
                and (
                    snake.head_position == food.position
                    or (snake.has_magnet() and manhattan_distance(snake.head_position, food.position) <= 2)
                )
            ]
            if not eaters:
                continue

            consumed_foods.append(food)
            for snake in eaters:
                snake.score += food.score_value
                snake.food_eaten += 1
                snake.grow(food.growth_value)
                snake.apply_effect(food.effect)
                if self.strategy_mode is not None:
                    self.strategy_mode.award_skill_points(snake.name, 1, reason="food")
                if self.rhythm_mode is not None:
                    self.rhythm_mode.register_food_capture()
                self.stats_store.record_item_use(food.effect)
                if food.effect == "freeze_others":
                    for other in self.snakes:
                        if other is not snake and other.alive:
                            other.slow_ticks = max(other.slow_ticks, 6)
                    self.round_message = self.t("msg_freeze_used", name=snake.name)
                elif food.effect == "haste":
                    self.round_message = self.t("msg_haste_used", name=snake.name)
                elif food.effect == "bounce":
                    self.round_message = self.t("msg_bounce_ready", name=snake.name)
                elif food.effect == "magnet":
                    self.round_message = self.t("msg_magnet_used", name=snake.name)
                elif snake.head_position != food.position and snake.has_magnet():
                    self.round_message = self.t(
                        "msg_magnet_pull", name=snake.name, food=self._food_name(food.kind)
                    )
                else:
                    self.round_message = self.t(
                        "msg_food_captured", name=snake.name, food=self._food_name(food.kind)
                    )

        for food in consumed_foods:
            self.foods.remove(food)
            if food.kind == "apple":
                self.pending_apple_spawn_ms = self.difficulty_profile.apple_respawn_delay_ms
            else:
                self.pending_special_spawn_ms = self.difficulty_profile.special_respawn_delay_ms

    def _update_food_timers(self, elapsed: int) -> None:
        expired_foods = [food for food in self.foods if food.tick(elapsed)]
        for food in expired_foods:
            self.foods.remove(food)
            if food.kind == "apple":
                self.pending_apple_spawn_ms = self.difficulty_profile.apple_respawn_delay_ms
            else:
                self.pending_special_spawn_ms = self.difficulty_profile.special_respawn_delay_ms
            self.round_message = self.t("msg_food_vanished", food=self._food_name(food.kind))

    def _update_spawn_timers(self, delta_ms: int) -> None:
        self.pending_apple_spawn_ms = max(0, self.pending_apple_spawn_ms - delta_ms)
        self.pending_special_spawn_ms = max(0, self.pending_special_spawn_ms - delta_ms)

    def _ensure_foods(self) -> None:
        if self.rhythm_mode is not None:
            if not self.rhythm_mode.should_refresh_food():
                return
            spawned = False
            if (
                not any(food.kind == "apple" for food in self.foods)
                and self.pending_apple_spawn_ms == 0
            ):
                self._spawn_food("apple")
                spawned = True
            if self.pending_special_spawn_ms == 0:
                before_count = len(self.foods)
                self._maybe_spawn_special_food()
                spawned = spawned or len(self.foods) > before_count
            if spawned:
                self.rhythm_mode.consume_food_refresh()
            return

        if not any(food.kind == "apple" for food in self.foods) and self.pending_apple_spawn_ms == 0:
            self._spawn_food("apple")
        if self.pending_special_spawn_ms == 0:
            self._maybe_spawn_special_food()

    def _update_dynamic_hazards(self) -> None:
        if not self.mode_info["hazards"]:
            return

        total_score = sum(snake.score for snake in self.snakes)
        bonus = {"easy": -1, "normal": 0, "hard": 1}.get(self.current_difficulty_id, 0)
        target_level = min(4, max(0, total_score // 5 + bonus))
        while self.obstacle_level < target_level:
            self._add_dynamic_obstacle()
            self.obstacle_level += 1

    def _add_dynamic_obstacle(self) -> None:
        blocked = self._blocked_positions() | self._forbidden_positions()
        candidates = [
            (x, y)
            for x in range(4, settings.BOARD_COLS - 4)
            for y in range(4, settings.BOARD_ROWS - 4)
            if (x, y) not in blocked
        ]
        if not candidates:
            return

        center = random.choice(candidates)
        cluster = {
            center,
            (center[0] + 1, center[1]),
            (center[0], center[1] + 1),
        }
        for cell in cluster:
            if (
                0 <= cell[0] < settings.BOARD_COLS
                and 0 <= cell[1] < settings.BOARD_ROWS
                and cell not in blocked
            ):
                self.obstacles.add(cell)
        self.round_message = self.t("msg_obstacles")

    def _check_end_conditions(self) -> None:
        alive_snakes = [snake for snake in self.snakes if snake.alive]
        team_score = sum(snake.score for snake in self.snakes)

        if self.current_mode_id == "timed_solo":
            if not alive_snakes:
                self._finish_round(
                    self.t("game_over"),
                    [
                        self.t("game_over_score", score=team_score),
                        self.t("result_reason", reason=self.snakes[0].death_reason or self.t("reason_wall")),
                    ],
                    None,
                    team_score,
                )
            return

        if self.current_mode_id == "coop":
            if team_score >= settings.COOP_TARGET_SCORE:
                self._finish_round(
                    self.t("mission_cleared"),
                    [
                        self.t("mission_score", score=team_score),
                        self.t("mission_team"),
                        self.t("result_reason", reason=self.t("reason_score_target")),
                    ],
                    "coop_clears",
                    team_score,
                )
                return

            if not alive_snakes:
                self._finish_round(
                    self.t("mission_failed"),
                    [
                        self.t("mission_failed_score", score=team_score),
                        self.t("result_reason", reason=self.t("reason_team_failed")),
                        self.t("mission_failed_tip"),
                    ],
                    None,
                    team_score,
                )
            return

        target_score = settings.DUEL_TARGET_SCORE
        if len(alive_snakes) <= 1 or any(
            snake.score >= target_score for snake in self.snakes
        ):
            ordered = sorted(
                self.snakes,
                key=lambda snake: (snake.alive, snake.score, len(snake.segments)),
                reverse=True,
            )
            winner = ordered[0]
            winner_key = self._winner_key(winner.name)
            if any(snake.score >= target_score for snake in self.snakes):
                reason = self.t("reason_score_target")
            else:
                reason = self.t("reason_last_alive")
            self._finish_round(
                self.t("winner_title", name=winner.name),
                [
                    self.t("winner_score", name=winner.name, score=winner.score),
                    self.t("opponent_score", score=ordered[1].score if len(ordered) > 1 else 0),
                    self.t("result_reason", reason=reason),
                ],
                winner_key,
                winner.score,
            )

    def _winner_key(self, name: str) -> str:
        lowered = name.lower()
        if "two" in lowered:
            return "player_two"
        if "ai" in lowered:
            return "ai"
        return "player_one"

    def _finish_round(
        self,
        title: str,
        lines: list[str],
        winner_key: str | None,
        team_score: int,
    ) -> None:
        if self.state == "game_over":
            return

        self.state = "game_over"
        self.result_title = title
        self.result_lines = lines
        self.result_actions = [
            self.t("result_play_again"),
            self.t("result_change_mode"),
            self.t("result_quit"),
        ]
        self.result_action_index = 0
        self.round_message = lines[0]
        if self.rhythm_mode is not None:
            self.rhythm_mode.on_exit(self)
        if self.current_mode_id != "lan_duel":
            self.stats_store.record_match(
                self.current_mode_id,
                self.snakes,
                winner_key,
                team_score,
            )
        elif isinstance(self.network_session, HostSession):
            self.network_session.update_live_status(winner=winner_key or "")
        self._broadcast_snapshot_if_needed()

    def _broadcast_snapshot_if_needed(self) -> None:
        if not isinstance(self.network_session, HostSession):
            return
        self.network_session.send_snapshot(self._build_snapshot())

    def _build_snapshot(self) -> dict:
        lan_live = self._lan_live_stats()
        return {
            "state": self.state,
            "mode_id": self.current_mode_id,
            "round_message": self.round_message,
            "result_title": getattr(self, "result_title", ""),
            "result_lines": getattr(self, "result_lines", []),
            "show_ai_paths": self.show_ai_paths,
            "portals": [list(item) for item in self.portals] if self.portals else [],
            "obstacles": [list(cell) for cell in sorted(self.obstacles)],
            "foods": [
                {
                    "kind": food.kind,
                    "position": list(food.position),
                    "label": food.label,
                    "color": list(food.color),
                    "score": food.score_value,
                }
                for food in self.foods
            ],
            "snakes": [
                {
                    "name": snake.name,
                    "segments": [list(segment) for segment in snake.segments],
                    "alive": snake.alive,
                    "score": snake.score,
                    "phase_ticks": snake.phase_ticks,
                    "slow_ticks": snake.slow_ticks,
                    "haste_ticks": snake.haste_ticks,
                    "bounce_ticks": snake.bounce_ticks,
                    "magnet_ticks": snake.magnet_ticks,
                    "is_ai": snake.is_ai,
                    "colors": snake.colors,
                    "last_path": [list(step) for step in snake.last_path],
                    "ai_status": snake.ai_status,
                }
                for snake in self.snakes
            ],
            "stats": self.stats_store.hud_summary(self.current_mode_id, lan_live=lan_live),
            "network_role": self.network_role,
            "language": self.localizer.language,
            "time_remaining_ms": self.time_remaining_ms,
            "difficulty_id": self.current_difficulty_id,
            "hud_extras": self._hud_extras(),
        }

    def _hud_extras(self) -> dict:
        lan_live = self._lan_live_stats()
        extras = {
            "mode": self.current_mode_id,
            "difficulty": self.current_difficulty_id,
            "skill_points": {},
            "combo": None,
            "event": "",
            "ai": {},
            "lan_live": lan_live,
        }
        if self.strategy_mode is not None:
            for snake in self.snakes:
                summary = self.strategy_mode.snake_hud_summary(snake.name)
                extras["skill_points"][snake.name] = summary.get("skill_points", 0)
            lines = self.strategy_mode.hud_lines()
            extras["event"] = lines[-1] if lines else ""
        if self.rhythm_mode is not None:
            state = self.rhythm_mode.hud_state()
            extras["combo"] = state.combo
            extras["beat"] = {
                "beat_in_bar": state.beat_in_bar,
                "beats_per_bar": self.rhythm_mode.beats_per_bar,
                "accuracy": state.accuracy_label,
            }
        for snake in self.snakes:
            extras["ai"][snake.name] = getattr(snake, "ai_status", {})
        return extras

    def _lan_live_stats(self) -> dict:
        if self.current_mode_id != "lan_duel":
            return {}
        host_score = self.snakes[0].score if len(self.snakes) > 0 else 0
        remote_score = self.snakes[1].score if len(self.snakes) > 1 else 0
        winner = ""
        if self.state == "game_over":
            winner = self.result_title
        live = {
            "players": 2 if len(getattr(self, "snakes", [])) > 1 else 1,
            "host_score": host_score,
            "remote_score": remote_score,
            "winner": winner,
        }
        if isinstance(self.network_session, HostSession):
            self.network_session.update_live_status(**live)
        return live

    def draw(self) -> None:
        """Draw the current frame."""
        self.renderer.draw(self)
        pygame.display.flip()

    def _handle_result_action(self) -> None:
        if not self.result_actions:
            self.start_mode(self.current_mode_id)
            return
        action = self.result_actions[self.result_action_index]
        if action == self.t("result_play_again"):
            self.start_mode(self.current_mode_id)
        elif action == self.t("result_change_mode"):
            self.enter_menu()
        else:
            self.is_running = False
            self._close_network()
