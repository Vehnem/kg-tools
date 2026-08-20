#!/usr/bin/env python3
"""
run_magellan.py — config-driven entity-resolution pipeline on top of
py_entitymatching (Magellan).

Usage:
    python run_magellan.py --input <input_dir> --output <output_dir> --config <config.yaml>

Expected layout of --input (paths are relative to --input unless the config
gives absolute paths, see CONFIG_REFERENCE.md, section "io"):
    <input_dir>/<io.ltable>
    <input_dir>/<io.rtable>
    <input_dir>/<io.labeled_data>   (optional)

All stages, their `method` values and `method_params` are documented in
CONFIG_REFERENCE.md.
"""

import argparse
import json
import logging
import os
import sys

import pandas as pd
import yaml

import py_entitymatching as em

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("run_magellan")


# --------------------------------------------------------------------------
# Registries
# --------------------------------------------------------------------------

BLOCKER_REGISTRY = {
    "attr_equivalence_blocker": em.AttrEquivalenceBlocker,
    "overlap_blocker": em.OverlapBlocker,
    "sorted_neighborhood_blocker": em.SortedNeighborhoodBlocker,
    "rule_based_blocker": em.RuleBasedBlocker,
    "black_box_blocker": em.BlackBoxBlocker,
}

# ML matchers (need feature vectors + fit/predict); constructor forwards
# **method_params straight to the underlying scikit-learn estimator.
ML_MATCHER_REGISTRY = {
    "decision_tree": em.DTMatcher,
    "random_forest": em.RFMatcher,
    "svm": em.SVMMatcher,
    "naive_bayes": em.NBMatcher,
    "logistic_regression": em.LogRegMatcher,
    "linear_regression": em.LinRegMatcher,
}

# XGBoostMatcher is only importable if the optional `xgboost` package is
# installed (py_entitymatching wraps the import in try/except ImportError).
if hasattr(em, "XGBoostMatcher"):
    ML_MATCHER_REGISTRY["xgboost"] = em.XGBoostMatcher

# Rule-based matcher: no training, operates directly on the candidate set.
RULE_MATCHER_NAME = "rule_based"


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def resolve_path(base_dir, path):
    if path is None:
        return None
    return path if os.path.isabs(path) else os.path.join(base_dir, path)


def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# --------------------------------------------------------------------------
# Stage: I/O
# --------------------------------------------------------------------------

def load_tables(cfg, input_dir):
    io_cfg = cfg["io"]
    l_path = resolve_path(input_dir, io_cfg["ltable"])
    r_path = resolve_path(input_dir, io_cfg["rtable"])

    log.info("Reading ltable from %s", l_path)
    ltable = em.read_csv_metadata(l_path, key=io_cfg["l_key"])
    log.info("Reading rtable from %s", r_path)
    rtable = em.read_csv_metadata(r_path, key=io_cfg["r_key"])

    labeled_data = None
    if io_cfg.get("labeled_data"):
        lab_path = resolve_path(input_dir, io_cfg["labeled_data"])
        log.info("Reading labeled data from %s", lab_path)
        labeled_data = pd.read_csv(lab_path)

    return ltable, rtable, labeled_data


# --------------------------------------------------------------------------
# Stage: blocking
# --------------------------------------------------------------------------

def build_blocker(blocker_cfg, feature_table_for_blocking=None):
    method = blocker_cfg["method"]
    if method not in BLOCKER_REGISTRY:
        raise ValueError(f"Unknown blocking method: {method}")
    cls = BLOCKER_REGISTRY[method]

    if method == "attr_equivalence_blocker":
        return cls()
    if method == "rule_based_blocker":
        blocker = cls()
        blocker.set_feature_table(feature_table_for_blocking)
        for rule in blocker_cfg.get("rules", []):
            blocker.add_rule(rule, feature_table_for_blocking)
        return blocker
    # overlap_blocker, sorted_neighborhood_blocker, black_box_blocker take
    # no constructor args in py_entitymatching 0.4.x
    return cls()


