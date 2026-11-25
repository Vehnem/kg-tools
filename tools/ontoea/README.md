# OntoEA Pipeline

Config-driven wrapper around
[OntoEA](https://github.com/ZihengZZH/OntoEA), an ontology-guided entity
alignment approach for knowledge graphs (TensorFlow 1.14, Python 3.6). All
hyperparameters live in a YAML config, and `run_ontoea.py` is invoked with
`--input`, `--output` and `--config`.

Upstream is driven by `main_from_args.py <args.json> <benchmark> <cuda>`;
the runner generates the args file from the YAML, builds a private view of
the benchmark directory, runs the training, and turns the integer-id results
into URI pairs plus an `evaluation.csv`.

See **`docker/CONFIG_REFERENCE.md`** for the benchmark layout, every config
key, the output files and the upstream quirks (verified against the OntoEA
source, not from memory).

## Files

| File                                            | Purpose                                                                                                  |
|-------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| `docker/wrapper/run_ontoea.py`                  | The runner: config validation → benchmark view → args JSON → training → URI alignment + evaluation CSV   |
| `docker/wrapper/ontoea.sh`                      | Thin shell wrapper: `bash ontoea.sh <benchmark_dir> <output_dir> <config.yaml>`                          |
| `docker/config-example.yaml`                    | Fully populated example config; equals upstream's `ontoea_args_15K.json`                                  |
| `docker/config-smoke.yaml`                      | Same, with `max_epoch: 10` (one iteration) for a quick pipeline check                                     |
| `docker/CONFIG_REFERENCE.md`                    | Reference for every key, output file and failure mode                                                    |
| `docker/Makefile`                               | `docker_build` / `docker_test` / `docker_help` / `clean`                                                 |
| `docker/Dockerfile`                             | Python 3.6.12 image with OntoEA pinned to a commit                                                       |
| `tool.yaml`                                     | Tool registration                                                                                        |
| `kgpipe/ontoea_tasks.py`                        | KGpipe task `ontoea_entity_alignment`                                                                    |
| `kgpipe/tests/ontoea_entity_alignment.yaml`     | Pytest harness fixture                                                                                   |

## Requirements

- Docker. There is no local venv target: OntoEA needs `tensorflow==1.14.0`,
  which only supports Python ≤ 3.7.
- The image is CPU-only (no CUDA). Training time was not measured.
- OntoEA is pinned to commit `afa1c79281fdfca5b123fc8e6dfc8ceb41dd4ded`
  (`ONTOEA_COMMIT` build argument).

## Quickstart

All `make` commands run inside `docker/`.

```bash
cd docker

# 1. Build the image
make docker_build

# 2. Smoke test on the shipped MED_BBK_9K benchmark (max_epoch: 10)
make docker_test
```

`docker_test` unzips the benchmark from the repository inside the image,
runs `config-smoke.yaml` and writes the results to `target/`
(`alignment.tsv`, `evaluation.csv`, raw OntoEA files, `ontoea_stdout.log`).
Other shipped benchmarks and configs:

```bash
make docker_test BENCHMARK=EN_FR_15K_V1 CONFIG=config-example.yaml
```

### Using your own data

Provide an unzipped benchmark directory (layout in `CONFIG_REFERENCE.md`
section 1):

```bash
docker run --rm \
  -v /path/to/MED_BBK_9K:/data/benchmark \
  -v $(pwd)/out:/out \
  kgt/ontoea bash ontoea.sh /data/benchmark /out config-example.yaml
```

With your own config file, mount it additionally and pass its container path.
The input directory may be mounted read-only.

## Makefile targets

| Target              | Effect                                                                                  |
|---------------------|-----------------------------------------------------------------------------------------|
| `make docker_build` | Builds the `kgt/ontoea` Docker image.                                                   |
| `make docker_test`  | Runs `$(CONFIG)` on `$(BENCHMARK)` from the image's repository, output in `$(OUTPUT_DIR)`.|
| `make docker_help`  | Shows example invocations for the Docker image.                                         |
| `make clean`        | Removes `target/`.                                                                      |

## Fixes compared to the initial Dockerfile / `ontoea.sh`

- `RUN export PYTHONPATH=...` only lives for that one build layer; it is now
  `ENV PYTHONPATH=...`.
- `ontoea.sh` called `python main_from_args.py "$IN1""$IN2" "$IN3"`, which
  concatenates the first two arguments. Also, the third argument of
  `main_from_args.py` is `CUDA_VISIBLE_DEVICES`, not a splits folder; the split
  is `dataset_division` in the config.
- The repository is checked out at a pinned commit instead of `HEAD`.
- `pyyaml` is installed for the runner.
- `docker_help` used `$args_file`, which `make` expands as a make variable
  (empty); the examples now use literal placeholders.

## Verified OntoEA quirks worth knowing about

All documented in full in `docker/CONFIG_REFERENCE.md`:

- **Silent typos:** upstream's args class accepts any key. The runner validates
  keys and types before TensorFlow starts.
- **Hard-coded asserts:** `init`, `alignment_module`, `optimizer`, `eval_metric`,
  `ent_l2_norm`, `alpha > 1` and `1 in top_k` are asserted by the code; the
  runner enforces them up front.
- **Path-dependent loader:** a benchmark path containing `raw`, `dbp15k` or
  `dwy100k` switches loaders. The runner uses a safe temp path.
- **Writes into the benchmark:** `onto_check_mat.h5` is written on every start,
  into the benchmark folder. The runner redirects it to a temp directory.
- **Id-only results:** `alignment_results_12` contains integer ids; `alignment.tsv`
  maps them back to URIs.
