"""Contract: every uv call in the Makefile goes through the vendored helper.

The helper (``scripts/uv_gate.py``) is copied byte for byte from
leynos/shared-actions and audited by concordat's ``uv-gate-baseline`` rule.
These checks keep this repository's wiring to it from drifting between audits.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = (ROOT / "Makefile").read_text(encoding="utf-8")
# The reviewed helper release (uv_gate 0.2.1). Update the digest when moving to a
# newer release, never to accept an edited copy.
HELPER_DIGEST = "fe7671d8663ec89ce1076ebb857847802e46c8d6607ab1e012daa443e335e66e"
GATE_LINE = re.compile(r"^UV_GATE \?= python3 scripts/uv_gate\.py$", re.MULTILINE)
CACHE_OVERRIDE = re.compile(r"UV_(?:CACHE|TOOL)_DIR\s*(?:[:?+]{0,2}=|:)")
UV_WORD = r"(?:uvx?|\$\(UV\))"
# A command that starts with uv, or any uv subcommand anywhere on the line.
BARE_UV = re.compile(
    rf"^[@+\-\s]*(?:\w+=\S+\s+)*{UV_WORD}(?=\s|$)"
    rf"|(?<![A-Za-z0-9_./$-]){UV_WORD}[ \t]+"
    r"(?:run|sync|tool|pip|lock|build|venv|export|add|remove|python|cache|init)\b"
)
SEGMENT_SPLIT = re.compile(r"&&|\|\||[;|]")
RULE = re.compile(r"^(?P<names>[^\s#:=][^:=]*?)\s*:(?![:=])(?P<prerequisites>[^#]*)")
RUNS_PROJECT = "$(UV_GATE) run"
HELPER_PREPARE = "$(UV_GATE) prepare"


Rules = dict[str, tuple[set[str], str]]


def _rules() -> Rules:
    """Map each rule name to its prerequisites and its recipe text."""
    rules: Rules = {}
    name = None
    for line in MAKEFILE.replace("\\\n", " ").splitlines():
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


def _project_runners() -> list[str]:
    """Return the variable and macro references that run the project."""
    assignments = re.findall(r"^(\w+)\s*[:?]?=\s*(.*)$", MAKEFILE, re.MULTILINE)
    macros = re.findall(
        r"^define (\w+)\n(.*?)^endef", MAKEFILE, re.DOTALL | re.MULTILINE
    )
    return [
        RUNS_PROJECT,
        *(
            f"$({name})"
            for name, value in assignments
            if value.startswith(RUNS_PROJECT)
        ),
        *(f"$(call {name}" for name, body in macros if RUNS_PROJECT in body),
    ]


def _depends_on_prepare(
    name: str, rules: Rules, seen: frozenset[str] = frozenset()
) -> bool:
    """Say whether building ``name`` first builds ``prepare``."""
    if name == "prepare" or HELPER_PREPARE in rules.get(name, (set(), ""))[1]:
        return True
    if name in seen or name not in rules:
        return False
    return any(
        _depends_on_prepare(item, rules, seen | {name}) for item in rules[name][0]
    )


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
    """No bare uv command remains, bar the release-tagged typos-config-builder."""
    offenders = [
        segment.strip()
        for line in MAKEFILE.replace("\\\n", " ").splitlines()
        if not line.lstrip().startswith("#")
        for segment in SEGMENT_SPLIT.split(line)
        if BARE_UV.search(segment)
        and "typos-config-builder.git@" not in segment
        and not segment.lstrip().startswith("UV ")
    ]

    assert not offenders, f"bare uv calls remain: {offenders}"


def test_prepare_installs_the_locked_environment() -> None:
    """`make prepare` exists and runs the helper's prepare subcommand."""
    rules = _rules()

    assert "prepare" in rules, "the Makefile must define a prepare target"
    assert any(HELPER_PREPARE in recipe for _, recipe in rules.values()), (
        "a recipe must run the helper's prepare subcommand"
    )
    assert _depends_on_prepare("prepare", rules), "prepare must be the entry point"


def test_every_gate_that_runs_the_project_depends_on_prepare() -> None:
    """The helper's run is offline, so the environment must exist beforehand."""
    rules = _rules()
    runners = _project_runners()

    offenders = [
        name
        for name, (prerequisites, recipe) in rules.items()
        if name != "prepare"
        and any(runner in recipe for runner in runners)
        and not any(_depends_on_prepare(item, rules) for item in prerequisites)
    ]

    assert not offenders, f"these targets run the project unprepared: {offenders}"
