# Project Report

## Project overview

This project implements a complete Futoshiki toolkit for CSC14003 Project 2. The repository includes a strict parser and validator, multiple solvers, logic-grounding and CNF utilities, a command-line interface, a local Streamlit UI, tests, benchmark artifacts, and a bundled dataset of ten solvable puzzle instances.

The guiding design choice is to separate:

- the puzzle model
- propagation and CSP search
- logic engines
- presentation layers such as CLI and UI

This separation keeps the academic parts honest. Forward chaining remains a real agenda-driven Horn inference engine. Backward chaining remains an SLD-style query engine. When either logic-only method is incomplete, fallback search is stated explicitly rather than hidden.

## Puzzle formalization

For a puzzle of size `N x N`:

- each row is a permutation of `1..N`
- each column is a permutation of `1..N`
- all horizontal and vertical inequalities must hold
- all given cells remain fixed

The core data model is `PuzzleInstance(size, grid, horizontal_constraints, vertical_constraints)`.

- `grid[r][c] = 0` means an empty cell
- `horizontal_constraints[r][c] = 1` means cell `(r,c) < (r,c+1)`
- `horizontal_constraints[r][c] = -1` means cell `(r,c) > (r,c+1)`
- `vertical_constraints[r][c] = 1` means cell `(r,c) < (r+1,c)`
- `vertical_constraints[r][c] = -1` means cell `(r,c) > (r+1,c)`

Input file format used by the final repository, matching the assignment screenshot:

- first line: `N`
- next `N` lines: grid rows, comma-separated
- next `N` lines: horizontal constraint rows, comma-separated with `N-1` integers each
- next `N-1` lines: vertical constraint rows, comma-separated with `N` integers each

Output file format:

- solved board only
- inequality signs kept as `<`, `>`, `^`, `v`
- readable by humans and checked by the CLI verifier against the original input signs

## FOL vocabulary and axioms

Vocabulary:

- `Val(i,j,v)`
- `Given(i,j,v)`
- `LessH(i,j)`
- `GreaterH(i,j)`
- `LessV(i,j)`
- `GreaterV(i,j)`
- `Less(v1,v2)`

Auxiliary predicates for finite-domain inference:

- `Possible(i,j,v)`
- `NotVal(i,j,v)`
- `Assigned(i,j)`
- `Contradiction(...)`

Schema axioms:

1. A1. Every cell has at least one value.  
   `forall i forall j exists v Val(i,j,v)`
2. A2. Every cell has at most one value.  
   `forall i forall j forall v1 forall v2 ((Val(i,j,v1) and Val(i,j,v2)) -> v1=v2)`
3. A3. Row uniqueness.  
   `forall i forall j1 forall j2 forall v ((j1 != j2 and Val(i,j1,v)) -> not Val(i,j2,v))`
4. A4. Column uniqueness.  
   `forall j forall i1 forall i2 forall v ((i1 != i2 and Val(i1,j,v)) -> not Val(i2,j,v))`
5. A5. Given implies value.  
   `forall i forall j forall v (Given(i,j,v) -> Val(i,j,v))`
6. A6. Horizontal inequality.  
   `forall i forall j forall v1 forall v2 ((LessH(i,j) and Val(i,j,v1) and Val(i,j+1,v2)) -> Less(v1,v2))`  
   `forall i forall j forall v1 forall v2 ((GreaterH(i,j) and Val(i,j,v1) and Val(i,j+1,v2)) -> Less(v2,v1))`
7. A7. Vertical inequality.  
   `forall i forall j forall v1 forall v2 ((LessV(i,j) and Val(i,j,v1) and Val(i+1,j,v2)) -> Less(v1,v2))`  
   `forall i forall j forall v1 forall v2 ((GreaterV(i,j) and Val(i,j,v1) and Val(i+1,j,v2)) -> Less(v2,v1))`
8. A8. Domain restriction.  
   `forall i forall j forall v (Val(i,j,v) -> v in {1..N})`
9. A9. Exactly-one convenience schema in grounded CNF.  
   At-least-one clause plus pairwise at-most-one clauses for each cell.

## Manual 4x4 derivation

The worked 4x4 derivation is separated into:

- [manual_4x4_fol.md](/C:/MEGA/co%20so%20ttnt/Project%202/reports/manual_4x4_fol.md)

That document presents the 4x4 instance, axiom schemas, representative quantifier elimination, Skolemization, and the final clause families for the instance.

## Ground KB generation

`src/futoshiki/logic/grounder.py` generates a grounded Horn program for a concrete instance.

Facts:

- `Given(i,j,v)` from the puzzle
- `LessH`, `GreaterH`, `LessV`, `GreaterV` from the inequality matrices
- `Less(a,b)` for all `1 <= a < b <= N`
- `Possible(i,j,v)` and `NotVal(i,j,v)` from the current domain snapshot

Ground rules include:

- `Given -> Val`
- `Val -> Assigned`
- `Val -> NotVal` for all conflicting values in the same cell
- `Val -> NotVal` for all conflicting row/column peers
- inequality-based pruning rules
- singleton-domain rules
- row-singleton and column-singleton rules
- contradiction rules for empty domains, duplicate fixed values, and violated inequalities

## CNF conversion

Two CNF paths are provided.

