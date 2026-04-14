from futoshiki.formatter import format_input_instance, format_instance
from futoshiki.parser import parse_file, parse_text


def test_input_format_roundtrip() -> None:
    instance = parse_file("inputs/input-02.txt")
    text = format_input_instance(instance)
    reparsed = parse_text(text)
    assert reparsed.size == instance.size
    assert reparsed.grid == instance.grid
    assert reparsed.horizontal_constraints == instance.horizontal_constraints
    assert reparsed.vertical_constraints == instance.vertical_constraints


def test_output_format_keeps_symbols() -> None:
    instance = parse_file("inputs/input-01.txt")
    text = format_instance(instance, grid=[[1, 2, 3, 4], [2, 3, 4, 1], [3, 4, 1, 2], [4, 1, 2, 3]])
    assert "<" in text
    assert "v" in text or "^" in text
