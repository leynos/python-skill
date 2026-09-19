---
name: skylos
description: Use for Skylos dead-code management in Python, including SKY-U001 triage, safe removal, implicit runtime callers, Protocol and callback false positives, precise entrypoint configuration, and merge or rename drift in CI gates.
metadata:
  globs: "**/*.py, **/*.pyi, **/pyproject.toml, **/Makefile"
---

# Skylos Dead-Code Management

Use this for an existing Skylos gate or a deliberate dead-code cleanup.
Use `python-quality-tools` to choose between scanners and profilers;
use `python-types-and-apis` or `python-concurrency` only when a genuine
contract or scheduling question remains.

## Working stance

- A finding is a candidate, not proof that deletion preserves behaviour.
  A passing scan is not proof that every file or runtime path was checked.
- Preserve the repository's pinned version, scan scope, confidence,
  exclusions, and verification settings. Do not make the gate green by
  changing its policy.
- Delete genuinely dead code. Preserve live contracts and represent
  demonstrated analysis gaps with the narrowest repository-approved
  configuration. Do not manufacture callers, exports, or inheritance.
- Read the relevant upstream documentation early. When behaviour differs,
  inspect the installed version and run one discriminating scratch probe
  instead of repeatedly guessing how the analyser ought to work.
- Keep scans local. Do not enable cloud upload, LLM remediation, tracing,
  or automatic source edits as a side effect of triage.

## Start with the actual gate

Read `AGENTS.md`, the Makefile or task runner, `pyproject.toml`, the CI
workflow, and existing configuration-contract tests. Record the commit,
working-tree changes, Python and Skylos versions, exact command, working
directory, scan roots, and active config.

Run the repository's failing target once with a fresh log and preserved
exit status. Then iterate on its Skylos subcommand, preserving every
policy option. A bare `skylos .` or a different `uvx` version is not a
reproduction of a pinned CI invocation. Keep `--no-grep-verify` when the
gate uses it; enabling a rescue mechanism changes the experiment.

Distinguish a completed scan with findings from a parser, environment,
configuration, or invocation failure. Inspect the full first failing
stage: later lint stages may never have run.

## Triage by evidence

For each reported definition, record its exact qualified name, file,
kind, confidence, classification, and available call/evidence fields.
Inspect structured output rather than inferring identity from the short
name printed in a table. Confirm the JSON schema before querying it.

Classify the candidate:

- **Genuinely dead:** no required public, packaging, registration, native,
  or runtime contract remains. Remove it in a small reviewable change;
  preserve side effects and callers' signatures where required.
- **Live but implicit:** identify the real dispatch or registration path
  and an executable test that reaches it. A test calling a helper directly
  does not establish that the production path reaches it.
- **Configuration drift:** a rename, extraction, or merge left old
  `full_name`, path, reason, or expected-symbol entries behind. Repair the
  code-to-config contract, not the implementation to fit an obsolete name.
- **Unknown:** retain the code, name the missing evidence, and run a bounded
  experiment or report a blocker. Do not quietly suppress uncertainty.

A `called_by` edge can connect two unreachable definitions. Conversely,
Protocol dispatch, callbacks forwarded through another constructor,
`threading.Thread(target=...)`, `functools.partial`, and native consumers
can create real callers that a particular scan does not establish.
Neither a text match nor an empty runtime trace settles the question.

## The entrypoint trap

Do not confuse these two mechanisms:

- `[[tool.skylos.dead_code.entrypoints]]` matches definitions for a
  reporting exemption. In the motivating 4.33.2 case, exempting `submit`
  did not rescue its four private callees.
- Packaged script entry points such as `[project.scripts]` feed a
  separate mechanism. They describe real installed commands, not a
  convenient place to hide private methods from a scanner.

The pinned source and the distinction are documented in
[configuration-and-evidence.md](references/configuration-and-evidence.md).
Do not generalize the 4.33.2 observation to an untested version. Equally,
do not assume a class exemption or a documented Protocol hard skip makes
all helpers reachable. Read method, class, and parameter findings
separately; changing `typ.Protocol` to `Protocol` is not a justified fix
without a controlled comparison.

## Choose the smallest honest change

First fix actual dead code, broken wiring, or stale names. When remaining
findings demonstrably describe live code, use exact `full_name` entries
with the correct `type`, a narrow path where appropriate, and a reason
that names the caller and the analyser limitation.

Several proven-live methods may share one rule with an explicit list.
Do not replace that finite list with a parent-only selector, a wildcard,
a whole-file exclusion, or a changed confidence threshold just to save lines.
A parent-only method rule can exempt future dead methods too. A finite
`name` list constrained by a precise `parent` is a different, narrower
choice; verify its matches against the pinned version.

An exemption is not a reachability repair. Do not inline cohesive
helpers, add unused `__all__` entries, convert structural Protocols to
nominal inheritance, or introduce dummy calls solely to appease Skylos.
If repository instructions prohibit new exemptions, keep that boundary:
report the demonstrated tool limitation and required policy decision.

## Close the configuration contract

Update the exception and its evidence together:

1. Replace stale names and paths rather than retaining both generations.
   Check reason strings, whitelist reports, docs, and CI references too.
2. Update the independently maintained expected-symbol set and assertions
   for kinds, selectors, and meaningful reasons. Do not generate the
   expected set from the configuration under test or weaken equality to
   permit arbitrary additions.
3. Keep a regression test through the real runtime seam. For workers or
   native paths, assert that the intended callback/backend actually ran;
   a skipped test or fallback-only success is not evidence for the claim.
4. In a scratch fixture, keep a genuinely unused sibling reportable after
   the exception. This catches accidental suppression of the whole class.

Use the project's development environment for contract tests: its
`conftest.py` may require dependencies absent from the isolated Skylos
tool environment. See
[triage-and-regression.md](references/triage-and-regression.md) for the
case study, controlled probe, and contract-test pattern.

## Bound the investigation and finish

Use one baseline, one hypothesis, and one changed variable per probe.
Write the expected result before running it. If it agrees with the pinned
source, record the decision and implement it. Reopen it only when new
evidence contradicts it; do not cycle through the same root-versus-filter
question or broaden the production refactor while deciding.

Run the targeted scan and contract/runtime tests first. Then run the
repository's complete gates sequentially on a stable tree. Coordinate
with an existing gate runner rather than starting another or editing its
inputs mid-run. A targeted Skylos pass does not validate later lint stages
that the earlier failure prevented from running.

Report the revision and commands tested, deleted definitions, justified
exceptions, remaining uncertainty, and any unrun or skipped checks.
Keep configuration changes, their contract tests, and caller evidence
in the same reviewable change.
