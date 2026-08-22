---
name: python-verification
description: Select the next testing adversary when pytest examples or lightweight Hypothesis properties are insufficient. Use to choose among advanced Hypothesis, CrossHair, and mutmut by the evidence required, not by perceived tool strength.
globs: ["**/*.py"]
---

# Python Verification

Use this when the required evidence is unclear or the task has outgrown ordinary
examples and a lightweight property. Do not insert a selector ceremony between
a clear, cheap invariant and a five-line `@given` test; load `hypothesis`
directly for that case.

The tools here answer different questions. They form an escalation map, not a
single scale from weak to strong.

## Before escalating

- One named scenario, exact output, or finite normative table belongs in
  `python-testing`.
- One invariant over a broad, cheap, repeatable input space belongs directly
  in `hypothesis`.
- Load this selector when valid data needs a substantial model, operation
  history matters, every reachable path matters, or the question is whether
  the suite would detect wrong code.

## The three questions

- **Hypothesis**: *Does this property hold across a generated input space?*
  Generation with shrinking is the cheapest adversary for round trips,
  idempotence, oracles, invariants, and metamorphic relations. Its advanced
  forms cover dependent data, recursive structures, and operation histories.
- **CrossHair**: *Is there an input that violates this assertion or contract?*
  Symbolic execution backed by Z3 explores reachable branches and reports a
  counter-example when possible. It suits small pure functions where path
  coverage matters.
- **mutmut**: *Would the test suite notice if the production code were
  wrong?* Mutation testing changes production code one small step at a time
  and runs the suite. It measures test sensitivity, not program correctness.

## Decision surface

- **Stay with lightweight Hypothesis** when built-in strategies can describe
  the input and one semantic assertion states the property.
- **Escalate within Hypothesis** when valid fields depend on one another, the
  data is recursive, or a bug depends on a sequence of operations.
  `st.builds`, `st.from_type`, `@st.composite`, recursive strategies, and
  `RuleBasedStateMachine` are successive tools, not prerequisites.
- **Pick CrossHair** when a small pure function has a contract, missed branch,
  or narrow boundary that broad generated search may not reach. Use
  `diffbehavior` when a critical refactor should preserve behaviour.
- **Pick mutmut** when the suite passes consistently but confidence in its
  assertions remains low. Mutation testing can audit example and property
  tests alike.
- **Leave this cluster** for real-service integration, race conditions,
  performance, resource leaks, and native undefined behaviour.

## What none of them establish

- A passing generated or symbolic search is not a proof outside the explored
  domain and budget.
- Race conditions and ordering bugs need scheduler-aware or stress tools.
- Resource leaks under load need load tests and OS-level profilers.
- Native-extension faults need sanitizers or native fuzzers.
- Architectural mistakes survive when the contract itself is wrong.

## Combining the tools

Use combinations only when the questions are orthogonal:

- Named pytest examples explain the specification and pin regressions.
- Hypothesis searches broad input spaces and shrinks failures.
- CrossHair scrutinizes reachable paths in selected small pure functions.
- mutmut checks whether the assertions notice plausible defects.

A common shape is pytest examples plus lightweight Hypothesis on every CI run,
targeted CrossHair on critical refactors or a slower cadence, and mutmut as a
nightly or pre-release suite audit. Do not run all three merely because all
three are installed.

## Red flags

- A direct invariant is routed through several selector documents before
  anyone writes the obvious `@given` test.
- A Hypothesis property filters most inputs. Construct valid data instead.
- A state machine models no history-dependent behaviour.
- A CrossHair run has no timeout. Symbolic execution can run arbitrarily long;
  cap the search budget.
- A mutmut run includes a slow, flaky integration suite or mutants the type
  checker already rejects.
- A verification CI job runs expensive tools on every push without a stated
  assurance target.
- A snapshot is treated as the system of record for an invariant. The property
  is the specification; the snapshot is an example.

Read [selection-matrix.md](references/selection-matrix.md) when the choice is
still unclear, then load the matching deep dive (`hypothesis`, `crosshair`, or
`mutmut`).
