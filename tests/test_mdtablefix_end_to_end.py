"""End-to-end checks of the formatting recipes against the real mdtablefix.

The tests in ``test_makefile.py`` hold the recipes' wiring against recording
stubs. These run the real ``make fmt`` and ``make check-fmt`` with the real
``mdtablefix`` in a scratch Git repository, so a recipe that drops a selection
flag or a rewrite flag changes what gets formatted and fails here. The Markdown
linter is replaced by ``true`` (``MDLINT=true``): its own behaviour is not under
test, and ``mdtablefix`` is the formatter the selection flags drive.
"""

from __future__ import annotations

import shutil
import typing as t

import pytest

if t.TYPE_CHECKING:  # pragma: no cover - typing only
    from tests._scratch import ScratchRepo

LONG = " ".join(["word"] * 40)  # one 199 character line, over the 80 column wrap
UNWRAPPED = f"# Title\n\n{LONG}\n"
NO_LINTER = "MDLINT=true"


@pytest.fixture(autouse=True)
def _require_mdtablefix() -> None:
    """Fail, not skip, when the formatter is missing, so the gap is not silent."""
    if shutil.which("mdtablefix") is None:
        pytest.fail("mdtablefix 0.6.1 or later must be on PATH (see the Makefile)")


def _lay_out(repo: ScratchRepo) -> None:
    """Create a tracked, an untracked and a Git-ignored unwrapped document."""
    repo.write(".gitignore", "ignored.md\n")
    repo.write("tracked.md", UNWRAPPED)
    repo.write("ignored.md", UNWRAPPED)
    repo.track(".gitignore", "tracked.md")
    repo.write("untracked.md", UNWRAPPED)


def test_fmt_wraps_tracked_and_untracked_files_but_not_ignored_ones(
    scratch_repo: ScratchRepo,
) -> None:
    """`fmt` rewrites what Git tracks plus unignored untracked files only."""
    _lay_out(scratch_repo)

    result = scratch_repo.make("fmt", NO_LINTER)

    assert result.returncode == 0, result.stderr
    for name in ("tracked.md", "untracked.md"):
        text = (scratch_repo.path / name).read_text(encoding="utf-8")
        assert all(len(line) <= 80 for line in text.splitlines()), f"{name} not wrapped"
        assert " ".join(text.split()[2:]) == LONG, f"{name} lost words"
    ignored = (scratch_repo.path / "ignored.md").read_text(encoding="utf-8")
    assert ignored == UNWRAPPED, "a Git-ignored file was rewritten"


def test_check_fmt_fails_on_unformatted_files_and_passes_once_formatted(
    scratch_repo: ScratchRepo,
) -> None:
    """`check-fmt` flags a tracked or untracked file `fmt` would change."""
    _lay_out(scratch_repo)

    before = scratch_repo.make("check-fmt", NO_LINTER)
    scratch_repo.make("fmt", NO_LINTER)
    after = scratch_repo.make("check-fmt", NO_LINTER)

    assert before.returncode != 0, "check-fmt passed unformatted Markdown"
    assert after.returncode == 0, after.stdout + after.stderr


def test_check_fmt_ignores_an_unformatted_git_ignored_file(
    scratch_repo: ScratchRepo,
) -> None:
    """With only an ignored file unformatted, `check-fmt` has nothing to flag."""
    scratch_repo.write(".gitignore", "ignored.md\n")
    scratch_repo.write("ignored.md", UNWRAPPED)
    scratch_repo.track(".gitignore")

    result = scratch_repo.make("check-fmt", NO_LINTER)

    assert result.returncode == 0, result.stdout + result.stderr
