"""Contract: every uv call in the Makefile goes through the vendored helper.

The helper (``scripts/uv_gate.py``) is copied byte for byte from
leynos/shared-actions and audited by concordat's ``uv-gate-baseline`` rule.
These checks keep this repository's wiring to it from drifting between audits.
They ask GNU make what it would run (``make -nB`` with a marker standing in for
the helper) instead of pattern-matching recipe text.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = (ROOT / "Makefile").read_text(encoding="utf-8")
# The reviewed helper release (uv_gate 0.2.1). Update the digest when moving to a
# newer release, never to accept an edited copy.
HELPER_DIGEST = "fe7671d8663ec89ce1076ebb857847802e46c8d6607ab1e012daa443e335e66e"
EXPECTED_PREPARE = "prepare --group dev"
EXPECTED_DEFAULT_GOAL = "check"
# The targets that run the project through the helper.
GATE_TARGETS: tuple[str, ...] = (
    "lint",
    "skill-frontmatter-lint",
    "skill-manifest-validate",
    "skill-manifest-check",
    "typecheck",
    "test",
    "check",
)
# Every Makefile line that mentions uv without going through the helper. A new
# mention fails the test until it is reviewed and added here.
ALLOWED_UV_LINES: tuple[str, ...] = (
    "UV ?= uv",
    "export PATH := $(if $(findstring /,$(UV)),$(patsubst %/,%,$(dir $(UV))):)$(PATH)",
)
MARKER = "UV-GATE-MARKER"
UV_WORD = re.compile(r"(?<![A-Za-z0-9_-])uvx?(?![A-Za-z0-9_-])|\$[({]UV[)}]")
COMMENT = re.compile(r"(?<!\\)(?:^|\s)#.*$")
SEGMENT_SPLIT = re.compile(r"&&|\|\||[;|]")
LEADING_WORDS = {"if", "then", "else", "elif", "do", "!", "time", "exec", "env"}
GATE_ASSIGNMENT = re.compile(
    r"^\s*(?:(?:override|export)\s+)*UV_GATE\s*[:?+!]*=", re.MULTILINE
)
CACHE_OVERRIDE = re.compile(r"UV_(?:CACHE|TOOL)_DIR\s*(?:[:?+]{0,2}=|:)")


def uv_mentions(makefile: str) -> list[str]:
    """Return the normalised Makefile lines that mention uv, comments removed."""
    lines = (
        COMMENT.sub("", line) for line in makefile.replace("\\\n", " ").splitlines()
    )
    return [" ".join(line.split()) for line in lines if UV_WORD.search(line)]


def helper_calls(printed: str) -> list[str]:
    """Return the commands in make's printed recipes that run the marker."""
    calls = []
    for line in printed.splitlines():
        for segment in SEGMENT_SPLIT.split(COMMENT.sub("", line)):
            words = segment.replace("(", " ").replace("{", " ").split()
            while words and (
                words[0].lstrip("@+-") in LEADING_WORDS
                or re.fullmatch(r"\w+=\S*", words[0])
                or not words[0].lstrip("@+-")
            ):
                words = words[1:]
            if words and words[0].lstrip("@+-") == MARKER:
                calls.append(" ".join(words).lstrip("@+-"))
    return calls


