"""Contract tests binding the router's routing table to the skills on disk.

The router is the catalogue's entry point: if it names a skill that does not
exist, the route dead-ends, and if a skill exists that no route reaches, it is
unreachable. Neither failure is visible from reading either file alone.

Only positive route declarations count as references — the destination of a
"Route by question" entry, or a cell in the routing matrix's skill columns.
Prose elsewhere mentions skills without routing to them, so counting it would
let a skill look reachable when nothing actually routes there.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

import pytest

FRONTMATTER_NAME = re.compile(r"^name:\s*(?P<name>\S+)\s*$", re.MULTILINE)
BACKTICKED = re.compile(r"`([^`\n]+)`")

# The router never routes to itself; that is expected, not an unrouted skill.
SELF = "python-router"


def _skill_dirs(repo_root: Path) -> list[Path]:
    return sorted(p for p in (repo_root / "skills").iterdir() if p.is_dir())


def _section(text: str, heading: str) -> str:
    """Return the body of a top-level section, excluding later sections."""
    body = text.split(f"\n## {heading}\n", 1)
    if len(body) != 2:
        msg = f"section '## {heading}' not found"
        raise AssertionError(msg)
    return body[1].split("\n## ", 1)[0]


def _bullets(section: str) -> Iterable[str]:
    """Yield each top-level list item, with continuation lines folded in."""
    current: list[str] = []
    for line in section.splitlines():
        if line.startswith("- "):
            if current:
                yield " ".join(current)
            current = [line[2:].strip()]
        elif current and line.startswith("  "):
            current.append(line.strip())
        elif current:
            yield " ".join(current)
            current = []
    if current:
        yield " ".join(current)


def _route_destinations(router_skill: str) -> set[str]:
    """Extract the skills each "Route by question" entry routes to.

    Every entry states its trigger, then a colon, then the destination. One
    entry names a primary skill and its deep dives after a semicolon, so all
    backticked tokens following the final colon count, not just the last.
    """
    names: set[str] = set()
    for bullet in _bullets(_section(router_skill, "Route by question")):
        _, _, destination = bullet.rpartition(":")
        names.update(BACKTICKED.findall(destination))
    return names


def _matrix_destinations(matrix: str) -> set[str]:
    """Extract skill names from the routing matrix's two skill columns."""
    names: set[str] = set()
    for line in matrix.splitlines():
        row = line.strip()
        if not row.startswith("|") or set(row) <= set("| -:"):
            continue
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        for cell in cells[1:3]:  # primary skill, common pair
            names.update(BACKTICKED.findall(cell))
    return names


@pytest.fixture(scope="session")
def skill_names(repo_root: Path) -> frozenset[str]:
    """Return every skill directory name under ``skills/``."""
    return frozenset(p.name for p in _skill_dirs(repo_root))


@pytest.fixture(scope="session")
def routed_names(repo_root: Path) -> frozenset[str]:
    """Return every skill the router positively routes to."""
    router = repo_root / "skills" / SELF
    skill_md = (router / "SKILL.md").read_text(encoding="utf-8")
    matrix = (router / "references" / "routing-matrix.md").read_text(encoding="utf-8")
    return frozenset(_route_destinations(skill_md) | _matrix_destinations(matrix))


def test_every_skill_directory_has_a_skill_file(repo_root: Path) -> None:
    """A directory under skills/ without a SKILL.md is not a loadable skill."""
    missing = [p.name for p in _skill_dirs(repo_root) if not (p / "SKILL.md").is_file()]

    assert not missing, f"skill directories without SKILL.md: {missing}"


def test_frontmatter_name_matches_directory(repo_root: Path) -> None:
    """The frontmatter name is how a skill is invoked; it must match its path."""
    mismatched: dict[str, str | None] = {}
    for path in _skill_dirs(repo_root):
        match = FRONTMATTER_NAME.search((path / "SKILL.md").read_text(encoding="utf-8"))
        declared = match.group("name") if match else None
        if declared != path.name:
            mismatched[path.name] = declared

    assert not mismatched, f"frontmatter name != directory name: {mismatched}"


def test_routes_resolve_to_real_skills(
    routed_names: frozenset[str], skill_names: frozenset[str]
) -> None:
    """Every route destination must exist on disk."""
    broken = sorted(routed_names - skill_names)

    assert not broken, f"routes point at non-existent skills: {broken}"


def test_every_skill_is_routed_to(
    routed_names: frozenset[str], skill_names: frozenset[str]
) -> None:
    """A skill no route reaches cannot be selected by the router."""
    unrouted = sorted(skill_names - routed_names - {SELF})

    assert not unrouted, f"skills nothing routes to: {unrouted}"


def test_deep_dive_skills_are_routed_to(routed_names: frozenset[str]) -> None:
    """Guard the parser itself.

    The deep dives are the only routes that trail a semicolon rather than a
    colon. If the parser regresses to taking one token per entry they vanish
    silently, and every other assertion here still passes.
    """
    assert {"hypothesis", "crosshair", "mutmut"} <= routed_names


def test_catalogue_status_lists_every_skill(
    repo_root: Path, skill_names: frozenset[str]
) -> None:
    """The catalogue status doc is the inventory; it must not drift."""
    status = (repo_root / "docs" / "skill-catalogue-status.md").read_text(
        encoding="utf-8"
    )
    listed = {
        entry[0]
        for bullet in _bullets(_section(status, "Active skills"))
        if (entry := BACKTICKED.findall(bullet))
    }
    missing = sorted(skill_names - listed)

    assert not missing, f"skills absent from skill-catalogue-status.md: {missing}"


def test_reference_links_in_skill_files_resolve(repo_root: Path) -> None:
    """Relative Markdown links between a skill and its references must exist."""
    link = re.compile(r"\]\((?P<target>references/[^)#]+)\)")
    broken: list[str] = []
    for path in _skill_dirs(repo_root):
        skill_file = path / "SKILL.md"
        targets: Iterable[str] = (
            m.group("target")
            for m in link.finditer(skill_file.read_text(encoding="utf-8"))
        )
        broken.extend(
            f"{path.name}/SKILL.md -> {target}"
            for target in targets
            if not (path / target).is_file()
        )

    assert not broken, f"broken reference links: {broken}"
