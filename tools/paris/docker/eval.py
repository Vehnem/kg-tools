#!/usr/bin/env python3

import argparse

def evaluate(predicted, gt):
    predicted = set(predicted)

    tp_set = predicted & gt
    fp_set = predicted - gt
    fn_set = gt - predicted

    tp = len(tp_set)
    fp = len(fp_set)
    fn = len(fn_set)

    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0
    )

    return {
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "Precision": precision,
        "Recall": recall,
        "F1": f1,
        "FP_matches": fp_set,
        "FN_matches": fn_set,
    }

def load_predictions(tsv_file):

    matches = set()

    with open(tsv_file, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")

            if len(parts) < 2:
                continue

            e1 = parts[0]
            e2 = parts[1]

            if "Restaurant" not in e1 or "Restaurant" not in e2:
                continue

            if "Address" in e1 or "Address" in e2:
                continue

            matches.add((e1, e2))

    return matches


def generate_ground_truth(n):

    base = "http://www.okkam.org/oaie/restaurant1-"

    gt = set()

    for i in range(0, n + 1):
        r = f"{base}Restaurant{i}"
        gt.add((r, r))

    return gt


def main():

    parser = argparse.ArgumentParser(
        description="Evaluate PARIS restaurant matching"
    )

    parser.add_argument(
        "matches",
        help="PARIS TSV output"
    )

    parser.add_argument(
        "restaurants",
        type=int,
        help="Ground Truth Restaurants Count"
    )

    args = parser.parse_args()


    predicted = load_predictions(args.matches)

    gt = generate_ground_truth(args.restaurants)


    print(f"Predicted matches: {len(predicted)}")
    print(f"Ground truth:      {len(gt)}")
    print()

    stats = evaluate(predicted, gt)

    for k, v in stats.items():
        if k in ["FP_matches", "FN_matches"]:
            continue

        if isinstance(v, float):
            print(f"{k:10}: {v:.4f}")
        else:
            print(f"{k:10}: {v}")

    print("\nFalse Positives:")
    for fp in stats["FP_matches"]:
        print(fp[0], " <---> ", fp[1])

    print("\nFalse Negatives:")
    for fn in stats["FN_matches"]:
        print(fn[0], " <---> ", fn[1])


if __name__ == "__main__":
    main()