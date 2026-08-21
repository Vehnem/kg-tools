#!/usr/bin/env python3
"""
run_splink.py
=============

Generic, config-driven runner for Splink (>= 4.0).

Usage
-----
    python run_splink.py \
        --input data/input.csv \
        --output data/output.csv \
        --config config.yaml

    # Linking two datasets (link_only / link_and_dedupe)
    python run_splink.py \
        --input data/left.csv \
        --input2 data/right.csv \
        --output data/output.csv \
        --config config.yaml

Everything that controls *how* Splink behaves (blocking rules, comparisons,
matchers/algorithms, training steps, thresholds, backend, ...) lives in the
YAML config file. See config.yaml and CONFIG_REFERENCE.md for the full list
of options.

Supported input/output formats (inferred from file extension):
    .csv, .tsv, .parquet, .jsonl / .json, .pkl / .pickle

Supported backends: duckdb, sqlite, spark, postgres
(spark/postgres require the corresponding extra Python packages and, for
spark, an already-running SparkSession / for postgres, a SQLAlchemy engine
supplied via environment-specific setup -- see CONFIG_REFERENCE.md).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from splink import Linker, SettingsCreator
import splink.comparison_library as cl


# --------------------------------------------------------------------------
# I/O helpers
# --------------------------------------------------------------------------

def read_table(path: str) -> pd.DataFrame:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(p)
    if suffix == ".tsv":
        return pd.read_csv(p, sep="\t")
    if suffix == ".parquet":
        return pd.read_parquet(p)
    if suffix in (".json", ".jsonl"):
        return pd.read_json(p, lines=(suffix == ".jsonl"))
    if suffix in (".pkl", ".pickle"):
        return pd.read_pickle(p)
    raise ValueError(f"Unsupported input file extension: {suffix}")


def write_table(df: pd.DataFrame, path: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    suffix = p.suffix.lower()
    if suffix == ".csv":
        df.to_csv(p, index=False)
    elif suffix == ".tsv":
        df.to_csv(p, sep="\t", index=False)
    elif suffix == ".parquet":
        df.to_parquet(p, index=False)
    elif suffix in (".json", ".jsonl"):
        df.to_json(p, orient="records", lines=(suffix == ".jsonl"))
    elif suffix in (".pkl", ".pickle"):
        df.to_pickle(p)
    else:
        raise ValueError(f"Unsupported output file extension: {suffix}")


def load_config(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if "splink" not in cfg:
        raise ValueError("Config file must have a top-level 'splink:' key.")
    return cfg["splink"]


# --------------------------------------------------------------------------
# Backend / DB API
# --------------------------------------------------------------------------

def get_db_api(cfg: dict[str, Any]):
    backend = (cfg.get("backend") or "duckdb").lower()

    if backend == "duckdb":
        from splink import DuckDBAPI
        return DuckDBAPI()

    if backend == "sqlite":
        from splink import SQLiteAPI
        return SQLiteAPI()

    if backend == "spark":
        from splink import SparkAPI
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.appName("splink").getOrCreate()
        return SparkAPI(spark_session=spark)

    if backend == "postgres":
        from splink import PostgresAPI
        conn_str = cfg.get("postgres_connection_string")
        if not conn_str:
            raise ValueError(
                "backend: postgres requires 'postgres_connection_string' in the config."
            )
        import sqlalchemy
        engine = sqlalchemy.create_engine(conn_str)
        return PostgresAPI(
            engine=engine,
            schema=cfg.get("postgres_schema", "splink"),
            other_schemas_to_search=cfg.get("postgres_other_schemas_to_search"),
        )

    raise ValueError(f"Unknown backend: {backend}")


# --------------------------------------------------------------------------
# Comparisons
# --------------------------------------------------------------------------

# Maps the 'comparison_type' string used in the YAML to the corresponding
# splink.comparison_library class name. Any class in comparison_library not
# listed here can still be used by simply supplying its exact class name as
# comparison_type (see CONFIG_REFERENCE.md).
_COMPARISON_TYPE_ALIASES = {
    "exact_match": "ExactMatch",
    "levenshtein": "LevenshteinAtThresholds",
    "damerau_levenshtein": "DamerauLevenshteinAtThresholds",
    "jaro": "JaroAtThresholds",
    "jaro_winkler": "JaroWinklerAtThresholds",
    "jaccard": "JaccardAtThresholds",
    "cosine_similarity": "CosineSimilarityAtThresholds",
    "distance_function": "DistanceFunctionAtThresholds",
    "pairwise_string_distance": "PairwiseStringDistanceFunctionAtThresholds",
    "distance_in_km": "DistanceInKMAtThresholds",
    "array_intersect": "ArrayIntersectAtSizes",
    "name_comparison": "NameComparison",
    "forename_surname": "ForenameSurnameComparison",
    "date_of_birth": "DateOfBirthComparison",
    "absolute_time_difference": "AbsoluteTimeDifferenceAtThresholds",
    "absolute_date_difference": "AbsoluteDateDifferenceAtThresholds",
    "postcode": "PostcodeComparison",
    "email": "EmailComparison",
}


# These are never constructor arguments on a comparison_library class -
# in current splink (>=4) they must be set afterwards via the comparison's
# .configure(...) method, which every ComparisonCreator subclass exposes.
_CONFIGURE_ONLY_KEYS = {"term_frequency_adjustments", "m_probabilities", "u_probabilities"}


def _build_one_comparison(comp_cfg: dict[str, Any]):
    """Build a single Splink comparison from one YAML entry."""

    # Escape hatch: a fully hand-written Splink comparison dict (the same
    # JSON/dict structure Splink itself uses internally, i.e. the output of
    # comparison.get_comparison(dialect).as_dict()). This guarantees every
    # possible Splink setting is reachable, even ones not modelled
    # explicitly by this script (e.g. a CustomComparison with hand-written
    # comparison_levels). This is passed straight through as a plain dict -
    # Splink's SettingsCreator accepts comparisons as either
    # ComparisonCreator objects or as raw dicts of this shape.
    if "raw" in comp_cfg:
        return comp_cfg["raw"]

    comparison_type = comp_cfg["comparison_type"]
    class_name = _COMPARISON_TYPE_ALIASES.get(comparison_type, comparison_type)

    try:
        comparison_cls = getattr(cl, class_name)
    except AttributeError as exc:
        raise ValueError(
            f"Unknown comparison_type '{comparison_type}'. It is neither a "
            f"recognised alias nor a class name in splink.comparison_library."
        ) from exc

    params = dict(comp_cfg.get("params") or {})

    # Pull out the options that must go through .configure() rather than
    # the constructor (see _CONFIGURE_ONLY_KEYS above).
    configure_kwargs = {
        key: params.pop(key) for key in list(params) if key in _CONFIGURE_ONLY_KEYS
    }

    # 'input_columns' -> most comparison_library classes take the column
    # name as the first positional argument ('col_name'); a few (e.g.
    # ForenameSurnameComparison, DistanceInKMAtThresholds, PostcodeComparison
    # with lat/long) take more than one. We pass them through as positional
    # args, in the order given.
    input_columns = comp_cfg.get("input_columns") or [comp_cfg["output_column_name"]]

    comparison = comparison_cls(*input_columns, **params)

    if configure_kwargs:
        comparison = comparison.configure(**configure_kwargs)

    return comparison


def build_comparisons(cfg: dict[str, Any]) -> list:
    return [_build_one_comparison(c) for c in cfg.get("comparisons", [])]


# --------------------------------------------------------------------------
# Settings
# --------------------------------------------------------------------------

def build_settings(cfg: dict[str, Any], comparisons: list) -> SettingsCreator:
    return SettingsCreator(
        link_type=cfg.get("link_type", "dedupe_only"),
        unique_id_column_name=cfg.get("unique_id_column_name", "unique_id"),
        comparisons=comparisons,
        blocking_rules_to_generate_predictions=cfg.get(
            "blocking_rules_to_generate_predictions", []
        ),
        retain_matching_columns=cfg.get("retain_matching_columns", True),
        retain_intermediate_calculation_columns=cfg.get(
            "retain_intermediate_calculation_columns", False
        ),
        additional_columns_to_retain=cfg.get("additional_columns_to_retain", []),
        probability_two_random_records_match=cfg.get(
            "probability_two_random_records_match"
        ),
        em_convergence=cfg.get("em_convergence", 0.0001),
        max_iterations=cfg.get("max_iterations", 25),
        source_dataset_column_name=cfg.get("source_dataset_column_name"),
        bayes_factor_column_prefix=cfg.get("bayes_factor_column_prefix", "bf_"),
        term_frequency_adjustment_column_prefix=cfg.get(
            "term_frequency_adjustment_column_prefix", "tf_"
        ),
        comparison_vector_value_column_prefix=cfg.get(
            "comparison_vector_value_column_prefix", "gamma_"
        ),
    )


# --------------------------------------------------------------------------
# Training
# --------------------------------------------------------------------------

def run_training(linker: Linker, cfg: dict[str, Any]) -> None:
    """
    Every sub-key under 'training:' in the YAML is forwarded as-is to the
    matching linker.training.* method, so any keyword argument that method
    supports can be set from the config (see CONFIG_REFERENCE.md for the
    exact keys each step accepts).
    """
    training_cfg = cfg.get("training") or {}
    if not training_cfg:
        return

    prm = training_cfg.get("estimate_probability_two_random_records_match")
    if prm:
        kwargs = dict(prm)
        deterministic_matching_rules = kwargs.pop("deterministic_matching_rules")
        linker.training.estimate_probability_two_random_records_match(
            deterministic_matching_rules, **kwargs
        )

    rand = training_cfg.get("estimate_u_using_random_sampling")
    if rand:
        kwargs = dict(rand)
        if "max_pairs" in kwargs:
            kwargs["max_pairs"] = float(kwargs["max_pairs"])
        linker.training.estimate_u_using_random_sampling(**kwargs)

    for em_cfg in training_cfg.get("estimate_parameters_using_expectation_maximisation", []):
        kwargs = dict(em_cfg)
        blocking_rule = kwargs.pop("blocking_rule")
        linker.training.estimate_parameters_using_expectation_maximisation(
            blocking_rule, **kwargs
        )

    label_col = training_cfg.get("estimate_m_from_label_column")
    if label_col:
        linker.training.estimate_m_from_label_column(label_col)


def apply_term_frequency_adjustments(linker: Linker, cfg: dict[str, Any]) -> None:
    tf_cfg = cfg.get("term_frequency_adjustments") or {}
    columns = tf_cfg.get("columns") or []
    for col in columns:
        linker.table_management.compute_tf_table(col)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a Splink dedupe/link job from a YAML config.")
    parser.add_argument("--input", required=True, help="Path to the primary input dataset.")
    parser.add_argument(
        "--input2",
        required=False,
        help="Path to a second input dataset (required for link_only / link_and_dedupe).",
    )
    parser.add_argument("--output", required=True, help="Path to write the results to.")
    parser.add_argument("--config", required=True, help="Path to the Splink YAML config file.")
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Override config 'output.threshold_match_probability' at the command line.",
    )
    args = parser.parse_args(argv)

    cfg = load_config(args.config)

    db_api = get_db_api(cfg)
    comparisons = build_comparisons(cfg)
    settings = build_settings(cfg, comparisons)

    df_left = read_table(args.input)
    if args.input2:
        df_right = read_table(args.input2)
        input_tables = [df_left, df_right]
    else:
        input_tables = df_left

    linker = Linker(input_tables, settings, db_api=db_api)

    run_training(linker, cfg)
    apply_term_frequency_adjustments(linker, cfg)

    predictions = linker.inference.predict(
        threshold_match_probability=(cfg.get("output") or {}).get(
            "threshold_match_probability"
        ),
        threshold_match_weight=(cfg.get("output") or {}).get("threshold_match_weight"),
    )
    result_df = predictions.as_pandas_dataframe()

    threshold = args.threshold
    if threshold is None:
        threshold = (cfg.get("output") or {}).get("threshold_match_probability")
    if threshold is not None and "match_probability" in result_df.columns:
        result_df = result_df[result_df["match_probability"] >= threshold]

    clusters_cfg = (cfg.get("output") or {}).get("clustering")
    if clusters_cfg and clusters_cfg.get("enabled"):
        clusters = linker.clustering.cluster_pairwise_predictions_at_threshold(
            predictions,
            threshold_match_probability=clusters_cfg.get("threshold_match_probability", 0.95),
        )
        write_table(clusters.as_pandas_dataframe(), args.output)
    else:
        write_table(result_df, args.output)

    print(f"Done. Wrote {len(result_df)} rows to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())