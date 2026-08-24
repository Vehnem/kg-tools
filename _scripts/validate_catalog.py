#!/usr/bin/env python3
"""Validate all tools/*/tool.yaml manifests against the JSON schema."""

import json
import sys
from pathlib import Path

import jsonschema
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from kgpipe_catalog import TEST_SCHEMA_PATH, iter_kgpipe_test_files, load_test_case  # noqa: E402

SCHEMA_PATH = REPO_ROOT / "catalog" / "schema" / "tool.schema.json"
TOOLS_DIR = REPO_ROOT / "tools"


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


def make_validator(schema):
    if hasattr(jsonschema, "Draft7Validator"):
        return jsonschema.Draft7Validator(schema)
    if hasattr(jsonschema, "Draft4Validator"):
        return jsonschema.Draft4Validator(schema)
    return jsonschema.Validator(schema)


def validate_kgpipe_tests(errors):
    if not TEST_SCHEMA_PATH.is_file():
        return
    with open(str(TEST_SCHEMA_PATH), encoding="utf-8") as f:
        schema = json.load(f)
    validator = make_validator(schema)
    for path in iter_kgpipe_test_files():
        with open(str(path), encoding="utf-8") as f:
            data = yaml.safe_load(f)
        errors.extend(
            "{}: {}: {}".format(
                path, ".".join(str(p) for p in err.path) or "(root)", err.message
            )
            for err in validator.iter_errors(data)
        )
        case = load_test_case(path)
        for slot, relative in case["inputs"].items():
            source = path.parent / relative
            if not source.is_file():
                errors.append("{}: missing input '{}' file {}".format(path, slot, source))
        for slot, relative in case["outputs"].items():
            expected = path.parent / relative
            if not expected.exists():
                errors.append(
                    "{}: missing output fixture '{}' path {}".format(path, slot, expected)
                )


def main():
    with open(str(SCHEMA_PATH), encoding="utf-8") as f:
        schema = json.load(f)
    validator = make_validator(schema)
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

    validate_kgpipe_tests(errors)

    if errors:
        print("Catalog validation failed:", file=sys.stderr)
        for err in errors:
            print("  - {}".format(err), file=sys.stderr)
        return 1

    print("Validated {} tool manifest(s).".format(len(manifests)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
