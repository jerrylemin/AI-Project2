"""Validation for puzzle instances and candidate solutions."""

from __future__ import annotations

from .models import PuzzleInstance


def validate_instance(instance: PuzzleInstance) -> tuple[bool, list[str]]:
    errors: list[str] = []
    n = instance.size
    if len(instance.grid) != n or any(len(row) != n for row in instance.grid):
        errors.append("Grid must be N x N.")
    if len(instance.horizontal_constraints) != n or any(
        len(row) != max(0, n - 1) for row in instance.horizontal_constraints
    ):
        errors.append("Horizontal constraints must be N x (N-1).")
    if len(instance.vertical_constraints) != max(0, n - 1) or any(
        len(row) != n for row in instance.vertical_constraints
    ):
        errors.append("Vertical constraints must be (N-1) x N.")

    for r, row in enumerate(instance.grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or value < 0 or value > n:
                errors.append(f"Cell ({r + 1},{c + 1}) has invalid value {value!r}.")

    for r, row in enumerate(instance.horizontal_constraints):
        for c, rel in enumerate(row):
            if rel not in {-1, 0, 1}:
                errors.append(f"Horizontal constraint ({r + 1},{c + 1}) must be -1, 0, or 1.")
    for r, row in enumerate(instance.vertical_constraints):
        for c, rel in enumerate(row):
            if rel not in {-1, 0, 1}:
                errors.append(f"Vertical constraint ({r + 1},{c + 1}) must be -1, 0, or 1.")

    for r in range(n):
        row_values = [value for value in instance.grid[r] if value != 0]
        if len(row_values) != len(set(row_values)):
            errors.append(f"Row {r + 1} duplicates a given value.")
    for c in range(n):
        col_values = [instance.grid[r][c] for r in range(n) if instance.grid[r][c] != 0]
        if len(col_values) != len(set(col_values)):
            errors.append(f"Column {c + 1} duplicates a given value.")

    valid_partial, partial_errors = validate_solution(
        instance, instance.grid, require_complete=False, enforce_givens=False
    )
    if not valid_partial:
        errors.extend(partial_errors)
    return not errors, errors


def validate_solution(
    instance: PuzzleInstance,
    grid: list[list[int]],
    *,
    require_complete: bool = True,
    enforce_givens: bool = True,
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    n = instance.size
    if len(grid) != n or any(len(row) != n for row in grid):
        return False, ["Candidate grid must be N x N."]

    for r in range(n):
        for c in range(n):
            value = grid[r][c]
            if not isinstance(value, int) or value < 0 or value > n:
                errors.append(f"Cell ({r + 1},{c + 1}) has invalid value {value!r}.")
            if require_complete and value == 0:
                errors.append(f"Cell ({r + 1},{c + 1}) is unassigned.")
            if enforce_givens and instance.grid[r][c] != 0 and value != instance.grid[r][c]:
                errors.append(f"Cell ({r + 1},{c + 1}) violates given value {instance.grid[r][c]}.")

    for r in range(n):
        row_values = [value for value in grid[r] if value != 0]
        if len(row_values) != len(set(row_values)):
            errors.append(f"Row {r + 1} repeats a value.")
        if require_complete and sorted(row_values) != list(range(1, n + 1)):
            errors.append(f"Row {r + 1} is not a permutation of 1..{n}.")

    for c in range(n):
        col_values = [grid[r][c] for r in range(n) if grid[r][c] != 0]
        if len(col_values) != len(set(col_values)):
            errors.append(f"Column {c + 1} repeats a value.")
        if require_complete and sorted(col_values) != list(range(1, n + 1)):
            errors.append(f"Column {c + 1} is not a permutation of 1..{n}.")

    for r in range(n):
        for c in range(n - 1):
            left = grid[r][c]
            right = grid[r][c + 1]
            rel = instance.horizontal_constraints[r][c]
            if left == 0 or right == 0 or rel == 0:
                continue
            if rel == 1 and not left < right:
                errors.append(f"Horizontal inequality at ({r + 1},{c + 1}) requires left < right.")
            if rel == -1 and not left > right:
                errors.append(f"Horizontal inequality at ({r + 1},{c + 1}) requires left > right.")

    for r in range(n - 1):
        for c in range(n):
            top = grid[r][c]
            bottom = grid[r + 1][c]
            rel = instance.vertical_constraints[r][c]
            if top == 0 or bottom == 0 or rel == 0:
                continue
            if rel == 1 and not top < bottom:
                errors.append(f"Vertical inequality at ({r + 1},{c + 1}) requires top < bottom.")
            if rel == -1 and not top > bottom:
                errors.append(f"Vertical inequality at ({r + 1},{c + 1}) requires top > bottom.")

    return not errors, errors
