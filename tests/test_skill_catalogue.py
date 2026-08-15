"""Contract tests binding the router's routing table to the skills on disk.

The router is the catalogue's entry point: if it names a skill that does not
exist, the route dead-ends, and if a skill exists that the router never names,
it is unreachable. Neither failure is visible from reading either file alone.
"""

from __future__ import annotations

import re
import typing as t
from pathlib import Path

import pytest

FRONTMATTER_NAME = re.compile(r"^name:\s*(?P<name>\S+)\s*$", re.MULTILINE)
BACKTICKED = re.compile(r"`([^`\n]+)`")

# Skill names follow one of two shapes in this catalogue. Restricting the
# broken-reference scan to these keeps ordinary prose in backticks — tool
# names, rule codes, Python constructs — from being mistaken for routes.
SKILL_NAME_SHAPES = (
    re.compile(r"^python-[a-z0-9]+(?:-[a-z0-9]+)*$"),
    re.compile(r"^ruff-\d+$"),
)

# The router never routes to itself; that is expected, not an unrouted skill.
SELF = "python-router"


def _skill_dirs(repo_root: Path) -> list[Path]:
    return sorted(p for p in (repo_root / "skills").iterdir() if p.is_dir())


@pytest.fixture(scope="session")
def skill_names(repo_root: Path) -> frozenset[str]:
    """Return every skill directory name under ``skills/``."""
    return frozenset(p.name for p in _skill_dirs(repo_root))


@pytest.fixture(scope="session")
def router_text(repo_root: Path) -> str:
    """Return the router's SKILL.md and routing matrix concatenated."""
    router = repo_root / "skills" / SELF
    sources = [router / "SKILL.md", router / "references" / "routing-matrix.md"]
    return "\n".join(path.read_text(encoding="utf-8") for path in sources)


def _referenced_names(text: str) -> set[str]:
    """Return backticked tokens that are shaped like catalogue skill names."""
    return {
        token
        for token in BACKTICKED.findall(text)
        if any(shape.match(token) for shape in SKILL_NAME_SHAPES)
    }


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


def test_router_references_resolve_to_real_skills(
    router_text: str, skill_names: frozenset[str]
) -> None:
    """Every skill-shaped name the router cites must exist on disk."""
    broken = sorted(_referenced_names(router_text) - skill_names)

    assert not broken, f"router routes to non-existent skills: {broken}"


def test_every_skill_is_reachable_from_the_router(
    router_text: str, skill_names: frozenset[str]
) -> None:
    """A skill the router never names cannot be routed to."""
    referenced = set(BACKTICKED.findall(router_text))
    unrouted = sorted(skill_names - referenced - {SELF})

    assert not unrouted, f"skills the router never references: {unrouted}"


def test_catalogue_status_lists_every_skill(
    repo_root: Path, skill_names: frozenset[str]
) -> None:
    """The catalogue status doc is the inventory; it must not drift."""
    status = (repo_root / "docs" / "skill-catalogue-status.md").read_text(
        encoding="utf-8"
    )
    listed = set(BACKTICKED.findall(status))
    missing = sorted(skill_names - listed)

    assert not missing, f"skills absent from skill-catalogue-status.md: {missing}"


def test_reference_links_in_skill_files_resolve(repo_root: Path) -> None:
    """Relative Markdown links between a skill and its references must exist."""
    link = re.compile(r"\]\((?P<target>references/[^)#]+)\)")
    broken: list[str] = []
    for path in _skill_dirs(repo_root):
        skill_file = path / "SKILL.md"
        targets: t.Iterable[str] = (
            m.group("target")
            for m in link.finditer(skill_file.read_text(encoding="utf-8"))
        )
        broken.extend(
            f"{path.name}/SKILL.md -> {target}"
            for target in targets
            if not (path / target).is_file()
        )

    assert not broken, f"broken reference links: {broken}"
