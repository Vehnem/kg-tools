#!/bin/bash
# Nutzung:
# ./pyjedai.sh infile1 infile2 outputfile [config] [gt] [separator] [attr1] [attr2]

IN1=$1
IN2=$2
OUT=$3
CONFIG=$4
GT=$5
SEP=${6:-"|"}
ATTR1=$7
ATTR2=$8

echo "\n"
echo "Source-File Path: $IN1"
echo "Target-File Path: $IN2"
echo "Output Path: $OUT"
echo "Seperator: $SEP"

CMD="python run_pipeline.py \
    --file1 \"$IN1\" \
    --file2 \"$IN2\" \
    --sep \"$SEP\" \
    --output \"$OUT\""

if [ -n "$GT" ]; then
    CMD="$CMD --gt \"$GT\""
    echo "Ground-Truth Path: $GT"
fi

if [ -n "$CONFIG" ]; then
    CMD="$CMD --config \"$CONFIG\""
    echo "Config Path: $CONFIG"
fi

if [ -n "$ATTR1" ]; then
    CMD="$CMD --attr1 \"$ATTR1\""
    echo "Blocking Attributes 2: $ATTR2"
fi

if [ -n "$ATTR2" ]; then
    CMD="$CMD --attr2 \"$ATTR2\""
    echo "Blocking Attributes 2: $ATTR2"
fi

echo "\n"
eval $CMD