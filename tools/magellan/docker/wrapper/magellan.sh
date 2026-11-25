#!/usr/bin/env bash
# magellan.sh — thin wrapper around run_magellan.py using the project venv.
#
# Usage:
#   ./magellan.sh <ltable.csv> <rtable.csv> <output_dir> <config.yaml> [labeled_data.csv]
#
# Example:
#   ./magellan.sh data/ltable.csv data/rtable.csv out/ config-example.yaml data/labeled.csv

set -euo pipefail

if [ "$#" -lt 4 ] || [ "$#" -gt 5 ]; then
  echo "Usage: $0 <ltable.csv> <rtable.csv> <output_dir> <config.yaml> [labeled_data.csv]" >&2
  exit 1
fi

LTABLE="$1"
RTABLE="$2"
OUTPUT_DIR="$3"
CONFIG_FILE="$4"
LABELED_DATA="${5:-}"

ARGS=(
  --ltable "${LTABLE}"
  --rtable "${RTABLE}"
  --output "${OUTPUT_DIR}"
  --config "${CONFIG_FILE}"
)

if [ -n "${LABELED_DATA}" ]; then
  ARGS+=(--labeled-data "${LABELED_DATA}")
fi

exec python run_magellan.py "${ARGS[@]}"