#!/bin/bash
# Usage:
# ./ditto.sh infile outfile config

IN=$1
OUT=$2
CONFIG=$3

echo "\n"
echo "Input Path: $IN"
echo "Output Path: $OUT"
echo "Config Path: $CONFIG"

CMD="python run_ditto.py \
    --config \"$CONFIG\""

if [ -n "$IN" ]; then
    CMD="$CMD --input \"$IN\""
fi

if [ -n "$OUT" ]; then
    CMD="$CMD --output \"$OUT\""
fi

echo "\n"
eval $CMD