# Overloads and typed kwargs

Two patterns for shaping the public API in ways the type checker can verify.

## @overload

`typing.overload` describes a closed family of call shapes that share an
implementation but have distinct, precise return types.

```python
from typing import overload, Literal

@overload
def parse(s: str, *, raw: Literal[True]) -> bytes: ...
@overload
def parse(s: str, *, raw: Literal[False] = False) -> dict[str, object]: ...

def parse(s: str, *, raw: bool = False) -> bytes | dict[str, object]:
    return s.encode() if raw else json.loads(s)
```

The implementation `def` carries the union return; the overloads carry the
precise per-shape returns. Callers see the right type for their literal
keyword argument.

Use `@overload` when:

- one return type depends on a literal argument or argument presence;
- the call shapes are closed and named (a handful, not an open set);
- the body could be expressed as a union but the union loses information
  callers want.

Avoid `@overload` when:

- the union return is already precise enough for callers;
- the number of overloads grows beyond ~4 (split the function instead).

## TypedDict and Unpack

`TypedDict` plus `Unpack[...]` (PEP 692) lets a function declare typed
keyword arguments without writing every parameter in the signature.

```python
from typing import NotRequired, TypedDict, Unpack

class ConnectKwargs(TypedDict):
    host: str
    port: int
    timeout: NotRequired[float]
    tls: NotRequired[bool]

def connect(**kwargs: Unpack[ConnectKwargs]) -> Connection: ...

connect(host="db", port=5432, tls=True)              # ok
connect(host="db", port=5432, time=0.5)              # type-check error
```

Use this pattern when:

- a function forwards `**kwargs` to a helper and the helper's keys are
  fixed (factories, builders, middleware wrappers);
- the schema is genuinely keyword-only and callers do not benefit from
  inline parameters in IDE help.

Avoid it when:

- the keys are not actually fixed (use a `Mapping[str, object]` and
  validate at runtime);
- the function is the primary public surface (named parameters give
  better tooling support than `TypedDict` kwargs).

## TypedDict variants

```python
from typing import Required, NotRequired, TypedDict

class Payload(TypedDict, total=False):
    id: Required[str]
    tag: str
    note: NotRequired[str]
```

`total=False` makes every key optional unless marked `Required`. The
mirror, `total=True`, is the default. `Required` and `NotRequired`
let a single class mix both.

## Common mistakes

- An overload set that overlaps in a way the checker cannot disambiguate.
  Order overloads from most specific to most general.
- A `TypedDict` used as a runtime dict without validation; the
  type-checker guarantee does not survive a JSON round trip. Use
  `msgspec.Struct` or a validator at the boundary.
- An implementation `def` annotated with one of the overload signatures.
  Type checkers will flag the mismatch; the implementation must accept
  the union of all overloads.
