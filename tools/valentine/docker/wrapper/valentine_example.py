import argparse
import inspect
import json
import sys
import time
from pathlib import Path

import pandas as pd
import yaml
from valentine import valentine_match
from valentine.algorithms import (
    Coma,
    Cupid,
    DistributionBased,
    Formula,
    JaccardDistanceMatcher,
    Policy,
    SimilarityFlooding,
    StringMatcher,
)
from valentine.algorithms.jaccard_distance import StringDistanceFunction
from valentine.data_sources import DataframeTable
from valentine.metrics import (
    F1Score,
    MeanReciprocalRank,
    Precision,
    PrecisionTopNPercent,
    Recall,
    RecallAtSizeofGroundTruth,
)

MATCHERS = {
    "Coma": Coma,
    "Cupid": Cupid,
    "DistributionBased": DistributionBased,
    "JaccardDistanceMatcher": JaccardDistanceMatcher,
    "SimilarityFlooding": SimilarityFlooding,
}

ENUM_PARAMS = {
    "JaccardDistanceMatcher": {"distance_fun": StringDistanceFunction},
    "SimilarityFlooding": {
        "coeff_policy": Policy,
        "formula": Formula,
        "string_matcher": StringMatcher,
    },
}

METRIC_CLASSES = {
    "Precision": Precision,
    "Recall": Recall,
    "F1Score": F1Score,
    "PrecisionTopNPercent": PrecisionTopNPercent,
    "RecallAtSizeofGroundTruth": RecallAtSizeofGroundTruth,
    "MeanReciprocalRank": MeanReciprocalRank,
}

ONE_TO_ONE_METRICS = {"Precision", "Recall", "F1Score", "PrecisionTopNPercent"}

SELECTION_METHODS = {
    "none",
    "one_to_one_greedy",
    "one_to_one_hungarian",
    "one_to_one_mutual_top",
}

TOP_LEVEL_KEYS = {"io", "matchers", "selection", "output", "evaluation"}
IO_KEYS = {
    "nrows",
    "encoding",
    "separator",
    "source_name",
    "target_name",
    "instance_sample_size",
}
SELECTION_KEYS = {
    "method",
    "threshold",
    "mutual_top_n",
    "min_score",
    "top_percent",
    "top_n",
    "top_n_per_source",
}
OUTPUT_KEYS = {"include_details", "evaluation_csv"}
EVALUATION_KEYS = {"enabled", "valentine_metrics"}
VALENTINE_METRICS_KEYS = {
    "enabled",
    "metrics",
    "one_to_one",
    "one_to_one_method",
    "top_n_percent",
}
MATCHER_ENTRY_KEYS = {"enabled", "params"}


def check_keys(section, given, allowed):
    unknown = set(given) - set(allowed)
    if unknown:
        raise ValueError(
            f"Unknown key(s) in '{section}': {sorted(unknown)}. "
            f"Allowed: {sorted(allowed)}"
        )


def section(config, name):
    value = config.get(name)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"'{name}' must be a mapping")
    return value


def load_config(path):
    with open(path, encoding="utf8") as f:
        config = yaml.safe_load(f)
    if not isinstance(config, dict):
        raise ValueError("Config must be a YAML mapping")
    check_keys("config", config, TOP_LEVEL_KEYS)
    check_keys("io", section(config, "io"), IO_KEYS)
    check_keys("selection", section(config, "selection"), SELECTION_KEYS)
    check_keys("output", section(config, "output"), OUTPUT_KEYS)
    evaluation = section(config, "evaluation")
    check_keys("evaluation", evaluation, EVALUATION_KEYS)
    check_keys(
        "evaluation.valentine_metrics",
        section(evaluation, "valentine_metrics"),
        VALENTINE_METRICS_KEYS,
    )
    matchers = section(config, "matchers")
    check_keys("matchers", matchers, MATCHERS)
    for name, entry in matchers.items():
        if entry is None:
            continue
        if not isinstance(entry, dict):
            raise ValueError(f"'matchers.{name}' must be a mapping")
        check_keys(f"matchers.{name}", entry, MATCHER_ENTRY_KEYS)
    return config


