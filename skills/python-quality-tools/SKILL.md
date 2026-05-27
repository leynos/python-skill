---
name: python-quality-tools
description: Use for Python code-quality scanners and profilers beyond unit testing and type-checking — `deadcode` for unused symbols, `pyscn` for unreachable code, clone, and coupling metrics, and Pyinstrument for low-overhead profiling.
globs: ["**/*.py", "**/pyproject.toml"]
---

# Python Quality Tools

Use this when the codebase needs a sanity sweep beyond what `ruff`,
`mypy`, and pytest cover. The three tools here answer different
questions and run on different cadences.

## Working stance

- Run lint, type-check, and tests on every push. Run the heavier
  scanners on a slower cadence.
- Each tool produces a worklist, not a build failure. Triage and
  promote real findings to issues or PRs.
- Pyinstrument is a profiler, not a benchmarker. Use it to find
  hot paths; use `pytest-benchmark` (see `python-testing`) to
  regression-test individual hot paths.

## Decision surface

- **`deadcode`** — name-based unused-symbol detection (Albertas
  Gimbutas's tool). Fast, runs on the whole repo, supports `--fix`
  to delete the dead names. Good for finding orphaned helpers,
  unused imports the linter missed, and obsolete public API.
- **`pyscn`** — Go + tree-sitter analyser. Three signals:
  - Dead-code detection from a control-flow graph (statements after
    `return`, branches behind impossible conditions).
  - Clone detection across Type 1 (identical), 2 (renamed), 3
    (near-miss), and 4 (semantic) similarity.
  - Coupling between objects (CBO) and cyclomatic complexity per
    function.
  Run with `uvx pyscn@latest analyze .`.
- **Pyinstrument** — statistical sampler (default 1 ms). Lower
  overhead than `cProfile`, accurate on tight loops and async event
  loops where deterministic profilers exaggerate small-function cost.

## When to reach for which

- *Unused function or import suspected* → `deadcode`.
- *Unreachable branch behind a refactor* → `pyscn` dead-code report.
- *Copy-pasted block now diverging* → `pyscn` clone report.
- *Cyclic complexity creeping up* → `pyscn` CBO and complexity.
- *Endpoint or test is slow* → Pyinstrument.

## deadcode quick-start

```bash
uv tool run deadcode .                       # list candidates
uv tool run deadcode . --fix                 # rewrite files
uv tool run deadcode . --exclude tests/ --ignore-names "test_*"
```

The tool is name-based, so dynamic dispatch (`getattr`, plugin
registries, ORM attributes referenced from templates) needs an
ignore list. Always review the diff before committing the `--fix`
output.

## pyscn quick-start

```bash
uvx pyscn@latest analyze .                   # everything
uvx pyscn@latest analyze . --json > pyscn.json
uvx pyscn@latest analyze . --check deadcode
uvx pyscn@latest analyze . --check clones --min-similarity 0.85
```

Outputs are table, JSON, and SARIF. The MCP server integration is
useful in editor-side reviews; CLI is enough for CI.

## Pyinstrument quick-start

```bash
uv run pyinstrument script.py
uv run pyinstrument --renderer=speedscope script.py > flame.json
uv run pyinstrument --renderer=html -o report.html script.py
```

Inside a pytest run:

```
uv run pytest --pyinstrument tests/test_hot.py
```

Inside code:

```python
import pyinstrument

with pyinstrument.profile():
    do_the_thing()
```

## Red flags

- A CI job that runs `deadcode --fix` automatically. Removing code
  needs a human review.
- A `pyscn` clone report with no triage. Clones flagged but not
  followed up create noise.
- A Pyinstrument report read in isolation. Compare against a
  baseline; a single profile says little about regressions.
- A `cProfile` flame graph used for async code. Deterministic
  profilers distort event-loop work; switch to Pyinstrument.

Read [deadcode-and-pyscn.md](references/deadcode-and-pyscn.md) and
[pyinstrument.md](references/pyinstrument.md) for invocation patterns,
output interpretation, and the CI tiering that earns the most signal
per minute of compute.
