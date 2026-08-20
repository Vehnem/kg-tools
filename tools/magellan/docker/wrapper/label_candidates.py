#!/usr/bin/env python3
"""
label_candidates.py — interactive labeling helper for the Magellan
pipeline, wrapping py_entitymatching's em.label_table.

This is a separate, standalone script rather than part of run_magellan.py
on purpose: em.label_table() launches a GUI (py_entitymatching.gui.table_gui,
built on PyQt5) and blocks until the user closes it. That's fundamentally
incompatible with run_magellan.py's role as a headless, --input/--output/
--config batch pipeline that should also work inside the Docker image.
Run this script locally, on a machine with a display; it is NOT usable
inside the Dockerfile's container, and is not wired into the Makefile's
`test_cleanclean` target.

Requires PyQt5 (`pip install PyQt5`) in addition to the base
requirements.txt — deliberately NOT pinned there, since it is only
needed for this one interactive workflow, not the batch pipeline.

Usage:
    python label_candidates.py --input <input_dir> --output <output_dir> --config <config.yaml> \
        [--sample-size N] [--seed 42]

What it does:
    1. Reads ltable/rtable and runs the SAME blocking config as
       run_magellan.py (section `blocking` in the given YAML), so the
       candidate set you label matches what the pipeline will actually
       see.
    2. Optionally down-samples the candidate set to a manageable size
       for manual labeling via em.sample_table.
    3. Opens the py_entitymatching labeling GUI (em.label_table). Enter
       0 (non-match) or 1 (match) per row; close the window when done.
    4. Writes the result to <output_dir>/labeled_pairs.csv in exactly
       the format run_magellan.py's io.labeled_data expects:
       columns `ltable_ID`, `rtable_ID`, `<label_column>`.
"""

import argparse
import os
import sys

import py_entitymatching as em

# Reuse the exact same config parsing / table loading / blocking logic as
# the main pipeline, so the labeled candidate set is guaranteed to match
# what run_magellan.py will produce from the same config.
import run_magellan as rm


def main():
    parser = argparse.ArgumentParser(
        description="Interactive labeling helper (em.label_table GUI) for the Magellan pipeline"
    )
    parser.add_argument("--input", required=True, help="Input directory containing ltable/rtable CSVs")
    parser.add_argument("--output", required=True, help="Output directory for labeled_pairs.csv")
    parser.add_argument("--config", required=True, help="Path to the pipeline YAML config (reuses io + blocking)")
    parser.add_argument("--sample-size", type=int, default=None,
                         help="If set, randomly down-sample the candidate set to this many pairs before labeling")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for --sample-size")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    cfg = rm.load_config(args.config)
    label_column = cfg.get("labeling", {}).get("label_column", "label")

    ltable, rtable, _ = rm.load_tables(cfg, args.input)
    feature_table_for_blocking = em.get_features_for_blocking(ltable, rtable, validate_inferred_attr_types=False)
    candset = rm.run_blocking(cfg, ltable, rtable, feature_table_for_blocking)

    if args.sample_size and args.sample_size < len(candset):
        rm.log.info("Down-sampling candidate set from %d to %d pairs for labeling", len(candset), args.sample_size)
        candset = em.sample_table(candset, args.sample_size, verbose=False)

    rm.log.info("Opening labeling GUI for %d candidate pairs (close the window when done)...", len(candset))
    try:
        labeled = em.label_table(candset, label_column)
    except ImportError as exc:
        rm.log.error(
            "em.label_table requires PyQt5, which is not installed (pip install PyQt5) "
            "and additionally requires a display (X11/Wayland) - it will not run inside "
            "the Dockerfile's headless container. Original error: %s", exc
        )
        return 1

    l_key = em.get_key(ltable)
    r_key = em.get_key(rtable)
    l_fk = "ltable_" + l_key
    r_fk = "rtable_" + r_key

    out_df = labeled[[l_fk, r_fk, label_column]].rename(
        columns={l_fk: "ltable_ID", r_fk: "rtable_ID"}
    )
    out_path = os.path.join(args.output, "labeled_pairs.csv")
    out_df.to_csv(out_path, index=False)
    rm.log.info("Wrote %d labeled pairs to %s", len(out_df), out_path)
    rm.log.info(
        "Point io.labeled_data at this file (relative to --input) to use it with run_magellan.py"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
