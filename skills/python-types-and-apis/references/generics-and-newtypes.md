# Generics and NewTypes

Generics share a type variable across a signature. `NewType` creates a
type-checker-only nominal alias around a primitive. The two solve different
problems and combine cleanly.

## NewType: nominal wrapping with zero runtime cost

```python
from typing import NewType

UserId = NewType("UserId", int)
OrderId = NewType("OrderId", int)

def cancel(order: OrderId) -> None: ...

cancel(UserId(7))       # type-checker error: UserId is not OrderId
cancel(OrderId(7))      # ok
```

At runtime `UserId(7)` is just `7`. The wrapper exists only in the type
checker, so it has none of the cost of a real class.

Use `NewType` when:

- two distinct domains share the same primitive (`UserId` vs `OrderId`,
  `Pence` vs `Pennies`, `EmailAddress` vs raw `str`);
- the constructor names a validation step that callers must go through.

Avoid `NewType` when:

- the wrapped type needs methods or invariants beyond the primitive (use
  a frozen dataclass or `msgspec.Struct` instead);
- the constructor is bypassed elsewhere in the codebase (the nominal
  guarantee is then a lie).

## NewType from NewType

`NewType` can layer:

```python
ValidatedEmail = NewType("ValidatedEmail", EmailAddress)

def send(_: ValidatedEmail) -> None: ...
```

The layered form expresses "this email has been validated against the
schema" without making the schema runtime-visible.

## Generic functions and classes

```python
def head[T](xs: list[T]) -> T:
    return xs[0]

class Page[T]:
    def __init__(self, items: list[T], cursor: str | None) -> None:
        self.items = items
        self.cursor = cursor
```

Prefer PEP 695 inline syntax in Python 3.12+. The older
`T = TypeVar("T")` style remains valid and is required for code that must
run on 3.11 or earlier.

## Generic protocols

```python
from typing import Protocol

class SupportsClose[T](Protocol):
    def close(self) -> T: ...
```

Generic protocols describe "anything that produces a `T` when closed"
without naming a base class. They compose well with `contextlib.contextmanager`
and with adapter layers.

## Variance

Most generics in Python are invariant by default. The exceptions:

- `Sequence[T]` and `Iterable[T]` are covariant in `T`.
- `Callable[[X], R]` is contravariant in `X` and covariant in `R`.

If a generic is read-only, mark the `TypeVar` `covariant=True`; if it is
write-only, `contravariant=True`. Most user-defined generics are
invariant and should stay so.

## Common mistakes

- Using `Generic[T]` and inline `[T]` together. Pick one syntax.
- Using `NewType` for a value that requires validation, then bypassing
  the constructor. The checker stays happy; the runtime invariant is
  silently broken.
- Adding a generic parameter that no caller varies. If every call site
  uses the same concrete type, the generic is noise.
