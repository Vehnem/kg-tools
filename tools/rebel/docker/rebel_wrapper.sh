#!/bin/bash
# bash rebel_wrapper.sh path/to/infile1 path/to/outputfile

IN=$1
OUT=$2

echo $OUT | python testrebel.py --file $IN --output $OUT
