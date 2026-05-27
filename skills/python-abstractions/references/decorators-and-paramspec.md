# Decorators with ParamSpec

A decorator is useful when a cross-cutting concern (logging, retry,
caching, transactions, authorisation) wraps many functions with the
same shape. The two failures to avoid are (1) erasing the wrapped
signature so the type checker stops helping, and (2) hiding control
flow that callers needed to see.

## Pattern: preserving the signature

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
```

`@wraps(fn)` copies `__name__`, `__doc__`, and `__wrapped__` so
introspection works; `ParamSpec` makes the type checker see `wrapped`
as having the same signature as `fn`.

## Pattern: a decorator factory

```python
def retry(
    *,
    attempts: int = 3,
    on: type[BaseException] | tuple[type[BaseException], ...] = Exception,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorate(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            last: BaseException | None = None
            for _ in range(attempts):
                try:
                    return fn(*args, **kwargs)
                except on as exc:
                    last = exc
            assert last is not None
            raise last
        return wrapped
    return decorate
```

Two layers: the outer factory takes configuration, the inner decorate
returns the wrapped callable. Both layers stay typed.

## Pattern: injecting a prefix argument

```python
from typing import Concatenate

def with_session(
    fn: Callable[Concatenate[Session, P], R],
) -> Callable[P, R]:
    @wraps(fn)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        with open_session() as sess:
            return fn(sess, *args, **kwargs)
    return wrapped
```

`Concatenate[Session, P]` tells the checker that `fn` expects a
`Session` first followed by the remaining `P` parameters; `wrapped`
hides the session from the call site.

## When not to write a decorator

- The wrapped function is called from one place. Inline the cross-cutting
  concern.
- The wrapper changes the return type. That is a transformation, not a
  decoration; give it a real name.
- The wrapper needs to talk to its caller (`commit()`, `rollback()`).
  Use a context manager instead.

## Decorating classes

`@dataclass`, `@dataclass_transform`, and `@runtime_checkable` are the
common cases. Custom class decorators belong in libraries; in
application code, prefer `__init_subclass__` or a metaclass when the
behaviour must run at class-creation time.

## Common mistakes

- Forgetting `@wraps`: callers lose `__name__`, `inspect.signature`
  reports the wrong shape, and `pickle`/`functools.partial` interact
  badly.
- Writing `def wrapped(*args, **kwargs):` without `P.args` and
  `P.kwargs`: the type checker collapses the signature to
  `(*Any, **Any) -> R`.
- Returning a `functools.partial` and calling it a decorator: it is a
  partial; the call site does not document the wrap.
