#!/usr/bin/env bash
# magellan.sh — thin wrapper around run_magellan.py using the project venv.
#
# Usage:
#   ./magellan.sh <input_dir> <output_dir> <config.yaml>
#
# Example:
#   ./magellan.sh data/ out/ config-example.yaml

set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <input_dir> <output_dir> <config.yaml>" >&2
  exit 1
fi

INPUT_DIR="$1"
OUTPUT_DIR="$2"
CONFIG_FILE="$3"

exec python run_magellan.py \
  --input "${INPUT_DIR}" \
  --output "${OUTPUT_DIR}" \
  --config "${CONFIG_FILE}"
