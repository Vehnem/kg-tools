#!/bin/bash
# bash pyjedai.sh path/to/infile1 path/to/infile2 path/to/gt path/to/outputfile

IN1=$1
IN2=$2
GT=$3
OUT=$4

echo $OUT | python cleanclean.py --file1 $IN1 --file2 $IN2 --gt $GT --output $OUT
