# ADR 0001: version-pinned Ruff skill with an explicit routing boundary

Date: 2026-07-26

Status: accepted

## Context

Ruff 0.16.0 (2026-07-23) raised the default rule set from 59 rules to
413, began formatting Python code blocks in Markdown files by default,
added native `ruff: ignore` suppression comments, and made several
fields in the JSON output nullable. Ruff 0.15.0 (2026-02-03) shipped the
2026 style guide and block suppressions. Both releases postdate the
training cut-off of current frontier models, so an agent asked about
Ruff's current behaviour will answer from a stale mental model unless a
skill supplies the delta.

The catalogue already touches Ruff in one place:
`python-errors-and-logging/references/ruff-rule-map.md` explains the
TRY/BLE/EM/LOG/N818/PERF203/B017 rules as guidance on how to raise,
catch, and log. That is a rule-level concern, not a tool-level one.

Two questions therefore needed answers: whether the Ruff material should
be a generic `ruff` skill or a version-pinned one, and where the
boundary sits between it and `python-errors-and-logging`.

## Decision

In the context of adding Ruff coverage to the catalogue,

facing the risk that a generic `ruff` skill silently rots as releases
land, and that two skills both claim rule-level questions,

we decided for a version-pinned skill named `ruff-016`, scoped to Ruff
itself — configuration, defaults, suppression, and version deltas — with
rule-level questions about exceptions and logging left to
`python-errors-and-logging`,

and neglected a generic `ruff` skill updated in place, and folding the
material into `python-quality-tools`,

to achieve an honest scope claim (the content is a snapshot of one
release and its delta, and says so) and a single owner for each kind of
question,

accepting that a later release needs its own skill or a deliberate
rename rather than a silent rewrite, and that the router and routing
matrix must both carry the boundary so it is enforced at routing time
rather than discovered by contradiction.

## Consequences

- Both the skill and its references name 0.16.0 explicitly, and
  `docs/skill-catalogue-status.md` carries a maintenance note listing
  what to re-derive when 0.17 ships: the default rule count, the newly
  stabilized rules, and any settings added to `ruff.schema.json`.
- `python-router/SKILL.md` gains a pairing rule and
  `references/routing-matrix.md` gains an anti-routing entry, so the
  boundary is stated on both sides.
- Claims in the skill are sourced from upstream artefacts — the
  changelogs, a `ruff.schema.json` diff across release tags, the rule
  registry in `crates/ruff_linter/src/codes.rs`, and the published
  default-rules page — because recollection is exactly what this skill
  exists to correct.
