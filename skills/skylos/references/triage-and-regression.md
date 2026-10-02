# Skylos triage and regression patterns

## The motivating failure

A maintainer-supplied, abridged Cuprum session from 18–19 September 2026
reported this sequence. It omitted terminal results and ended while a full test
gate was still running; do not cite it as a completed green build or as an
independently reproduced Skylos benchmark.

1. Main introduced a Skylos rule naming
   `_PersistentNativePumpExecutor.submit`. The feature branch renamed the
   implementation to `_PooledNativePumpExecutor`. Git merged the text, but code
   and configuration no longer agreed.
2. Correcting that name exempted `submit`, yet `_start_worker`,
   `_take_worker`, `_retire_or_reuse`, and `_worker_loop` still reported. The
   agent repeatedly reconsidered whether entrypoint exemptions propagated
   through their `called_by` edges.
3. Source inspection and a scratch probe distinguished per-definition
   exemptions from packaged script entry points. The gate disabled grep
   verification, so a different rescue-enabled run was not equivalent.
4. A parent selector cleared the helpers, but would also cover future
   dead methods. The eventual change kept an explicit method-name list,
   corrected the callback explanation, and updated the exact-set contract test.
   That test needed the project's development environment.
5. The agent reported a passing full lint rerun, including stages the
   first failure had prevented from running. The copied session did not
   establish the final full-test result.

The portable lesson is not "whitelist every warning". It is to identify real
callers, determine the actual scanner semantics once, and keep each justified
exception narrow and independently testable.

## A bounded investigation

Keep a small decision record with the candidate names, baseline command, one
hypothesis, predicted result, observed result, and chosen action. Do not write
pages of repeated possibilities before checking the docs.

For the root-versus-exemption question, use a scratch directory outside the
repository's scan roots. Preserve the package layout and the pinned launcher's
config-discovery behaviour. Copy only the relevant policy, not private
production payloads or an entire application environment.

Make the fixture contain a Protocol-dispatched method, a private helper that it
calls, and a truly unused sibling. Start with the minimum case that actually
reproduces the reported helper finding. When callbacks matter, preserve the
intermediate constructor forwarding the callable to `Thread.target`; replacing
it with a direct call tests a different analysis shape.

Run four variants sequentially, with unchanged source except where the
experiment explicitly calls for a mutation:

| Variant                                          | Expected discriminating evidence                                               |
| ------------------------------------------------ | ------------------------------------------------------------------------------ |
| Baseline without the candidate exception         | The target helper and unused control are reportable.                           |
| Exact rule for the public dispatch method only   | Whether the helper finding remains answers the propagation question.           |
| Explicit rules for the demonstrated live methods | Those findings disappear; the unused sibling remains.                          |
| Broad parent-only method rule, scratch only      | Check whether it also hides the unused sibling. Reject that production policy. |

These are predictions to test, not promised outputs on all versions. If the
baseline does not report the intended helper, the fixture is not a
reproduction. In particular, naming heuristics or Protocol hard skips can make
a simplified example vacuous. Inspect class, method, and parameter findings
separately before drawing a conclusion.

After one discriminating result that agrees with the pinned source, record the
finding and proceed. If they disagree, preserve the exact fixture, version,
config, and JSON for an upstream issue. Do not turn triage into speculative
rewrites of the worker implementation.

## Prove live code through its real entry

For a pool, the useful regression starts at the application boundary that
receives the Protocol-typed executor. Observe the submitted work, worker
callback, result, and completion/retirement behaviour. A test that calls
`_worker_loop` directly proves only that the test can call it.

Use synchronization rather than arbitrary sleeps when the question is whether a
callback started. Assert the intended backend and at least one actual callback
invocation. An available native extension does not imply that a test used it; a
fallback can make an otherwise convincing test pass without reaching the code
under review.

Where practical, demonstrate test sensitivity in an isolated copy: remove or
miswire the relevant call and show the regression fails for the expected
reason. Restore the fixture before the final gates. A syntax error, failed
import, or unrelated timeout is not that evidence.

For deletions, also inspect import side effects, public exports, plugin
registrations, packaging entry points, reflection, native consumers, and
external compatibility promises. An unused binding does not make the right-hand
side of its assignment dispensable. Removing an unused parameter can still
break a callback or public signature. Remove dead components in coherent small
steps and rescan after each step rather than deleting an entire report blindly.

## Keep exception tests independent

Adapt the consuming repository's existing contract test. The following
illustrative test checks the configuration example in
[configuration-and-evidence.md](configuration-and-evidence.md); the repository
root is one level above the test file. It deliberately pins an independently
written set rather than reading its expectation from the same TOML.

```python
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_METHODS = frozenset(
    {
        "example.pool.PoolExecutor.submit",
        "example.pool.PoolExecutor._take_worker",
        "example.pool.PoolExecutor._start_worker",
        "example.pool.PoolExecutor._worker_loop",
        "example.pool.PoolExecutor._retire_or_reuse",
    }
)


def test_pool_dead_code_configuration() -> None:
    """Keep the pool exception finite and tied to its actual callers."""
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    entries = data["tool"]["skylos"]["dead_code"]["entrypoints"]
    pool_rules = [
        rule
        for rule in entries
        if rule.get("path") == "example/pool.py"
    ]
    assert len(pool_rules) == 1
    rule = pool_rules[0]
    assert set(rule) == {"type", "full_name", "path", "reason"}
    assert rule["type"] == "method"
    names = rule["full_name"]
    assert isinstance(names, list)
    assert len(names) == len(EXPECTED_METHODS)
    assert set(names) == EXPECTED_METHODS
    assert isinstance(rule["reason"], str)
    assert rule["reason"].strip()
```

This is a configuration-shape test, not proof of liveness or a complete
repository-wide exemption audit. A broad overlapping rule elsewhere could still
hide the unused sibling; the scanner negative control must catch that. Existing
repository policy should also constrain other whitelists, ignored rules,
excluded paths, and gate options.

Add a check that configured definitions still exist with the claimed kind and
module. An AST-based inventory avoids importing application modules that start
threads or load native extensions. Review reasons against the current call
chain; nonempty prose alone cannot prove truth.

For a rename or extraction, update names, paths, reasons, expected sets, docs,
and workflow whitelist reports together. Search both the old class name and the
old module name; do not retain obsolete entries "for compatibility" when only
configuration still references them.

## Separate probe evidence from gate evidence

Use the Skylos environment for scanner probes and the project environment for
pytest. If `conftest.py` fails to import, repair the environment and rerun:
that is not a failed configuration assertion. Do not install test dependencies
into the scanner tool environment as an ad hoc workaround.

Give every scan and gate a unique log, record exit status and revision, and let
one runner own the gate sequence. Do not overwrite a previous log or edit the
worktree while another runner validates it. If files change, invalidate the
affected evidence explicitly.

The finish order is the targeted Skylos check, configuration and runtime tests,
then all repository-required gates on the final tree. A stopped lint pipeline
leaves later stages untested. A clean earlier commit, pre-merge approval, or
successful targeted run does not validate a new merged tree. Report skipped or
unavailable checks as such.

A useful hand-off names the removed code or exact exceptions, the real caller
evidence, the unused negative control, the version and command, the final
revision, and any remaining limitation. Keep the original private transcript
and scratch logs out of a public repository.
