# Python skill research notes

Consolidated firecrawl findings on each requested topic, with a relevance
weighting that drives the skill catalogue distillation.

## Weighting key

- **Core**: deserves a first-class language or domain skill.
- **Section**: deserves a section inside an existing first-class skill.
- **Reference**: useful detail for a `references/` document, not the main
  decision surface.

______________________________________________________________________

## Subinterpreters and PEP 734 — Core

Python 3.13 added a working C-level subinterpreter API; Python 3.14 ships the
high-level `concurrent.interpreters` module and
`concurrent.futures.InterpreterPoolExecutor`.
Each subinterpreter has its own GIL, so CPU-bound work in pure Python scales
across cores without the free-threaded build.

Operational shape:

- Workers do not share Python objects; communication crosses a queue with
  pickle-able payloads or shared memory primitives.
- Startup cost is non-trivial; treat each interpreter as a thread-pool worker
  with state, not as a coroutine.
- C-extension authors must opt in to per-interpreter GIL via module slots
  (`Py_mod_multiple_interpreters = Py_MOD_PER_INTERPRETER_GIL_SUPPORTED`).
- Existing thread/asyncio idioms remain correct for I/O-bound work; PEP 734
  is for CPU-bound parallelism without `multiprocessing` fork overhead.

Weight: Core. Drives a `python-concurrency` skill that contrasts threads,
asyncio, multiprocessing, and subinterpreters by workload shape.

## msgspec — Core

`msgspec.Struct` is a fast, schema-validating data class. Key design knobs:

- `frozen=True`, `kw_only=True`, `omit_defaults=True`, `forbid_unknown_fields=True`,
  `array_like=True`, `rename="camel"`, `gc=False`.
- Tagged unions via `tag` and `tag_field` on each variant; the decoder picks
  the right struct from a discriminator.
- `Meta` annotations attach validation constraints (`ge`, `le`, `min_length`,
  `pattern`).
- Encoding and decoding bypass the JSON parser for JSON, MessagePack, YAML,
  and TOML payloads; struct creation goes through `StructMeta` so attribute
  layout is fixed at class definition time.
- The library competes with `pydantic` for the same role; the trade-off is
  speed and a smaller feature surface versus pydantic's richer validators.

Weight: Core in a `python-data-shapes` skill alongside dataclasses, attrs,
and TypedDict guidance.

## CrossHair — Core deep dive

CrossHair runs Python under symbolic execution backed by Z3. It explores
all reachable paths through a function (within an interpreter timeout)
and reports counter-examples when contracts or assertions fail.

Modes:

- `crosshair check <module>` — verify contracts (icontract / deal / PEP 316
  docstring contracts) or `assert` statements.
- `crosshair cover <function>` — find inputs that drive a function down
  unexplored branches; useful for filling coverage holes.
- `crosshair diffbehavior old.f new.f` — find an input where two implementations
  disagree.
- Hypothesis backend: `@given` strategies can dispatch to CrossHair as a
  search engine when Hypothesis cannot find a falsifying example.

Limits: pure Python only, slow on heap-heavy code, weak on string and float
arithmetic, no support for `ctypes`, threads, or I/O. It pairs with mutmut
(does the property notice the bug?) and Hypothesis (how big is the example
space?).

Weight: Core. Deserves its own deep-dive skill loaded after `python-verification`.

## Hypothesis — Core deep dive

Property-based testing for Python. Three sub-topics drive the deep dive:

1. Strategies: `st.builds`, `st.from_type`, `st.recursive`, `st.composite`,
   `assume`, and the filtering trap (parallel to proptest).
2. Stateful testing: `RuleBasedStateMachine` with `@rule`, `@invariant`,
   `@precondition`, `Bundle`. Used for collection, cache, parser, and
   protocol invariants.
3. Settings and CI: `settings(max_examples=...)`, deadlines, derandomise,
   the `.hypothesis/examples` database, `--hypothesis-seed`, and the
   `pytest --hypothesis-show-statistics` flag.

Weight: Core deep dive. Mirrors the `proptest` deep dive on the Rust side.

## mutmut — Core deep dive

Mutation testing tool. v3 rewrote the engine; the workflow is:

- `mutmut run` (forks per mutant on POSIX; on Windows uses WSL).
- `mutmut browse` opens a TUI that shows surviving mutants per file.
- `mutmut show <id>` displays the diff; `mutmut apply <id>` writes it.
- Configuration in `[tool.mutmut]` of `pyproject.toml`: `paths_to_mutate`,
  `tests_dir`, `runner`, `do_not_mutate`, `also_copy`.
- `# pragma: no mutate` excludes a line.
- Pair with type-checker filtering: mutants caught by mypy/pyright count
  for "the type system already enforces this" but should be filtered out
  of the survivor list.

Weight: Core deep dive alongside Hypothesis and CrossHair.

