"""Behavioural tests for the Makefile gates.

These cover four things the gate wiring must get right: which target runs by
default, which gates ``check`` actually aggregates, that a failing tool fails
the build rather than being swallowed, and that the file list handed to
``mdtablefix`` is built safely.
"""

from __future__ import annotations

import shutil
import subprocess
import typing as t
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from tests._scratch import (
    RECORD_ENV,
    ScratchRepo,
    install_recorders,
    recorded_argv,
)

if t.TYPE_CHECKING:  # pragma: no cover - typing only
    from cmd_mox import CmdMox

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


@pytest.mark.parametrize("failing", ["markdownlint", "nixie"])
def test_lint_fails_when_a_tool_fails(
    scratch_repo: ScratchRepo, cmd_mox: CmdMox, failing: str
) -> None:
    """A non-zero exit from either lint tool must fail `make lint`."""
    for tool in ("markdownlint", "nixie"):
        cmd_mox.stub(tool).returns(exit_code=1 if tool == failing else 0)
    cmd_mox.replay()

    result = scratch_repo.make("lint")

    cmd_mox.verify()
    assert result.returncode != 0, f"a failing {failing} did not fail the gate"


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


def test_fmt_passes_leading_hyphen_filenames_as_paths(
    scratch_repo: ScratchRepo, cmd_mox: CmdMox
) -> None:
    """A tracked name starting with `-` must be a path, not an option.

    Regression test: without a `--` terminator in the argv xargs builds,
    mdtablefix parses `-dash.md` as a bundle of short options.
    """
    hyphenated = "-dash.md"
    scratch_repo.write(hyphenated)
    scratch_repo.track()

    spy = cmd_mox.spy("mdtablefix").returns(exit_code=0)
    cmd_mox.stub("markdownlint").returns(exit_code=0)
    cmd_mox.replay()

    result = scratch_repo.make("fmt")

    cmd_mox.verify()
    assert result.returncode == 0, result.stderr

    (invocation,) = spy.invocations
    assert "--" in invocation.args, "option parsing is never terminated"
    terminator = invocation.args.index("--")
    paths = invocation.args[terminator + 1 :]
    assert hyphenated in paths, f"{hyphenated!r} absent after `--`; got {paths}"


def test_fmt_fails_when_file_discovery_fails(
    tmp_path: Path, repo_root: Path, cmd_mox: CmdMox
) -> None:
    """A failing `git ls-files` must fail the recipe, not be swallowed.

    Regression test: a pipeline reports only its last command's status, so
    `git ls-files` exiting 128 outside a work tree was masked by xargs
    exiting 0 on empty input, and `fmt` carried on regardless.
    """
    shutil.copy(repo_root / "Makefile", tmp_path / "Makefile")
    outside_git = ScratchRepo(tmp_path)

    spy = cmd_mox.spy("markdownlint").returns(exit_code=0)
    cmd_mox.stub("mdtablefix").returns(exit_code=0)
    cmd_mox.replay()

    result = outside_git.make("fmt")

    cmd_mox.verify()
    assert result.returncode != 0, "git failure was swallowed by the pipeline"
    assert spy.call_count == 0, "recipe continued past the failed discovery"


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


# --- property: filename safety over arbitrary tracked Markdown names --------

# Characters a shell would act on, plus ordinary ones. All are legal in a
# POSIX filename; only "/" and NUL are excluded because the kernel forbids
# them in a path component.
_HOSTILE = " -;&|$`()<>*?[]{}'\"\\!#%^+=,~\n\ta1Z"

_STEMS = st.text(alphabet=st.sampled_from(list(_HOSTILE)), min_size=1, max_size=12)


def _usable(stem: str) -> bool:
    """Reject stems git or the filesystem would not round-trip."""
    name = f"{stem}.md"
    return (
        name not in {".", ".."}
        and not name.startswith(".git")
        and len(name.encode()) <= 200
    )


@given(stems=st.lists(_STEMS.filter(_usable), min_size=1, max_size=4, unique=True))
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_fmt_preserves_arbitrary_tracked_markdown_names(
    tmp_path_factory: pytest.TempPathFactory, stems: list[str]
) -> None:
    """Any tracked Markdown name reaches mdtablefix exactly, and inertly.

    The invariant the `-z`/`xargs -0`/`--` combination exists to hold: every
    tracked Markdown path is delivered byte-for-byte as one argument, nothing
    untracked or non-Markdown is delivered, and no filename is ever executed.

    cmd-mox cannot be used here — its fixture is function-scoped, which
    Hypothesis refuses because the fixture would not be reset between
    examples — so recording shims stand in for the external tools.
    """
    root = tmp_path_factory.mktemp("fmt")
    subprocess.run(  # noqa: S603 - fixed argv, no shell
        ["git", "init", "-q"], cwd=root, check=True, capture_output=True
    )
    shutil.copy(Path(__file__).resolve().parent.parent / "Makefile", root / "Makefile")
    repo = ScratchRepo(root)

    expected = {f"{stem}.md" for stem in stems}
    for name in expected:
        repo.write(name)
    repo.write("decoy.txt", "not markdown\n")
    repo.track()

    bin_dir = root / ".bin"
    record = install_recorders(bin_dir, "mdtablefix", "markdownlint")
    before = {p.name for p in root.iterdir()}

    result = repo.make(
        "fmt",
        env={
            "PATH": f"{bin_dir}:{Path('/usr/bin')}:{Path('/bin')}",
            RECORD_ENV: str(record),
        },
    )

    assert result.returncode == 0, result.stderr

    # A list, not a set: delivering the same path twice would still be wrong,
    # and a set would quietly absorb it.
    delivered: list[str] = []
    for argv in recorded_argv(record):
        if argv[0] != "mdtablefix":
            continue
        delivered.extend(argv[argv.index("--") + 1 :])

    assert sorted(delivered) == sorted(expected)
    assert {p.name for p in root.iterdir()} == before, "a filename was executed"
