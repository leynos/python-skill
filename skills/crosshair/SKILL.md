---
name: crosshair
description: Run symbolic execution on Python functions with CrossHair to find counter-examples to contracts or assertions, fill coverage holes via `cover`, and detect behavioural drift via `diffbehavior`. Use after `python-verification` confirms CrossHair is the right adversary.
---

# CrossHair symbolic execution for Python

CrossHair runs Python under symbolic execution backed by Z3. It explores
reachable paths through a function (within a per-call budget) and
reports concrete counter-examples when contracts or assertions fail.
Where Hypothesis searches by random sampling and shrinks, CrossHair
searches by satisfiability and reports a satisfying assignment.

## When to apply

Apply when the function under scrutiny:

- is pure (no I/O, no time, no randomness),
- has a small reachable state space (low loop depth, few collections),
- carries a contract you would rather see proved than sampled
  (`assert`, PEP 316 docstrings, `icontract`, `deal`),
- has a sibling implementation you want to compare against
  (`diffbehavior`).

Do not apply when:

- the function depends on threads, sockets, files, or wall time,
- inputs are strings or floats over a wide domain (the SMT solver can
  stall),
- the function calls into C extensions (CrossHair cannot execute
  through them),
- you have a fast example-based suite that already covers the cases
  — CrossHair complements Hypothesis, it does not replace it.

## Installation

```bash
uv add --dev crosshair-tool
```

Per-test timeouts live in `pyproject.toml`:

```toml
[tool.crosshair]
per_path_timeout = 4
per_condition_timeout = 30
```

## Three modes

### `check` — verify contracts and asserts

```bash
uv run crosshair check mypkg.parse
```

CrossHair walks each branch of `mypkg.parse` and reports any input
that violates an `assert` or contract. PEP 316 docstring contracts
look like:

```python
def withdraw(balance: int, amount: int) -> int:
    """
    pre: amount >= 0
    pre: balance >= amount
    post: __return__ == balance - amount
    """
    return balance - amount
```

`icontract` and `deal` use decorators (`@require`, `@ensure`) — both
are supported.

### `cover` — find inputs that drive a function down each branch

```bash
uv run crosshair cover mypkg.parse
```

Useful for filling coverage holes the random generator missed.
CrossHair prints concrete inputs that reach previously unexplored
branches; promote these to named regression tests.

### `diffbehavior` — find an input where two functions disagree

```bash
uv run crosshair diffbehavior mypkg.parse_old mypkg.parse_new
```

The single most useful refactor tool: rename `parse` to `parse_old`,
write `parse_new`, run `diffbehavior`. If CrossHair finds a
disagreement within the budget, the refactor changed behaviour; if it
finds none, behaviour is unchanged within the limits of the search.

## Hypothesis backend

`hypothesis-crosshair` registers CrossHair as a Hypothesis backend.
Use it when Hypothesis cannot find a falsifying example and you
suspect one exists in a narrow corner:

```python
from hypothesis import given, settings, strategies as st

@settings(backend="crosshair")
@given(x=st.integers())
def test_property(x: int) -> None:
    assert invariant(x)
```

CrossHair searches more thoroughly within the budget; the cost is
time. Use sparingly.

## Limits

- **Floats and strings**: Z3's theories for these are improving but
  slow; expect timeouts on regex-heavy code.
- **Collections**: bounded loops and small lists are fine; deep
  recursion or unbounded collections stall.
- **Async, threads, I/O**: not supported. Symbolic execution requires
  determinism CrossHair can reason about.
- **Performance**: each path costs SMT time. Budget per function;
  parallelise across functions in CI.

## Project integration

- Run `crosshair check` on a nightly job or on PRs that touch the
  relevant module — not on every push (the search budget compounds).
- Treat counter-examples as named regression tests pinned in the
  unit-test file with a comment referencing the CrossHair run.
- Use `diffbehavior` whenever a critical pure function is rewritten;
  bake it into the refactor PR checklist.

## Hard-won lessons

- **Search budget matters.** A 30-second per-condition budget catches
  the everyday bugs; longer budgets find rarer cases. Tune in
  `pyproject.toml`, not per-run.
- **Pure functions only.** Wrapping an impure function in a "pretend
  pure" shell to make CrossHair work usually means the shell is the
  bug.
- **`diffbehavior` after every non-trivial refactor.** It is the
  cheapest insurance against accidentally changing semantics during
  a "cosmetic" rewrite.
- **CrossHair and Hypothesis are complements.** Hypothesis covers the
  vast input space cheaply; CrossHair covers the narrow corners
  exhaustively.

## References

- [CrossHair documentation](https://crosshair.readthedocs.io/) and
  [GitHub repository](https://github.com/pschanely/CrossHair).
- [`crosshair check`](https://crosshair.readthedocs.io/en/latest/check.html),
  [`crosshair cover`](https://crosshair.readthedocs.io/en/latest/cover.html),
  [`crosshair diffbehavior`](https://crosshair.readthedocs.io/en/latest/diff_behavior.html).
- [Hypothesis-CrossHair backend](https://github.com/pschanely/hypothesis-crosshair).
- [`references/modes-and-limits.md`](references/modes-and-limits.md)
  for the per-mode invocation patterns and limit cases.
- Selection between CrossHair and other verification tools lives in
  [`../python-verification/SKILL.md`](../python-verification/SKILL.md).
