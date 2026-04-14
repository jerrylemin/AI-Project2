from futoshiki.logic.cnf import Implies, PredicateExpr, to_cnf_clauses


def test_cnf_pipeline_eliminates_simple_implication() -> None:
    clauses = to_cnf_clauses(Implies(PredicateExpr("A", ("x",)), PredicateExpr("B", ("x",))))
    assert clauses == [["~A(x)", "B(x)"]]
