# Ruff rule map for errors and logging

The decision surface in `SKILL.md` maps directly onto Ruff rules. Enable the
families in `pyproject.toml`:

```toml
[tool.ruff.lint]
select = [
  "TRY",      # Tryceratops: exception design
  "BLE",      # blind-except
  "EM",       # flake8-errmsg
  "LOG",      # flake8-logging
  "N818",     # exception names end with Error
  "PERF203",  # try/except in loop
  "B017",     # assert-raises-exception
]
```

## Rule-by-rule reminders

- **TRY003** — avoid long messages in `raise X(...)` constructors; build
  the message and pass it.
- **TRY004** — raise `TypeError` for wrong types, `ValueError` for bad
  values; reach for domain errors otherwise.
- **TRY200** — re-raising the same exception type does not need
  `from None` or `from exc`; bare `raise` keeps the traceback.
- **TRY201** — when transforming a vendor exception into a domain
  exception, use `raise DomainError(...) from exc`.
- **TRY300** — separate the happy-path tail with `else:` rather than
  letting it sit inside the `try`.
- **TRY401** — `logger.exception("Failed: %s", exc)` doubles the
  exception in the output; drop the `%s` and the argument.
- **BLE001** — `except Exception:` and bare `except:` only when the
  comment names a sound reason (top-level worker boundary that must not
  crash the process).
- **EM101 / EM102** — `raise X(f"…")` and `raise X("plain text")` get
  flagged; build the message first, then pass it.
- **LOG004 / LOG014** — f-strings inside logging calls evaluate
  regardless of level. Use `logger.warning("… %s", x)`.
- **LOG007** — `%`-formatting in the message string defeats lazy
  interpolation in the same way.
- **LOG009** — `logger.warn` is deprecated; use `logger.warning`.
- **LOG015** — calls on `logging` itself rather than a named logger
  prevent per-module configuration.
- **N818** — concrete exception classes end with `Error`
  (`CardDeclinedError`, not `CardDeclined`); base classes can omit the
  suffix if they are abstract (`PaymentsError` is also fine because it
  refers to a domain group, not a specific failure).
- **PERF203** — `try`/`except` inside a hot loop is slower than hoisting
  the block; only keep the inner form when each iteration genuinely
  needs to recover and the rate is low.
- **B017** — `pytest.raises(Exception)` matches anything; always pin
  the type and, when useful, the `match=` regex.

## What Ruff does not catch

- Wrapping a vendor exception without `from`: `raise Wrapped(str(exc))`
  passes the rule check but discards lineage. Review for this manually.
- Mis-tiered logging: emitting an `error`-level log for an expected
  outcome (e.g. validation rejection) is not a Ruff concern.
- The "log once at the boundary" rule. Multiple `logger.exception` calls
  along a chain are valid Python; the cost is operator confusion.
