---
name: python-concurrency
description: Use for choosing between threads, `asyncio`, `multiprocessing`, and PEP 734 subinterpreters in Python. Covers workload shape (CPU vs I/O), shared state and the GIL, cancellation, and the `concurrent.interpreters` / `InterpreterPoolExecutor` API new in Python 3.14.
globs: ["**/*.py"]
---

# Python Concurrency

Use this when the question is which concurrency model fits the workload
and how to keep state safe across it.

## Working stance

- Start from the workload shape, not the API. CPU-bound, I/O-bound, and
  blocking-but-cheap have different answers.
- Prefer the model with the least shared mutable state. Asyncio if all
  work is awaitable; threads if some library blocks; interpreters or
  processes if pure Python must scale across cores.
- Treat the global interpreter lock (GIL) as a fact about CPython: one
  interpreter, one Python bytecode at a time. Free-threaded CPython
  (PEP 703, opt-in) lifts that; PEP 734 lifts it via per-interpreter
  GILs.
- Set timeouts and cancellation policy at the boundary; never let a
  worker decide on its own when to abandon work.

## Decision surface

- **`asyncio`**: I/O-bound work with cooperative scheduling. Single
  thread, single interpreter, everything awaitable. Use
  `asyncio.TaskGroup` for structured concurrency; never `await` inside
  a `for` over a list of coroutines when `gather` or a task group is
  the right shape.
- **`threading` / `concurrent.futures.ThreadPoolExecutor`**: blocking
  I/O libraries (database drivers, OS file calls) that cannot be made
  async. Threads share memory; protect mutable state with `Lock`,
  `RLock`, or a queue.
- **`multiprocessing` / `ProcessPoolExecutor`**: CPU-bound pure
  Python today. Each process is its own interpreter and its own GIL;
  pay the pickling and fork cost on every task.
- **PEP 734 subinterpreters (Python 3.14+)**: CPU-bound pure Python
  without the fork cost. `concurrent.interpreters` and
  `InterpreterPoolExecutor` give a per-interpreter GIL with a single
  process and shared memory via explicit channels.
- **Free-threaded CPython (PEP 703)**: experimental in 3.13, supported
  in 3.14. One interpreter, no GIL. Useful when C extensions are
  thread-safe and the build is acceptable to operators.

## PEP 734 in practice

```python
from concurrent.futures import InterpreterPoolExecutor

with InterpreterPoolExecutor(max_workers=4) as pool:
    futures = [pool.submit(compute, n) for n in inputs]
    results = [f.result() for f in futures]
```

What changes versus a thread pool:

- Each worker has its own interpreter and its own GIL; CPU-bound pure
  Python scales.
- No Python objects are shared. Arguments are serialised across the
  boundary; return values likewise.
- Channels (`concurrent.interpreters.create_channel`) handle queue
  communication when futures are not enough.
- C extensions must opt in to per-interpreter GIL support
  (`Py_mod_multiple_interpreters`); pure-Python work always works.

## Async discipline

- Default to `asyncio.TaskGroup` (3.11+) for fan-out. Structured
  concurrency means a failure cancels siblings deterministically and
  the context manager re-raises an `ExceptionGroup` containing every
  task failure.
- Reach for `asyncio.gather` only when the call is *tolerant fan-out*:
  pass `return_exceptions=True` and inspect the result list. Bare
  `gather(...)` leaks unfinished tasks on the first failure.
- Treat `task.cancel()` as a *request*: schedule the cancellation,
  then `await` the task to know whether it finished, cancelled, or
  raised. Never swallow `CancelledError` — let it propagate after any
  cleanup so the cancellation chain completes.
- Wrap a coroutine in `asyncio.shield(...)` only when the inner work
  *must* finish even if the caller is cancelled (final flush, commit,
  audit log). Document the rule; orphaned shielded work hides bugs.
- Set timeouts with `asyncio.timeout()` rather than `wait_for`; the
  context manager is cancellation-safe and composes with `TaskGroup`.
- Custom task factories belong at the loop boundary: use them for
  context propagation (`contextvars`), logging tags, and observability.
  Switch to `asyncio.eager_task_factory` (3.12+) when profiling shows
  the deferred-start cost matters and the codebase does not rely on
  lazy task semantics.
- Never call blocking I/O on the event loop. `asyncio.to_thread` or a
  thread pool offloads it.
- `asyncio.run(main())` once per process; nested loops are an
  anti-pattern.

## Red flags

- `asyncio` mixed with blocking calls inside the same coroutine,
- threads coordinating via a shared `list` without a `Lock`,
- a thread pool used for CPU-bound work where a process pool or
  subinterpreter pool would scale,
- `multiprocessing.Pool` chosen when the work is already async,
- a subinterpreter worker that tries to share a mutable object across
  the boundary,
- `time.sleep` inside an async coroutine,
- cancellation that relies on the worker checking a flag at every
  iteration rather than catching `CancelledError`.

Read [subinterpreters-pep734.md](references/subinterpreters-pep734.md)
and [workload-shape-matrix.md](references/workload-shape-matrix.md)
when the workload shape or the choice between threads, asyncio, and
interpreters dominates. Read
[async-task-discipline.md](references/async-task-discipline.md) when
the question is `TaskGroup` versus `gather`, cancellation and shield
semantics, or task factories.
