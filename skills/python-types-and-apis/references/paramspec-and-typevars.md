# ParamSpec and TypeVar

`TypeVar` ties an input type to an output type. `ParamSpec` ties an entire
parameter list. The two compose: `ParamSpec` carries the call shape while
`TypeVar` carries the return.

## Decorator that preserves the wrapped signature

```python
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar
import logging

P = ParamSpec("P")
R = TypeVar("R")
log = logging.getLogger(__name__)

def trace(fn: Callable[P, R]) -> Callable[P, R]:
    @wraps(fn)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        log.debug("call %s", fn.__qualname__)
        return fn(*args, **kwargs)
    return wrapped

@trace
def charge(amount: int, *, currency: str = "GBP") -> str: ...
```

Type checkers see `charge` as `(amount: int, *, currency: str = "GBP") -> str`.
A wrapper typed `Callable[..., Any]` would erase that.

## Concatenate: inject a prefix argument

```python
from typing import Concatenate

def with_request(
    fn: Callable[Concatenate[Request, P], R],
) -> Callable[P, R]:
    @wraps(fn)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        return fn(current_request(), *args, **kwargs)
    return wrapped
```

The wrapped callable loses its first positional parameter; callers see the
remaining `(P)` shape.

## PEP 695 inline generics (Python 3.12+)

```python
def first[T](xs: list[T]) -> T:
    return xs[0]

class Cache[K, V]:
    def __init__(self) -> None:
        self._d: dict[K, V] = {}
```

Inline syntax replaces module-level `TypeVar("T")` for new code and keeps the
scope of the type variable visible at the use site.

## TypeVar defaults (PEP 696)

```python
from typing import TypeVar

E = TypeVar("E", default=Exception)

class Result[T, E = Exception]:
    ok: T | None
    err: E | None
```

Defaults are useful when a generic is parameterised on a "usually
`Exception`" knob and most callers should not need to spell it.

## Bounds and constraints

```python
N = TypeVar("N", bound=int)        # any subtype of int
S = TypeVar("S", str, bytes)       # one of str or bytes, not both at once
```

Use a bound when "anything that behaves like a `T`" is the intent (often a
protocol). Use constraints sparingly; they cannot be combined.

## Common mistakes

- Reusing one `TypeVar` across unrelated signatures in the same module.
  Each generic relationship deserves its own name or its own scope.
- Annotating a decorator `(Callable[..., R]) -> Callable[..., R]`. The
  inner `...` swallows the signature.
- Forgetting `@functools.wraps`. Without it, the type-checker view stays
  intact but introspection (docstrings, name) breaks.
