"""Horn rules and logic programs."""

from __future__ import annotations

from dataclasses import dataclass, field

from .predicates import Atom


@dataclass(frozen=True, slots=True)
class HornRule:
    head: Atom
    body: tuple[Atom, ...]
    name: str = ""

    def __str__(self) -> str:
        if not self.body:
            return str(self.head)
        return f"{self.head} :- {', '.join(str(atom) for atom in self.body)}."


@dataclass(slots=True)
class LogicProgram:
    facts: set[Atom] = field(default_factory=set)
    rules: list[HornRule] = field(default_factory=list)

    def add_fact(self, fact: Atom) -> None:
        self.facts.add(fact)

    def add_rule(self, rule: HornRule) -> None:
        self.rules.append(rule)
