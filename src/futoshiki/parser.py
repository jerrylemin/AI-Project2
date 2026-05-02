"""Parsers for puzzle inputs and human-readable solved outputs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .models import PuzzleInstance


@dataclass(slots=True)
class ParsedOutput:
    grid: list[list[int]]
    horizontal_constraints: list[list[int]]
    vertical_constraints: list[list[int]]


class PuzzleFormatError(ValueError):
    """Raised when an input file does not follow the expected format."""


def _meaningful_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(stripped)
    return lines


def parse_text(text: str, *, name: str = "") -> PuzzleInstance:
    """Parse a puzzle from text.

    Assumed format:
    - first meaningful line: integer N
    - followed by N grid rows of N comma-separated integers
    - followed by N horizontal constraint rows of N-1 comma-separated integers
    - followed by N-1 vertical constraint rows of N comma-separated integers
    """

    lines = _meaningful_lines(text)
    if not lines:
        raise PuzzleFormatError("Empty puzzle text.")

    try:
        size = int(lines[0])
    except ValueError as exc:
        raise PuzzleFormatError("First line must be an integer size N.") from exc

    if size < 2:
        raise PuzzleFormatError("Puzzle size must be at least 2.")

    expected_body_lines = 3 * size - 1
    body = lines[1:]
    if len(body) != expected_body_lines:
        raise PuzzleFormatError(
            f"Expected {expected_body_lines} body lines for size {size}, got {len(body)}."
        )

    grid: list[list[int]] = []
    horizontal: list[list[int]] = []
    vertical: list[list[int]] = []

    def parse_csv_integers(line: str, expected: int, line_number: int) -> list[int]:
        tokens = [token.strip() for token in line.split(",")]
        if len(tokens) != expected:
            raise PuzzleFormatError(
                f"Line {line_number}: expected {expected} comma-separated values, got {len(tokens)}."
            )
        try:
            return [int(token) for token in tokens]
        except ValueError as exc:
            raise PuzzleFormatError(f"Line {line_number}: all values must be integers.") from exc

    for idx in range(size):
        row_values = parse_csv_integers(body[idx], size, idx + 2)
        for value in row_values:
            if value < 0 or value > size:
                raise PuzzleFormatError(f"Line {idx + 2}: cell values must be in [0,{size}].")
        grid.append(row_values)

    for offset in range(size):
        line_number = size + offset + 2
        row_constraints = parse_csv_integers(body[size + offset], size - 1, line_number)
        for rel in row_constraints:
            if rel not in {-1, 0, 1}:
                raise PuzzleFormatError(f"Line {line_number}: horizontal constraints must be -1, 0, or 1.")
        horizontal.append(row_constraints)

    for offset in range(size - 1):
        line_number = 2 * size + offset + 2
        row_constraints = parse_csv_integers(body[2 * size + offset], size, line_number)
        for rel in row_constraints:
            if rel not in {-1, 0, 1}:
                raise PuzzleFormatError(f"Line {line_number}: vertical constraints must be -1, 0, or 1.")
        vertical.append(row_constraints)

    return PuzzleInstance(
        size=size,
        grid=grid,
        horizontal_constraints=horizontal,
        vertical_constraints=vertical,
        name=name,
    )


def parse_file(path: str | Path) -> PuzzleInstance:
    puzzle = parse_text(Path(path).read_text(encoding="utf-8"), name=Path(path).stem)
    puzzle.source_path = Path(path)
    return puzzle


def parse_output_grid(text: str, size: int) -> list[list[int]]:
    """Parse a solved output board.

    The output format is human-readable: solved rows interleaved with inequality symbols.
    Only the solved row numbers are extracted here; inequality symbols are kept for readability
    but are not needed for validation because the original input file already contains them.
    """

    return parse_output(text, size).grid


def parse_output(text: str, size: int) -> ParsedOutput:
    """Parse the readable output board, including inequality symbols."""

    lines = [line.rstrip("\n\r") for line in text.splitlines() if not line.lstrip().startswith("#")]
    expected_lines = 2 * size - 1
    if len(lines) != expected_lines:
        raise PuzzleFormatError(
            f"Expected {expected_lines} output lines for size {size}, got {len(lines)}."
        )

    grid: list[list[int]] = []
    horizontal: list[list[int]] = []
    vertical: list[list[int]] = []
    number_width = len(str(size))
    for row_idx in range(size):
        line = lines[2 * row_idx]
        matches = list(re.finditer(r"\d+", line))
        values = [int(match.group()) for match in matches]
        if len(values) != size:
            raise PuzzleFormatError(
                f"Output row {row_idx + 1}: expected {size} integers, got {len(values)}."
            )
        grid.append(values)

        h_row: list[int] = []
        for idx in range(size - 1):
            between = line[matches[idx].end() : matches[idx + 1].start()]
            if "<" in between and ">" not in between:
                h_row.append(1)
            elif ">" in between and "<" not in between:
                h_row.append(-1)
            elif "<" not in between and ">" not in between:
                h_row.append(0)
            else:
                raise PuzzleFormatError(f"Output row {row_idx + 1}: ambiguous horizontal sign.")
        horizontal.append(h_row)

        if row_idx < size - 1:
            v_line = lines[2 * row_idx + 1]
            v_row: list[int] = []
            for col in range(size):
                pos = col * (number_width + 3)
                ch = v_line[pos] if pos < len(v_line) else " "
                if ch == "v":
                    v_row.append(1)
                elif ch == "^":
                    v_row.append(-1)
                else:
                    v_row.append(0)
            vertical.append(v_row)
    return ParsedOutput(grid, horizontal, vertical)
