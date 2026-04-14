"""Benchmark helpers for running multiple solvers on a batch of puzzles."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .parser import parse_file
from .solvers.astar import AStarSolver
from .solvers.backtracking import BacktrackingSolver
from .solvers.base import SolverConfig
from .solvers.bruteforce import BruteforceSolver
from .solvers.logic_backward_solver import LogicBackwardSolver
from .solvers.logic_forward_solver import LogicForwardSolver
from .validator import validate_solution


@dataclass(slots=True)
class SolverSpec:
    name: str
    label: str


BENCHMARK_SPECS = [
    SolverSpec("bruteforce", "bruteforce"),
    SolverSpec("backtracking", "backtracking"),
    SolverSpec("astar-h0", "astar-h0"),
    SolverSpec("astar-main", "astar-main"),
    SolverSpec("logic-forward", "logic-forward"),
    SolverSpec("logic-backward", "logic-backward"),
]


def create_solver(name: str):
    if name in {"bruteforce"}:
        return BruteforceSolver()
    if name in {"backtracking"}:
        return BacktrackingSolver(SolverConfig())
    if name in {"astar", "astar-main"}:
        return AStarSolver(SolverConfig(heuristic="main"))
    if name == "astar-h0":
        return AStarSolver(SolverConfig(heuristic="h0"))
    if name in {"logic-forward", "logic-fc"}:
        return LogicForwardSolver(SolverConfig(fallback_search=True))
    if name in {"logic-backward", "logic-bc"}:
        return LogicBackwardSolver(SolverConfig(fallback_search=True))
    raise ValueError(f"Unknown solver {name!r}.")


def benchmark_inputs(
    inputs_dir: str | Path,
    out_csv: str | Path,
    *,
    solver_names: list[str] | None = None,
) -> list[dict[str, object]]:
    paths = sorted(Path(inputs_dir).glob("input-*.txt"))
    if not paths:
        raise FileNotFoundError(f"No input files found in {inputs_dir}.")
    requested = solver_names or [spec.name for spec in BENCHMARK_SPECS]
    rows: list[dict[str, object]] = []
    for path in paths:
        instance = parse_file(path)
        for solver_name in requested:
            solver = create_solver(solver_name)
            result = solver.solve(instance)
            valid = result.grid is not None and validate_solution(instance, result.grid)[0]
            rows.append(
                {
                    "input": path.name,
                    "size": instance.size,
                    "solver": solver_name,
                    "solved": result.solved,
                    "valid": valid,
                    "runtime_ms": round(result.stats.runtime_ms, 3),
                    "nodes_expanded": result.stats.nodes_expanded,
                    "recursive_calls": result.stats.recursive_calls,
                    "rule_firings": result.stats.rule_firings,
                    "contradictions": result.stats.contradictions,
                    "peak_frontier": result.stats.peak_frontier,
                    "peak_open_set": result.stats.peak_open_set,
                    "peak_domain_size_sum": result.stats.peak_domain_size_sum,
                }
            )

    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    with Path(out_csv).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def summarize_benchmark(rows: list[dict[str, object]]) -> str:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(str(row["solver"]), []).append(row)

    lines = [
        "# Benchmark Summary",
        "",
        "| Solver | Solved/Total | Avg runtime (ms) | Max runtime (ms) |",
        "|---|---:|---:|---:|",
    ]
    for solver, solver_rows in grouped.items():
        solved = sum(1 for row in solver_rows if row["solved"])
        avg_runtime = sum(float(row["runtime_ms"]) for row in solver_rows) / len(solver_rows)
        max_runtime = max(float(row["runtime_ms"]) for row in solver_rows)
        lines.append(f"| {solver} | {solved}/{len(solver_rows)} | {avg_runtime:.3f} | {max_runtime:.3f} |")
    return "\n".join(lines)
