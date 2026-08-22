---
name: hypothesis
description: Write lightweight and advanced Hypothesis property-based tests for Python, from replacing representative parameter tables with invariants through strategy design and stateful testing. Use directly for cheap, repeatable invariant tests; use `python-verification` when choosing whether to escalate to CrossHair or mutmut.
---

# Hypothesis property-based testing for Python

Hypothesis generates inputs against a property and shrinks failures towards
a small counter-example. Treat it as ordinary pytest when the code is cheap to
run, repeatable, and governed by a clear invariant. Start with `@given`, a
built-in strategy, and one semantic assertion. Custom strategies, settings
profiles, and state machines are escalation tools, not an entrance fee.

## Default stance

Add a lightweight property test as a matter of course when:

- the same relation should hold across a broad input space,
- the code under test is fast enough to run many times,
- side effects are isolated or rolled back between examples, and
- a failure can shrink to a useful reproducer.

Round trips, idempotence, conservation, ordering, differential oracles, and
metamorphic relations are the everyday cases. Keep named pytest examples for
normative examples, regressions, and behaviour that deserves a readable test
name.

## Start light

A parameter table often samples a property without saying so:

```python
import pytest


@pytest.mark.parametrize("n", [0, 1, 2, 127, 128, 255, 256, 65_535])
def test_varint_roundtrips(n: int) -> None:
    assert decode_varint(encode_varint(n)) == n
```

Replace the representative sample with the domain and preserve any important
named edge case explicitly:

```python
from hypothesis import example, given, strategies as st


@example(n=0)
@given(n=st.integers(min_value=0, max_value=2**64 - 1))
def test_varint_roundtrips(n: int) -> None:
    assert decode_varint(encode_varint(n)) == n
```

That is a complete property test. Do not add `@st.composite`, `assume()`, a
profile, or a state machine unless the domain forces the issue.

## Recognize property-shaped parametrization

A `pytest.mark.parametrize` table is probably trying to do property testing
when:

- every row exercises the same assertion relation,
- the values are described as representative, typical, edge, or weird cases,
- another bug adds another row without changing the test's meaning,
- several columns manually sample a cross-product of independent dimensions,
  or
- the expected result comes from a simple invariant or a structurally
  different reference implementation.

Keep parametrization when the rows form a finite truth table or protocol
example set, each row has distinct semantic meaning, exact rendered output or
error text matters, or the test is too slow or impure to repeat freely. A
four-row standards table does not need a generator orbiting it.

## Everyday properties

Prefer properties that state behaviour independently of the implementation:

- **Round trip:** `decode(encode(value)) == value`.
- **Idempotence:** `normalize(normalize(value)) == normalize(value)`.
- **Oracle or differential:** an optimized implementation agrees with a slow,
  obviously different reference implementation.
- **Invariant or conservation:** sorting preserves the multiset; a transaction
  preserves total value; a transformation preserves schema constraints.
- **Metamorphic relation:** changing the input in a known way changes, or does
  not change, the output in a predictable way.
- **Totality or robustness:** valid-shaped input does not crash. Use this when
  accepting all such input is itself the contract; otherwise assert a stronger
  semantic fact too.

Do not re-implement the production algorithm inside the assertion. A second
copy of the same mistake is not an oracle.

## Core concepts

A property test pairs a **strategy** with a semantic assertion:

```python
from hypothesis import given, strategies as st


@given(
    y=st.integers(min_value=0, max_value=9999),
    m=st.integers(min_value=1, max_value=12),
    d=st.integers(min_value=1, max_value=28),
)
def test_parse_roundtrips(y: int, m: int, d: int) -> None:
    rendered = f"{y:04}-{m:02}-{d:02}"
    assert parse_date(rendered) == (y, m, d)
```

The everyday pieces are deliberately small:

- `st.integers`, `st.text`, `st.binary`, `st.lists`, `st.sampled_from`,
  `st.from_type`, and `st.builds` cover most inputs.
- `assert` reports failure; Hypothesis searches for and shrinks a
  counter-example.
- `@example(...)` preserves a named boundary or regression alongside generated
  examples.
- Default settings are normally sufficient. Tune `@settings(...)` only for a
  measured cost or search need.

A worked round-trip example, structured values, and the filtering-trap fix live
in [`references/strategy-examples.md`](references/strategy-examples.md).
Stateful testing has its own write-up in
[`references/stateful-testing.md`](references/stateful-testing.md).

## When Hypothesis is the wrong tool

Use a simpler or different tool when:

- the requirement is one named scenario or a finite table of exact outcomes;
  use `python-testing`,
- the domain is tiny and genuinely exhaustive; enumerate it directly,
- each example performs heavy real database, filesystem, network, or service
  I/O; move the property to a cheap model or fake, or write a bounded
  integration test,
- the bug depends on scheduling, timing, load, or resource exhaustion; use
  concurrency, stress, benchmark, or profiler tooling,
