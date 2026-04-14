from futoshiki.logic.backward_chaining import BackwardChainer, extract_constant_answers
from futoshiki.logic.predicates import atom
from futoshiki.logic.rules import LogicProgram
from futoshiki.logic.terms import var
from futoshiki.parser import parse_file
from futoshiki.propagation import initialize_domains, propagate
from futoshiki.solvers.logic_backward_solver import LogicBackwardSolver, build_snapshot_program


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


def test_snapshot_program_proves_val_via_rule_not_fact() -> None:
    instance = parse_file("inputs/input-01.txt")
    domains = propagate(instance, initialize_domains(instance), use_forward_checking=False, use_ac3=True).domains
    program = build_snapshot_program(instance, domains)
    assert atom("Val", 1, 2, 2) not in program.facts

    query_var = var("V")
    result = BackwardChainer(program).ask(atom("Val", 1, 2, query_var))
    answers = [constant.value for constant in extract_constant_answers(result, query_var)]
    assert answers == [2]
