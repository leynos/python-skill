# Skylos configuration and evidence

## Version boundary and sources

The motivating maintainer-supplied transcript used Skylos **4.33.2**.
Its command results were omitted from the copy, so the case study records
what the agent reported rather than claiming an independently repeated
end-to-end scan. The implementation references below use upstream tag
`v4.33.2`, commit `de23f0c52a21c724fdbdcdaa340fc573676e9f6a`.
Use the consuming repository's pin, not an assumed latest version.

Read the relevant upstream page before experimenting:

- [Configuration][configuration]: selector fields and whitelist forms.
- [Dead-code detection][dead-code]: findings, JSON output, and tracing.
- [Confidence and penalties][penalties]: Protocol and other skip heuristics.
- [CLI reference][cli]: invocation and output options.

These documentation pages move independently of a repository's pin.
For version-sensitive questions, inspect that installed source or a
versioned source link, then reproduce the smallest relevant case.

## Capture a reproducible baseline

Prefer the repository launcher. The following is a standalone version
check for a project that uses a `uv` tool environment; it does not replace
an existing Makefile target or imply that 4.33.2 must be installed:

```bash
: "${SKYLOS_VERSION:?Set the exact repository pin}"
skylos=(uv tool run --from "skylos==${SKYLOS_VERSION}" skylos)
"${skylos[@]}" --version
"${skylos[@]}" --help
```

Do not assume the executable on `PATH` belongs to the project or that
an isolated tool's package lives inside `.venv`. Locate the executable
and package through the same launcher/interpreter that runs the gate;
`importlib.metadata.version("skylos")` and `skylos.__file__` help there.
Avoid searching every shared cache or reading other agents' logs.

For a repository whose failing target is `make lint`, capture it with a
fresh directory and the original exit status:

```bash
set -euo pipefail
logdir="$(mktemp -d "${TMPDIR:-/tmp}/skylos-triage.XXXXXX")"
git rev-parse HEAD > "$logdir/revision.txt"
git status --porcelain=v1 > "$logdir/worktree.txt"
status=0
make lint > "$logdir/lint.log" 2>&1 || status=$?
printf '%s\n' "$status" > "$logdir/lint.exit"
cat "$logdir/lint.log"
printf 'Evidence: %s\n' "$logdir"
exit "$status"
```

This wrapper preserves failure; it does not turn it into success. Record
policy and config separately. For the diagnostic rerun, copy the resolved
Skylos command exactly and add only the pinned version's JSON output
options. The documented shape is `skylos . --json -o report.json`;
replace `.` with the gate's actual root and retain all its policy flags.
Keep diagnostic stderr separate from machine-readable JSON.

A source-root change can alter both the available callers and definition
names. A changed working directory can also select a different config.
Use an explicit config option only when that pinned CLI supports it;
otherwise reproduce the gate's discovery layout. Inspect excludes,
parse diagnostics, trace/cache inputs, confidence, and grep verification
before comparing counts. Do not equate zero findings with a complete scan.

## Reporting exemptions are not script entry points

The 4.33.2 [configured-entrypoint matcher][matcher] checks one definition
at a time. Its result is a matching reason, not a traversal of callees.
The supplied case reported that listing `submit` removed that finding
while its four private helpers remained `likely_dead`, even though the
JSON contained `called_by` links between those helpers.

Separately, [script-entrypoint extraction][scripts] reads
`[project.scripts]`, `[project.gui-scripts]`, and string-valued Poetry
scripts. It does not read `tool.skylos.dead_code.entrypoints`.
[The evidence builder][evidence] accepts those extracted qualified names
and records package-entrypoint evidence. Do not extrapolate that into a
promise of perfect transitive resolution through every dynamic call.

A genuine installed command belongs in packaging metadata. A callback
analysis exception belongs in the repository's exception policy. Never
invent a console script, export, or runtime call to alter scan results.

## A narrow, valid configuration

This example uses illustrative names. Replace them with the exact
qualified names and paths from the consuming repository's scan and
verify the matches. The finite list represents individually reviewed
methods, not a blanket claim that every member of an executor is live.

```toml
[[tool.skylos.dead_code.entrypoints]]
type = "method"
full_name = [
  "example.pool.PoolExecutor.submit",
  "example.pool.PoolExecutor._take_worker",
  "example.pool.PoolExecutor._start_worker",
  "example.pool.PoolExecutor._worker_loop",
  "example.pool.PoolExecutor._retire_or_reuse",
]
path = "example/pool.py"
reason = """
The runtime dispatches submit through its executor Protocol; submit calls
_take_worker and _start_worker. _start_worker passes _worker_loop through
the worker constructor to Thread.target; the loop calls _retire_or_reuse.
The pinned scan does not establish this live runtime path. The runtime
regression exercises that dispatch and observes the worker callback.
"""
```

Add this only after that evidence exists. Update an existing rule rather
than appending duplicates. Do not put `entrypoints = []` in
`[tool.skylos.dead_code]` before declaring the same key as an array of
tables: that defines the key twice and is invalid TOML.

In the pinned matcher:

- Supplied selector fields constrain the same match; alternatives within
  a list use any-match semantics. String patterns use `fnmatchcase`.
