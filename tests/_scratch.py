"""A throwaway git repository used to exercise the real Makefile recipes."""

from __future__ import annotations

import subprocess
from pathlib import Path


class ScratchRepo:
    """A throwaway git repository carrying the project's real Makefile."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def write(self, relative: str, content: str = "# heading\n") -> Path:
        """Create a file, making parent directories as needed."""
        target = self.path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def track(self, *paths: str) -> None:
        """Stage the named paths, or everything when none are given."""
        if paths:
            self._git("add", "--", *paths)
        else:
            self._git("add", "-A")

    def make(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Invoke make in the scratch repository and capture its output."""
        return subprocess.run(  # noqa: S603 - fixed argv, no shell
            ["make", *args],
            cwd=self.path,
            capture_output=True,
            text=True,
            check=False,
        )

    def _git(self, *args: str) -> None:
        subprocess.run(  # noqa: S603 - fixed argv, no shell
            ["git", *args], cwd=self.path, check=True, capture_output=True
        )
