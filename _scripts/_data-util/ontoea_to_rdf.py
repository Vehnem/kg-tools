#!/usr/bin/env python3
"""
ontoea_to_rdf.py

Wandelt ein Dataset im OntoEA-Format (z. B. D_W_15K_V2_A) in vier Teile um:

    ontology   Klassenhierarchie, Disjunktheit, Labels      (ontology.nt)
    source     KG 1: rel_triples_1 + attr_triples_1 + Typen (source.nt)
    target     KG 2: rel_triples_2 + attr_triples_2 + Typen (target.nt)
    reference  Gold-Standard (ent_links) + Folds (TSV, optional Alignment-API-XML)

Ausgabestruktur:
    out/
      ontology.nt
      source.nt
      target.nt
      reference/
        all.tsv                  (alle ent_links)
        fold1/{train,valid,test}.tsv  ... fold5/
      stats.json                 (Zaehlungen fuer das Profiling)

Beispiele
---------
python ontoea_to_rdf.py D_W_15K_V2/D_W_15K_V2_A -o converted/D_W_15K_V2_A
python ontoea_to_rdf.py D_W_15K_V2/D_W_15K_V2_A -o converted/D_W_15K_V2_A \\
    --formats nt,xml --alignment-xml          # zusaetzlich RDF/XML (z. B. fuer AML/LogMap)
python ontoea_to_rdf.py ... --merge-ontology  # Ontologie in source.nt und target.nt einbetten

Hinweise
--------
* Standard-Ausgabe ist N-Triples (schnell, streamend). Turtle/RDF-XML entstehen per rdflib
  (pip install rdflib) und brauchen mehr Speicher.
* Die Ontologie (DBpedia-Klassen) ist fuer beide KGs gemeinsam, beide KGs sind mit diesen
  Klassen getypt (crossview_link_1/2). Mit --merge-ontology teilen source und target daher
  dieselben Klassen-URIs: Klassen-Alignment ist dann trivial. Standard: nicht einbetten.
* Literale in attr_triples (unquotiert, "..."^^<dt> oder "..."@lang) werden zu
  gueltigen N-Triples-Literalen normalisiert.
"""

import argparse
import json
import re
import sys
from pathlib import Path

RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
OWL = "http://www.w3.org/2002/07/owl#"
OWL_CLASS = OWL + "Class"
OWL_THING = OWL + "Thing"
OWL_OBJ_PROP = OWL + "ObjectProperty"
OWL_DATA_PROP = OWL + "DatatypeProperty"
OWL_INDIVIDUAL = OWL + "NamedIndividual"

BAD_IRI_CHARS = re.compile(r'[\x00-\x20<>"{}|\\^`]')
LITERAL_RE = re.compile(r'^"(.*)"(?:\^\^<([^>]+)>|@([A-Za-z]+(?:-[A-Za-z0-9]+)*))?$', re.S)
IRI_IN_LINE = re.compile(r"<([^>]+)>")


# ------------------------------------------------------------------ Hilfsfunktionen

def iri(s: str) -> str:
    """URI als N-Triples-IRI ausgeben, unzulaessige Zeichen werden prozentkodiert."""
    s = s.strip()
    if s.startswith("<") and s.endswith(">"):
        s = s[1:-1]
    return "<" + BAD_IRI_CHARS.sub(lambda m: "%%%02X" % ord(m.group()), s) + ">"