- `full_name` matches the definition's internal qualified name, not
  necessarily its short display name. Verify it rather than guessing a
  package prefix or relying on suffix coincidences.
- `path`, `module`, and `type` alone are insufficient. Add a specific
  symbol selector. Prefer nonempty literal names to broad patterns.
- A `parent` selector inspects the parent class. Without a member-name
  constraint it can match all methods, including future dead ones.
  A class-only exemption is not equivalent to a method selector.

Keep function and method rules separate. A helper moved from a thread
target to a direct call needs a new reason or removal of a now-unnecessary
exception, not a stale story copied from the old implementation.

## Documentation liveness and its ceilings

The 4.33.2 [liveness pass][liveness] rescues a method with the reason
`documented_public_api` when all of the following hold:

- The method name is public, and its file is not under a `test`,
  `tests`, `docs`, or `examples` directory. Module-level functions are
  never rescued this way.
- The owning class is live: it has a reference, is exported, or has a
  public name. A private `_Owner` needs a reference or an export.
- The combined document text contains `Owner.method` on word
  boundaries, a `:meth:` role ending in `Owner.method` or `method`, or,
  for a method name of at least ten characters containing `_`,
  `.method(`.

Documents are files ending in `.md`, `.rst`, or `.txt`, or whose stem is
`README` or `FAQ`, found by `rglob` under the resolved project root: the
nearest ancestor of the scan path holding `pyproject.toml`,
`package.json`, `setup.py`, or `.git`. Scanning `src/` still reads the
repository's `docs/`. Only `.git`, `.venv`, `venv`, and `__pycache__`
are excluded, so build output, vendored trees, and `node_modules` spend
the same budget.

Two constants bound the read, with no warning and no setting:

- A document over 300000 bytes is skipped. Exactly 300000 bytes is read.
- Reading stops at the first document that would take the running total
  past 2000000 bytes; it and every later document are ignored.

`rglob` order follows the filesystem, not a sorted path, so which
documents fall outside the total budget can differ between machines.
`SKYLOS_DEAD_CODE_LIVENESS=0` disables every liveness rescue at once; it
is an experiment switch, not a repair.

A scratch probe with the 4.33.2 release, run as
`skylos pkg --json --no-grep-verify`, confirmed each boundary. A 46-byte
guide naming `Owner.documented_method` rescued it. Padding that guide to
300045 bytes returned the method to `unused_functions` with nothing on
stderr. With the guide read after seven 290000-byte text files, it was
skipped; with six, it was read. The motivating repository's developers'
guide crossed 300000 bytes during ordinary documentation growth, so
further material moved to a separate topic document.

To diagnose a finding that appeared after a docs-only change, compare
`analysis_summary.dead_code_liveness.rescued` in the JSON report before
and after that change. A lost `documented_public_api` rescue shows that
the ceiling changed the evidence; it does not show whether the method is
live. Triage it as in the skill: restore a missing caller, record a
verified implicit caller as an entrypoint naming it, or delete dead code.

## Inspect evidence without overreading it

Find the exact symbol in the emitted schema. Depending on the version
and report, identity may appear in a findings bucket's `name` or in a
symbol evidence record's `qualified_name`. Keep kind and file alongside
it; a class, one of its methods, and that method's parameter are not the
same finding.

`called_by` establishes a recorded edge, not a live root. A
`likely_dead` classification or a high confidence score remains a
static-analysis judgement, not proof that deleting an externally called
API is safe. Check registration, packaging, dependency injection,
Protocol-typed attributes, native bindings, and callback forwarding.

The penalty documentation describes explicit and structural Protocol
heuristics. Treat these as patterns to verify, not a reason to assume
all implementations and private callees must disappear from every scan.
An alias-versus-direct-import probe must compare the same definitions,
configuration, and scan roots. Do not change production inheritance or
import style based on a toy example that exercised a different path.

Runtime tracing is an optional, separate experiment: it executes code
and changes the evidence available to the scan. Use the project test
environment, confirm callback or backend hit counts, and preserve the
static gate policy. An observed call proves that execution occurred;
no observed call does not prove deadness. Do not commit stale traces,
enable uploads, or start paid AI review merely to clear a static gate.

[configuration]: https://docs.skylos.dev/configuration
[dead-code]: https://docs.skylos.dev/dead-code-detection
[penalties]: https://docs.skylos.dev/guides/penalty-system
[cli]: https://docs.skylos.dev/cli-reference
[matcher]: https://github.com/duriantaco/skylos/blob/de23f0c52a21c724fdbdcdaa340fc573676e9f6a/skylos/deadcode/config_entrypoints.py
[scripts]: https://github.com/duriantaco/skylos/blob/de23f0c52a21c724fdbdcdaa340fc573676e9f6a/skylos/analysis/pyproject_entrypoints.py
[liveness]: https://github.com/duriantaco/skylos/blob/de23f0c52a21c724fdbdcdaa340fc573676e9f6a/skylos/deadcode/liveness.py
[evidence]: https://github.com/duriantaco/skylos/blob/de23f0c52a21c724fdbdcdaa340fc573676e9f6a/skylos/deadcode/evidence.py
