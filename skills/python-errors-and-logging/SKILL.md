---
name: python-errors-and-logging
description: Use for Python exception design, raising, catching, and logging. Covers narrow `except`, `raise … from …`, domain hierarchies with `Error` suffixes, parameterised logging, `logger.exception`, and the Ruff TRY/BLE/EM/LOG/N818/PERF203 rules.
globs: ["**/*.py"]
---

# Python Errors and Logging

Use this when the question is "what should this code raise, catch, or log?"
The Ruff rule families (Tryceratops `TRY`, blind-except `BLE`, errmsg `EM`,
logging `LOG`, naming `N818`, perflint `PERF203`, bug-bear `B017`) encode
the same decision surface; enforce them in `pyproject.toml`.

## Working stance

- Exceptions are part of the public API; design a small hierarchy with a
  package base class and `*Error` suffix (`N818`).
- Raise specific built-ins (`ValueError`, `TypeError`,
  `NotImplementedError`) or domain errors; never `Exception` directly
  (`TRY003`, `TRY004`).
- When wrapping a vendor exception, use `raise DomainError(...) from exc`
  (`TRY201`); when re-raising the same type, plain `raise` keeps the
  traceback (`TRY200`).
- Catch only what can be handled. `except Exception:` and bare `except:`
  are `BLE001`.
- Use `else:` for the happy path inside `try` blocks (`TRY300`).
- Build exception messages once, then pass them in (`EM101`/`EM102`):
  `msg = f"…"; raise X(msg)`.
- Log once, at a boundary, via a module logger
  (`logger = logging.getLogger(__name__)`).

## Decision surface

- **Raise vs return**: raise when the caller cannot continue without
  policy input; return an `Optional`/`Result`-shaped value for expected
  alternatives (missing cache key, empty page).
- **Built-in vs domain error**: a built-in suffices when the caller's
  recovery is "fix the input" (`ValueError`, `TypeError`); a domain error
  is needed when callers must distinguish payment-declined from
  payment-timeout.
- **Wrap vs propagate**: wrap at a layer boundary so callers do not
  import vendor exceptions; propagate inside a layer where the type is
  already domain-shaped.
- **Log vs raise**: log at the outermost boundary that has context
  (request handler, worker entry, CLI `main`); do not log-and-reraise on
  every layer.
- **Logger call shape**: `logger.warning("Failed for user_id=%s", uid)` —
  lazy interpolation, module logger, no f-string (`LOG004`/`LOG014`), no
  `%`-formatting in the format string (`LOG007`), no
  `logging.warn` (`LOG009`), no root-logger calls (`LOG015`).
- **Hot loops**: hoist `try`/`except` outside the loop body when the
  exception is rare (`PERF203`); when it must stay inside, treat it as a
  micro-optimisation guided by profiling.

## Red flags

- `raise Exception(...)` or `raise RuntimeError(...)` where a built-in
  or domain error fits better,
- `except Exception:` (or bare `except:`) with no comment explaining why
  every exception is recoverable,
- `raise NewError(str(exc))` discarding the cause (use `from exc`),
- `logger.exception("…: %s", exc)` duplicating the traceback,
- `logging.warning(f"…")` or `logging.warning("… %s" % x)`,
- `pytest.raises(Exception)` without a `match=` regex (`B017`),
- a `try`/`except` wrapping every iteration in a hot loop,
- log-and-reraise chains that emit the same failure at three layers.

Read [ruff-rule-map.md](references/ruff-rule-map.md) and
[logging-recipes.md](references/logging-recipes.md) for the rule-by-rule
mapping and the boundary-logging recipes.
