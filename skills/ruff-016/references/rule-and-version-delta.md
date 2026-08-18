# Rule delta: 0.14.x → 0.15.x → 0.16.0

What changed in the rule set across the three release series, for
checking whether a code exists, whether it is stable, and when it
appeared. Current state: <https://docs.astral.sh/ruff/rules/>.

Release dates: 0.14.0 on 2025-10-07, 0.15.0 on 2026-02-03, 0.16.0 on
2026-07-23. Most current models were trained before 0.15.0.

## Stabilized in 0.16.0

Twelve rules left preview:

| Code      | Name                                                  |
| --------- | ----------------------------------------------------- |
| `AIR303`  | `airflow3-incompatible-function-signature`            |
| `CPY001`  | `missing-copyright-notice`                            |
| `FURB164` | `unnecessary-from-float`                              |
| `FURB192` | `sorted-min-max`                                      |
| `ISC004`  | `implicit-string-concatenation-in-collection-literal` |
| `LOG004`  | `log-exception-outside-except-handler`                |
| `PLE0304` | `invalid-bool-return-type`                            |
| `PLR0917` | `too-many-positional-arguments`                       |
| `PLR1708` | `stop-iteration-return`                               |
| `RUF036`  | `none-not-at-end-of-union`                            |
| `RUF063`  | `access-annotations-from-class-dict`                  |
| `RUF068`  | `duplicate-entry-in-dunder-all`                       |

Behaviour stabilized alongside them:

- `BLE001` no longer fires when the exception is logged via a `logging`
  method other than `critical`, `error`, or `exception`.
- `FA102` checks more PEP 585-compatible APIs, including
  `collections.abc`.
- `INT001`/`INT002`/`INT003` recognize more `gettext` idioms, including
  assignment to `builtins._`.
- `S310` resolves local string-literal bindings, cutting false
  positives.
- `S508`/`S509` understand the newer PySNMP API.
- `UP019` recognizes `typing_extensions.Text`.

## Stabilized in 0.15.0

Sixteen rules left preview:

`ASYNC212`, `ASYNC240`, `ASYNC250`, `B912`, `FURB110`, `FURB171`,
`PLC0207`, `PLW0108`, `RUF037`, `RUF060`, `RUF061`, `RUF064`,
`RUF102`, `RUF103`, `RUF104`, `UP042`.

Behaviour: `A003` covers decorators and default arguments; `PYI016`
considers `typing.Optional`; `SIM905` fixes with `maxsplit` alone;
`SIM910` handles more key expressions; `UP008` has a safe fix when no
comments are lost; `UP043` applies to `.pyi` below Python 3.13.

## Preview rules added in 0.14.x-0.15.x

Rules predating 0.14.0, such as `PLC2701`, are out of scope here; see
the rule index under "Sources" for the complete list.

Enable lint preview rules with `preview = true` under
`[tool.ruff.lint]`, or `ruff check --preview` on the command line.
Formatter preview is a separate setting, so enabling one does not
enable the other. Expect these rules to stabilize in a later release.