def run_one_blocker(blocker, blocker_cfg, ltable, rtable):
    method = blocker_cfg["method"]
    params = dict(blocker_cfg.get("method_params", {}))

    if method == "attr_equivalence_blocker":
        return blocker.block_tables(
            ltable, rtable,
            blocker_cfg["block_attr_l"], blocker_cfg["block_attr_r"],
            l_output_attrs=blocker_cfg.get("l_output_attrs"),
            r_output_attrs=blocker_cfg.get("r_output_attrs"),
            n_jobs=blocker_cfg.get("n_jobs", 1),
        )
    if method == "overlap_blocker":
        return blocker.block_tables(
            ltable, rtable,
            blocker_cfg["block_attr_l"], blocker_cfg["block_attr_r"],
            l_output_attrs=blocker_cfg.get("l_output_attrs"),
            r_output_attrs=blocker_cfg.get("r_output_attrs"),
            show_progress=blocker_cfg.get("show_progress", False),
            n_jobs=blocker_cfg.get("n_jobs", 1),
            **params,
        )
    if method == "sorted_neighborhood_blocker":
        candset = blocker.block_tables(
            ltable, rtable,
            blocker_cfg["block_attr_l"], blocker_cfg["block_attr_r"],
            l_output_attrs=blocker_cfg.get("l_output_attrs"),
            r_output_attrs=blocker_cfg.get("r_output_attrs"),
            n_jobs=blocker_cfg.get("n_jobs", 1),
            **params,
        )
        # py_entitymatching 0.4.2's SortedNeighborhoodBlocker (an
        # "experimental" feature per its own runtime warning) has two
        # verified quirks that break combine_blocker_outputs_via_union
        # if left uncorrected:
        #  1) it registers an internally-copied ltable/rtable in the
        #     catalog instead of the original objects (union compares by
        #     identity via id());
        #  2) it unconditionally adds junk columns literally named
        #     "<l_output_prefix>ID" / "<r_output_prefix>ID" (see
        #     sn_blocker.py block_tables(), hardcoded "ID" suffix) on top
        #     of the real fk columns, which the union step then
        #     misinterprets as an output attribute called "ID".
        em.set_ltable(candset, ltable)
        em.set_rtable(candset, rtable)
        junk_cols = [c for c in ("ltable_id", "rtable_id") if c in candset.columns]
        if junk_cols:
            candset.drop(columns=junk_cols, inplace=True)
        return candset
    if method == "rule_based_blocker":
        return blocker.block_tables(
            ltable, rtable,
            l_output_attrs=blocker_cfg.get("l_output_attrs"),
            r_output_attrs=blocker_cfg.get("r_output_attrs"),
            show_progress=blocker_cfg.get("show_progress", False),
            n_jobs=blocker_cfg.get("n_jobs", 1),
        )
    if method == "black_box_blocker":
        module_name, func_name = blocker_cfg["function"].rsplit(".", 1)
        import importlib
        mod = importlib.import_module(module_name)
        blocker.set_black_box_function(getattr(mod, func_name))
        return blocker.block_tables(
            ltable, rtable,
            l_output_attrs=blocker_cfg.get("l_output_attrs"),
            r_output_attrs=blocker_cfg.get("r_output_attrs"),
            show_progress=blocker_cfg.get("show_progress", False),
            n_jobs=blocker_cfg.get("n_jobs", 1),
        )
    raise ValueError(f"Unhandled blocking method: {method}")


