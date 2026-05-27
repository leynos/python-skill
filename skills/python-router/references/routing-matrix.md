# Python routing matrix

Use this when the router's question list does not resolve to one skill.

| Symptom or task                                | Primary skill                       | Common pair                     |
| ---------------------------------------------- | ----------------------------------- | ------------------------------- |
| `mypy` or `pyright` flags a `ParamSpec` misuse | `python-types-and-apis`             | `python-abstractions`           |
| `TypeIs` narrows the wrong branch              | `python-types-and-apis`             | —                               |
| `except Exception` survives review             | `python-errors-and-logging`         | —                               |
| Vendor exception leaks into public API         | `python-errors-and-logging`         | `python-types-and-apis`         |
| Decorator drops type information               | `python-abstractions`               | `python-types-and-apis`         |
| `with` block needs cleanup on exception        | `python-iterators-and-generators`   | `python-abstractions`           |
| Deeply nested loop with bookkeeping            | `python-iterators-and-generators`   | —                               |
| JSON DTO with discriminator                    | `python-data-shapes`                | `python-types-and-apis`         |
| Frozen, slotted, sub-millisecond struct        | `python-data-shapes`                | —                               |
| Threads block the event loop                   | `python-concurrency`                | `python-errors-and-logging`     |
| CPU-bound pure-Python work across cores        | `python-concurrency`                | `python-data-shapes`            |
| Flaky test relies on time or order             | `python-testing`                    | `python-verification`           |
| Bug shrinks to a minimal counter-example       | `hypothesis`                        | `python-testing`                |
| Two implementations disagree                   | `crosshair`                         | —                               |
| Tests pass but mutants survive                 | `mutmut`                            | `python-testing`                |
| Unused symbols and unreachable branches        | `python-quality-tools`              | —                               |
| Hot loop too slow                              | `python-quality-tools`              | `python-iterators-and-generators` |

## Anti-routing

- Do not load `python-abstractions` for a function that just needs a
  decorator pattern shown in `python-types-and-apis/references/`.
- Do not load both `python-iterators-and-generators` and
  `python-abstractions` for the same refactor; pick the one whose decision
  surface dominates.
- Do not load any deep dive without first reading the relevant selector
  skill (`python-verification`).
