# Developers' guide

This guide covers working on this repository: the Markdown skill
catalogue itself, its Python test suite, and the `Makefile` gates that
tie the two together. It does not cover using the skills; see
[Users' guide](users-guide.md) for that.

## Prerequisites

- `uv`, for resolving and running the pinned `dev` dependency group.
- `markdownlint` (markdownlint-cli2), `nixie`, and `mdtablefix` on
  `PATH`. These are external tools, not Python dependencies, and the
  lint gates call them directly.

`pyproject.toml` sets `requires-python = ">=3.14"` and
`[tool.uv] package = false`: the repository is not an installable
package, only a source of test tooling for the catalogue's build
process.

## Getting started

`uv.lock` is committed, so `uv run --group dev <tool>` resolves the
pinned versions of every `dev` dependency without a separate
installation step. The `dev` group supplies four tools:

- `pytest` — the test runner.
- `cmd-mox` — stubs external commands, so the test suite never invokes
  a real Markdown tool.
- `mypy` — strict-mode type-checking of `tests/`.
- `hypothesis` — property-based testing, used for one test over
  arbitrary tracked Markdown filenames.

## The gates

`.DEFAULT_GOAL := check`, so a bare `make` runs the full commit gate.
`make check` must pass before committing.

| Target              | What it does                                 |
| ------------------- | -------------------------------------------- |
| `make help`         | Show the target list and descriptions        |
| `make fmt`          | Reflow tables, then apply markdownlint fixes |
| `make markdownlint` | Lint every Markdown file                     |
| `make nixie`        | Validate every Mermaid diagram               |
| `make lint`         | Run `markdownlint` and `nixie`               |
| `make check-fmt`    | Formatting gate; re-runs `markdownlint`      |
| `make typecheck`    | Run `mypy` via `uv`                          |
| `make test`         | Run `pytest` via `uv`                        |
| `make check`        | Default goal; runs every gate above          |

`make fmt` reflows Markdown tables with `mdtablefix` before applying
markdownlint's own fixes; it is deliberately not part of `check`
because it rewrites files, and a commit gate should not mutate the
working tree as a side effect. `check-fmt` does not run
`mdtablefix`, so it can only detect formatting drift, not correct
it.

The `Makefile` sets `SHELL := /bin/bash` and
`.SHELLFLAGS := -eu -o pipefail -c`, so a failure anywhere in a
recipe's pipeline propagates instead of being masked by the exit
status of the pipeline's last command.

## What the tests cover

The test suite lives in `tests/`. It runs `make` against a scratch
git repository so the real `Makefile` is exercised end to end, and
stubs the external Markdown tools with `cmd-mox`, so no third-party
tool actually runs during a unit test. A `hypothesis` property test
drives the file-selection logic over arbitrary tracked Markdown
filenames.

`mypy` runs in strict mode over `tests/` only; the catalogue's
Markdown content is not type-checked, since it contains no Python.

## Testing catalogue boundary

The testing hierarchy is also a routing boundary. Start with named pytest
examples or a finite semantic table in `python-testing`; route a cheap,
repeatable invariant directly to `hypothesis`. Stay with Hypothesis for
dependent, recursive, or stateful generated data, and use CrossHair for
bounded path scrutiny of small pure functions. `mutmut` is orthogonal: it
audits whether the configured test runner notices plausible defects, including
only symbolic checks that runner explicitly invokes. Standalone CrossHair
commands need their own run.

`python-router` owns the first route. `python-verification` is the escalation
selector when the required evidence is unclear; it is not a prerequisite for
an obvious lightweight property. Integration, concurrency, load, performance,
resource, and native-fault questions remain outside this hierarchy and need
their specialist tests or tools.

## Adding Python

Any new Python added to this repository, including test helpers,
follows [Scripting standards](scripting-standards.md). That document
sets the local baseline at Python 3.14, ahead of its own upstream
default, and records the other deliberate divergences kept when
re-importing it.
