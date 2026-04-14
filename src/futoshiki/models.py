"""Core data models shared by the whole project."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

Cell = tuple[int, int]
DomainMap = dict[Cell, set[int]]


@dataclass(slots=True)
class PuzzleInstance:
    """Immutable representation of one Futoshiki puzzle instance."""

    size: int
    grid: list[list[int]]
    horizontal_constraints: list[list[int]]
    vertical_constraints: list[list[int]]
    name: str = ""
    source_path: Path | None = None

    def clone(self) -> "PuzzleInstance":
        return PuzzleInstance(
            size=self.size,
            grid=[row[:] for row in self.grid],
            horizontal_constraints=[row[:] for row in self.horizontal_constraints],
            vertical_constraints=[row[:] for row in self.vertical_constraints],
            name=self.name,
            source_path=self.source_path,
        )

    def iter_cells(self) -> list[Cell]:
        return [(r, c) for r in range(self.size) for c in range(self.size)]

    def givens(self) -> dict[Cell, int]:
        return {
            (r, c): self.grid[r][c]
            for r in range(self.size)
            for c in range(self.size)
            if self.grid[r][c] != 0
        }

    def is_given(self, cell: Cell) -> bool:
        r, c = cell
        return self.grid[r][c] != 0


@dataclass(slots=True)
class SolveTraceEvent:
    """One trace event emitted by a solver or propagator."""

    category: str
    message: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SolveStats:
    """Metrics collected while solving one puzzle."""

    solver_name: str
    runtime_ms: float = 0.0
    nodes_expanded: int = 0
    recursive_calls: int = 0
    rule_firings: int = 0
    contradictions: int = 0
    peak_frontier: int = 0
    peak_open_set: int = 0
    peak_domain_size_sum: int = 0
    propagations: int = 0
    depth: int = 0
    consistent: bool = True
    solved_by_search: bool = False
    heuristic_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "solver": self.solver_name,
            "runtime_ms": round(self.runtime_ms, 3),
            "nodes_expanded": self.nodes_expanded,
            "recursive_calls": self.recursive_calls,
            "rule_firings": self.rule_firings,
            "contradictions": self.contradictions,
            "peak_frontier": self.peak_frontier,
            "peak_open_set": self.peak_open_set,
            "peak_domain_size_sum": self.peak_domain_size_sum,
            "propagations": self.propagations,
            "depth": self.depth,
            "consistent": self.consistent,
            "solved_by_search": self.solved_by_search,
            "heuristic": self.heuristic_name,
        }


@dataclass(slots=True)
class SolverResult:
    """Final solver output."""

    solved: bool
    valid: bool
    grid: list[list[int]] | None
    stats: SolveStats
    trace: list[SolveTraceEvent] = field(default_factory=list)
    message: str = ""
    domains: DomainMap | None = None
    assignment_origins: dict[Cell, str] = field(default_factory=dict)
    cnf_stats: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
