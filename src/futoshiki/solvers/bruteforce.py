"""Naive brute-force solver for baseline comparisons."""

from __future__ import annotations

from ..constraints import is_pair_allowed
from ..models import DomainMap, PuzzleInstance, SolveTraceEvent
from ..utils import deep_copy_grid
from ..validator import validate_solution
from .base import BaseSolver


class BruteforceSolver(BaseSolver):
    def __init__(self) -> None:
        super().__init__("bruteforce")

    def solve(
        self,
        instance: PuzzleInstance,
        *,
        initial_domains: DomainMap | None = None,
    ):
        grid = deep_copy_grid(instance.grid)
        with self._time_solve() as timer:
            solved = self._search(instance, grid, 0)
        self.stats.runtime_ms = timer.elapsed_ms
        if solved:
            valid, errors = validate_solution(instance, grid)
            message = "Solved." if valid else "; ".join(errors)
            return self._make_result(instance, grid, message=message)
        return self._make_result(instance, None, message="No solution found.")

    def _search(self, instance: PuzzleInstance, grid: list[list[int]], depth: int) -> bool:
        self.stats.recursive_calls += 1
        self.stats.depth = max(self.stats.depth, depth)
        self.stats.peak_frontier = max(self.stats.peak_frontier, depth + 1)
        cell = self._next_empty(instance, grid)
        if cell is None:
            return True
        r, c = cell
        self.stats.nodes_expanded += 1
        for value in range(1, instance.size + 1):
            if self._is_partial_assignment_valid(instance, grid, r, c, value):
                grid[r][c] = value
                self.trace.append(
                    SolveTraceEvent(
                        category="branch",
                        message=f"Bruteforce tried ({r + 1},{c + 1}) = {value}",
                        payload={"cell": (r, c), "value": value, "depth": depth},
                    )
                )
                if self._search(instance, grid, depth + 1):
                    return True
                grid[r][c] = 0
            else:
                self.stats.contradictions += 1
        return False

    def _next_empty(self, instance: PuzzleInstance, grid: list[list[int]]) -> tuple[int, int] | None:
        for r in range(instance.size):
            for c in range(instance.size):
                if grid[r][c] == 0:
                    return r, c
        return None

    def _is_partial_assignment_valid(
        self,
        instance: PuzzleInstance,
        grid: list[list[int]],
        row: int,
        col: int,
        value: int,
    ) -> bool:
        if value in grid[row]:
            return False
        if value in [grid[r][col] for r in range(instance.size)]:
            return False
        grid[row][col] = value
        neighbors = []
        if col > 0:
            neighbors.append((row, col - 1))
        if col < instance.size - 1:
            neighbors.append((row, col + 1))
        if row > 0:
            neighbors.append((row - 1, col))
        if row < instance.size - 1:
            neighbors.append((row + 1, col))
        for nr, nc in neighbors:
            other = grid[nr][nc]
            if other == 0:
                continue
            if not is_pair_allowed(instance, (row, col), (nr, nc), value, other):
                grid[row][col] = 0
                return False
        grid[row][col] = 0
        return True
