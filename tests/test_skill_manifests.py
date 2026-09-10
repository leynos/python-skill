"""Contract tests for shipped Agent Skills manifests.

Each shipped skill's ``SKILL.md`` opens with YAML frontmatter that a strict
loader reads before the skill is usable, and the manifest's ``name`` is the
identifier discovery resolves. The Makefile targets exercised here are the
ones ``make lint`` depends on, so a manifest that a loader could not use fails
the commit gate rather than reaching an installation untouched.

Unlike the other Makefile tests, these run in the checkout rather than in a
scratch repository: the manifest targets resolve their tools through
``uv run``, which needs the real ``pyproject.toml`` and ``uv.lock``.
"""

from __future__ import annotations

import subprocess
import typing as t
from pathlib import Path

import pytest
import yaml

if t.TYPE_CHECKING:  # pragma: no cover - typing only
    from cmd_mox import CmdMox

REPO_ROOT = Path(__file__).resolve().parents[1]
SHIPPED_MANIFESTS = sorted((REPO_ROOT / "skills").glob("*/SKILL.md"))
MARKDOWN_TOOLS = ("markdownlint", "nixie")

# A manifest that is not valid YAML, and a conformant skill sorted after it. The
# conformant skill must not mask the malformed one in a `for` loop's status.
BROKEN_MANIFEST = "---\nname: [unclosed\n---\n\n# Broken\n"
VALID_MANIFEST = (
    "---\n"
    "name: z-valid\n"
    "description: A conformant trailing fixture.\n"
    "---\n"
    "\n"
    "# Valid\n"
)

# Valid YAML that omits the required `description`, so it passes the frontmatter
# lint and fails schema validation.
INVALID_MANIFEST = "---\nname: b-invalid\n---\n\n# Fixture\n"