def esc(text: str) -> str:
    return (text.replace("\\", "\\\\").replace('"', '\\"')
            .replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t"))


def literal(obj: str) -> str:
    """attr_triples-Objekt zu N-Triples-Literal."""
    obj = obj.strip()
    m = LITERAL_RE.match(obj)
    if m:
        lex, dt, lang = m.groups()
        out = '"' + esc(lex) + '"'
        if dt:
            out += "^^" + iri(dt)
        elif lang:
            out += "@" + lang
        return out
    return '"' + esc(obj) + '"'


def read_tsv(path: Path, ncols: int, stats: dict, key: str):
    """Liest eine tab-separierte Datei, zaehlt unbrauchbare Zeilen in stats[key]."""
    rows, bad = [], 0
    if not path.exists():
        sys.exit(f"Datei fehlt: {path}")
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\r\n")
            if not line.strip():
                continue
            parts = line.split("\t", ncols - 1)
            if len(parts) < ncols or any(not p.strip() for p in parts):
                bad += 1
                continue
            rows.append(tuple(parts))
    stats[key] = {"rows": len(rows), "skipped_bad_lines": bad}
    if bad:
        print(f"[WARN] {path.name}: {bad} unbrauchbare Zeilen uebersprungen", file=sys.stderr)
    return rows


def triple(f, s, p, o):
    f.write(f"{s} {p} {o} .\n")


# ------------------------------------------------------------------------ Bausteine

def build_ontology(d: Path, out_path: Path, class_path: dict, extra_classes: set, stats: dict):
    classes = set(extra_classes)
    for k, vals in class_path.items():
        classes.add(k)
        classes.update(vals)
    counts = {}
    with open(out_path, "w", encoding="utf-8") as out:
        for fname, take in [("onto_subClassOf_triples", (0, 2)),
                            ("onto_disjointWith_triples", (0, 2)),
                            ("onto_attr_triples", (0,))]:
            n = 0
            with open(d / fname, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if not line.endswith("."):
                        line += " ."
                    out.write(line + "\n")
                    iris = IRI_IN_LINE.findall(line)
                    for i in take:
                        if i < len(iris):
                            classes.add(iris[i])
                    n += 1
            counts[fname] = n
        classes.discard(OWL_THING)
        for c in sorted(classes):
            triple(out, iri(c), iri(RDF_TYPE), iri(OWL_CLASS))
    stats["ontology"] = {"classes": len(classes), **counts}


def build_kg(d: Path, idx: int, out_path: Path, class_path: dict, declare: bool,
             materialize: bool, stats: dict):
    name = f"kg{idx}"
    rel = read_tsv(d / f"rel_triples_{idx}", 3, stats, f"{name}_rel_input")
    attr = read_tsv(d / f"attr_triples_{idx}", 3, stats, f"{name}_attr_input")
    types = read_tsv(d / f"crossview_link_{idx}", 2, stats, f"{name}_types_input")

    ents, rel_preds, attr_preds, used_classes = set(), set(), set(), set()
    n_triples = 0
    with open(out_path, "w", encoding="utf-8") as out:
        for s, p, o in rel:
            triple(out, iri(s), iri(p), iri(o))
            ents.update((s.strip(), o.strip()))
            rel_preds.add(p.strip())
            n_triples += 1
        for s, p, o in attr:
            triple(out, iri(s), iri(p), literal(o))
            ents.add(s.strip())
            attr_preds.add(p.strip())
            n_triples += 1
        for e, c in types:
            e, c = e.strip(), c.strip()
            ents.add(e)
            targets = [c]
            if materialize:
                targets = [x for x in class_path.get(c, [c]) if x != OWL_THING] or [c]
            for t in targets:
                triple(out, iri(e), iri(RDF_TYPE), iri(t))
                used_classes.add(t)
                n_triples += 1
        if declare:
            for p in sorted(rel_preds):
                triple(out, iri(p), iri(RDF_TYPE), iri(OWL_OBJ_PROP))
            for p in sorted(attr_preds - rel_preds):
                triple(out, iri(p), iri(RDF_TYPE), iri(OWL_DATA_PROP))
            for e in sorted(ents):
                triple(out, iri(e), iri(RDF_TYPE), iri(OWL_INDIVIDUAL))
    stats[name] = {
        "entities": len(ents), "rel_triples": len(rel), "attr_triples": len(attr),
        "type_triples_input": len(types), "relation_predicates": len(rel_preds),
        "attribute_predicates": len(attr_preds), "classes_used": len(used_classes),
        "triples_written_without_declarations": n_triples,
    }
    return ents, used_classes


def write_pairs(path: Path, pairs, alignment_xml: bool):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("src_uri\ttgt_uri\n")
        for s, t in pairs:
            f.write(f"{s.strip()}\t{t.strip()}\n")
    if alignment_xml:
        from xml.sax.saxutils import quoteattr
        with open(path.with_suffix(".rdf"), "w", encoding="utf-8", newline="\n") as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>\n'
                    '<rdf:RDF xmlns="http://knowledgeweb.semanticweb.org/heterogeneity/alignment#" '
                    'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
                    'xmlns:xsd="http://www.w3.org/2001/XMLSchema#">\n<Alignment>\n'
                    '  <xml>yes</xml>\n  <level>0</level>\n  <type>11</type>\n')
            for s, t in pairs:
                f.write("  <map><Cell>\n"
                        f"    <entity1 rdf:resource={quoteattr(s.strip())}/>\n"
                        f"    <entity2 rdf:resource={quoteattr(t.strip())}/>\n"
                        "    <relation>=</relation>\n"
                        '    <measure rdf:datatype="http://www.w3.org/2001/XMLSchema#float">1.0</measure>\n'
                        "  </Cell></map>\n")
            f.write("</Alignment>\n</rdf:RDF>\n")


def convert_with_rdflib(nt_path: Path, fmt: str):
    try:
        from rdflib import Graph
    except ImportError:
        print("[WARN] rdflib fehlt (pip install rdflib), Format %s wird uebersprungen" % fmt,
              file=sys.stderr)
        return
    ext, rdflib_fmt = {"ttl": ("ttl", "turtle"), "xml": ("rdf", "xml")}[fmt]
    g = Graph()
    g.parse(str(nt_path), format="nt")
    target = nt_path.with_suffix("." + ext)
    try:
        g.serialize(destination=str(target), format=rdflib_fmt)
    except Exception as e:  # z. B. Praedikate, die sich nicht als XML-Name schreiben lassen
        print(f"[WARN] {nt_path.name} -> {fmt} fehlgeschlagen: {e}", file=sys.stderr)


# ------------------------------------------------------------------------------ Main

def main():
    ap = argparse.ArgumentParser(description="OntoEA-Format nach ontology/source/target/reference.")
    ap.add_argument("input", help="Ordner im OntoEA-Format (enthaelt ent_links, rel_triples_1, ...)")
    ap.add_argument("-o", "--output", required=True, help="Ausgabeordner")
    ap.add_argument("--formats", default="nt",
                    help="Kommagetrennt aus nt,ttl,xml (Default: nt). ttl/xml per rdflib.")
    ap.add_argument("--merge-ontology", action="store_true",
                    help="Ontologie-Tripel zusaetzlich in source und target einbetten")
    ap.add_argument("--materialize-types", action="store_true",
                    help="Alle Oberklassen aus class_path.json als rdf:type setzen")
    ap.add_argument("--no-declarations", action="store_true",
                    help="Keine owl:NamedIndividual / ObjectProperty / DatatypeProperty-Deklarationen")
    ap.add_argument("--alignment-xml", action="store_true",
                    help="Referenzen zusaetzlich im Alignment-API-Format (.rdf) schreiben")
    args = ap.parse_args()

    d, out = Path(args.input), Path(args.output)
    if not (d / "ent_links").exists():
        sys.exit(f"{d} sieht nicht wie ein OntoEA-Datensatz aus (ent_links fehlt).")
    out.mkdir(parents=True, exist_ok=True)
    formats = {f.strip() for f in args.formats.split(",") if f.strip()}
    bad = formats - {"nt", "ttl", "xml"}
    if bad:
        sys.exit(f"Unbekannte Formate: {bad}")

    stats = {}
    with open(d / "class_path.json", encoding="utf-8") as f:
        class_path = json.load(f)

    # KGs zuerst, damit die Ontologie auch alle getypten Klassen kennt
    src_ents, src_classes = build_kg(d, 1, out / "source.nt", class_path,
                                     not args.no_declarations, args.materialize_types, stats)
    tgt_ents, tgt_classes = build_kg(d, 2, out / "target.nt", class_path,
                                     not args.no_declarations, args.materialize_types, stats)
    build_ontology(d, out / "ontology.nt", class_path, src_classes | tgt_classes, stats)

    if args.merge_ontology:
        onto_text = (out / "ontology.nt").read_text(encoding="utf-8")
        for name in ("source.nt", "target.nt"):
            with open(out / name, "a", encoding="utf-8") as f:
                f.write(onto_text)

    # Referenz
    links = read_tsv(d / "ent_links", 2, stats, "ent_links_input")
    write_pairs(out / "reference" / "all.tsv", links, args.alignment_xml)
    all_set = {(s.strip(), t.strip()) for s, t in links}
    stats["reference"] = {
        "links": len(links),
        "source_not_in_kg1": sum(1 for s, _ in links if s.strip() not in src_ents),
        "target_not_in_kg2": sum(1 for _, t in links if t.strip() not in tgt_ents),
    }

    fold_root = d / "721_5fold"
    stats["folds"] = {}
    if fold_root.is_dir():
        for fd in sorted((p for p in fold_root.iterdir() if p.is_dir()),
                         key=lambda p: (len(p.name), p.name)):
            parts = {}
            for split in ("train", "valid", "test"):
                rows = read_tsv(fd / f"{split}_links", 2, stats, f"fold{fd.name}_{split}_input")
                parts[split] = {(s.strip(), t.strip()) for s, t in rows}
                write_pairs(out / "reference" / f"fold{fd.name}" / f"{split}.tsv", sorted(parts[split]),
                            args.alignment_xml)
            union = parts["train"] | parts["valid"] | parts["test"]
            stats["folds"][fd.name] = {
                "train": len(parts["train"]), "valid": len(parts["valid"]), "test": len(parts["test"]),
                "union_equals_ent_links": union == all_set,
                "overlap_train_test": len(parts["train"] & parts["test"]),
                "overlap_valid_test": len(parts["valid"] & parts["test"]),
            }
    else:
        print("[WARN] 721_5fold nicht gefunden, keine Folds geschrieben.", file=sys.stderr)

    # Zusatzformate
    for fmt in sorted(formats - {"nt"}):
        for name in ("ontology.nt", "source.nt", "target.nt"):
            convert_with_rdflib(out / name, fmt)
    if "nt" not in formats:
        print("[INFO] Hinweis: .nt-Dateien bleiben als Zwischenformat erhalten.", file=sys.stderr)

    with open(out / "stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    # Kurzbericht
    print(f"Ausgabe: {out}")
    print(f"  source:   {stats['kg1']['entities']} Entitaeten, "
          f"{stats['kg1']['rel_triples']} rel + {stats['kg1']['attr_triples']} attr Tripel")
    print(f"  target:   {stats['kg2']['entities']} Entitaeten, "
          f"{stats['kg2']['rel_triples']} rel + {stats['kg2']['attr_triples']} attr Tripel")
    print(f"  ontology: {stats['ontology']['classes']} Klassen")
    print(f"  reference: {stats['reference']['links']} Links, "
          f"nicht in KG1: {stats['reference']['source_not_in_kg1']}, "
          f"nicht in KG2: {stats['reference']['target_not_in_kg2']}")
    for k, v in stats["folds"].items():
        ok = "ok" if v["union_equals_ent_links"] and not v["overlap_train_test"] \
            and not v["overlap_valid_test"] else "PRUEFEN"
        print(f"  fold{k}: train {v['train']} / valid {v['valid']} / test {v['test']}  [{ok}]")


if __name__ == "__main__":
    main()