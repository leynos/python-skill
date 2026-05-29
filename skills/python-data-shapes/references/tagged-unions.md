# Tagged unions

A tagged union (sum type) names the closed set of shapes a value can
take and carries a discriminator that selects the variant. Used at the
wire boundary, it removes the most common source of "what shape did the
parser actually return?" bugs.

## msgspec tagged unions

```python
import msgspec

class CardPayment(
    msgspec.Struct,
    tag="card",
    tag_field="kind",
    frozen=True,
    forbid_unknown_fields=True,
):
    pence: int
    last4: str

class CashPayment(
    msgspec.Struct,
    tag="cash",
    tag_field="kind",
    frozen=True,
    forbid_unknown_fields=True,
):
    pence: int

Payment = CardPayment | CashPayment

decoded = msgspec.json.decode(payload, type=Payment)
match decoded:
    case CardPayment(pence=p, last4=l):
        ...
    case CashPayment(pence=p):
        ...
```

`tag` is the literal value carried in the discriminator field; `tag_field`
is the field name. The decoder picks the variant before validating the
remaining fields, so unknown discriminators fail loudly.

## Discriminator placement

- `tag_field="kind"` keeps the discriminator next to the rest of the
  fields; the default `"type"` collides with user fields surprisingly
  often.
- The discriminator value can be a string (`tag="card"`) or an
  integer (`tag=1`). Strings are easier to debug; integers shrink the
  payload.
- Every variant must use the same `tag_field`. Mixing fields produces
  a parser that cannot disambiguate.

## Pattern matching on the union

`match` with class patterns is the cleanest consumer:

```python
def total(p: Payment) -> int:
    match p:
        case CardPayment(pence=p):
            return p
        case CashPayment(pence=p):
            return p
```

The type checker exhausts the match against the union; adding a new
variant without updating the consumer produces a checker error.

## Tag inheritance

A common pattern is a base struct with shared fields:

```python
class _Base(msgspec.Struct, kw_only=True):
    created_at: datetime

class Click(_Base, tag="click", tag_field="kind"):
    target: str

class Submit(_Base, tag="submit", tag_field="kind"):
    form_id: str

Event = Click | Submit
```

The base supplies common fields; each subclass carries its
discriminator. Avoid making the base itself part of the union — only
the leaf variants should be decoded.

## When a tagged union is the wrong tool

- The variants share most fields and differ in one optional value.
  Use a single struct with `Optional` fields.
- The discriminator is computed (`if x > 0 then A else B`). A tagged
  union forces a wire-level distinction; if no wire-level distinction
  exists, model the rule in code.
- The set of variants is open (plugins register new ones at runtime).
  A registry plus a polymorphic loader is a better fit; tagged unions
  are closed by design.

## Common mistakes

- Forgetting `forbid_unknown_fields=True`: unknown keys inside a variant
  decode silently, hiding wire drift.
- Reusing one `tag_field` across two unrelated unions. The decoder
  cannot disambiguate; pick distinct fields per union.
- Treating the decoded variant as a `dict` and writing `if d["kind"] ==
  "card"` ladders. The whole point of the union is that the decoder
  has already picked the type.
