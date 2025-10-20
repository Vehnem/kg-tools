#!/bin/bash
# bash agreementmaker.sh path/to/infile1 path/to/infile2 path/to/outputfile

IN1=$1
IN2=$2
OUT=$3

echo $OUT | java -jar AgreementMakerLight.jar -a -s $IN1 -t $IN2 -o $OUT