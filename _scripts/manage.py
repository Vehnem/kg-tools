#!/usr/bin/env python3
"""Contributor CLI for catalog validation, generation, and Docker checks."""

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "_scripts"


def run(*command):
    """Run a repository command and return its exit status."""
    completed = subprocess.run(command, cwd=str(REPO_ROOT))
    return completed.returncode


def main():
    parser = argparse.ArgumentParser(
        description="Maintain and test the kg-tools catalog."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate", help="validate every tool.yaml manifest")
    subparsers.add_parser(
        "check", help="run the fast checks used by catalog validation CI"
    )

    for command in ("build", "test"):
        command_parser = subparsers.add_parser(
            command, help="{} selected Docker tools".format(command)
        )
        command_parser.add_argument(
            "tools",
            nargs="*",
            metavar="TOOL",
            help="tool ids; omit to use tools enabled for this operation in tool.yaml",
        )

    generate_parser = subparsers.add_parser(
        "generate", help="regenerate derived repository files"
    )
    generate_parser.add_argument("artifact", choices=("readme", "pages", "ci", "all"))

    subparsers.add_parser(
        "kgpipe-test",
        help="run KGpipe task pytest cases locally and write catalog/reports/kgpipe-tasks.json",
    )

    args = parser.parse_args()
    python = sys.executable

    if args.command == "validate":
        return run(python, str(SCRIPTS_DIR / "validate_catalog.py"))
    if args.command == "check":
        status = run(python, str(SCRIPTS_DIR / "validate_catalog.py"))
        if status:
            return status
        for script in ("gen_readme.py", "gen_pages.py"):
            status = run(python, str(SCRIPTS_DIR / script), "--check")
            if status:
                return status
        return 0
    if args.command in ("build", "test"):
        return run(str(SCRIPTS_DIR / args.command), *args.tools)
    if args.command == "generate":
        if args.artifact in ("readme", "all"):
            status = run(python, str(SCRIPTS_DIR / "gen_readme.py"))
            if status:
                return status
        if args.artifact in ("pages", "all"):
            status = run(python, str(SCRIPTS_DIR / "gen_pages.py"))
            if status:
                return status
        if args.artifact in ("ci", "all"):
            return run(python, str(SCRIPTS_DIR / "gen_ci.py"))
        return 0
    if args.command == "kgpipe-test":
        return run(
            python,
            "-m",
            "pytest",
            "tests/kgpipe",
            "-m",
            "kgpipe",
            "-o",
            "addopts=",
        )

    parser.error("unknown command")


if __name__ == "__main__":
    sys.exit(main())
