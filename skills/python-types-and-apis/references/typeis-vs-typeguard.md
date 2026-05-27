# TypeIs vs TypeGuard

Both annotate a predicate that narrows a parameter. They differ in what the
checker can infer in the false branch.

## TypeIs (PEP 742, Python 3.13+)

`TypeIs[T]` says "this predicate is an honest equivalence". The type
checker narrows to `T` in the true branch and removes `T` from the union in
the false branch.

```python
from typing import TypeIs

def is_str(x: object) -> TypeIs[str]:
    return isinstance(x, str)

def handle(x: int | str) -> None:
    if is_str(x):
        reveal_type(x)   # str
    else:
        reveal_type(x)   # int
```

Prefer `TypeIs` whenever the predicate genuinely characterises membership
in a type (`isinstance` checks, schema validators that return the parsed
value, structural sniffs that cover the entire union).

## TypeGuard

`TypeGuard[T]` says "the true branch narrows to `T`". The false branch
carries no information; the parameter keeps its original type.

```python
from typing import TypeGuard

def is_non_empty(xs: list[str]) -> TypeGuard[list[str]]:
    return bool(xs)

def first_label(xs: list[str]) -> str | None:
    if is_non_empty(xs):
        return xs[0]      # safe, but the false branch is still list[str]
    return None
```

Use `TypeGuard` when "true" carries a refinement that "false" cannot reverse:
non-emptiness, sorted-ness, the presence of a key, having been validated
against a side schema.

## Picking between them

- The predicate is `isinstance(x, T)` or equivalent — `TypeIs[T]`.
- The predicate narrows to a refinement type that is a subtype of the
  argument but not a member of a closed union — `TypeGuard[T]`.
- The predicate could be replaced by a parser that returns `T | None` —
  prefer the parser; predicates that hide a parse cost are a red flag.

## Common mistakes

- Using `TypeIs[str]` for `len(x) > 0` — false does not eliminate `str`,
  it just says the string was empty. Reach for `TypeGuard` or a parser.
- Returning `True` from a `TypeIs` body when the runtime type is not
  actually `T`. The checker will narrow, the runtime will crash.
- Annotating a predicate `-> bool` and then expecting narrowing. Without
  `TypeIs` or `TypeGuard` the checker keeps the original type.
