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

The catalogue gains a version-pinned skill named `ruff-016`, scoped to
Ruff itself. `ruff-016` covers Ruff's tool-level concerns —
configuration, defaults, suppression, and version deltas — while the
semantics of exception and logging rules remain the responsibility of
`python-errors-and-logging`.

Two alternatives were considered and rejected: a generic `ruff` skill
updated in place, and folding the material into
`python-quality-tools`.

The version-pinned skill was chosen for two reasons. It makes an honest
scope claim: the skill documents one release, Ruff 0.16.0, together
with the deltas from 0.14.0 onwards, and it names that scope
explicitly. It also gives each concern a clear owner: questions that
mix tool-level and rule-level concerns are handled by pairing
`ruff-016` with `python-errors-and-logging`, so both skills load
together rather than one being chosen over the other.

This decision accepts a trade-off. A later release needs its own
skill or a deliberate rename rather than a silent rewrite, and the
router and routing matrix must both carry the boundary so it is
enforced at routing time rather than discovered by contradiction.

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
