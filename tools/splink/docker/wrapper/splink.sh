#!/bin/bash
# Usage:
#   bash splink.sh path/to/left.csv path/to/right.csv path/to/output.csv \
#       path/to/config.yaml [threshold]

if [ "$#" -lt 4 ]; then
  echo "Usage: bash splink.sh <left.csv> <right.csv> <output.csv> <config.yaml> [threshold]" >&2
  exit 1
fi

LEFT=$1
RIGHT=$2
OUTPUT=$3
CONFIG=$4
THRESHOLD=${5:-}

CMD=(
  python run_splink.py
  --input "$LEFT"
  --input2 "$RIGHT"
  --output "$OUTPUT"
  --config "$CONFIG"
)

if [ -n "$THRESHOLD" ]; then
  CMD+=(--threshold "$THRESHOLD")
fi

"${CMD[@]}"