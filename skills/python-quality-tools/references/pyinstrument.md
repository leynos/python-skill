# Pyinstrument

A statistical sampler. The default interval is 1 ms; the overhead is
small enough to leave on in a development workflow. Pyinstrument is
the right profiler for tight loops, async event loops, and any case
where `cProfile` would distort the function-call cost.

## Installation

```toml
[dependency-groups]
dev = [
  "pyinstrument>=4",
]
```

## Invocation patterns

### Command-line

```bash
uv run pyinstrument script.py                          # console renderer
uv run pyinstrument --renderer=speedscope script.py > flame.json
uv run pyinstrument --renderer=html -o report.html script.py
uv run pyinstrument -i 0.001 script.py                  # 1 ms interval
```

The `speedscope` renderer produces a file the speedscope viewer reads;
upload to `speedscope.app` or use a local viewer. The HTML renderer
produces a self-contained interactive report.

### As a context manager

```python
import pyinstrument

with pyinstrument.profile() as p:
    do_the_thing()

print(p.output_text(unicode=True, color=True))
```

Useful in tests and REPL sessions when CLI invocation is awkward.

### Inside pytest

```bash
uv run pytest --pyinstrument tests/test_hot.py
```

Drops a flamegraph per test in the `prof/` directory. Use to identify
slow tests; do not regression-test performance with this — use
`pytest-benchmark`.

### As a middleware (web frameworks)

`pyinstrument` ships a Django and a Flask middleware that records
each request's profile. Sample a fraction of requests in development
and on a feature-flag basis in production.

## Reading the output

The default console output is a top-down tree of function calls
weighted by sample count. The interpretation:

- Each line is "self time" plus "child time"; the percentage is of
  the whole sampled window.
- Lines with `[runtime]` are CPython internals; lines with `[await]`
  are coroutine awaits.
- A function whose self-time is high deserves attention; a function
  whose self-time is low but child-time is high is a caller, not the
  hot path.

The speedscope flamegraph shows time on the x-axis and call depth on
the y-axis; the widest blocks at the top are the work.

## Async profiling

```python
import asyncio
import pyinstrument

async def main() -> None:
    with pyinstrument.profile():
        await heavy_task()

asyncio.run(main())
```

Pyinstrument samples the active stack, including coroutine frames.
`cProfile` reports each `await` as a separate call, which clouds the
picture; Pyinstrument keeps the coroutine view intact.

## When Pyinstrument is the wrong tool

- Profiling at the per-line level. Use `line_profiler` for that.
- Measuring tiny micro-benchmarks. Statistical sampling will not
  resolve nanosecond-scale differences; use `pytest-benchmark` or
  `timeit`.
- Detecting memory issues. Use `tracemalloc` or `memray`.

## CI tiering

- **Per-push**: do not profile. The cost is small but the noise is
  high.
- **On performance-flagged PRs**: run pyinstrument on the touched
  endpoint or test and attach the report.
- **Weekly**: sample a representative production trace if production
  middleware is enabled.

## Common mistakes

- Reading a profile in isolation. The number is meaningful relative
  to a baseline; collect both before and after.
- Optimising the function with the highest percentage without
  checking whether the workload is representative. A profile of a
  small input is a profile of a small input.
- Treating Pyinstrument as a benchmarker. The same code can show
  noticeable variance run to run; benchmarks need repeated runs and
  statistical reporting.
