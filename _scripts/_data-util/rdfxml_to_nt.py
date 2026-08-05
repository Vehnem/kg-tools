#!/usr/bin/env python3

from rdflib import Graph
import sys
import os


def rdfxml_to_ntriples(input_file, output_file):
    g = Graph()

    print(f"Lese {input_file} ...")
    g.parse(input_file, format="xml")

    print(f"Gefundene Tripel: {len(g)}")

    print(f"Schreibe {output_file} ...")
    g.serialize(
        destination=output_file,
        format="nt"
    )

    print("Fertig!")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            f"Usage: {sys.argv[0]} input.rdf output.nt"
        )
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    if not os.path.exists(input_file):
        print(f"Datei nicht gefunden: {input_file}")
        sys.exit(1)

    rdfxml_to_ntriples(input_file, output_file)