#!/usr/bin/env python3
"""
run_ditto.py
============
Thin orchestration wrapper around Ditto's own scripts
(https://github.com/megagonlabs/ditto).

Ditto does not ship a single config file - all settings are normally passed
as CLI flags to `matcher.py` (matching/inference) or `train_ditto.py`
(training). This wrapper keeps ALL of those settings in one YAML file
(see ditto_config.yaml / CONFIG_REFERENCE.md) and translates them into the
exact CLI call Ditto expects, then runs it as a subprocess inside the Ditto
repo. That way it stays 100% compatible with upstream Ditto - nothing about
Ditto itself is reimplemented here.

Usage
-----
    python run_ditto.py --input input/candidates.jsonl \
                         --output output/matched.jsonl \
                         --config ditto_config.yaml

    # Training mode (set mode: train in the config; --input/--output are
    # not needed since train_ditto.py reads trainset/validset/testset from
    # configs.json instead):
    python run_ditto.py --config ditto_config.yaml

Requirements
------------
* A local clone of https://github.com/megagonlabs/ditto with its own Python
  environment installed (see that repo's README.md / requirements.txt).
* For mode: match, a trained checkpoint at
  `<paths.checkpoint_path>/<task.name>/model.pt`.
* PyYAML (`pip install pyyaml`) for this wrapper itself.

configs.json
------------
Ditto looks up datasets by name in a `configs.json` file inside its own
repo. Instead of requiring that file to already exist, this wrapper
generates/updates the entry for `task.name` itself on every run, from the
`task.task_type` / `task.vocab` / `task.trainset` / `task.validset` /
`task.testset` fields in the YAML config. Any existing entries for other
task names in `configs.json` are left untouched; an existing entry with the
same name is overwritten.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not cfg:
        raise ValueError(f"Config file '{path}' is empty or invalid.")
    for required in ("task", "paths", "model"):
        if required not in cfg:
            raise ValueError(f"Config file '{path}' is missing required section '{required}'.")
    return cfg


def build_task_entry(cfg: dict) -> dict:
    """Build the configs.json entry for `task` from the wrapper config.

    Ditto's own configs.json format is a JSON list of dicts like:
        {
            "name": "Structured/Beer",
            "task_type": "classification",
            "vocab": ["0", "1"],
            "trainset": "data/er_magellan/Structured/Beer/train.txt",
            "validset": "data/er_magellan/Structured/Beer/valid.txt",
            "testset": "data/er_magellan/Structured/Beer/test.txt"
        }
    trainset/validset/testset paths are resolved relative to paths.ditto_repo
    (i.e. exactly as Ditto itself expects them, since matcher.py/
    train_ditto.py are run with that repo as the working directory).
    """
    task = cfg["task"]
    for required in ("name", "trainset", "validset", "testset"):
        if required not in task:
            raise ValueError(
                f"config section 'task' is missing required field '{required}' "
                f"(needed to generate configs.json)."
            )

    task_type = task.get("task_type", "classification")
    entry = {
        "name": task["name"],
        "task_type": task_type,
        "trainset": task["trainset"],
        "validset": task["validset"],
        "testset": task["testset"],
    }
    if task_type == "classification":
        entry["vocab"] = task.get("vocab", ["0", "1"])

    return entry


def write_configs_json(ditto_repo: Path, entry: dict) -> Path:
    """Insert/update `entry` (by name) in <ditto_repo>/configs.json.

    Other existing entries (other task names) are kept as-is. The file is
    created if it doesn't exist yet.
    """
    configs_path = ditto_repo / "configs.json"

    configs = []
    if configs_path.exists():
        with open(configs_path, "r", encoding="utf-8") as f:
            try:
                configs = json.load(f)
            except json.JSONDecodeError:
                configs = []
        if not isinstance(configs, list):
            configs = []

    configs = [c for c in configs if c.get("name") != entry["name"]]
    configs.append(entry)

    with open(configs_path, "w", encoding="utf-8") as f:
        json.dump(configs, f, indent=2)
        f.write("\n")

    return configs_path


def build_match_command(cfg: dict, input_path: str, output_path: str, python_bin: str) -> list[str]:
    """Build the CLI call to Ditto's matcher.py from the config."""
    task = cfg["task"]["name"]
    model = cfg["model"]
    opt = cfg.get("optimizations", {})

    cmd = [
        python_bin, "matcher.py",
        "--task", task,
        "--input_path", input_path,
        "--output_path", output_path,
        "--lm", model["lm"],
        "--max_len", str(model["max_len"]),
        "--checkpoint_path", cfg["paths"]["checkpoint_path"],
    ]

    if model.get("use_gpu", False):
        cmd.append("--use_gpu")
    if model.get("fp16", False):
        cmd.append("--fp16")

    dk = opt.get("domain_knowledge", {})
    if dk.get("enabled", False):
        cmd += ["--dk", dk["mode"]]

    su = opt.get("summarization", {})
    if su.get("enabled", False):
        cmd.append("--summarize")

    return cmd


