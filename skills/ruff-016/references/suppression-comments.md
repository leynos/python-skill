# Suppression comments in Ruff 0.16

Ruff now has a native suppression syntax alongside `noqa`. All four
forms below are stable in 0.16.0. `noqa` and `# flake8: noqa` continue
to work; nothing is deprecated.

## The four forms

### `ruff: ignore[...]` — line level

```python
import math  # ruff: ignore[F401]
```

Placed on its own line *above* a statement, it covers the whole
**logical** line — the entire multi-line signature, call, or literal:

```python
# ruff: ignore[ARG001]  covers the entire function signature
def foo(
    arg1,
    arg2,
): ...
```

Placed *inside* a multi-line construct or at the end of a physical
line, it covers only that physical line:

```python
def foo(
    arg1,
    # ruff: ignore[ARG001]  only covers `arg2`
    arg2,
): ...
```

Comments stack; intervening comments do not break the association:

```python
# ruff: ignore[E741]
# ruff: ignore[F841]
# Intentional local name.
i = 1
```

This is the capability `noqa` lacks: `noqa` binds to a physical line
only, so suppressing a diagnostic reported against a multi-line
statement means guessing which line Ruff anchors it to.

### `ruff: file-ignore[...]` — whole file

```python
# ruff: file-ignore[F401, ARG001] Re-exports are intentional
```

Own-line, at module scope, preferably near the top. Trailing prose
after the closing bracket is the reason and is ignored by the parser.

### `ruff: disable[...]` / `ruff: enable[...]` — block range

```python
def foo():
    # ruff: disable[E741, F841]
    i = 1
    # ruff: enable[E741, F841]
```

Rules:

- codes must match, in the same order, on both comments;
- indentation must match within the logical block;
- no blanket form — at least one code is required;
- an `enable` cannot turn on a rule the configuration did not select;
- a `disable` with no matching `enable` becomes an *implicit* range
  running until a scope indented less than the comment, and raises
  **`RUF104`** (`unmatched-suppression-comment`). Prefer explicit
  ranges; at module scope an implicit range can silently swallow the
  rest of the file.

Block suppressions were introduced in 0.15.0.

### `noqa` — unchanged

`# noqa`, `# noqa: F401`, `# ruff: noqa`, `# ruff: noqa: F841`, and
`# flake8: noqa` behave as before. For multi-line strings the `noqa`
goes after the closing quotes; for an import block it goes on the first
line.

## Syntax notes

- The canonical spelling has a space after the colon —
  `# ruff: ignore[F401]`. 0.16.0 makes Ruff insert one when it writes
  these comments; the parser accepts `#ruff:ignore[...]` too.
- The `#ruff:` prefix is **case sensitive**; `noqa` matching is not.
- Codes are separated by commas, optional whitespace, optional trailing
  comma.
- **Rule names** (`unused-import` instead of `F401`) are accepted in
  `ruff: ignore`, `ruff: file-ignore`, `ruff: disable`, and
  `ruff: enable` **in preview mode only**, and in rule selectors in
  preview. On stable, use codes.

## Inserting and cleaning up

```console
ruff check path/ --add-noqa          # insert `# noqa: CODE`
ruff check path/ --add-ignore        # insert `# ruff: ignore[CODE]`
ruff check path/ --extend-select RUF100 --fix   # remove dead ones
```

- `--add-ignore` is new in 0.16.0 (preview in 0.15.21). With
  `preview = true` it writes human-readable names.
- `--add-noqa` gained a reason option in 0.14.5.
- Bulk insertion is a migration tool. Pair it with an issue and a
  deadline, or it becomes the permanent state of the codebase.

## The suppression-hygiene rules

These fire on suppression comments themselves and are worth selecting
on any project that uses them heavily:

| Code     | Name                                 | Status in 0.16     |
| -------- | ------------------------------------ | ------------------ |
| `RUF100` | `unused-noqa`                        | stable, default-on |
| `RUF101` | `redirected-noqa`                    | stable, default-on |
| `RUF102` | `invalid-rule-code`                  | stable (0.15.0)    |
| `RUF103` | `invalid-suppression-comment`        | stable (0.15.0)    |
| `RUF104` | `unmatched-suppression-comment`      | stable (0.15.0)    |
| `RUF105` | `noqa-comments`                      | preview            |
| `RUF106` | `rule-codes-in-suppression-comments` | preview            |
| `RUF201` | `rule-codes-in-selectors`            | preview            |

Since 0.15.3, `RUF100` ignores unknown rule codes and `RUF102` reports
them instead. `RUF105` rewrites `noqa` to `ruff: ignore`; `RUF106` and
`RUF201` push codes towards human-readable names, in comments and in
configuration selectors respectively.

## isort action comments

`# isort: skip_file`, `# isort: on`, `# isort: off`, `# isort: skip`,
and `# isort: split` are respected, as are `# ruff: isort: …` variants.
Not respected inside docstrings.
