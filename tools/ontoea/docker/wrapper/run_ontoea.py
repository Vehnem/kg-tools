#!/usr/bin/env python3
"""
run_ontoea.py — headless, config-driven runner around OntoEA
(https://github.com/ZihengZZH/OntoEA, code/run/main_from_args.py).

Usage:
    python run_ontoea.py --input <benchmark_dir> --output <output_dir> --config <config.yaml>

Why a runner instead of calling main_from_args.py directly:
  * main_from_args.py takes (args_json, benchmark_name, CUDA_VISIBLE_DEVICES) and
    resolves the benchmark as <training_data><benchmark_name>/. The runner builds
    that layout in a private temp directory (symlinks to the real files), so the
    input directory can be read-only and any path works.
  * The loader switches to a different code path if the full benchmark path
    contains "raw", "dbp15k" or "dwy100k". The temp directory is checked for that.
  * OntoEA writes onto_check_mat.h5 into the benchmark directory on every run;
    that happens in the temp directory, never in --input.
  * Upstream accepts any key in the args JSON and silently ignores typos; the
    runner validates keys, types and the values that OntoEA hard-asserts.
  * Upstream saves alignment results as integer entity ids; the runner maps them
    back to URIs (alignment.tsv) and writes evaluation.csv from the printed metrics.

Compatible with Python 3.6 (the OntoEA image uses python:3.6.12). All keys and
values are documented in CONFIG_REFERENCE.md.
"""

import argparse
import csv
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile

import yaml

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s", stream=sys.stderr)
log = logging.getLogger("run_ontoea")

ONTOEA_HOME = os.environ.get("ONTOEA_HOME", "/app/OntoEA")
BENCHMARK_NAME = "benchmark"
FORBIDDEN_PATH_PARTS = ("raw", "dbp15k", "dwy100k")

REQUIRED = object()

SCHEMA = [
    ("io", "dataset_division", "str", '721_5fold/1/', None),
    ("io", "ordered", "bool", True, None),

    ("runtime", "cuda_visible_devices", "str", REQUIRED, None),
    ("runtime", "batch_threads_num", "int", 4, None),
    ("runtime", "test_threads_num", "int", 8, None),

    ("word_embeddings", "word_embed", "str", '../../benchmarks/wiki-news-300d-1M.vec', None),
    ("word_embeddings", "use_word_embed_init", "flag", 0, None),
    ("word_embeddings", "use_word_embed_init_onto", "flag", 0, None),
    ("word_embeddings", "word_embed_init_zh", "flag", 0, None),
    ("word_embeddings", "use_alter_label", "flag", 0, None),

    ("model", "embedding_module", "str", 'OntoEA', ["OntoEA"]),
    ("model", "alignment_module", "str", 'mapping', ["mapping"]),
    ("model", "ent_emb_loss", "str", 'limit_loss', ["limit_loss", "pos_loss"]),
    ("model", "onto_training_method", "str", 'hier', ["hier", "transe", "linear"]),
    ("model", "fusion_way", "nstr", 'add', [None, "add"]),
    ("model", "dim", "int", 300, None),
    ("model", "onto_dim", "int", 300, None),
    ("model", "init", "str", 'unit', ["unit"]),
    ("model", "ent_l2_norm", "bool", True, [True]),
    ("model", "rel_l2_norm", "bool", True, None),
    ("model", "loss_norm", "str", 'L2', ['L1', 'L2']),
    ("model", "alpha", "float", 5, None),
    ("model", "beta", "float", 0, None),
    ("model", "gamma", "float", 1, None),
    ("model", "sigma", "float", 1, None),

    ("ontology", "cvlink_module", "nstr", None, [None, "swapping"]),
    ("ontology", "check_version", "int", 4, [0, 1, 2, 3, 4, 5]),
    ("ontology", "onto_neg_sampling", "nstr", None, [None, "prob_based"]),
    ("ontology", "likelihood_vaild", "bool", True, None),
    ("ontology", "onto_likelihood_epochs", "int", 5, None),
    ("ontology", "likelihood_slice", "int", 10, None),

    ("sampling", "neg_sampling", "str", 'truncated', None),
    ("sampling", "neg_triple_num", "int", 10, None),
    ("sampling", "truncated_epsilon", "float", 0.9, None),
    ("sampling", "alignment_neg_sampling", "str", 'type_based', ['type_based', 'random']),
    ("sampling", "pos_margin", "float", 0.01, None),
    ("sampling", "neg_margin", "float", 2.0, None),
    ("sampling", "neg_margin_balance", "float", 0.2, None),

    ("training", "optimizer", "str", 'Adagrad', ["Adagrad"]),
    ("training", "learning_rate", "float", 0.01, None),
    ("training", "cv_link_lr", "float", 0.001, None),
    ("training", "likelihood_lr", "float", 0.001, None),
    ("training", "max_epoch", "int", 2000, None),
    ("training", "sub_epoch", "int", 10, None),
    ("training", "align_sub_epoch", "int", 5, None),
    ("training", "batch_size", "int", 4500, None),
    ("training", "onto_batch_size", "int", 64, None),
    ("training", "cvlink_batch_size", "int", 2000, None),

    ("evaluation", "start_valid", "int", 50, None),
    ("evaluation", "eval_freq", "int", 10, None),
    ("evaluation", "stop_metric", "str", 'hits1', ["hits1", "mrr"]),
    ("evaluation", "eval_metric", "str", 'inner', ["inner"]),
    ("evaluation", "eval_norm", "bool", True, None),
    ("evaluation", "csls", "int", 10, None),
    ("evaluation", "top_k", "list_int", [1, 5, 10, 50], None),

    ("output", "keep_embeddings", "bool", True, None),
]

