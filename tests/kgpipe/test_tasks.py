"""Execute KGpipe task cases (inputs, outputs, optional config). Not run in CI."""

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "_scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from kgpipe_catalog import discover_test_cases  # noqa: E402
from kgpipe_harness import run_case  # noqa: E402

CASES = discover_test_cases()


def _kgpipe_available():
    try:
        import kgpipe.common  # noqa: F401
    except ImportError:
        return False
    return True


@pytest.mark.kgpipe
@pytest.mark.skipif(not _kgpipe_available(), reason="kgpipe is not installed")
@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_kgpipe_task(case, tmp_path):
    run_case(case, tmp_path)
