# Verification selection matrix

A side-by-side view of Hypothesis, CrossHair, and mutmut against the
question each one answers best.

## At a glance

| Concern                                  | Hypothesis                  | CrossHair                          | mutmut                       |
| ---------------------------------------- | --------------------------- | ---------------------------------- | ---------------------------- |
| Engine                                   | Random + shrinking          | Symbolic execution (Z3)            | Mutation of production code  |
| Catches                                  | Property violations         | Reachable assertion failures       | Test-suite blind spots       |
| Best on                                  | Pure functions, state machines | Small pure functions, branchy code | Suite quality                |
| Worst on                                 | C extensions, scheduling   | Floats, strings, heap-heavy code   | Slow suites                  |
| Time per run (typical)                   | Seconds to minutes          | Seconds to hours                   | Hours (parallelize nightly)  |
| Counter-example shape                    | Shrunk minimal input        | Concrete satisfying assignment     | Diff of surviving mutant     |
| Pairs naturally with                     | mutmut                      | Hypothesis                         | Hypothesis, pytest suites    |

## Pick by question

- "I want a property to hold for every input the user can produce."
  → Hypothesis. Express the property; let shrinking explain the
  smallest failure.
- "I want to know whether the function can reach the `assert` I just
  wrote." → CrossHair `check`. Symbolic execution explores branches
  the random generator may not have.
- "I refactored a function and want to verify nothing changes
  behaviour." → CrossHair `diffbehavior old.f new.f`.
- "Tests pass; I do not trust they would catch a bug." → mutmut.
- "I have a property and the test suite passes for the right reason."
  Combine Hypothesis (verifies the property) and mutmut (verifies the
  test would notice a violation).

## When to escalate beyond the three

- **Concurrency**: race-detector tools (Helgrind, ThreadSanitizer on
  C extensions), or specialized libraries like
  [`pytest-trio`/`pytest-anyio`] for async; the three tools here do
  not search the scheduling space.
- **Performance**: benchmarks plus profilers (`python-quality-tools`),
  not verification.
- **System invariants** (database, file system, network): end-to-end
  tests with a real or simulated backend.

## Common mis-applications

- Hypothesis on a function that calls a real database. The random
  inputs do not represent real load; the database is the bottleneck;
  the run is slow. Move to a fake or test the layer above.
- CrossHair on string-heavy code (regex compilers, parsers). Z3's
  string theory is improving but slow. The cost may exceed the
  benefit.
- mutmut on a slow suite without `pytest-xdist` or marker filtering.
  Each mutant runs the suite; the cost compounds.
- All three at once in CI on every push. Hypothesis in CI is fine;
  CrossHair and mutmut belong on slower cadences.
