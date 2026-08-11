#!/bin/bash
# bash paris.sh path/to/settings.ini path/to/infile1 path/to/infile2 path/to/outputfolder

SETTINGS=$1
IN1=$2
IN2=$3
OUT=$4

CONF=$(mktemp)
trap 'rm -f "$CONF"' EXIT

cp "$SETTINGS" "$CONF"

mkdir -p "$OUT"

{
  echo "factstore1=$IN1"
  echo "factstore2=$IN2"
  echo "resultTSV=$OUT"
  echo "home=$OUT"
} >> "$CONF"

JAR=${PARIS_JAR:-}
if [ -z "$JAR" ]; then
  JAR=$(ls ./*.jar 2>/dev/null | head -n1)
fi
if [ -z "$JAR" ]; then
  echo "No PARIS jar found." >&2
  exit 1
fi

echo "$OUT" | java -jar "$JAR" "$CONF"
