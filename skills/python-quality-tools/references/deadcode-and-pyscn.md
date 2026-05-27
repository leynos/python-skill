# deadcode and pyscn

The two complementary dead-code detectors. `deadcode` chases unused
names; `pyscn` chases unreachable statements. Run both; treat the
output as a worklist.

## deadcode

Installation:

```bash
uv tool install deadcode
```

Basic invocation:

```bash
uv tool run deadcode .
```

What gets flagged:

- functions, classes, and methods defined but never called,
- variables assigned and never read,
- imports that nothing in the package uses,
- attributes set but never read (subject to ignore lists).

Useful flags:

- `--fix` — rewrite source files to remove the flagged names. Always
  review the diff before committing.
- `--exclude PATH` — skip a directory (commonly `tests/`,
  `migrations/`, generated code).
- `--ignore-names NAME[,NAME]` — keep names that match a glob.
- `--ignore-names-in-files PATH[,PATH]` — keep names in specific files.
- `--no-color`, `--quiet` — CI-friendly output.

Configuration in `pyproject.toml`:

```toml
[tool.deadcode]
exclude = ["tests", "migrations", "src/mypkg/_generated"]
ignore-names = ["test_*", "_setup_*", "Meta"]
```

### Limits

deadcode is name-based; dynamic dispatch (`getattr`, plugin registries,
ORM attributes referenced from templates, fixtures pytest discovers by
name) needs explicit ignores. A false positive is cheap to dismiss; a
false negative is invisible.

## pyscn

Installation needs Go or use uvx:

```bash
uvx pyscn@latest analyze .
```

What pyscn reports:

- **Dead code** — control-flow graph identifies statements after
  `return`/`raise`, branches behind impossible conditions, and
  unreachable `elif`/`else` arms.
- **Clones** — Type 1 (identical), 2 (renamed identifiers), 3
  (near-miss with small changes), 4 (semantic equivalence). The
  threshold is configurable.
- **CBO (coupling between objects)** — per-class import and
  attribute coupling.
- **Cyclomatic complexity** — per-function decision count.

Useful invocations:

```bash
uvx pyscn@latest analyze .                            # everything
uvx pyscn@latest analyze . --check deadcode           # one report
uvx pyscn@latest analyze . --check clones --min-similarity 0.9
uvx pyscn@latest analyze . --json > pyscn.json
uvx pyscn@latest analyze . --sarif > pyscn.sarif
```

The MCP server (built-in) lets editor-side agents query the analysis
on demand:

```bash
uvx pyscn@latest mcp
```

### Interpreting the output

- *Dead code report*: each entry is a file path, a line range, and a
  reason. Investigate; either delete the code or add the test that
  reaches it.
- *Clone report*: each entry pairs two locations. Extract a shared
  helper or accept the duplication with a comment.
- *Coupling report*: a high CBO does not always mean a refactor is
  needed; combine with module-boundary intent.
- *Complexity report*: functions over the threshold are candidates for
  splitting, but the threshold is a heuristic; treat it as a hint.

## Combining the two

```bash
uv tool run deadcode . --no-color > deadcode.txt
uvx pyscn@latest analyze . --check deadcode --json > pyscn.json
```

`deadcode.txt` lists the unused names; `pyscn.json` lists the
unreachable statements. The union is the worklist. A line flagged
by both is a strong candidate for deletion.

## CI tiering

- **Per-push**: run `deadcode` against the changed files only (use
  `--include` if available; otherwise `deadcode src/...`). The cost
  is small.
- **Weekly**: run `pyscn analyze .` on `main`; publish the JSON or
  SARIF artefact.
- **Pre-release**: review the survivor list and triage.

## Common mistakes

- Treating `deadcode --fix` as a one-step command. Always review the
  diff; tests may not reach a "dead" name yet, but the design might.
- Ignoring all `pyscn` clone findings because the project "obviously"
  has shared idioms. Look at the diff; small near-misses often hide
  divergent fixes that should be merged.
- Reading complexity numbers without the function. A 25-branch state
  machine is fine; a 25-branch helper is not.
