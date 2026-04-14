"""Backtracking solver with MRV, degree heuristic, forward checking, and AC-3."""

from __future__ import annotations

from ..heuristics import order_domain_values, select_unassigned_cell
from ..models import DomainMap, PuzzleInstance, SolveTraceEvent
from ..propagation import clone_domains, domains_to_grid, initialize_domains, propagate
from ..utils import domain_size_sum
from .base import BaseSolver, SolverConfig


class BacktrackingSolver(BaseSolver):
    def __init__(self, config: SolverConfig | None = None) -> None:
        super().__init__("backtracking", config)

    def solve(
        self,
        instance: PuzzleInstance,
        *,
        initial_domains: DomainMap | None = None,
    ):
        domains = clone_domains(initial_domains) if initial_domains is not None else initialize_domains(instance)
        self.stats.peak_domain_size_sum = max(self.stats.peak_domain_size_sum, domain_size_sum(domains))
        with self._time_solve() as timer:
            initial = propagate(
                instance,
                domains,
                use_forward_checking=False,
                use_ac3=self.config.use_ac3,
                trace_enabled=True,
            )
            self.trace.extend(initial.trace)
            self.stats.propagations += 1
            self.stats.contradictions += initial.contradictions
            self.stats.peak_domain_size_sum = max(
                self.stats.peak_domain_size_sum,
                domain_size_sum(initial.domains),
            )
            if not initial.consistent:
                self.stats.runtime_ms = timer.elapsed_ms
                self.stats.consistent = False
                return self._make_result(instance, None, message="Initial propagation found contradiction.")

            solution_domains = self._search(instance, initial.domains, depth=0)
        self.stats.runtime_ms = timer.elapsed_ms
        if solution_domains is None:
            return self._make_result(instance, None, message="No solution found.", domains=initial.domains)
        return self._make_result(
            instance,
            domains_to_grid(instance, solution_domains),
            message="Solved.",
            domains=solution_domains,
        )

    def _search(self, instance: PuzzleInstance, domains: DomainMap, depth: int) -> DomainMap | None:
        self.stats.recursive_calls += 1
        self.stats.depth = max(self.stats.depth, depth)
        self.stats.peak_frontier = max(self.stats.peak_frontier, depth + 1)
        self.stats.peak_domain_size_sum = max(self.stats.peak_domain_size_sum, domain_size_sum(domains))
        if all(len(values) == 1 for values in domains.values()):
            return domains

        cell = (
            select_unassigned_cell(instance, domains, use_degree=self.config.use_degree)
            if self.config.use_mrv
            else next(cell for cell, values in domains.items() if len(values) > 1)
        )
        self.stats.nodes_expanded += 1
        for value in order_domain_values(domains, cell):
            self.stats.solved_by_search = True
            next_domains = clone_domains(domains)
            next_domains[cell] = {value}
            self.trace.append(
                SolveTraceEvent(
                    category="branch",
                    message=f"Backtracking assigns ({cell[0] + 1},{cell[1] + 1}) = {value}",
                    payload={"cell": cell, "value": value, "depth": depth},
                )
            )
            result = propagate(
                instance,
                next_domains,
                assigned_cell=cell,
                use_forward_checking=self.config.use_forward_checking,
                use_ac3=self.config.use_ac3,
                trace_enabled=True,
            )
            self.trace.extend(result.trace)
            self.stats.propagations += 1
            self.stats.contradictions += result.contradictions
            self.stats.peak_domain_size_sum = max(
                self.stats.peak_domain_size_sum,
                domain_size_sum(result.domains),
            )
            if not result.consistent:
                continue
            solved = self._search(instance, result.domains, depth + 1)
            if solved is not None:
                return solved
        return None
