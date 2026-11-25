#!/usr/bin/env python3
"""
alignment_rdf_to_csv.py

Converts reference alignments in Alignment API format (RDF/XML, <Alignment><map><Cell>...)
into CSV/TSV format. Works, among others, with OAEI Anatomy (reference.rdf, trivial.rdf),
OAEI Conference (cmt-edas.rdf, ...) and the OAEI Knowledge Graph Track (*-reference.xml).

Output columns:
    pair, src_uri, tgt_uri, relation, measure
and, if ontologies are provided (validation):
    src_type, tgt_type, src_in_onto, tgt_in_onto

Examples
--------

# Conference: directory containing 21 reference alignments -> one CSV, validated against the OWL files
python alignment_rdf_to_csv.py conference/reference-alignment \
    -o conference_gold.csv --ontologies conference/ontologies

# Anatomy: single file, explicitly specify the ontologies
python alignment_rdf_to_csv.py anatomy/reference.rdf -o anatomy_gold.tsv \
    --delimiter tab --source-onto anatomy/mouse.owl --target-onto anatomy/human.owl

# Alignments only, no validation, equivalence ('=') only
python alignment_rdf_to_csv.py anatomy/trivial.rdf -o anatomy_trivial.csv --only-equivalence

Note: Validation requires rdflib (pip install rdflib). Without --ontologies /
--source-onto, rdflib is not required (only the Python standard library is used).

The filename convention 'A-B.rdf' (Conference) is used for --ontologies:
A and B are searched for as A.owl / B.owl (case-insensitive).
"""

import argparse
import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDF_RESOURCE = f"{{{RDF_NS}}}resource"
RDF_ABOUT = f"{{{RDF_NS}}}about"


