# mutmut workflow and configuration

Project setup and the day-to-day triage routine.

## End-to-end setup

```toml
# pyproject.toml
[dependency-groups]
dev = [
  "mutmut>=3",
  "pytest-xdist>=3",                 # for parallel test runs
]

[tool.mutmut]
paths_to_mutate = ["src/"]
pytest_add_cli_args_test_selection = ["tests/"]
runner = "uv run pytest -x --no-header -q -p no:cacheprovider"
do_not_mutate = [
  "src/mypkg/_version.py",
  "src/mypkg/_generated/",
  "src/mypkg/migrations/",
]
also_copy = ["src/mypkg/data/*.json"]
```

What each option buys:

- `paths_to_mutate` (array) — restrict mutation to your code, not
  vendored dependencies. Must be a TOML array under `[tool.mutmut]`;
  a scalar string is silently rejected.
- `pytest_add_cli_args_test_selection` (array) — extra arguments
  passed through to the runner to narrow test discovery. Also an
  array under `[tool.mutmut]`.
- `runner` — the suite invocation. `-x` aborts on the first failure
  (a killed mutant); `-q` reduces noise.
- `-p no:cacheprovider` avoids contaminating the pytest cache across
  forks.
- `do_not_mutate` — version files, generated code, and migrations
  produce noise; skip them.
- `also_copy` — non-Python data the tests need.

## Running the suite

```bash
uv run mutmut run                   # full sweep
uv run mutmut run src/mypkg/parse.py    # one file
uv run mutmut run --no-progress     # CI-friendly output
```

The first run is the slowest; subsequent runs reuse the per-mutant
hash and skip unchanged code.

## The browse TUI

```bash
uv run mutmut browse
```

Keys:

- arrow keys — navigate.
- `enter` — open the mutant diff.
- `s` — show source context.
- `k` — mark as killed (sanity check; mutmut already tracked it).

Use `browse` to triage survivors interactively. The terminal output of
`mutmut results` is useful for CI logging but slow to consume.

## Triage cheat sheet

| Survivor diff                                     | Likely cause                | Action                                  |
| ------------------------------------------------- | --------------------------- | --------------------------------------- |
| `+ 0`, `* 1`, `- 0`, `// 1`                       | Equivalent mutant            | `# pragma: no mutate` with a one-liner  |
| `return True` → `return False` on a getter        | Tests asserted only one branch | Add the other-branch test            |
| Boolean operator flipped (`and` → `or`)           | Test exercised the easy path | Add a case where the operator matters  |
| `>` → `>=`                                        | Boundary case missing        | Add a boundary test                    |
| `raise FooError` → `raise BarError`               | Tests asserted exception group, not type | Use `pytest.raises(FooError)`  |
| Constants changed (e.g. `42` → `43`)              | Constants not tested         | Add a test that pins the constant      |

## Type-checker filtering

Wrap the runner so the type checker runs first; mutants that fail
type-checking never reach pytest:

```toml
[tool.mutmut]
runner = "uv run mypy src/ && uv run pytest -x -q"
```

Mutants caught by the type checker are killed quickly; the survivor
list reflects real behavioural gaps.

## CI integration

```yaml
# .github/workflows/mutation.yml (sketch)
- name: Mutation test
  run: |
    uv run mutmut run
    uv run mutmut results --status all > mutmut_summary.txt
- name: Upload summary
  uses: actions/upload-artifact@v4
  with:
    name: mutmut-summary
    path: mutmut_summary.txt
```

Run nightly, not per-push. Track the survivor count over time; a
rising trend is a regression in the suite.

## Common mistakes

- Running mutmut against a flaky suite. The flakes appear as
  random kills; triage becomes impossible.
- Counting all surviving mutants as test gaps. The equivalent
  fraction is real and can dominate; triage matters more than the
  number.
- Mutating generated code, migrations, or auto-generated client
  bindings. The signal is noise.
- Treating `# pragma: no mutate` as a build-passing trick. Each
  pragma is a deliberate decision; document it.
