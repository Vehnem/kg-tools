#!/usr/bin/env bash

FILE=$1
LISTFILE="$(mktemp)"

if [[ -d $FILE ]]; then
    echo "$FILE is a directory"
    find $FILE -type f -name "*.txt" > $LISTFILE
elif [[ -f $FILE ]]; then
    echo "$FILE is a file"
    echo $FILE > $LISTFILE
else
    echo "$FILE is not valid"
    exit 1
fi

cat $LISTFILE

java -mx1g -cp "*" edu.stanford.nlp.naturalli.OpenIE --format ollie --filelist $LISTFILE --output $2