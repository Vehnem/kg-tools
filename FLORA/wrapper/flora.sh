#!/bin/bash
# bash flora.sh path/to/kb1 path/to/kb2 path/to/outputfolder

IN1=$1
IN2=$2
OUTPUT=$3

echo $OUTPUT | python FLORA/src/main.py --kb1 $IN1 --kb2 $IN2 --save_dir $OUTPUT
