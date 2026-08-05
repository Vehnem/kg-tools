#!/bin/bash
# bash ontoea.sh /path/to/args_file /path/to/benchmark /path/to/splits

IN1=$1
IN2=$2
IN3=$3

python main_from_args.py "$IN1""$IN2" "$IN3"