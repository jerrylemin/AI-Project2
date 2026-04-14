"""Agenda-based forward chaining over ground Horn rules."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

from .predicates import Atom
from .rules import HornRule, LogicProgram
from ..models import SolveTraceEvent


@dataclass(slots=True)
class ForwardChainingResult:
    facts: set[Atom]
    rule_firings: int
    contradictions: int
    trace: list[SolveTraceEvent] = field(default_factory=list)


class ForwardChainer:
    """Forward chaining for ground Horn programs."""

    def __init__(self, program: LogicProgram):
        self.program = program
        self.rules_by_body_atom: dict[Atom, list[int]] = defaultdict(list)
        for idx, rule in enumerate(program.rules):
            for atom in rule.body:
                self.rules_by_body_atom[atom].append(idx)

    def run(self) -> ForwardChainingResult:
        facts = set(self.program.facts)
        agenda = deque(sorted(self.program.facts, key=str))
        fired_rules: set[int] = set()
        trace: list[SolveTraceEvent] = []
        rule_firings = 0
        contradictions = sum(1 for fact in facts if fact.name == "Contradiction")

        while agenda:
            fact = agenda.popleft()
            for rule_idx in self.rules_by_body_atom.get(fact, []):
                if rule_idx in fired_rules:
                    continue
                rule = self.program.rules[rule_idx]
                if all(body_atom in facts for body_atom in rule.body):
                    fired_rules.add(rule_idx)
                    rule_firings += 1
                    trace.append(
                        SolveTraceEvent(
                            category="rule-fire",
                            message=f"Fired {rule.name or 'rule'} => {rule.head}",
                            payload={"rule": str(rule)},
                        )
                    )
                    if rule.head not in facts:
                        facts.add(rule.head)
                        agenda.append(rule.head)
                        trace.append(
                            SolveTraceEvent(
                                category="fact",
                                message=f"Derived {rule.head}",
                                payload={"fact": str(rule.head)},
                            )
                        )
                        if rule.head.name == "Contradiction":
                            contradictions += 1

        return ForwardChainingResult(
            facts=facts,
            rule_firings=rule_firings,
            contradictions=contradictions,
            trace=trace,
        )
