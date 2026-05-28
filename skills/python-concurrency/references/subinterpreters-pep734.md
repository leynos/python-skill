# Subinterpreters (PEP 734)

Python 3.13 stabilized the C-level subinterpreter API; Python 3.14 ships
the high-level `concurrent.interpreters` module and
`concurrent.futures.InterpreterPoolExecutor`. Each subinterpreter has
its own GIL, so CPU-bound pure-Python work scales across cores without
the fork or pickle cost of `multiprocessing`.

## Mental model

- One process, many interpreters. Each interpreter has its own
  modules, its own globals, and its own GIL.
- Python objects are not shared. Anything crossing the boundary is
  serialized and reconstructed on the other side.
- Communication uses queues: `concurrent.interpreters.create_queue()`
  returns a cross-interpreter `queue.Queue` implementation.
- Start-up cost is real (a fresh interpreter must import its modules);
  amortize it via a pool, not per-task spin-up.

## Pool executor

```python
from concurrent.futures import InterpreterPoolExecutor

def heavy(x: int) -> int:
    # pure-Python CPU work
    return sum(i * i for i in range(x))

with InterpreterPoolExecutor(max_workers=4) as pool:
    futures = [pool.submit(heavy, n) for n in inputs]
    totals = [f.result() for f in futures]
```

`InterpreterPoolExecutor` mirrors `ProcessPoolExecutor`. The submitted
callable must be importable in the worker (top-level function in a
module), and the arguments must be encodable across the boundary.

## Queues

```python
from concurrent.interpreters import create, create_queue

interp = create()
requests = create_queue()
results = create_queue()

interp.prepare_main(requests=requests, results=results)
interp.exec(
    "from work import worker_main\n"
    "worker_main(requests, results)"
)

requests.put({"task": "compute", "n": 100})
result = results.get()
```

`create_queue()` returns a `queue.Queue` implementation that is safe to
share across interpreters. Use queues when futures do not fit
(long-running workers, streaming results, fan-in/fan-out).

## What does and does not work

Pure Python:

- Number crunching, parsing, code generation, interpretation of
  domain-specific languages — all scale linearly with cores.
- Standard-library modules that pure-Python can use directly.

C extensions:

- Must declare `Py_mod_multiple_interpreters = Py_MOD_PER_INTERPRETER_GIL_SUPPORTED`
  in their module slots to be loadable in a subinterpreter. Numpy,
  asyncio, and many widely used libraries are working through this
  transition.
- A subinterpreter cannot import a C extension that lacks the slot;
  the import raises `ImportError`.

State:

- No shared globals across interpreters. The same module is imported
  separately in each.
- File descriptors and OS resources can be shared with care (the OS
  does not distinguish interpreters); higher-level wrappers (locks,
  semaphores) must be per-interpreter.

## Choosing between interpreters and processes

Pick subinterpreters when:

- the work is pure Python or uses C extensions that opt in,
- start-up cost matters (no fork, no pickle roundtrip per task),
- the workers share read-only inputs that are easy to ship via
  the cross-interpreter queue.

Pick processes when:

- the relevant C extensions do not support a per-interpreter GIL,
- a worker crash must not bring down the parent (each subprocess is
  an isolation boundary; subinterpreters share the process and OS
  resources),
- forking semantics are needed (copy-on-write of pre-loaded state).

## Common mistakes

- Submitting a closure or a `lambda` to the pool. Workers must
  import the callable; top-level module functions only.
- Treating the cross-interpreter queue like shared memory. Items are
  serialized across the boundary.
- Mixing `asyncio` with `InterpreterPoolExecutor` by awaiting a
  future inside a coroutine without `asyncio.run_in_executor` or the
  `loop.run_in_executor` bridge.
- Assuming the GIL is gone everywhere. The GIL is gone *between*
  interpreters; inside one interpreter it still applies.