def local(tag: str) -> str:
    """Return the local name of an XML tag without its namespace."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def child_by_local(elem, name):
    for ch in elem:
        if local(ch.tag) == name:
            return ch
    return None


def uri_of(elem):
    if elem is None:
        return None
    val = elem.get(RDF_RESOURCE) or elem.get(RDF_ABOUT)
    return val.strip() if val else None


def parse_alignment(path: Path):
    """Read an Alignment API file and return a list of dictionaries."""
    root = ET.parse(path).getroot()
    cells = []
    for cell in root.iter():
        if local(cell.tag) != "Cell":
            continue
        e1 = uri_of(child_by_local(cell, "entity1"))
        e2 = uri_of(child_by_local(cell, "entity2"))
        if not e1 or not e2:
            continue
        rel = child_by_local(cell, "relation")
        meas = child_by_local(cell, "measure")
        cells.append({
            "src_uri": e1,
            "tgt_uri": e2,
            "relation": (rel.text or "").strip() if rel is not None else "",
            "measure": (meas.text or "").strip() if meas is not None else "",
        })
    return cells


# ---------------------------------------------------------------- Validation

class Ontology:
    """Stores the URI set and types of an ontology (via rdflib)."""

    TYPE_MAP = {
        "Class": "class",
        "ObjectProperty": "object_property",
        "DatatypeProperty": "data_property",
        "AnnotationProperty": "annotation_property",
        "Property": "property",
    }

    def __init__(self, path: Path):
        try:
            from rdflib import Graph, URIRef, RDF, RDFS, OWL
        except ImportError:
            sys.exit("rdflib is required for validation: pip install rdflib")
        g = Graph()
        g.parse(str(path))  # Format is inferred from the file extension / content
        self.uris = set()
        for s, p, o in g:
            if isinstance(s, URIRef):
                self.uris.add(str(s))
            if isinstance(o, URIRef):
                self.uris.add(str(o))
        self.types = {}
        type_nodes = {
            OWL.Class: "class", RDFS.Class: "class",
            OWL.ObjectProperty: "object_property",
            OWL.DatatypeProperty: "data_property",
            OWL.AnnotationProperty: "annotation_property",
            RDF.Property: "property",
        }
        for node, label in type_nodes.items():
            for s in g.subjects(RDF.type, node):
                if isinstance(s, URIRef):
                    self.types.setdefault(str(s), label)

    def has(self, uri):
        return uri in self.uris

    def type_of(self, uri):
        return self.types.get(uri, "unknown" if uri in self.uris else "")


def find_ontology_file(onto_dir: Path, name: str):
    wanted = name.lower()
    for p in onto_dir.iterdir():
        if p.is_file() and p.suffix.lower() in {".owl", ".rdf", ".xml", ".ttl", ".nt"} \
                and p.stem.lower() == wanted:
            return p
    return None


def split_pair_name(stem: str):
    """'cmt-confOf' -> ('cmt', 'confOf'). Returns None if the name is ambiguous."""
    parts = stem.split("-")
    return (parts[0], parts[1]) if len(parts) == 2 else None


# ------------------------------------------------------------------------ Main

def main():
    ap = argparse.ArgumentParser(
        description="Convert Alignment API RDF (reference alignments) to CSV/TSV.")
    ap.add_argument("input", help="Alignment file or directory containing alignment files")
    ap.add_argument("-o", "--output", required=True, help="Output file (CSV/TSV)")
    ap.add_argument("--delimiter", choices=["comma", "tab"], default="comma")
    ap.add_argument("--ext", default=".rdf,.xml",
                    help="File extensions when using a directory as input, comma-separated (default: .rdf,.xml)")
    ap.add_argument("--only-equivalence", action="store_true",
                    help="Keep only cells with relation '='")
    ap.add_argument("--ontologies",
                    help="Directory containing OWL files (filename convention A-B.rdf -> A.owl, B.owl)")
    ap.add_argument("--source-onto", help="Source ontology (for a single file)")
    ap.add_argument("--target-onto", help="Target ontology (for a single file)")
    args = ap.parse_args()

    inp = Path(args.input)
    if inp.is_dir():
        exts = {e.strip().lower() for e in args.ext.split(",")}
        files = sorted(p for p in inp.iterdir() if p.is_file() and p.suffix.lower() in exts)
    elif inp.is_file():
        files = [inp]
    else:
        sys.exit(f"Input not found: {inp}")
    if not files:
        sys.exit("No alignment files found.")

    validate = bool(args.ontologies or args.source_onto or args.target_onto)
    onto_cache = {}

    def load(path: Path):
        if path not in onto_cache:
            onto_cache[path] = Ontology(path)
        return onto_cache[path]

    fields = ["pair", "src_uri", "tgt_uri", "relation", "measure"]
    if validate:
        fields += ["src_type", "tgt_type", "src_in_onto", "tgt_in_onto"]

    delim = "\t" if args.delimiter == "tab" else ","
    total = 0
    missing_total = 0
    per_pair = []

    with open(args.output, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter=delim)
        w.writeheader()
        for f in files:
            cells = parse_alignment(f)
            if args.only_equivalence:
                cells = [c for c in cells if c["relation"] == "="]

            src_o = tgt_o = None
            if validate:
                if args.source_onto and args.target_onto:
                    src_o, tgt_o = load(Path(args.source_onto)), load(Path(args.target_onto))
                elif args.ontologies:
                    names = split_pair_name(f.stem)
                    odir = Path(args.ontologies)
                    if names:
                        ps = find_ontology_file(odir, names[0])
                        pt = find_ontology_file(odir, names[1])
                        if ps and pt:
                            src_o, tgt_o = load(ps), load(pt)
                    if src_o is None:
                        print(f"[WARN] No ontologies found for {f.name}; skipping validation.",
                              file=sys.stderr)
                else:
                    sys.exit("When using --source-onto, --target-onto must also be specified.")

            miss = 0
            for c in cells:
                row = {"pair": f.stem, **c}
                if validate:
                    if src_o is not None:
                        row["src_in_onto"] = src_o.has(c["src_uri"])
                        row["tgt_in_onto"] = tgt_o.has(c["tgt_uri"])
                        row["src_type"] = src_o.type_of(c["src_uri"])
                        row["tgt_type"] = tgt_o.type_of(c["tgt_uri"])
                        if not (row["src_in_onto"] and row["tgt_in_onto"]):
                            miss += 1
                    else:
                        row.update(src_type="", tgt_type="", src_in_onto="", tgt_in_onto="")
                w.writerow(row)
            total += len(cells)
            missing_total += miss
            per_pair.append((f.stem, len(cells), miss))

    print(f"{len(files)} file(s), {total} cells -> {args.output}")
    for name, n, m in per_pair:
        extra = f"  (URIs not found in ontology: {m})" if validate and m else ""
        print(f"  {name}: {n}{extra}")
    if validate and missing_total:
        print(f"[WARN] {missing_total} cells contain URIs that do not occur in the ontologies. "
              "Check namespaces / file mappings.", file=sys.stderr)


if __name__ == "__main__":
    main()