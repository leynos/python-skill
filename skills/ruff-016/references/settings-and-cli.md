# Settings, formatter, and CLI: 0.14.0 → 0.16.0

Every configuration key added between 0.14.0 and 0.16.0, plus the
formatter and CLI changes that go with them. Nothing was removed from
the settings schema over this range.

Full reference: <https://docs.astral.sh/ruff/settings/>.

## New settings

### `extension` (top level, 0.16.0; preview in 0.15.3)

Maps file extensions to a known language: `python`, `pyi`, `ipynb`, or
`markdown`. Mapped extensions are added to `include` automatically as
`*.{ext}`, so they are discovered without further configuration.

```toml
[tool.ruff]
extension = { mdx = "markdown", qmd = "markdown" }
```

This replaces the built-in `.qmd` handling, which was dropped in
0.15.3. There is a matching `--extension` CLI flag, which overrides the
file setting.

### `format.nested-string-quote-style` (0.16.0; preview in 0.15.9)

Quote style for strings nested inside interpolated expressions.

- `alternating` (default) — `f"{data['key']}"`
- `preferred` — `f"{data["key"]}"`, using `format.quote-style`

No effect below Python 3.12, which cannot reuse the outer quote.

### `lint.isort.import-heading` (0.16.0)

Map of section name to heading comment; Ruff inserts or replaces the
comment above each section. Compatible with isort's
`import_heading_{section}` options.

```toml
[tool.ruff.lint.isort.import-heading]
future = "Future"
standard-library = "Standard library"
third-party = "Third party"
first-party = "First party"
local-folder = "Local"
```

Custom section names are accepted as additional keys.

### `lint.flake8-tidy-imports.ban-lazy` and `require-lazy` (0.16.0)

Both only apply when targeting **Python 3.15 or newer**, where the
`lazy import` statement exists. Each takes either `"all"` or an
include/exclude selector:

```toml
[tool.ruff.lint.flake8-tidy-imports]
require-lazy = { include = "all", exclude = ["mypkg.config"] }
ban-lazy = ["django", "mypkg.plugins"]
```

- `require-lazy` — imports that *must* use `lazy`. Contexts where
  `lazy import` is illegal (function and class bodies, `try`/`except`,
  `__future__` imports, `from … import *`) are skipped.
- `ban-lazy` — imports that must **not** be lazy.

Both drive **`TID254`** (`lazy-import-mismatch`, preview). The related
**`TID255`** (`lazy-import-immediately-resolved`, preview) flags a lazy
import whose binding is used eagerly anyway.

### `lint.pylint.max-statements-in-try` (0.16.0)

Threshold for **`PLW0717`** (`too-many-statements-in-try-clause`,
preview), added in 0.15.14.

### `lint.ruff.strictly-empty-init-modules` (0.15.0)

When true, **`RUF067`** (`non-empty-init-module`, preview) requires
`__init__.py` to be entirely empty — no imports, no docstring.

### `analyze.type-checking-imports` (0.15.0)

Whether `ruff analyze graph` includes imports inside
`if TYPE_CHECKING:` blocks. Defaults to `true`; set `false` to exclude
them. Matching CLI option added in 0.14.6.

## Changed settings

- `line-length` accepts a larger maximum since 0.15.13.
- `target-version` accepts `py315` (preview from 0.14.11).
- Default and maximum Python versions moved to 3.14 in 0.14.0.
- Extended configuration files are now all resolved before Ruff falls
  back to a default Python version (0.15.0).
- `required-version` is checked before rules are parsed (0.14.11).

## Formatter

### Markdown code blocks (default-on in 0.16.0)

`ruff format` formats Python code blocks in Markdown files, and `.md`
files are part of default discovery.

- Info strings formatted: `python`, `py`, `python3`, `py3`, `pyi`.
  `pycon` blocks are supported too. `pyi` blocks use stub style.
- Quarto-style `{python}` fences are handled.
- Unlabelled fences are left alone.
- A block that does not parse, or that would not round-trip, is
  skipped.
- Suppression: normal `# fmt: off` / `# fmt: on` inside the block, or
  HTML comments around blocks — `<!-- fmt:off -->` / `<!-- fmt:on -->`,
  and the blacken-docs spellings `<!-- blacken-docs:off -->` /
  `<!-- blacken-docs:on -->`. An `off` without a matching `on` runs to
  the end of the document.
- Opt out entirely with `extend-exclude = ["*.md"]`.
- Under `ruff-pre-commit`, Markdown must be opted in via `types_or`:

  ```yaml
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.16.0
    hooks:
      - id: ruff-format
        types_or: [python, pyi, markdown]
  ```

The LSP formats Markdown too, since 0.15.1.

### 2026 style guide (0.15.0)

`ruff format` output changed. Reformat in a dedicated commit.

- Lambda parameters stay on one line; lambda bodies gain parentheses so
  they can break.
- Parentheses around exception tuples in `except` are removed on
  Python 3.14+.
- A single blank line is now permitted at the start of a function body.
- Long `as` captures in `match` avoid parentheses.
- Extra spaces between an escaped quote and a closing triple quote may
  be dropped.
- Blank lines are enforced before decorated classes in stub files.

## CLI

| Version | Change                                                                                                                                                      |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0.14.5  | `--add-noqa` accepts a reason; `--help` is colourized                                                                                                       |
| 0.14.6  | `ruff analyze` can skip `TYPE_CHECKING` imports; clickable diagnostic links                                                                                 |
| 0.14.7  | Partial-fixability indicator in `--statistics`                                                                                                              |
| 0.15.0  | `--color` to force colour; `--output-format` respected in `--watch` (now defaulting to `full`)                                                              |
| 0.15.17 | `ruff rule` accepts rule names, not just codes                                                                                                              |
| 0.15.21 | `ruff format --extend-exclude`                                                                                                                              |
| 0.16.0  | `--add-ignore`; `check` and `format --check` render fix diffs inline; `format --check` supports every linter output format, including `github` and `gitlab` |

### JSON output is now nullable

In `--output-format json`, these fields may be `null` rather than the
old `""` / row 1, column 1 placeholders:

- `filename`
- `location`, `end_location`
- `fix.edits[].location`, `fix.edits[].end_location`

Anything consuming Ruff JSON — dashboards, review bots, CI
annotations — needs a null check before 0.16 lands.

### `format --check` in CI

```console
$ ruff format --check --output-format github .
::error title=ruff (unformatted),file=try.md,line=2,col=8,...
```

`--silent` suppresses the diagnostic body while keeping the exit code.