FIXED_ARGS = {
    "onto_valid": True,
    "seed_ent_type": "normal",
    "data_version": "popular",
}

REQUIRED_BENCHMARK_FILES = [
    "rel_triples_1", "rel_triples_2", "attr_triples_1", "attr_triples_2",
    "onto_subClassOf_triples", "onto_disjointWith_triples", "onto_attr_triples",
    "crossview_link_1", "crossview_link_2", "class_path.json",
]
REQUIRED_SPLIT_FILES = ["train_links", "valid_links", "test_links"]

EVAL_LABELS = ["entity_only", "fusion", "fusion_csls"]
EVAL_RE = re.compile(
    r"^accurate results.*?hits@\[([^\]]*)\]\s*=\s*\[([^\]]*)\]%,\s*mr\s*=\s*([0-9.eE+-]+),\s*mrr\s*=\s*([0-9.eE+-]+)"
)


class ConfigError(Exception):
    pass


def check_value(section, key, kind, value, allowed):
    where = "{}.{}".format(section, key)
    if kind == "bool":
        if not isinstance(value, bool):
            raise ConfigError("{}: expected true|false, got {!r}".format(where, value))
    elif kind == "flag":
        if isinstance(value, bool) or value not in (0, 1):
            raise ConfigError("{}: expected 0 or 1, got {!r}".format(where, value))
    elif kind == "int":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ConfigError("{}: expected integer, got {!r}".format(where, value))
    elif kind == "float":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ConfigError("{}: expected number, got {!r}".format(where, value))
        value = float(value)
    elif kind == "str":
        if not isinstance(value, str):
            raise ConfigError("{}: expected string, got {!r}".format(where, value))
    elif kind == "nstr":
        if value is not None and not isinstance(value, str):
            raise ConfigError("{}: expected string or null, got {!r}".format(where, value))
    elif kind == "list_int":
        if (not isinstance(value, list) or not value
                or any(isinstance(v, bool) or not isinstance(v, int) for v in value)):
            raise ConfigError("{}: expected non-empty list of integers, got {!r}".format(where, value))
    if allowed is not None and value not in allowed:
        raise ConfigError("{}: allowed values are {!r}, got {!r}".format(where, allowed, value))
    return value


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    if not isinstance(raw, dict):
        raise ConfigError("config root must be a mapping")

    known = {}
    for section, key, kind, default, allowed in SCHEMA:
        known.setdefault(section, {})[key] = (kind, default, allowed)

    for section, body in raw.items():
        if section not in known:
            raise ConfigError("unknown config section: {}".format(section))
        if not isinstance(body, dict):
            raise ConfigError("section '{}' must be a mapping".format(section))
        for key in body:
            if key not in known[section]:
                raise ConfigError("unknown config key: {}.{}".format(section, key))

    cfg = {}
    for section, key, kind, default, allowed in SCHEMA:
        body = raw.get(section) or {}
        if key in body:
            value = body[key]
        elif default is REQUIRED:
            raise ConfigError("{}.{} is required".format(section, key))
        else:
            value = default
        cfg.setdefault(section, {})[key] = check_value(section, key, kind, value, allowed)

    model, training, sampling = cfg["model"], cfg["training"], cfg["sampling"]
    if model["alpha"] <= 1:
        raise ConfigError("model.alpha must be > 1 (asserted by OntoEA)")
    if 1 not in cfg["evaluation"]["top_k"]:
        raise ConfigError("evaluation.top_k must contain 1 (asserted by OntoEA)")
    if sampling["neg_sampling"] == "truncated" and not 0.0 < sampling["truncated_epsilon"] < 1.0:
        raise ConfigError("sampling.truncated_epsilon must be in (0, 1) when neg_sampling is 'truncated'")
    if training["sub_epoch"] < 1 or training["max_epoch"] < training["sub_epoch"]:
        raise ConfigError("training.max_epoch must be >= training.sub_epoch >= 1 "
                          "(iterations = max_epoch // sub_epoch)")
    if cfg["evaluation"]["eval_freq"] < 1:
        raise ConfigError("evaluation.eval_freq must be >= 1")

    wanted = cfg["word_embeddings"]
    if wanted["use_word_embed_init"] == 1 or wanted["use_word_embed_init_onto"] == 1:
        if not os.path.isfile(wanted["word_embed"]):
            raise ConfigError("word_embeddings.word_embed must point to an existing file when "
                              "use_word_embed_init or use_word_embed_init_onto is 1")
    return cfg


