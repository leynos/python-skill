"""Contract: every uv call in the Makefile goes through the vendored helper.

The helper (``scripts/uv_gate.py``) is copied byte for byte from leynos/shared-actions
and audited by concordat's ``uv-gate-baseline`` rule. These checks keep this
repository's wiring to it from drifting between audits.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = (ROOT / "Makefile").read_text(encoding="utf-8")
# Released uv_gate digests (0.1.0, 0.2.0, 0.2.1); add the new one when moving to a release.
CANONICAL_DIGESTS = {
    "cc8dc5dfba51efcca4e3c117e55e2fcbb463455929f5988efbf9c4532988f163",
    "1aee16702de67cc7dd5dfe15e434f589dfaecf3ca813c85fbff5320c5fe584fe",
    "fe7671d8663ec89ce1076ebb857847802e46c8d6607ab1e012daa443e335e66e",
}
BARE_UV = re.compile(
    r"(?<![A-Za-z0-9_./$-])(?:uvx|(?:uv|\$\(UV\))[ \t]+(?:run|sync|tool[ \t]+run))\b"
)


def test_the_vendored_helper_is_a_released_copy() -> None:
    """The helper's bytes are one of the audited releases."""
    digest = hashlib.sha256((ROOT / "scripts" / "uv_gate.py").read_bytes()).hexdigest()

    assert digest in CANONICAL_DIGESTS


def test_the_gate_variable_is_the_helper() -> None:
    """UV_GATE holds exactly the helper command."""
    assert re.search(r"^UV_GATE \?= python3 scripts/uv_gate\.py$", MAKEFILE, re.M)


def test_no_uv_cache_override_remains() -> None:
    """Neither the Makefile nor the workflows set the uv cache or tool directory."""
    texts = [MAKEFILE, *(p.read_text(encoding="utf-8") for p in ROOT.glob(".github/**/*.y*ml"))]

    assert not [t for t in texts if re.search(r"UV_(?:CACHE|TOOL)_DIR\s*[:=]", t)]


def test_recipes_reach_uv_only_through_the_helper() -> None:
    """No bare uv run, sync, tool run or uvx remains, bar typos-config-builder at a tag."""
    offenders = [
        line.strip()
        for line in MAKEFILE.splitlines()
        if BARE_UV.search(line)
        and not line.lstrip().startswith("#")
        and "typos-config-builder" not in line
    ]

    assert not offenders, offenders
