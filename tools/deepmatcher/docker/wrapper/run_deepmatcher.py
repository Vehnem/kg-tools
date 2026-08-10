import json
import os

import argparse
import deepmatcher as dm
import numpy as np
from pathlib import Path

import nltk
nltk.download('punkt_tab')

try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

DEFAULT_CONFIG = {
    "process": {
        "cache": "cacheddata.pth",
        "check_cached_data": True,
        "auto_rebuild_cache": True,
        "tokenize": "nltk",
        "lowercase": True,
        "embeddings": "glove.6B.50d",
        "embeddings_cache_path": "~/.vector_cache",
        "ignore_columns": [],
        "include_lengths": True,
        "id_attr": "id",
        "label_attr": "label",
        "left_prefix": "left_",
        "right_prefix": "right_",
        "use_magellan_convention": False,
        "pca": True,
    },
    "process_unlabeled": {
        "ignore_columns": None,
    },
    "model": {
        "attr_summarizer": "hybrid",
        "attr_condense_factor": "auto",
        "attr_comparator": None,
        "attr_merge": "concat",
        "classifier": "2-layer-highway",
        "hidden_size": 300,
    },
    "train": {
        "epochs": 30,
        "criterion": None,
        "optimizer": None,
        "pos_neg_ratio": None,
        "pos_weight": None,
        "label_smoothing": 0.05,
        "save_every_prefix": None,
        "save_every_freq": 1,
        "batch_size": 32,
        "device": None,
        "progress_style": "bar",
        "log_freq": 5,
        "sort_in_buckets": None,
    },
    "eval": {
        "batch_size": 32,
        "device": None,
        "progress_style": "bar",
        "log_freq": 5,
        "sort_in_buckets": None,
    },
    "prediction": {
        "output_attributes": False,
        "batch_size": 32,
        "device": None,
        "progress_style": "bar",
        "log_freq": 5,
        "sort_in_buckets": None,
    },
    "threshold": {
        "enabled": False,
        "mode": "fixed",
        "value": 0.8,
        "fraction": 0.1,
        "std_multiplier": 1.0,
        "percentile": 90,
        "output_mode": "filter",
    },
}


def load_config(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    if path.endswith((".yaml", ".yml")):
        if not _HAS_YAML:
            raise RuntimeError(
                "PyYAML is not installed (`pip install pyyaml`), "
                "but the Config-File has a .yaml/.yml Ending."
            )
        return yaml.safe_load(text)
    return json.loads(text)


def deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def compute_threshold(scores, cfg: dict) -> float:
    mode = cfg.get("mode", "fixed")

    if mode == "fixed":
        return float(cfg["value"])

    mean = float(np.mean(scores))

    if mode == "relative_to_mean":
        return mean * (1 - float(cfg.get("fraction", 0.1)))

    if mode == "relative_to_max":
        max_score = float(np.max(scores))
        return max_score * (1 - float(cfg.get("fraction", 0.1)))

    if mode == "mean_minus_std":
        std = float(np.std(scores))
        return mean - float(cfg.get("std_multiplier", 1.0)) * std

    if mode == "percentile":
        return float(np.percentile(scores, float(cfg.get("percentile", 90))))

    raise ValueError(
        f"Unknown threshold-mode '{mode}'. "
        "Use: fixed | relative_to_mean | relative_to_max | mean_minus_std | percentile"
    )


def apply_threshold(predictions, cfg: dict):
    if not cfg.get("enabled", False):
        return predictions

    scores = predictions["match_score"]
    threshold_value = compute_threshold(scores, cfg)
    print(f"Threshold-Mode '{cfg.get('mode', 'fixed')}' -> Threshold: {threshold_value:.4f}")

    output_mode = cfg.get("output_mode", "filter")
    if output_mode == "filter":
        before = len(predictions)
        predictions = predictions[scores >= threshold_value].reset_index(drop=True)
        print(f"Threshold filtered: {before} -> kept {len(predictions)} lines.")
    elif output_mode == "flag":
        predictions = predictions.copy()
        predictions["is_match"] = scores >= threshold_value
    else:
        raise ValueError(
            f"Unknown threshold.output_mode '{output_mode}'. Use: filter | flag"
        )

    return predictions


def main(
    data_directory: str,
    train_csv: str,
    validation_csv: str,
    test_csv: str,
    best_model_path: str,
    unlabeled_csv: str,
    output_csv: str,
    cfg: dict,
):
    train, validation, test = dm.data.process(
        path=data_directory,
        train=train_csv,
        validation=validation_csv,
        test=test_csv,
        **cfg["process"],
    )

    model = dm.MatchingModel(**cfg["model"])

    model.run_train(
        train,
        validation,
        best_save_path=best_model_path,
        **cfg["train"],
    )

    model.run_eval(test, **cfg["eval"])

    unlabeled = dm.data.process_unlabeled(
        path=unlabeled_csv,
        trained_model=model,
        **cfg["process_unlabeled"],
    )

    predictions = model.run_prediction(unlabeled, **cfg["prediction"])
    predictions = apply_threshold(predictions, cfg["threshold"])

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    predictions.to_csv(output_csv, index=False)
    print(f"Predictions saved: {output_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run training, eval and prediction of a deepmatcher model"
    )

    parser.add_argument(
        "--data_directory",
        required=True,
        help="Directory containing train/validation/test CSV files",
    )
    parser.add_argument("--train_csv", required=True, help="Training CSV filename")
    parser.add_argument("--validation_csv", required=True, help="Validation CSV filename")
    parser.add_argument("--test_csv", required=True, help="Test CSV filename")
    parser.add_argument("--best_model", required=True, help="Path to save the best model (.pth)")
    parser.add_argument("--unlabeled_csv", required=True, help="CSV file containing unlabeled data")
    parser.add_argument("--output", required=True, help="Path to output csv")
    parser.add_argument("--config",required=False,default=None,help="Path to deepmatcher config yaml/json")

    args = parser.parse_args()

    cfg = DEFAULT_CONFIG
    if args.config:
        cfg = deep_merge(DEFAULT_CONFIG, load_config(args.config))

    main(
        data_directory=args.data_directory,
        train_csv=args.train_csv,
        validation_csv=args.validation_csv,
        test_csv=args.test_csv,
        best_model_path=args.best_model,
        unlabeled_csv=args.unlabeled_csv,
        output_csv=args.output,
        cfg=cfg,
    )