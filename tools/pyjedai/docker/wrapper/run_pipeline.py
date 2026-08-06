import argparse
import json
import os
from pathlib import Path

import pandas as pd

import data_cleaning
import data_reading
import block_building
import block_purging
import block_cleaning
import comparison_cleaning
import clustering
import entity_matching
import evaluation

try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False


DEFAULT_CONFIG = {
    "data_cleaning": {
        "enabled": False,
        "params": {
            "remove_stopwords": True,
            "remove_punctuation": True,
            "remove_numbers": True,
            "remove_unicodes": True,
        },
    },
    "blocking": {
        "method": "standard_blocking",
        "attributes_1": None,
        "attributes_2": None,
        "method_params": {},
    },
    "block_purging": {"enabled": False, "method": "block_purging", "method_params": {}},
    "block_cleaning": {"enabled": False, "method": "block_filtering", "method_params": {"ratio": 0.8}},
    "comparison_cleaning": {
        "enabled": False,
        "method": "weighted_edge_pruning",
        "method_params": {"weighting_scheme": "EJS"},
    },
    "matching": {
        "matchers": {
            "char_bigram_tfidf": {
                "method": "entity_matching",
                "metric": "cosine",
                "tokenizer": "char_tokenizer",
                "vectorizer": "tfidf",
                "qgram": 2,
                "similarity_threshold": 0.8,
            }
        }
    },
    "clustering": {
        "enabled": False,
        "method": "unique_mapping_clustering",
        "method_params": {"similarity_threshold": 0.17},
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="pyJedAI Entity-Resolution-Pipeline")
    parser.add_argument("--file1", required=True)
    parser.add_argument("--file2", required=True)
    parser.add_argument("--gt", required=False)
    parser.add_argument("--sep", required=False, default="|", help="Separator of csv files")
    parser.add_argument("--output", required=True)
    parser.add_argument("--config", required=False, default=None)
    parser.add_argument("--attr1", required=False, help="Comma-separated Blocking-Attribute Dataset 1")
    parser.add_argument("--attr2", required=False, help="Comma-separated Blocking-Attribute Dataset 2")

    args = parser.parse_args()

    cfg = DEFAULT_CONFIG
    if args.config:
        cfg = deep_merge(DEFAULT_CONFIG, load_config(args.config))

    data = data_reading.read(args.file1, args.file2, ground_truth_path=args.gt, sep=args.sep)
    df1 = data.dataset_1
    df2 = data.dataset_2
    gt = data.ground_truth

    offset = len(df1)
    id_col1 = data.id_column_name_1
    id_col2 = data.id_column_name_2

    if cfg["data_cleaning"].get("enabled", False):
        data_cleaning.clean(data, **cfg["data_cleaning"].get("params", {}))

    attributes1 = (
        [a.strip() for a in args.attr1.split(",")] if args.attr1
        else cfg["blocking"].get("attributes_1")
    )
    attributes2 = (
        [a.strip() for a in args.attr2.split(",")] if args.attr2
        else cfg["blocking"].get("attributes_2")
    )

    print(df1.columns)
    print(df2.columns)

    # --- Pipeline-Stages ---
    blocks = block_building.block(
        data, attributes1, attributes2,
        method=cfg["blocking"]["method"],
        method_params=cfg["blocking"].get("method_params", {}),
    )

    if cfg["block_purging"].get("enabled", False):
        blocks = block_purging.purge(
            blocks, data,
            method=cfg["block_purging"]["method"],
            method_params=cfg["block_purging"].get("method_params", {}),
        )

    if cfg["block_cleaning"].get("enabled", False):
        blocks = block_cleaning.clean(
            blocks, data,
            method=cfg["block_cleaning"]["method"],
            method_params=cfg["block_cleaning"].get("method_params", {}),
        )

    if cfg["comparison_cleaning"].get("enabled", False):
        blocks = comparison_cleaning.clean(
            blocks, data,
            method=cfg["comparison_cleaning"]["method"],
            method_params=cfg["comparison_cleaning"].get("method_params", {}),
        )

    os.makedirs(args.output, exist_ok=True)
    evaluation_rows = []

    for matcher_name, matcher_cfg in cfg["matching"]["matchers"].items():
        print(f"Running {matcher_name}")
        pairs_graph, runtime = entity_matching.match(matcher_cfg, blocks, data, df1, df2)

        if cfg["clustering"].get("enabled", False):
            clustering.cluster(
                pairs_graph, data,
                method=cfg["clustering"]["method"],
                method_params=cfg["clustering"].get("method_params", {}),
            )

        results, predicted = [], []
        for node1, node2, data_dict in pairs_graph.edges(data=True):
            score = float(data_dict.get("weight", 1.0))
            if score < 0.8:
                continue

            val1 = df1.iloc[node1][id_col1] if node1 < offset else df2.iloc[node1 - offset][id_col2]
            val2 = df1.iloc[node2][id_col1] if node2 < offset else df2.iloc[node2 - offset][id_col2]

            predicted.append((val1, val2))
            results.append({"id_1": val1, "id_2": val2, "score": score, "id_type": "entity"})

        outfile = os.path.join(args.output, f"{matcher_name}.json")
        with open(outfile, "w", encoding="utf8") as f:
            json.dump({"matches": results, "blocks": [], "clusters": []}, f, indent=4, ensure_ascii=False)

        if gt is not None:
            metrics = evaluation.evaluate(predicted, gt)
            evaluation_rows.append({"matcher": matcher_name, "runtime": runtime, **metrics})

    if evaluation_rows:
        pd.DataFrame(evaluation_rows).to_csv(os.path.join(args.output, "evaluation.csv"), index=False)


if __name__ == "__main__":
    main()