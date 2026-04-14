"""Base classes and helpers for solvers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..models import DomainMap, PuzzleInstance, SolveStats, SolveTraceEvent, SolverResult
from ..propagation import domains_to_grid
from ..utils import Timer
from ..validator import validate_solution


@dataclass(slots=True)
class SolverConfig:
    use_mrv: bool = True
    use_degree: bool = True
    use_forward_checking: bool = True
    use_ac3: bool = True
    fallback_search: bool = True
    heuristic: str = "main"


class BaseSolver(ABC):
    """Abstract solver interface."""

    def __init__(self, name: str, config: SolverConfig | None = None):
        self.name = name
        self.config = config or SolverConfig()
        self.trace: list[SolveTraceEvent] = []
        self.stats = SolveStats(solver_name=name, heuristic_name=self.config.heuristic)

    @abstractmethod
    def solve(
        self,
        instance: PuzzleInstance,
        *,
        initial_domains: DomainMap | None = None,
    ) -> SolverResult:
        raise NotImplementedError

    def _make_result(
        self,
        instance: PuzzleInstance,
        grid: list[list[int]] | None,
        *,
        message: str = "",
        domains: DomainMap | None = None,
        metadata: dict | None = None,
        assignment_origins: dict | None = None,
    ) -> SolverResult:
        valid = False
        if grid is not None:
            valid, _ = validate_solution(instance, grid)
        return SolverResult(
            solved=grid is not None and valid,
            valid=valid,
            grid=grid,
            stats=self.stats,
            trace=self.trace,
            message=message,
            domains=domains,
            metadata=metadata or {},
            assignment_origins=assignment_origins or {},
        )

    def _grid_from_domains(self, instance: PuzzleInstance, domains: DomainMap) -> list[list[int]] | None:
        grid = domains_to_grid(instance, domains)
        return grid if all(value != 0 for row in grid for value in row) else None

    def _time_solve(self):
        return Timer()
