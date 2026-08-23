# Verification selection matrix

Use this after the testing hierarchy has ruled out a named pytest example, a
finite parameter table, and an obvious lightweight Hypothesis property. The
matrix chooses an escalation target; it is not a reason to escalate.

## Enter at the right level

- One exact scenario or finite normative case set → `python-testing`.
- One relation over many cheap, repeatable inputs → lightweight `hypothesis`.
- Dependent data, operation history, reachable-path scrutiny, or suite
  sensitivity → use the matrix below.

## At a glance

| Concern                | Hypothesis                     | CrossHair                          | mutmut                      |
| ---------------------- | ------------------------------ | ---------------------------------- | --------------------------- |
| Engine                 | Generation plus shrinking      | Symbolic execution with Z3         | Mutation of production code |
| Answers                | Does the property survive?     | Can a path violate the contract?   | Would the suite notice?     |
| Best on                | Data and operation spaces      | Small pure, branchy functions      | Fast, stable test suites    |
| Worst on               | Slow external effects          | Floats, strings, heap-heavy code   | Slow or flaky suites        |
| Typical cadence        | Every CI run                   | Targeted or slower CI              | Nightly or pre-release      |
| Counter-example shape  | Shrunk small input             | Concrete satisfying assignment     | Diff of surviving mutant    |
| Pairs naturally with   | Pytest examples and mutmut     | Hypothesis and pytest regressions  | Any existing test style     |

## Pick by question

- "The same relation should hold over many values, and built-in strategies
  describe them." → Lightweight Hypothesis; no selector ceremony is needed.
- "Valid fields depend on one another, data is recursive, or the bug needs a
  sequence of operations." → Advanced Hypothesis with structured strategies or
  `RuleBasedStateMachine`.
- "I want to know whether a small pure function can reach this failed
  assertion or violate this contract." → CrossHair `check`.
- "I refactored a small pure function and want to search for changed
  behaviour." → CrossHair `diffbehavior`.
- "Tests pass; I do not trust that they would catch a defect." → mutmut.
- "I have a useful property and want to know whether its assertion is
  sensitive to wrong code." → Combine Hypothesis and mutmut.

## When to leave the cluster

- **Concurrency:** use scheduler-aware async tests, stress tests, or native race
  detectors.
- **Performance:** use benchmarks and profilers (`python-quality-tools`).
- **System invariants:** use end-to-end tests with a real or simulated
  database, filesystem, process, or network boundary.
- **Native faults:** use sanitizers or coverage-guided fuzzers for extension
  code.

## Common mis-applications

- Replacing a finite standards table with generated values. The table is the
  specification; keep it readable.
- Building a state machine where a normal `@given` test already expresses the
  property.
- Hypothesis driving a real database once per example without transaction
  rollback or a tight integration-test budget.
- CrossHair on string-heavy or heap-heavy code without a bounded timeout.
- mutmut on a slow or flaky suite without narrowing the mutation target.
- All three on every push. Match cadence and cost to the assurance question.
