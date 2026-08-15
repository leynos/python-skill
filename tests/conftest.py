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
import typing as t
from pathlib import Path

import pytest

from tests._scratch import ScratchRepo

pytest_plugins = ("cmd_mox.pytest_plugin",)

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Return the catalogue's checkout root."""
    return REPO_ROOT


@pytest.fixture
def scratch_repo(tmp_path: Path, repo_root: Path) -> t.Iterator[ScratchRepo]:
    """Yield a git repository containing a copy of the real Makefile."""
    subprocess.run(  # noqa: S603 - fixed argv, no shell
        ["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True
    )
    shutil.copy(repo_root / "Makefile", tmp_path / "Makefile")
    yield ScratchRepo(tmp_path)
