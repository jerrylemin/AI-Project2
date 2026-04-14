# Manual 4x4 FOL Derivation

This section uses `inputs/input-01.txt`.

## Instance

```text
4
1, 0, 0, 4
0, 3, 4, 0
0, 4, 1, 0
4, 0, 0, 3
1, 1, 1
1, 1, -1
1, -1, 1
-1, 1, 1
1, 1, 1, -1
1, 1, -1, 1
1, -1, 1, 1
```

Indices range over `1..4`.

## Vocabulary

- `Val(i,j,v)`: cell `(i,j)` has value `v`
- `Given(i,j,v)`: puzzle provides `v` at `(i,j)`
- `LessH(i,j)`: `(i,j) < (i,j+1)`
- `GreaterH(i,j)`: `(i,j) > (i,j+1)`
- `LessV(i,j)`: `(i,j) < (i+1,j)`
- `GreaterV(i,j)`: `(i,j) > (i+1,j)`
- `Less(v1,v2)`: arithmetic order over domain values

Auxiliary finite-domain predicates:

- `Possible(i,j,v)`
- `NotVal(i,j,v)`
- `Assigned(i,j)`

## Instance facts

Givens:

- `Given(1,1,1)`
- `Given(1,4,4)`
- `Given(2,2,3)`
- `Given(2,3,4)`
- `Given(3,2,4)`
- `Given(3,3,1)`
- `Given(4,1,4)`
- `Given(4,4,3)`

Horizontal facts:

- `LessH(1,1)`, `LessH(1,2)`, `LessH(1,3)`
- `LessH(2,1)`, `LessH(2,2)`, `GreaterH(2,3)`
- `LessH(3,1)`, `GreaterH(3,2)`, `LessH(3,3)`
- `GreaterH(4,1)`, `LessH(4,2)`, `LessH(4,3)`

Vertical facts:

- `LessV(1,1)`, `LessV(1,2)`, `LessV(1,3)`, `GreaterV(1,4)`
- `LessV(2,1)`, `LessV(2,2)`, `GreaterV(2,3)`, `LessV(2,4)`
- `LessV(3,1)`, `GreaterV(3,2)`, `LessV(3,3)`, `LessV(3,4)`

Order facts:

- `Less(1,2)`, `Less(1,3)`, `Less(1,4)`
- `Less(2,3)`, `Less(2,4)`
- `Less(3,4)`

## Axiom schemas

### A1. At least one value per cell

`forall i forall j exists v Val(i,j,v)`

For cell `(1,2)`:

`exists v Val(1,2,v)`

Skolemized over universal `i,j`:

`Val(1,2,Sk_12)`

For finite grounding in this project, A1 is encoded more conveniently as:

`Val(1,2,1) or Val(1,2,2) or Val(1,2,3) or Val(1,2,4)`

The same clause family is generated for every cell.

### A2. At most one value per cell

`forall i forall j forall v1 forall v2 ((Val(i,j,v1) and Val(i,j,v2)) -> v1=v2)`

Pairwise finite-domain form for cell `(1,2)`:

- `not Val(1,2,1) or not Val(1,2,2)`
- `not Val(1,2,1) or not Val(1,2,3)`
- `not Val(1,2,1) or not Val(1,2,4)`
- `not Val(1,2,2) or not Val(1,2,3)`
- `not Val(1,2,2) or not Val(1,2,4)`
- `not Val(1,2,3) or not Val(1,2,4)`

### A3. Row uniqueness

`forall i forall j1 forall j2 forall v ((j1 != j2 and Val(i,j1,v)) -> not Val(i,j2,v))`

Ground sample for row 1, value 1:

- `not Val(1,1,1) or not Val(1,2,1)`
- `not Val(1,1,1) or not Val(1,3,1)`
- `not Val(1,1,1) or not Val(1,4,1)`

### A4. Column uniqueness

`forall j forall i1 forall i2 forall v ((i1 != i2 and Val(i1,j,v)) -> not Val(i2,j,v))`

Ground sample for column 1, value 4:

- `not Val(1,1,4) or not Val(2,1,4)`
- `not Val(1,1,4) or not Val(3,1,4)`
- `not Val(1,1,4) or not Val(4,1,4)`

### A5. Givens

`forall i forall j forall v (Given(i,j,v) -> Val(i,j,v))`

Example:

