from futoshiki.logic.forward_chaining import ForwardChainer
from futoshiki.logic.predicates import atom
from futoshiki.logic.rules import HornRule, LogicProgram
from futoshiki.parser import parse_file
from futoshiki.solvers.logic_forward_solver import LogicForwardSolver


def test_logic_forward_solves_reference_instance() -> None:
    instance = parse_file("inputs/input-02.txt")
    result = LogicForwardSolver().solve(instance)
    assert result.solved
    assert result.stats.rule_firings > 0


def test_forward_chaining_derives_new_fact() -> None:
    program = LogicProgram(
        facts={atom("A", 1)},
        rules=[HornRule(atom("B", 1), (atom("A", 1),), "a-implies-b")],
    )
    result = ForwardChainer(program).run()
    assert atom("B", 1) in result.facts
    assert result.rule_firings == 1
