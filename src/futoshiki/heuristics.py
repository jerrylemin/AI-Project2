"""Variable/value ordering and admissible A* heuristics."""

from __future__ import annotations

from collections import deque

from .constraints import constraint_graph
from .models import Cell, DomainMap, PuzzleInstance


def select_unassigned_cell(
    instance: PuzzleInstance,
    domains: DomainMap,
    *,
    use_degree: bool = True,
) -> Cell | None:
    candidates = [cell for cell, values in domains.items() if len(values) > 1]
    if not candidates:
        return None
    graph = constraint_graph(instance)

    def key(cell: Cell) -> tuple[int, int, int, int]:
        unresolved_degree = sum(1 for peer in graph.get(cell, set()) if len(domains[peer]) > 1)
        return (
            len(domains[cell]),
            -unresolved_degree if use_degree else 0,
            cell[0],
            cell[1],
        )

    return min(candidates, key=key)


def order_domain_values(domains: DomainMap, cell: Cell) -> list[int]:
    return sorted(domains[cell])


def heuristic_zero(_: PuzzleInstance, __: DomainMap) -> int:
    return 0


def heuristic_weak(_: PuzzleInstance, domains: DomainMap) -> int:
    return 1 if any(len(values) > 1 for values in domains.values()) else 0


def count_ambiguous_components(instance: PuzzleInstance, domains: DomainMap) -> int:
    graph = constraint_graph(instance)
    ambiguous = {cell for cell, values in domains.items() if len(values) > 1}
    seen: set[Cell] = set()
    components = 0

    for start in ambiguous:
        if start in seen:
            continue
        components += 1
        queue = deque([start])
        seen.add(start)
        while queue:
            cell = queue.popleft()
            for peer in graph.get(cell, set()):
                if peer in ambiguous and peer not in seen:
                    seen.add(peer)
                    queue.append(peer)
    return components


def heuristic_main(instance: PuzzleInstance, domains: DomainMap) -> int:
    return count_ambiguous_components(instance, domains)


HEURISTICS = {
    "h0": heuristic_zero,
    "hweak": heuristic_weak,
    "main": heuristic_main,
}
