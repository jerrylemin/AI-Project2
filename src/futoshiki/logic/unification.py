"""Unification for first-order terms and atoms."""

from __future__ import annotations

from .predicates import Atom
from .terms import Function, Term, Variable

Substitution = dict[Variable, Term]


def occurs(variable: Variable, term: Term, substitution: Substitution) -> bool:
    term = walk(term, substitution)
    if variable == term:
        return True
    if isinstance(term, Function):
        return any(occurs(variable, arg, substitution) for arg in term.args)
    return False


def walk(term: Term, substitution: Substitution) -> Term:
    while isinstance(term, Variable) and term in substitution:
        replacement = substitution[term]
        if replacement == term:
            break
        term = replacement
    return term


def unify_terms(left: Term, right: Term, substitution: Substitution | None = None) -> Substitution | None:
    subst = dict(substitution or {})
    left = walk(left, subst)
    right = walk(right, subst)

    if left == right:
        return subst
    if isinstance(left, Variable):
        if occurs(left, right, subst):
            return None
        subst[left] = right
        return subst
    if isinstance(right, Variable):
        if occurs(right, left, subst):
            return None
        subst[right] = left
        return subst
    if isinstance(left, Function) and isinstance(right, Function):
        if left.name != right.name or len(left.args) != len(right.args):
            return None
        for left_arg, right_arg in zip(left.args, right.args):
            subst = unify_terms(left_arg, right_arg, subst)
            if subst is None:
                return None
        return subst
    return None


def unify_atoms(left: Atom, right: Atom, substitution: Substitution | None = None) -> Substitution | None:
    if left.name != right.name or len(left.terms) != len(right.terms):
        return None
    subst = dict(substitution or {})
    for left_term, right_term in zip(left.terms, right.terms):
        subst = unify_terms(left_term, right_term, subst)
        if subst is None:
            return None
    return subst
