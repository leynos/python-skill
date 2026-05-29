# Stateful testing with RuleBasedStateMachine

`RuleBasedStateMachine` generates sequences of operations against a
reference model and a system under test, checks invariants after every
step, and shrinks failing sequences to the smallest counter-example.
The pattern shines on collections, caches, allocators, and protocol
clients where the bug needs a particular history to surface.

## Anatomy

```python
from hypothesis.stateful import (
    Bundle,
    RuleBasedStateMachine,
    invariant,
    precondition,
    rule,
)
from hypothesis import strategies as st

class CacheTest(RuleBasedStateMachine):
    keys: Bundle[str] = Bundle("keys")

    def __init__(self) -> None:
        super().__init__()
        self.model: dict[str, int] = {}
        self.cache = Cache(capacity=8)

    @rule(target=keys, k=st.text(min_size=1, max_size=8))
    def add_key(self, k: str) -> str:
        return k

    @rule(k=keys, v=st.integers())
    def set_value(self, k: str, v: int) -> None:
        self.model[k] = v
        self.cache[k] = v

    @rule(k=keys)
    @precondition(lambda self: bool(self.model))
    def get_value(self, k: str) -> None:
        assert self.cache.get(k) == self.model.get(k)

    @invariant()
    def capacity_holds(self) -> None:
        assert len(self.cache) <= 8


TestCache = CacheTest.TestCase
```

What each piece does:

- `Bundle` threads values produced by one rule into later rules. The
  `target=keys` argument on `add_key` says "the return value of this
  rule joins the `keys` bundle".
- `@rule` defines an operation; the runner picks rules at random,
  respecting `precondition` and the bundles.
- `@invariant` runs after every rule; if it fails, the runner shrinks
  the trace.
- `Class.TestCase` produces a `unittest`-style class that pytest
  picks up.

## When to apply

- The data structure has hidden state that a single-call property
  cannot reach (LRU cache, write-ahead log, transaction journal).
- A protocol client's invariants depend on the order of messages.
- A subprocess's behaviour depends on the previous command.

## When not to apply

- The function is stateless. A `@given` test is cheaper.
- Each operation touches a real database or external service; the
  cost per shrinking step compounds.

## Reading a failure

The runner prints a trace like:

```python
state = CacheTest()
v1 = state.add_key(k='a')
state.set_value(k=v1, v=0)
state.set_value(k=v1, v=1)
state.get_value(k=v1)
```

Reproduce locally, then promote to a named unit test that pins the
trace. The trace is the spec; the bug is whatever the trace shows.

## Common mistakes

- A `precondition` that filters most cases. Each rule should be
  generally applicable; preconditions are for "this rule needs a key
  in the bundle" not "this rule needs a specific value".
- An invariant that depends on which rule ran last. Invariants should
  hold after every step.
- A bundle without a `target`. The bundle stays empty and rules that
  depend on it never run.
- A model that diverges silently from the system under test. Assert
  equality at every read, not at the end.
