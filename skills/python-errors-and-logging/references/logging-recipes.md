# Logging recipes

Patterns for the everyday questions: which logger, which level, where to
catch, and how to keep payloads useful without leaking secrets.

## Module logger, never the root

```python
import logging

logger = logging.getLogger(__name__)
```

`logger = logging.getLogger(__name__)` lets operators tune levels per
package and gives every record a `name` field that downstream
aggregators can index. `logging.warning(...)` (no logger) targets the
root logger and is `LOG015`.

## Lazy interpolation

```python
logger.info("Dispatched order_id=%s to shop_id=%s", order_id, shop_id)
logger.error("Task %s crashed after %d retries", task_id, attempts)
```

The format string is evaluated only when the level is enabled. f-strings
and `%`-formatting in the message string defeat that.

## Logging the active exception

```python
try:
    risky()
except ValueError:
    logger.exception("Risky operation failed")    # includes traceback
    raise
```

`logger.exception(...)` is a shortcut for `logger.error(..., exc_info=True)`
and only makes sense inside an `except` block. Do not append the exception
to the format arguments — the traceback already carries it (`TRY401`).

## Boundary logging

```python
def worker_main() -> None:
    while True:
        job = queue.get()
        try:
            handle(job)
        except PaymentsError:
            logger.exception("Job failed due to payments error")
            # do not re-raise; the worker keeps the loop going
        except Exception:                          # noqa: BLE001 — last-resort
            logger.exception("Unhandled exception; job dropped")
```

Log once, at the outermost layer that has context (request handler, worker
loop, CLI `main`). Inner layers either resolve the problem or propagate
it; double-logging is a frequent operational headache.

## Structured payloads

```python
logger.info(
    "Charge accepted",
    extra={"order_id": order_id, "amount_pennies": amount},
)
```

The `extra` mapping is merged into the log record. With a JSON formatter
this gives operators searchable fields without parsing message strings.
Do not put secrets in the message or in `extra`; tag the logger or use a
filter to redact them.

## Custom levels

Avoid them. The five built-in levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`,
`CRITICAL`) cover every operational need and stay legible across the
ecosystem.

## Tests

In pytest, `caplog` captures records by level and message:

```python
def test_warns_once(caplog):
    with caplog.at_level(logging.WARNING):
        run()
    assert [r.message for r in caplog.records] == ["expected once"]
```

Assert on `record.message` and `record.args` rather than the rendered
output; the renderer changes with handler configuration but the record
is stable.

## What to log, what not to log

- Log at boundaries: request in, request out, job started, job ended,
  external call started/ended (with duration and outcome).
- Do not log every branch; the logger is not a debugger.
- Do not log payloads that contain PII or secrets; redact at the
  formatter or use structured `extra` and a redaction filter.
- Do not log the same failure at three layers; pick the boundary and
  raise quietly elsewhere.
