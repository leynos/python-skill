# CrossHair modes and limits

A deeper look at when each mode is the right tool and how to bound
the search so it terminates.

## `check` in detail

```bash
uv run crosshair check mypkg.parse --per_condition_timeout 30
uv run crosshair check mypkg --per_condition_timeout 60   # whole module
```

Targets can be a fully qualified function name, a module, or a
glob. The runner enumerates contracts (`assert`, PEP 316,
`icontract`, `deal`) and tries to violate each.

Useful flags:

- `--per_condition_timeout` — SMT time budget per condition.
- `--per_path_timeout` — SMT time budget per explored path.
- `--analysis_kind` — restrict to `asserts`, `pep316`, `icontract`,
  `deal`, or combinations.

A successful run reports nothing on `stdout`. A failure prints the
violated condition and a concrete input that produces it.

## `cover` in detail

```bash
uv run crosshair cover mypkg.parse --coverage_type opcode
```

CrossHair reports inputs that drive `parse` through previously
uncovered opcodes. The output is a sequence of suggested example
inputs; copy them into a parametrized test:

```python
@pytest.mark.parametrize("payload", [
    b"",
    b"\x00",
    b"\xff" * 64,
])
def test_parse_smoke(payload: bytes) -> None:
    parse(payload)         # property: does not crash
```

`cover` is the cheap way to find inputs Hypothesis missed. Pair it
with `pytest --cov-branch` to confirm coverage holes have closed.

## `diffbehavior` in detail

```bash
uv run crosshair diffbehavior mypkg.parse_old mypkg.parse_new
```

CrossHair finds an input where the two functions disagree (return
value, raised exception type, or observable side effect inside the
symbolic boundary). Output is a satisfying input; the recommended
follow-up is a regression test pinning the input.

Tips:

- Keep the two functions in the same module so imports are stable.
- Run after every refactor of a critical pure function.
- The "no disagreement found" outcome is *within the budget*, not a
  proof. Widen the budget for critical paths.

## What CrossHair cannot prove

- **Termination**: CrossHair bounds loops in its search; an infinite
  loop in production code that CrossHair did not unroll stays
  invisible.
- **Memory safety**: a Python OOM is not a CrossHair concern.
- **Behaviour under threads**: the symbolic execution assumes
  single-threaded execution.
- **Side effects outside the function**: writes to a global, calls
  through `__getattr__`, and dynamic imports are out of scope.

## Tuning the budget

The cheapest tuning lives in `pyproject.toml`:

```toml
[tool.crosshair]
per_path_timeout = 4
per_condition_timeout = 30
analysis_kind = "asserts,pep316,icontract"
```

In CI, run with these defaults for the touched modules; once a
month, run a longer "deep" job with `per_condition_timeout = 300`.

## Pairing with Hypothesis

```python
from hypothesis import given, settings, strategies as st

@settings(backend="crosshair")
@given(x=st.integers())
def test_inverse(x: int) -> None:
    assert f(g(x)) == x
```

Hypothesis explores the random space; CrossHair fills in the corners
when the random generator misses. Use the `crosshair` backend for
specific properties, not the whole suite.

## Common mistakes

- Pointing CrossHair at a function that calls `requests.get`. The
  search blows up; the actual answer is "this is not a pure function".
- Running `check` on every push at 60-second budget. Budget compounds;
  pick a cadence and stay there.
- Treating a `diffbehavior` "no disagreement" result as a proof. It
  is a strong signal within the budget.
- Ignoring the SMT theory limits. Regex parsers and float arithmetic
  will not finish; pick a different adversary for them.
