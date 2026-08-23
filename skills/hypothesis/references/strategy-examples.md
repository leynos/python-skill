# Strategy examples

Start with the smallest strategy that describes the domain. The examples move
from lightweight properties to structured and dependent data; later sections
are escalation tools, not a checklist for every test.

## Lightweight round trip

```python
from hypothesis import example, given, strategies as st


@example(value=0)
@given(value=st.integers(min_value=0, max_value=2**64 - 1))
def test_varint_roundtrips(value: int) -> None:
    assert decode_varint(encode_varint(value)) == value
```

This is the default shape: one built-in strategy, one invariant, and an
explicit boundary worth preserving. No custom strategy or settings override is
needed.

## Several independent fields

Keep independent fields independent. Hypothesis will explore their
combinations:

```python
@given(
    width=st.integers(min_value=1, max_value=4096),
    height=st.integers(min_value=1, max_value=4096),
)
def test_area_is_symmetric(width: int, height: int) -> None:
    assert area(width, height) == area(height, width)
```

Do not build a tuple or composite strategy merely to make the decorator
shorter.

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


@given(order=orders)
def test_order_roundtrips(order: Order) -> None:
    assert decode_order(encode_order(order)) == order
```

`st.builds` constructs the value directly. `st.from_type(Order)` can infer a
default strategy from type annotations when the inferred domain is suitable.

## Dependent values justify `@st.composite`

Use a composite strategy when one generated field genuinely constrains
another:

```python
@st.composite
def intervals(draw) -> tuple[int, int]:
    start = draw(st.integers(min_value=-1_000_000, max_value=1_000_000))
    length = draw(st.integers(min_value=0, max_value=10_000))
    return start, start + length


@given(interval=intervals())
def test_interval_normalization_is_idempotent(
    interval: tuple[int, int],
) -> None:
    assert normalize_interval(normalize_interval(interval)) == (
        normalize_interval(interval)
    )
```

The dependency is the reason for the abstraction. If fields are independent,
keep them as separate `@given` arguments or use `st.builds`.

## The filtering trap, before and after

```python
# Rejection sampling: shrinks badly and can exhaust the budget.
@given(n=st.integers().filter(lambda n: n % 2 == 0))
def test_even_property_old(n: int) -> None:
    assert (n * n) % 4 == 0


# Construct only valid values.
@given(half=st.integers())
def test_even_property(half: int) -> None:
    n = half * 2
    assert (n * n) % 4 == 0
```

```python
# Two draws plus assume: shrinking loses information.
@given(a=st.integers(), b=st.integers())
def test_order_old(a: int, b: int) -> None:
    assume(a < b)
    assert relation(a, b)


# Draw one bound, then generate the dependent value inside it.
@st.composite
def bounded_order(draw) -> tuple[int, int]:
    b = draw(st.integers(min_value=1))
    a = draw(st.integers(min_value=0, max_value=b - 1))
    return a, b


@given(pair=bounded_order())
def test_order(pair: tuple[int, int]) -> None:
    a, b = pair
    assert relation(a, b)
```

The old assertion should test real behaviour rather than `assert a < b`; the
latter merely repeats the assumption. The example keeps `relation(...)`
abstract to emphasize that distinction.

## Oracle comparison

```python
@given(values=st.lists(st.integers(), max_size=128))
def test_sort_matches_python(values: list[int]) -> None:
    assert custom_sort(values) == sorted(values)
```

A structurally different oracle catches semantic disagreement. Here the
built-in sort has a different implementation and a much broader test history
than `custom_sort`.

## Registered strategies

For a domain type used across many tests, register a default strategy:

```python
st.register_type_strategy(UserId, st.integers(min_value=1).map(UserId))


@given(user_id=st.from_type(UserId))
def test_user_id_roundtrips(user_id: UserId) -> None:
    assert UserId.parse(str(user_id)) == user_id
```

Registration is worthwhile when several tests share the same domain rule. A
single test does not need a strategy registry.

## Targeted property generation

`hypothesis.target(value)` maximizes finite numeric observations. It has no
separate minimization mode; for a minimum search, negate the score with
`target(-score)`. Use it for a specific search objective such as longest
output, deepest tree, or greatest memory estimate. Do not add targets to an
ordinary invariant without evidence that useful cases are otherwise rare.

## Common mistakes

- Writing `@st.composite` before trying built-in strategies, `st.builds`, or
  `st.from_type`.
- Rejecting most draws with `.filter` or `assume` instead of constructing valid
  data.
- Hiding the property beneath a reusable strategy framework that has only one
  caller.
- Using an oracle that calls or copies the function under test.
- Adding a state machine when a normal `@given` test can generate the relevant
  sequence as a list.
- Applying `@given` to an `async def` test without an async-compatible runner.
  Use the project's pytest async plugin and keep fixture lifetime in mind.
