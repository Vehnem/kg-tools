#!/usr/bin/env bash

IN=$1
OUT=$2

java -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLP -annotators tokenize,pos,lemma,ner,parse,coref,kbp -coref.md.type RULE -fileList $(bash ./util_filelistfile.sh $IN) -outputFormat json -outputDirectory $OUT
