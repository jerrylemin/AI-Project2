from futoshiki.logic.cnf import (
    Exists,
    ForAll,
    Implies,
    PredicateExpr,
    drop_universal_quantifiers,
    skolemize,
    standardize_variables,
    to_cnf_clauses,
)


def test_cnf_pipeline_eliminates_simple_implication() -> None:
    clauses = to_cnf_clauses(Implies(PredicateExpr("A", ("x",)), PredicateExpr("B", ("x",))))
    assert clauses == [["~A(x)", "B(x)"]]


def test_skolemization_keeps_universal_dependencies() -> None:
    formula = ForAll(("x",), Exists(("y",), PredicateExpr("P", ("x", "y"))))
    standardized = standardize_variables(formula)
    skolemized = drop_universal_quantifiers(skolemize(standardized))
    assert skolemized == PredicateExpr("P", ("x_0", "Sk0(x_0)"))
