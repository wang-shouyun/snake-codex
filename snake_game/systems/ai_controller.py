"""Pathfinding and decision making for AI-controlled snakes."""

from __future__ import annotations

from collections import deque

from entities.food import Food
from entities.snake import Snake
from systems.collision import resolve_portal
from utils.helpers import DIRECTIONS, inside_board, manhattan_distance


class SnakeAI:
    """Chooses safe directions using BFS with a lightweight fallback heuristic."""

    def choose_direction(
        self,
        snake: Snake,
        snakes: list[Snake],
        foods: list[Food],
        obstacles: set[tuple[int, int]],
        portals: tuple[tuple[int, int], tuple[int, int]] | None,
        strategy_weights: dict[str, float] | None = None,
    ) -> tuple[int, int]:
        """Return the next direction for an AI snake."""
        weights = strategy_weights or {"food": 1.0, "space": 1.0, "risk": 1.0}
        occupied = self._occupied_cells(snakes, snake)
        danger_heads = self._danger_heads(snakes, snake, portals)
        snake.ai_status = {
            "mode": "search",
            "target": None,
            "status": "Scanning foods",
            "lookahead": 0,
            "risk": "medium",
        }
        targets = sorted(
            foods,
            key=lambda food: (
                manhattan_distance(snake.head_position, food.position) * weights["risk"]
                - food.score_value * weights["food"]
            ),
        )

        for food in targets:
            path = self._find_path(
                snake.head_position,
                food.position,
                occupied,
                obstacles,
                portals,
                snake.can_phase(),
                blocked_heads=danger_heads,
            )
            if path and self._path_is_safe(
                snake,
                path,
                occupied,
                obstacles,
                portals,
                snake.can_phase(),
                danger_heads,
            ):
                snake.last_path = path
                snake.ai_status = {
                    "mode": "safe-path",
                    "target": food.position,
                    "status": f"Safe path to {food.kind}",
                    "lookahead": len(path),
                    "risk": self._risk_label(len(path)),
                }
                next_cell = path[0]
                return next_cell[0] - snake.head_position[0], next_cell[1] - snake.head_position[1]

        fallback_direction = self._fallback_direction(
            snake,
            occupied,
            obstacles,
            portals,
            snake.can_phase(),
            space_weight=weights["space"],
            blocked_heads=danger_heads,
        )
        snake.last_path = []
        snake.ai_status = {
            "mode": "fallback",
            "target": None,
            "status": "Space-first fallback",
            "lookahead": 2,
            "risk": "medium",
        }
        return fallback_direction

    def _occupied_cells(self, snakes: list[Snake], current: Snake) -> set[tuple[int, int]]:
        occupied: set[tuple[int, int]] = set()
        for snake in snakes:
            if not snake.alive:
                continue
            if snake is current:
                occupied.update(snake.segments[:-1])
            else:
                occupied.update(snake.segments)
        return occupied

    def _find_path(
        self,
        start: tuple[int, int],
        target: tuple[int, int],
        occupied: set[tuple[int, int]],
        obstacles: set[tuple[int, int]],
        portals: tuple[tuple[int, int], tuple[int, int]] | None,
        can_phase: bool,
        blocked_heads: set[tuple[int, int]] | None = None,
    ) -> list[tuple[int, int]]:
        queue = deque([start])
        parents: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
        blocked_heads = blocked_heads or set()

        while queue:
            current = queue.popleft()
            if current == target:
                return self._rebuild_path(parents, target)

            for dir_x, dir_y in DIRECTIONS:
                candidate = (current[0] + dir_x, current[1] + dir_y)
                if not inside_board(candidate):
                    continue
                candidate = resolve_portal(candidate, portals)
                if candidate in parents:
                    continue
                if candidate in blocked_heads and candidate != target:
                    continue
                if not can_phase and (candidate in occupied or candidate in obstacles):
                    continue
                if candidate in occupied and candidate != target:
                    continue
                parents[candidate] = current
                queue.append(candidate)

        return []

    def _rebuild_path(
        self,
        parents: dict[tuple[int, int], tuple[int, int] | None],
        target: tuple[int, int],
    ) -> list[tuple[int, int]]:
        path = [target]
        current = target
        while parents[current] is not None:
            current = parents[current]
            path.append(current)
        path.reverse()
        return path[1:]

    def _fallback_direction(
        self,
        snake: Snake,
        occupied: set[tuple[int, int]],
        obstacles: set[tuple[int, int]],
        portals: tuple[tuple[int, int], tuple[int, int]] | None,
        can_phase: bool,
        space_weight: float = 1.0,
        blocked_heads: set[tuple[int, int]] | None = None,
    ) -> tuple[int, int]:
        safe_moves: list[tuple[float, tuple[int, int]]] = []
        blocked_heads = blocked_heads or set()

        for direction in DIRECTIONS:
            snake.set_direction(direction)
            candidate = snake.preview_next_head()
            candidate = resolve_portal(candidate, portals)
            if not inside_board(candidate):
                continue
            if candidate in blocked_heads:
                continue
            if not can_phase and (candidate in occupied or candidate in obstacles):
                continue
            open_neighbors = self._free_neighbor_count(
                candidate,
                occupied,
                obstacles,
                portals,
                can_phase,
                blocked_heads,
            )
            reachable_space = self._flood_space(
                candidate,
                occupied,
                obstacles,
                portals,
                can_phase,
                blocked_heads,
                limit=80,
            )
            score = reachable_space * (1.8 * space_weight) + open_neighbors * 3
            if direction == snake.direction:
                score += 1.5
            safe_moves.append((score, direction))

        if safe_moves:
            safe_moves.sort(reverse=True)
            return safe_moves[0][1]
        return snake.direction

    def _path_is_safe(
        self,
        snake: Snake,
        path: list[tuple[int, int]],
        occupied: set[tuple[int, int]],
        obstacles: set[tuple[int, int]],
        portals: tuple[tuple[int, int], tuple[int, int]] | None,
        can_phase: bool,
        blocked_heads: set[tuple[int, int]],
    ) -> bool:
        simulated = list(snake.segments)
        for step in path:
            simulated = [step] + simulated[:-1]

        simulated_head = simulated[0]
        simulated_occupied = set(simulated[:-1])
        escape_target = simulated[-1]
        escape_path = self._find_path(
            simulated_head,
            escape_target,
            simulated_occupied,
            obstacles,
            portals,
            can_phase,
            blocked_heads=blocked_heads,
        )
        reachable_space = self._flood_space(
            simulated_head,
            simulated_occupied,
            obstacles,
            portals,
            can_phase,
            blocked_heads,
            limit=100,
        )
        return bool(escape_path) or reachable_space >= max(8, len(simulated) // 2)

    def _danger_heads(
        self,
        snakes: list[Snake],
        current: Snake,
        portals: tuple[tuple[int, int], tuple[int, int]] | None,
    ) -> set[tuple[int, int]]:
        danger: set[tuple[int, int]] = set()
        for snake in snakes:
            if snake is current or not snake.alive:
                continue
            for dir_x, dir_y in DIRECTIONS:
                candidate = (snake.head_position[0] + dir_x, snake.head_position[1] + dir_y)
                if not inside_board(candidate):
                    continue
                danger.add(resolve_portal(candidate, portals))
        return danger

    def _free_neighbor_count(
        self,
        position: tuple[int, int],
        occupied: set[tuple[int, int]],
        obstacles: set[tuple[int, int]],
        portals: tuple[tuple[int, int], tuple[int, int]] | None,
        can_phase: bool,
        blocked_heads: set[tuple[int, int]],
    ) -> int:
        open_neighbors = 0
        for dir_x, dir_y in DIRECTIONS:
            near = (position[0] + dir_x, position[1] + dir_y)
            if not inside_board(near):
                continue
            near = resolve_portal(near, portals)
            if near in blocked_heads:
                continue
            if can_phase or (near not in occupied and near not in obstacles):
                open_neighbors += 1
        return open_neighbors

    def _flood_space(
        self,
        start: tuple[int, int],
        occupied: set[tuple[int, int]],
        obstacles: set[tuple[int, int]],
        portals: tuple[tuple[int, int], tuple[int, int]] | None,
        can_phase: bool,
        blocked_heads: set[tuple[int, int]],
        limit: int = 120,
    ) -> int:
        queue = deque([start])
        seen = {start}
        while queue and len(seen) < limit:
            current = queue.popleft()
            for dir_x, dir_y in DIRECTIONS:
                candidate = (current[0] + dir_x, current[1] + dir_y)
                if not inside_board(candidate):
                    continue
                candidate = resolve_portal(candidate, portals)
                if candidate in seen or candidate in blocked_heads:
                    continue
                if not can_phase and (candidate in occupied or candidate in obstacles):
                    continue
                seen.add(candidate)
                queue.append(candidate)
        return len(seen)

    def _risk_label(self, path_length: int) -> str:
        if path_length <= 2:
            return "high"
        if path_length <= 5:
            return "medium"
        return "low"
