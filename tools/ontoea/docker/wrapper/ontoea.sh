#!/usr/bin/env bash
# ontoea.sh — thin wrapper around run_ontoea.py.
#
# Usage:
#   bash ontoea.sh <benchmark_dir> <output_dir> <config.yaml>
#
# Example:
#   bash ontoea.sh /data/MED_BBK_9K /out config-example.yaml

set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <benchmark_dir> <output_dir> <config.yaml>" >&2
  exit 1
fi

exec python run_ontoea.py --input "$1" --output "$2" --config "$3"
