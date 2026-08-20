# Magellan (py_entitymatching) Pipeline

Config-driven entity-resolution pipeline on top of
[`py_entitymatching`](https://sites.google.com/site/anhaidgroup/projects/magellan/py_entitymatching)
("Magellan"): all
blocking, feature-generation, and matcher hyperparameters live in a
YAML config, and `run_magellan.py` is invoked with `--input`,
`--output`, and `--config`.

See **`CONFIG_REFERENCE.md`** for the full list of supported stages,
`method` values, and parameters (verified directly against
`py_entitymatching==0.4.2` source, not from memory).

## Files

| File                          | Purpose                                                                                                        |
|-------------------------------|----------------------------------------------------------------------------------------------------------------|
| `wrapper/run_magellan.py`     | The pipeline: I/O → blocking (union/chain) → labeling → features → matcher_selection → matching → evaluation   |
| `wrapper/label_candidates.py` | Standalone interactive labeling helper (GUI, local machine only)                                               |
| `config-example.yaml`         | Fully populated example config, ready to run                                                                   |
| `CONFIG_REFERENCE.md`         | Reference for every stage/method/param                                                                         |
| `wrapper/magellan.sh`         | Thin shell wrapper calling the venv's `run_magellan.py`                                                        |
| `requirements.txt`            | Pinned dependencies (see pandas note below)                                                                    |
| `Makefile`                    | `venv` / `test` / `docker_*` targets                                                                           |
| `Dockerfile`                  | Containerized runtime                                                                                          |

## Requirements

- Python ≥ 3.7 (tested Python 3.11).
- `py_entitymatching==0.4.2` and its dependencies (installed via
  `requirements.txt`).

### ⚠️ pandas version pin

`py_entitymatching==0.4.2` (via its dependency `py-stringsimjoin`) is
**not** compatible with pandas's newer default string dtype
(reproduced on pandas 3.0: `TypeError: Cannot interpret
'<StringDtype(...)>' as a data type` inside `OverlapBlocker`/
`SortedNeighborhoodBlocker`). `requirements.txt` pins
`pandas>=2.0,<2.2`; don't upgrade past that unless you've verified
`py_entitymatching` compatibility yourself.

XGBoost support (`method: xgboost` in the config) is included by
default — `xgboost` is an optional dependency of `py_entitymatching`
itself (see `CONFIG_REFERENCE.md`, section 7a), but is pinned in
`requirements.txt` here so it's always available.

## Quickstart

```bash
# 1. Create venv, install py_entitymatching + deps
make venv

# 2. Test run against the demo dataset under $KG_TESTDATA/_snippets/magellan
make test
```

Results land under `target/` by default: one `<matcher_name>.csv` per
configured matcher plus `evaluation.csv`, and, if enabled,
`debug_blocker_output.csv` and `matcher_selection.csv`.

The test target expects the demo dataset to already be present at
`$(KG_TESTDATA)/_snippets/magellan`:

```
acm_demo.csv
dblp_demo.csv
labeled_data_demo.csv
```

`config-example.yaml`'s `io:` section points at these three files
(`ltable_path: acm_demo.csv`, `rtable_path: dblp_demo.csv`,
`labeled_data: labeled_data_demo.csv`) — see `CONFIG_REFERENCE.md`
section 1 if you need to point it at a different layout.

### Using your own data

```bash
make test \
  MAGELLAN_DIR=path/to/data \
  OUTPUT_DIR=out/my_run \
  CONFIG=my_config.yaml
```

Or directly without `make`:

```bash
.venv/bin/python3 run_magellan.py --input path/to/data --output out/my_run --config my_config.yaml
```

Or via the shell wrapper:

```bash
bash magellan.sh path/to/data out/my_run my_config.yaml
```

`<input_dir>` should contain the ltable/rtable CSVs (and, optionally, a
labeled-pairs CSV) at the relative paths given under `io:` in the
config — see `CONFIG_REFERENCE.md` section 1.

## Matcher selection (cross-validation)

Set `matcher_selection.enabled: true` in the config to have
`em.select_matcher` run k-fold CV over a chosen subset of your ML
matchers and report which one wins by precision/recall/F1 — see
`CONFIG_REFERENCE.md` section 8. This runs alongside, not instead of,
the normal per-matcher train/predict — it's a decision-support report,
all configured matchers still produce their own predictions file.

## Interactive labeling

`run_magellan.py` assumes gold labels already exist as a CSV. To
create that CSV interactively, use the separate `label_candidates.py`:

```bash
python label_candidates.py --input /home/theo/kg-testdata/_snippets/magellan/ --output /home/theo/kg-testdata/_snippets/magellan/ --config /home/theo/PycharmProjects/kg-tools-new/tools/magellan/docker/config-example.yaml
```

It reuses the same `io`/`blocking` config, runs blocking, opens
Magellan's built-in labeling GUI (`em.label_table`), and writes
`labeled_pairs.csv` in the exact format `io.labeled_data` expects.
**Requires `PyQt5` and a display** — install it separately
(`pip install PyQt5`), and run this locally rather than inside Docker
or a headless CI job. See `CONFIG_REFERENCE.md` for details and the
verified GUI-dependency caveat.

## Makefile targets

| Target                | Effect                                                                                                            |
|-----------------------|-------------------------------------------------------------------------------------------------------------------|
| `make venv`           | Creates the venv (Python 3.11) and installs `requirements.txt` into it.                                           |
| `make test`           | Runs `run_magellan.py` against `$(MAGELLAN_DIR)` (default: `$(KG_TESTDATA)/_snippets/magellan`) with `$(CONFIG)`. |
| `make clean`          | Removes `target/` and the venv.                                                                                   |
| `make docker_build`   | Builds the `kgt/magellan` Docker image.                                                                           |
| `make docker_test`    | Copies the demo dataset into `target/data` and runs a test pass inside the Docker container (via `magellan.sh`).  |
| `make docker_help`    | Shows example invocations for the Docker image.                                                                   |

All paths (`KG_TESTDATA`, `VENV_DIR`, `OUTPUT_DIR`, `CONFIG`,
`MAGELLAN_DIR`, ...) can be overridden on invocation, e.g.
`make test CONFIG=other_config.yaml`.

## Docker

```bash
make docker_build
make docker_help
docker run --rm -v $(pwd)/data:/app/data -v $(pwd)/out:/app/out \
  kgt/magellan bash magellan.sh /app/data /app/out config-example.yaml
```

## Verified library quirks worth knowing about

Both documented in full in `CONFIG_REFERENCE.md`:

- **`SortedNeighborhoodBlocker`** is explicitly marked experimental by
  the library itself and has two real bugs (broken catalog identity,
  and junk `ID` columns) that break combining it with other blockers.
  `run_magellan.py` works around both automatically.
- **`em.XGBoostMatcher`** exists in `py_entitymatching` but is only
  importable if `xgboost` is separately installed — confirmed via
  source (`try: ... except ImportError: pass` in `__init__.py`).