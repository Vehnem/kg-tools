import json
import os
import sys
import glob
import pandas as pd
import time
from valentine import valentine_match
from valentine.algorithms import (
    Coma,
    Cupid,
    DistributionBased,
    JaccardDistanceMatcher,
    SimilarityFlooding,
)

MATCHERS = {
    "Coma": Coma,
    "Cupid": Cupid,
    "DistributionBased": DistributionBased,
    "JaccardDistanceMatcher": JaccardDistanceMatcher,
    "SimilarityFlooding": SimilarityFlooding,
}


def load_ground_truth(mapping_file):
    with open(mapping_file, encoding="utf8") as f:
        mapping = json.load(f)

    gt = set()

    for m in mapping["matches"]:
        gt.add((m["source_column"], m["target_column"]))

    return gt


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


def run_matcher(source_csv, target_csv, matcher_name, matcher_cls,
                output_json, cutoff=None):
    start = time.perf_counter()

    df1 = pd.read_csv(source_csv, nrows=cutoff)
    df2 = pd.read_csv(target_csv, nrows=cutoff)

    matcher = matcher_cls()

    matches = valentine_match([df1, df2], matcher)
    one_to_one = matches.one_to_one_greedy()

    results = []
    predicted = []

    for columnpair, score in one_to_one.items():
        results.append({
            "id_1": columnpair.source_column,
            "id_2": columnpair.target_column,
            "score": float(score),
            "id_type": type(columnpair.source_column).__name__
        })

        predicted.append(
            (columnpair.source_column, columnpair.target_column)
        )

    with open(output_json, "w", encoding="utf8") as f:
        json.dump(
            {"matches": results, "blocks": [], "clusters": []},
            f,
            indent=4,
            ensure_ascii=False,
        )

    runtime = time.perf_counter() - start

    return predicted, runtime


def process_dataset(folder, output_root, cutoff):

    source = glob.glob(os.path.join(folder, "*_source.csv"))[0]
    target = glob.glob(os.path.join(folder, "*_target.csv"))[0]
    mapping = glob.glob(os.path.join(folder, "*_mapping.json"))[0]

    dataset_name = os.path.basename(folder)

    dataset_output = os.path.join(output_root, dataset_name)
    os.makedirs(dataset_output, exist_ok=True)

    ground_truth = load_ground_truth(mapping)

    rows = []

    for matcher_name, matcher_cls in MATCHERS.items():

        print(f"Running {matcher_name} on {os.path.basename(folder)}")

        output_file = os.path.join(
            str(dataset_output),
            f"{matcher_name}_matches.json"
        )

        predicted, runtime = run_matcher(
            source,
            target,
            matcher_name,
            matcher_cls,
            output_file,
            cutoff,
        )

        metrics = evaluate(predicted, ground_truth)

        rows.append({
            "dataset": os.path.basename(folder),
            "matcher": matcher_name,
            "runtime_seconds": runtime,
            **metrics
        })

    return rows


def main():

    if len(sys.argv) not in [2, 3]:
        print("Usage:")
        print("python benchmark.py <dataset_root> [cutoff]")
        sys.exit(1)

    root = sys.argv[1]

    cutoff = None

    if len(sys.argv) == 3:
        cutoff = int(sys.argv[2])

    evaluation_rows = []

    output_folder_name = "benchmark_results"
    output_root = os.path.join(root, output_folder_name)
    os.makedirs(output_root, exist_ok=True)

    for entry in sorted(os.listdir(root)):
        if entry == output_folder_name:
            continue

        folder = os.path.join(root, entry)

        if not os.path.isdir(folder):
            continue

        evaluation_rows.extend(
            process_dataset(folder, output_root, cutoff)
        )

    df = pd.DataFrame(evaluation_rows)

    df.to_csv(
        os.path.join(output_root, "evaluation.csv"),
        index=False,
    )

    print(df)


if __name__ == "__main__":
    main()