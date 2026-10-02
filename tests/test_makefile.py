"""Behavioural tests for the Makefile gates.

These cover four things the gate wiring must get right: which target runs by
default, which gates ``check`` actually aggregates, that a failing tool fails
the build rather than being swallowed, and that the file list handed to
``mdtablefix`` is invoked with the estate's selection and rewrite flags.
"""

from __future__ import annotations

import shutil
import subprocess
import typing as t
from pathlib import Path

from cmd_mox import Invocation
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

EXTERNAL_TOOLS = ("mdtablefix", "markdownlint-cli2", "nixie", "uv")
LINTER = "markdownlint-cli2"
# `--git --include-untracked` choose the files (mdtablefix does the selecting,
# so the Makefile builds no file list); the rest choose the rewrites.
ESTATE_FLAGS = (
    "--git",
    "--include-untracked",
    "--wrap",
    "--renumber",
    "--breaks",
    "--ellipsis",
    "--fences",
)


def _stub_all(cmd_mox: CmdMox) -> None:
    """Register passing stubs for every external tool the recipes call."""
    for tool in EXTERNAL_TOOLS:
        cmd_mox.stub(tool).returns(exit_code=0)


# --- default goal and target wiring -----------------------------------------


def test_default_goal_is_check(scratch_repo: ScratchRepo) -> None:
    """Running make with no target must plan exactly what `make check` plans."""
    bare = scratch_repo.make("-n")
    explicit = scratch_repo.make("-n", "check")

    assert bare.returncode == 0, bare.stderr
    assert explicit.returncode == 0, explicit.stderr
    assert bare.stdout == explicit.stdout, (
        "the default goal plans something other than check"
    )


