"""Optional CNF-based verification helper."""

from __future__ import annotations

from dataclasses import dataclass

from ..logic.cnf import assignment_from_grid, encode_instance_to_cnf, satisfies_cnf
from ..models import PuzzleInstance
from ..validator import validate_solution


@dataclass(slots=True)
class VerificationResult:
    valid_solution: bool
    valid_cnf: bool
    details: list[str]
    cnf_stats: dict[str, int]


def verify_solution_with_cnf(instance: PuzzleInstance, grid: list[list[int]]) -> VerificationResult:
    valid_solution, errors = validate_solution(instance, grid)
    encoding = encode_instance_to_cnf(instance)
    valid_cnf = False
    if valid_solution:
        assignment = assignment_from_grid(instance, grid)
        valid_cnf = satisfies_cnf(encoding, assignment)
    details = errors[:] if errors else []
    if valid_solution and not valid_cnf:
        details.append("Grid satisfies the explicit validator but not the CNF encoding.")
    return VerificationResult(
        valid_solution=valid_solution,
        valid_cnf=valid_cnf,
        details=details,
        cnf_stats={"variables": encoding.num_variables, "clauses": encoding.num_clauses},
    )