1. A symbolic FOL pipeline in `logic/cnf.py`:
   - implication elimination
   - negation normal form
   - variable standardization
   - Skolemization
   - universal quantifier dropping
   - distribution of disjunction over conjunction
   - clause extraction
2. A direct propositional encoder for concrete instances:
   - one boolean variable per `Val(i,j,v)`
   - clauses for exactly-one per cell
   - row uniqueness clauses
   - column uniqueness clauses
   - unit clauses for givens
   - binary clauses for violated inequalities

This direct encoder is used by `verify`, not by the main solvers.

## Forward chaining design

`logic/forward_chaining.py` implements a real forward chaining engine over ground Horn rules:

- agenda of newly added facts
- indexed rules by body atoms
- tracking of fired rules
- contradiction counting
- derivation trace

The solver `logic_forward_solver.py` first runs pure forward chaining. If all cells become singleton, the puzzle is solved without search. Otherwise, a clearly marked fallback to backtracking is used. The separation is explicit in logs and metadata.

## Backward chaining and SLD resolution

`logic/backward_chaining.py` implements:

- first-order terms
- unification from scratch
- depth-first SLD goal reduction
- loop guard on the active goal stack
- memoization for repeated top-level goals

`logic_backward_solver.py` uses backward chaining as a query engine over a domain snapshot after propagation. This is deliberate: the BC engine stays genuine, while the coordinator keeps runtime practical on larger instances. If the query answers do not fully determine the grid, fallback search is enabled and documented. This solver should be read as "SLD queries over a propagated snapshot plus explicit fallback", not as a claim that pure Prolog-style inference alone solves every instance.

## Brute-force

The brute-force baseline:

- scans cells row-major
- tries values `1..N`
- checks row, column, and local inequality consistency after each assignment

It exists for comparison, not as the main solver.

## Backtracking

The backtracking solver is the reference complete solver in this project.

Features:

- MRV variable ordering
- degree tiebreaker
- forward checking
- AC-3 propagation
- shared validator for final correctness

Because the bundled dataset is constraint-rich, backtracking solves all ten instances comfortably and serves as the source of the shipped `output-XX.txt` files.

## A*

The A* solver searches over propagated domain states instead of plain numeric boards.

- state: current domains
- action: assign one value to one ambiguous cell, then propagate
- `g(s)`: number of branching decisions so far
- `h0(s)=0`
- `hweak(s)=1` if any ambiguity remains, else `0`
- `hmain(s)`: number of ambiguous connected components in the active constraint graph

## Heuristic justification

`hmain` is admissible.

Reason:

1. The A* state is always propagated to an AC-3 fixed point before `hmain` is evaluated.
2. Any remaining ambiguous connected component contains at least one cell whose domain has more than one value.
3. One action assigns one cell, and disconnected components in the binary constraint graph do not propagate into each other.
4. Therefore each still-ambiguous component needs at least one future branching decision under this state/action definition.

Hence `hmain(s)` is a lower bound on the remaining number of decisions for this A* formulation, so it is admissible.

## UI design

The Streamlit UI provides:

- bundled input selection and file upload
- free-form text editor
- board rendering with inequality symbols in correct positions
- solver picker and benchmark panel
- metrics and logs
- backward-chaining query panel
- CNF statistics panel
- short theory tab

The UI is intentionally local-first and lightweight so it can be run with a single `streamlit run` command.

## Experimental setup

- Python version used in this workspace: 3.10
- Inputs: ten bundled instances across sizes 4, 5, 6, 7, and 9
- Solvers benchmarked:
  - `bruteforce`
  - `backtracking`
  - `astar-h0`
  - `astar-main`
  - `logic-forward`
  - `logic-backward`

Benchmark command:

```bash
python -m futoshiki.cli benchmark --inputs inputs --out reports/benchmark_results.csv
```

## Results and discussion

Observed summary on the bundled dataset:

- `bruteforce`: solved 10/10
- `backtracking`: solved 10/10
- `astar-h0`: solved 10/10
- `astar-main`: solved 10/10
- `logic-forward`: solved 10/10
- `logic-backward`: solved 10/10

Exact runtimes are in `reports/benchmark_results.csv` and `reports/benchmark_summary.md`. They should be regenerated after code changes because the values depend on the machine and Streamlit/cache changes do not affect CLI benchmark timing.

Interpretation:

- The bundled instances are rich in adjacency inequalities, so even naive search is pruned aggressively.
- `logic-forward` has the heaviest academic machinery because of the large grounded Horn rule base, which dominates runtime.
- `logic-backward` benefits from using backward chaining as a query layer over a propagation snapshot.
- `backtracking` remains the best general-purpose reference solver in this implementation.

## Limitations

1. The full original assignment PDF was not present in the workspace. The repository was updated to match the provided requirement screenshot for input/output formatting.
2. The bundled benchmark set is intentionally solver-friendly enough that brute-force remains fast; this is useful for classroom benchmarking but not representative of very hard Futoshiki instances.
3. Pure forward chaining and pure backward chaining are not guaranteed to finish every larger instance without search fallback.
4. The SAT/CNF path is verification-only in this project.

## How to run

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python -m futoshiki.cli solve --input inputs/input-01.txt --solver backtracking
python -m futoshiki.cli benchmark --inputs inputs --out reports/benchmark_results.csv
streamlit run src/futoshiki/ui/streamlit_app.py
```