@pytest.mark.parametrize(
    ("gate", "command"),
    [
        ("markdownlint", LINTER),
        ("nixie", "nixie"),
        ("skill-manifest-check", "skills-ref"),
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
    """`fmt` rewrites files, so the gate may check but must never rewrite."""
    result = scratch_repo.make("-n", "check")

    assert result.returncode == 0, result.stderr
    assert "mdtablefix --check" in result.stdout, "check never verifies Markdown"
    assert "--in-place" not in result.stdout, "the gate would rewrite files"
    assert "--fix" not in result.stdout, "the gate would apply lint fixes"


# --- failure propagation ----------------------------------------------------


@pytest.mark.parametrize("failing", [LINTER, "nixie"])
def test_lint_fails_when_a_tool_fails(
    scratch_repo: ScratchRepo, cmd_mox: CmdMox, failing: str
) -> None:
    """A non-zero exit from either lint tool must fail `make lint`."""
    for tool in (LINTER, "nixie"):
        cmd_mox.stub(tool).returns(exit_code=1 if tool == failing else 0)
    cmd_mox.replay()

    result = scratch_repo.make("lint")

    cmd_mox.verify()
    assert result.returncode != 0, f"a failing {failing} did not fail the gate"


def test_lint_passes_when_both_tools_pass(
    scratch_repo: ScratchRepo, cmd_mox: CmdMox
) -> None:
    """All lint tools passing must leave `make lint` green."""
    scratch_repo.write(
        "skills/example/SKILL.md",
        "---\nname: example\ndescription: Example skill.\n---\n",
    )
    _stub_all(cmd_mox)
    cmd_mox.replay()

    result = scratch_repo.make("lint", "SKILL_DIRS=skills/example/")

    cmd_mox.verify()
    assert result.returncode == 0, result.stderr


def test_lint_fails_when_skill_manifest_check_fails(
    scratch_repo: ScratchRepo, cmd_mox: CmdMox
) -> None:
    """A failed manifest validator must fail the aggregate lint gate."""
    scratch_repo.write(
        "skills/example/SKILL.md",
        "---\nname: example\ndescription: Example skill.\n---\n",
    )
    for tool in (LINTER, "nixie"):
        cmd_mox.stub(tool).returns(exit_code=0)

    def uv_result(invocation: Invocation) -> tuple[str, str, int]:
        if invocation.args[3:4] == ["yamllint"]:
            return "", "", 0
        if invocation.args[3:5] == ["skills-ref", "validate"]:
            return "", "", 1
        pytest.fail(f"unexpected uv invocation: {invocation.args!r}")

    uv_spy = cmd_mox.spy("uv").runs(uv_result)
    cmd_mox.replay()

    result = scratch_repo.make("lint", "SKILL_DIRS=skills/example/")

    cmd_mox.verify()
    assert result.returncode != 0, "a failed skill-manifest gate was swallowed"
    assert [invocation.args[3] for invocation in uv_spy.invocations] == [
        "yamllint",
        "skills-ref",
    ]
    uv_spy.assert_called_with(
        "run", "--group", "dev", "skills-ref", "validate", "skills/example/"
    )


def test_check_fmt_runs_markdownlint(
    scratch_repo: ScratchRepo, cmd_mox: CmdMox
) -> None:
    """The formatting gate must actually invoke the Markdown linter."""
    spy = cmd_mox.spy(LINTER).returns(exit_code=0)
    cmd_mox.stub("mdtablefix").returns(exit_code=0)
    cmd_mox.replay()

    result = scratch_repo.make("check-fmt")

    cmd_mox.verify()
    assert result.returncode == 0, result.stderr
    assert spy.call_count == 1, f"the linter ran {spy.call_count} times, not once"


# --- mdtablefix invocation --------------------------------------------------


def _argv_of(spy: t.Any, flag: str) -> list[str]:
    """Return the one recorded argument list that carries ``flag``."""
    (matching,) = [list(call.args) for call in spy.invocations if flag in call.args]
    return matching


def test_check_fmt_runs_the_table_check_with_every_estate_flag(
    scratch_repo: ScratchRepo, cmd_mox: CmdMox
) -> None:
    """`check-fmt` calls `mdtablefix --check` with the selection and rewrite flags."""
    spy = cmd_mox.spy("mdtablefix").returns(exit_code=0)
    cmd_mox.stub(LINTER).returns(exit_code=0)
    cmd_mox.replay()

    result = scratch_repo.make("check-fmt")

    cmd_mox.verify()
    assert result.returncode == 0, result.stderr
    argv = _argv_of(spy, "--check")
    assert set(ESTATE_FLAGS) <= set(argv), f"missing flags in {argv}"
    assert "--in-place" not in argv, f"check-fmt would rewrite files: {argv}"


def test_fmt_rewrites_with_every_estate_flag_then_lints_with_fix(
    scratch_repo: ScratchRepo, cmd_mox: CmdMox
) -> None:
    """`fmt` rewrites in place, then applies the linter's fixes, in that order."""
    scratch_repo.write("tracked.md")
    scratch_repo.track()

    spy = cmd_mox.spy("mdtablefix").returns(exit_code=0)
    lint = cmd_mox.spy(LINTER).returns(exit_code=0)
    cmd_mox.replay()

    result = scratch_repo.make("fmt")

    cmd_mox.verify()
    assert result.returncode == 0, result.stderr
    argv = _argv_of(spy, "--in-place")
    assert set(ESTATE_FLAGS) <= set(argv), f"missing flags in {argv}"
    assert "--check" not in argv, f"fmt would only check: {argv}"
    assert "--fix" in _argv_of(lint, "--fix"), "the linter was not asked to fix"


def test_fmt_lints_after_it_rewrites(tmp_path: Path, repo_root: Path) -> None:
    """The linter's fixes apply to the text mdtablefix has just written.

    cmd-mox spies do not share an ordering, so recording shims capture the
    sequence of tool invocations in one log.
    """
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    shutil.copy(repo_root / "Makefile", tmp_path / "Makefile")
    repo = ScratchRepo(tmp_path)
    bin_dir = tmp_path / ".bin"
    record = install_recorders(bin_dir, "mdtablefix", LINTER)

    result = repo.make(
        "fmt",
        env={
            "PATH": f"{bin_dir}:{Path('/usr/bin')}:{Path('/bin')}",
            RECORD_ENV: str(record),
        },
    )

    assert result.returncode == 0, result.stderr
    order = [argv[0] for argv in recorded_argv(record)]
    assert order == ["mdtablefix", LINTER], f"unexpected order {order}"


def test_fmt_builds_no_file_list(scratch_repo: ScratchRepo, cmd_mox: CmdMox) -> None:
    """mdtablefix selects the files itself, so no path reaches its argv.

    Replaces the old guards on the `git ls-files | xargs` pipeline (hostile
    names, leading hyphens, a failing `git`): with no pipeline there is no
    file list to quote, terminate or lose.
    """
    for name in ("tracked.md", "-dash.md", "docs/a b;touch INJECTED.md"):
        scratch_repo.write(name)
    scratch_repo.track()

    spy = cmd_mox.spy("mdtablefix").returns(exit_code=0)
    cmd_mox.stub(LINTER).returns(exit_code=0)
    cmd_mox.replay()

    result = scratch_repo.make("fmt")

    cmd_mox.verify()
    assert result.returncode == 0, result.stderr
    assert not (scratch_repo.path / "INJECTED.md").exists(), (
        "a tracked name was executed"
    )
    argv = _argv_of(spy, "--in-place")
    assert all(arg.startswith("--") for arg in argv), f"a path reached {argv}"


@pytest.mark.parametrize(
    ("target", "tool"),
    [("fmt", "mdtablefix"), ("fmt", LINTER), ("check-fmt", "mdtablefix")],
)
def test_a_failing_formatter_fails_the_target(
    scratch_repo: ScratchRepo, cmd_mox: CmdMox, target: str, tool: str
) -> None:
    """The tool's exit status reaches Make; it is not swallowed by a pipeline."""
    for name in EXTERNAL_TOOLS:
        cmd_mox.stub(name).returns(exit_code=1 if name == tool else 0)
    cmd_mox.replay()

    result = scratch_repo.make(target)

    cmd_mox.verify()
    assert result.returncode != 0, f"a failing {tool} did not fail {target}"


# --- property: tracked names never reach, or run from, the recipe -----------

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
def test_fmt_argv_is_independent_of_tracked_markdown_names(
    tmp_path_factory: pytest.TempPathFactory, stems: list[str]
) -> None:
    """Whatever Markdown names are tracked, `fmt` runs the same two commands.

    The recipe no longer builds a file list, so no name can be split, expanded
    or executed by it: the recorded mdtablefix argv is exactly the estate flags
    plus `--in-place`, never a path, and nothing in the tree is created by a
    filename being run.

    cmd-mox cannot be used here, because its fixture is function-scoped and
    Hypothesis refuses that, so recording shims stand in for the tools.
    """
    root = tmp_path_factory.mktemp("fmt")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True)
    shutil.copy(Path(__file__).resolve().parent.parent / "Makefile", root / "Makefile")
    repo = ScratchRepo(root)

    for stem in stems:
        repo.write(f"{stem}.md")
    repo.write("decoy.txt", "not markdown\n")
    repo.track()

    bin_dir = root / ".bin"
    record = install_recorders(bin_dir, "mdtablefix", LINTER)
    before = {p.name for p in root.iterdir()}

    result = repo.make(
        "fmt",
        env={
            "PATH": f"{bin_dir}:{Path('/usr/bin')}:{Path('/bin')}",
            RECORD_ENV: str(record),
        },
    )

    assert result.returncode == 0, result.stderr

    rewrites = [a for a in recorded_argv(record) if a[0] == "mdtablefix"]
    assert len(rewrites) == 1, f"expected one rewrite, got {rewrites}"
    assert sorted(rewrites[0][1:]) == sorted(["--in-place", *ESTATE_FLAGS])
    assert {p.name for p in root.iterdir()} == before, "a filename was executed"
