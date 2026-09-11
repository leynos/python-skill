# Agent Instructions

Guidance for agents working in this repository. Read this before
changing tracked files.

## Commit gates

Prefer `Makefile` targets over running tools directly, and run the
gates sequentially rather than in parallel: this repository relies on
build caching, and sequential runs benefit from it.

Run the full sequence before committing:

```bash
make check-fmt
make lint
make typecheck
make test
```

`make check` is the default goal and runs the same four gates in one
command.

## Changes under `skills/`

Every skill is a directory containing a `SKILL.md` whose YAML
frontmatter is an Agent Skills manifest. The manifest `name` is the
discovery name: a skill whose manifest omits it, or gives it as an
empty string, is not discoverable by a strict loader.

`make lint` depends on `skill-manifest-check`, so the manifest
contract is already enforced by the commit gates above. When adding,
renaming, or editing anything under `skills/`, the following are
required:

- Run `make lint`. It runs `skill-frontmatter-lint` (`yamllint` over
  each extracted frontmatter block) and `skill-manifest-validate`
  (`skills-ref validate` over each skill directory). Both must pass
  before committing.
- Run `make test`. `tests/test_skill_manifests.py` asserts that every
  shipped manifest satisfies the contract, and that `make lint` still
  enforces it.
- Keep the directory name equal to the manifest `name`.
- Keep `metadata`, when present, a mapping of strings to strings.
  `skills-ref` coerces every value with `str(v)` rather than rejecting
  other shapes, so a list or mapping value passes validation but
  reaches consumers as a Python repr. Encode multi-valued entries as a
  single string, such as the comma-separated `globs` pattern list.

Do not weaken these checks to make a manifest pass. Fix the manifest
instead of excluding it from `SKILL_DIRS` or relaxing the `yamllint`
configuration.

To check one skill or a fixture while iterating:

```bash
make skill-manifest-check SKILL_DIRS=skills/ruff-016/
```

## Documentation

Changes that alter skill discovery, installation, or naming belong in
[the users' guide](docs/users-guide.md). Changes to validation tooling,
`Makefile` targets, or development dependencies belong in
[the developers' guide](docs/developers-guide.md).