def make(*arguments: str) -> subprocess.CompletedProcess[str]:
    """Run GNU make in the repository root and capture its output."""
    executable = shutil.which("make")
    if executable is None:
        pytest.skip("make is not installed")
    return subprocess.run(
        [executable, "--no-print-directory", "-f", "Makefile", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def test_the_vendored_helper_is_the_reviewed_release() -> None:
    """The helper's bytes are the reviewed release, unedited."""
    digest = hashlib.sha256((ROOT / "scripts/uv_gate.py").read_bytes()).hexdigest()

    assert digest == HELPER_DIGEST, f"scripts/uv_gate.py has digest {digest}"


def test_the_gate_variable_is_assigned_once_to_the_helper() -> None:
    """UV_GATE has one assignment, and make's effective value is the helper."""
    assignments = GATE_ASSIGNMENT.findall(MAKEFILE)
    database = make("-qp", "--").stdout

    assert len(assignments) == 1, f"UV_GATE is assigned {len(assignments)} times"
    assert re.search(
        r"^UV_GATE = python3 scripts/uv_gate\.py$", database, re.MULTILINE
    ), "make's effective UV_GATE must be the helper command"


def test_no_uv_cache_override_remains() -> None:
    """Neither the Makefile nor the workflows set a uv cache or tool directory."""
    workflows = [p.read_text(encoding="utf-8") for p in ROOT.glob(".github/**/*.y*ml")]

    offenders = [t[:40] for t in [MAKEFILE, *workflows] if CACHE_OVERRIDE.search(t)]
    assert not offenders, f"a uv cache location is overridden: {offenders}"


def test_every_remaining_mention_of_uv_is_reviewed() -> None:
    """A uv mention that is not routed through the helper must be on the list."""
    unreviewed = [
        line for line in uv_mentions(MAKEFILE) if line not in ALLOWED_UV_LINES
    ]

    assert not unreviewed, f"unreviewed uv mentions (use the helper): {unreviewed}"


@pytest.mark.parametrize(
    "line",
    [
        "\tuv run pytest",
        "RUNNER = uvx ruff check",
        "RUNNER = uv --directory . run pytest",
        "\t${UV} run pytest",
        "\t$(UV) --offline run pytest",
        "\t'/usr/bin/uv' run pytest",
        "\tenv uvx ruff check",
        "\ttrue && uv lock",
        "\tuv sync  # $(UV_GATE) run --",
        "ifeq ($(shell command -v uv),)",
    ],
)
def test_the_scan_finds_a_mention(line: str) -> None:
    """Every spelling of a direct uv call is found."""
    assert uv_mentions(f"check:\n{line}\n")


@pytest.mark.parametrize(
    "line",
    [
        "\t$(UV_GATE) run -- pytest",
        "\t$(UV_GATE) tool --from ruff@0.9.0 -- ruff check",
        "# uv run is described here",
        "\t@echo done  # uv is not needed",
    ],
)
def test_the_scan_ignores_gated_calls_and_comments(line: str) -> None:
    """The helper's own spellings and comments are not mentions."""
    assert not uv_mentions(f"check:\n{line}\n")


@pytest.mark.parametrize(
    ("printed", "expected"),
    [
        (f"{MARKER} prepare --group dev", [f"{MARKER} prepare --group dev"]),
        (f"@{MARKER} run -- pytest -q", [f"{MARKER} run -- pytest -q"]),
        (f"echo {MARKER} prepare --group dev", []),
        (f"# {MARKER} run -- pytest", []),
        (f"true && {MARKER} run -- pytest", [f"{MARKER} run -- pytest"]),
        (f"echo hi; {MARKER} tool --from x@1 -- x", [f"{MARKER} tool --from x@1 -- x"]),
        (f"if ! {MARKER} run -- x; then echo no; fi", [f"{MARKER} run -- x"]),
    ],
)
def test_the_printed_recipe_parser_finds_only_executed_helper_calls(
    printed: str, expected: list[str]
) -> None:
    """Only a helper call in command position counts, not echoed or commented text."""
    assert helper_calls(printed) == expected


def test_prepare_is_phony_and_runs_the_helper_prepare() -> None:
    """`make prepare` is phony and executes exactly the expected helper command."""
    printed = make("-nB", "prepare", f"UV_GATE={MARKER}").stdout

    assert re.search(r"^\.PHONY:.*\bprepare\b", MAKEFILE, re.MULTILINE), (
        "prepare must be phony"
    )
    assert f"{MARKER} {EXPECTED_PREPARE}" in helper_calls(printed), (
        f"make prepare must run `{EXPECTED_PREPARE}` as a command: {printed!r}"
    )


@pytest.mark.parametrize("target", GATE_TARGETS)
def test_a_gate_prepares_before_it_runs_and_separates_every_command(
    target: str,
) -> None:
    """Each gate prepares before its first project run, and `--` ends options."""
    printed = make("-nB", target, f"UV_GATE={MARKER}").stdout
    calls = helper_calls(printed)
    subcommands = [call.split()[1] for call in calls]
    prepare = f"{MARKER} {EXPECTED_PREPARE}"

    assert {"run", "tool"} & set(subcommands), (
        f"make {target} must run its commands through the helper: {printed!r}"
    )
    if "run" in subcommands:
        first_run = subcommands.index("run")
        assert prepare in calls[:first_run], (
            f"make {target} must prepare before it runs the project: {calls}"
        )
    unseparated = [
        c for c in calls if c.split()[1] in {"run", "tool"} and " -- " not in c
    ]
    assert not unseparated, f"helper calls without `--`: {unseparated}"


def test_the_default_goal_is_unchanged() -> None:
    """Adding `prepare` must not change what a bare `make` runs."""
    database = make("-qp", "--").stdout

    assert f".DEFAULT_GOAL := {EXPECTED_DEFAULT_GOAL}" in database, (
        f"a bare make must still run {EXPECTED_DEFAULT_GOAL}"
    )


def test_a_selected_uv_leads_the_exported_path() -> None:
    """`make UV=/dir/uv` hands recipes a PATH that starts with that directory."""
    probe = ".PHONY: __uv_path\n__uv_path:\n\t@printf '%s' \"$$PATH\""
    done = make("UV=/opt/selected-uv/uv", f"--eval={probe}", "__uv_path")

    assert done.stdout.startswith("/opt/selected-uv:"), (
        f"recipes must see the selected uv first on PATH, got {done.stdout!r}"
    )
