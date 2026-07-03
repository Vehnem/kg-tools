import json
import os
import sys
import pandas as pd
from valentine.metrics import F1Score, PrecisionTopNPercent

from valentine import valentine_match
from valentine.algorithms import JaccardDistanceMatcher
import pprint
pp = pprint.PrettyPrinter(indent=4, sort_dicts=False)


def main():
    if len(sys.argv) != 4 and len(sys.argv) != 5:
        print("Usage: python main.py <path1> <path2> <outputfile> (<csv_cutoff>)")
        sys.exit(1)

    path1 = sys.argv[1]
    path2 = sys.argv[2]
    output_file = sys.argv[3]

    cutoff = None

    if "CSV_CUTOFF" in os.environ:
        cutoff = os.environ["CSV_CUTOFF"]

    if len(sys.argv) == 5:
        cutoff = sys.argv[4]

    try:
        cutoff = int(cutoff)
        if cutoff <= 0:
            cutoff = None
    except (TypeError, ValueError):
        cutoff = None

    if cutoff is not None:
        print(f"cutoff is set to {cutoff}")
    else:
        print("Not using cutoff")

    # Load data using pandas
    df1 = pd.read_csv(path1, nrows=cutoff)
    df2 = pd.read_csv(path2, nrows=cutoff)
    # Instantiate matcher and run
    matcher = JaccardDistanceMatcher()
    matches = valentine_match(df1, df2, matcher)

    # Print matches
    print("Found the following matches:")
    pp.pprint(matches)

    print("\nGetting the one-to-one matches:")
    one_to_one_matches = matches.one_to_one()
    pp.pprint(one_to_one_matches)

    print("\nThe MatcherResults object is a dict and can be treated such:")
    for match in matches:
        print(f"{str(match): <60} {matches[match]}")

    # Convert matches to required output format
    results = []
    for ((_, left), (_, right)), measure in one_to_one_matches.items():
        results.append({
            "id_1": left,
            "id_2": right,
            "score": float(measure),
            "id_type": type(left).__name__
        })

    output_data = {"matches": results, "blocks": [], "clusters": []}

    # Save matches to output file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
    print(f"Matches saved to {output_file}")

if __name__ == '__main__':
    main()