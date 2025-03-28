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
    if len(sys.argv) != 4:
        print("Usage: python main.py <path1> <path2> <outputfile>")
        sys.exit(1)

    path1 = sys.argv[1]
    path2 = sys.argv[2]
    output_file = sys.argv[3]

    # Load data using pandas
    df1 = pd.read_csv(path1)
    df2 = pd.read_csv(path2)

    # Instantiate matcher and run
    matcher = JaccardDistanceMatcher()
    matches = valentine_match(df1, df2, matcher)

    # Print matches
    print("Found the following matches:")
    pp.pprint(matches)

    print("\nGetting the one-to-one matches:")
    one_to_one_matches = matches.one_to_one()
    pp.pprint(one_to_one_matches)

    # If ground truth available, calculate metrics
    ground_truth = [('Cited by', 'Cited by'),
                    ('Authors', 'Authors'),
                    ('EID', 'EID')]

    metrics = matches.get_metrics(ground_truth)

    print("\nAccording to the ground truth:")
    pp.pprint(ground_truth)

    print("\nThese are the scores of the default metrics for the matcher:")
    pp.pprint(metrics)

    print("\nYou can also get specific metric scores:")
    specific_metrics = matches.get_metrics(ground_truth, metrics={
        PrecisionTopNPercent(n=80),
        F1Score()
    })
    pp.pprint(specific_metrics)

    print("\nThe MatcherResults object is a dict and can be treated such:")
    for match in matches:
        print(f"{str(match): <60} {matches[match]}")

    # Save matches to output file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=4)
    print(f"Matches saved to {output_file}")

if __name__ == '__main__':
    main()