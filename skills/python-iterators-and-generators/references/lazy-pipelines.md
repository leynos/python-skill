# Lazy pipelines

A lazy pipeline is a sequence of generators where each stage pulls from
the previous one. Memory is bounded by the largest single item; the
input can be infinite.

## Building blocks

`itertools` carries most of the everyday operators:

- `chain(a, b, c)` — concatenate.
- `islice(it, start, stop)` — slice without materialising.
- `groupby(it, key=...)` — adjacent grouping; sort first if non-adjacent
  groups need merging.
- `accumulate(it, func)` — running totals or folds.
- `pairwise(it)` — consecutive pairs (Python 3.10+).
- `batched(it, n)` — fixed-size chunks (Python 3.12+).
- `chain.from_iterable(its)` — flatten one level.

Each is a generator, so composing them is `O(1)` memory per stage.

## Example pipeline

```python
from itertools import islice, groupby
from collections.abc import Iterable, Iterator

def parse_lines(it: Iterable[str]) -> Iterator[Event]:
    for line in it:
        if line and not line.startswith("#"):
            yield Event.parse(line)

def by_user(it: Iterable[Event]) -> Iterator[tuple[UserId, list[Event]]]:
    keyed = sorted(it, key=lambda e: e.user)        # required before groupby
    for user, group in groupby(keyed, key=lambda e: e.user):
        yield user, list(group)

def first_n_active(n: int, source: Iterable[str]) -> Iterator[UserId]:
    pipe = parse_lines(source)
    grouped = by_user(pipe)
    active = (uid for uid, evs in grouped if any(e.active for e in evs))
    return islice(active, n)
```

`first_n_active` reads the source on demand; consuming five items
processes the smallest prefix that produces five active users.

## When laziness costs more than it gives

- The intermediate stage needs random access (sorting, sampling without
  replacement, percentile). Materialise that stage explicitly.
- A consumer reads the iterator twice. Either restart the producer or
  materialise once into a `tuple`/`list`.
- The pipeline crosses a process boundary; pickle-able items must be
  produced eagerly per batch.

## `tee` is rarely the answer

`itertools.tee(it, n)` looks like it duplicates an iterator. Under the
hood it buffers items between the slowest and fastest consumer; if one
consumer falls far behind, the buffer grows without bound. Reach for a
real second pass over the source instead.

## Async pipelines

```python
async def pages(client) -> AsyncIterator[Page]:
    cursor: str | None = None
    while True:
        page = await client.get(cursor=cursor)
        yield page
        if page.cursor is None:
            return
        cursor = page.cursor

async def records(client) -> AsyncIterator[Record]:
    async for page in pages(client):
        for r in page.records:
            yield r
```

Async generators compose with `async for` and pair well with
`asyncio.TaskGroup` when the consumer needs fan-out concurrency.

## Common mistakes

- Calling `len(it)` on a generator. Generators do not have a length;
  materialise or count separately if a length is required.
- Building a generator and then returning `list(gen)` from the same
  function. Either return the generator or write a `list` directly.
- Holding two `itertools.tee` outputs alive in different threads.
  `tee` is not thread-safe and the shared buffer breaks.
- Treating `groupby` as a global group operator. It groups adjacent
  equal keys; sort first when the input is not already grouped.