def build_train_command(cfg: dict, python_bin: str) -> list[str]:
    """Build the CLI call to Ditto's train_ditto.py from the config."""
    task = cfg["task"]["name"]
    model = cfg["model"]
    training = cfg.get("training", {})
    opt = cfg.get("optimizations", {})

    cmd = [
        python_bin, "train_ditto.py",
        "--task", task,
        "--run_id", str(training.get("run_id", 0)),
        "--batch_size", str(training.get("batch_size", 64)),
        "--max_len", str(model["max_len"]),
        "--lr", str(training.get("lr", 3e-5)),
        "--n_epochs", str(training.get("n_epochs", 20)),
        "--logdir", training.get("logdir", cfg["paths"]["checkpoint_path"]),
        "--lm", model["lm"],
    ]

    if training.get("finetuning", True):
        cmd.append("--finetuning")
    if training.get("save_model", True):
        cmd.append("--save_model")
    if model.get("fp16", False):
        cmd.append("--fp16")
    if training.get("size"):
        cmd += ["--size", str(training["size"])]

    da = opt.get("data_augmentation", {})
    if da.get("enabled", False):
        if not da.get("operator"):
            raise ValueError("optimizations.data_augmentation.enabled is true but 'operator' is not set.")
        cmd += ["--da", da["operator"], "--alpha_aug", str(da.get("alpha_aug", 0.8))]

    dk = opt.get("domain_knowledge", {})
    if dk.get("enabled", False):
        cmd += ["--dk", dk["mode"]]

    su = opt.get("summarization", {})
    if su.get("enabled", False):
        cmd.append("--summarize")

    return cmd


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Ditto (matching or training) driven by a single YAML config file."
    )
    parser.add_argument("--input", help="Input JSONL file with candidate pairs (match mode).")
    parser.add_argument("--output", help="Output JSONL file (match mode).")
    parser.add_argument("--config", required=True, help="Path to the YAML configuration file.")
    args = parser.parse_args()

    cfg = load_config(args.config)

    ditto_repo = Path(cfg["paths"]["ditto_repo"]).expanduser().resolve()
    if not ditto_repo.exists():
        sys.exit(
            f"paths.ditto_repo '{ditto_repo}' does not exist. "
            f"Clone https://github.com/megagonlabs/ditto there, or update the config."
        )

    task_entry = build_task_entry(cfg)
    configs_path = ditto_repo / "configs.json"
    write_configs_json(ditto_repo, task_entry)
    print(f"Configs    : {configs_path} (task '{task_entry['name']}' written)")

    python_bin = cfg.get("runtime", {}).get("python_bin", sys.executable)
    mode = cfg.get("mode", "match")

    if mode == "match":
        input_path = args.input or cfg["paths"].get("input_path")
        output_path = args.output or cfg["paths"].get("output_path")
        if not input_path or not output_path:
            sys.exit(
                "mode: match requires --input and --output "
                "(or paths.input_path / paths.output_path in the config)."
            )
        cmd = build_match_command(cfg, input_path, output_path, python_bin)
    elif mode == "train":
        cmd = build_train_command(cfg, python_bin)
    else:
        sys.exit(f"Unknown mode '{mode}' in config (expected 'match' or 'train').")

    print("Ditto repo :", ditto_repo)
    print("Command    :", " ".join(cmd))

    env = os.environ.copy()
    gpu_devices = cfg.get("runtime", {}).get("cuda_visible_devices")
    if gpu_devices is not None:
        env["CUDA_VISIBLE_DEVICES"] = str(gpu_devices)

    result = subprocess.run(cmd, cwd=str(ditto_repo), env=env)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()