- the assertion merely restates the implementation and no independent
  property, oracle, or invariant exists, or
- undefined behaviour lives below Python in a native extension; use a native
  sanitizer or coverage-guided fuzzer.

Property-based testing can exercise side effects, but every example must remain
isolated and repeatable. The problem is not impurity itself; it is uncontrolled
state and an unaffordable inner loop.

## Escalation ladder

Stop at the first rung that answers the question:

1. **Lightweight property:** built-in strategies, one invariant, default
   settings. This should be the common case.
2. **Structured values:** use `st.builds` or `st.from_type` when the input is a
   dataclass, attrs class, or other typed value.
3. **Dependent or recursive values:** introduce `@st.composite`, `flatmap`, or
   recursive strategies only when valid fields depend on one another or the
   data is recursive.
4. **Operation histories:** use `RuleBasedStateMachine` when bugs depend on
   sequences such as insert/delete/reorder, cache invalidation, or protocol
   transitions.
5. **Reachable-path scrutiny:** move to CrossHair when a small, pure function
   carries a contract and every reachable branch matters more than broad input
   sampling.
6. **Suite sensitivity:** add mutmut when the question is whether the tests
   would notice a defect. Mutation testing audits the suite; it does not replace
   the property.

Escalate from light Hypothesis when the strategy starts encoding substantial
domain rules, rejection dominates generation, the failure depends on history,
or the assurance target changes from broad search to path exploration or
test-suite sensitivity. Load `python-verification` when that choice is unclear.

## The filtering trap

`assume(cond)` and `.filter(pred)` reject generated cases. Heavy rejection
starves exploration and makes shrinking less effective because a rejected
candidate reveals nothing about whether the failure still holds.

Construct valid values instead. Replace "draw an integer, assume it is even"
with "draw an integer and double it"; replace "draw `a` and `b`, assume
`a < b`" with a strategy that constructs the ordered pair. Before-and-after
examples live in
[`references/strategy-examples.md`](references/strategy-examples.md).

## Anti-patterns

- **Building a strategy framework before the first property.** Start with
  primitive strategies and let real constraints justify abstraction.
- **Using a state machine for a pure function.** A normal `@given` test is
  cheaper to read, run, and debug.
- **Swallowing an assertion inside `try/except`.** Hypothesis sees no failure,
  so the bug survives.
- **Treating "does not raise" as a universal substitute for semantics.** It is
  useful when totality is the contract; otherwise pair it with an invariant,
  oracle, or round trip.
- **Re-implementing the function under test as the oracle.** Use a
  structurally different reference, prior version, or independent predicate.
- **Lowering `max_examples` to hide a failure.** If the property fails at 500
  examples but not 100, it found a bug.
- **Relying on the example database as the regression suite.** Promote
  important failures to `@example` or a named pytest test.

## Project integration

- Run lightweight properties in the ordinary pytest job.
- Treat `.hypothesis` as a disposable cache and do not commit it by default.
  Use `@example` for durable regressions or a shared database or CI artifact
  when failures must move between environments.
- Keep generated tests focused enough that the default profile remains fast.
  Add a slower profile or fuzzing job only for code that benefits from a wider
  search.
- Validate important properties with a deliberate mutation. Break the
  production code, confirm the property fails with a useful counter-example,
  then restore it; mutmut can automate this across the suite.

## Hard-won lessons

- **The property is the specification.** A broad strategy cannot rescue a weak
  or circular assertion.
- **Strategies decide what gets searched.** Audit the domain before tuning the
  number of examples.
- **Shrinking is sacred.** Preserve determinism, do not swallow failures, and
  construct valid data rather than filtering most draws.
- **Light is a feature.** A five-line property that survives refactoring is
  often more valuable than an elaborate generator that nobody wants to touch.

## References

- [Hypothesis documentation](https://hypothesis.readthedocs.io/) and
  [GitHub repository](https://github.com/HypothesisWorks/hypothesis).
- [Introduction: when to use Hypothesis](https://hypothesis.readthedocs.io/en/latest/tutorial/introduction.html).
- [Evolving toward property-based testing](https://hypothesis.works/articles/incremental-property-based-testing/).
- [Strategies reference](https://hypothesis.readthedocs.io/en/latest/reference/strategies.html).
- [Replaying failures](https://hypothesis.readthedocs.io/en/latest/tutorial/replaying-failures.html).
- [Stateful testing](https://hypothesis.readthedocs.io/en/latest/stateful.html).
- [`references/strategy-examples.md`](references/strategy-examples.md) for
  worked strategies and the filtering-trap fix.
- [`references/stateful-testing.md`](references/stateful-testing.md) for
  `RuleBasedStateMachine`.
- Selection and escalation between Hypothesis and other verification tools
  live in
  [`../python-verification/SKILL.md`](../python-verification/SKILL.md).
