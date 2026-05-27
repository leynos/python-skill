---
name: hypothesis
description: Write and maintain Hypothesis property-based tests for Python, including strategy design, the filtering trap, stateful testing with RuleBasedStateMachine, the example database, and CI tiering. Use after `python-verification` confirms Hypothesis is the right adversary.
---

# Hypothesis property-based testing for Python

Hypothesis generates many random inputs against a property and shrinks
any failing case to a minimal counter-example. It is the cheapest
verification adversary for pure functions whose input space is too
large to enumerate. Load `python-verification` first to confirm
Hypothesis is the right tool; load this skill once it is.

## When to apply

Apply when a pure function has an algebraic property (round-trip,
idempotence, ordering, conservation), when a parser or codec must
round-trip across all valid inputs, when an oracle is available
(reference implementation, invariant predicate, prior version), or
when a unit-test corpus keeps growing because each new bug needs
another hand-written case.

Do not apply when the property requires exhaustive coverage of a
bounded space (use CrossHair), when the bug is a scheduling artefact
(use thread/async race tools), when the failure mode is undefined
behaviour in a C extension (no Python tool sees it), or when each
generated input does heavy real I/O (slow runs starve the inner loop).

## Installation

```toml
[dependency-groups]
dev = [
  "hypothesis>=6",
]
```

Tests run under the normal pytest driver. Environment variables tune
the runner without recompiling: `HYPOTHESIS_PROFILE=ci`,
`HYPOTHESIS_VERBOSITY=verbose`, and per-test `@settings(...)` overrides.

## Core concepts

A property test pairs a **strategy** (how to generate values) with a
property assertion:

```python
from hypothesis import given, strategies as st

@given(
    y=st.integers(min_value=0, max_value=9999),
    m=st.integers(min_value=1, max_value=12),
    d=st.integers(min_value=1, max_value=28),
)
def test_parse_roundtrips(y: int, m: int, d: int) -> None:
    s = f"{y:04}-{m:02}-{d:02}"
    parsed = parse_date(s)
    assert parsed == (y, m, d)
```

Key pieces:

- A **strategy** is anything implementing `SearchStrategy[T]`.
  `st.integers`, `st.text`, `st.lists`, `st.from_type`, and
  `st.builds` are the everyday starters.
- `assert` reports failure to the runner; Hypothesis catches it and
  shrinks.
- `assume(cond)` rejects the current case as uninteresting; use it
  sparingly.
- `st.composite` builds reusable strategies returning structured
  values.
- `@settings(max_examples=..., deadline=...)` tunes per-test.

A worked round-trip example, a stateful sketch with
`RuleBasedStateMachine`, and the
`st.builds` derive pattern live in
[`references/strategy-examples.md`](references/strategy-examples.md).
Stateful testing has its own write-up in
[`references/stateful-testing.md`](references/stateful-testing.md).

## The filtering trap

`assume(cond)` and `.filter(pred)` use rejection sampling. The runner
aborts once the rejection budget is exhausted, and shrinking interacts
badly with rejection: a shrunk candidate that gets rejected cannot
tell the runner whether to keep shrinking, so the minimised
counter-example is larger than it needs to be.

The fix is to construct only valid values from the seed. Replace
"draw an int, assume it is even" with "draw an int and double it";
replace "draw two values, assume `a < b`" with "draw `b`, then draw
`a` from `0..b`". Before-and-after examples live in
`references/strategy-examples.md`.

## Anti-patterns

- **`assert` inside a `try/except` that swallows the failure.** The
  runner sees no failure and the bug stays hidden.
- **Asserting "does not raise".** Pair every "no-raise" property with
  a real check (round-trip, oracle).
- **Re-implementing the function under test as the oracle.** Use a
  structurally different reference: brute force, prior version,
  property predicate.
- **Hiding regressions.** Hypothesis stores failing seeds in
  `.hypothesis/examples`; promote each one to a named unit test with
  the input pinned and a comment explaining the bug.
- **Lowering `max_examples` to make a flake go away.** If the property
  fails at 500 cases but not 100, the test has found a bug.

## Project integration

- **Check the `.hypothesis/examples` directory into VCS** so CI replays
  failing seeds first.
- **Promote shrunk failures to named unit tests** — the database is a
  backstop, not the system of record.
- **Tier runs.** Default profile in CI; nightly profile with
  `max_examples=10000` widens the search without slowing the inner
  loop.
- **Validate each property with a deliberate mutation.** Break the
  production code, confirm the property fails with a useful shrunk
  input, then restore. `mutmut` automates this across the suite.

## Hard-won lessons

- **Strategies decide what you test.** A weak strategy makes a strong
  property look strong. Audit the strategy first.
- **Shrinking is sacred.** Never swallow failures, never tune
  `max_examples` to hide a flake, never filter when you can compose.
- **The database is not a regression test.** Promote each failure to
  a named unit test with the input pinned.
- **Pair with mutmut.** Hypothesis shows the property holds for the
  inputs the strategy reaches; mutation testing shows the property
  would notice if the production code were wrong.

## References

- [Hypothesis documentation](https://hypothesis.readthedocs.io/) and
  [GitHub repository](https://github.com/HypothesisWorks/hypothesis).
- [Strategies reference](https://hypothesis.readthedocs.io/en/latest/reference/strategies.html).
- [Stateful testing](https://hypothesis.readthedocs.io/en/latest/reference/stateful.html).
- [`references/strategy-examples.md`](references/strategy-examples.md)
  for worked strategies and the filtering-trap fix.
- [`references/stateful-testing.md`](references/stateful-testing.md)
  for `RuleBasedStateMachine`.
- Selection between Hypothesis and other verification tools lives in
  [`../python-verification/SKILL.md`](../python-verification/SKILL.md).
