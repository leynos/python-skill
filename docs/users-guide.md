# Users' guide

This guide walks through installation, invocation, the routing rules,
and the situations that justify reaching for the verification and
quality-tool skills.

## Installation

Copy the catalogue under Codex's skill directory:

```bash
mkdir -p ~/.codex/skills
cp -a skills/* ~/.codex/skills/
```

The catalogue is self-contained; the only directories Codex needs are
`skills/<name>/SKILL.md` and `skills/<name>/references/*.md`.

## Invocation

The router is the default entry point. Invoke it explicitly in a
session:

```text
Use $python-router to plan this Python task.
```

The router resolves the task to the smallest useful follow-on skill;
each skill loads only its own `SKILL.md` until a reference is needed.
Avoid loading more than one language skill and one domain or quality
skill in the same turn.

For a known pressure point, call the skill directly:

```text
Use $python-types-and-apis to review this `ParamSpec` decorator for
type-checker friendliness.
```

## Routing rules

The router asks a short question list and resolves to a single skill:

- *Typing or public-surface question* → `python-types-and-apis`.
- *Exception or logging question* → `python-errors-and-logging`.
- *Decorator, descriptor, context manager, or metaclass* →
  `python-abstractions`.
- *Iterator or generator refactor* → `python-iterators-and-generators`.
- *Container choice (msgspec, dataclass, TypedDict)* → `python-data-shapes`.
- *Concurrency or subinterpreter question* → `python-concurrency`.
- *Testing pattern, fixture, plugin* → `python-testing`.
- *Verification adversary selection* → `python-verification`, then load
  one of `hypothesis`, `crosshair`, or `mutmut`.
- *Dead code, clones, profiling* → `python-quality-tools`.

Pairing rules:

- Web or worker boundaries usually pair `python-errors-and-logging`
  with `python-concurrency` or `python-data-shapes`.
- Library API work usually pairs `python-types-and-apis` with
  `python-data-shapes` (data-shaped surface) or `python-abstractions`
  (behaviour-shaped surface).
- Verification work always starts with `python-verification`; a deep
  dive follows only after the selector confirms the right tool.

## When to reach for verification

Use the verification cluster when example-based tests cover the
obvious cases but the bug class is broader than the corpus.

- **Hypothesis** — when a property should hold across an input space
  (round-trip, oracle, invariant). Mirrors the rust-skill `proptest`
  deep dive.
- **CrossHair** — when symbolic execution can prove or disprove an
  assertion over a small pure function. Best on parsers, codecs,
  finance code, and refactors validated with `diffbehavior`.
- **mutmut** — when the suite passes consistently and the question
  is whether the tests would notice a regression.

Run Hypothesis on every CI run; run CrossHair and mutmut on slower
cadences.

## When to reach for the quality tools

- **deadcode** — when the question is "is this name still used?".
  Run on changed files in CI; review `--fix` diffs by hand.
- **pyscn** — when the question is "is this branch reachable?", "is
  this block a clone?", or "is this module getting too coupled?".
  Run weekly on `main`; treat findings as a worklist, not a build
  failure.
- **Pyinstrument** — when a request or test is slow and the question
  is "where does the time go?". Use to find hot paths; use
  `pytest-benchmark` to regression-test them.

## Common pitfalls

- Loading two language skills in one turn. Pick the one whose
  decision surface dominates and keep the other in reserve.
- Reaching for a deep dive without first reading `python-verification`.
  The selector cuts most "which tool?" questions in seconds.
- Treating mutation testing as a build gate. The survivor list is a
  worklist; CI should publish the trend, not fail the build.
- Profiling without a baseline. Pyinstrument is most useful as a
  before-and-after comparison.

## Extending the catalogue

Keep new material under `skills/`. Match the shape of the existing
skills: YAML frontmatter, a working stance, a decision surface, red
flags, and references for longer detail. Update
[skill-catalogue-status.md](skill-catalogue-status.md) when adding or
retiring a skill, and (if the change is structural) record the
rationale in
[execplans/initial-skill.md](execplans/initial-skill.md).
