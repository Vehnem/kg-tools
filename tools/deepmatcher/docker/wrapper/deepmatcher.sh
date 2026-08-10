#!/bin/bash
# Usage:
#   bash deepmatcher.sh path/to/data_dir train.csv validation.csv test.csv \
#       path/to/best_model.pth path/to/unlabeled.csv path/to/output.csv [path/to/config.yaml]

if [ "$#" -lt 6 ]; then
  echo "Usage: bash deepmatcher.sh <data_dir> <train.csv> <validation.csv> <test.csv> <best_model.pth> <unlabeled.csv> <output.csv> [config.yaml]" >&2
  exit 1
fi

DATA_DIR=$1
TRAIN=$2
VALID=$3
TEST=$4
BEST_MODEL=$5
UNLABELED=$6
OUTPUT=$7
CONFIG=${8:-}

CMD=(
  python run_deepmatcher.py
  --data_directory "$DATA_DIR"
  --train_csv "$TRAIN"
  --validation_csv "$VALID"
  --test_csv "$TEST"
  --best_model "$BEST_MODEL"
  --unlabeled_csv "$UNLABELED"
  --output "$OUTPUT"
)

if [ -n "$CONFIG" ]; then
  CMD+=(--config "$CONFIG")
fi

"${CMD[@]}"