"""Text formatting helpers for CSV inputs and readable solved outputs."""

from __future__ import annotations

from .models import PuzzleInstance

HORIZONTAL_OUT = {0: ".", 1: "<", -1: ">"}
VERTICAL_OUT = {0: ".", 1: "v", -1: "^"}


def format_input_grid(
    grid: list[list[int]],
    horizontal_constraints: list[list[int]],
    vertical_constraints: list[list[int]],
) -> str:
    size = len(grid)
    lines: list[str] = [str(size)]
    lines.extend(", ".join(str(value) for value in row) for row in grid)
    lines.extend(", ".join(str(value) for value in row) for row in horizontal_constraints)
    lines.extend(", ".join(str(value) for value in row) for row in vertical_constraints)
    return "\n".join(lines)


def format_input_instance(instance: PuzzleInstance, *, grid: list[list[int]] | None = None) -> str:
    return format_input_grid(
        grid if grid is not None else instance.grid,
        instance.horizontal_constraints,
        instance.vertical_constraints,
    )


def format_grid(
    grid: list[list[int]],
    horizontal_constraints: list[list[int]],
    vertical_constraints: list[list[int]],
) -> str:
    size = len(grid)
    number_width = len(str(size))
    lines: list[str] = []
    for r in range(size):
        row_tokens: list[str] = []
        for c in range(size):
            row_tokens.append(f"{grid[r][c]:>{number_width}}")
            if c < size - 1:
                symbol = {1: "<", -1: ">"}.get(horizontal_constraints[r][c], " ")
                row_tokens.append(symbol)
        lines.append(" ".join(row_tokens).rstrip())
        if r < size - 1:
            sep_tokens: list[str] = []
            for c in range(size):
                symbol = {1: "v", -1: "^"}.get(vertical_constraints[r][c], " ")
                sep_tokens.append(symbol.center(number_width))
                if c < size - 1:
                    sep_tokens.append(" ")
            lines.append(" ".join(sep_tokens).rstrip())
    return "\n".join(lines)


def format_instance(instance: PuzzleInstance, *, grid: list[list[int]] | None = None) -> str:
    return format_grid(
        grid if grid is not None else instance.grid,
        instance.horizontal_constraints,
        instance.vertical_constraints,
    )
