# Dataclasses, attrs, NamedTuple, TypedDict

The stdlib and near-stdlib containers cover the cases where `msgspec`
is the wrong weight. Use this map to pick.

## dataclasses.dataclass

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True, kw_only=True)
class Address:
    line1: str
    line2: str | None
    postcode: str
```

Reach for `dataclasses` when:

- the type is a domain object that never crosses the wire,
- you want `__init__`/`__repr__`/`__eq__` generated,
- the validation needed is "the constructor accepts these arguments"
  and nothing more.

Combine `frozen=True`, `slots=True`, `kw_only=True` for safe defaults.
`__post_init__` covers the single-line validations; richer rules
suggest `attrs` or `msgspec`.

## attrs

```python
import attrs

@attrs.frozen(kw_only=True)
class Address:
    line1: str
    line2: str | None = None
    postcode: str = attrs.field(validator=attrs.validators.matches_re(r"^[A-Z0-9 ]+$"))
```

`attrs` is dataclasses with extra knobs: converters, validators,
slotted by default in `attrs.frozen`, `__attrs_post_init__` for
cross-field checks. Pick it when validation and conversion logic
multiply and you do not want to rebuild it on every container.

## NamedTuple

```python
from typing import NamedTuple

class Version(NamedTuple):
    major: int
    minor: int
    patch: int
```

Use when:

- the data is genuinely a small positional record,
- callers want tuple unpacking (`maj, _, _ = version`),
- immutability and hashability are required and the tuple shape is
  stable.

Avoid when:

- callers always access by name (a dataclass is cheaper to evolve),
- you find yourself adding methods (the class will fight tuple
  semantics),
- the data is keyword-only at construction (NamedTuple is positional
  first).

## TypedDict

```python
from typing import NotRequired, TypedDict

class Payload(TypedDict):
    id: str
    note: NotRequired[str]
```

Use when:

- the data must remain a `dict` for legacy reasons (vendor SDK,
  third-party library that mutates),
- the function signature wants typed kwargs via
  `**kwargs: Unpack[Payload]`,
- the schema is loose and you only need static checking, not runtime
  validation.

`TypedDict` does not validate at runtime. Pair with a parser or
`msgspec.convert` if the payload arrives from an untrusted source.

## Mutable defaults

The dataclass trap repeats in every container. Mutable defaults are
shared across instances unless wrapped in a factory:

```python
@dataclass
class Bad:
    tags: list[str] = []          # shared list across instances

@dataclass
class Good:
    tags: list[str] = field(default_factory=list)
```

`msgspec.Struct` uses `msgspec.field(default_factory=list)`. `attrs`
uses `attrs.field(factory=list)`. The error mode is identical
everywhere; the syntax differs.

## Picking between containers

- Cross-the-wire, must validate on decode: `msgspec.Struct`.
- In-process domain shape, no decode: `dataclass(frozen, slots,
  kw_only)`.
- In-process with rich validators: `attrs.frozen`.
- Small positional tuple: `NamedTuple`.
- Typed view over a `dict`: `TypedDict`.

The wrong move is to mix three containers in one module. Pick one for
each layer (wire, domain, helpers) and stick to it.
