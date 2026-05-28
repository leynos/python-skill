# Extracting an iterator or a context manager

Two refactoring moves that reduce nested-loop complexity.

## Extract an iterator

The smell: a function carries a deep `for` nest, mutates a list of
intermediate items, then loops over the list at the end. The shape
hides a producer.

```python
# Before
def changed_users(snapshots: list[Snapshot]) -> list[User]:
    out: list[User] = []
    for snap in snapshots:
        for user in snap.users:
            if user.dirty:
                out.append(user)
    return out
```

```python
# After
def changed_users(snapshots: Iterable[Snapshot]) -> Iterator[User]:
    for snap in snapshots:
        for user in snap.users:
            if user.dirty:
                yield user
```

The producer is now lazy, the caller chooses whether to materialize it,
and the function name names what it yields rather than how it loops.

### When the iterator has internal state

```python
def watermarks(events: Iterable[Event]) -> Iterator[tuple[Event, int]]:
    high = 0
    for ev in events:
        high = max(high, ev.value)
        yield ev, high
```

State that exists for the lifetime of the stream lives inside the
generator. A class with `__iter__`/`__next__` is the right shape only
when the consumer must call extra methods (`peek`, `seek`, `reset`).

### When the iterator owns a resource

```python
def lines(path: str) -> Iterator[str]:
    with open(path) as fh:                  # closes when the generator finishes
        for line in fh:
            yield line.rstrip()
```

`with` inside a generator works because the `try/finally` runs when the
generator is closed (either by the consumer stopping or by garbage
collection). For deterministic close, hand the file to the caller via a
context manager and yield from an inner generator:

```python
@contextmanager
def open_lines(path: str) -> Iterator[Iterator[str]]:
    with open(path) as fh:
        yield (line.rstrip() for line in fh)

with open_lines(path) as it:
    for line in it:
        process(line)
```

## Extract a context manager

The smell: a function opens a resource at the top, closes it in
several branches, and tracks the same cleanup state in two places.
Move the open/close pair into a `@contextmanager` and let the caller
hold the `with`. Worked example lives in
[`../../python-abstractions/references/context-manager-extraction.md`](../../python-abstractions/references/context-manager-extraction.md).

## Send, throw, and close

Generators are coroutines: callers can push values via `gen.send(x)`,
raise via `gen.throw(exc)`, or finalize via `gen.close()`. The everyday
producer ignores all of this; the patterns are worth remembering when
implementing trampolines, simulated time, or pre-3.4-style async.

`yield from inner` forwards `send`/`throw`/`close` to `inner` correctly,
which is why it is preferred to a hand-rolled `for x in inner: yield x`.

## Common mistakes

- Materializing the iterator at the end of the producer (`return
  list(out)`) defeats the point. Return the generator and let the
  caller materialize if needed.
- Returning a generator from a function that should have returned a
  value. If the body has exactly one `yield` at the end, it is a
  function in disguise.
- Calling `next(gen)` in two places concurrently. Generators are not
  thread-safe and a `tee` only papers over the problem; spawn one
  consumer per generator.
- Holding a file or socket inside a long-lived generator that the
  caller forgets to close. Use an explicit context manager.
