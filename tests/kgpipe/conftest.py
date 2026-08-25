"""Collect KGpipe task pytest outcomes into catalog/reports/kgpipe-tasks.json."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "_scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from catalog_util import REPO_ROOT  # noqa: E402
from kgpipe_catalog import REPORT_PATH, discover_test_cases  # noqa: E402

_RESULTS = []
_CASES_BY_ID = {case["id"]: case for case in discover_test_cases()}


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "kgpipe: long-running KGpipe task tests that need wrappers; not run in CI",
    )


def pytest_runtest_logreport(report):
    if report.when == "call":
        pass
    elif report.when == "setup" and (report.failed or report.skipped):
        pass
    else:
        return
    nodeid = report.nodeid
    case_id = None
    if "[" in nodeid and nodeid.endswith("]"):
        case_id = nodeid[nodeid.rfind("[") + 1 : -1]
    parts = (case_id or "").split("/", 1)
    case = _CASES_BY_ID.get(case_id or "")
    tool = case["tool"] if case else (parts[0] if len(parts) == 2 else "")
    task = case["task"] if case else (parts[1] if len(parts) == 2 else case_id or "")
    outcome = report.outcome
    error = None
    if report.failed:
        error = str(report.longrepr)
    _RESULTS.append(
        {
            "id": case_id or nodeid,
            "task": task,
            "tool": tool,
            "path": str(case["path"].relative_to(REPO_ROOT)) if case else None,
            "outcome": outcome,
            "duration_s": round(getattr(report, "duration", 0.0) or 0.0, 3),
            "error": error,
        }
    )


def pytest_sessionfinish(session, exitstatus):
    markexpr = (getattr(session.config.option, "markexpr", None) or "").strip()
    if markexpr == "not kgpipe":
        return
    if not _RESULTS and "kgpipe" not in markexpr:
        return
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pytest_exitstatus": int(exitstatus),
        "cases": _RESULTS,
    }
    REPORT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