def run_one_blocker_candset(blocker, blocker_cfg, candset):
    """Apply a blocker as a chained filter on an existing candidate set
    (block_candset), instead of block_tables on the full ltable/rtable."""
    method = blocker_cfg["method"]
    params = dict(blocker_cfg.get("method_params", {}))

    if method == "sorted_neighborhood_blocker":
        # Verified: sn_blocker.py's block_candset is a stub that
        # unconditionally raises AssertionError('unimplemented') — it is
        # not a bug in this runner, py_entitymatching itself does not
        # support sorted-neighborhood blocking as a chained/second-stage
        # blocker. It may only be the first blocker in a chain.
        raise ValueError(
            "sorted_neighborhood_blocker does not support block_candset "
            "(py_entitymatching raises 'unimplemented'); it can only be "
            "used as the first blocker in a 'chain', never a later stage."
        )
    if method == "attr_equivalence_blocker":
        return blocker.block_candset(
            candset,
            blocker_cfg["block_attr_l"], blocker_cfg["block_attr_r"],
            show_progress=blocker_cfg.get("show_progress", False),
            n_jobs=blocker_cfg.get("n_jobs", 1),
        )
    if method == "overlap_blocker":
        return blocker.block_candset(
            candset,
            blocker_cfg["block_attr_l"], blocker_cfg["block_attr_r"],
            show_progress=blocker_cfg.get("show_progress", False),
            n_jobs=blocker_cfg.get("n_jobs", 1),
            **params,
        )
    if method == "rule_based_blocker":
        return blocker.block_candset(
            candset,
            show_progress=blocker_cfg.get("show_progress", False),
            n_jobs=blocker_cfg.get("n_jobs", 1),
        )
    if method == "black_box_blocker":
        module_name, func_name = blocker_cfg["function"].rsplit(".", 1)
        import importlib
        mod = importlib.import_module(module_name)
        blocker.set_black_box_function(getattr(mod, func_name))
        return blocker.block_candset(
            candset,
            show_progress=blocker_cfg.get("show_progress", False),
            n_jobs=blocker_cfg.get("n_jobs", 1),
        )
    raise ValueError(f"Unhandled blocking method for block_candset: {method}")


def run_blocking(cfg, ltable, rtable, feature_table_for_blocking=None):
    blocking_cfg = cfg["blocking"]
    blocker_cfgs = blocking_cfg["blockers"]
    combine_strategy = blocking_cfg.get("combine", "union")

    if combine_strategy == "chain":
        # Sequential/cascading blocking: the first blocker runs
        # block_tables on the full ltable/rtable, every subsequent
        # blocker runs block_candset on the previous stage's output —
        # i.e. each stage progressively filters down the same candidate
        # set, rather than each stage independently blocking the full
        # tables and unioning the results.
        first_cfg = blocker_cfgs[0]
        log.info("Running blocker '%s' (%s) [chain: stage 1/%d]",
                  first_cfg.get("name", first_cfg["method"]), first_cfg["method"], len(blocker_cfgs))
        blocker = build_blocker(first_cfg, feature_table_for_blocking)
        combined = run_one_blocker(blocker, first_cfg, ltable, rtable)
        log.info("  -> %d candidate pairs", len(combined))

        for i, b_cfg in enumerate(blocker_cfgs[1:], start=2):
            log.info("Running blocker '%s' (%s) [chain: stage %d/%d]",
                      b_cfg.get("name", b_cfg["method"]), b_cfg["method"], i, len(blocker_cfgs))
            blocker = build_blocker(b_cfg, feature_table_for_blocking)
            combined = run_one_blocker_candset(blocker, b_cfg, combined)
            log.info("  -> %d candidate pairs", len(combined))
    else:
        if combine_strategy != "union":
            raise ValueError("blocking.combine must be 'union' or 'chain'")
        outputs = []
        for b_cfg in blocker_cfgs:
            log.info("Running blocker '%s' (%s)", b_cfg.get("name", b_cfg["method"]), b_cfg["method"])
            blocker = build_blocker(b_cfg, feature_table_for_blocking)
            candset = run_one_blocker(blocker, b_cfg, ltable, rtable)
            log.info("  -> %d candidate pairs", len(candset))
            outputs.append(candset)

        combined = outputs[0] if len(outputs) == 1 else em.combine_blocker_outputs_via_union(outputs)

    cs_cfg = cfg.get("candidate_set", {})
    if cs_cfg.get("drop_duplicates", True):
        before = len(combined)
        # inplace=True keeps the same DataFrame object identity, which is
        # required because py_entitymatching's catalog tracks metadata by
        # object id; reassigning to a new DataFrame would drop it.
        combined.drop_duplicates(
            subset=["ltable_" + em.get_key(ltable), "rtable_" + em.get_key(rtable)],
            inplace=True,
        )
        combined.reset_index(drop=True, inplace=True)
        log.info("Candidate set dedup: %d -> %d", before, len(combined))

    log.info("Total candidate set size after blocking: %d", len(combined))
    return combined


