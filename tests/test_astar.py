from futoshiki.heuristics import heuristic_main, heuristic_weak, heuristic_zero
from futoshiki.parser import parse_file
from futoshiki.propagation import initialize_domains, propagate
from futoshiki.solvers.astar import AStarSolver
from futoshiki.solvers.base import SolverConfig


def test_astar_main_solves_reference_instance() -> None:
    instance = parse_file("inputs/input-05.txt")
    result = AStarSolver(SolverConfig(heuristic="main")).solve(instance)
    assert result.solved
    assert result.valid


def test_astar_h0_solves_reference_instance() -> None:
    instance = parse_file("inputs/input-05.txt")
    result = AStarSolver(SolverConfig(heuristic="h0")).solve(instance)
    assert result.solved


def test_astar_heuristics_are_basic_lower_bounds_after_ac3() -> None:
    instance = parse_file("inputs/input-01.txt")
    domains = propagate(instance, initialize_domains(instance), use_forward_checking=False, use_ac3=True).domains
    ambiguous = any(len(values) > 1 for values in domains.values())
    assert heuristic_zero(instance, domains) == 0
    assert heuristic_weak(instance, domains) in {0, 1}
    if ambiguous:
        assert heuristic_main(instance, domains) >= 1
    else:
        assert heuristic_main(instance, domains) == 0
