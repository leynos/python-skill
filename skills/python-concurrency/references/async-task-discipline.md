# Async task discipline

Deeper notes for the `python-concurrency` skill on structured concurrency,
`gather`, cancellation and shielding, and task factories. Use this when
the choice between `TaskGroup` and `gather` dominates, or when a
cancellation bug is suspected.

## `TaskGroup` versus `gather`

`asyncio.TaskGroup` (3.11+) is structured concurrency in the standard
library. The context manager creates tasks via `tg.create_task(...)` and
awaits them at exit. If any task raises, the remaining siblings are
cancelled and the group re-raises an `ExceptionGroup` (or
`BaseExceptionGroup` if a `BaseException` such as `KeyboardInterrupt`
escapes). Handlers use `except*` to match by exception type without
losing the rest of the group.

```python
async with asyncio.TaskGroup() as tg:
    tg.create_task(fetch_user(user_id))
    tg.create_task(fetch_orders(user_id))
    tg.create_task(fetch_addresses(user_id))
# On exit: all three results are available, or an ExceptionGroup is raised
# with every failure and the surviving tasks already cancelled.
```

`asyncio.gather` predates structured concurrency. Two failure modes
make it the wrong default:

- `gather(*coros)` (default `return_exceptions=False`) re-raises the
  first exception but does **not** cancel the other coroutines. They
  keep running in the background, hold resources, and may log
  spurious errors after the caller has moved on.
- `gather(*coros, return_exceptions=True)` returns a list mixing
  results and exceptions. This is the *tolerant fan-out* shape: every
  coroutine is allowed to fail independently and the caller decides
  what to do with the failures.

Reach for `gather` when tolerant fan-out is the requirement; otherwise
use `TaskGroup`. Writing `await gather(*coros)` and expecting
structured-concurrency semantics is a mistake — the leak on first
failure is real.

## Cancellation discipline

`task.cancel()` schedules a `CancelledError` to be raised at the
task's next suspension point. It is a *request*, not a guarantee:

- The task may already be near completion when the cancellation
  arrives; awaiting the task afterwards is the only way to know
  whether it finished, cancelled, or raised something else.
- The task can intercept `CancelledError`, do clean-up, and re-raise.
  This is the supported pattern. Swallowing `CancelledError` without
  re-raising breaks the cancellation chain and is almost always a
  bug.
- A task can also raise something other than `CancelledError` between
  the cancel request and the next suspension — for example, an I/O
  call that completes successfully and then a follow-up failure.
  Code that calls `cancel()` must be ready for the awaited task to
  raise any exception, not only `CancelledError`.

Patterns that hold up under load:

```python
task = asyncio.create_task(work())
...
task.cancel("operator triggered shutdown")
try:
    await task
except asyncio.CancelledError:
    pass  # expected, the task observed our request
except Exception:
    log.exception("worker failed during shutdown")
```

The `msg` argument to `cancel()` (3.9+) propagates through
`CancelledError.args` and is invaluable when debugging multi-task
cancellations.

Common pitfalls:

- `task.cancel(); await task` without exception handling. When the
  task ignores the cancellation and finishes normally, the `await`
  succeeds and the caller assumes work was abandoned. It was not.
- A worker loop that checks a `should_stop` flag on every iteration
  instead of catching `CancelledError`. The flag drifts behind
  long-running awaits and the cancellation arrives only after the
  current step finishes.
- Cancelling many tasks in sequence with `await` in between. The
  first task can take a long time to observe the cancellation, and
  the rest sit idle. Schedule the cancellations first, then await
  them as a group (a `TaskGroup` does this automatically).

## `asyncio.shield`

`asyncio.shield(inner)` returns a future that protects `inner` from
cancellation through the outer await. If the outer task is cancelled,
`shield` raises `CancelledError` to the caller but lets `inner` keep
running.

Use it for:

- final commit/flush/audit work where the caller has been cancelled
  but the side effect must complete,
- semantics where the outer timeout should not abort an
  externally-visible operation.

Do not use it as a generic "ignore cancellation" toggle. The hazards:

- If the outer task is cancelled, `inner` keeps running with **no
  remaining reference**. Whatever logs or surfaces the result must
  still hold its own handle, or the work happens silently and any
  exception ends up in the "task exception was never retrieved"
  warning.
- Inside a `TaskGroup`, shielding a sibling does not stop the group
  from cancelling on a peer failure. The group cancellation is
  reasserted; document the rule and design the shielded path to be
  short.
- `await asyncio.shield(coro)` still propagates exceptions from
  `coro` if the outer task is not cancelled. Shield protects against
  cancellation only; it is not a try/except.

```python
async def commit_with_shield(tx):
    try:
        await asyncio.shield(tx.commit())
    except asyncio.CancelledError:
        # tx.commit() is still running. Decide on a separate task to
        # observe its result, or rely on the database's idempotency.
        raise
```

## Task factories

`loop.set_task_factory(factory)` lets a single hook intercept every
`create_task` call on the loop. The factory receives `(loop, coro,
**kwargs)` and returns the `Task` instance. Two practical uses:

- **Context propagation and observability.** Wrap each task in a
  `contextvars.Context.copy()` snapshot that carries request IDs,
  tenant IDs, or trace state. Attach loggers, metrics tags, or
  cancellation hooks. The factory is the only seam that catches all
  tasks, including those created by libraries.
- **Eager execution.** `asyncio.eager_task_factory` (3.12+) starts
  the coroutine synchronously and only schedules it on the loop if
  it suspends. For coroutines that complete without ever awaiting
  (cache hits, validation that finishes synchronously), this skips
  the round-trip through the scheduler.

```python
loop = asyncio.get_running_loop()
loop.set_task_factory(asyncio.eager_task_factory)
# Now create_task(...) and TaskGroup.create_task(...) run eagerly.
```

Caveats:

- Eager execution changes the order tasks observe other tasks. Code
  that relies on the historical "create_task does not run until the
  next yield" timing breaks. Tests written against the lazy model
  often fail under the eager factory; treat the switch as a
  behavioural change.
- A coroutine that completes synchronously under the eager factory
  never appears in `asyncio.all_tasks()`. Tooling that enumerates
  tasks for liveness or cancellation must account for this.
- Custom factories compose by chaining: an observability factory can
  delegate to `eager_task_factory` after attaching its own state.
  Keep the factory cheap; it runs on every task creation.

## Cross-cutting checks

- Treat `gather` as a code-review smell. Confirm `return_exceptions`
  is set deliberately or rewrite as a `TaskGroup`.
- Every `cancel()` site should be paired with a documented await and
  exception policy.
- Every `shield()` site should explain why the inner work must
  outlive the caller.
- Custom task factories belong at the loop boundary (process entry,
  test fixture, FastAPI lifespan), not sprinkled mid-flow.
- When in doubt, prefer the structured tool: `TaskGroup` over
  `gather`, `asyncio.timeout` over `wait_for`, `to_thread` over
  ad-hoc `run_in_executor` calls.
