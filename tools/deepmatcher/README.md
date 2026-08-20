# DeepMatcher Pipeline

Configurable training/evaluation/prediction for [DeepMatcher](https://github.com/anhaidgroup/deepmatcher),
driven by a YAML/JSON config instead of hardcoded hyperparameters.

## Files

| File                         | Purpose                                                                     |
|------------------------------|-----------------------------------------------------------------------------|
| `wrapper/run_deepmatcher.py` | Main script: training, evaluation, prediction, optional score thresholding. |
| `config-example.yaml`        | Example config with all available parameters.                               |
| `CONFIG_REFERENCE.md`        | Full reference of all config parameters, options, and defaults.             |
| `wrapper/deepmatcher.sh`     | Shell wrapper around `run_deepmatcher.py`.                                  |
| `Makefile`                   | Setup (venv, repo clone) and test run via `make`.                           |

## Requirements

- Python ≥ 3.7 (tested Python 3.8) (deepmatcher uses `torchtext.legacy`, which was removed in
  newer torchtext versions — if installation fails, check for an older
  `torchtext` version that still includes `torchtext.legacy`). 
- `git` (only for `make download`, to fetch the test datasets from the
  official deepmatcher repo).
- Internet access on the first run, since `dm.data.process(...)`
  automatically downloads word embeddings (see the "Embeddings" section
  below).

## Quickstart

```bash
# 1. Create venv, install deepmatcher, clone test datasets
make download

# 2. Test run with the example config
make test
```

Results land under `output/predictions.csv` and `output/best_model.pth`
by default.

### Using your own data

```bash
make test \
  DATA_DIR=path/to/data \
  BEST_MODEL=output/my_model.pth \
  OUTPUT_CSV=output/my_predictions.csv \
  CONFIG=my_config.yaml
```

Or directly without `make`:

```bash
venv/bin/python3 run_deepmatcher.py \
  --data_directory path/to/data \
  --train_csv train.csv \
  --validation_csv validation.csv \
  --test_csv test.csv \
  --best_model output/best_model.pth \
  --unlabeled_csv path/to/unlabeled.csv \
  --output output/predictions.csv \
  --config config-example.yaml
```

Or via the shell wrapper:

```bash
bash deepmatcher.sh path/to/data train.csv validation.csv test.csv \
  output/best_model.pth path/to/unlabeled.csv \
  output/predictions.csv config-example.yaml
```

`--config`/the 7th argument is optional — if omitted, the defaults from
`DEFAULT_CONFIG` in `run_deepmatcher.py` apply (these match deepmatcher's
own defaults).

## Configuration

All model, training, and post-processing parameters come from the config
file — no code changes needed. Overview of the sections:

- **`process`** — how CSVs are read/tokenized, which embeddings are used.
- **`process_unlabeled`** — settings for the unlabeled data.
- **`model`** — network architecture (`attr_summarizer`, `classifier`, etc.).
- **`train`** — training hyperparameters (`epochs`, `batch_size`, ...).
- **`eval`** — parameters for test-set evaluation.
- **`prediction`** — parameters for prediction on unlabeled data.
- **`threshold`** — custom post-processing: filters/flags predictions
  based on the `match_score` column, with either a fixed or an adaptive
  threshold (`fixed`, `relative_to_mean`, `relative_to_max`,
  `mean_minus_std`, `percentile`).

Details on each individual parameter, its valid values, and defaults:
see [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md).

## Embeddings

On the first call to `dm.data.process(...)`, deepmatcher automatically
downloads word embeddings (default: `glove.6B.50d`, ~822 MB). The download goes into the
`embeddings_cache_path` directory (default `~/.vector_cache`) and is
reused on subsequent runs.

## Makefile targets

| Target              | Effect                                                                                                                   |
|---------------------|--------------------------------------------------------------------------------------------------------------------------|
| `make download`     | Creates the venv, installs `deepmatcher`+`pyyaml`, clones the official repo (for its test datasets) into `deepmatcher/`. |
| `make test`         | Runs `run_deepmatcher.py` on the test datasets.                                                                          |
| `make clean`        | Removes `deepmatcher/`, `output/`, and `venv/`.                                                                          |
| `make docker_build` | Builds the `kgt/deepmatcher` Docker image.                                                                               |
| `make docker_test`  | Runs a test pass inside the Docker container (via `deepmatcher.sh`).                                                     |
| `make docker_help`  | Shows example invocations for the Docker image.                                                                          |

All paths (`INSTALL_DIR`, `VENV_DIR`, `OUTPUT_DIR`, `CONFIG`, `DATA_DIR`,
`BEST_MODEL`, `OUTPUT_CSV`, ...) can be overridden on invocation, e.g.
`make test CONFIG=other_config.yaml`.

## Docker

```bash
make docker_build
make docker_help
docker run --rm kgt/deepmatcher bash deepmatcher.sh \
  data_dir train.csv validation.csv test.csv \
  best_model.pth unlabeled.csv predictions.csv config.yaml
```