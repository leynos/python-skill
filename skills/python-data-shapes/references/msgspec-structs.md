# msgspec.Struct

`msgspec.Struct` is a fast, slotted, schema-validating data type that
encodes and decodes JSON, MessagePack, YAML, and TOML. The decode path
checks types and constraints; the encode path is a direct C-level
serializer.

## Anatomy

```python
import msgspec
from typing import Annotated

class Order(
    msgspec.Struct,
    kw_only=True,
    frozen=True,
    forbid_unknown_fields=True,
    omit_defaults=True,
    rename="camel",
):
    order_id: str
    pence: Annotated[int, msgspec.Meta(ge=0)]
    customer_email: str
    note: str | None = None
```

What each knob does:

- `kw_only=True`: every field is keyword-only at the constructor; safer
  for evolution.
- `frozen=True`: immutable instances; hashable; safe across threads.
- `forbid_unknown_fields=True`: decode rejects unknown keys instead of
  silently dropping them — the safer default for public APIs.
- `omit_defaults=True`: encode skips fields equal to their default,
  reducing payload size.
- `rename="camel"`: encode `customer_email` as `customerEmail` and
  accept either form on decode.
- `Annotated[..., msgspec.Meta(ge=0)]`: per-field validation
  (`ge`, `le`, `gt`, `lt`, `multiple_of`, `min_length`, `max_length`,
  `pattern`, `tz` for datetimes).

## Encoding and decoding

```python
raw = msgspec.json.encode(order)
parsed = msgspec.json.decode(raw, type=Order)
```

`msgspec.json.Decoder(type=Order)` is the right shape inside a hot loop;
constructing the decoder once amortizes the per-decode setup.

## Array-shaped structs

```python
class Point(msgspec.Struct, array_like=True):
    x: float
    y: float
```

`array_like=True` encodes the struct as `[x, y]` rather than
`{"x": ..., "y": ...}`. Use it for fixed-shape numeric data where the
payload size matters and field names are stable.

## Defaults and `field`

Mutable defaults need `msgspec.field(default_factory=list)` for the
same reasons dataclasses do.

```python
class Cart(msgspec.Struct, kw_only=True):
    items: list[str] = msgspec.field(default_factory=list)
```

## `gc=False`

Setting `gc=False` opts out of cyclic-garbage tracking for the
instance. Use when the struct holds no references that could form a
cycle (primitives, other `gc=False` structs, frozen collections).
The decode budget shrinks noticeably; the bug surface (forgotten
cycle) is real.

## Validation discipline

Validate at the boundary. Once a `msgspec.Struct` has been constructed
or decoded, treat its fields as already valid. Re-validation deeper in
the call stack hides which layer is responsible for the invariant.

## Interop with `msgspec.to_builtins` / `msgspec.convert`

`msgspec.to_builtins(struct)` returns a `dict`/`list` payload; useful
for handing data to a library that does not understand `Struct`.
`msgspec.convert(value, type=Order)` validates and converts a Python
dict into a `Struct` — the right tool when a foreign library hands
you a `dict` already.

## Common mistakes

- Constructing a `Struct` by passing a wide `**dict` of untrusted
  keys without `forbid_unknown_fields`. Drift goes silent.
- Treating the constructor's validation as enough on its own; the
  decoder also validates, and the two paths can diverge if a custom
  `__post_init__`-style setup happens elsewhere.
- Subclassing a struct to add fields without setting `kw_only=True` on
  both. Positional ordering then conflicts on construction.
- Reaching for `pydantic` because `msgspec` "looks too thin". For
  domain data with a known schema, `msgspec` is usually the right
  weight; for a forms framework with computed fields and many
  validators, `pydantic` is fine.
