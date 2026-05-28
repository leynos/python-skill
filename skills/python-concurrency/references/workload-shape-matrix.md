# Workload shape matrix

The choice between asyncio, threads, processes, and subinterpreters
follows from the work's shape, not from convenience.

## The matrix

| Workload                                              | Recommended model                       | Notes                                                  |
| ----------------------------------------------------- | --------------------------------------- | ------------------------------------------------------ |
| HTTP/RPC fan-out, mostly waiting on responses         | `asyncio` + `TaskGroup`                 | Hundreds of concurrent calls per process              |
| Blocking driver (psycopg2, paramiko) that has no async API | `ThreadPoolExecutor`              | Bound the pool; queue overflows are operational signals |
| CPU-bound pure-Python (parsing, codegen, simulation)  | `InterpreterPoolExecutor` (3.14+)       | Fall back to `ProcessPoolExecutor` on 3.13 or earlier  |
| CPU-bound with heavy NumPy/SciPy                      | `ThreadPoolExecutor`                    | NumPy releases the GIL; threads scale                  |
| Mixed CPU + I/O in one task                           | Split: async wrapper, pool worker       | Do not run CPU work on the event loop                  |
| One long worker, many requests                        | Async or threading + queue              | Pick by whether requests are awaitable                 |
| Crash isolation needed                                | `multiprocessing` (separate processes)  | Subinterpreters share the OS process                   |

## Anti-patterns by shape

- **`asyncio` on the event loop with blocking calls.** A single
  `time.sleep` or synchronous DB call freezes every coroutine. Move
  blocking work to a thread via `asyncio.to_thread` or
  `loop.run_in_executor`.
- **`ThreadPoolExecutor` for CPU-bound pure Python.** The GIL
  serializes bytecode execution; extra workers add scheduling
  overhead without throughput. Use a process or interpreter pool.
- **`ProcessPoolExecutor` for tasks shorter than the fork cost.**
  Forking and pickling per task can cost more than the work. Batch
  the work or use subinterpreters.
- **Shared mutable state across threads without a lock.** Even
  primitive operations are not always atomic in CPython; use
  `queue.Queue`, `threading.Lock`, or atomic patterns
  (compare-and-swap via `Lock`).
- **Mixed cancellation policies.** Some tasks cooperate with a flag,
  others use `CancelledError`. Pick one model per pool.

## Cancellation cheatsheet

- `asyncio.TaskGroup` and `asyncio.timeout` handle cancellation
  structurally; tasks that catch `CancelledError` must re-raise it
  after cleanup.
- `concurrent.futures.Future.cancel()` only works for pending tasks;
  running tasks must check a flag or accept that they will finish.
- `multiprocessing.Pool` workers are killed via signal; trust nothing
  about their state on cancellation.
- `InterpreterPoolExecutor` cancellation semantics mirror
  `concurrent.futures` — pending tasks can be cancelled, running
  tasks must check.

## Timeouts

Set timeouts at the boundary that has context — the HTTP handler, the
job dispatcher, the CLI entry — not deep inside a worker. Workers
should respect a deadline passed in, not invent one.

```python
async def handle(request):
    async with asyncio.timeout(5.0):
        return await downstream(request)
```

## Choosing under uncertainty

- If unsure between threads and asyncio, profile a representative
  case. Threads win for blocking libraries; asyncio wins for waitable
  ones.
- If unsure between processes and subinterpreters, check the C
  extensions in use. Subinterpreters require per-interpreter GIL
  support in every imported extension.
- If unsure between asyncio and a sync codebase, do not rewrite to
  asyncio without a measurement; thread-based parallelism is often
  enough.
