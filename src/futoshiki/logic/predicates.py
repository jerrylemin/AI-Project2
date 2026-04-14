"""Predicate atoms."""

from __future__ import annotations

from dataclasses import dataclass

from .terms import Constant, Function, Term, Variable


@dataclass(frozen=True, slots=True)
class Atom:
    name: str
    terms: tuple[Term, ...]

    def substitute(self, substitution: dict[Variable, Term]) -> "Atom":
        return Atom(self.name, tuple(_substitute_term(term, substitution) for term in self.terms))

    @property
    def is_ground(self) -> bool:
        return all(not isinstance(term, Variable) for term in self.terms)

    def __str__(self) -> str:
        return f"{self.name}({', '.join(str(term) for term in self.terms)})"


def _substitute_term(term: Term, substitution: dict[Variable, Term]) -> Term:
    if isinstance(term, Variable):
        replacement = substitution.get(term, term)
        if replacement == term:
            return term
        return _substitute_term(replacement, substitution)
    if isinstance(term, Function):
        return Function(term.name, tuple(_substitute_term(arg, substitution) for arg in term.args))
    if isinstance(term, Constant):
        return term
    return term


def atom(name: str, *values: object) -> Atom:
    converted: list[Term] = []
    for value in values:
        if isinstance(value, (Variable, Constant, Function)):
            converted.append(value)
        else:
            converted.append(Constant(value))
    return Atom(name, tuple(converted))
