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
- *Named test, finite parameter table, fixture, or plugin* →
  `python-testing`.
- *Cheap invariant over a broad input space* → `hypothesis`.
- *Verification escalation or adversary selection* →
  `python-verification`, then one primary deep dive from `hypothesis`,
  `crosshair`, or `mutmut`.
- *Dead code, clones, profiling* → `python-quality-tools`.
- *Ruff configuration, defaults, suppression, or upgrade* → `ruff-016`.

Pairing rules:

- Web or worker boundaries usually pair `python-errors-and-logging`
  with `python-concurrency` or `python-data-shapes`.
- Library API work usually pairs `python-types-and-apis` with
  `python-data-shapes` (data-shaped surface) or `python-abstractions`
  (behaviour-shaped surface).
- A clear lightweight invariant goes straight to `hypothesis`.
  `python-verification` chooses an escalation path when the right
  adversary is unclear.
- `mutmut` may pair with any testing style because it audits the suite
  rather than generating production inputs.

## Testing hierarchy

Pick the first level whose evidence matches the question:

1. **Named pytest example**: one scenario, regression, exact output,
   or error contract matters.
2. **Parameterized pytest**: a finite truth table, standards corpus,
   or set of cases whose rows each carry semantic meaning.
3. **Lightweight Hypothesis**: one round trip, invariant, oracle, or
   metamorphic relation should hold across many cheap, repeatable
   inputs. A growing set of representative parameter rows is the
   usual signal.
4. **Structured or stateful Hypothesis**: valid data has dependent or
   recursive structure, or failures depend on operation history.
5. **CrossHair**: a small pure function needs bounded symbolic
   exploration of contracts or changed behaviour.

Mutation testing sits beside the hierarchy. Use **mutmut** when the
question is whether the current suite would notice a plausible defect.

Leave the hierarchy for integration, scheduling, load, performance,
resource, or native-code failures. Those need real or simulated
boundaries, concurrency or stress tools, benchmarks and profilers, or
native sanitizers.

Examples remain useful beside generated tests. Keep exact protocol
examples and named regressions even when a property searches the wider
domain.

Run lightweight Hypothesis properties on every CI run; run targeted
CrossHair and mutmut on slower cadences.

## When to reach for the quality tools

- **deadcode**: when the question is "is this name still used?".
  Run on changed files in CI; review `--fix` diffs by hand.
- **pyscn**: when the question is "is this branch reachable?", "is
  this block a clone?", or "is this module getting too coupled?".
  Run weekly on `main`; treat findings as a worklist, not a build
  failure.
- **Pyinstrument**: when a request or test is slow and the question
  is "where does the time go?". Use to find hot paths; use
  `pytest-benchmark` to regression-test them.

## When to reach for the Ruff skill

`ruff-016` covers Ruff as a tool rather than any one rule family.

- **Upgrading.** Ruff 0.16.0 raised the default rule set from 59 to
  413, started formatting Python blocks in Markdown files, and made
  fields in the JSON output nullable. An upgrade needs a plan, not a
  version bump.
- **Configuration review.** Whether `select`, `ignore`, and
  `per-file-ignores` still say what the project means under the new
  defaults, and which of the settings added since 0.14.0 apply.
- **Suppression.** `ruff: ignore`, `ruff: file-ignore`, and
  `ruff: disable`/`enable` versus `noqa`, plus `--add-ignore` and the
  `RUF100`–`RUF106` hygiene rules.
- **"Does this rule exist yet?"** The reference tables record what
  stabilized in 0.15.0 and 0.16.0 and what is still preview, material
  that postdates most models' training data.

Rule-level questions about exceptions and logging stay with
`python-errors-and-logging`; its `ruff-rule-map.md` reference is the
decision surface for TRY, BLE, EM, LOG, `N818`, and `PERF203`.

## Common pitfalls

- Loading two language skills in one turn. Pick the one whose
  decision surface dominates and keep the other in reserve.
- Routing an obvious five-line invariant through a verification
  ceremony instead of loading `hypothesis` directly.
- Replacing a finite normative parameter table with generated values.
  The table is the specification.
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
