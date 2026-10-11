"""Contract: every uv call in the Makefile goes through the vendored helper.

The helper (``scripts/uv_gate.py``) is copied byte for byte from
leynos/shared-actions and audited by concordat's ``uv-gate-baseline`` rule.
These checks keep this repository's wiring to it from drifting between audits.
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
EXPECTED_PREPARE = "$(UV_GATE) prepare --group dev"
EXPECTED_DEFAULT_GOAL = "check"
# Commands the spelling baseline requires to stay direct (empty when none).
DIRECT_EXEMPTIONS: tuple[str, ...] = ()
GATE_LINE = re.compile(r"^UV_GATE \?= python3 scripts/uv_gate\.py$", re.MULTILINE)
CACHE_OVERRIDE = re.compile(r"UV_(?:CACHE|TOOL)_DIR\s*(?:[:?+]{0,2}=|:)")
UV_WORD = r"(?:(?:\S*/)?uvx?|\$[({]UV[)}])"
# A command that starts with uv (after env and assignments), or a uv subcommand
# anywhere on the line.
BARE_UV = re.compile(
    rf"^[@+\-\s]*(?:env\s+(?:-\S+\s+)*)?(?:\w+=\S+\s+)*{UV_WORD}(?=\s|$)"
    rf"|(?<![A-Za-z0-9_.$-]){UV_WORD}[ \t]+(?:--?\S+[ \t]+)*"
    r"(?:run|sync|tool|pip|lock|build|venv|export|add|remove|python|cache|init)\b"
)
SEGMENT_SPLIT = re.compile(r"&&|\|\||[;|]")
COMMENT = re.compile(r"(?<!\\)\s#.*$")
RULE = re.compile(r"^(?P<names>[^\s#:=][^:=]*?)\s*:(?![:=])(?P<prerequisites>[^#]*)")
RUNS_PROJECT = "$(UV_GATE) run"
HELPER_PREPARE = "$(UV_GATE) prepare"
GATED_CALL = re.compile(r"\$\(UV_GATE\) (?:run|tool)\b")
Rules = dict[str, tuple[set[str], str]]


def bare_uv_calls(makefile: str) -> list[str]:
    """Return the command segments that call uv without the helper."""
    offenders = []
    for line in makefile.replace("\\\n", " ").splitlines():
        if line.lstrip().startswith("#"):
            continue
        for segment in SEGMENT_SPLIT.split(COMMENT.sub("", line)):
            if not BARE_UV.search(segment) or segment.lstrip().startswith("UV "):
                continue
            if any(exempt in segment for exempt in DIRECT_EXEMPTIONS):
                continue
            offenders.append(segment.strip())
    return offenders


def parse_rules(makefile: str) -> Rules:
    """Map each rule name to its prerequisites and its recipe text."""
    rules: Rules = {}
    name = None
    for line in makefile.replace("\\\n", " ").splitlines():
        if line.startswith("\t") and name is not None:
            prerequisites, recipe = rules[name]
            rules[name] = (prerequisites, f"{recipe}\n{line.strip()}")
            continue
        rule = RULE.match(line)
        name = None
        if rule:
            name = rule["names"].strip()
            rules[name] = (set(rule["prerequisites"].split()), "")
    return rules


def project_runners(makefile: str) -> list[str]:
    """Return the variable and macro references that run the project."""
    assignments = re.findall(r"^(\w+)\s*[:?]?=\s*(.*)$", makefile, re.MULTILINE)
    macros = re.findall(
        r"^define (\w+)\n(.*?)^endef", makefile, re.DOTALL | re.MULTILINE
    )
    return [
        RUNS_PROJECT,
        *(f"$({n})" for n, value in assignments if value.startswith(RUNS_PROJECT)),
        *(f"$(call {n}" for n, body in macros if RUNS_PROJECT in body),
    ]


def reaches_prepare(
    name: str, rules: Rules, seen: frozenset[str] = frozenset()
) -> bool:
    """Say whether building ``name`` runs the helper's prepare, via its own recipe."""
    if name in seen or name not in rules:
        return False
    prerequisites, recipe = rules[name]
    return EXPECTED_PREPARE in recipe or any(
        reaches_prepare(item, rules, seen | {name}) for item in prerequisites
    )


def unprepared_gates(makefile: str) -> list[str]:
    """Return the targets that run the project without a prepared environment."""
    rules = parse_rules(makefile)
    runners = project_runners(makefile)
    return [
        name
        for name, (prerequisites, recipe) in rules.items()
        if name != "prepare"
        and any(runner in recipe for runner in runners)
        and not any(
            item == "prepare" or reaches_prepare(item, rules) for item in prerequisites
        )
    ]


