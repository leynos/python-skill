"""A throwaway git repository used to exercise the real Makefile recipes."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

RECORD_ENV = "ARGV_RECORD"

_RECORDER = """#!/usr/bin/env python3
import json
import os
import sys

with open(os.environ["{env}"], "a", encoding="utf-8") as handle:
    handle.write(json.dumps([os.path.basename(sys.argv[0]), *sys.argv[1:]]) + "\\n")
"""


class ScratchRepo:
    """A throwaway git repository carrying the project's real Makefile.

    Recipes are exercised against a copy of the real Makefile so that the
    tests cannot drift from the file they describe, while hostile filenames
    stay out of the catalogue's own working tree.

    Parameters
    ----------
    path : Path
        Root of the scratch repository. A git repository is expected to have
        been initialised there already, with the Makefile copied in.

    Attributes
    ----------
    path : Path
        Root of the scratch repository.
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    def write(self, relative: str, content: str = "# heading\n") -> Path:
        """Create a file inside the repository.

        Parameters
        ----------
        relative : str
            Path relative to the repository root. Parent directories are
            created as needed.
        content : str, optional
            Text written to the file, UTF-8 encoded.

        Returns
        -------
        Path
            The absolute path of the file just written.

        Side effects
        ------------
        Creates directories and writes to the filesystem, overwriting any
        file already at that path.
        """
        target = self.path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def track(self, *paths: str) -> None:
        """Stage paths so that ``git ls-files`` will report them.

        Parameters
        ----------
        *paths : str
            Paths to stage, relative to the repository root. When none are
            given, everything in the working tree is staged.

        Side effects
        ------------
        Runs ``git add`` in the scratch repository, mutating its index.
        Paths are passed after ``--`` so that a leading hyphen is treated as
        a filename rather than an option.
        """
        if paths:
            self._git("add", "--", *paths)
        else:
            self._git("add", "-A")

    def make(
        self, *args: str, env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        """Invoke make in the repository and capture its output.

        Parameters
        ----------
        *args : str
            Arguments passed to ``make``, such as a target name or ``-n``.
        env : dict of str to str, optional
            Extra environment variables layered over the inherited
            environment. Used to point recording shims at their log.

        Returns
        -------
        subprocess.CompletedProcess of str
            The completed process, with stdout and stderr decoded as text.
            The exit status is returned rather than raised on, since several
            tests assert that a gate fails.

        Side effects
        ------------
        Runs make, which executes recipes against the scratch repository.
        """
        merged = {**os.environ, **(env or {})}
        return subprocess.run(  # noqa: S603 - fixed argv, no shell
            ["make", *args],
            cwd=self.path,
            capture_output=True,
            text=True,
            check=False,
            env=merged,
        )

    def _git(self, *args: str) -> None:
        """Run a git command in the repository, raising on a non-zero exit."""
        subprocess.run(  # noqa: S603 - fixed argv, no shell
            ["git", *args], cwd=self.path, check=True, capture_output=True
        )


def install_recorders(bin_dir: Path, *names: str) -> Path:
    """Put argv-recording stand-ins for external tools on a directory.

    Used where cmd-mox cannot be: its fixture is function-scoped, and
    Hypothesis rejects function-scoped fixtures because they are not reset
    between examples.

    Parameters
    ----------
    bin_dir : Path
        Directory to write the executables into. Prepend it to ``PATH`` so
        the recipes resolve these rather than the real tools.
    *names : str
        Command names to shadow, for example ``mdtablefix``.

    Returns
    -------
    Path
        The JSON Lines file each invocation appends its argv to. Its path
        must be exported as ``ARGV_RECORD`` for the shims to find it.

    Side effects
    ------------
    Creates ``bin_dir`` and writes an executable script per name.
    """
    bin_dir.mkdir(parents=True, exist_ok=True)
    record = bin_dir / "argv.jsonl"
    for name in names:
        shim = bin_dir / name
        shim.write_text(_RECORDER.format(env=RECORD_ENV), encoding="utf-8")
        shim.chmod(0o755)
    return record


def recorded_argv(record: Path) -> list[list[str]]:
    """Read back the argv lists captured by :func:`install_recorders`.

    Parameters
    ----------
    record : Path
        The JSON Lines file returned by :func:`install_recorders`.

    Returns
    -------
    list of list of str
        One entry per invocation, in call order, each beginning with the
        invoked command's basename. Empty when the file does not exist,
        which means no shim ran.
    """
    if not record.is_file():
        return []
    lines = record.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line]
