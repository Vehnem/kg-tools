#!/bin/bash
# bash pyjedai_wrapper.sh path/to/infile1 path/to/infile2 path/to/outputfile

IN1=$1
IN2=$2
OUT=$3

echo $OUT | python valentine_example.py $IN1 $IN2 $OUT