def make_database(*arguments: str) -> str:
    """Return GNU make's printed database for the Makefile, without running a recipe."""
    make = shutil.which("make")
    if make is None:
        pytest.skip("make is not installed")
    done = subprocess.run(
        [make, "-qp", "-f", "Makefile", *arguments, "--"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    return done.stdout


def test_the_vendored_helper_is_the_reviewed_release() -> None:
    """The helper's bytes are the reviewed release, unedited."""
    digest = hashlib.sha256((ROOT / "scripts/uv_gate.py").read_bytes()).hexdigest()

    assert digest == HELPER_DIGEST, f"scripts/uv_gate.py has digest {digest}"


def test_the_gate_variable_is_the_helper() -> None:
    """UV_GATE holds exactly the helper command."""
    assert GATE_LINE.search(MAKEFILE), "UV_GATE must default to the helper"


def test_no_uv_cache_override_remains() -> None:
    """Neither the Makefile nor the workflows set a uv cache or tool directory."""
    workflows = [p.read_text(encoding="utf-8") for p in ROOT.glob(".github/**/*.y*ml")]

    offenders = [t[:40] for t in [MAKEFILE, *workflows] if CACHE_OVERRIDE.search(t)]
    assert not offenders, f"a uv cache location is overridden: {offenders}"


def test_recipes_reach_uv_only_through_the_helper() -> None:
    """No bare uv command remains, bar the one the spelling baseline keeps direct."""
    offenders = bare_uv_calls(MAKEFILE)

    assert not offenders, f"bare uv calls remain: {offenders}"


@pytest.mark.parametrize(
    "recipe",
    [
        "\tuv run pytest",
        "\t@uv sync --group dev",
        "\t${UV} run pytest",
        "\t$(UV) --offline run pytest",
        "\t/usr/bin/uv run pytest",
        "\tenv uv --offline run pytest",
        "\tenv uvx ruff check",
        "\tFOO=1 uvx ruff check",
        "\ttrue && uv lock",
        "\tuv sync; echo typos-config-builder.git@v1  # typos-config-builder.git@v1",
    ],
)
def test_the_detector_rejects_bare_uv_forms(recipe: str) -> None:
    """The scan catches the spellings a careless edit could use."""
    assert bare_uv_calls(f"check:\n{recipe}\n")


@pytest.mark.parametrize(
    "recipe",
    [
        "\t$(UV_GATE) run -- pytest",
        "\t$(UV_GATE) tool --from ruff@0.9.0 -- ruff check",
        "UV ?= uv",
        "# uv run is described here",
        "\t@echo uv is required",
    ],
)
def test_the_detector_accepts_gated_forms(recipe: str) -> None:
    """The scan leaves the helper's own spellings alone."""
    assert not bare_uv_calls(f"check:\n{recipe}\n")


def test_every_helper_run_and_tool_call_has_a_separator() -> None:
    """`run` and `tool` take the command after `--`, so it cannot be read as a flag."""
    offenders = [
        line.strip()
        for line in MAKEFILE.replace("\\\n", " ").splitlines()
        if GATED_CALL.search(line) and " -- " not in line
    ]

    assert not offenders, f"helper calls without `--`: {offenders}"


def test_prepare_installs_the_locked_environment() -> None:
    """`make prepare` is phony and itself runs, or builds, the helper's prepare."""
    rules = parse_rules(MAKEFILE)

    assert "prepare" in rules, "the Makefile must define a prepare target"
    assert re.search(r"^\.PHONY:.*\bprepare\b", MAKEFILE, re.MULTILINE), (
        "prepare must be phony"
    )
    assert reaches_prepare("prepare", rules), (
        f"prepare must reach `{EXPECTED_PREPARE}` through its recipe or prerequisites"
    )


def test_every_gate_that_runs_the_project_depends_on_prepare() -> None:
    """The helper's run is offline, so the environment must exist beforehand."""
    offenders = unprepared_gates(MAKEFILE)

    assert not offenders, f"these targets run the project unprepared: {offenders}"


def test_an_empty_prepare_target_is_detected() -> None:
    """Moving the preparation out of `prepare` fails the contract."""
    makefile = "\n".join(
        [
            "prepare:",
            "test: prepare",
            "\t$(UV_GATE) run -- pytest",
            "build:",
            f"\t{EXPECTED_PREPARE}",
        ]
    )
    rules = parse_rules(makefile)

    assert not reaches_prepare("prepare", rules)


def test_the_default_goal_is_unchanged() -> None:
    """Adding `prepare` must not turn it into what a bare `make` runs."""
    database = make_database()

    assert f".DEFAULT_GOAL := {EXPECTED_DEFAULT_GOAL}" in database, (
        f"a bare make must still run {EXPECTED_DEFAULT_GOAL}"
    )


def test_a_selected_uv_leads_the_path() -> None:
    """`make UV=/dir/uv` puts that uv's directory first on PATH for the helper."""
    database = make_database("UV=/opt/selected-uv/uv")

    assert re.search(r"^PATH := /opt/selected-uv:", database, re.MULTILINE), (
        "the Makefile must export the selected uv's directory on PATH"
    )
