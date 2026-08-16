# ExecPlan: initial Python skill catalogue

## Big picture

Build an advanced Python skill set modelled on `rust-skill.worktrees/skill-refresh`.
A single router resolves a Python task to the smallest useful first-class skill;
deep dives back the heaviest verification tools. The exception, logging, typing,
and context-manager rules from `agent-template-python/template/.rules` are
restated as decision surfaces, not enforced rules.

## Constraints

- Each `SKILL.md` follows the rust-skill format: YAML frontmatter (`name`,
  `description`, optional `globs`), a working stance, a decision surface,
  red flags, and pointers into `references/`.
- Keep each `SKILL.md` under ~120 lines; push tables and worked examples to
  `references/*.md`.
- Catalogue tone: helpful technical lead, no superlatives, no life-coach prose.
- All English (en-GB), Oxford spelling, no emojis.
- Skills live under `skills/<name>/SKILL.md` with optional
  `references/*.md` siblings.

## Catalogue topology

Router:

- `python-router`

Language skills:

- `python-types-and-apis` — typing, generics (PEP 695), `TypeVar`,
  `ParamSpec`, `TypeIs`/`TypeGuard`, `NewType`, overloads, typed kwargs.
- `python-errors-and-logging` — exception hierarchies, narrow `except`,
  EM-style messages, parameterized logging, `logger.exception`.
- `python-abstractions` — decorators, descriptors, metaclasses, context
  managers (function and class form), multiple dispatch.
- `python-iterators-and-generators` — iterators, generators, lazy pipelines,
  refactoring by extracting an iterator or a context manager.
- `python-data-shapes` — `msgspec.Struct`, dataclasses, `TypedDict`,
  `attrs`, typed kwargs, tagged unions.
- `python-concurrency` — threads, asyncio, multiprocessing, and PEP 734
  subinterpreters.

Domain and quality skills:

- `python-testing` — pytest at depth: fixtures, parametrization, marks,
  plugin ecosystem, snapshot testing, async tests.
- `python-verification` — selector between Hypothesis, CrossHair, mutmut.
- `python-quality-tools` — deadcode, pyscn, Pyinstrument.
- `ruff-016` — Ruff 0.16 defaults, suppression comments, settings and
  CLI deltas (added after the initial catalogue; see the progress log).

Deep dives:

- `hypothesis`
- `crosshair`
- `mutmut`

## Reference document plan

Each language skill carries 2–4 reference documents covering the longer
comparison tables and worked examples. Examples:

- `python-types-and-apis/references/`
  - `paramspec-and-typevars.md`
  - `typeis-vs-typeguard.md`
  - `generics-and-newtypes.md`
  - `overloads-and-typed-kwargs.md`
- `python-errors-and-logging/references/`
  - `ruff-rule-map.md`
  - `logging-recipes.md`
- `python-abstractions/references/`
  - `decorators-and-paramspec.md`
  - `context-manager-extraction.md`
  - `descriptors.md`
  - `metaclasses-and-dispatch.md`
- `python-iterators-and-generators/references/`
  - `extracting-iterators.md`
  - `lazy-pipelines.md`
- `python-data-shapes/references/`
  - `msgspec-structs.md`
  - `tagged-unions.md`
  - `dataclasses-and-typeddict.md`
- `python-concurrency/references/`
  - `subinterpreters-pep734.md`
  - `workload-shape-matrix.md`
  - `async-task-discipline.md`
- `python-testing/references/`
  - `fixtures-and-parametrize.md`
  - `pytest-plugins.md`
- `python-verification/references/`
  - `selection-matrix.md`
- `python-quality-tools/references/`
  - `deadcode-and-pyscn.md`
  - `pyinstrument.md`
- `hypothesis/references/`
  - `strategy-examples.md`
  - `stateful-testing.md`
- `crosshair/references/`
  - `modes-and-limits.md`
- `mutmut/references/`
  - `workflow-and-config.md`

## Documents

- `README.md` — rebuild adapted to Python: installation under `~/.codex/skills`,
  a quick-start, feature list, learn-more links, acknowledgements (mirroring
  rust-skill), MIT licence note.
- `docs/users-guide.md` — installation, invocation, routing examples.
- `docs/skill-catalogue-status.md` — what is active, what is research input.

## Validation

