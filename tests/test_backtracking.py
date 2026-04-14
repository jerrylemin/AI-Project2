from futoshiki.parser import parse_file
from futoshiki.solvers.backtracking import BacktrackingSolver


def test_backtracking_solves_reference_instance() -> None:
    instance = parse_file("inputs/input-04.txt")
    result = BacktrackingSolver().solve(instance)
    assert result.solved
    assert result.valid
    assert result.stats.propagations >= 1
