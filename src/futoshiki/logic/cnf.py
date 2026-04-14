"""CNF conversion utilities and direct propositional encoding for Futoshiki."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from ..models import PuzzleInstance


@dataclass(frozen=True, slots=True)
class PredicateExpr:
    name: str
    args: tuple[str, ...]

    def __str__(self) -> str:
        return f"{self.name}({', '.join(self.args)})"


@dataclass(frozen=True, slots=True)
class Not:
    operand: object


@dataclass(frozen=True, slots=True)
class And:
    operands: tuple[object, ...]


@dataclass(frozen=True, slots=True)
class Or:
    operands: tuple[object, ...]


@dataclass(frozen=True, slots=True)
class Implies:
    left: object
    right: object


@dataclass(frozen=True, slots=True)
class ForAll:
    variables: tuple[str, ...]
    body: object


@dataclass(frozen=True, slots=True)
class Exists:
    variables: tuple[str, ...]
    body: object


Formula = PredicateExpr | Not | And | Or | Implies | ForAll | Exists


def eliminate_implications(formula: Formula) -> Formula:
    if isinstance(formula, Implies):
        return Or((Not(eliminate_implications(formula.left)), eliminate_implications(formula.right)))
    if isinstance(formula, And):
        return And(tuple(eliminate_implications(item) for item in formula.operands))
    if isinstance(formula, Or):
        return Or(tuple(eliminate_implications(item) for item in formula.operands))
    if isinstance(formula, Not):
        return Not(eliminate_implications(formula.operand))
    if isinstance(formula, (ForAll, Exists)):
        return type(formula)(formula.variables, eliminate_implications(formula.body))
    return formula


def move_negation_inwards(formula: Formula) -> Formula:
    if isinstance(formula, Not):
        operand = formula.operand
        if isinstance(operand, Not):
            return move_negation_inwards(operand.operand)
        if isinstance(operand, And):
            return Or(tuple(move_negation_inwards(Not(item)) for item in operand.operands))
        if isinstance(operand, Or):
            return And(tuple(move_negation_inwards(Not(item)) for item in operand.operands))
        if isinstance(operand, ForAll):
            return Exists(operand.variables, move_negation_inwards(Not(operand.body)))
        if isinstance(operand, Exists):
            return ForAll(operand.variables, move_negation_inwards(Not(operand.body)))
        return formula
    if isinstance(formula, And):
        return And(tuple(move_negation_inwards(item) for item in formula.operands))
    if isinstance(formula, Or):
        return Or(tuple(move_negation_inwards(item) for item in formula.operands))
    if isinstance(formula, (ForAll, Exists)):
        return type(formula)(formula.variables, move_negation_inwards(formula.body))
    return formula


def standardize_variables(formula: Formula, counter: list[int] | None = None) -> Formula:
    counter = [0] if counter is None else counter
    if isinstance(formula, ForAll):
        mapping = {var: f"{var}_{counter[0] + idx}" for idx, var in enumerate(formula.variables)}
        counter[0] += len(formula.variables)
        return ForAll(tuple(mapping.values()), _rename_formula(formula.body, mapping))
    if isinstance(formula, Exists):
        mapping = {var: f"{var}_{counter[0] + idx}" for idx, var in enumerate(formula.variables)}
        counter[0] += len(formula.variables)
        return Exists(tuple(mapping.values()), _rename_formula(formula.body, mapping))
    if isinstance(formula, And):
        return And(tuple(standardize_variables(item, counter) for item in formula.operands))
    if isinstance(formula, Or):
        return Or(tuple(standardize_variables(item, counter) for item in formula.operands))
    if isinstance(formula, Not):
        return Not(standardize_variables(formula.operand, counter))
    return formula


def _rename_formula(formula: Formula, mapping: dict[str, str]) -> Formula:
    if isinstance(formula, PredicateExpr):
        return PredicateExpr(formula.name, tuple(mapping.get(arg, arg) for arg in formula.args))
    if isinstance(formula, Not):
        return Not(_rename_formula(formula.operand, mapping))
    if isinstance(formula, And):
        return And(tuple(_rename_formula(item, mapping) for item in formula.operands))
    if isinstance(formula, Or):
        return Or(tuple(_rename_formula(item, mapping) for item in formula.operands))
    if isinstance(formula, Implies):
        return Implies(_rename_formula(formula.left, mapping), _rename_formula(formula.right, mapping))
    if isinstance(formula, ForAll):
        return ForAll(formula.variables, _rename_formula(formula.body, mapping))
    if isinstance(formula, Exists):
        return Exists(formula.variables, _rename_formula(formula.body, mapping))
    return formula


def skolemize(formula: Formula, skolem_counter: list[int] | None = None) -> Formula:
    skolem_counter = [0] if skolem_counter is None else skolem_counter
    if isinstance(formula, Exists):
        mapping = {}
        for variable in formula.variables:
            mapping[variable] = f"Sk{skolem_counter[0]}"
            skolem_counter[0] += 1
        return skolemize(_rename_formula(formula.body, mapping), skolem_counter)
    if isinstance(formula, ForAll):
        return ForAll(formula.variables, skolemize(formula.body, skolem_counter))
    if isinstance(formula, And):
        return And(tuple(skolemize(item, skolem_counter) for item in formula.operands))
    if isinstance(formula, Or):
        return Or(tuple(skolemize(item, skolem_counter) for item in formula.operands))
    if isinstance(formula, Not):
        return Not(skolemize(formula.operand, skolem_counter))
    return formula


def drop_universal_quantifiers(formula: Formula) -> Formula:
    if isinstance(formula, ForAll):
        return drop_universal_quantifiers(formula.body)
    if isinstance(formula, And):
        return And(tuple(drop_universal_quantifiers(item) for item in formula.operands))
    if isinstance(formula, Or):
        return Or(tuple(drop_universal_quantifiers(item) for item in formula.operands))
    if isinstance(formula, Not):
        return Not(drop_universal_quantifiers(formula.operand))
    return formula


def distribute_or_over_and(formula: Formula) -> Formula:
    if isinstance(formula, Or):
        if len(formula.operands) == 2:
            left = distribute_or_over_and(formula.operands[0])
            right = distribute_or_over_and(formula.operands[1])
            if isinstance(left, And):
                return And(tuple(distribute_or_over_and(Or((item, right))) for item in left.operands))
            if isinstance(right, And):
                return And(tuple(distribute_or_over_and(Or((left, item))) for item in right.operands))
            return Or((left, right))
        current = distribute_or_over_and(formula.operands[0])
        for operand in formula.operands[1:]:
            current = distribute_or_over_and(Or((current, distribute_or_over_and(operand))))
        return current
    if isinstance(formula, And):
        return And(tuple(distribute_or_over_and(item) for item in formula.operands))
    return formula


def extract_clauses(formula: Formula) -> list[list[str]]:
    if isinstance(formula, And):
        clauses: list[list[str]] = []
        for operand in formula.operands:
            clauses.extend(extract_clauses(operand))
        return clauses
    if isinstance(formula, Or):
        clause: list[str] = []
        for operand in formula.operands:
            clause.extend(extract_clauses(operand)[0])
        return [clause]
    if isinstance(formula, Not) and isinstance(formula.operand, PredicateExpr):
        return [[f"~{formula.operand}"]]
    if isinstance(formula, PredicateExpr):
        return [[str(formula)]]
    return [[str(formula)]]


def to_cnf_clauses(formula: Formula) -> list[list[str]]:
    """Run the textbook CNF conversion steps used in the report."""

    no_implication = eliminate_implications(formula)
    nnf = move_negation_inwards(no_implication)
    standardized = standardize_variables(nnf)
    skolemized = skolemize(standardized)
    quantifier_free = drop_universal_quantifiers(skolemized)
    cnf_formula = distribute_or_over_and(quantifier_free)
    return extract_clauses(cnf_formula)


@dataclass(slots=True)
class CNFEncoding:
    variable_ids: dict[str, int]
    clauses: list[list[int]]

    @property
    def num_variables(self) -> int:
        return len(self.variable_ids)

    @property
    def num_clauses(self) -> int:
        return len(self.clauses)


def encode_instance_to_cnf(instance: PuzzleInstance) -> CNFEncoding:
    n = instance.size
    variables: dict[str, int] = {}
    clauses: list[list[int]] = []

    def var_id(i: int, j: int, v: int) -> int:
        key = f"Val_{i}_{j}_{v}"
        if key not in variables:
            variables[key] = len(variables) + 1
        return variables[key]

    for i in range(1, n + 1):
        for j in range(1, n + 1):
            clauses.append([var_id(i, j, v) for v in range(1, n + 1)])
            for v1, v2 in combinations(range(1, n + 1), 2):
                clauses.append([-var_id(i, j, v1), -var_id(i, j, v2)])

    for i in range(1, n + 1):
        for v in range(1, n + 1):
            for j1, j2 in combinations(range(1, n + 1), 2):
                clauses.append([-var_id(i, j1, v), -var_id(i, j2, v)])

    for j in range(1, n + 1):
        for v in range(1, n + 1):
            for i1, i2 in combinations(range(1, n + 1), 2):
                clauses.append([-var_id(i1, j, v), -var_id(i2, j, v)])

    for r in range(n):
        for c in range(n):
            if instance.grid[r][c] != 0:
                clauses.append([var_id(r + 1, c + 1, instance.grid[r][c])])

    for r in range(n):
        for c in range(n - 1):
            rel = instance.horizontal_constraints[r][c]
            if rel == 0:
                continue
            for left in range(1, n + 1):
                for right in range(1, n + 1):
                    if rel == 1 and left >= right:
                        clauses.append([-var_id(r + 1, c + 1, left), -var_id(r + 1, c + 2, right)])
                    if rel == -1 and left <= right:
                        clauses.append([-var_id(r + 1, c + 1, left), -var_id(r + 1, c + 2, right)])

    for r in range(n - 1):
        for c in range(n):
            rel = instance.vertical_constraints[r][c]
            if rel == 0:
                continue
            for top in range(1, n + 1):
                for bottom in range(1, n + 1):
                    if rel == 1 and top >= bottom:
                        clauses.append([-var_id(r + 1, c + 1, top), -var_id(r + 2, c + 1, bottom)])
                    if rel == -1 and top <= bottom:
                        clauses.append([-var_id(r + 1, c + 1, top), -var_id(r + 2, c + 1, bottom)])

    return CNFEncoding(variables, clauses)


def assignment_from_grid(instance: PuzzleInstance, grid: list[list[int]]) -> dict[int, bool]:
    encoding = encode_instance_to_cnf(instance)
    assignment: dict[int, bool] = {var_id: False for var_id in encoding.variable_ids.values()}
    for r in range(instance.size):
        for c in range(instance.size):
            value = grid[r][c]
            assignment[encoding.variable_ids[f"Val_{r + 1}_{c + 1}_{value}"]] = True
    return assignment


def satisfies_cnf(encoding: CNFEncoding, assignment: dict[int, bool]) -> bool:
    for clause in encoding.clauses:
        if not any((lit > 0 and assignment.get(lit, False)) or (lit < 0 and not assignment.get(-lit, False)) for lit in clause):
            return False
    return True
