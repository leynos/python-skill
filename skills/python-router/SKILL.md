---
name: python-router
description: Route Python work to the smallest useful skill. Use for Python coding, design, typing, errors and logging, decorators and other abstractions, iterators and generators, data shapes, concurrency, testing, verification, and quality-tool selection.
globs: ["**/pyproject.toml", "**/*.py", "**/*.pyi"]
---

# Python Router

Load this first for non-trivial Python work, then load only the smallest useful
follow-on skill.

## Working stance

- Start from the concrete problem: the failing call, the offending boundary,
  the hot loop, or the leaky exception.
- Prefer one language skill plus at most one domain or quality skill.
- Use the general `leta` skill for code navigation, references, and
  refactors; use `grepai` for semantic search.
- If the answer starts turning into a tutorial, stop and cut back to the
  decision that matters.
- When a local fix needs `Any`, broad `except`, runtime introspection, or a
  metaclass, re-check the design before keeping the patch.
- For testing work, choose the evidence required before choosing the tool.
  More machinery is not automatically more confidence.

## Route by question

- Generics, `TypeVar`, `ParamSpec`, `TypeIs`, `TypeGuard`, `NewType`,
  overloads, typed kwargs, or public API typing: `python-types-and-apis`
- Exception hierarchy, `raise … from …`, narrow `except`, parameterized
  logging, or `logger.exception` discipline: `python-errors-and-logging`
- Decorators, descriptors, context managers, metaclasses, or multiple
  dispatch: `python-abstractions`
- Iterators, generators, lazy pipelines, or refactoring by extracting an
  iterator or context manager: `python-iterators-and-generators`
- `msgspec.Struct`, dataclasses, `TypedDict`, `attrs`, tagged unions, or
  typed kwargs payloads: `python-data-shapes`
- Threads, `asyncio`, `multiprocessing`, or PEP 734 subinterpreters:
  `python-concurrency`
- Named examples, fixtures, finite parameter tables, marks, plugins,
  snapshots, integration boundaries, or async tests: `python-testing`
- A cheap, repeatable invariant across a broad input space, or a parameter
  table that merely samples one relation: `hypothesis`
- Choosing whether to escalate among generated, symbolic, and mutation
  testing: `python-verification`; deep dives in `hypothesis`, `crosshair`,
  `mutmut`
- Dead-code detection, clone and complexity scans, or profiling:
  `python-quality-tools`
- Ruff configuration, settings and CLI changes, selector rewrites,
  suppression comments, the 0.16 default rule set, formatter and
  Markdown behaviour, nullable JSON output, or an upgrade from
  0.14/0.15: `ruff-016`

## Testing hierarchy

This is a decision hierarchy, not a prestige ranking. Pick the first rung whose
evidence matches the question, and stop there.

1. **Named pytest example**: choose `python-testing` when one scenario,
   boundary, regression, rendered output, or error contract matters. The test
   name should explain why that example belongs in the specification.
2. **Parameterized pytest**: choose `python-testing` when the cases form a
   finite truth table or standards corpus and each row has distinct semantic
   meaning. Parametrization removes duplicated test bodies; it should not
   impersonate coverage of an open-ended domain.
3. **Lightweight property test**: choose `hypothesis` when the same invariant,
   round trip, oracle, or metamorphic relation should hold for many cheap,
   repeatable inputs. A growing list of representative parameter rows is the
   usual signal. Start with built-in strategies and default settings.
4. **Structured or stateful property test**: stay with `hypothesis` when valid
   values have dependent fields, recursive structure, or bugs depend on a
   sequence of operations. Custom strategies and `RuleBasedStateMachine` are
   justified here, not before.
5. **Symbolic path exploration**: choose `crosshair` when a small pure
   function carries a contract, every reachable branch matters, and a bounded
   SMT search is tractable. It is especially useful for contracts and
   `diffbehavior`, not as a replacement for ordinary unit tests.

Mutation testing sits beside the hierarchy rather than above it. Choose
`mutmut` when the production behaviour is already specified and the question
is whether the suite would notice a plausible defect.

Leave this hierarchy when the failure depends primarily on a real service,
process boundary, schedule, load, memory use, or native undefined behaviour.
Use integration tests, concurrency or stress tooling, benchmarks and
profilers, or native sanitizers instead.

## Testing selection rubric

Ask these questions in order:

- Is this one meaningful scenario or a finite set of normative cases? Use
  pytest examples or parametrization.
- Should one semantic relation hold over a broad, cheap input space? Use a
  lightweight Hypothesis property.
- Does generating valid input require a domain model, or does operation
  history matter? Escalate within Hypothesis.
- Must every reachable path through a small pure function satisfy a contract?
  Use CrossHair.
- Do the tests pass, but their ability to detect wrong code remains unclear?
  Use mutmut.
- Does the failure depend on external state, scheduling, or performance?
  Leave the property and symbolic tools for a specialist test.

Examples remain valuable at every rung. Keep exact protocol examples and named
regressions beside a property; do not delete readable specification merely
because a generator can rediscover it.

## Pairing rules

- Web or worker boundaries usually pair `python-errors-and-logging` with
  `python-concurrency` or `python-data-shapes`.
- Library API work usually pairs `python-types-and-apis` with
  `python-data-shapes` when the surface is data-shaped, or
  `python-abstractions` when it is behaviour-shaped.
- Refactoring a deep `for` loop usually pairs
  `python-iterators-and-generators` with `python-types-and-apis`.
- A clear lightweight invariant goes straight to `hypothesis`; no selector
  ceremony is required.
- Load `python-verification` when the testing rung or escalation path is
  unclear, then choose one primary adversary. `mutmut` may pair with any rung
  because it audits the suite rather than generating production inputs.
- Ruff rule-family semantics, such as selecting `BLE001` for exception
  handling, belong to `python-errors-and-logging` for the TRY, BLE, EM,
  and LOG families; `ruff-016` covers configuration, defaults,
  suppression, and version deltas.

## Escalate when

- type errors are silenced with `# type: ignore` or `Any` without a comment
  explaining the invariant,
- a public API needs a metaclass, runtime `getattr` dispatch, or `eval`,
- async code grows shared mutable state and cancellation semantics at once,
- a lightweight property needs heavy rejection, recursive generation, or an
  operation model to reach valid cases,
- a critical pure function needs reachable-path scrutiny rather than sampled
  confidence,
- a passing suite gives no evidence that its assertions detect wrong
  behaviour,
- performance claims appear before measurements, or
- `except Exception:` survives review without a documented reason.

Read [routing-matrix.md](references/routing-matrix.md) only when the route
is still unclear.
