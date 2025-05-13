#!/bin/bash
# bash paris_wrapper.sh path/to/infile1 path/to/infile2 path/to/outputfolder

IN1=$1
IN2=$2
OUT=$3

CONF=settings.ini

echo "endIteration=20" > $CONF
echo "factstore1=$IN1" >> $CONF
echo "factstore2=$IN2" >> $CONF
echo "resultTSV=$OUT" >> $CONF
echo "home=$OUT" >> $CONF

mkdir -p $OUT
echo $OUT | java -jar *.jar settings.ini
