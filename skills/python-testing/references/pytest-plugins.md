# pytest plugin sketch

The plugin ecosystem is large; this is the short list of plugins that
earn their keep in most production codebases.

## Parallel execution

`pytest-xdist`:

```console
uv run pytest -n auto
```

`-n auto` matches the CPU count. Requires test independence; a flake
that depends on order is exposed quickly. Pair with `pytest-randomly`
when adopting xdist.

## Async tests

`pytest-asyncio`:

```python
@pytest.mark.asyncio
async def test_pings():
    async with build_client() as client:
        assert await client.ping()
```

Configure the default loop scope and mode in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"           # decorate-less marking, opt-out per file
```

`asyncio_mode = "auto"` removes the per-test `@pytest.mark.asyncio`
decoration; pair with `loop_scope = "function"` to keep each test
isolated.

## Coverage

`pytest-cov`:

```console
uv run pytest --cov=src --cov-branch --cov-report=term-missing
```

Branch coverage is the cheapest signal that conditionals are
exercised; line coverage alone hides whole `if` arms.

## Benchmarking

`pytest-benchmark`:

```python
def test_serialise(benchmark):
    benchmark(msgspec.json.encode, payload)
```

Reports min/max/mean/stddev. Useful for spotting regressions in
small, focused benchmarks; for system-level profiling load
`python-quality-tools` and use Pyinstrument.

## Snapshot testing

`syrupy`:

```python
def test_renders(snapshot):
    assert render(payload) == snapshot
```

Snapshots live next to the test; `--snapshot-update` rewrites them.
Review the diff like any other code change.

## Order randomization

`pytest-randomly`:

```toml
[tool.pytest.ini_options]
addopts = "-p pytest_randomly"
```

Randomizes test order and seeds RNG. Use the seed reported on
failure (`pytest --randomly-seed=12345`) to reproduce.

## Profile a slow test

`pytest-pyinstrument`:

```console
uv run pytest --pyinstrument tests/test_hot.py
```

Drops a flamegraph into `prof/` for review. Deep dive lives in
`../python-quality-tools/references/pyinstrument.md`.

## Boundary plugins

- `pytest-httpx` — record and replay HTTPX traffic.
- `pytest-postgresql` / `pytest-redis` — ephemeral processes.
- `pytest-mock` — `mocker.patch(...)` fixture wrapping `unittest.mock`.
- `pytest-freezegun` / `freezer` — control `datetime.now()` without
  monkeypatching every call site.

## Plugin discipline

- Adopt a plugin only when its functionality recurs across many
  tests; one-off helpers belong as plain fixtures.
- Pin plugin versions; pytest plugins change interfaces and a minor
  bump can change behaviour.
- Document the plugins in use in `pyproject.toml` and (briefly) in
  the repo's testing guide.
