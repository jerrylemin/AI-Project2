"""Solver driven by forward chaining, with optional CSP fallback."""

from __future__ import annotations

from ..logic.forward_chaining import ForwardChainer
from ..logic.grounder import build_logic_program, logic_facts_to_domains
from ..models import DomainMap, PuzzleInstance, SolveTraceEvent
from ..propagation import domains_to_grid, initialize_domains
from ..utils import domain_size_sum
from .backtracking import BacktrackingSolver
from .base import BaseSolver, SolverConfig


class LogicForwardSolver(BaseSolver):
    def __init__(self, config: SolverConfig | None = None) -> None:
        config = config or SolverConfig(fallback_search=True)
        super().__init__("logic-forward", config)

    def solve(
        self,
        instance: PuzzleInstance,
        *,
        initial_domains: DomainMap | None = None,
    ):
        domains = initial_domains if initial_domains is not None else initialize_domains(instance)
        with self._time_solve() as timer:
            program = build_logic_program(instance, domains)
            fc_result = ForwardChainer(program).run()
            self.trace.extend(fc_result.trace)
            self.stats.rule_firings = fc_result.rule_firings
            self.stats.contradictions = fc_result.contradictions
            inferred_domains = logic_facts_to_domains(instance, fc_result.facts)
            self.stats.peak_domain_size_sum = domain_size_sum(inferred_domains)

            if fc_result.contradictions:
                self.stats.runtime_ms = timer.elapsed_ms
                self.stats.consistent = False
                return self._make_result(
                    instance,
                    None,
                    message="Forward chaining derived contradiction.",
                    domains=inferred_domains,
                )

            solved_grid = domains_to_grid(instance, inferred_domains)
            if all(value != 0 for row in solved_grid for value in row):
                self.stats.runtime_ms = timer.elapsed_ms
                return self._make_result(instance, solved_grid, message="Solved by forward chaining.", domains=inferred_domains)

            self.trace.append(
                SolveTraceEvent(
                    category="logic-fallback",
                    message="Pure forward chaining incomplete; switching to backtracking fallback.",
                    payload={},
                )
            )

            if self.config.fallback_search:
                fallback = BacktrackingSolver(SolverConfig())
                result = fallback.solve(instance, initial_domains=inferred_domains)
                self.trace.extend(result.trace)
                self.stats.nodes_expanded += result.stats.nodes_expanded
                self.stats.recursive_calls += result.stats.recursive_calls
                self.stats.contradictions += result.stats.contradictions
                self.stats.propagations += result.stats.propagations
                self.stats.depth = max(self.stats.depth, result.stats.depth)
                self.stats.peak_frontier = max(self.stats.peak_frontier, result.stats.peak_frontier)
                self.stats.peak_domain_size_sum = max(
                    self.stats.peak_domain_size_sum,
                    result.stats.peak_domain_size_sum,
                )
                self.stats.solved_by_search = result.stats.solved_by_search or result.stats.nodes_expanded > 0
                self.stats.runtime_ms = timer.elapsed_ms
                return self._make_result(
                    instance,
                    result.grid,
                    message="Solved with forward chaining + fallback search." if result.solved else result.message,
                    domains=result.domains,
                    metadata={"pure_logic_complete": False},
                )

        self.stats.runtime_ms = timer.elapsed_ms
        return self._make_result(
            instance,
            None,
            message="Forward chaining incomplete and fallback disabled.",
            domains=inferred_domains,
            metadata={"pure_logic_complete": False},
        )
