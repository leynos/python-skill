---
name: python-types-and-apis
description: Use for Python typing decisions — generics, `TypeVar`, `ParamSpec`, `TypeIs` and `TypeGuard`, `NewType`, `Protocol`, `@overload`, typed kwargs, and the shape of public function signatures.
globs: ["**/pyproject.toml", "**/*.py", "**/*.pyi"]
---

# Python Types and APIs

Use this when the real question is how much of the design should be expressed
in type hints, protocols, and public signatures.

## Working stance

- Make invalid states hard to represent before adding runtime checks.
- Keep public APIs narrower than internal helper code: precise return types,
  permissive argument types.
- Prefer concrete types and named protocols over open `object` or `Any`.
- Reach for generics when a single concrete type flows through the call
  site; otherwise stay concrete.
- Treat `# type: ignore` as a code smell that needs a comment naming the
  invariant the checker cannot see.

## Decision surface

- `TypeVar`: a function or class needs to preserve a relationship between
  inputs and outputs (`def first[T](xs: list[T]) -> T`). Prefer PEP 695
  inline syntax in Python 3.12+ for new code.
- `ParamSpec`: a decorator must preserve the wrapped function's signature.
  Pair with `typing.Concatenate` when the wrapper injects a prefix
  argument.
- `TypeIs` (PEP 742): a predicate is an honest equivalence — `is_str(x)`
  returning `True` proves `x: str` in the true branch and `not str` in the
  false branch.
- `TypeGuard`: a one-way narrowing where the false branch carries no
  information (e.g. `is_non_empty(xs)`).
- `NewType`: a primitive must not be confused with another primitive of the
  same shape (`UserId = NewType("UserId", int)`).
- `Protocol`: structural typing is the right description ("anything with
  `.read()` and `.close()`") and an explicit base class would over-constrain
  callers.
- `@overload`: a function takes a closed set of argument shapes and the
  return type depends on the shape; the implementation `def` stays
  unannotated for the union and the overloads carry the precise types.
- `TypedDict` or `Unpack[TypedDict]`: kwargs are a fixed schema that needs
  type-checker enforcement at the call site.

## Red flags

- public functions accept or return `Any` without a comment naming the
  invariant the checker cannot express,
- a decorator wraps `Callable[..., Any]` and erases the wrapped signature
  (use `ParamSpec`),
- a predicate annotated `-> bool` is consumed by callers as a narrower
  (`TypeIs` or `TypeGuard` is missing),
- `isinstance` chains where a `Protocol` would express the intent,
- a `NewType` exists but its constructor is bypassed elsewhere in the
  module,
- two `bool` parameters in one signature (boolean blindness; use an enum
  or an options `TypedDict`),
- a `cast(...)` call sits next to a runtime check that would let the
  checker narrow on its own,
- generic parameters appear in the public signature for purely internal
  flexibility.

Read [paramspec-and-typevars.md](references/paramspec-and-typevars.md),
[typeis-vs-typeguard.md](references/typeis-vs-typeguard.md),
[generics-and-newtypes.md](references/generics-and-newtypes.md), and
[overloads-and-typed-kwargs.md](references/overloads-and-typed-kwargs.md)
when one of those forks becomes the main design pressure.
