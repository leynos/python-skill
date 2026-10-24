---
name: crosshair
description: Run symbolic execution on Python functions with CrossHair to find counter-examples to contracts or assertions, fill coverage holes via `cover`, and detect behavioural drift via `diffbehavior`. Use after `python-verification` confirms CrossHair is the right adversary.
---

# CrossHair symbolic execution for Python

CrossHair runs Python under symbolic execution backed by Z3. It explores
reachable paths through a function, bounded by per-path timeouts, per-condition
timeouts and a cap on consecutive iterations that make no progress, and reports
concrete counter-examples when contracts or assertions fail. Where Hypothesis
searches by random sampling and shrinks, CrossHair searches by satisfiability
and reports a satisfying assignment.

## When to apply

Apply when the function under scrutiny:

- is pure (no I/O, no time, no randomness),
- has a small reachable state space (low loop depth, few collections),
- carries a contract worth searching symbolically rather than sampling
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

To use the Hypothesis backend below, also install `hypothesis-crosshair` with
`uv add --dev hypothesis-crosshair`.

Set per-path and per-condition timeouts with the `--per_path_timeout` and
`--per_condition_timeout` CLI flags, or matching `# crosshair:` source
directives. CrossHair does not read `[tool.crosshair]` from `pyproject.toml`.

## Three modes

### `check` — verify contracts and selected assertions

```bash
uv run crosshair check mypkg.parse
```

By default, `crosshair check` checks PEP 316, `deal`, and `icontract`
contracts. Include `asserts` in `--analysis_kind` to check Python `assert`
statements as contracts. CrossHair analyzes only code reachable from a function
with a contract; a targeted function needs at least one pre- or postcondition.
In `asserts` mode, leading `assert` statements can supply those conditions.
CrossHair explores paths within the budget and reports a counter-example when
an active contract or selected assertion fails. PEP 316 docstring contracts
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

`icontract` and `deal` use decorators (`@require`, `@ensure`) — both are
supported.

### `cover` — find inputs for previously uncovered opcodes

```bash
uv run crosshair cover mypkg.parse
```

Use `cover` to search for additional test inputs within its configured budget.
It can complement generated examples but does not guarantee additional
coverage. Measure the results, then promote useful candidates to named
regression tests.

### `diffbehavior` — find an input where two functions disagree

```bash
uv run crosshair diffbehavior mypkg.parse_old mypkg.parse_new
```

The single most useful refactor tool: rename `parse` to `parse_old`, write
`parse_new`, run `diffbehavior`. If CrossHair finds a disagreement within the
budget, the refactor changed behaviour; if it finds none, behaviour is
unchanged within the limits of the search.

## Hypothesis backend

`hypothesis-crosshair` registers CrossHair as a Hypothesis backend. Use it for
a targeted property when symbolic path search complements generated examples:

```python
from hypothesis import given, settings, strategies as st

@settings(backend="crosshair")
@given(x=st.integers())
def test_property(x: int) -> None:
    assert invariant(x)
```

This backend uses CrossHair's symbolic search under its configured limits. Use
it for targeted properties, not as a guarantee of broader coverage.

## Limits

- **Floats and strings**: Z3's theories for these are improving but
  slow; expect timeouts on regex-heavy code.
- **Collections**: bounded loops and small lists are fine; deep
  recursion or unbounded collections stall.
- **Async, threads, I/O**: not supported. Symbolic execution requires
  determinism CrossHair can reason about.
- **Performance**: each path costs SMT time. Budget per function;
  parallelize across functions in CI.

## Project integration

- Run `crosshair check` on a nightly job or on PRs that touch the
  relevant module — not on every push (the search budget compounds).
- Treat counter-examples as named regression tests pinned in the
  unit-test file with a comment referencing the CrossHair run.
- Use `diffbehavior` whenever a critical pure function is rewritten;
  bake it into the refactor PR checklist.

## Hard-won lessons

- **Search budget matters.** Longer per-path and per-condition timeouts may
  permit more path exploration, at a runtime cost. Set them with the
  `--per_path_timeout` and `--per_condition_timeout` CLI flags or the matching
  `# crosshair:` source directives; CrossHair does not read them from
  `pyproject.toml`.
- **Pure functions only.** Wrapping an impure function in a "pretend
  pure" shell to make CrossHair work usually means the shell is the bug.
- **`diffbehavior` after every non-trivial refactor.** It is the
  cheapest insurance against accidentally changing semantics during a
  "cosmetic" rewrite.
- **CrossHair and Hypothesis are complements.** Hypothesis samples inputs and
  shrinks failures; CrossHair searches feasible paths symbolically. Their
  different strategies can produce different counter-examples, and neither is
  generally more thorough. Finding no counter-example within CrossHair's budget
  does not prove the property.

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
