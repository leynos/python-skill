"""Execute the Skylos skill's documented examples rather than trusting them.

The skill presents a narrow entrypoint configuration and a contract test that
guards it as a working pair. If either drifts, a reader copies an example that
fails on first use, or a contract that admits the very defects it is meant to
reject. The shell snippets are only syntax-checked: running them needs a
consuming repository and a pinned Skylos release.
"""

from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
from pathlib import Path
from types import ModuleType

import pytest

REFERENCES = Path("skills") / "skylos" / "references"
CONFIG_DOC = REFERENCES / "configuration-and-evidence.md"
CONTRACT_DOC = REFERENCES / "triage-and-regression.md"
FENCE = re.compile(r"^```(?P<lang>\w+)\n(?P<body>.*?)^```$", re.MULTILINE | re.DOTALL)


def _blocks(document: Path, lang: str) -> list[str]:
    """Return the bodies of every fenced block in ``lang``."""
    text = document.read_text(encoding="utf-8")
    return [m.group("body") for m in FENCE.finditer(text) if m.group("lang") == lang]


def _only_block(document: Path, lang: str) -> str:
    blocks = _blocks(document, lang)
    assert len(blocks) == 1, f"{document}: expected one {lang} block, got {len(blocks)}"
    return blocks[0]


@pytest.fixture
def documented_toml(repo_root: Path) -> str:
    """Return the documented entrypoint configuration."""
    return _only_block(repo_root / CONFIG_DOC, "toml")


@pytest.fixture
def contract(repo_root: Path, tmp_path: Path) -> tuple[ModuleType, Path]:
    """Load the documented contract test from a scratch repository layout.

    The example resolves the repository root as the parent of its own
    directory, so it is written to ``tests/`` beneath the scratch root.
    """
    source = _only_block(repo_root / CONTRACT_DOC, "python")
    module_path = tmp_path / "tests" / "test_pool_contract.py"
    module_path.parent.mkdir()
    module_path.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("skylos_pool_contract", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, tmp_path / "pyproject.toml"


def test_documented_contract_accepts_documented_configuration(
    contract: tuple[ModuleType, Path], documented_toml: str
) -> None:
    """The two examples describe the same five methods and must agree."""
    module, pyproject = contract
    pyproject.write_text(documented_toml, encoding="utf-8")

    module.test_pool_dead_code_configuration()


@pytest.mark.parametrize(
    ("old", "new"),
    [
        pytest.param(
            '"example.pool.PoolExecutor._worker_loop"',
            '"example.pool.PoolExecutor._run_worker"',
            id="stale-rename",
        ),
        pytest.param(
            '"example.pool.PoolExecutor._worker_loop"',
            '"example.pool.PoolExecutor.*"',
            id="wildcard-name",
        ),
        pytest.param(
            '"example.pool.PoolExecutor._worker_loop"',
            '"example.pool.PoolExecutor.submit"',
            id="duplicate-name",
        ),
        pytest.param(
            '  "example.pool.PoolExecutor._retire_or_reuse",\n',
            '  "example.pool.PoolExecutor._retire_or_reuse",\n'
            '  "example.pool.PoolExecutor.unused_sibling",\n',
            id="extra-symbol",
        ),
        pytest.param('type = "method"', 'type = "function"', id="wrong-kind"),
        pytest.param(
            'type = "method"',
            'type = "method"\nparent = "PoolExecutor"',
            id="parent-selector",
        ),
        pytest.param(
            re.compile(r'reason = """.*?"""', re.DOTALL),
            'reason = "  "',
            id="empty-reason",
        ),
    ],
)
def test_documented_contract_rejects_defects(
    contract: tuple[ModuleType, Path],
    documented_toml: str,
    old: str | re.Pattern[str],
    new: str,
) -> None:
    """Each defect the skill warns about must fail the documented contract."""
    module, pyproject = contract
    if isinstance(old, re.Pattern):
        broken, count = old.subn(new, documented_toml)
    else:
        count = documented_toml.count(old)
        broken = documented_toml.replace(old, new)
    assert count == 1, "the defect must apply to exactly one site"
    pyproject.write_text(broken, encoding="utf-8")

    with pytest.raises(AssertionError):
        module.test_pool_dead_code_configuration()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is unavailable")
@pytest.mark.parametrize("index", [0, 1])
def test_documented_shell_examples_parse(repo_root: Path, index: int) -> None:
    """The shell examples must at least be syntactically valid Bash."""
    blocks = _blocks(repo_root / CONFIG_DOC, "bash")
    assert len(blocks) == 2

    result = subprocess.run(
        ["bash", "-n"],
        input=blocks[index],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
