# Fixtures and parametrize

The two pillars of pytest. Used well they keep tests short and the
failure messages precise; used badly they hide the setup that the
failure depends on.

## Fixture scopes

```python
import pytest

@pytest.fixture
def small_db() -> Iterator[DB]:
    db = DB(":memory:")
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def schema(small_db) -> DB:
    apply_schema(small_db)
    return small_db
```

- `function` (default) — fresh per test.
- `class` — shared across tests in a class.
- `module` — shared across tests in a module.
- `package` — shared across a directory.
- `session` — shared across the whole run.

A wider scope means faster runs but more cross-test coupling. Move the
scope wider only when the fixture is read-only inside the broader
group.

## Parametrize a test

```python
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("0", 0),
        ("42", 42),
        ("-7", -7),
    ],
    ids=["zero", "positive", "negative"],
)
def test_parses_int(value: str, expected: int) -> None:
    assert parse_int(value) == expected
```

The `ids=` argument is worth the keystrokes: failures report
`test_parses_int[negative]` instead of `test_parses_int[ -7--7]`.

## Parametrize a fixture

```python
@pytest.fixture(params=["sqlite", "postgres"])
def db(request) -> Iterator[DB]:
    if request.param == "sqlite":
        yield SQLite()
    else:
        yield Postgres()

def test_inserts(db: DB) -> None:
    db.insert({"id": 1})
    assert db.count() == 1
```

Every test that uses `db` now runs twice — once per backend. Used
deliberately, this is the cheapest way to verify a contract across
implementations.

## Indirect parametrization

```python
@pytest.fixture
def user(request) -> User:
    return make_user(role=request.param)

@pytest.mark.parametrize("user", ["admin", "guest"], indirect=True)
def test_can_view(user: User) -> None:
    assert can_view_dashboard(user)
```

`indirect=True` feeds the parameter into the fixture rather than into
the test directly. Use it when the value identifies the system under
test rather than the input.

## Fixture composition

Fixtures can depend on other fixtures:

```python
@pytest.fixture
def client(db: DB) -> Iterator[Client]:
    app = build_app(db)
    with TestClient(app) as c:
        yield c
```

The dependency graph is resolved automatically; cycles raise an
error.

## Marker hygiene

```python
import pytest

@pytest.mark.slow
def test_full_replay(): ...

@pytest.mark.requires_postgres
def test_uses_pg(): ...
```

Register markers in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
  "slow: long-running tests",
  "requires_postgres: needs a running postgres",
]
```

Unregistered markers warn or fail depending on configuration.

## Common mistakes

- A fixture that yields a mock pretending to be a collaborator. The
  test passes against the mock and fails against reality. Either use
  the real collaborator or test the contract elsewhere.
- A `module`-scope fixture that mutates state. The next test in the
  module sees the mutation; flakes follow.
- Parametrizing over inputs that share a fixture's setup, in
  which case the fixture should be parametrized, not the test.
- Asserting on the fixture inside the fixture body. Fixtures
  prepare; tests assert.
