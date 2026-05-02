from __future__ import annotations

import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from futoshiki.formatter import format_input_instance, format_instance
from futoshiki.heuristics import order_domain_values, select_unassigned_cell
from futoshiki.models import Cell, PuzzleInstance
from futoshiki.parser import parse_file, parse_output
from futoshiki.propagation import clone_domains, domains_to_grid, initialize_domains, propagate

Edge = tuple[str, int, int]


def count_solutions(instance: PuzzleInstance, limit: int = 2) -> int:
    initial = propagate(
        instance,
        initialize_domains(instance),
        use_forward_checking=False,
        use_ac3=True,
        trace_enabled=False,
    )
    if not initial.consistent:
        return 0

    def search(domains: dict[Cell, set[int]], found: int) -> int:
        if found >= limit:
            return found
        if all(len(values) == 1 for values in domains.values()):
            grid = domains_to_grid(instance, domains)
            return found + 1 if all(all(value != 0 for value in row) for row in grid) else found

        cell = select_unassigned_cell(instance, domains, use_degree=True)
        if cell is None:
            return found

        for value in order_domain_values(domains, cell):
            next_domains = clone_domains(domains)
            next_domains[cell] = {value}
            result = propagate(
                instance,
                next_domains,
                assigned_cell=cell,
                use_forward_checking=True,
                use_ac3=True,
                trace_enabled=False,
            )
            if not result.consistent:
                continue
            found = search(result.domains, found)
            if found >= limit:
                return found
        return found

    return search(initial.domains, 0)


def iter_edges(instance: PuzzleInstance) -> list[Edge]:
    edges: list[Edge] = []
    for r in range(instance.size):
        for c in range(instance.size - 1):
            if instance.horizontal_constraints[r][c] != 0:
                edges.append(("H", r, c))
    for r in range(instance.size - 1):
        for c in range(instance.size):
            if instance.vertical_constraints[r][c] != 0:
                edges.append(("V", r, c))
    return edges


def get_relation(instance: PuzzleInstance, edge: Edge) -> int:
    axis, r, c = edge
    if axis == "H":
        return instance.horizontal_constraints[r][c]
    return instance.vertical_constraints[r][c]


def set_relation(instance: PuzzleInstance, edge: Edge, value: int) -> None:
    axis, r, c = edge
    if axis == "H":
        instance.horizontal_constraints[r][c] = value
    else:
        instance.vertical_constraints[r][c] = value


def target_remaining(size: int, total_edges: int) -> int:
    return max(size + 2, round(total_edges * 0.28))


def sparsify_instance(instance: PuzzleInstance, seed: int) -> PuzzleInstance:
    sparse = instance.clone()
    edges = iter_edges(sparse)
    rng = random.Random(seed)
    rng.shuffle(edges)
    goal = target_remaining(sparse.size, len(edges))
    remaining = len(edges)

    for edge in edges:
        if remaining <= goal:
            break
        relation = get_relation(sparse, edge)
        set_relation(sparse, edge, 0)
        if count_solutions(sparse, limit=2) == 1:
            remaining -= 1
        else:
            set_relation(sparse, edge, relation)
    return sparse


def main() -> None:
    inputs_dir = PROJECT_ROOT / "inputs"
    outputs_dir = PROJECT_ROOT / "outputs"

    for idx, input_path in enumerate(sorted(inputs_dir.glob("input-*.txt")), start=1):
        output_path = outputs_dir / input_path.name.replace("input", "output")
        instance = parse_file(input_path)
        solution = parse_output(output_path.read_text(encoding="utf-8"), instance.size).grid
        sparse = sparsify_instance(instance, seed=20260503 + idx * 97)

        input_path.write_text(format_input_instance(sparse), encoding="utf-8")
        output_path.write_text(format_instance(sparse, grid=solution), encoding="utf-8")

        remaining = sum(1 for edge in iter_edges(sparse) if get_relation(sparse, edge) != 0)
        total = (instance.size * (instance.size - 1)) * 2
        print(f"{input_path.name}: kept {remaining}/{total} constraints")


if __name__ == "__main__":
    main()