def run_debug_blocker(cfg, candset, ltable, rtable, output_dir):
    dbg_cfg = cfg.get("debug_blocker", {})
    if not dbg_cfg.get("enabled", False):
        return
    log.info("Running debug_blocker for false-negative analysis")
    debug_df = em.debug_blocker(
        candset, ltable, rtable,
        output_size=dbg_cfg.get("output_size", 200),
        n_jobs=dbg_cfg.get("n_jobs", 1),
    )
    out_path = os.path.join(output_dir, dbg_cfg.get("output_path", "debug_blocker_output.csv"))
    debug_df.to_csv(out_path, index=False)
    log.info("Wrote debug_blocker output to %s", out_path)


# --------------------------------------------------------------------------
# Stage: labeling (merge gold labels into the candidate set)
# --------------------------------------------------------------------------

def _find_column(df, candidates):
    """Return the first of `candidates` that exists in df.columns, or None."""
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _require_nonempty(df, stage_name, hint=""):
    """Fail loudly, at the stage that actually produced 0 rows, instead of
    letting the pipeline continue and crash several stages later inside
    py_entitymatching/numpy with the opaque
    'ValueError: number sections must be larger than 0.' — that error is
    what em.extract_feature_vecs / matcher.fit raise internally when handed
    a 0-row table, because they compute their parallel chunk count as
    min(n_jobs, len(table)) and then call np.array_split(table, 0)."""
    if len(df) == 0:
        msg = f"{stage_name} produced 0 rows."
        if hint:
            msg += " " + hint
        raise ValueError(msg)


def attach_labels(cfg, candset, labeled_data, ltable, rtable):
    label_cfg = cfg.get("labeling", {})
    strategy = label_cfg.get("strategy", "none")
    if strategy == "none" or labeled_data is None:
        return candset, False

    label_column = label_cfg.get("label_column", "label")
    l_key = em.get_key(ltable)
    r_key = em.get_key(rtable)
    l_fk = "ltable_" + l_key
    r_fk = "rtable_" + r_key

    if label_column not in labeled_data.columns:
        raise ValueError(
            f"labeling.label_column '{label_column}' not found in io.labeled_data "
            f"columns: {list(labeled_data.columns)}"
        )

    # The labeled-data CSV's id columns are not guaranteed to spell/case
    # match the table's own key column (e.g. key "id" vs. the common
    # benchmark convention "ltable_ID"/"rtable_ID") — accept any of the
    # usual spellings instead of hardcoding one, since silently selecting
    # the wrong (or a KeyError'ing) column here is the most common way this
    # stage ends up merging 0 rows.
    l_src_col = _find_column(labeled_data, ["ltable_ID", "ltable_id", l_fk])
    r_src_col = _find_column(labeled_data, ["rtable_ID", "rtable_id", r_fk])
    if l_src_col is None or r_src_col is None:
        raise ValueError(
            "io.labeled_data is missing the expected id columns. Looked for "
            f"one of ['ltable_ID', 'ltable_id', '{l_fk}'] and "
            f"['rtable_ID', 'rtable_id', '{r_fk}'], got columns: "
            f"{list(labeled_data.columns)}"
        )

    # Join on string-cast copies of the key columns rather than the raw
    # dtypes: a very common cause of a silent 0-row merge is the candidate
    # set's fk columns (int64, from em.read_csv_metadata) not matching the
    # labeled CSV's id columns (object/str, from a plain pd.read_csv) even
    # though the values "look" the same.
    merge_l, merge_r = "__label_merge_l", "__label_merge_r"
    candset_join = candset.copy()
    candset_join[merge_l] = candset_join[l_fk].astype(str)
    candset_join[merge_r] = candset_join[r_fk].astype(str)

    labels = labeled_data[[l_src_col, r_src_col, label_column]].copy()
    labels[merge_l] = labels[l_src_col].astype(str)
    labels[merge_r] = labels[r_src_col].astype(str)

    merged = candset_join.merge(
        labels[[merge_l, merge_r, label_column]], on=[merge_l, merge_r], how="inner"
    )
    merged.drop(columns=[merge_l, merge_r], inplace=True)
    em.copy_properties(candset, merged)

    _require_nonempty(
        merged,
        "Attaching labels to the candidate set",
        hint=(
            f"None of the {len(candset)} candidate pairs matched an "
            f"({l_src_col!r}, {r_src_col!r}) pair in io.labeled_data "
            f"(matched against candidate set columns {l_fk!r}/{r_fk!r}). "
            "Check that the id values actually overlap and that blocking "
            "isn't discarding every true match."
        ),
    )
    log.info("Attached labels to candidate set: %d labeled pairs", len(merged))
    return merged, True


