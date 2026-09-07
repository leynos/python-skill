"""Regression tests for strict Agent Skills frontmatter loading."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


def _validator(repo_root: Path) -> ModuleType:
    """Load the gate script as a module without requiring it to be packaged."""
    path = repo_root / "scripts" / "validate_skill_frontmatter.py"
    spec = importlib.util.spec_from_file_location("skill_frontmatter_validator", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_shipped_frontmatters_parse_and_provide_required_fields(repo_root: Path) -> None:
    """Every shipped skill must be discoverable by a strict YAML loader."""
    validator = _validator(repo_root)
    skill_files = sorted((repo_root / "skills").glob("*/SKILL.md"))

    assert skill_files, "the catalogue has no shipped SKILL.md files"
    for skill_file in skill_files:
        metadata = validator._metadata(skill_file)
        assert metadata["name"] == skill_file.parent.name
        assert metadata["description"].strip()


def test_unquoted_description_colon_is_rejected_by_the_strict_loader(
    repo_root: Path, tmp_path: Path
) -> None:
    """A colon followed by a space must be quoted or folded in a scalar."""
    validator = _validator(repo_root)
    source = (repo_root / "skills" / "python-testing" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    broken = source.replace(
        'description: "Use for advanced pytest usage: fixture scopes, named examples, finite parametrization, marks, plugins, snapshot and approval tests, async tests, and the boundary between example, property, and verification testing."',
        "description: Use for advanced pytest usage: fixture scopes, named examples, finite parametrization, marks, plugins, snapshot and approval tests, async tests, and the boundary between example, property, and verification testing.",
    )
    path = tmp_path / "SKILL.md"
    path.write_text(broken, encoding="utf-8")

    with pytest.raises(validator.FrontmatterValidationError, match="invalid YAML"):
        validator._metadata(path)


def test_validator_lints_and_reference_validates_every_shipped_skill(
    monkeypatch: pytest.MonkeyPatch, repo_root: Path
) -> None:
    """The lint gate reaches both YAML tools once per shipped manifest."""
    validator = _validator(repo_root)
    calls: list[tuple[object, ...]] = []

    def record(command: tuple[object, ...], *, check: bool) -> None:
        assert check
        calls.append(command)

    monkeypatch.setattr(validator.subprocess, "run", record)
    validator.validate(repo_root)

    skill_count = len(list((repo_root / "skills").rglob("SKILL.md")))
    assert sum(command[0] == "yamllint" for command in calls) == skill_count
    assert sum(command[0] == "npx" for command in calls) == skill_count
