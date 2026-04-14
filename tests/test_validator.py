from futoshiki.parser import parse_file
from futoshiki.validator import validate_instance, validate_solution


def test_validate_instance_ok() -> None:
    instance = parse_file("inputs/input-03.txt")
    ok, errors = validate_instance(instance)
    assert ok, errors


def test_validate_solution_rejects_duplicate() -> None:
    instance = parse_file("inputs/input-01.txt")
    bad_grid = [[1, 1, 3, 4], [2, 3, 4, 1], [3, 4, 1, 2], [4, 2, 2, 3]]
    ok, errors = validate_solution(instance, bad_grid)
    assert not ok
    assert errors
