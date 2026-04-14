"""Small utilities used across modules."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Iterable

from .models import Cell


def ensure_dir(path: str | Path) -> Path:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def deep_copy_grid(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def domain_size_sum(domains: dict[Cell, set[int]]) -> int:
    return sum(len(values) for values in domains.values())


def ordered_values(values: Iterable[int]) -> list[int]:
    return sorted(values)


def cell_label(cell: Cell) -> str:
    return f"({cell[0] + 1},{cell[1] + 1})"


def default_output_path(input_path: str | Path, output_dir: str | Path) -> Path:
    input_name = Path(input_path).name.replace("input", "output")
    return ensure_dir(output_dir) / input_name


def write_text(path: str | Path, content: str) -> None:
    Path(path).write_text(content, encoding="utf-8")


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


@dataclass
class Timer:
    """Context-like timer."""

    start: float = 0.0

    def __enter__(self) -> "Timer":
        self.start = perf_counter()
        return self

    def __exit__(self, *_: object) -> None:
        return None

    @property
    def elapsed_ms(self) -> float:
        return (perf_counter() - self.start) * 1000.0
