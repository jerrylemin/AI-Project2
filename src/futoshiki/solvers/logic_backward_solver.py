"""Solver driven by backward chaining queries, with optional CSP fallback."""

from __future__ import annotations

from ..logic.backward_chaining import BackwardChainer, extract_constant_answers
from ..logic.predicates import atom
from ..logic.rules import LogicProgram
from ..logic.terms import var
from ..models import DomainMap, PuzzleInstance, SolveTraceEvent
from ..propagation import clone_domains, domains_to_grid, initialize_domains, propagate
from .backtracking import BacktrackingSolver
from .base import BaseSolver, SolverConfig


class LogicBackwardSolver(BaseSolver):
    def __init__(self, config: SolverConfig | None = None) -> None:
        config = config or SolverConfig(fallback_search=True)
        super().__init__("logic-backward", config)

    def solve(
        self,
        instance: PuzzleInstance,
        *,
        initial_domains: DomainMap | None = None,
    ):
        domains = clone_domains(initial_domains) if initial_domains is not None else initialize_domains(instance)
        with self._time_solve() as timer:
            propagated = propagate(
                instance,
                domains,
                use_forward_checking=False,
                use_ac3=True,
                trace_enabled=True,
            )
            self.trace.extend(propagated.trace)
            self.stats.propagations += 1
            self.stats.contradictions += propagated.contradictions
            if not propagated.consistent:
                self.stats.runtime_ms = timer.elapsed_ms
                self.stats.consistent = False
                return self._make_result(instance, None, message="Initial propagation found contradiction.")

            domains = propagated.domains
            program = build_snapshot_program(instance, domains)
            engine = BackwardChainer(program)

            query_var = var("V")
            goals_resolved = 0
            for r in range(instance.size):
                for c in range(instance.size):
                    result = engine.ask(atom("Val", r + 1, c + 1, query_var))
                    goals_resolved += result.goals_resolved
                    self.trace.extend(result.trace)
                    answers = {constant.value for constant in extract_constant_answers(result, query_var)}
                    if len(answers) == 1:
                        domains[(r, c)] = answers
                    else:
                        possible = engine.ask(atom("Possible", r + 1, c + 1, query_var))
                        goals_resolved += possible.goals_resolved
                        self.trace.extend(possible.trace)
                        possible_answers = {constant.value for constant in extract_constant_answers(possible, query_var)}
                        if possible_answers:
                            domains[(r, c)] &= possible_answers

                    if not domains[(r, c)]:
                        self.stats.runtime_ms = timer.elapsed_ms
                        self.stats.consistent = False
                        self.stats.contradictions += 1
                        return self._make_result(instance, None, message="Backward chaining derived contradiction.")

            self.stats.rule_firings = goals_resolved
            solved_grid = domains_to_grid(instance, domains)
            if all(value != 0 for row in solved_grid for value in row):
                self.stats.runtime_ms = timer.elapsed_ms
                return self._make_result(instance, solved_grid, message="Solved by backward chaining.", domains=domains)

            self.trace.append(
                SolveTraceEvent(
                    category="logic-fallback",
                    message="Backward chaining left ambiguous cells; switching to backtracking fallback.",
                    payload={},
                )
            )

            if self.config.fallback_search:
                fallback = BacktrackingSolver(SolverConfig())
                result = fallback.solve(instance, initial_domains=domains)
                self.trace.extend(result.trace)
                self.stats.nodes_expanded += result.stats.nodes_expanded
                self.stats.recursive_calls += result.stats.recursive_calls
                self.stats.contradictions += result.stats.contradictions
                self.stats.propagations += result.stats.propagations
                self.stats.depth = max(self.stats.depth, result.stats.depth)
                self.stats.runtime_ms = timer.elapsed_ms
                return self._make_result(
                    instance,
                    result.grid,
                    message="Solved with backward chaining + fallback search." if result.solved else result.message,
                    domains=result.domains,
                    metadata={"pure_logic_complete": False},
                )

        self.stats.runtime_ms = timer.elapsed_ms
        return self._make_result(
            instance,
            None,
            message="Backward chaining incomplete and fallback disabled.",
            domains=domains,
            metadata={"pure_logic_complete": False},
        )


def build_snapshot_program(instance: PuzzleInstance, domains: DomainMap) -> LogicProgram:
    """Facts used by the BC coordinator after propagation has reduced domains."""

    program = LogicProgram()
    for r in range(instance.size):
        for c in range(instance.size):
            i = r + 1
            j = c + 1
            if instance.grid[r][c] != 0:
                program.add_fact(atom("Given", i, j, instance.grid[r][c]))
            if len(domains[(r, c)]) == 1:
                program.add_fact(atom("Val", i, j, next(iter(domains[(r, c)]))))
            for value in range(1, instance.size + 1):
                if value in domains[(r, c)]:
                    program.add_fact(atom("Possible", i, j, value))
                else:
                    program.add_fact(atom("NotVal", i, j, value))
    return program
