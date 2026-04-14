"""Ground knowledge base generation for concrete puzzle instances."""

from __future__ import annotations

from .predicates import Atom, atom
from .rules import HornRule, LogicProgram
from ..models import DomainMap, PuzzleInstance
from ..propagation import initialize_domains


def build_logic_program(instance: PuzzleInstance, domains: DomainMap | None = None) -> LogicProgram:
    """Build a grounded Horn program for the given instance."""

    n = instance.size
    program = LogicProgram()
    active_domains = domains if domains is not None else initialize_domains(instance)

    for a in range(1, n + 1):
        for b in range(a + 1, n + 1):
            program.add_fact(atom("Less", a, b))

    for r in range(n):
        for c in range(n):
            i = r + 1
            j = c + 1
            value = instance.grid[r][c]
            if value != 0:
                program.add_fact(atom("Given", i, j, value))
            for v in range(1, n + 1):
                if v in active_domains[(r, c)]:
                    program.add_fact(atom("Possible", i, j, v))
                else:
                    program.add_fact(atom("NotVal", i, j, v))

    for r in range(n):
        for c in range(n - 1):
            rel = instance.horizontal_constraints[r][c]
            if rel == 1:
                program.add_fact(atom("LessH", r + 1, c + 1))
            elif rel == -1:
                program.add_fact(atom("GreaterH", r + 1, c + 1))

    for r in range(n - 1):
        for c in range(n):
            rel = instance.vertical_constraints[r][c]
            if rel == 1:
                program.add_fact(atom("LessV", r + 1, c + 1))
            elif rel == -1:
                program.add_fact(atom("GreaterV", r + 1, c + 1))

    _add_value_rules(program, n)
    _add_row_column_rules(program, n)
    _add_inequality_rules(program, instance)
    _add_contradiction_rules(program, instance)
    return program


def _add_value_rules(program: LogicProgram, n: int) -> None:
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            for v in range(1, n + 1):
                program.add_rule(HornRule(atom("Val", i, j, v), (atom("Given", i, j, v),), "given->val"))
                program.add_rule(
                    HornRule(atom("Assigned", i, j), (atom("Val", i, j, v),), "val->assigned")
                )
                program.add_rule(
                    HornRule(atom("Possible", i, j, v), (atom("Val", i, j, v),), "val->possible")
                )
                for u in range(1, n + 1):
                    if u == v:
                        continue
                    program.add_rule(
                        HornRule(atom("NotVal", i, j, u), (atom("Val", i, j, v),), "unique-cell")
                    )

                body = tuple(atom("NotVal", i, j, u) for u in range(1, n + 1) if u != v)
                program.add_rule(HornRule(atom("Val", i, j, v), body, "singleton-domain"))


def _add_row_column_rules(program: LogicProgram, n: int) -> None:
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            for v in range(1, n + 1):
                for other_j in range(1, n + 1):
                    if other_j == j:
                        continue
                    program.add_rule(
                        HornRule(atom("NotVal", i, other_j, v), (atom("Val", i, j, v),), "row-unique")
                    )
                body = tuple(atom("NotVal", i, other_j, v) for other_j in range(1, n + 1) if other_j != j)
                program.add_rule(HornRule(atom("Val", i, j, v), body, "row-singleton"))

    for j in range(1, n + 1):
        for i in range(1, n + 1):
            for v in range(1, n + 1):
                for other_i in range(1, n + 1):
                    if other_i == i:
                        continue
                    program.add_rule(
                        HornRule(atom("NotVal", other_i, j, v), (atom("Val", i, j, v),), "col-unique")
                    )
                body = tuple(atom("NotVal", other_i, j, v) for other_i in range(1, n + 1) if other_i != i)
                program.add_rule(HornRule(atom("Val", i, j, v), body, "col-singleton"))


