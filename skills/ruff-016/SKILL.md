---
name: ruff-016
description: "Use for Ruff 0.16 — the 413-rule default set, `ruff: ignore` and `ruff: file-ignore` suppression comments, Markdown code-block formatting, and the settings, CLI, and rule changes introduced across 0.14.x, 0.15.x, and 0.16.0. Load when upgrading Ruff, writing or reviewing `[tool.ruff]` configuration, or when a Ruff behaviour looks unfamiliar."
globs: ["**/pyproject.toml", "**/ruff.toml", "**/.ruff.toml", "**/*.py", "**/*.pyi", "**/*.md"]
---

# Ruff 0.16

Ruff 0.16.0 (2026-07-23) is the largest behavioural break since 0.1: the
default rule set went from 59 rules to 413, the formatter now touches
Markdown files, and `noqa` has a first-class Ruff-native alternative.
Treat any pre-0.16 mental model of "what Ruff does out of the box" as
wrong.

**Assume your training data predates most of this.** Ruff 0.15.0 shipped
2026-02-03 and 0.16.0 shipped 2026-07-23; both are after the December
2025 cut-off of most current frontier models. Check
`ruff --version` before advising, and prefer the version-delta reference
over recollection.

## Working stance

- Read the project's `[tool.ruff]` or `ruff.toml` before proposing rule
  changes. On 0.16 an empty config is no longer a near-empty rule set.
- An upgrade to 0.16 is a code change, not a tooling bump. Expect a
  large diff on first run, and land it separately from feature work.
- Do not paper over the new defaults with a blanket `ignore` list. Pick
  either the old selectors or the new defaults, deliberately.
- Prefer `ruff: ignore[RULE]` over `noqa: RULE` in new code on 0.16;
  it is Ruff-specific, and an own-line comment placed above a statement
  covers the whole logical line — trailing or mid-construct comments
  cover only their own physical line. A reason is optional.
- Never invent rule codes. If unsure a code exists, run
  `ruff rule <code>` (0.15.17+ also accepts rule names).

## The three changes that break builds

1. **Default rule set: 59 → 413.** `select` now defaults to a broad set
   spanning 34 linters, including `I001` (import sorting), `F401`,
   `UP006`/`UP007`/`UP045` (PEP 585/604 annotation rewrites), `B008`,
   `SIM102`, `RUF012`, and `RUF013`. Notably *absent*: `E501`, the
   `E711`, `E712`, `E713`, `E714`, `E721`, `E731`, `E741`, `E742`, and
   `E743` comparison and ambiguity rules, `D1xx` docstring requirements,
   `ANN`, `ARG`, `S101`, `TRY003`, `EM101`, `COM812`, `Q000`, and
   `PLR0913`. `E722` (bare `except`) remains in the default set.
   See [default-rule-set.md](references/default-rule-set.md).
2. **`ruff format` formats Markdown.** Python code blocks in `.md`
   files are formatted by default, and `.md` files are discovered by
   default. Opt out with `extend-exclude = ["*.md"]`.
3. **JSON output can contain `null`.** `filename`, `location`,
   `end_location`, and `fix.edits[].location`/`end_location` may now be
   `null` instead of `""` and row 1, column 1. Any tooling that parses
   `--output-format json` needs a null check.

## Upgrade decision

Two honest options; pick one and record it.

- **Keep the old surface.** Pin the pre-0.16 defaults explicitly:

  ```toml
  [tool.ruff.lint]
  select = ["E4", "E7", "E9", "F"]
  ```

  This is the documented escape hatch and is the right first move for a
  large codebase mid-release.

- **Adopt the new defaults.** Run `ruff check --fix`, then
  `ruff check --statistics` on the remainder, and triage. Expect the
  bulk of the noise from `I001`, `UP006`/`UP007`, `SIM`, `PYI`, and
  `PLW`. Land the mechanical fixes first, then the judgement calls.

Either way, run `ruff format` in the same commit — the 2026 style guide
landed in 0.15.0 and will reflow lambdas, `except` tuples, and blank
lines at the top of function bodies.

## Suppression comments

Ruff 0.16 supports four forms. `noqa` still works everywhere.

```python
import math  # ruff: ignore[F401]

# ruff: ignore[E501]  covers the whole logical line below
things = [
    "really long string literal ...",
]

# ruff: file-ignore[F401] Re-exports are intentional here
# ruff: disable[E741]
l = 1
# ruff: enable[E741]
```

- `ruff: ignore[...]` — trailing or own-line; own-line covers the entire
  following *logical* line, which `noqa` cannot do.
- `ruff: file-ignore[...]` — whole file, own-line, module scope.
- `ruff: disable[...]` / `ruff: enable[...]` — block range, matching
  codes and indentation. An unmatched `disable` is an implicit range and
  raises `RUF104`.
- `--add-ignore` inserts `ruff: ignore` comments the way `--add-noqa`
  inserts `noqa`. In preview it writes human-readable rule names.

Prefer rule *codes* for stable-mode usage; individual codes may still be
withdrawn in later Ruff releases. Rule *names* in suppression comments
and selectors remain preview-only. See
[suppression-comments.md](references/suppression-comments.md).

## Settings added since 0.14

| Setting                                 | Purpose                                                 |
| --------------------------------------- | ------------------------------------------------------- |
| `extension`                             | Map extensions to `python`/`pyi`/`ipynb`/`markdown`     |
| `format.nested-string-quote-style`      | `alternating` (default) or `preferred` inside f-strings |
| `lint.isort.import-heading`             | Section heading comments, per isort                     |
| `lint.flake8-tidy-imports.ban-lazy`     | Forbid `lazy import` for named modules (3.15+)          |
| `lint.flake8-tidy-imports.require-lazy` | Require `lazy import` where legal (3.15+)               |
| `lint.pylint.max-statements-in-try`     | Threshold for `PLW0717`                                 |
| `lint.ruff.strictly-empty-init-modules` | `RUF067` strictness                                     |
| `analyze.type-checking-imports`         | Include `TYPE_CHECKING` imports in the graph            |

Details, defaults, and the CLI additions are in
[settings-and-cli.md](references/settings-and-cli.md).

## Red flags

- A `pyproject.toml` upgraded to 0.16 with no `select` and no
  discussion of the 413-rule default. Someone will be surprised.
- `extend-select = ["ALL"]`-style configuration on 0.16. The defaults
  already cover the useful ground; `ALL` now buys mostly conflict.
- `# noqa` added in bulk to survive the upgrade. Use `--add-ignore`
  once, with a follow-up issue, or fix the rule family properly.
- CI parsing `--output-format json` without null handling.
- A pre-commit config on 0.16 that expects Markdown to be untouched, or
  one that expects Markdown to be formatted without `types_or` including
  `markdown`.
- Advice citing a rule as "preview" or "stable" without checking:
  twelve rules stabilized in 0.16 and fifteen in 0.15. See
  [rule-and-version-delta.md](references/rule-and-version-delta.md).
