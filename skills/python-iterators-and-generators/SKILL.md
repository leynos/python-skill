---
name: python-iterators-and-generators
description: Use for Python iterators, generators, lazy evaluation, and refactoring deeply nested loops by extracting an iterator or a context manager. Covers `yield`, `yield from`, generator expressions, `itertools` discipline, and async iteration.
globs: ["**/*.py"]
---

# Python Iterators and Generators

Use this when a function is doing too much in one place because it owns
both the iteration and the work, or when memory and throughput pressure
points to an eager `list` that should be lazy.

## Working stance

- Generators are the cheapest abstraction for "produce a stream of
  values"; reach for one before reaching for an iterator class.
- Yield one logical item per `yield`; do not flatten unrelated layers
  of structure into a single generator.
- Push the iteration into a named producer; keep consumers small.
- A generator is a context-bound resource: it owns open files,
  sockets, or transactions while it lives. Pair it with a context
  manager when the resource must be closed even if the consumer stops
  early.
- For async streams, use `async def` generators with `async for`; do
  not mix `yield` and `await` semantics in an opaque iterator class.

## Decision surface

- **Generator function (`def f(): yield`)**: a producer with internal
  state — pagination, decompression, tokenization, simulated time.
- **Generator expression (`(x for x in xs)`)**: a single-step
  transformation; passable directly to `sum`, `any`, `min`,
  `"".join`.
- **`yield from`**: a generator delegates an entire sub-stream;
  removes a manual `for x in inner: yield x` loop and forwards
  `send`/`throw`/`close` correctly.
- **Iterator class (`__iter__` + `__next__`)**: the producer must
  expose more than iteration — `peek()`, `tell()`, restart semantics,
  or multiple independent passes.
- **`itertools` building blocks**: `chain`, `islice`, `groupby`,
  `accumulate`, `tee` (carefully), `product`, `pairwise`, `batched`
  (3.12+). Compose with generators instead of writing custom loops.
- **Async generator**: the stream is awaited (HTTP page chunks, queue
  consumption, server-sent events).

## Refactoring patterns

- **Extract an iterator**: a function with three nested `for` loops and
  bookkeeping is hiding a producer. Move the loops into a generator
  named after the item it yields (`def changed_records(...): yield ...`)
  and let the caller iterate.
- **Extract a context manager**: a generator that owns a connection
  and a cursor should not also be the place where the caller commits
  or rolls back. Wrap the resource in a context manager and let the
  generator be a pure producer.
- **Replace materialization with iteration**: an intermediate
  `list(...)` between two transformations is usually wrong; the
  pipeline can be lazy from end to end unless one stage needs random
  access.

## Red flags

- a generator function whose body is mostly bookkeeping and a single
  `yield value` at the end (call it a function and return the value),
- `tee` used to feed two independent consumers (one rewinds the
  source; consider a real reader),
- `list(...)` in the middle of a pipeline that is otherwise lazy,
- a generator that owns a file but is consumed via `next(...)` calls
  spread across several functions (move ownership to a context
  manager),
- `yield from` flattening unrelated structure into a single stream,
- an iterator class with no extra surface beyond `__iter__` and
  `__next__` (collapse to a generator),
- an async generator that performs blocking I/O between `await`
  points.

Read [extracting-iterators.md](references/extracting-iterators.md) and
[lazy-pipelines.md](references/lazy-pipelines.md) for the refactoring
patterns and the everyday composition idioms.