def _add_inequality_rules(program: LogicProgram, instance: PuzzleInstance) -> None:
    n = instance.size
    for i in range(1, n + 1):
        for j in range(1, n):
            for left in range(1, n + 1):
                for right in range(1, n + 1):
                    if left < right:
                        continue
                    program.add_rule(
                        HornRule(
                            atom("NotVal", i, j + 1, right),
                            (atom("LessH", i, j), atom("Val", i, j, left)),
                            "lessh-left",
                        )
                    )
                    program.add_rule(
                        HornRule(
                            atom("NotVal", i, j, left),
                            (atom("LessH", i, j), atom("Val", i, j + 1, right)),
                            "lessh-right",
                        )
                    )
            for left in range(1, n + 1):
                for right in range(1, n + 1):
                    if left > right:
                        continue
                    program.add_rule(
                        HornRule(
                            atom("NotVal", i, j + 1, right),
                            (atom("GreaterH", i, j), atom("Val", i, j, left)),
                            "greath-left",
                        )
                    )
                    program.add_rule(
                        HornRule(
                            atom("NotVal", i, j, left),
                            (atom("GreaterH", i, j), atom("Val", i, j + 1, right)),
                            "greath-right",
                        )
                    )

    for i in range(1, n):
        for j in range(1, n + 1):
            for top in range(1, n + 1):
                for bottom in range(1, n + 1):
                    if top < bottom:
                        continue
                    program.add_rule(
                        HornRule(
                            atom("NotVal", i + 1, j, bottom),
                            (atom("LessV", i, j), atom("Val", i, j, top)),
                            "lessv-top",
                        )
                    )
                    program.add_rule(
                        HornRule(
                            atom("NotVal", i, j, top),
                            (atom("LessV", i, j), atom("Val", i + 1, j, bottom)),
                            "lessv-bottom",
                        )
                    )
            for top in range(1, n + 1):
                for bottom in range(1, n + 1):
                    if top > bottom:
                        continue
                    program.add_rule(
                        HornRule(
                            atom("NotVal", i + 1, j, bottom),
                            (atom("GreaterV", i, j), atom("Val", i, j, top)),
                            "greaterv-top",
                        )
                    )
                    program.add_rule(
                        HornRule(
                            atom("NotVal", i, j, top),
                            (atom("GreaterV", i, j), atom("Val", i + 1, j, bottom)),
                            "greaterv-bottom",
                        )
                    )


def _add_contradiction_rules(program: LogicProgram, instance: PuzzleInstance) -> None:
    n = instance.size
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            for v in range(1, n + 1):
                program.add_rule(
                    HornRule(
                        atom("Contradiction", "cell", i, j, v),
                        (atom("Val", i, j, v), atom("NotVal", i, j, v)),
                        "val-notval",
                    )
                )
            body = tuple(atom("NotVal", i, j, v) for v in range(1, n + 1))
            program.add_rule(HornRule(atom("Contradiction", "empty", i, j), body, "empty-domain"))

    for i in range(1, n + 1):
        for j1 in range(1, n + 1):
            for j2 in range(j1 + 1, n + 1):
                for v in range(1, n + 1):
                    program.add_rule(
                        HornRule(
                            atom("Contradiction", "row", i, j1, j2, v),
                            (atom("Val", i, j1, v), atom("Val", i, j2, v)),
                            "row-duplicate",
                        )
                    )

    for j in range(1, n + 1):
        for i1 in range(1, n + 1):
            for i2 in range(i1 + 1, n + 1):
                for v in range(1, n + 1):
                    program.add_rule(
                        HornRule(
                            atom("Contradiction", "col", i1, i2, j, v),
                            (atom("Val", i1, j, v), atom("Val", i2, j, v)),
                            "col-duplicate",
                        )
                    )

    for i in range(1, n + 1):
        for j in range(1, n):
            for left in range(1, n + 1):
                for right in range(1, n + 1):
                    if left < right:
                        continue
                    program.add_rule(
                        HornRule(
                            atom("Contradiction", "lessh", i, j, left, right),
                            (atom("LessH", i, j), atom("Val", i, j, left), atom("Val", i, j + 1, right)),
                            "lessh-contradiction",
                        )
                    )
                    if left > right:
                        continue
                    program.add_rule(
                        HornRule(
                            atom("Contradiction", "greath", i, j, left, right),
                            (atom("GreaterH", i, j), atom("Val", i, j, left), atom("Val", i, j + 1, right)),
                            "greath-contradiction",
                        )
                    )

    for i in range(1, n):
        for j in range(1, n + 1):
            for top in range(1, n + 1):
                for bottom in range(1, n + 1):
                    if top < bottom:
                        continue
                    program.add_rule(
                        HornRule(
                            atom("Contradiction", "lessv", i, j, top, bottom),
                            (atom("LessV", i, j), atom("Val", i, j, top), atom("Val", i + 1, j, bottom)),
                            "lessv-contradiction",
                        )
                    )
                    if top > bottom:
                        continue
                    program.add_rule(
                        HornRule(
                            atom("Contradiction", "greaterv", i, j, top, bottom),
                            (atom("GreaterV", i, j), atom("Val", i, j, top), atom("Val", i + 1, j, bottom)),
                            "greaterv-contradiction",
                        )
                    )


def logic_facts_to_domains(instance: PuzzleInstance, facts: set[Atom]) -> DomainMap:
    n = instance.size
    domains = initialize_domains(instance)
    positive_vals: dict[tuple[int, int], set[int]] = {}

    for fact in facts:
        if fact.name == "Val":
            i, j, v = (term.value for term in fact.terms)
            positive_vals.setdefault((i, j), set()).add(v)
        elif fact.name == "NotVal":
            i, j, v = (term.value for term in fact.terms)
            domains[(i - 1, j - 1)].discard(v)

    for (i, j), values in positive_vals.items():
        domains[(i - 1, j - 1)] = set(values)
    return domains