def normalize_division(value):
    value = value.strip().strip("/")
    return (value + "/") if value else ""


def check_benchmark(input_dir, division):
    if not os.path.isdir(input_dir):
        raise ConfigError("--input is not a directory: {}".format(input_dir))
    missing = [f for f in REQUIRED_BENCHMARK_FILES if not os.path.isfile(os.path.join(input_dir, f))]
    missing += [os.path.join(division, f) for f in REQUIRED_SPLIT_FILES
                if not os.path.isfile(os.path.join(input_dir, division, f))]
    if missing:
        raise ConfigError("benchmark is missing required files in {}: {}".format(input_dir, ", ".join(missing)))


def make_workdir():
    for _ in range(20):
        work = tempfile.mkdtemp(prefix="ontoea_")
        lowered = os.path.join(work, BENCHMARK_NAME).lower()
        if not any(part in lowered for part in FORBIDDEN_PATH_PARTS):
            return work
        shutil.rmtree(work, ignore_errors=True)
    raise ConfigError("could not create a temp directory whose path avoids {} "
                      "(check TMPDIR={})".format(FORBIDDEN_PATH_PARTS, os.environ.get("TMPDIR")))


def build_benchmark_view(work, input_dir, division):
    bench = os.path.join(work, BENCHMARK_NAME)
    os.makedirs(bench)
    for name in REQUIRED_BENCHMARK_FILES:
        os.symlink(os.path.abspath(os.path.join(input_dir, name)), os.path.join(bench, name))
    if division:
        os.makedirs(os.path.join(bench, division))
    for name in REQUIRED_SPLIT_FILES:
        os.symlink(os.path.abspath(os.path.join(input_dir, division, name)),
                   os.path.join(bench, division, name))


def build_args_json(cfg, work, division):
    args = dict(FIXED_ARGS)
    for section, key, kind, default, allowed in SCHEMA:
        if section in ("runtime", "output") and key in ("cuda_visible_devices", "keep_embeddings"):
            continue
        args[key] = cfg[section][key]
    args["dataset_division"] = division
    args["training_data"] = work + os.sep
    args["output"] = os.path.join(work, "results") + os.sep
    return args


def run_ontoea(args_path, cuda, log_path):
    env = dict(os.environ)
    src = os.path.join(ONTOEA_HOME, "code", "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["PYTHONUNBUFFERED"] = "1"
    cmd = [sys.executable, os.path.join(ONTOEA_HOME, "code", "run", "main_from_args.py"),
           args_path, BENCHMARK_NAME, cuda]
    log.info("Running: %s", " ".join(cmd))
    lines = []
    with open(log_path, "w", encoding="utf-8") as logf:
        proc = subprocess.Popen(cmd, cwd=os.path.join(ONTOEA_HOME, "code", "run"), env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                universal_newlines=True, bufsize=1)
        for line in proc.stdout:
            sys.stdout.write(line)
            logf.write(line)
            lines.append(line.rstrip("\n"))
        proc.wait()
    return proc.returncode, lines


def find_result_dir(results_root):
    found = []
    for dirpath, _dirs, files in os.walk(results_root):
        if "alignment_results_12" in files:
            found.append(dirpath)
    if not found:
        return None
    return max(found, key=lambda d: os.path.getmtime(os.path.join(d, "alignment_results_12")))


def read_id_file(path):
    mapping = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) == 2:
                mapping[parts[1].strip()] = parts[0]
    return mapping


