"""Constraint propagation: domain initialization, forward checking, and AC-3."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from .constraints import all_arcs, constraint_graph, is_pair_allowed
from .models import Cell, DomainMap, PuzzleInstance, SolveTraceEvent
from .utils import cell_label


@dataclass(slots=True)
class PropagationResult:
    consistent: bool
    domains: DomainMap
    trace: list[SolveTraceEvent] = field(default_factory=list)
    pruned: int = 0
    contradictions: int = 0
    revisions: int = 0


def initialize_domains(instance: PuzzleInstance, grid: list[list[int]] | None = None) -> DomainMap:
    source_grid = grid if grid is not None else instance.grid
    domains: DomainMap = {}
    for r in range(instance.size):
        for c in range(instance.size):
            value = source_grid[r][c]
            domains[(r, c)] = {value} if value != 0 else set(range(1, instance.size + 1))
    return domains


def clone_domains(domains: DomainMap) -> DomainMap:
    return {cell: values.copy() for cell, values in domains.items()}


def domains_to_grid(instance: PuzzleInstance, domains: DomainMap) -> list[list[int]]:
    grid = [[0 for _ in range(instance.size)] for _ in range(instance.size)]
    for (r, c), values in domains.items():
        if len(values) == 1:
            grid[r][c] = next(iter(values))
    return grid


def revise(
    instance: PuzzleInstance,
    domains: DomainMap,
    xi: Cell,
    xj: Cell,
    trace: list[SolveTraceEvent],
) -> tuple[bool, int]:
    removed: list[int] = []
    for value in sorted(domains[xi]):
        if not any(is_pair_allowed(instance, xi, xj, value, other) for other in domains[xj]):
            removed.append(value)
    if not removed:
        return False, 0
    for value in removed:
        domains[xi].remove(value)
        trace.append(
            SolveTraceEvent(
                category="ac3-prune",
                message=f"AC-3 pruned {value} from {cell_label(xi)} due to {cell_label(xj)}.",
                payload={"cell": xi, "peer": xj, "value": value},
            )
        )
    return True, len(removed)


def enforce_unary_constraints(
    instance: PuzzleInstance,
    domains: DomainMap,
    trace: list[SolveTraceEvent],
) -> tuple[bool, int]:
    pruned = 0
    for r in range(instance.size):
        for c in range(instance.size):
            given = instance.grid[r][c]
            if given != 0:
                other_values = [value for value in domains[(r, c)] if value != given]
                for value in other_values:
                    domains[(r, c)].remove(value)
                    pruned += 1
                trace.append(
                    SolveTraceEvent(
                        category="given",
                        message=f"Given fixed {cell_label((r, c))} = {given}.",
                        payload={"cell": (r, c), "value": given},
                    )
                )
            if not domains[(r, c)]:
                trace.append(
                    SolveTraceEvent(
                        category="contradiction",
                        message=f"Cell {cell_label((r, c))} has empty domain.",
                        payload={"cell": (r, c)},
                    )
                )
                return False, pruned
    return True, pruned


def ac3(
    instance: PuzzleInstance,
    domains: DomainMap,
    *,
    trace_enabled: bool = True,
) -> PropagationResult:
    domains = clone_domains(domains)
    trace: list[SolveTraceEvent] = []
    consistent, pruned = enforce_unary_constraints(instance, domains, trace)
    if not consistent:
        return PropagationResult(False, domains, trace, pruned=pruned, contradictions=1)

    queue = deque(all_arcs(instance))
    graph = constraint_graph(instance)
    revisions = 0
    contradictions = 0

    while queue:
        xi, xj = queue.popleft()
        revised, removed_count = revise(instance, domains, xi, xj, trace if trace_enabled else [])
        if not revised:
            continue
        pruned += removed_count
        revisions += 1
        if not domains[xi]:
            contradictions += 1
            trace.append(
                SolveTraceEvent(
                    category="contradiction",
                    message=f"Domain wipeout at {cell_label(xi)}.",
                    payload={"cell": xi},
                )
            )
            return PropagationResult(
                False,
                domains,
                trace,
                pruned=pruned,
                contradictions=contradictions,
                revisions=revisions,
            )
        for neighbor in graph.get(xi, set()):
            if neighbor != xj:
                queue.append((neighbor, xi))

    return PropagationResult(
        True,
        domains,
        trace,
        pruned=pruned,
        contradictions=contradictions,
        revisions=revisions,
    )


def forward_check(
    instance: PuzzleInstance,
    domains: DomainMap,
    assigned_cell: Cell,
    *,
    trace_enabled: bool = True,
) -> PropagationResult:
    trace: list[SolveTraceEvent] = []
    working = clone_domains(domains)
    value = next(iter(working[assigned_cell]))
    pruned = 0
    contradictions = 0
    graph = constraint_graph(instance)

    for cell in sorted(graph.get(assigned_cell, set())):
        if cell == assigned_cell:
            continue
        if len(working[cell]) == 1:
            continue
        to_remove = {
            other for other in working[cell] if not is_pair_allowed(instance, cell, assigned_cell, other, value)
        }
        if not to_remove:
            continue
        working[cell] -= to_remove
        pruned += len(to_remove)
        if trace_enabled:
            trace.append(
                SolveTraceEvent(
                    category="forward-check",
                    message=(
                        f"Forward checking pruned {sorted(to_remove)} from {cell_label(cell)} "
                        f"after assigning {cell_label(assigned_cell)} = {value}."
                    ),
                    payload={"cell": cell, "assigned_cell": assigned_cell, "removed": sorted(to_remove)},
                )
            )
        if not working[cell]:
            contradictions += 1
            trace.append(
                SolveTraceEvent(
                    category="contradiction",
                    message=f"Forward checking emptied {cell_label(cell)}.",
                    payload={"cell": cell},
                )
            )
            return PropagationResult(False, working, trace, pruned=pruned, contradictions=contradictions)

    return PropagationResult(True, working, trace, pruned=pruned, contradictions=contradictions)


def propagate(
    instance: PuzzleInstance,
    domains: DomainMap,
    *,
    assigned_cell: Cell | None = None,
    use_forward_checking: bool = True,
    use_ac3: bool = True,
    trace_enabled: bool = True,
) -> PropagationResult:
    working = clone_domains(domains)
    trace: list[SolveTraceEvent] = []
    total_pruned = 0
    total_contradictions = 0
    revisions = 0

    if assigned_cell is not None and use_forward_checking:
        fc_result = forward_check(
            instance,
            working,
            assigned_cell,
            trace_enabled=trace_enabled,
        )
        working = fc_result.domains
        trace.extend(fc_result.trace)
        total_pruned += fc_result.pruned
        total_contradictions += fc_result.contradictions
        if not fc_result.consistent:
            return PropagationResult(
                False,
                working,
                trace,
                pruned=total_pruned,
                contradictions=total_contradictions,
            )

    if use_ac3:
        ac3_result = ac3(instance, working, trace_enabled=trace_enabled)
        working = ac3_result.domains
        trace.extend(ac3_result.trace)
        total_pruned += ac3_result.pruned
        total_contradictions += ac3_result.contradictions
        revisions += ac3_result.revisions
        if not ac3_result.consistent:
            return PropagationResult(
                False,
                working,
                trace,
                pruned=total_pruned,
                contradictions=total_contradictions,
                revisions=revisions,
            )

    return PropagationResult(
        True,
        working,
        trace,
        pruned=total_pruned,
        contradictions=total_contradictions,
        revisions=revisions,
    )
