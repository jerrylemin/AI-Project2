"""Backward chaining with depth-first SLD resolution."""

from __future__ import annotations

from dataclasses import dataclass, field

from .predicates import Atom
from .rules import LogicProgram
from .terms import Constant, Variable
from .unification import Substitution, unify_atoms
from ..models import SolveTraceEvent


@dataclass(slots=True)
class BackwardChainingResult:
    substitutions: list[Substitution]
    goals_resolved: int
    trace: list[SolveTraceEvent] = field(default_factory=list)


class BackwardChainer:
    """Simple Prolog-like SLD resolution with loop guards."""

    def __init__(self, program: LogicProgram, *, max_depth: int = 256):
        self.program = program
        self.max_depth = max_depth
        self.goals_resolved = 0
        self.trace: list[SolveTraceEvent] = []
        self._cache: dict[str, list[Substitution]] = {}
        self._facts_by_name: dict[str, list[Atom]] = {}
        self._rules_by_head_name = {}
        for fact in program.facts:
            self._facts_by_name.setdefault(fact.name, []).append(fact)
        for rule in program.rules:
            self._rules_by_head_name.setdefault(rule.head.name, []).append(rule)

    def ask(self, query: Atom) -> BackwardChainingResult:
        self.goals_resolved = 0
        self.trace = []
        self._cache = {}
        answers = list(self._prove([query], {}, 0, set()))
        return BackwardChainingResult(answers, self.goals_resolved, self.trace)

    def _prove(
        self,
        goals: list[Atom],
        substitution: Substitution,
        depth: int,
        active_goals: set[str],
    ):
        if depth > self.max_depth:
            return
        if not goals:
            yield substitution
            return

        current = goals[0].substitute(substitution)
        rest = [goal.substitute(substitution) for goal in goals[1:]]
        goal_key = str(current)
        if not rest and goal_key in self._cache:
            for cached in self._cache[goal_key]:
                merged = dict(substitution)
                merged.update(cached)
                yield merged
            return
        if goal_key in active_goals:
            return

        self.goals_resolved += 1
        self.trace.append(
            SolveTraceEvent(
                category="bc-goal",
                message=f"Trying goal {current}",
                payload={"goal": str(current), "depth": depth},
            )
        )

        next_active = set(active_goals)
        next_active.add(goal_key)
        local_answers: list[Substitution] = []

        for fact in self._facts_by_name.get(current.name, []):
            unified = unify_atoms(current, fact, substitution)
            if unified is None:
                continue
            self.trace.append(
                SolveTraceEvent(
                    category="bc-fact",
                    message=f"Matched fact {fact}",
                    payload={"goal": str(current), "fact": str(fact)},
                )
            )
            for answer in self._prove(rest, unified, depth + 1, next_active):
                if not rest:
                    local_answers.append({key: value for key, value in answer.items() if key not in substitution})
                yield answer

        for rule in self._rules_by_head_name.get(current.name, []):
            unified = unify_atoms(current, rule.head, substitution)
            if unified is None:
                continue
            self.trace.append(
                SolveTraceEvent(
                    category="bc-rule",
                    message=f"Expanded via rule {rule.name or str(rule)}",
                    payload={"goal": str(current), "rule": str(rule)},
                )
            )
            new_goals = [body.substitute(unified) for body in rule.body] + rest
            for answer in self._prove(new_goals, unified, depth + 1, next_active):
                if not rest:
                    local_answers.append({key: value for key, value in answer.items() if key not in substitution})
                yield answer

        if not rest:
            self._cache[goal_key] = local_answers


def extract_constant_answers(result: BackwardChainingResult, variable: Variable) -> list[Constant]:
    answers: list[Constant] = []
    seen: set[object] = set()
    for substitution in result.substitutions:
        value = substitution.get(variable)
        if isinstance(value, Constant) and value.value not in seen:
            seen.add(value.value)
            answers.append(value)
    return answers