- Each `SKILL.md` is under ~120 lines and contains the four required sections.
- Each language skill references at least one `references/*.md` for its
  longest topic.
- The router lists every active skill and reaches each via a question prompt.
- The README links to the router and to the users' guide.

## Living-document discipline

Update this plan after each milestone with:

- Skills completed (path and line count).
- Open questions raised by writing the skill that need follow-up research.
- Drift from the catalogue topology, with justification.

## Progress log

- 2026-05-27: research consolidated in `docs/research/topic-notes.md`;
  catalogue topology fixed; directory skeleton created; execplan written.
- 2026-05-27 (continued): all thirteen `SKILL.md` files written
  (`python-router`, six language skills, `python-testing`,
  `python-verification`, `python-quality-tools`, and the
  `hypothesis`/`crosshair`/`mutmut` deep dives) along with their
  reference documents. README, users' guide, catalogue-status, and
  LICENSE written. Skill line counts: language and domain skills 67–111
  lines; deep dives 146–159 lines (in line with rust-skill's
  `proptest/SKILL.md` precedent of 226 lines).

## Validation outcome

- Each language skill carries the four required sections (working
  stance, decision surface, red flags, references) and at least one
  `references/*.md` for its dominant decision surface.
- The router lists every active skill and reaches each via a question
  prompt; the routing matrix carries the secondary cases.
- README links to the router and to the users' guide;
  `skill-catalogue-status.md` enumerates active skills with their
  references.

- 2026-05-27 (continued): LICENSE switched from MIT to ISC per user
  direction (copied from `../actix-v2a/LICENSE`); README updated
  accordingly. `python-concurrency/SKILL.md` Async discipline section
  expanded to cover `TaskGroup` as default, `gather` caveats,
  `cancel()` as a request, `shield` rules, and custom task factories
  (including `eager_task_factory`). New reference document
  `python-concurrency/references/async-task-discipline.md` written
  with the firecrawl-sourced detail; SKILL.md trailing links and
  `skill-catalogue-status.md` updated to reference it.

- 2026-07-26: `ruff-016` added as a fourth domain-and-quality skill
  (`skills/ruff-016/SKILL.md` plus `default-rule-set.md`,
  `suppression-comments.md`, `settings-and-cli.md`, and
  `rule-and-version-delta.md`). This departs from the original topology,
  and the departure is justified: Ruff 0.16.0 changed the default rule
  set from 59 rules to 413, began formatting Markdown code blocks, and
  added native `ruff: ignore` suppression, all after the training
  cut-off of current models. Routing boundary recorded in
  [ADR 0001](../adr/0001-ruff-skill-routing-boundary.md). Every factual
  claim was sourced from upstream artefacts (the `astral-sh/ruff`
  changelogs, a `ruff.schema.json` diff across the 0.14.0/0.15.0/0.16.0
  tags, `crates/ruff_linter/src/codes.rs` at 0.16.0, and a parse of the
  published default-rules page) rather than recollection. The schema
  diff caught one error: `lint.ruff.parenthesize-tuple-in-subscript`
  already existed in 0.14.0 and was dropped from the new-settings table.
  Maintenance trigger for Ruff 0.17 is recorded in
  `docs/skill-catalogue-status.md`.

- 2026-08-16: the repository gained `pyproject.toml`, `uv.lock`, a
  `tests/` suite (pytest, cmd-mox, hypothesis, mypy strict), and a
  `Makefile` wiring the lint, format, type-check, and test gates
  together. `typecheck` and `test` were previously no-op targets and
  now run real tools. `docs/scripting-standards.md` was imported from
  `agent-template-python`, with the local baseline set to Python 3.14.
  This is drift from the original Markdown-only topology, and the
  drift is justified: the `Makefile`'s own behaviour — file selection
  via `git ls-files`, failure propagation through `pipefail`, and
  `--` option-terminator handling before `mdtablefix` — was carrying
  real defects that only tests could catch. New documentation:
  `docs/developers-guide.md`, covering the gates and the test suite
  for anyone working on this repository rather than using the skills.

## Open follow-up (deferred)

- A `python-pyproject` skill mirroring `arch-crate-design` (the
  `agent-template-python` rules currently cover this material;
  deferred until a concrete user task surfaces).
- A `python-supply-chain` skill covering `uv` lockfiles, `pip-audit`,
  and SBOM generation (deferred for the same reason).