def load_ground_truth(mapping_file):
    with open(mapping_file, encoding="utf8") as f:
        mapping = json.load(f)
    return {(m["source_column"], m["target_column"]) for m in mapping["matches"]}


def evaluate(predicted, ground_truth):
    predicted = set(predicted)

    tp = len(predicted & ground_truth)
    fp = len(predicted - ground_truth)
    fn = len(ground_truth - predicted)

    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0

    if precision + recall:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0

    return {
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "Precision": precision,
        "Recall": recall,
        "F1": f1,
    }


def read_table(path, io_cfg):
    return pd.read_csv(
        path,
        nrows=io_cfg.get("nrows"),
        encoding=io_cfg.get("encoding", "utf-8"),
        sep=io_cfg.get("separator", ","),
    )


def to_enum(enum_cls, matcher_name, param, value):
    if isinstance(value, enum_cls):
        return value
    try:
        return enum_cls[str(value)]
    except KeyError:
        valid = [m.name for m in enum_cls]
        raise ValueError(
            f"matchers.{matcher_name}.params.{param}: '{value}' is not valid. "
            f"Allowed: {valid}"
        )


def build_matcher(name, params, io_cfg):
    cls = MATCHERS[name]
    accepted = set(inspect.signature(cls.__init__).parameters) - {"self"}
    check_keys(f"matchers.{name}.params", params, accepted)

    kwargs = {}
    for key, value in params.items():
        if value is None:
            continue
        if key in ENUM_PARAMS.get(name, {}):
            value = to_enum(ENUM_PARAMS[name][key], name, key, value)
        elif key == "tfidf_corpus":
            value = [
                DataframeTable(
                    read_table(p, io_cfg),
                    name=Path(p).stem,
                    instance_sample_size=io_cfg.get("instance_sample_size", 1000),
                )
                for p in value
            ]
            if not value:
                continue
        kwargs[key] = value
    return cls(**kwargs)


def apply_selection(results, selection):
    method = selection.get("method", "one_to_one_greedy")
    if method not in SELECTION_METHODS:
        raise ValueError(
            f"selection.method '{method}' is not valid. "
            f"Allowed: {sorted(SELECTION_METHODS)}"
        )

    threshold = selection.get("threshold")
    if method == "one_to_one_greedy":
        selected = results.one_to_one_greedy(threshold=threshold)
    elif method == "one_to_one_hungarian":
        selected = results.one_to_one_hungarian(threshold=threshold)
    elif method == "one_to_one_mutual_top":
        n = selection.get("mutual_top_n")
        selected = (
            results.one_to_one_mutual_top()
            if n is None
            else results.one_to_one_mutual_top(n=n)
        )
    else:
        selected = results

    if selection.get("min_score") is not None:
        selected = selected.filter(selection["min_score"])
    if selection.get("top_percent") is not None:
        selected = selected.take_top_percent(selection["top_percent"])
    if selection.get("top_n") is not None:
        selected = selected.take_top_n(selection["top_n"])
    if selection.get("top_n_per_source") is not None:
        selected = selected.take_top_n_per_source(selection["top_n_per_source"])
    return selected


def build_metrics(metrics_cfg):
    names = metrics_cfg.get("metrics") or list(METRIC_CLASSES)
    unknown = set(names) - set(METRIC_CLASSES)
    if unknown:
        raise ValueError(
            f"evaluation.valentine_metrics.metrics: unknown {sorted(unknown)}. "
            f"Allowed: {sorted(METRIC_CLASSES)}"
        )
    metrics = set()
    for name in names:
        kwargs = {}
        if name in ONE_TO_ONE_METRICS and metrics_cfg.get("one_to_one") is not None:
            kwargs["one_to_one"] = metrics_cfg["one_to_one"]
        if name == "PrecisionTopNPercent" and metrics_cfg.get("top_n_percent") is not None:
            kwargs["n"] = metrics_cfg["top_n_percent"]
        metrics.add(METRIC_CLASSES[name](**kwargs))
    return metrics


