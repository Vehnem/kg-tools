#!/bin/bash
# bash pyjedai.sh path/to/infile1 path/to/infile2 path/to/outputfile

IN1=$1
IN2=$2
OUT=$3

echo $OUT | python cleanclean.py --file1 $IN1 --file2 $IN2 --output $OUT
