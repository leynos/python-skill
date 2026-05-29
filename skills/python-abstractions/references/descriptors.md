# Descriptors

A descriptor is any class that defines `__get__`, `__set__`, or
`__delete__`. The descriptor protocol sits underneath `@property`,
`@classmethod`, `@staticmethod`, and `functools.cached_property`.

Reach for a custom descriptor when an attribute pattern (validation,
lazy computation, per-instance caching) repeats across many classes
or many attributes of one class, and `@property` would force a
hand-written copy each time.

## Pattern: validated field

```python
from typing import Any

class Positive:
    def __set_name__(self, owner: type, name: str) -> None:
        self._name = "_" + name

    def __get__(self, obj: Any, owner: type | None = None) -> int:
        if obj is None:
            return self                   # access on the class
        return getattr(obj, self._name)

    def __set__(self, obj: Any, value: int) -> None:
        if value <= 0:
            msg = f"value must be positive, got {value!r}"
            raise ValueError(msg)
        setattr(obj, self._name, value)

class Order:
    quantity = Positive()
    pence = Positive()
```

`__set_name__` runs when the class body is executed; it captures the
attribute name so the descriptor can store per-instance state on the
owning object (`_quantity`, `_pence`) rather than on the descriptor
itself.

## Pattern: lazy attribute (cached_property style)

```python
class Once:
    def __init__(self, fn):
        self._fn = fn
        self._name = fn.__name__

    def __set_name__(self, owner: type, name: str) -> None:
        self._name = name

    def __get__(self, obj, owner=None):
        if obj is None:
            return self
        value = self._fn(obj)
        obj.__dict__[self._name] = value
        return value

class Report:
    @Once
    def summary(self) -> dict[str, int]:
        return compute_summary()
```

Writing the computed value into `obj.__dict__` makes the next access
skip the descriptor entirely; this is exactly how
`functools.cached_property` works. Prefer the stdlib version unless
the descriptor needs custom invalidation or shared cache.

## Data vs non-data descriptors

A descriptor that defines `__set__` (or `__delete__`) is a **data**
descriptor; it wins over the instance `__dict__`. A descriptor that
only defines `__get__` is a **non-data** descriptor; the instance
`__dict__` wins.

`cached_property` is non-data on purpose: the cached value lives in
`__dict__` and shadows the descriptor on every subsequent access.

## Where descriptors do not belong

- A single attribute on a single class. Use `@property`.
- A protocol negotiation between two unrelated classes. Use a
  `Protocol` and explicit methods.
- A registry of "all subclasses of X". Use `__init_subclass__`.
- A surrogate for dependency injection. Use plain constructor
  arguments.

## Common mistakes

- Storing per-instance state on the descriptor object: every instance
  of the owning class shares one slot, so values leak between
  instances. Use `__set_name__` plus instance attributes.
- Forgetting the `obj is None` branch in `__get__`: access on the
  class (`Order.quantity`) crashes.
- Defining `__set__` when only lazy read was intended; that turns the
  descriptor into a data descriptor and breaks subclass overrides via
  `__dict__`.
- Reaching for a descriptor when a dataclass with a `__post_init__`
  validation would do.