def write_alignment_tsv(result_dir, out_path):
    ids1 = read_id_file(os.path.join(result_dir, "kg1_ent_ids"))
    ids2 = read_id_file(os.path.join(result_dir, "kg2_ent_ids"))
    count = 0
    with open(os.path.join(result_dir, "alignment_results_12"), "r", encoding="utf-8") as src, \
            open(out_path, "w", encoding="utf-8") as dst:
        for line in src:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            dst.write("{}\t{}\n".format(ids1[parts[0].strip()], ids2[parts[1].strip()]))
            count += 1
    return count


def write_evaluation_csv(lines, out_path):
    rows = []
    for line in lines:
        m = EVAL_RE.match(line.strip())
        if m:
            ks = [k.strip() for k in m.group(1).split(",")]
            hits = m.group(2).split()
            if len(ks) != len(hits):
                raise ConfigError("cannot parse hits from: {}".format(line))
            rows.append((ks, hits, m.group(3), m.group(4)))
    if len(rows) < len(EVAL_LABELS):
        raise ConfigError("expected {} 'accurate results' lines in the OntoEA output, found {}".format(
            len(EVAL_LABELS), len(rows)))
    rows = rows[-len(EVAL_LABELS):]
    ks = rows[0][0]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["setting"] + ["hits_at_" + k for k in ks] + ["mr", "mrr"])
        for label, (_ks, hits, mr, mrr) in zip(EVAL_LABELS, rows):
            writer.writerow([label] + [repr(float(h)) for h in hits] + [mr, mrr])


def main():
    parser = argparse.ArgumentParser(description="Config-driven runner for OntoEA")
    parser.add_argument("--input", required=True, help="Benchmark directory (see CONFIG_REFERENCE.md, section 1)")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--config", required=True, help="Path to the YAML config")
    opts = parser.parse_args()

    try:
        cfg = load_config(opts.config)
        division = normalize_division(cfg["io"]["dataset_division"])
        check_benchmark(opts.input, division)
        for rel in ("code/run/main_from_args.py", "code/src/openea"):
            if not os.path.exists(os.path.join(ONTOEA_HOME, rel)):
                raise ConfigError("ONTOEA_HOME={} does not contain {}".format(ONTOEA_HOME, rel))
    except ConfigError as exc:
        log.error("%s", exc)
        return 1

    os.makedirs(opts.output, exist_ok=True)
    output_dir = os.path.abspath(opts.output)
    work = make_workdir()
    try:
        build_benchmark_view(work, opts.input, division)
        args_path = os.path.join(work, "args.json")
        with open(args_path, "w", encoding="utf-8") as f:
            json.dump(build_args_json(cfg, work, division), f, indent=2)
        shutil.copy(args_path, os.path.join(output_dir, "ontoea_args.json"))

        log_path = os.path.join(output_dir, "ontoea_stdout.log")
        code, lines = run_ontoea(args_path, cfg["runtime"]["cuda_visible_devices"], log_path)
        if code != 0:
            log.error("OntoEA exited with code %d. See %s", code, log_path)
            return 1

        result_dir = find_result_dir(os.path.join(work, "results"))
        if result_dir is None:
            log.error("OntoEA finished but wrote no alignment_results_12. See %s", log_path)
            return 1

        skip_embeddings = not cfg["output"]["keep_embeddings"]
        for name in sorted(os.listdir(result_dir)):
            if skip_embeddings and name.endswith(".npy"):
                continue
            src = os.path.join(result_dir, name)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(output_dir, name))

        n = write_alignment_tsv(result_dir, os.path.join(output_dir, "alignment.tsv"))
        write_evaluation_csv(lines, os.path.join(output_dir, "evaluation.csv"))
        log.info("Wrote %d aligned pairs to %s", n, os.path.join(output_dir, "alignment.tsv"))
        log.info("Wrote %s", os.path.join(output_dir, "evaluation.csv"))
        return 0
    except (ConfigError, KeyError) as exc:
        log.error("%s", exc)
        return 1
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
