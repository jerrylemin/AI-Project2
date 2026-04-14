"""Constraint helpers for Latin and inequality restrictions."""

from __future__ import annotations

from collections import defaultdict

from .models import Cell, PuzzleInstance


def row_peers(instance: PuzzleInstance, cell: Cell) -> list[Cell]:
    r, c = cell
    return [(r, other_c) for other_c in range(instance.size) if other_c != c]


def col_peers(instance: PuzzleInstance, cell: Cell) -> list[Cell]:
    r, c = cell
    return [(other_r, c) for other_r in range(instance.size) if other_r != r]


def inequality_neighbors(instance: PuzzleInstance, cell: Cell) -> list[tuple[Cell, str, int]]:
    """Return neighboring inequality constraints touching the cell.

    Each item is (other_cell, axis, relation) where relation is:
    - 1  => this cell < other_cell
    - -1 => this cell > other_cell
    """

    r, c = cell
    neighbors: list[tuple[Cell, str, int]] = []
    if c < instance.size - 1:
        rel = instance.horizontal_constraints[r][c]
        if rel == 1:
            neighbors.append(((r, c + 1), "H", 1))
        elif rel == -1:
            neighbors.append(((r, c + 1), "H", -1))
    if c > 0:
        rel = instance.horizontal_constraints[r][c - 1]
        if rel == 1:
            neighbors.append(((r, c - 1), "H", -1))
        elif rel == -1:
            neighbors.append(((r, c - 1), "H", 1))
    if r < instance.size - 1:
        rel = instance.vertical_constraints[r][c]
        if rel == 1:
            neighbors.append(((r + 1, c), "V", 1))
        elif rel == -1:
            neighbors.append(((r + 1, c), "V", -1))
    if r > 0:
        rel = instance.vertical_constraints[r - 1][c]
        if rel == 1:
            neighbors.append(((r - 1, c), "V", -1))
        elif rel == -1:
            neighbors.append(((r - 1, c), "V", 1))
    return neighbors


def is_pair_allowed(instance: PuzzleInstance, left: Cell, right: Cell, a: int, b: int) -> bool:
    if left[0] == right[0]:
        if a == b:
            return False
        row = left[0]
        c1, c2 = sorted((left[1], right[1]))
        if c2 == c1 + 1:
            rel = instance.horizontal_constraints[row][c1]
            if rel == 1 and left[1] < right[1]:
                return a < b
            if rel == 1 and left[1] > right[1]:
                return a > b
            if rel == -1 and left[1] < right[1]:
                return a > b
            if rel == -1 and left[1] > right[1]:
                return a < b
        return True
    if left[1] == right[1]:
        if a == b:
            return False
        col = left[1]
        r1, r2 = sorted((left[0], right[0]))
        if r2 == r1 + 1:
            rel = instance.vertical_constraints[r1][col]
            if rel == 1 and left[0] < right[0]:
                return a < b
            if rel == 1 and left[0] > right[0]:
                return a > b
            if rel == -1 and left[0] < right[0]:
                return a > b
            if rel == -1 and left[0] > right[0]:
                return a < b
        return True
    return True


def all_arcs(instance: PuzzleInstance) -> list[tuple[Cell, Cell]]:
    arcs: list[tuple[Cell, Cell]] = []
    for r in range(instance.size):
        for c in range(instance.size):
            cell = (r, c)
            for peer in row_peers(instance, cell):
                arcs.append((cell, peer))
            for peer in col_peers(instance, cell):
                arcs.append((cell, peer))
            for peer, _, _ in inequality_neighbors(instance, cell):
                arcs.append((cell, peer))
    return list(dict.fromkeys(arcs))


def constraint_graph(instance: PuzzleInstance) -> dict[Cell, set[Cell]]:
    graph: dict[Cell, set[Cell]] = defaultdict(set)
    for cell, peer in all_arcs(instance):
        graph[cell].add(peer)
    return dict(graph)
