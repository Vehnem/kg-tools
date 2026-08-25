"""Discover KGpipe tasks, pytest cases, and collected local reports."""

import json
import re
from pathlib import Path

from catalog_util import TOOLS_DIR, kgpipe_refs, load_yaml

REPORT_PATH = Path(__file__).resolve().parents[1] / "catalog" / "reports" / "kgpipe-tasks.json"
TEST_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "catalog" / "schema" / "kgpipe_task_test.schema.json"
)

KG_TASK_NAME_RE = re.compile(
    r"""KgTask\(\s*name\s*=\s*["']([^"']+)["']""",
    re.MULTILINE,
)


def iter_kgpipe_test_files():
    for path in sorted(TOOLS_DIR.glob("*/kgpipe/tests/*.yaml")):
        if path.parent.parent.parent.name == "_template":
            continue
        yield path


def load_test_case(path):
    data = load_yaml(path)
    if not isinstance(data, dict):
        data = {}
    task = data.get("task") or path.stem
    tool_id = path.parents[2].name
    return {
        "id": "{}/{}".format(tool_id, path.stem),
        "task": task,
        "tool": tool_id,
        "path": path,
        "description": data.get("description") or "",
        "inputs": dict(data.get("inputs") or {}),
        "outputs": dict(data.get("outputs") or {}),
        "config": dict(data.get("config") or {}),
        "raw": data,
    }


def discover_test_cases():
    return [load_test_case(path) for path in iter_kgpipe_test_files()]


def local_task_names(tool_dir):
    names = []
    kgpipe_dir = tool_dir / "kgpipe"
    if not kgpipe_dir.is_dir():
        return names
    for path in sorted(kgpipe_dir.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        names.extend(KG_TASK_NAME_RE.findall(text))
    return names


def collect_kgpipe_tasks(manifests):
    """One row per task name: refs, locally defined KgTasks, and test cases."""
    by_name = {}

    def ensure(name, tool_id, local=False):
        row = by_name.setdefault(
            name,
            {
                "task": name,
                "tool": tool_id,
                "local": False,
                "tests": [],
            },
        )
        if local:
            row["local"] = True
        if row["tool"] != tool_id and local:
            row["tool"] = tool_id
        return row

    for manifest in manifests:
        tool_id = manifest["id"]
        tool_dir = manifest["_path"]
        for ref in kgpipe_refs(manifest):
            ensure(ref, tool_id)
        for name in local_task_names(tool_dir):
            ensure(name, tool_id, local=True)

    for case in discover_test_cases():
        row = ensure(case["task"], case["tool"], local=False)
        row["tests"].append(case)

    return sorted(by_name.values(), key=lambda row: (row["tool"], row["task"]))


def load_task_report():
    if not REPORT_PATH.is_file():
        return {"generated_at": None, "cases": []}
    try:
        data = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"generated_at": None, "cases": []}
    if not isinstance(data, dict):
        return {"generated_at": None, "cases": []}
    data.setdefault("generated_at", None)
    data.setdefault("cases", [])
    return data


def report_by_task(report):
    """Latest outcome per task name from a collected report."""
    by_task = {}
    for case in report.get("cases") or []:
        task = case.get("task")
        if not task:
            continue
        by_task[task] = case
    return by_task
