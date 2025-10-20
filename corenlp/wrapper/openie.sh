#!/usr/bin/env bash

IN=$1
OUT=$2

echo java -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLP -annotators tokenize,ssplit,pos,lemma,ner,depparse,natlog,coref,openie -filelist $(bash ./util_filelistfile.sh $IN) -outputFormat json -outputDirectory $OUT
java -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLP -annotators tokenize,ssplit,pos,lemma,ner,depparse,natlog,coref,openie -filelist $(bash ./util_filelistfile.sh $IN) -outputFormat json -outputDirectory $OUT
