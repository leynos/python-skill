---
name: python-verification
description: Select between Hypothesis, CrossHair, and mutmut for Python verification work. Use when example-based tests are not enough and the question is which adversary should generate or evaluate cases.
globs: ["**/*.py"]
---

# Python Verification

Use this when example-based tests cover the obvious cases but the bug
class is broader than the corpus. The three tools each answer a
different question; load this skill to choose, then load the matching
deep dive.

## The three questions

- **Hypothesis** — *Does this property hold across a generated input
  space?* Random generation with shrinking; the cheapest adversary for
  pure-ish functions with an algebraic property (round-trip, oracle,
  invariant).
- **CrossHair** — *Is there an input that violates this assertion or
  contract?* Symbolic execution backed by Z3; explores reachable
  branches and reports counter-examples when possible. Useful for code
  where every reachable path matters and a small search budget is
  acceptable.
- **mutmut** — *Would the test suite notice if the production code
  were wrong?* Mutation testing rewrites the production code one
  small step at a time and runs the suite; surviving mutants are
  tests that did not exercise the changed behaviour.

## Decision surface

- **Pick Hypothesis** when a pure function has an algebraic property,
  an oracle is available, or the corpus of hand-written cases keeps
  growing because each new bug needs another case. State machines
  with `RuleBasedStateMachine` extend the same idea to collections,
  caches, and protocol clients.
- **Pick CrossHair** when the function is small, pure, and the bug is
  a missed branch or boundary case. Also useful for
  `crosshair diffbehavior old.f new.f` — verifying that a refactor
  preserves behaviour.
- **Pick mutmut** when the suite passes consistently but the team is
  not confident the tests would catch a regression. Mutation testing
  measures the suite, not the code.

## What none of them detect

- Race conditions and ordering bugs — use thread sanitizers or
  scheduler-pinning tools.
- Resource leaks under load — use load tests and OS-level profilers.
- Bugs in C extensions — Hypothesis and mutmut see the Python
  surface; CrossHair cannot execute through C.
- Architectural mistakes — verification proves the code as written
  matches the contract as written; both can still be wrong.

## Combining the three

The cheap composition runs Hypothesis at every CI run, runs mutmut on
a nightly job, and reaches for CrossHair when a specific function
needs scrutiny:

- Hypothesis catches the property failures and reports a shrunk
  counter-example.
- CrossHair confirms that no reachable branch violates the property
  (within its limits).
- mutmut confirms the property would notice if the production code
  were wrong.

A property that Hypothesis cannot falsify and mutmut shows is
exercised by surviving zero mutants is a property worth keeping.

## Red flags

- A Hypothesis property that filters most inputs (`assume` or
  `prop_filter` rejection budget exhausted) — the strategy should
  construct valid inputs.
- A CrossHair run with no timeout — symbolic execution can run
  arbitrarily long; cap with `--per-test-timeout`.
- A mutmut run that includes mutants ruled out by the type checker —
  filter them out so the survivor list reflects real test gaps.
- A "verification" CI job that only runs Hypothesis at `max_examples=10`.
- Snapshot tests promoted as the system of record for a property —
  the property is the spec; the snapshot is a fixture.

Read [selection-matrix.md](references/selection-matrix.md) when the
choice between tools is still unclear, then load the matching deep
dive (`hypothesis`, `crosshair`, or `mutmut`).
