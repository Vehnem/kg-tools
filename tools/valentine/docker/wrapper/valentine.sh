#!/bin/bash
# bash valentine.sh path/to/source.csv path/to/target.csv path/to/output_dir path/to/config.yaml [path/to/mapping.json]

set -euo pipefail

if [ "$#" -lt 4 ]; then
    echo "Usage: bash valentine.sh <source.csv> <target.csv> <output_dir> <config.yaml> [mapping.json]" >&2
    exit 1
fi

SOURCE=$1
TARGET=$2
OUT=$3
CONFIG=$4

if [ -n "${5:-}" ]; then
    python valentine_example.py "$SOURCE" "$TARGET" "$OUT" "$CONFIG" "$5"
else
    python valentine_example.py "$SOURCE" "$TARGET" "$OUT" "$CONFIG"
fi