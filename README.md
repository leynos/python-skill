# python-skill

*A compact Python skill catalogue for Codex, shaped to help with real Python
work without drowning out the work itself.*

This repository carries an advanced Python skill set modelled on the
`rust-skill` catalogue: a single router, a handful of focused language
skills, a verification selector with three deep dives, and a quality-tools
skill for the scanners and profilers beyond unit testing and type-checking.

______________________________________________________________________

## Why python-skill?

- **Small default load**: One router and a small set of first-class skills;
  references carry the longer comparison material.
- **Python-specific judgement**: The catalogue focuses on typing decisions,
  errors and logging, abstractions, iterators and generators, data shapes,
  concurrency, testing, verification, and quality tooling.
- **Clear routing**: `python-router` directs to the smallest useful skill
  instead of loading half the catalogue at once.
- **Practical tone**: The skills aim to sound like a helpful technical lead,
  not a tutorial.

______________________________________________________________________

## Quick start

### Installation

```bash
mkdir -p ~/.codex/skills
cp -a skills/* ~/.codex/skills/
```

### Basic usage

```text
Use $python-router to route this Python task, then help me design the
exception hierarchy for a payments service.
```

When the pressure point is already known, call the skill directly:

```text
Use $python-errors-and-logging to review this handler's `except` clauses
for a publishable library.
```

______________________________________________________________________

## Features

- One router, six language skills, and four domain or quality skills.
- Short `SKILL.md` files, with references for the longer comparison material.
- Coverage for typing (PEP 612, PEP 695, PEP 696, PEP 698, PEP 742),
  exceptions and logging (Ruff TRY/BLE/EM/LOG/N818/PERF203/B017),
  decorators and descriptors, context-manager extraction, iterator
  refactors, msgspec-shaped data, dataclass and TypedDict choices, and
  PEP 734 subinterpreters.
- Verification skills covering selection plus deep dives for
  `hypothesis`, `crosshair`, and `mutmut`.
- Quality-tool skill for `deadcode`, `pyscn`, and Pyinstrument.

______________________________________________________________________

## Learn more

- [Users' guide](docs/users-guide.md) — installation, invocation, routing,
  and when to reach for the verification or quality-tool skills.
- [Skill catalogue status](docs/skill-catalogue-status.md) — what is
  active and what is research input.
- [Initial-skill execplan](docs/execplans/initial-skill.md) — design,
  rationale, and validation history for the catalogue.
- [Python router](skills/python-router/SKILL.md) — the main entry point.
- [Types and APIs](skills/python-types-and-apis/SKILL.md) — generics,
  `TypeVar`, `ParamSpec`, `TypeIs`, overloads, typed kwargs.

______________________________________________________________________

## Acknowledgements

This catalogue draws on the Python rules and guides shipped with
`agent-template-python` (exceptions and logging, typing, context managers,
generators, return discipline, pyproject layout) and on the structure
established by the [`rust-skill`](https://github.com/leynos/rust-skill)
catalogue. The verification skills lean on the documentation and source
of [Hypothesis](https://github.com/HypothesisWorks/hypothesis),
[CrossHair](https://github.com/pschanely/CrossHair), and
[mutmut](https://github.com/boxed/mutmut); the quality-tool skill leans
on [`deadcode`](https://github.com/albertas/deadcode),
[`pyscn`](https://github.com/ludo-technologies/pyscn), and
[Pyinstrument](https://github.com/joerick/pyinstrument).

______________________________________________________________________

## Licence

ISC — see [LICENSE](LICENSE) for details.

______________________________________________________________________

## Contributing

Contributions are welcome. Keep new material under `skills/`, prefer short
first-class skills with references for longer detail, and update
[docs/skill-catalogue-status.md](docs/skill-catalogue-status.md) when adding
or retiring a skill.
