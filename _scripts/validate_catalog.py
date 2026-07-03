#!/usr/bin/env python3
"""Validate all tools/*/tool.yaml manifests against the JSON schema."""

import json
import sys
from pathlib import Path

import jsonschema
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "catalog" / "schema" / "tool.schema.json"
TOOLS_DIR = REPO_ROOT / "tools"


def load_schema():
    with open(str(SCHEMA_PATH), encoding="utf-8") as f:
        return json.load(f)


def discover_manifests():
    if not TOOLS_DIR.is_dir():
        return []
    return sorted(
        p for p in TOOLS_DIR.glob("*/tool.yaml") if p.parent.name != "_template"
    )


def validate_layout(tool_dir, manifest):
    errors = []
    tool_id = manifest.get("id")
    if tool_id and tool_dir.name != tool_id:
        errors.append(
            "{}: directory name '{}' != id '{}'".format(tool_dir, tool_dir.name, tool_id)
        )

    kinds = manifest.get("kind", [])
    ci = manifest.get("ci", {})
    if ci.get("docker_build"):
        docker_dir = tool_dir / "docker"
        if not docker_dir.is_dir():
            errors.append("{}: ci.docker_build=true but docker/ missing".format(tool_dir))
        elif not (docker_dir / "Makefile").is_file():
            errors.append("{}: docker/Makefile missing".format(tool_dir))

    if "docker_cli" in kinds or "docker_api" in kinds:
        if not manifest.get("execution", {}).get("docker", {}).get("image"):
            errors.append("{}: docker kind requires execution.docker.image".format(tool_dir))

    if not (tool_dir / "README.md").is_file():
        errors.append("{}: README.md missing".format(tool_dir))

    return errors


def main():
    schema = load_schema()
    if hasattr(jsonschema, "Draft7Validator"):
        validator = jsonschema.Draft7Validator(schema)
    elif hasattr(jsonschema, "Draft4Validator"):
        validator = jsonschema.Draft4Validator(schema)
    else:
        validator = jsonschema.Validator(schema)
    manifests = discover_manifests()

    if not manifests:
        print("No tool manifests found under tools/*/tool.yaml", file=sys.stderr)
        return 1

    errors = []
    for path in manifests:
        with open(str(path), encoding="utf-8") as f:
            data = yaml.safe_load(f)
        errors.extend(
            "{}: {}: {}".format(path, ".".join(str(p) for p in err.path) or "(root)", err.message)
            for err in validator.iter_errors(data)
        )
        errors.extend(validate_layout(path.parent, data))

    if errors:
        print("Catalog validation failed:", file=sys.stderr)
        for err in errors:
            print("  - {}".format(err), file=sys.stderr)
        return 1

    print("Validated {} tool manifest(s).".format(len(manifests)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