# --------------------------------------------------------------------------
# Stage: feature generation
# --------------------------------------------------------------------------

def build_feature_table(cfg, ltable, rtable):
    fg_cfg = cfg.get("feature_generation", {})
    feature_table = em.get_features_for_matching(
        ltable, rtable,
        validate_inferred_attr_types=fg_cfg.get("validate_inferred_attr_types", False),
    )

    select_features = fg_cfg.get("select_features")
    if select_features:
        feature_table = feature_table[feature_table["feature_name"].isin(select_features)].reset_index(drop=True)

    for bb in fg_cfg.get("blackbox_features", []):
        module_name, func_name = bb["function"].rsplit(".", 1)
        import importlib
        mod = importlib.import_module(module_name)
        feature_table = em.add_blackbox_feature(
            feature_table, bb["feature_name"], getattr(mod, func_name)
        )

    return feature_table


def extract_features(cfg, labeled_candset, feature_table, label_column=None):
    fg_cfg = cfg.get("feature_generation", {})
    attrs_after = fg_cfg.get("attrs_after")
    # The label column must survive feature extraction so matchers can
    # train against it; extract_feature_vecs only keeps key/fk columns
    # plus whatever is listed in attrs_before/attrs_after.
    if label_column:
        attrs_after = list(attrs_after) if attrs_after else []
        if label_column not in attrs_after:
            attrs_after.append(label_column)
    return em.extract_feature_vecs(
        labeled_candset,
        feature_table=feature_table,
        attrs_before=fg_cfg.get("attrs_before"),
        attrs_after=attrs_after,
        show_progress=fg_cfg.get("show_progress", False),
        n_jobs=fg_cfg.get("n_jobs", 1),
    )


# --------------------------------------------------------------------------
# Stage: matching
# --------------------------------------------------------------------------

def build_matcher(name, m_cfg, feature_table):
    method = m_cfg["method"]
    if method in ML_MATCHER_REGISTRY:
        cls = ML_MATCHER_REGISTRY[method]
        params = dict(m_cfg.get("method_params", {}))
        return cls(name=name, **params)
    if method == RULE_MATCHER_NAME:
        matcher = em.BooleanRuleMatcher(name=name)
        for rule in m_cfg.get("rules", []):
            matcher.add_rule(rule, feature_table)
        return matcher
    raise ValueError(f"Unknown matching method: {method}")


