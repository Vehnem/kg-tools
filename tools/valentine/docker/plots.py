#!/usr/bin/env python3
from pathlib import Path
import argparse

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


plt.style.use("ggplot")


def save(fig, outdir, name):
    fig.tight_layout()
    fig.savefig(outdir / f"{name}.png", dpi=300)
    fig.savefig(outdir / f"{name}.pdf")
    plt.close(fig)


def main(csv_file, output_dir):

    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_file)

    metric_cols = [
        "Precision",
        "Recall",
        "F1",
        "runtime_seconds"
    ]

    ###################################################
    # Durchschnittswerte
    ###################################################

    summary = (
        df.groupby("matcher")[metric_cols]
        .mean()
        .sort_values("F1", ascending=False)
    )

    summary.to_csv(output_dir / "average_metrics.csv")

    ###################################################
    # Ranking
    ###################################################

    ranking = summary.sort_values("F1", ascending=False)

    print("\n=== Ranking nach F1 ===\n")
    print(ranking)

    ranking.to_csv(output_dir / "ranking.csv")

    ###################################################
    # Balkendiagramm F1
    ###################################################

    fig, ax = plt.subplots(figsize=(8,5))

    ranking["F1"].plot.bar(ax=ax)

    ax.set_ylabel("Average F1")
    ax.set_xlabel("")
    ax.set_title("Average F1 Score by Matcher")

    save(fig, output_dir, "bar_f1")

    ###################################################
    # Precision
    ###################################################

    fig, ax = plt.subplots(figsize=(8,5))

    ranking["Precision"].plot.bar(ax=ax)

    ax.set_ylabel("Average Precision")
    ax.set_title("Average Precision")

    save(fig, output_dir, "bar_precision")

    ###################################################
    # Recall
    ###################################################

    fig, ax = plt.subplots(figsize=(8,5))

    ranking["Recall"].plot.bar(ax=ax)

    ax.set_ylabel("Average Recall")
    ax.set_title("Average Recall")

    save(fig, output_dir, "bar_recall")

    ###################################################
    # Runtime
    ###################################################

    fig, ax = plt.subplots(figsize=(8,5))

    ranking["runtime_seconds"].plot.bar(ax=ax)

    ax.set_ylabel("Seconds")
    ax.set_title("Average Runtime")

    save(fig, output_dir, "bar_runtime")

    ###################################################
    # Scatter Runtime vs F1
    ###################################################

    fig, ax = plt.subplots(figsize=(7,6))

    ax.scatter(
        summary["runtime_seconds"],
        summary["F1"],
        s=120
    )

    for matcher, row in summary.iterrows():
        ax.text(
            row["runtime_seconds"],
            row["F1"],
            matcher,
            fontsize=9
        )

    ax.set_xlabel("Average Runtime (s)")
    ax.set_ylabel("Average F1")

    ax.set_title("Runtime vs F1")

    save(fig, output_dir, "runtime_vs_f1")

    ###################################################
    # Heatmap
    ###################################################

    heat = df.pivot_table(
        index="dataset",
        columns="matcher",
        values="F1",
        aggfunc="mean"
    )

    fig, ax = plt.subplots(figsize=(10,12))

    im = ax.imshow(
        heat.values,
        aspect="auto",
        interpolation="nearest"
    )

    ax.set_xticks(np.arange(len(heat.columns)))
    ax.set_xticklabels(heat.columns, rotation=45, ha="right")

    ax.set_yticks(np.arange(len(heat.index)))
    ax.set_yticklabels(heat.index, fontsize=7)

    cbar = plt.colorbar(im)
    cbar.set_label("F1")

    ax.set_title("Heatmap of F1 Scores")

    save(fig, output_dir, "heatmap_f1")

    ###################################################
    # Boxplot
    ###################################################

    fig, ax = plt.subplots(figsize=(9,5))

    df.boxplot(
        column="F1",
        by="matcher",
        ax=ax,
        grid=False
    )

    plt.suptitle("")
    ax.set_title("Distribution of F1 Scores")

    ax.set_xlabel("")
    ax.set_ylabel("F1")

    save(fig, output_dir, "boxplot_f1")

    ###################################################
    # TP FP FN
    ###################################################

    totals = (
        df.groupby("matcher")[["TP","FP","FN"]]
        .sum()
    )

    fig, ax = plt.subplots(figsize=(9,5))

    totals.plot.bar(ax=ax)

    ax.set_title("Total TP / FP / FN")

    save(fig, output_dir, "tp_fp_fn")

    print(f"\nPlots saved:\n{output_dir}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "csv",
        type=Path,
        help="CSV from Valentine"
    )

    parser.add_argument(
        "output",
        type=Path,
        help="Output directory"
    )

    args = parser.parse_args()

    main(args.csv, args.output)