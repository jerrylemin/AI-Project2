from pathlib import Path

import pytest

from futoshiki.parser import PuzzleFormatError, parse_file, parse_text


def test_parse_valid_file() -> None:
    instance = parse_file(Path("inputs/input-01.txt"))
    assert instance.size == 4
    assert instance.grid[0][0] == 1
    assert instance.horizontal_constraints[0][0] == 1
    assert instance.vertical_constraints[0][0] == 1


def test_parse_invalid_token_count() -> None:
    bad = "4\n0, 0, 0\n0, 0, 0, 0\n0, 0, 0, 0\n0, 0, 0, 0\n0, 0, 0\n0, 0, 0\n0, 0, 0\n0, 0, 0\n0, 0, 0, 0\n0, 0, 0, 0\n0, 0, 0, 0"
    with pytest.raises(PuzzleFormatError):
        parse_text(bad)
