# Ditto Pipeline Wrapper

A config-driven wrapper around [Ditto](https://github.com/megagonlabs/ditto)
(entity matching with pretrained language models). `run_ditto.py` translates
a single `config-example.yaml` into the matching CLI call for `matcher.py`
(matching) or `train_ditto.py` (training) and runs it as a subprocess inside
the Ditto repo. Ditto itself is not reimplemented - the wrapper stays 100%
compatible with the upstream project.

Tested with Python 3.7.7.

## Repository layout

```
.
├── docker
│   ├── config-example.yaml
│   ├── CONFIG_REFERENCE.md
│   ├── Dockerfile
│   ├── install_ditto_deps.sh
│   ├── Makefile
│   └── wrapper
│       ├── ditto.sh
│       └── run_ditto.py
├── kgpipe
│   └── ditto_tasks.py
├── README.md
└── tool.yaml
```

## Installation

### Local (venv)

```bash
make venv       # creates .venv, installs pyyaml
make download   # clones megagonlabs/ditto into ./bin/ditto
                # and installs its requirements (torch,
                # transformers, spacy, nltk, ...) into the venv
```

You do **not** need to create a `configs.json` in the Ditto repo by hand:
`run_ditto.py` automatically writes the entry for `task.name` on every run -
generated from `task.task_type`, `task.vocab`, `task.trainset`,
`task.validset` and `task.testset` in the YAML config (see
`docker/config-example.yaml`). Existing entries for other task names are
left untouched; only the entry with the matching name is overwritten.

For `mode: match`, a trained checkpoint is expected under
`<paths.checkpoint_path>/<task.name>/model.pt`.

### Docker

```bash
make docker_build   # builds the kgt/ditto image (wrapper + pyyaml only)
```

Ditto itself (including its heavy dependencies) is intentionally **not**
baked into the image, but mounted as a volume at runtime -
`paths.ditto_repo` in the config must then point to the mounted path.
Dependencies are installed via `docker/install_ditto_deps.sh`.

## Standard usage

### Via the shell script

```bash
./docker/wrapper/ditto.sh <input.jsonl> <output.jsonl> <config.yaml>
```

- `input.jsonl` / `output.jsonl`: only needed for `mode: match`. For
  `mode: train`, both can be left empty (`""`), since `train_ditto.py`
  reads its datasets from `configs.json`.
- `config.yaml`: path to the wrapper config (see
  `docker/config-example.yaml` / `docker/CONFIG_REFERENCE.md`).

Example (matching):

```bash
./docker/wrapper/ditto.sh input/candidates.jsonl output/matched.jsonl docker/config-example.yaml
```

Example (training, `mode: train` set in the config):

```bash
./docker/wrapper/ditto.sh "" "" docker/config-example.yaml
```

### Directly via Python

```bash
python docker/wrapper/run_ditto.py --input input/candidates.jsonl \
                     --output output/matched.jsonl \
                     --config docker/config-example.yaml
```

### Via Make

```bash
make test          # uses test data from $KG_TESTDATA/_snippets/ditto
                    # and CONFIG=config-example.yaml
```

Relevant variables (can be overridden via `make test CONFIG=... INPUT_JSONL=...`):

| Variable       | Meaning                              | Default                                         |
|----------------|--------------------------------------|-------------------------------------------------|
| `CONFIG`       | Path to the YAML config              | `config-example.yaml`                           |
| `INPUT_JSONL`  | Input file with candidate pairs      | `$KG_TESTDATA/_snippets/ditto/candidates.jsonl` |
| `OUTPUT_JSONL` | Target file for the matching results | `target/matched.jsonl`                          |
| `INSTALL_DIR`  | Location for the cloned Ditto repo   | `./bin`                                         |
| `VENV_DIR`     | Location of the Python venv          | `./.venv`                                       |

### Via Docker

```bash
make docker_test    # copies test data into the target directory and
                     # runs ditto.sh inside the container
make docker_help    # shows both call variants (shell & Python)
```

## Files

| File                           | Purpose                                                                                     |
|--------------------------------|---------------------------------------------------------------------------------------------|
| `docker/wrapper/run_ditto.py`  | Python wrapper, translates config → CLI call                                                |
| `docker/wrapper/ditto.sh`      | Shell wrapper with a fixed positional argument list                                         |
| `docker/config-example.yaml`   | Example / default configuration (incl. task fields for automatic `configs.json` generation) |
| `docker/CONFIG_REFERENCE.md`   | Description of all config fields                                                            |
| `docker/Dockerfile`            | Minimal image with wrapper + pyyaml                                                         |
| `docker/install_ditto_deps.sh` | Installs Ditto's dependencies at build/run time                                             |
| `docker/Makefile`              | Setup, local tests, Docker build/test                                                       |
| `kgpipe/ditto_tasks.py`        | KGpipe task definition wrapping Ditto as an entity-matching task                            |
| `tool.yaml`                    | Tool metadata/registration for the pipeline                                                 |