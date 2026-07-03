#!/usr/bin/env bash
# Legacy wrapper — generates .gitlab-ci.yml from catalog (deprecated).
# Prefer: python _scripts/gen_ci.py for GitHub Actions.

set -euo pipefail
echo "Note: gen_ci.sh is deprecated. Use: python _scripts/gen_ci.py" >&2
exec python3 "$(dirname "$0")/gen_ci.py"
