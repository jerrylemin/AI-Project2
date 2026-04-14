from futoshiki.parser import parse_text
from futoshiki.propagation import initialize_domains, propagate


def test_ac3_prunes_by_inequality() -> None:
    instance = parse_text(
        "\n".join(
            [
                "4",
                "1, 0, 0, 0",
                "0, 0, 0, 0",
                "0, 0, 0, 0",
                "0, 0, 0, 0",
                "1, 0, 0",
                "0, 0, 0",
                "0, 0, 0",
                "0, 0, 0",
                "0, 0, 0, 0",
                "0, 0, 0, 0",
                "0, 0, 0, 0",
            ]
        )
    )
    result = propagate(instance, initialize_domains(instance), use_forward_checking=False, use_ac3=True)
    assert result.consistent
    assert 1 not in result.domains[(0, 1)]


def test_ac3_detects_contradictory_given_and_inequality() -> None:
    instance = parse_text(
        "\n".join(
            [
                "4",
                "4, 1, 0, 0",
                "0, 0, 0, 0",
                "0, 0, 0, 0",
                "0, 0, 0, 0",
                "1, 0, 0",
                "0, 0, 0",
                "0, 0, 0",
                "0, 0, 0",
                "0, 0, 0, 0",
                "0, 0, 0, 0",
                "0, 0, 0, 0",
            ]
        )
    )
    result = propagate(instance, initialize_domains(instance), use_forward_checking=False, use_ac3=True)
    assert not result.consistent
