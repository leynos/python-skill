# The Ruff 0.16 default rule set

Ruff 0.16.0 enables **413 rules by default**, up from 59. The set is
published at <https://docs.astral.sh/ruff/default-rules/> and is the
authoritative list; this reference exists so the shape can be reasoned
about without fetching the page.

Counts below are for 0.16.0 as released. Patch releases may adjust the
set; verify with `ruff check --show-settings` or the docs page before
making a claim that matters.

## Families and counts

| Prefix  | Linter                    | Rules |
| ------- | ------------------------- | ----- |
| `PYI`   | flake8-pyi                | 47    |
| `UP`    | pyupgrade                 | 42    |
| `F`     | Pyflakes                  | 39    |
| `RUF`   | Ruff-specific             | 36    |
| `PLE`   | Pylint (error)            | 33    |
| `B`     | flake8-bugbear            | 29    |
| `SIM`   | flake8-simplify           | 21    |
| `PLW`   | Pylint (warning)          | 20    |
| `C4`    | flake8-comprehensions     | 17    |
| `FURB`  | refurb                    | 17    |
| `PLR`   | Pylint (refactor)         | 13    |
| `ASYNC` | flake8-async              | 10    |
| `DTZ`   | flake8-datetimez          | 10    |
| `YTT`   | flake8-2020               | 10    |
| `PIE`   | flake8-pie                | 8     |
| `PLC`   | Pylint (convention)       | 8     |
| `PT`    | flake8-pytest-style       | 6     |
| `LOG`   | flake8-logging            | 5     |
| `TRY`   | tryceratops               | 5     |
| `EXE`   | flake8-executable         | 4     |
| `G`     | flake8-logging-format     | 4     |
| `TC`    | flake8-type-checking      | 4     |
| `INT`   | flake8-gettext            | 3     |
| `PERF`  | Perflint                  | 3     |
| `S`     | flake8-bandit             | 3     |
| `E`     | pycodestyle (error)       | 2     |
| `FA`    | flake8-future-annotations | 2     |
| `PTH`   | flake8-use-pathlib        | 2     |

Plus one rule each from `BLE`, `D`, `FLY`, `I`, `ISC`, `N`, `PGH`,
`RET`, `T10`, and `W`. Thirty-four linters in total.

## Where the surprise lives

The single-rule and small families are the ones that catch people out,
because the *family* being on says nothing about which rule is on:

- `I` is **`I001` only** — import sorting is now on by default, and it
  is fixable, so `ruff check --fix` will reorder every import block in
  the repo. `I002` (required imports) is not enabled.
- `E` is **`E722`** (bare `except`) and **`E902`** (IO error) only.
  `E501` line length is *not* in the defaults; the formatter owns line
  length now.
- `W` is **`W605`** (invalid escape sequence) only.
- `D` is **`D419`** (empty docstring) only. No `D1xx` "missing
  docstring" rules, no `D2xx`/`D4xx` style rules.
- `N` is **`N999`** (invalid module name) only. No `N801`/`N802`
  naming rules.
- `S` is **`S102`**, **`S110`**, **`S112`** only — `exec`, and
  `try`/`except: pass|continue`. Not `S101` (`assert`), not the
  request/crypto rules.
- `PTH` is **`PTH124`** and **`PTH210`** only, not the `os.path`
  migration rules.
- `TC` is **`TC004`, `TC005`, `TC007`, `TC010`** — the correctness
  rules, not `TC001`–`TC003` which move imports into `TYPE_CHECKING`.
- `LOG` is **`LOG001`, `LOG002`, `LOG009`, `LOG014`, `LOG015`** — five
  of the seven; `LOG004` and `LOG007` are not enabled. The logging
  surface is partly on by default, so it is not an `extend-select`
  decision from scratch.
- `PT` is six rules; `PGH` is `PGH005`; `RET` is `RET501`; `ISC` is
  `ISC004`; `BLE` is `BLE001`; `T10` is `T100`; `FLY` is `FLY002`.

## The high-churn defaults

On a first run against an existing codebase, expect most of the diff
from:

- **`I001`** — import sorting, fixable.
- **`UP006`, `UP007`, `UP045`** — `List` → `list`, `Union` → `|`,
  `Optional[X]` → `X | None`. In preview these fixes also insert
  `from __future__ import annotations` where needed.
- **`UP031`/`UP032`** — `%` and `.format()` → f-strings.
- **`SIM`** (21 rules) — `SIM102` collapsible `if` and friends.
- **`PYI`** (47 rules) — mostly stub files, but `PYI033` extends to
  `.py` files in preview.
- **`F401`** — unused imports, with a fix that deletes them. Check
  `__init__.py` re-exports before running `--fix` repo-wide.
- **`RUF012`** — mutable class attributes need `ClassVar`.
- **`RUF013`** — implicit `Optional` from a `None` default.
- **`B008`** — function call in a default argument (noisy under
  FastAPI; add a per-file ignore or `lint.flake8-bugbear.extend-immutable-calls`).

## What is deliberately not enabled

Style and opinion families stay off: `ANN` (annotations required),
`ARG` (unused arguments), `COM` (trailing commas), `Q` (quotes),
`D1xx`, `ERA` (commented-out code), `T20` (`print`), `TD`/`FIX`
(TODOs), `EM` (exception message strings), `TRY003`, `SLF001`,
`FBT` (boolean traps), `A` (builtin shadowing), `C901` complexity,
`PLR0913` argument counts, `PLR2004` magic values, the `E711`, `E712`,
`E713`, `E714`, and `E721` comparison rules that a type checker covers
better, the `E741`, `E742`, and `E743` ambiguous-name rules, and `E731`
(lambda assignment).
`E401`/`E402` (import placement) and `F403`/`F405`/`F406` (star imports)
are out as well.

If a project wants any of those, they go in `extend-select`, and each
needs a reason. `EM`, `TRY003`, `TRY300`, `PERF203`, and `N818` are the
opt-in examples on the errors-and-logging surface — see the
`python-errors-and-logging` skill rather than enabling them blind.

Do not reach for `extend-select` across the whole of that surface,
though. `BLE001`, `LOG001`, `LOG002`, `LOG009`, `LOG014`, and `LOG015`
are already on by default, so the question for those is how to satisfy
them, not whether to enable them.

## Restoring the old behaviour

```toml
[tool.ruff.lint]
select = ["E4", "E7", "E9", "F"]
```

This is the documented rollback. Note it is not identical to the
pre-0.16 defaults in every patch release, but it is what Astral
recommends and what the release notes publish.

## Preview history

The expanded default set landed in **preview** in 0.15.2 (412 rules)
and was trimmed slightly in 0.15.6 before stabilizing at 413 in 0.16.0.
A project that ran 0.15.x with `preview = true` has already absorbed
this change; one that did not will meet all of it at once.
