# Skill catalogue status

Snapshot of what is active in `skills/` and what lives elsewhere as
input or supporting material.

## Active skills

### Router

- `python-router` — main entry point. References: `routing-matrix.md`.

### Language

- `python-types-and-apis` — generics, `TypeVar`, `ParamSpec`,
  `TypeIs`/`TypeGuard`, `NewType`, overloads, typed kwargs.
  References: `paramspec-and-typevars.md`,
  `typeis-vs-typeguard.md`,
  `generics-and-newtypes.md`,
  `overloads-and-typed-kwargs.md`.
- `python-errors-and-logging` — exception hierarchies, narrow `except`,
  parameterised logging, Ruff TRY/BLE/EM/LOG/N818/PERF203/B017.
  References: `ruff-rule-map.md`, `logging-recipes.md`.
- `python-abstractions` — decorators, descriptors, context managers,
  metaclasses, multiple dispatch.
  References: `decorators-and-paramspec.md`,
  `context-manager-extraction.md`,
  `descriptors.md`,
  `metaclasses-and-dispatch.md`.
- `python-iterators-and-generators` — iterators, generators, lazy
  pipelines, refactor patterns.
  References: `extracting-iterators.md`, `lazy-pipelines.md`.
- `python-data-shapes` — `msgspec.Struct`, dataclasses, `TypedDict`,
  `NamedTuple`, `attrs`, tagged unions.
  References: `msgspec-structs.md`, `tagged-unions.md`,
  `dataclasses-and-typeddict.md`.
- `python-concurrency` — threads, `asyncio`, `multiprocessing`, and
  PEP 734 subinterpreters.
  References: `subinterpreters-pep734.md`, `workload-shape-matrix.md`,
  `async-task-discipline.md`.

### Domain and quality

- `python-testing` — advanced pytest patterns, async tests,
  parametrisation, plugins.
  References: `fixtures-and-parametrize.md`, `pytest-plugins.md`.
- `python-verification` — selector between Hypothesis, CrossHair,
  and mutmut.
  References: `selection-matrix.md`.
- `python-quality-tools` — `deadcode`, `pyscn`, and Pyinstrument.
  References: `deadcode-and-pyscn.md`, `pyinstrument.md`.

### Verification deep dives

- `hypothesis` — strategy design, the filtering trap, stateful testing,
  CI tiering. References: `strategy-examples.md`,
  `stateful-testing.md`.
- `crosshair` — `check`, `cover`, `diffbehavior`, the Hypothesis
  backend, and the Z3 limits. References: `modes-and-limits.md`.
- `mutmut` — v3 workflow, `pyproject.toml` configuration, the
  triage routine. References: `workflow-and-config.md`.

## Documentation

- [README](../README.md) — installation and quick-start.
- [Users' guide](users-guide.md) — invocation and routing.
- [Initial-skill execplan](execplans/initial-skill.md) — design,
  rationale, and the living progress log.
- [Research notes](research/topic-notes.md) — consolidated firecrawl
  findings on each requested topic with relevance weighting.

## Inputs (not part of the active catalogue)

- `../agent-template-python/template/.rules/python-*.md` — the
  exception/logging, typing, context-manager, generator, return, and
  pyproject rules. The active skills distil this material into
  decision surfaces; the rules files remain authoritative as a style
  reference.
- `../rust-skill.worktrees/skill-refresh/` — the Rust catalogue this
  one is modelled on. Format and routing conventions match.

## Open questions

- Whether to add a `python-pyproject` skill mirroring the Rust
  `arch-crate-design` skill. Deferred: the existing `.rules` material
  is reusable as-is and there is no strong Python-specific decision
  surface yet.
- Whether to add a `python-supply-chain` skill covering `uv` lockfile
  hygiene, `pip-audit`, and SBOM generation. Deferred pending a
  concrete user task.
