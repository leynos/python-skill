"""Behavioural tests for the Makefile gates.

These cover four things the gate wiring must get right: which target runs by
default, which gates ``check`` actually aggregates, that a failing tool fails
the build rather than being swallowed, and that the file list handed to
``mdtablefix`` is built safely.
"""

from __future__ import annotations

import typing as t

import pytest

if t.TYPE_CHECKING:  # pragma: no cover - typing only
    from cmd_mox import CmdMox

    from tests._scratch import ScratchRepo

MARKDOWN_TOOLS = ("mdtablefix", "markdownlint", "nixie")


def _stub_all(cmd_mox: CmdMox) -> None:
    """Register passing stubs for every external tool the recipes call."""
    for tool in MARKDOWN_TOOLS:
        cmd_mox.stub(tool).returns(exit_code=0)


# --- default goal and target wiring -----------------------------------------


def test_default_goal_is_check(scratch_repo: ScratchRepo) -> None:
    """Running make with no target must plan exactly what `make check` plans."""
    bare = scratch_repo.make("-n")
    explicit = scratch_repo.make("-n", "check")

    assert bare.returncode == 0, bare.stderr
    assert explicit.returncode == 0, explicit.stderr
    assert bare.stdout == explicit.stdout


@pytest.mark.parametrize(
    ("gate", "command"),
    [
        ("markdownlint", "markdownlint"),
        ("nixie", "nixie"),
        ("typecheck", "mypy"),
        ("test", "pytest"),
    ],
)
def test_check_aggregates_every_gate(
    scratch_repo: ScratchRepo, gate: str, command: str
) -> None:
    """`check` must reach lint, check-fmt, typecheck and test, not lint alone."""
    result = scratch_repo.make("-n", "check")

    assert result.returncode == 0, result.stderr
    assert command in result.stdout, f"{gate} gate is not reached by check"


def test_fmt_is_not_part_of_check(scratch_repo: ScratchRepo) -> None:
    """`fmt` rewrites files, so the gate must not run it."""
    result = scratch_repo.make("-n", "check")

    assert result.returncode == 0, result.stderr
    assert "mdtablefix" not in result.stdout


# --- failure propagation ----------------------------------------------------


def test_lint_fails_when_markdownlint_fails(
    scratch_repo: ScratchRepo, cmd_mox: CmdMox
) -> None:
    """A non-zero markdownlint must fail `make lint`."""
    cmd_mox.stub("markdownlint").returns(exit_code=1)
    cmd_mox.stub("nixie").returns(exit_code=0)
    cmd_mox.replay()

    result = scratch_repo.make("lint")

    cmd_mox.verify()
    assert result.returncode != 0


def test_lint_fails_when_nixie_fails(
    scratch_repo: ScratchRepo, cmd_mox: CmdMox
) -> None:
    """A non-zero nixie must fail `make lint` even though markdownlint passed."""
    cmd_mox.stub("markdownlint").returns(exit_code=0)
    cmd_mox.stub("nixie").returns(exit_code=1)
    cmd_mox.replay()

    result = scratch_repo.make("lint")

    cmd_mox.verify()
    assert result.returncode != 0


def test_lint_passes_when_both_tools_pass(
    scratch_repo: ScratchRepo, cmd_mox: CmdMox
) -> None:
    """Both tools passing must leave `make lint` green."""
    _stub_all(cmd_mox)
    cmd_mox.replay()

    result = scratch_repo.make("lint")

    cmd_mox.verify()
    assert result.returncode == 0, result.stderr


def test_check_fmt_runs_markdownlint(
    scratch_repo: ScratchRepo, cmd_mox: CmdMox
) -> None:
    """The formatting gate must actually invoke markdownlint."""
    spy = cmd_mox.spy("markdownlint").returns(exit_code=0)
    cmd_mox.replay()

    result = scratch_repo.make("check-fmt")

    cmd_mox.verify()
    assert result.returncode == 0, result.stderr
    assert spy.call_count == 1


# --- file selection ---------------------------------------------------------


def test_fmt_passes_pathological_filenames_as_single_arguments(
    scratch_repo: ScratchRepo, cmd_mox: CmdMox
) -> None:
    """A filename holding shell metacharacters must arrive as one argument.

    Regression test: the file list was once interpolated unquoted into the
    recipe, so a tracked name containing ``;`` ran as a second shell command
    and a name containing a space was split into two arguments.
    """
    hostile = "docs/a b;touch INJECTED.md"
    scratch_repo.write(hostile)
    scratch_repo.track()

    spy = cmd_mox.spy("mdtablefix").returns(exit_code=0)
    cmd_mox.stub("markdownlint").returns(exit_code=0)
    cmd_mox.replay()

    result = scratch_repo.make("fmt")

    cmd_mox.verify()
    assert result.returncode == 0, result.stderr
    assert not (scratch_repo.path / "INJECTED.md").exists()

    (invocation,) = spy.invocations
    assert hostile in invocation.args


def test_fmt_selects_only_tracked_markdown(
    scratch_repo: ScratchRepo, cmd_mox: CmdMox
) -> None:
    """Untracked files and non-Markdown files must not reach mdtablefix."""
    scratch_repo.write("tracked.md")
    scratch_repo.write("nested/deep.markdown")
    scratch_repo.write("notes.txt", "plain\n")
    scratch_repo.track()
    scratch_repo.write("untracked.md")

    spy = cmd_mox.spy("mdtablefix").returns(exit_code=0)
    cmd_mox.stub("markdownlint").returns(exit_code=0)
    cmd_mox.replay()

    result = scratch_repo.make("fmt")

    cmd_mox.verify()
    assert result.returncode == 0, result.stderr

    (invocation,) = spy.invocations
    selected = set(invocation.args)
    assert "tracked.md" in selected
    assert "nested/deep.markdown" in selected
    assert "notes.txt" not in selected
    assert "untracked.md" not in selected


def test_fmt_succeeds_with_no_markdown_files(
    scratch_repo: ScratchRepo, cmd_mox: CmdMox
) -> None:
    """An empty file list must skip mdtablefix rather than invoking it bare."""
    spy = cmd_mox.spy("mdtablefix").returns(exit_code=0)
    cmd_mox.stub("markdownlint").returns(exit_code=0)
    cmd_mox.replay()

    result = scratch_repo.make("fmt")

    cmd_mox.verify()
    assert result.returncode == 0, result.stderr
    assert spy.call_count == 0
