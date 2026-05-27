# Context manager extraction

`with` blocks are the right home for any pair of "set up, then guarantee
cleanup" operations: locks, transactions, temporary files, mocked time,
spans, observation contexts.

## Function form: @contextmanager

```python
from contextlib import contextmanager
from collections.abc import Iterator

@contextmanager
def acquired(lock: Lock) -> Iterator[None]:
    lock.acquire()
    try:
        yield
    finally:
        lock.release()

with acquired(my_lock):
    critical_section()
```

Use when:

- the resource is `try/finally`-shaped,
- one `yield` is enough,
- the manager is reused but does not need to expose methods.

## Class form: `__enter__` and `__exit__`

```python
class Transaction:
    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    def __enter__(self) -> Transaction:
        self._conn.execute("BEGIN")
        return self

    def execute(self, sql: str, *args: object) -> None:
        self._conn.execute(sql, *args)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        if exc is None:
            self._conn.execute("COMMIT")
        else:
            self._conn.execute("ROLLBACK")
        return False        # never suppress
```

Use when:

- the manager holds state between `__enter__` and `__exit__`,
- callers should call methods on the manager inside the block,
- `__exit__` needs to suppress an exception (return `True`) under a
  specific rule.

## Refactoring by extracting a context manager

The smell: a function opens a resource, does work, and closes it, with
the close path repeated in two or three places. The fix is to extract
the open/close pair behind a context manager and let the caller hold
the `with`.

```python
# Before: cleanup repeated three times
def export(path: str) -> None:
    f = open_temp()
    try:
        write_header(f)
        if has_rows():
            write_rows(f)
        else:
            cancel(f)
            return
        write_footer(f)
    except Exception:
        cancel(f)
        raise
    finally:
        close_temp(f)
```

```python
# After: the manager owns the lifecycle
@contextmanager
def temp_file() -> Iterator[TempFile]:
    f = open_temp()
    try:
        yield f
    except Exception:
        cancel(f)
        raise
    finally:
        close_temp(f)

def export(path: str) -> None:
    with temp_file() as f:
        write_header(f)
        if has_rows():
            write_rows(f)
            write_footer(f)
        else:
            cancel(f)
            return
```

The caller no longer mentions cleanup; the manager handles it once.

## Async managers

`@asynccontextmanager` and the `__aenter__`/`__aexit__` pair mirror the
sync forms. The body must not call blocking I/O on the event loop;
acquire and release asynchronously.

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def session() -> AsyncIterator[Session]:
    s = await connect()
    try:
        yield s
    finally:
        await s.close()
```

## Composing managers

`contextlib.ExitStack` (and `AsyncExitStack`) lets a single block manage
a dynamic set of resources:

```python
from contextlib import ExitStack

def merge(paths: list[str]) -> None:
    with ExitStack() as stack:
        files = [stack.enter_context(open(p)) for p in paths]
        write_merged(files)
```

`ExitStack` is the right answer when the number of resources is not
known at compile time, or when one resource depends on the value of an
earlier one.

## Common mistakes

- A `@contextmanager` whose body spans many branches with custom cleanup
  per branch. Promote to a class-based manager and put the logic in
  `__exit__`.
- A class-based manager whose `__exit__` returns `True` to swallow every
  exception. Suppression is a deliberate decision; always document the
  rule in a comment.
- A manager that opens a resource in `__init__` instead of `__enter__`.
  The resource then leaks when the `with` is never reached.
