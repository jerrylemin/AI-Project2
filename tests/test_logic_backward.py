from futoshiki.logic.backward_chaining import BackwardChainer, extract_constant_answers
from futoshiki.logic.predicates import atom
from futoshiki.logic.rules import LogicProgram
from futoshiki.logic.terms import var
from futoshiki.parser import parse_file
from futoshiki.solvers.logic_backward_solver import LogicBackwardSolver


def test_backward_chaining_answers_fact_query() -> None:
    program = LogicProgram(facts={atom("Val", 1, 1, 2)}, rules=[])
    result = BackwardChainer(program).ask(atom("Val", 1, 1, var("V")))
    answers = [constant.value for constant in extract_constant_answers(result, var("V"))]
    assert answers == [2]


def test_logic_backward_solves_reference_instance() -> None:
    instance = parse_file("inputs/input-02.txt")
    result = LogicBackwardSolver().solve(instance)
    assert result.solved
    assert result.valid
