#!/bin/bash

KG_FILE="$1"
ONTOLOGY_FILE="$2"
OUTPUT_DIR="$3"

if [ ! -f "$KG_FILE" ]; then
  echo "Knowledge graph file not found: $KG_FILE"
  exit 1
fi

if [ ! -f "$ONTOLOGY_FILE" ]; then
  echo "Ontology file not found: $ONTOLOGY_FILE"
  exit 1
fi

/RDFUnit/bin/rdfunit \
  -d "$KG_FILE" \
  -s "$ONTOLOGY_FILE" \
  -r aggregate

cp -r ./data/results/. "$OUTPUT_DIR"