- `Given(1,1,1) -> Val(1,1,1)`
- CNF: `not Given(1,1,1) or Val(1,1,1)`

Since `Given(1,1,1)` is a fact, unit propagation yields `Val(1,1,1)`.

### A6. Horizontal inequalities

`forall i forall j forall v1 forall v2 ((LessH(i,j) and Val(i,j,v1) and Val(i,j+1,v2)) -> Less(v1,v2))`

Example at `(1,1)` where `LessH(1,1)`:

- `not LessH(1,1) or not Val(1,1,1) or not Val(1,2,1) or Less(1,1)`
- `not LessH(1,1) or not Val(1,1,1) or not Val(1,2,2) or Less(1,2)`
- ...

Using the extensional order facts, any pair with `v1 >= v2` becomes a forbidden clause:

- `not Val(1,1,1) or not Val(1,2,1)`
- `not Val(1,1,2) or not Val(1,2,1)`
- `not Val(1,1,3) or not Val(1,2,2)`
- ...

### A7. Vertical inequalities

`forall i forall j forall v1 forall v2 ((LessV(i,j) and Val(i,j,v1) and Val(i+1,j,v2)) -> Less(v1,v2))`

At `(1,1)` with `LessV(1,1)` the forbidden pairs are all `v_top >= v_bottom`:

- `not Val(1,1,1) or not Val(2,1,1)`
- `not Val(1,1,2) or not Val(2,1,1)`
- `not Val(1,1,4) or not Val(2,1,3)`
- ...

For `GreaterV(1,4)` the forbidden pairs are all `v_top <= v_bottom`.

### A8. Domain restriction

Finite grounding makes A8 implicit because only variables `Val(i,j,1)` through `Val(i,j,4)` are created.

### A9. Exactly-one convenience

For each cell the direct CNF encoding uses:

- one at-least-one clause
- six at-most-one clauses

For 16 cells this contributes:

- `16` at-least-one clauses
- `16 * 6 = 96` at-most-one clauses

## Quantifier elimination and Skolemization walkthrough

Take A1 for a generic cell:

1. Original:

`forall i forall j exists v Val(i,j,v)`

2. Standardized:

`forall i_1 forall j_1 exists v_1 Val(i_1,j_1,v_1)`

3. Skolemized:

`forall i_1 forall j_1 Val(i_1,j_1,Sk(i_1,j_1))`

4. Drop universal quantifiers:

`Val(i_1,j_1,Sk(i_1,j_1))`

5. For the finite domain encoder used in code, replace the Skolem witness by explicit disjunction:

`Val(i,j,1) or Val(i,j,2) or Val(i,j,3) or Val(i,j,4)`

Take A5:

1. Original:

`forall i forall j forall v (Given(i,j,v) -> Val(i,j,v))`

2. Remove implication:

`forall i forall j forall v (not Given(i,j,v) or Val(i,j,v))`

3. Already in NNF and CNF.

4. Drop universal quantifiers:

`not Given(i,j,v) or Val(i,j,v)`

5. Ground example:

`not Given(2,2,3) or Val(2,2,3)`

## Clause families for the 4x4 instance

Let `X_ijv` denote `Val(i,j,v)`.

Counts:

- cell exactly-one clauses: `112`
- row uniqueness clauses: `96`
- column uniqueness clauses: `96`
- givens: `8`
- horizontal inequality clauses: `120`
- vertical inequality clauses: `120`

Total: `552` clauses

This matches the automatic encoder statistics for `input-01.txt`.

## Sample derivation chain

From the givens:

- `Given(1,1,1)`
- `Given(1,4,4)`

Using A5:

- `Val(1,1,1)`
- `Val(1,4,4)`

Using row uniqueness:

- `NotVal(1,2,1)`, `NotVal(1,3,1)`, `NotVal(1,4,1)`
- `NotVal(1,1,4)`, `NotVal(1,2,4)`, `NotVal(1,3,4)`

Using `LessH(1,1)` and `Val(1,1,1)`:

- `NotVal(1,2,1)`

Using `LessH(1,3)` and `Val(1,4,4)` backwards as a forbidden pair:

- `NotVal(1,3,4)`

Accumulating row and inequality restrictions eventually leaves:

- `Val(1,2,2)`
- `Val(1,3,3)`

The same process propagates through rows and columns until the full solution is forced:

```text
1 2 3 4
2 3 4 1
3 4 1 2
4 1 2 3
```