def run_ml_matcher(name, matcher, m_cfg, feature_vecs, label_column, exclude_attrs, output_dir):
    split_cfg = m_cfg.get("train_test_split") or {}
    train_proportion = split_cfg.get("train_proportion", 0.5)
    random_state = split_cfg.get("random_state")

    # em.split_train_test floors/ceils train_proportion * len(feature_vecs)
    # into train/test row counts; with too few labeled rows one side comes
    # out 0, which then hits the same 'number sections must be larger than
    # 0' failure inside fit()/predict() as an outright empty table would.
    if len(feature_vecs) < 2:
        raise ValueError(
            f"Matcher '{name}': only {len(feature_vecs)} labeled feature "
            "vector(s) available, need at least 2 to form a non-empty "
            "train/test split. Check io.labeled_data and blocking recall."
        )

    split = em.split_train_test(
        feature_vecs, train_proportion=train_proportion, random_state=random_state
    )
    train, test = split["train"], split["test"]

    matcher.fit(
        table=train,
        exclude_attrs=exclude_attrs,
        target_attr=label_column,
    )
    predictions = matcher.predict(
        table=test,
        exclude_attrs=exclude_attrs,
        target_attr="predicted_label",
        append=True,
        inplace=False,
    )

    pred_path = os.path.join(output_dir, f"{name}.csv")
    predictions.to_csv(pred_path, index=False)
    log.info("Wrote predictions for matcher '%s' to %s", name, pred_path)

    eval_summary = em.eval_matches(predictions, label_column, "predicted_label")
    return predictions, eval_summary


def run_rule_matcher(name, matcher, feature_vecs, label_column, output_dir):
    predictions = matcher.predict(
        table=feature_vecs, target_attr="predicted_label", append=True, inplace=False,
    )
    # predict(..., inplace=False) returns a fresh DataFrame that is not yet
    # registered in the catalog; eval_matches needs the key/fk metadata.
    em.copy_properties(feature_vecs, predictions)

    pred_path = os.path.join(output_dir, f"{name}.csv")
    predictions.to_csv(pred_path, index=False)
    log.info("Wrote predictions for matcher '%s' to %s", name, pred_path)

    eval_summary = None
    if label_column and label_column in predictions.columns:
        eval_summary = em.eval_matches(predictions, label_column, "predicted_label")
    return predictions, eval_summary


def run_matcher_selection(cfg, feature_vecs, feature_table, label_column, exclude_attrs, output_dir):
    ms_cfg = cfg.get("matcher_selection", {})
    if not ms_cfg.get("enabled", False):
        return

    matching_cfg = cfg["matching"]
    candidate_names = ms_cfg.get("candidates") or [
        name for name, m in matching_cfg["matchers"].items() if m["method"] in ML_MATCHER_REGISTRY
    ]
    unknown = [n for n in candidate_names if n not in matching_cfg["matchers"]]
    if unknown:
        raise ValueError(f"matcher_selection.candidates references unknown matcher(s): {unknown}")
    non_ml = [n for n in candidate_names if matching_cfg["matchers"][n]["method"] not in ML_MATCHER_REGISTRY]
    if non_ml:
        raise ValueError(f"matcher_selection.candidates must all be ML matchers, got non-ML: {non_ml}")

    log.info("Running select_matcher over candidates: %s", candidate_names)
    # Fresh matcher instances — select_matcher fits each one internally
    # during cross-validation, so these must not be the same objects used
    # (and already fit) in the per-matcher train/predict loop below.
    matchers = [
        build_matcher(name, matching_cfg["matchers"][name], feature_table)
        for name in candidate_names
    ]

    result = em.select_matcher(
        matchers,
        table=feature_vecs,
        exclude_attrs=exclude_attrs,
        target_attr=label_column,
        k=ms_cfg.get("k", 5),
        metric_to_select_matcher=ms_cfg.get("metric_to_select_matcher", "precision"),
        metrics_to_display=ms_cfg.get("metrics_to_display", ["precision", "recall", "f1"]),
        random_state=ms_cfg.get("random_state"),
    )

    cv_stats_path = os.path.join(output_dir, ms_cfg.get("output_csv", "matcher_selection.csv"))
    result["cv_stats"].to_csv(cv_stats_path, index=False)
    log.info("Wrote matcher_selection cross-validation stats to %s", cv_stats_path)
    log.info("select_matcher chose: '%s' (%s)", result["selected_matcher"].name, ms_cfg.get("metric_to_select_matcher", "precision"))