def _run_make(target: str, *skill_dirs: Path) -> subprocess.CompletedProcess[str]:
    """Run a Makefile target over shipped skills or given fixture directories.

    Parameters
    ----------
    target : str
        The Makefile target to run, such as ``skill-manifest-check``.
    *skill_dirs : Path
        Fixture skill directories to check instead of the shipped set. When
        none are given, ``SKILL_DIRS`` keeps its default of every shipped
        skill.

    Returns
    -------
    subprocess.CompletedProcess of str
        The completed process, with stdout and stderr decoded as text. The
        exit status is returned rather than raised on, since several tests
        assert that a gate fails.
    """
    arguments = ["make", target]
    if skill_dirs:
        arguments.append(
            "SKILL_DIRS=" + " ".join(f"{directory}/" for directory in skill_dirs)
        )
    return subprocess.run(  # noqa: S603 - fixed argv, no shell
        arguments,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _run_manifest_check(
    skill_dir: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run the manifest contract over the shipped skills or one fixture."""
    return _run_make("skill-manifest-check", *([skill_dir] if skill_dir else []))


def _frontmatter(manifest: Path) -> dict[str, object]:
    """Parse the YAML frontmatter block of a skill manifest.

    Parameters
    ----------
    manifest : Path
        The ``SKILL.md`` to parse.

    Returns
    -------
    dict of str to object
        The parsed frontmatter mapping, empty when the block holds no keys.
    """
    lines = manifest.read_text(encoding="utf-8").splitlines()
    assert lines and lines[0] == "---", (
        f"{manifest} does not open with a frontmatter fence"
    )
    closing = lines.index("---", 1)
    parsed = yaml.safe_load("\n".join(lines[1:closing]))
    assert parsed is None or isinstance(parsed, dict), (
        f"{manifest} frontmatter is not a mapping"
    )
    return {str(key): value for key, value in (parsed or {}).items()}


def _write_manifest(skill_dir: Path, body: str) -> Path:
    """Create a skill directory containing the given manifest text.

    Parameters
    ----------
    skill_dir : Path
        Directory to create; it must not already exist.
    body : str
        The complete ``SKILL.md`` content, fences included.

    Returns
    -------
    Path
        The directory just created.
    """
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
    return skill_dir


def test_shipped_skill_manifests_satisfy_the_contract() -> None:
    """Every shipped skill passes YAML and Agent Skills schema validation."""
    result = _run_manifest_check()

    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("case", "frontmatter", "expected"),
    [
        (
            "missing-name",
            "description: A fixture that lacks the required name.\n",
            "Missing required field in frontmatter: name",
        ),
        (
            "empty-name",
            'name: ""\ndescription: A fixture whose name is empty.\n',
            "Field 'name' must be a non-empty string",
        ),
        (
            "missing-description",
            "name: missing-description\n",
            "Missing required field in frontmatter: description",
        ),
        (
            "empty-description",
            'name: empty-description\ndescription: ""\n',
            "Field 'description' must be a non-empty string",
        ),
    ],
)
def test_manifest_check_rejects_an_unusable_manifest(
    tmp_path: Path, case: str, frontmatter: str, expected: str
) -> None:
    """Both required fields are enforced, present but unusable included.

    An absent ``name`` or ``description`` and an empty one fail validation
    identically. Where the schema checks it, the directory name matches the
    manifest ``name``, so a rejection can only come from the field under test.
    """
    skill_dir = _write_manifest(
        tmp_path / case,
        f"---\n{frontmatter}---\n\n# Fixture\n",
    )

    result = _run_manifest_check(skill_dir)

    assert result.returncode != 0, result.stdout + result.stderr
    assert expected in result.stderr, result.stdout + result.stderr


@pytest.mark.parametrize(
    "manifest", SHIPPED_MANIFESTS, ids=lambda path: path.parent.name
)
def test_shipped_metadata_values_are_strings(manifest: Path) -> None:
    """Metadata carries only string values, which ``skills-ref`` silently coerces.

    ``skills_ref.parser`` rewrites every metadata value with ``str(v)``, so a
    YAML sequence survives validation but reaches consumers as a Python repr.
    The specification admits string keys and string values only, so reject the
    non-conformant shapes here rather than shipping a silently mangled value.
    """
    metadata = _frontmatter(manifest).get("metadata", {})

    assert isinstance(metadata, dict), (
        f"metadata must be a mapping, got {type(metadata).__name__}"
    )
    non_strings = {
        key: value for key, value in metadata.items() if not isinstance(value, str)
    }
    assert not non_strings, f"metadata values must be strings: {non_strings}"


def test_frontmatter_lint_reports_an_early_failure(tmp_path: Path) -> None:
    """A failure in any skill fails the target, not just one in the final skill.

    The shell ``for`` loop otherwise exits with the status of its last
    iteration, letting a conformant trailing skill mask a malformed earlier
    one.
    """
    broken = _write_manifest(tmp_path / "a-broken", BROKEN_MANIFEST)
    valid = _write_manifest(tmp_path / "z-valid", VALID_MANIFEST)

    result = _run_make("skill-frontmatter-lint", broken, valid)

    assert result.returncode != 0, result.stdout + result.stderr
    assert "syntax error" in result.stdout, result.stdout + result.stderr


@pytest.mark.parametrize(
    "invalid_first", [True, False], ids=["invalid-first", "invalid-last"]
)
def test_manifest_validate_reports_a_failure_in_any_position(
    tmp_path: Path, invalid_first: bool
) -> None:
    """A non-conformant directory fails the target wherever it sits in the list.

    An invalid directory first is the ``set -e`` guard: without it the loop
    exits with the status of the valid skill that follows. An invalid directory
    last proves the loop reaches the end of ``SKILL_DIRS``.
    """
    valid = _write_manifest(tmp_path / "z-valid", VALID_MANIFEST)
    invalid = _write_manifest(tmp_path / "b-invalid", INVALID_MANIFEST)
    skill_dirs = (invalid, valid) if invalid_first else (valid, invalid)

    result = _run_make("skill-manifest-validate", *skill_dirs)

    assert result.returncode != 0, result.stdout + result.stderr
    assert "Missing required field in frontmatter: description" in result.stderr


def test_lint_runs_the_manifest_contract(
    tmp_path: Path, cmd_mox: CmdMox
) -> None:
    """``make lint`` fails on a malformed manifest, proving the targets are wired in.

    The contract is only enforced because ``lint`` depends on
    ``skill-manifest-check``; without this test, dropping that prerequisite
    would silently disable manifest validation while every other test still
    passed. The Markdown lint tools are stubbed, so the failure can only come
    from the manifest targets.
    """
    for tool in MARKDOWN_TOOLS:
        cmd_mox.stub(tool).returns(exit_code=0)
    cmd_mox.replay()

    skill_dir = _write_manifest(
        tmp_path / "unlintable",
        "---\ndescription: A fixture that lacks the required name.\n---\n\n# Fixture\n",
    )

    result = _run_make("lint", skill_dir)

    cmd_mox.verify()
    assert result.returncode != 0, result.stdout + result.stderr
    assert "Missing required field in frontmatter: name" in result.stderr


def test_frontmatter_lint_reports_an_unreadable_manifest(tmp_path: Path) -> None:
    """A manifest that cannot be read fails the target rather than being skipped.

    ``awk`` fails to read a missing ``SKILL.md``, a distinct failure path from
    ``yamllint`` rejecting parsed content, and one that only ``pipefail``
    surfaces.
    """
    absent = tmp_path / "absent"
    absent.mkdir()
    valid = _write_manifest(tmp_path / "z-valid", VALID_MANIFEST)

    result = _run_make("skill-frontmatter-lint", absent, valid)

    assert result.returncode != 0, result.stdout + result.stderr
