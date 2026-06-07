---
name: mutmut
description: "Configure and run mutmut v3 for Python mutation testing — fork-based execution, `[tool.mutmut]` in `pyproject.toml`, the `mutmut browse` TUI, `# pragma: no mutate` suppression, and the discipline of promoting surviving mutants to new tests. Use after `python-verification` confirms mutmut is the right adversary."
---

# mutmut mutation testing for Python

mutmut runs the test suite against systematically mutated versions of
the production code; surviving mutants identify tests that did not
exercise the changed behaviour. The goal is not 100 % kill rate — it
is to use the survivor list as a worklist for the test suite.

## When to apply

Apply when:

- the suite passes consistently and is fast enough to amortize
  mutation runs (single-digit seconds is comfortable; minutes scales
  badly),
- coverage is already high and the question has shifted from "is the
  code reached?" to "would the test notice if it were wrong?",
- a critical pure module (parser, codec, financial calculation) needs
  hardening before it ships.

Do not apply when:

- the suite is flaky; mutmut amplifies flakes,
- the suite is dominated by integration tests that touch real
  services,
- the codebase is mostly type-checked declarations that the type
  checker would catch (filter these out before counting survivors).

## Installation

```toml
[dependency-groups]
dev = [
  "mutmut>=3",
]
```

On Windows, mutmut v3 uses WSL; on POSIX it forks per mutant.

## Configuration

`pyproject.toml`:

```toml
[tool.mutmut]
paths_to_mutate = ["src/"]
pytest_add_cli_args_test_selection = ["tests/"]
runner = "uv run pytest -x --no-header -q"
do_not_mutate = [
  "src/mypkg/_version.py",
  "src/mypkg/migrations/",
]
also_copy = [
  "src/mypkg/data/*.json",
]
```

In `pyproject.toml`, mutmut v3 requires path-shaped settings to be
arrays. `paths_to_mutate = "src/"` (a scalar string) is accepted in
`setup.cfg` but rejected or silently ignored under `[tool.mutmut]`;
keep the brackets.

`runner` is the suite invocation. `-x` and `-q` speed the per-mutant
run. `do_not_mutate` skips generated code, version files, and
boilerplate where mutation has no signal.

## Workflow

```bash
uv run mutmut run                    # run all mutants
uv run mutmut browse                 # TUI: pick a survivor and inspect
uv run mutmut show 42                # diff of mutant 42
uv run mutmut apply 42               # write the diff to the file
uv run mutmut results                # numeric summary
```

For an individual file:

```bash
uv run mutmut run src/mypkg/parse.py
```

`mutmut browse` is the everyday UI: navigate to a survivor, read the
diff, decide whether the survivor is a test gap, dead code, or a
mutation that does not change behaviour (a true equivalent mutant).

## Suppressing a line

```python
def serialise(x: int) -> str:
    return str(x)               # pragma: no mutate
```

Use sparingly; every suppression is a place mutmut will not check.

## Pairing with the type checker

A mutant that changes `int` arithmetic to bitwise operations might be
caught by `mypy`/`pyright` before pytest runs. Filter these out:

```toml
[tool.mutmut]
runner = "uv run mypy src/ && uv run pytest -x -q"
```

Now the survivor list excludes mutants the type system already
catches; the remaining survivors are real test gaps.

## Triage discipline

Each surviving mutant fits one of four categories:

1. **Real test gap**: add a test that fails on the mutated code.
2. **Equivalent mutant**: the mutation does not change behaviour
   (`+ 0`, `* 1`). Add `# pragma: no mutate` with a comment.
3. **Dead code**: the mutation lives in code no test reaches because
   the code is unreachable. Delete the code; pair with
   `python-quality-tools` (pyscn).
4. **Untestable boundary**: the mutation requires real I/O the suite
   does not perform. Document and move on.

Track the survivor count over time; a rising count signals tests have
regressed.

## CI tiering

- **Per-push**: do not run mutmut. The cost is high.
- **Nightly or weekly**: full `mutmut run` on `main`, publish the
  survivor count.
- **Pre-release**: run mutmut on the modules touched in the release.

Pair with `pytest-xdist` to parallelize the suite each mutant runs.

## Hard-won lessons

- **Aim for a falling survivor count, not zero.** Zero is achievable
  only for tiny pure modules; the cost on a real codebase exceeds
  the value.
- **Filter the noise first.** Type-checker filtering and explicit
  `do_not_mutate` lists cut the survivor count to the meaningful
  set.
- **Triage every survivor.** Unreviewed survivors hide the real
  test gaps in a sea of equivalents.
- **Mutmut measures the suite, not the code.** A surviving mutant
  is a test gap; the production code is not the bug.

## References

- [mutmut documentation](https://mutmut.readthedocs.io/) and
  [GitHub repository](https://github.com/boxed/mutmut).
- [mutmut v3 release notes](https://mutmut.readthedocs.io/en/latest/index.html#whats-new-in-version-3).
- [`references/workflow-and-config.md`](references/workflow-and-config.md)
  for end-to-end project setup and a triage cheat sheet.
- Selection between mutmut and other verification tools lives in
  [`../python-verification/SKILL.md`](../python-verification/SKILL.md).
