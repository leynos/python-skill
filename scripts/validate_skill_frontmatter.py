"""Validate all shipped Agent Skills frontmatter with strict YAML tooling."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import NoReturn

import yaml

SKILLS_REF = "skills-ref@0.1.5"
YAMLLINT_CONFIG = "{extends: default, rules: {line-length: disable}}"
REQUIRED_FIELDS = ("name", "description")


class FrontmatterValidationError(ValueError):
    """Raised when one shipped skill has invalid frontmatter."""


def _fail(path: Path, message: str) -> NoReturn:
    raise FrontmatterValidationError(f"{path}: {message}")


def _frontmatter(path: Path) -> str:
    """Return the YAML document delimited by the first two marker lines."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        _fail(path, "missing opening frontmatter delimiter")
    for index, line in enumerate(lines[1:], start=1):
        if line.rstrip("\r\n") == "---":
            return "".join(lines[1:index])
    _fail(path, "missing closing frontmatter delimiter")


def _metadata(path: Path) -> dict[str, object]:
    """Parse and validate the YAML metadata required by strict loaders."""
    try:
        parsed = yaml.safe_load(_frontmatter(path))
    except yaml.YAMLError as error:
        _fail(path, f"invalid YAML frontmatter: {error}")
    if not isinstance(parsed, dict):
        _fail(path, "frontmatter must be a mapping")
    for field in REQUIRED_FIELDS:
        value = parsed.get(field)
        if not isinstance(value, str) or not value.strip():
            _fail(path, f"required {field!r} must be a non-empty string")
    return parsed


def _skill_files(root: Path) -> list[Path]:
    """Return the shipped skill manifests in deterministic order."""
    return sorted((root / "skills").rglob("SKILL.md"))


def _lint_frontmatter(path: Path, frontmatter: str) -> None:
    """Run yamllint against YAML only, never the Markdown instruction body."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", encoding="utf-8", delete=False
    ) as temporary:
        temporary.write(f"---\n{frontmatter}")
        temporary_path = Path(temporary.name)
    try:
        subprocess.run(
            ("yamllint", "--strict", "-d", YAMLLINT_CONFIG, temporary_path),
            check=True,
        )
    finally:
        temporary_path.unlink(missing_ok=True)


def _copy_for_reference_validation(
    source: Path, destination: Path, metadata: dict[str, object]
) -> None:
    """Copy one skill while removing the non-standard, supported ``globs`` key.

    The original file has already passed strict YAML parsing.  The reference
    validator currently permits only specification fields, while consumers of
    this catalogue use ``globs`` for skill discovery.
    """
    shutil.copytree(source.parent, destination)
    body = source.read_text(encoding="utf-8").split("\n---\n", maxsplit=1)[1]
    reference_metadata = {key: value for key, value in metadata.items() if key != "globs"}
    frontmatter = yaml.safe_dump(
        reference_metadata, allow_unicode=True, sort_keys=False, default_flow_style=False
    )
    (destination / "SKILL.md").write_text(
        f"---\n{frontmatter}---\n{body}", encoding="utf-8"
    )


def validate(root: Path) -> None:
    """Validate YAML, lint it, then validate every manifest with ``skills-ref``."""
    skill_files = _skill_files(root)
    if not skill_files:
        _fail(root / "skills", "no shipped SKILL.md files found")

    parsed = [(path, _frontmatter(path), _metadata(path)) for path in skill_files]
    for path, frontmatter, _ in parsed:
        _lint_frontmatter(path, frontmatter)

    with tempfile.TemporaryDirectory(prefix="python-skill-reference-") as directory:
        reference_root = Path(directory)
        for source, _, metadata in parsed:
            destination = reference_root / source.parent.relative_to(root / "skills")
            _copy_for_reference_validation(source, destination, metadata)
            subprocess.run(
                ("npx", "--yes", SKILLS_REF, "validate", destination), check=True
            )


if __name__ == "__main__":
    validate(Path(__file__).resolve().parents[1])
