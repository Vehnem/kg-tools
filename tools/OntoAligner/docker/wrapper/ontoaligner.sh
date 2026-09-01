#!/bin/bash
# Usage:
#   bash ontoaligner.sh path/to/source.owl path/to/target.owl path/to/output_dir \
#       path/to/config.yaml [method]

if [ "$#" -lt 4 ]; then
  echo "Usage: bash ontoaligner.sh <source.owl> <target.owl> <output_dir> <config.yaml> [method]" >&2
  exit 1
fi

SOURCE=$1
TARGET=$2
OUTPUT_DIR=$3
CONFIG=$4
METHOD=${5:-}

CMD=(
  python run_ontoaligner.py
  --config "$CONFIG"
  --source "$SOURCE"
  --target "$TARGET"
  --output-dir "$OUTPUT_DIR"
)

if [ -n "$METHOD" ]; then
  CMD+=(--method "$METHOD")
fi

"${CMD[@]}"