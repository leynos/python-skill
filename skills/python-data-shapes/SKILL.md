---
name: python-data-shapes
description: Use for choosing a Python data container — `msgspec.Struct`, `dataclasses.dataclass`, `attrs`, `TypedDict`, `NamedTuple`, frozen vs mutable, tagged unions, and the boundary between wire format and domain object.
globs: ["**/*.py"]
---

# Python Data Shapes

Use this when the question is which container should carry a piece of
domain data and how it should cross wire boundaries.

## Working stance

- Pick the lightest container that carries the invariants you need.
- Domain objects belong in immutable, slotted containers; wire payloads
  belong in validated schema types; dictionaries belong only at
  serialization boundaries.
- Treat construction as the only place where invariants are checked;
  trust the type elsewhere.
- For JSON/MessagePack/YAML/TOML, parse to a schema type at the
  boundary and never let the raw `dict` leak inward.

## Decision surface

- **`msgspec.Struct`**: high-throughput serialization (HTTP APIs, RPC,
  queues). Slots by default, validation on decode, tagged unions via
  `tag`/`tag_field`, `kw_only=True`, `frozen=True`, `array_like=True`,
  `rename="camel"`, `forbid_unknown_fields=True`. Use when the type
  crosses a boundary and the decode budget matters.
- **`dataclasses.dataclass`**: stdlib, no decode path. Combine
  `slots=True`, `frozen=True`, `kw_only=True` for safe domain objects.
  Use for in-process domain shapes that do not need a serde codec.
- **`attrs.define` / `attrs.frozen`**: same niche as dataclasses, with
  richer validators and converters and `__attrs_post_init__`. Reach
  for it when validators and converters multiply.
- **`NamedTuple`**: positional tuple with field names. Use when the
  data really is a small positional record (coordinates, version
  triples) and tuple semantics (immutability, hashing, unpacking) are
  desired.
- **`TypedDict`**: a typed view over an existing `dict` payload (kwargs
  schema, untyped JSON returned from a vendor). Use only when the
  payload must remain a `dict` for legacy reasons.
- **`enum.Enum` / `enum.StrEnum` / `enum.IntEnum`**: closed sets of
  named values. Pair with `msgspec.Struct` tagged unions for
  discriminator fields.

## Tagged unions with msgspec

```python
import msgspec

class CardPayment(msgspec.Struct, tag="card", tag_field="kind", frozen=True):
    pence: int
    last4: str

class CashPayment(msgspec.Struct, tag="cash", tag_field="kind", frozen=True):
    pence: int

Payment = CardPayment | CashPayment   # decoder picks the variant via "kind"

decoded = msgspec.json.decode(payload, type=Payment)
```

Tagged unions remove the "read a `dict`, then branch on a string field"
pattern. The decoder validates the discriminator and rejects unknown
variants when `forbid_unknown_fields=True`.

## Red flags

- a `dict[str, object]` flowing more than one layer into the codebase
  (parse to a schema type at the boundary),
- a dataclass that is rebuilt on every serialization and parse (use
  `msgspec.Struct`),
- a mutable domain object passed across thread or coroutine boundaries
  (freeze it or hand a copy),
- a `TypedDict` that grew validators, defaults, or computed properties
  (promote to `msgspec.Struct`),
- a `NamedTuple` queried by name everywhere (use a dataclass; tuple
  positional access is not needed),
- `forbid_unknown_fields=False` on a public API (silent acceptance of
  drift),
- discriminator branching written by hand when a tagged union would
  let the decoder do it.

Read [msgspec-structs.md](references/msgspec-structs.md),
[tagged-unions.md](references/tagged-unions.md), and
[dataclasses-and-typeddict.md](references/dataclasses-and-typeddict.md)
when the boundary, the discriminator, or the dataclass-vs-dict question
dominates.