def run_matching(cfg, candset, labeled, feature_table, output_dir):
    matching_cfg = cfg["matching"]
    label_cfg = cfg.get("labeling", {})
    label_column = label_cfg.get("label_column", "label") if labeled else None

    l_key_col = [c for c in candset.columns if c.startswith("ltable_")][0]
    r_key_col = [c for c in candset.columns if c.startswith("rtable_")][0]
    exclude_attrs = [em.get_key(candset), l_key_col, r_key_col]
    if label_column:
        exclude_attrs.append(label_column)

    feature_vecs = None
    if any(m["method"] in ML_MATCHER_REGISTRY for m in matching_cfg["matchers"].values()):
        if not labeled:
            raise ValueError(
                "ML matchers require labeled data; set io.labeled_data and "
                "labeling.strategy: from_file in the config."
            )
        _require_nonempty(
            candset, "The labeled candidate set going into feature extraction"
        )
        feature_vecs = extract_features(cfg, candset, feature_table, label_column)
        _require_nonempty(
            feature_vecs,
            "em.extract_feature_vecs",
            hint="Got a labeled candidate set but 0 feature vectors came out.",
        )

    run_matcher_selection(cfg, feature_vecs, feature_table, label_column, exclude_attrs, output_dir)

    eval_rows = []
    for name, m_cfg in matching_cfg["matchers"].items():
        method = m_cfg["method"]
        log.info("Running matcher '%s' (%s)", name, method)
        matcher = build_matcher(name, m_cfg, feature_table)

        if method in ML_MATCHER_REGISTRY:
            _, eval_summary = run_ml_matcher(
                name, matcher, m_cfg, feature_vecs, label_column, exclude_attrs, output_dir
            )
        else:
            source_table = feature_vecs if feature_vecs is not None else candset
            _, eval_summary = run_rule_matcher(
                name, matcher, source_table, label_column, output_dir
            )

        if eval_summary is not None:
            eval_rows.append({
                "matcher": name,
                "method": method,
                "precision": eval_summary["precision"],
                "recall": eval_summary["recall"],
                "f1": eval_summary["f1"],
            })

    if eval_rows:
        eval_df = pd.DataFrame(eval_rows)
        eval_path = os.path.join(output_dir, cfg.get("evaluation", {}).get("output_csv", "evaluation.csv"))
        eval_df.to_csv(eval_path, index=False)
        log.info("Wrote evaluation summary to %s", eval_path)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Config-driven Magellan (py_entitymatching) pipeline")
    parser.add_argument("--input", required=True, help="Input directory containing ltable/rtable/labeled_data CSVs")
    parser.add_argument("--output", required=True, help="Output directory for predictions and evaluation")
    parser.add_argument("--config", required=True, help="Path to the pipeline YAML config")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    cfg = load_config(args.config)

    ltable, rtable, labeled_data = load_tables(cfg, args.input)

    # Feature table used both for rule-based blocking and matching.
    feature_table_for_blocking = em.get_features_for_blocking(ltable, rtable, validate_inferred_attr_types=False)

    candset = run_blocking(cfg, ltable, rtable, feature_table_for_blocking)
    run_debug_blocker(cfg, candset, ltable, rtable, args.output)

    candset, labeled = attach_labels(cfg, candset, labeled_data, ltable, rtable)

    feature_table = build_feature_table(cfg, ltable, rtable)
    run_matching(cfg, candset, labeled, feature_table, args.output)

    log.info("Pipeline finished. Output written to %s", args.output)


if __name__ == "__main__":
    sys.exit(main())