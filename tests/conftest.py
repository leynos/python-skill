"""Shared fixtures for the catalogue's test suite.

The Makefile tests run ``make`` against a scratch git repository so that the
real recipes are exercised without touching the working tree, and so that
pathological filenames can be committed safely. Third-party tools that the
recipes shell out to (``mdtablefix``, ``markdownlint``, ``nixie``) are replaced
by cmd-mox shims, keeping their real execution outside the unit tests.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from tests._scratch import ScratchRepo

pytest_plugins = ("cmd_mox.pytest_plugin",)

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Locate the catalogue's checkout root.

    Returns
    -------
    Path
        The repository root, derived from this file's location rather than
        the working directory, so the suite is insensitive to where pytest
        was invoked from.
    """
    return REPO_ROOT


@pytest.fixture
def scratch_repo(tmp_path: Path, repo_root: Path) -> ScratchRepo:
    """Build a git repository containing a copy of the real Makefile.

    Parameters
    ----------
    tmp_path : Path
        Per-test temporary directory supplied by pytest, used as the
        repository root.
    repo_root : Path
        The catalogue checkout, used as the source of the Makefile.

    Returns
    -------
    ScratchRepo
        A handle for writing files, staging them, and running make.

    Side effects
    ------------
    Initialises a git repository in ``tmp_path`` and copies the Makefile
    into it. pytest removes the directory as part of its own tmp_path
    housekeeping, so no explicit teardown is needed.
    """
    subprocess.run(  # noqa: S603 - fixed argv, no shell
        ["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True
    )
    shutil.copy(repo_root / "Makefile", tmp_path / "Makefile")
    return ScratchRepo(tmp_path)