def run_matcher(name, params, df_source, df_target, io_cfg, selection, match_kwargs):
    matcher = build_matcher(name, params, io_cfg)

    start = time.perf_counter()
    results = valentine_match([df_source, df_target], matcher, **match_kwargs)
    selected = apply_selection(results, selection)
    runtime = time.perf_counter() - start

    return results, selected, runtime


def write_matches(selected, output_json, include_details):
    matches = []
    for pair, score in selected.items():
        entry = {
            "id_1": pair.source_column,
            "id_2": pair.target_column,
            "score": float(score),
            "id_type": type(pair.source_column).__name__,
        }
        if include_details:
            details = selected.get_details(pair)
            if details:
                entry["details"] = {k: float(v) for k, v in details.items()}
        matches.append(entry)

    with open(output_json, "w", encoding="utf8") as f:
        json.dump(
            {"matches": matches, "blocks": [], "clusters": []},
            f,
            indent=4,
            ensure_ascii=False,
        )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Schema matching with Valentine, configured via YAML."
    )
    parser.add_argument("source", help="Path to the source CSV")
    parser.add_argument("target", help="Path to the target CSV")
    parser.add_argument("output", help="Output directory")
    parser.add_argument("config", help="Path to config.yaml")
    parser.add_argument(
        "mapping",
        nargs="?",
        default=None,
        help="Optional ground-truth mapping JSON for evaluation",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    config = load_config(args.config)
    io_cfg = section(config, "io")
    selection = section(config, "selection")
    output_cfg = section(config, "output")
    eval_cfg = section(config, "evaluation")
    metrics_cfg = section(eval_cfg, "valentine_metrics")
    matchers_cfg = section(config, "matchers")

    enabled = {
        name: (entry or {})
        for name, entry in matchers_cfg.items()
        if (entry or {}).get("enabled", True)
    }
    if not enabled:
        raise ValueError("No matcher is enabled in 'matchers'")

    source_name = io_cfg.get("source_name")
    target_name = io_cfg.get("target_name")
    if (source_name is None) != (target_name is None):
        raise ValueError("io.source_name and io.target_name must be set together")

    match_kwargs = {}
    if source_name is not None:
        match_kwargs["df_names"] = [source_name, target_name]
    if "instance_sample_size" in io_cfg:
        match_kwargs["instance_sample_size"] = io_cfg["instance_sample_size"]

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    df_source = read_table(args.source, io_cfg)
    df_target = read_table(args.target, io_cfg)

    ground_truth = None
    if args.mapping is not None:
        ground_truth = load_ground_truth(args.mapping)
    elif eval_cfg.get("enabled", True):
        print(
            "No mapping file given: evaluation metrics are skipped",
            file=sys.stderr,
        )

    do_evaluation = ground_truth is not None and eval_cfg.get("enabled", True)
    metrics = build_metrics(metrics_cfg) if metrics_cfg.get("enabled", False) else None

    dataset_name = Path(args.source).stem
    rows = []

    for name, entry in enabled.items():
        print(f"Running {name} on {dataset_name}")

        results, selected, runtime = run_matcher(
            name,
            entry.get("params") or {},
            df_source,
            df_target,
            io_cfg,
            selection,
            match_kwargs,
        )

        write_matches(
            selected,
            output_dir / f"{name}_matches.json",
            output_cfg.get("include_details", False),
        )

        row = {
            "dataset": dataset_name,
            "matcher": name,
            "runtime_seconds": runtime,
            "n_matches": len(selected),
        }

        if do_evaluation:
            predicted = [(p.source_column, p.target_column) for p in selected]
            row.update(evaluate(predicted, ground_truth))
            if metrics is not None:
                valentine_scores = results.get_metrics(
                    sorted(ground_truth),
                    metrics=metrics,
                    one_to_one_method=metrics_cfg.get("one_to_one_method", "hungarian"),
                )
                row.update({f"valentine_{k}": v for k, v in valentine_scores.items()})

        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(
        output_dir / output_cfg.get("evaluation_csv", "evaluation.csv"),
        index=False,
    )

    print(df)


if __name__ == "__main__":
    main()