| Code       | Name                                          | Added   |
| ---------- | --------------------------------------------- | ------- |
| `DOC102`   | `docstring-extraneous-parameter`              | 0.14.1  |
| `RUF066`   | `property-without-return`                     | 0.14.7  |
| `RUF067`   | `non-empty-init-module`                       | 0.14.11 |
| `RUF069`   | `float-equality-comparison`                   | 0.15.1  |
| `RUF070`   | `unnecessary-assign-before-yield`             | 0.15.3  |
| `D420`     | `incorrect-section-order`                     | 0.15.3  |
| `PLR1712`  | `swap-with-temporary-variable`                | 0.15.3  |
| `B043`     | `delattr-with-constant`                       | 0.15.6  |
| `TID254`   | `lazy-import-mismatch`                        | 0.15.6  |
| `RUF071`   | `os-path-commonprefix`                        | 0.15.6  |
| `RUF050`   | `unnecessary-if`                              | 0.15.8  |
| `RUF072`   | `useless-finally`                             | 0.15.8  |
| `RUF073`   | `f-string-percent-format`                     | 0.15.8  |
| `AIR201`   | `airflow-xcom-pull-in-template-string`        | 0.15.11 |
| `AIR004`   | `task-branch-as-short-circuit`                | 0.15.12 |
| `TID255`   | `lazy-import-immediately-resolved`            | 0.15.13 |
| `AIR202`   | `airflow-task-implicit-multiple-outputs`      | 0.15.14 |
| `PLW0717`  | `too-many-statements-in-try-clause`           | 0.15.14 |
| `RUF074`   | `incorrect-decorator-order`                   | 0.15.14 |
| `RUF075`   | `fallible-context-manager`                    | 0.15.14 |
| `ASYNC119` | `yield-in-context-manager-in-async-generator` | 0.15.16 |
| `D421`     | `property-docstring-starts-with-verb`         | 0.15.18 |
| `UP051`    | `deprecated-abc-decorator`                    | 0.15.21 |
| `RUF105`   | `noqa-comments`                               | 0.15.22 |
| `RUF106`   | `rule-codes-in-suppression-comments`          | 0.15.22 |
| `RUF201`   | `rule-codes-in-selectors`                     | 0.15.22 |

Also preview from the Airflow set: `AIR003`
(`airflow-variable-get-outside-task`, 0.15.6), `AIR304`
(`airflow3-dag-dynamic-value`, 0.15.6), and `AIR321`
(`airflow31-moved`, 0.15.1).

Removed: **`RUF076`** (`pytest-fixture-autouse`) was added in 0.15.17
and withdrawn in 0.15.20 as too opinionated for the `RUF` category. Do
not recommend it.

## Notable preview behaviour changes

Worth knowing because they change fixes, not just diagnostics:

- `UP006`, `UP007`, `UP045` insert `from __future__ import annotations`
  automatically when the fix needs it (0.15.6, 0.15.17).
- `E402` gained an autofix (0.15.22).
- `SIM102`'s `collapsible-if` fix became safe (0.15.10).
- `F811` reports annotated redeclarations (0.15.9) and duplicate
  imports inside `TYPE_CHECKING` blocks (0.15.15).
- `PYI033` extends to `.py` files (0.15.18).
- `PYI041` also checks string annotations (0.15.2).
- `S401`–`S415` allow suspicious imports inside `TYPE_CHECKING`
  (0.15.3).
- `PERF102` extends to comprehensions and generators (0.15.5).
- `RUF017` uses starred unpacking on Python 3.15+ (0.15.6).
- `RUF036` is limited to typing contexts and its fix is unsafe outside
  them (0.15.6).
- `C409`'s tuple-comprehension preview behaviour was dropped (0.15.21).

## Language and parser support

- Python 3.14 is the maximum stable target version from 0.14.0.
- With no explicit `target-version` and no inferable `requires-python`,
  Ruff defaults `target-version` to `py310`.
- `py315` is accepted as a target from 0.14.11 (preview).
- Lazy imports (Python 3.15) parse from 0.15.6 (preview), with isort
  preserving the `lazy` keyword and semantic-syntax errors reported for
  illegal placements.
- PEP 798 star-unpacking in comprehensions parses from 0.15.6 (preview).
- `frozendict` is recognized as a builtin on 3.15+ (0.15.8, preview).

## Sources

- Release notes: <https://astral.sh/blog/ruff-v0.16.0>
- Changelogs: `CHANGELOG.md`, `changelogs/0.15.x.md`,
  `changelogs/0.14.x.md` in `astral-sh/ruff`
- Rule index: <https://docs.astral.sh/ruff/rules/>
- Defaults: <https://docs.astral.sh/ruff/default-rules/>
