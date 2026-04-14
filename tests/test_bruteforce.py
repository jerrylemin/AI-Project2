from futoshiki.parser import parse_file
from futoshiki.solvers.bruteforce import BruteforceSolver


def test_bruteforce_solves_small_instance() -> None:
    instance = parse_file("inputs/input-01.txt")
    result = BruteforceSolver().solve(instance)
    assert result.solved
    assert result.valid
