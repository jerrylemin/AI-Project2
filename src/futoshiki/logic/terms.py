"""Term representation for first-order logic."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Variable:
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True, slots=True)
class Constant:
    value: object

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class Function:
    name: str
    args: tuple["Term", ...]

    def __str__(self) -> str:
        return f"{self.name}({', '.join(str(arg) for arg in self.args)})"


Term = Variable | Constant | Function


def var(name: str) -> Variable:
    return Variable(name)


def const(value: object) -> Constant:
    return Constant(value)
