"""Shared catalog loading and integration-status helpers."""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
CATEGORIES_PATH = REPO_ROOT / "catalog" / "categories.yaml"
INDEX_PATH = REPO_ROOT / "catalog" / "index.yaml"
GITHUB_REPO = "https://github.com/vehnem/kg-tools"


def load_yaml(path):
    with open(str(path), encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_category_meta():
    return load_yaml(CATEGORIES_PATH).get("categories", {})


def load_featured_ids():
    featured = load_yaml(INDEX_PATH).get("featured", [])
    return list(featured) if featured else []


def load_manifests():
    manifests = []
    for path in sorted(TOOLS_DIR.glob("*/tool.yaml")):
        if path.parent.name == "_template":
            continue
        data = load_yaml(path)
        data["_path"] = path.parent
        manifests.append(data)
    return manifests


def humanize_category(key):
    spaced = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", key)
    if not spaced:
        return key
    return spaced[0] + spaced[1:].lower()


def has_wrapper(tool_dir):
    docker = tool_dir / "docker"
    if (docker / "wrapper").is_dir():
        return True
    if docker.is_dir():
        for path in docker.iterdir():
            if path.is_file() and "wrapper" in path.name.lower():
                return True
    return False


def has_local_kgpipe(tool_dir):
    kgpipe_dir = tool_dir / "kgpipe"
    if not kgpipe_dir.is_dir():
        return False
    return any(kgpipe_dir.iterdir())


def kgpipe_refs(manifest):
    return list(manifest.get("kgpipe", {}).get("task_refs") or [])


def require_featured_ids(manifests, featured_ids):
    by_id = {m["id"]: m for m in manifests}
    missing = [tool_id for tool_id in featured_ids if tool_id not in by_id]
    if missing:
        raise SystemExit(
            "catalog/index.yaml featured ids not found: {}".format(", ".join(missing))
        )
    return by_id