## pyscn — Section

Go-based static analyser using tree-sitter. Capabilities:

- Dead code detection from a control-flow graph (reaches code after `return`,
  unconditional `raise`, unreachable `elif`).
- Clone detection across Type 1–4 (identical, renamed, near-miss, semantic).
- CBO (coupling between objects) and complexity metrics per function.
- MCP server integration; the everyday invocation is `uvx pyscn@latest analyze .`.
- Output JSON, SARIF, or table; pairs with `deadcode --fix` for the
  unreferenced-symbol half of the dead-code question.

Weight: Section inside a `python-quality-tools` skill alongside `deadcode`
and `pyinstrument`.

## deadcode — Section

PyPI tool (Albertas Gimbutas). Single binary, finds unused symbols by name
and scope. Key flags:

- `deadcode .` — list candidates.
- `--fix` — rewrite files to remove candidates (review the diff!).
- `--exclude`, `--ignore-names`, `--ignore-names-in-files` — suppression knobs.
- `--no-color`, `--quiet` — CI-friendly output.

Limits: name-based, so dynamic dispatch (`getattr`, plugin registries, ORM
lazy attributes) needs ignore lists. Complements pyscn's CFG-based
unreachable-code detection — different failure modes.

Weight: Section in `python-quality-tools`.

## Pyinstrument — Section

Statistical sampling profiler. Defaults: 1 ms interval, low overhead, plays
nicely with pytest (`pytest --pyinstrument`) and Django/Flask middleware.

Usage patterns:

- `pyinstrument script.py`
- `with pyinstrument.profile():` block in a test or REPL session.
- `--renderer=speedscope` produces a flamegraph for the speedscope viewer;
  `--renderer=html` produces a self-contained report.

Trade-off versus `cProfile`: sampling misses very short functions but does
not perturb tight loops or async event loops; deterministic profilers
exaggerate small-function cost.

Weight: Section in `python-quality-tools`.

## multipledispatch — Section

Three layers exist in practice:

1. `functools.singledispatch` (stdlib) — first argument only, used widely
   for serialisers and pretty-printers.
2. `multipledispatch` (PyPI) — multi-argument dispatch, global registry,
   uses MRO; mature but unfashionable.
3. `plum-dispatch` and `ovld` — newer, faster, type-hint native, support
   generics and `Annotated`.

The decision surface: are you dispatching on one or many arguments, do you
need to dispatch across module boundaries (global vs explicit registry),
and is `typing.overload` for a static checker enough?

Weight: Section in `python-abstractions` skill (decorators, descriptors,
context managers, metaclasses, dispatch).

## ParamSpec, TypeVar, TypeIs, and TypeGuard — Section + reference

PEP 612 introduced `ParamSpec` for decorators that preserve a wrapped
function's signature; `typing.Concatenate` adds prefix arguments.

```python
P = ParamSpec("P")
R = TypeVar("R")

def trace(fn: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(fn)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        log.debug("call %s", fn.__qualname__)
        return fn(*args, **kwargs)
    return wrapped
```

PEP 742 (`TypeIs`) narrows both branches; `TypeGuard` narrows only the
true branch. Prefer `TypeIs` for predicates that are honest equivalences,
keep `TypeGuard` for one-way narrowings (e.g. "this is non-empty").

PEP 695 brings inline generic syntax:

```python
def first[T](xs: list[T]) -> T: ...
class Cache[K, V]: ...
```

PEP 696 adds `TypeVar` defaults; PEP 698 adds `@override` for safer subclass
overrides.

Weight: Core section in `python-types-and-apis`; the worked decorator and
narrowing examples live in references.

## Hypothesis stateful testing — Reference

`RuleBasedStateMachine` lets Hypothesis drive a reference model alongside
a system under test. Rules pick the next operation; invariants run after
every step; bundles thread generated values through later rules. Shrinking
reduces the failing trace to a minimal sequence.

Weight: Reference inside `hypothesis` deep dive.

______________________________________________________________________

## Cross-cutting design conclusions

- Mirror the rust-skill topology: one router, several language skills, one
  domain cluster (data shapes, concurrency, quality tools), one verification
  selector, and three verification deep dives (`hypothesis`, `crosshair`,
  `mutmut`).
- Pull exception and logging rules from
  `../agent-template-python/template/.rules` into a dedicated
  `python-errors-and-logging` skill; the rule files already encode the
  decision surface (TRY/BLE/EM/LOG/N818/PERF203/B017) and only need
  re-framing as "when to load" and "decision surface" sections.
- Keep each SKILL.md under ~120 lines; defer long examples and comparison
  tables to `references/`.
- The router should resolve to one language skill plus at most one of:
  `python-data-shapes`, `python-concurrency`, `python-testing`,
  `python-verification`, `python-quality-tools`.
