# Metaclasses and multiple dispatch

Two advanced patterns that share a common warning: most of the things they
seem to solve have a simpler answer.

## Before reaching for a metaclass

Try these first:

- `__init_subclass__` runs at subclass-definition time and receives the
  subclass and the keyword arguments passed on the `class` line. It
  covers most "register every subclass" and "enforce one method on
  every subclass" use cases.
- `__class_getitem__` (and `Generic[T]`) handles subscripted class
  syntax (`MyType[int]`) without touching class creation.
- `typing.dataclass_transform` lets a decorator pretend to be
  `@dataclass` for the static type checker without involving a
  metaclass.
- Class decorators handle one-off transformations of a single class.

A metaclass is the right answer only when the behaviour must run at
class-creation time and must do something the alternatives cannot —
custom MRO, control over which name binds the class, or a fully
custom `__call__` that does not return the class itself. The notable
real-world examples are `abc.ABCMeta`, `enum.EnumMeta`, and
`msgspec.Struct`'s `StructMeta`.

## Pattern: registration via `__init_subclass__`

```python
class Plugin:
    registry: dict[str, type[Plugin]] = {}

    def __init_subclass__(cls, *, name: str, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        Plugin.registry[name] = cls

class Json(Plugin, name="json"): ...
class Toml(Plugin, name="toml"): ...
```

Every subclass registers itself; no metaclass is required.

## Pattern: minimal metaclass

```python
class SealedMeta(type):
    def __new__(mcs, name, bases, ns, /, **kwds):
        cls = super().__new__(mcs, name, bases, ns, **kwds)
        if any(isinstance(b, SealedMeta) for b in bases) and ns.get("__sealed__"):
            msg = f"Cannot subclass sealed type {bases[0].__name__}"
            raise TypeError(msg)
        return cls

class Sealed(metaclass=SealedMeta):
    __sealed__ = True
```

Use this shape sparingly. `dataclass_transform` is the right answer
when the goal is to give the type checker something extra; a
metaclass should buy you a runtime invariant that nothing else can.

## Multiple dispatch

`isinstance` ladders in a public function are a classic refactoring
target:

```python
def render(node):
    if isinstance(node, Text):
        return render_text(node)
    if isinstance(node, Image):
        return render_image(node)
    ...
```

The three layered alternatives:

### `functools.singledispatch` — stdlib, first argument only

```python
from functools import singledispatch

@singledispatch
def render(node) -> str:
    msg = f"no renderer for {type(node).__name__}"
    raise TypeError(msg)

@render.register
def _(node: Text) -> str: ...
@render.register
def _(node: Image) -> str: ...
```

Use when one argument carries the dispatch and the registry can live in
one module.

### `plum-dispatch` and `ovld` — multi-argument, type-hint native

```python
from plum import dispatch

@dispatch
def overlap(a: Box, b: Box) -> bool: ...
@dispatch
def overlap(a: Box, b: Circle) -> bool: ...
@dispatch
def overlap(a: Circle, b: Circle) -> bool: ...
```

Use when dispatch is genuinely multi-argument (geometry overlap,
arithmetic over polymorphic operands) and the types involved are
named.

### `typing.overload` — static only

```python
from typing import overload, Literal

@overload
def parse(s: str, *, raw: Literal[True]) -> bytes: ...
@overload
def parse(s: str, *, raw: Literal[False] = False) -> dict[str, object]: ...
```

`@overload` does not dispatch at runtime; it tells the type checker that
the return type depends on the literal argument. Use it when the
runtime body is one function but the static surface has shape variation.

### When to keep the `isinstance` ladder

If there are two cases and the function is internal, do not paper over
it with dispatch. Polymorphism (a method on each subclass) is also a
better answer when the dispatched function naturally belongs on the
class.

## Common mistakes

- A metaclass introduced for naming or registration that
  `__init_subclass__` would handle.
- `singledispatch` on a method that should be a real virtual call on
  the class.
- A dispatch library imported just to give the checker overload-shape
  information; `@overload` does that without adding a runtime
  dependency.
