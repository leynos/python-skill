# Python routing matrix

Use this when the router's question list does not resolve to one skill.

| Symptom or task                                 | Primary skill                     | Common pair                       |
| ----------------------------------------------- | --------------------------------- | --------------------------------- |
| `mypy` or `pyright` flags a `ParamSpec` misuse  | `python-types-and-apis`           | `python-abstractions`             |
| `TypeIs` narrows the wrong branch               | `python-types-and-apis`           | None                              |
| `except Exception` survives review              | `python-errors-and-logging`       | None                              |
| Vendor exception leaks into public API          | `python-errors-and-logging`       | `python-types-and-apis`           |
| Decorator drops type information                | `python-abstractions`             | `python-types-and-apis`           |
| `with` block needs cleanup on exception         | `python-iterators-and-generators` | `python-abstractions`             |
| Deeply nested loop with bookkeeping             | `python-iterators-and-generators` | None                              |
| JSON DTO with discriminator                     | `python-data-shapes`              | `python-types-and-apis`           |
| Frozen, slotted, sub-millisecond struct         | `python-data-shapes`              | None                              |
| Threads block the event loop                    | `python-concurrency`              | `python-errors-and-logging`       |
| CPU-bound pure-Python work across cores         | `python-concurrency`              | `python-data-shapes`              |
| One named regression or exact output            | `python-testing`                  | None                              |
| Finite standards table with meaningful rows     | `python-testing`                  | None                              |
| Parameter rows keep sampling one invariant      | `hypothesis`                      | `python-testing`                  |
| Round trip, idempotence, or differential oracle | `hypothesis`                      | `python-testing`                  |
| Valid data has dependent or recursive structure | `hypothesis`                      | `python-verification`             |
| Failure depends on a sequence of operations     | `hypothesis`                      | `python-verification`             |
| Small pure function needs contract path search  | `crosshair`                       | `hypothesis`                      |
| Pure refactor needs symbolic behaviour diff     | `crosshair`                       | `python-testing`                  |
| Tests pass but mutants survive                  | `mutmut`                          | `python-testing`                  |
| Flaky test relies on time or order              | `python-testing`                  | `python-concurrency`              |
| Real service, load, or resource behaviour       | `python-testing`                  | `python-quality-tools`            |
| Unused symbols and unreachable branches         | `python-quality-tools`            | None                              |
| Hot loop too slow                               | `python-quality-tools`            | `python-iterators-and-generators` |
| Ruff upgrade floods CI with new diagnostics     | `ruff-016`                        | None                              |
| `select` / `ignore` list needs a rewrite        | `ruff-016`                        | `python-errors-and-logging`       |
| `noqa` vs `ruff: ignore` in new code            | `ruff-016`                        | None                              |
| `ruff format` reflowed Markdown unexpectedly    | `ruff-016`                        | None                              |

## Anti-routing

- Do not load `python-abstractions` for a function that just needs a
  decorator pattern shown in `python-types-and-apis/references/`.
- Do not load both `python-iterators-and-generators` and
  `python-abstractions` for the same refactor; pick the one whose decision
  surface dominates.
- Do not route an obvious lightweight invariant through
  `python-verification`; load `hypothesis` directly.
- Do not replace a finite standards table or named regression with generated
  values merely because Hypothesis is available.
- Load `python-verification` when the testing rung or escalation path is
  unclear. Choose one primary adversary; add `mutmut` only when the separate
  question is test-suite sensitivity.
- Do not load `ruff-016` to explain a single diagnostic whose family is
  already covered by a language skill; load it when the question is about
  Ruff itself: configuration, defaults, suppression, or a version delta.
