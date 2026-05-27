---
name: python-abstractions
description: Use for Python decorators, descriptors, context managers (function and class form), metaclasses, and multiple dispatch. The common question is "which abstraction hides this complexity at the right level?".
globs: ["**/*.py"]
---

# Python Abstractions

Use this when the design question is which abstraction mechanism — decorator,
descriptor, context manager, metaclass, or dispatch — should carry a cross-
cutting concern.

## Working stance

- Reach for the lightest mechanism that works. Function ≺ decorator ≺
  context manager ≺ descriptor ≺ metaclass.
- Decorators preserve call shape; pair them with `ParamSpec` so the type
  checker sees through them.
- Class-based context managers are right when there is state to hold and
  shut down; `@contextmanager` is right when the resource is `try/finally`
  shaped and a single function expresses it cleanly.
- Descriptors belong on classes whose attributes need consistent
  validation, lazy computation, or per-instance bookkeeping; never use
  them when a `@property` suffices.
- Metaclasses are a last resort. Most "I want to customise class creation"
  problems are solved by `__init_subclass__`, decorators, or
  `dataclass_transform`.
- For multi-argument dispatch, prefer `functools.singledispatch` for the
  one-argument case and a typed external library for the multi-argument
  case; never fall back to `isinstance` ladders in a public function.

## Decision surface

- **Decorator (`P`, `R`)**: a cross-cutting concern (logging, retry,
  caching, transactions) wraps a function with a fixed call shape; the
  wrapper must preserve the wrapped signature for callers and type
  checkers (`ParamSpec`).
- **Function context manager (`@contextlib.contextmanager`)**: setup and
  teardown collapse into a single function with one `yield`; reuse is
  local.
- **Class context manager (`__enter__`/`__exit__`)**: the manager holds
  state, exposes methods between `__enter__` and `__exit__`, or needs
  custom exception suppression (`__exit__` returning `True`).
- **Async context manager (`__aenter__`/`__aexit__`,
  `@asynccontextmanager`)**: the resource is awaited (connection pool,
  HTTP session); never block in `__aenter__`.
- **Descriptor (`__get__`/`__set__`/`__set_name__`)**: an attribute
  needs validation, lazy computation, or per-instance state and the
  rule repeats across attributes (validated fields, typed columns,
  cached_property variants).
- **Metaclass**: class-creation behaviour cannot be expressed via
  `__init_subclass__`, `__class_getitem__`, decorators, or
  `dataclass_transform`. Examples: ORM model registries with custom
  MRO, plugin systems with strict invariants, `msgspec.Struct` itself.
- **Dispatch**:
  - `typing.overload` — static-only narrowing, no runtime dispatch.
  - `functools.singledispatch` — one argument, stdlib, global registry.
  - `plum-dispatch` / `ovld` — multi-argument, type-hint native,
    fast; reach for these when `isinstance` chains grow in a public
    function.

## Red flags

- a decorator typed `Callable[..., Any]` that erases the wrapped
  signature,
- a `@contextmanager` whose body spans tens of lines with branching
  cleanup (promote to a class-based manager),
- a class-based context manager that hides only a single
  `try/finally` (collapse to `@contextmanager`),
- a descriptor that stores per-instance state on the class object
  (data leaks across instances),
- a metaclass introduced for naming, validation, or registration that
  `__init_subclass__` could handle,
- a multi-argument `isinstance` ladder in a public function,
- `singledispatch` used on a method that should be a regular
  polymorphism point on the class.

Read [decorators-and-paramspec.md](references/decorators-and-paramspec.md),
[context-manager-extraction.md](references/context-manager-extraction.md),
[descriptors.md](references/descriptors.md), and
[metaclasses-and-dispatch.md](references/metaclasses-and-dispatch.md) when
one of those forks dominates.
