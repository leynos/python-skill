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
- pytest at depth: fixtures, parametrization, marks, plugins, snapshots,
  async tests: `python-testing`
- Selecting between Hypothesis, CrossHair, and mutmut: `python-verification`;
  deep dives in `hypothesis`, `crosshair`, `mutmut`
- Dead-code detection, clone and complexity scans, or profiling:
  `python-quality-tools`
- Ruff configuration, settings and CLI changes, selector rewrites,
  suppression comments, the 0.16 default rule set, formatter and
  Markdown behaviour, nullable JSON output, or an upgrade from
  0.14/0.15: `ruff-016`

## Pairing rules

- Web or worker boundaries usually pair `python-errors-and-logging` with
  `python-concurrency` or `python-data-shapes`.
- Library API work usually pairs `python-types-and-apis` with
  `python-data-shapes` (when the surface is data-shaped) or
  `python-abstractions` (when it is behaviour-shaped).
- Refactoring a deep `for` loop usually pairs
  `python-iterators-and-generators` with `python-types-and-apis`.
- Verification work loads `python-verification` first to choose the tool,
  then exactly one of `hypothesis`, `crosshair`, or `mutmut`.
- Ruff rule-family semantics, such as selecting `BLE001` for exception
  handling, belong to `python-errors-and-logging` for the TRY, BLE, EM,
  and LOG families; `ruff-016` covers configuration, defaults,
  suppression, and version deltas.

## Escalate when

- type errors are silenced with `# type: ignore` or `Any` without a comment
  explaining the invariant,
- a public API needs a metaclass, runtime `getattr` dispatch, or `eval`,
- async code grows shared mutable state and cancellation semantics at once,
- performance claims appear before measurements,
- `except Exception:` survives review without a documented reason.

Read [routing-matrix.md](references/routing-matrix.md) only when the route
is still unclear.
