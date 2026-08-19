#!/usr/bin/env python3
"""Generate README.md tool catalog tables from tools/*/tool.yaml manifests."""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
README_PATH = REPO_ROOT / "README.md"

README_HEADER = """# kg-tools — Knowledge Graph Integration Tool Catalog

> A curated collection of tools for knowledge graph data integration: Dockerized CLIs, utilities, and visualization assets.

## Quick start

```bash
git clone https://github.com/vehnem/kg-tools.git
cd kg-tools
```

Each dockerized tool lives under `tools/<id>/docker/` with `make docker_build`, `make docker_test`, and `make docker_help`.

Validate the catalog:

```bash
pip install -r _scripts/requirements.txt
python _scripts/validate_catalog.py
```

## Tool catalog

<!-- CATALOG-START -->
"""

README_FOOTER = """<!-- CATALOG-END -->

## Repository layout

```
kg-tools/
  catalog/           # JSON schema and category taxonomy
  tools/<id>/        # One directory per tool
    tool.yaml        # Machine-readable catalog entry
    README.md        # Usage documentation
    docker/          # Docker build context (when applicable)
  _scripts/          # Maintenance CLI and supporting scripts (see _scripts/README.md)
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

Repository maintenance commands are documented in [_scripts/README.md](_scripts/README.md).

## License

MIT — see [LICENSE](LICENSE).
"""


def load_manifests():
    manifests = []
    for path in sorted(TOOLS_DIR.glob("*/tool.yaml")):
        if path.parent.name == "_template":
            continue
        with open(str(path), encoding="utf-8") as f:
            data = yaml.safe_load(f)
        data["_path"] = path.parent
        manifests.append(data)
    return manifests


def format_kgpipe_refs(manifest):
    refs = manifest.get("kgpipe", {}).get("task_refs", [])
    return ", ".join("`{}`".format(r) for r in refs) if refs else "—"


def format_docker_image(manifest):
    docker = manifest.get("execution", {}).get("docker", {})
    if not docker:
        return "—"
    image = docker.get("image", "")
    tag = docker.get("tag", "latest")
    return "`{}:{}`".format(image, tag) if image else "—"


def generate_tables(manifests):
    by_category = defaultdict(list)
    for m in manifests:
        for cat in m.get("categories", ["DatasetUtility"]):
            by_category[cat].append(m)

    lines = []
    for category in sorted(by_category):
        lines.append("### {}\n".format(category))
        lines.append("| Tool | Kind | Status | Docker image | KGpipe task refs |")
        lines.append("|------|------|--------|--------------|------------------|")
        for m in sorted(by_category[category], key=lambda x: x["id"]):
            kinds = ", ".join(m.get("kind", []))
            lines.append(
                "| [{name}](tools/{id}/README.md) "
                "| {kinds} | {status} "
                "| {docker} | {refs} |".format(
                    name=m["name"],
                    id=m["id"],
                    kinds=kinds,
                    status=m["status"],
                    docker=format_docker_image(m),
                    refs=format_kgpipe_refs(m),
                )
            )
        lines.append("")
    return "\n".join(lines)


def render_readme(manifests):
    return README_HEADER + generate_tables(manifests) + README_FOOTER


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()

    manifests = load_manifests()
    if not manifests:
        print("No manifests found.", file=sys.stderr)
        return 1

    content = render_readme(manifests)

    if args.stdout:
        print(content, end="")
        return 0

    if args.check:
        current = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""
        if current != content:
            print("README.md is out of date. Run: python _scripts/gen_readme.py", file=sys.stderr)
            return 1
        print("README.md is up to date.")
        return 0

    with open(str(README_PATH), "w", encoding="utf-8") as f:
        f.write(content)
    print("Wrote {} ({} tools).".format(README_PATH, len(manifests)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
