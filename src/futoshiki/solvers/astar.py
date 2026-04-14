"""A* solver over partial assignments with propagated domains."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field

from ..heuristics import HEURISTICS, order_domain_values, select_unassigned_cell
from ..models import DomainMap, PuzzleInstance, SolveTraceEvent
from ..propagation import clone_domains, domains_to_grid, initialize_domains, propagate
from ..utils import domain_size_sum
from .base import BaseSolver, SolverConfig


@dataclass(order=True)
class PrioritizedState:
    priority: int
    counter: int
    g_cost: int = field(compare=False)
    domains: DomainMap = field(compare=False)


class AStarSolver(BaseSolver):
    def __init__(self, config: SolverConfig | None = None) -> None:
        config = config or SolverConfig(heuristic="main")
        super().__init__("astar", config)

    def solve(
        self,
        instance: PuzzleInstance,
        *,
        initial_domains: DomainMap | None = None,
    ):
        heuristic_fn = HEURISTICS[self.config.heuristic]
        domains = clone_domains(initial_domains) if initial_domains is not None else initialize_domains(instance)
        with self._time_solve() as timer:
            initial = propagate(instance, domains, use_forward_checking=False, use_ac3=True, trace_enabled=True)
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

            queue: list[PrioritizedState] = []
            seen_best_g: dict[tuple, int] = {}
            counter = 0
            start_h = heuristic_fn(instance, initial.domains)
            heapq.heappush(queue, PrioritizedState(start_h, counter, 0, initial.domains))
            seen_best_g[_signature(initial.domains)] = 0
            self.stats.peak_open_set = 1

            while queue:
                state = heapq.heappop(queue)
                signature = _signature(state.domains)
                if signature in seen_best_g and seen_best_g[signature] < state.g_cost:
                    continue
                self.stats.nodes_expanded += 1
                self.stats.peak_domain_size_sum = max(
                    self.stats.peak_domain_size_sum, domain_size_sum(state.domains)
                )
                if all(len(values) == 1 for values in state.domains.values()):
                    self.stats.runtime_ms = timer.elapsed_ms
                    self.stats.depth = state.g_cost
                    return self._make_result(
                        instance,
                        domains_to_grid(instance, state.domains),
                        message="Solved.",
                        domains=state.domains,
                    )

                cell = select_unassigned_cell(instance, state.domains, use_degree=self.config.use_degree)
                if cell is None:
                    continue
                for value in order_domain_values(state.domains, cell):
                    self.stats.solved_by_search = True
                    next_domains = clone_domains(state.domains)
                    next_domains[cell] = {value}
                    result = propagate(
                        instance,
                        next_domains,
                        assigned_cell=cell,
                        use_forward_checking=True,
                        use_ac3=True,
                        trace_enabled=True,
                    )
                    self.trace.extend(result.trace)
                    self.stats.propagations += 1
                    self.stats.contradictions += result.contradictions
                    if not result.consistent:
                        continue
                    next_g = state.g_cost + 1
                    next_h = heuristic_fn(instance, result.domains)
                    priority = next_g + next_h
                    counter += 1
                    signature = _signature(result.domains)
                    if signature in seen_best_g and seen_best_g[signature] <= next_g:
                        continue
                    seen_best_g[signature] = next_g
                    heapq.heappush(queue, PrioritizedState(priority, counter, next_g, result.domains))
                    self.stats.peak_open_set = max(self.stats.peak_open_set, len(queue))
                    self.stats.peak_frontier = self.stats.peak_open_set
                    self.trace.append(
                        SolveTraceEvent(
                            category="astar-branch",
                            message=(
                                f"A* enqueued ({cell[0] + 1},{cell[1] + 1}) = {value} "
                                f"with g={next_g}, h={next_h}, f={priority}"
                            ),
                            payload={"cell": cell, "value": value, "g": next_g, "h": next_h, "f": priority},
                        )
                    )

        self.stats.runtime_ms = timer.elapsed_ms
        return self._make_result(instance, None, message="No solution found.")


def _signature(domains: DomainMap) -> tuple:
    return tuple((cell, tuple(sorted(values))) for cell, values in sorted(domains.items()))
