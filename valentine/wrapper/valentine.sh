#!/bin/bash
# bash valentine.sh path/to/infile1 path/to/infile2 path/to/outputfile

IN1=$1
IN2=$2
OUT=$3


if [ -n "$4" ]; then
    python valentine_example.py "$IN1" "$IN2" "$OUT" "$4"
else
    python valentine_example.py "$IN1" "$IN2" "$OUT"
fi

