# Strategy examples

Patterns for the strategies that recur in real test suites, with the
filtering-trap fix and the derive shortcut.

## Round-trip with composed values

```python
from hypothesis import given, strategies as st

@st.composite
def valid_dates(draw) -> tuple[int, int, int]:
    y = draw(st.integers(min_value=0, max_value=9999))
    m = draw(st.integers(min_value=1, max_value=12))
    d = draw(st.integers(min_value=1, max_value=28))
    return y, m, d

@given(date=valid_dates())
def test_parse_roundtrips(date: tuple[int, int, int]) -> None:
    y, m, d = date
    s = f"{y:04}-{m:02}-{d:02}"
    assert parse_date(s) == (y, m, d)
```

`@st.composite` lets `draw` pull from inner strategies; the resulting
strategy is reusable across multiple tests.

## Building structured values

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Order:
    pence: int
    customer_id: str

orders = st.builds(
    Order,
    pence=st.integers(min_value=0, max_value=1_000_000),
    customer_id=st.text(min_size=1, max_size=32),
)
```

`st.builds` constructs the value directly. For complex types,
`st.from_type(Order)` infers a default strategy from the type
annotations.

## The filtering trap, before and after

```python
# ❌ Rejection sampling: shrinks badly, can exhaust the budget.
@given(n=st.integers().filter(lambda n: n % 2 == 0))
def test_even_prop_old(n: int) -> None:
    assert (n * n) % 4 == 0

# ✅ Construct only valid values.
@given(half=st.integers())
def test_even_prop(half: int) -> None:
    n = half * 2
    assert (n * n) % 4 == 0
```

```python
# ❌ Two draws plus assume — shrinks lose information.
@given(a=st.integers(), b=st.integers())
def test_order_old(a: int, b: int) -> None:
    assume(a < b)
    assert a < b

# ✅ Draw one bound, then the other from inside it.
@given(b=st.integers(min_value=1), a_from=st.integers(min_value=0))
def test_order(b: int, a_from: int) -> None:
    a = a_from % b
    assert a < b
```

## Oracle comparison

```python
@given(xs=st.lists(st.integers(), max_size=128))
def test_sort_matches_python(xs: list[int]) -> None:
    assert custom_sort(xs) == sorted(xs)
```

A structurally different oracle (`sorted` is implemented in C and
optimised differently from `custom_sort`) catches semantic
disagreement.

## `from_type` and registered strategies

For widely used types, register a default strategy:

```python
st.register_type_strategy(UserId, st.integers(min_value=1).map(UserId))

@given(uid=st.from_type(UserId))
def test_user(uid: UserId) -> None:
    ...
```

Now every test that needs a `UserId` can ask `st.from_type`; the
generation rule lives in one place.

## Targeted property generation

`hypothesis.target(value)` tells the runner to bias the search toward
inputs that maximise `value`. Useful for "find the input that maximises
memory" or "find the input that produces the longest output".

## Common mistakes

- A strategy that draws a value and then rejects most of them via
  `.filter`. Re-shape the strategy so every draw is valid.
- An oracle that calls the function under test. The test then proves
  only that the developer can copy code.
- A `@given` decoration above an `async def` test without an asyncio
  bridge. Use `pytest-asyncio` and a thin sync wrapper, or
  Hypothesis's async helpers.
