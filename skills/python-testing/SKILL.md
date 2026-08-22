---
name: python-testing
description: Use for advanced pytest usage: fixture scopes, named examples, finite parametrization, marks, plugins, snapshot and approval tests, async tests, and the boundary between example, property, and verification testing.
globs: ["**/tests/**/*.py", "**/test_*.py", "**/conftest.py"]
---

# Python Testing (pytest)

Use this when the question is how to structure an example-based test suite,
design fixtures, express a finite case table, or pick the right plugin. Load
`hypothesis` directly for an obvious lightweight invariant. Load
`python-verification` when the choice between generated, symbolic, and mutation
testing is itself the problem.

## Working stance

- Tests describe behaviour, not implementation. A passing test should survive
  a refactor that does not change behaviour.
- One assertion subject per test.
- `pytest.mark.parametrize` expresses a finite set of semantically meaningful
  cases without duplicating the test body.
- Hypothesis expresses one relation over a broad input space without
  pretending a handful of representative rows is coverage.
- Fixtures own setup and teardown; tests stay declarative about what they
  exercise.
- Asserting on log records, exception types, and structured payloads beats
  asserting on rendered strings.
- Cover the happy path, the boundaries, and one named bug per regression.
  Coverage percentage is a hygiene metric, not a goal.

## Parametrize or property

Choose `pytest.mark.parametrize` when each row belongs in the specification:
a protocol example, truth table, supported version, error mapping, or exact
input/output pair. Give rows readable `ids=` and expect reviewers to reason
about each one.

Choose a lightweight Hypothesis property when every row exercises the same
invariant and the values merely sample a larger domain. Common signals are a
table labelled "edge cases", manual cross-products of independent dimensions,
and a new row for every escaped bug. Keep exact normative examples and named
regressions alongside the property.

A property test is not automatically superior. For a four-row standard, a
slow integration boundary, or distinct expected messages and side effects,
parametrization is clearer and cheaper.

## Decision surface

- **Function-scope fixture**: state is small, cheap to create, and not shared
  across tests. The default.
- **Module-scope fixture**: setup is expensive, such as a database schema or
  parser warmup, and tests in the module read but do not mutate the state.
- **Session-scope fixture**: process-wide, immutable, expensive resources such
  as a test database or hot import.
- **`autouse=True`**: required setup that should not be opted into case by case,
  such as timezone freezing or a deterministic RNG. Use sparingly.
- **`pytest.mark.parametrize`**: one assertion subject across a finite list of
  meaningful inputs and expected outputs. `ids=` improves the report. If the
  list is representative rather than normative, route to `hypothesis`.
- **`pytest.mark.parametrize(indirect=True)`**: a parameter feeds a fixture
  rather than the test directly; use it to vary the system under test, not the
  inputs.
- **`pytest.fixture(params=...)`**: every test using the fixture runs once per
  parameter. Pick it when the fixture's identity varies, not when test inputs
  vary.
- **`monkeypatch`**: replace an attribute or environment variable for one test;
  pytest restores it at teardown.
- **`tmp_path` / `tmp_path_factory`**: per-test or per-session temporary
  directories.
- **`caplog`**: capture log records; assert on `record.levelno`,
  `record.message`, and `record.args`.
- **`pytest.raises(..., match=...)`**: pin the type and a regex for the message;
  `pytest.raises(Exception)` without `match=` is a `B017` smell.

## Plugins worth knowing

- `pytest-xdist`: parallelize across cores; requires test independence.
- `pytest-asyncio`: `@pytest.mark.asyncio` and an `event_loop` fixture.
- `pytest-cov`: coverage with branch reporting; aim for branch coverage on
  critical paths.
- `pytest-benchmark`: micro-benchmark fixture with statistics; pair with
  `python-quality-tools` for system-level profiling.
- `syrupy` or `pytest-insta`: snapshot or approval testing for rendered
  output such as HTML, JSON, and golden files.
- `pytest-randomly`: randomize test order; surfaces hidden dependencies.
- `pytest-pyinstrument`: drop-in profiler; see `python-quality-tools`.

## Async testing

```python
import pytest


@pytest.mark.asyncio
async def test_handler_responds() -> None:
    client = await build_client()
    async with client:
        response = await client.get("/healthz")
        assert response.status == 200
```

Each test gets its own event loop by default. Use `pytest-asyncio`'s
`loop_scope` to share a loop across a module when a fixture needs to outlive a
test.

## Red flags

- A fixture that constructs the system under test and asserts on it. Move the
  assertion into the test.
- A `for` loop in a test body that should be parametrization.
- A parameter table that keeps growing to sample one invariant. Replace the
  sampling job with a lightweight Hypothesis property and retain named
  regressions.
- `time.sleep` in a test to "let async work finish". Use a fixture that awaits
  the work directly.
- `caplog` plus `assert "foo" in caplog.text`. Assert on records, not rendered
  text.
- A test that mocks an entire collaborator to avoid setting up its state.
  Either the seam is wrong or the collaborator is too heavy.
- `@pytest.fixture(autouse=True)` introduced to fix one test.
- Snapshot tests with no review step on regenerate; the snapshot is the spec.

Read [fixtures-and-parametrize.md](references/fixtures-and-parametrize.md)
and [pytest-plugins.md](references/pytest-plugins.md) for the patterns that
recur across suites.
