# LogMap Pipeline

Config-driven wrapper around
[LogMap](https://github.com/ernestojimenezruiz/logmap-matcher), a Java
ontology matching system with built-in reasoning and alignment repair.
All LogMap parameters live in a flat `key=value` config, and
`run_logmap.sh` is invoked with the two ontologies, an output directory
and the config.

LogMap has no swappable matchers or blockers, so — unlike the Magellan
wrapper — there is no Python layer: the shell script translates the config
into LogMap's native `parameters.txt` and calls the CLI.

See **`CONFIG_REFERENCE.md`** for the full list of supported keys, their
types and defaults (verified directly against the LogMap source, not from
memory).

## Files

| File                          | Purpose                                                                                           |
|-------------------------------|---------------------------------------------------------------------------------------------------|
| `docker/wrapper/run_logmap.sh` | The runner: config validation → `parameters.txt` → `java -jar` (MATCHER or EVALUATION) → checks   |
| `docker/config-example.conf`  | Fully populated example config; reproduces LogMap's shipped `parameters.txt` values               |
| `docker/CONFIG_REFERENCE.md`  | Reference for every key, output file and failure mode                                             |
| `docker/Makefile`             | `build` / `test` / `docker_*` targets                                                             |
| `docker/Dockerfile`           | Multi-stage build: Maven (JDK 17) → JRE 17 runtime                                                |
| `tool.yaml`                   | Tool registration                                                                                 |
| `kgpipe/logmap_tasks.py`      | KGpipe task `logmap_ontology_matching`                                                            |
| `kgpipe/tests/logmap_ontology_matching.yaml` | Pytest harness fixture                                                          |

## Requirements

- bash ≥ 4 (associative arrays; the Docker image has it, stock macOS does not).
- Java 17 and Maven for a local build (`make build`); not needed for Docker.
- The LogMap sources are pinned to commit
  `a031fa9889e139fd5ab9e8c7415c8113f9c285ee` (`LOGMAP_COMMIT`), jar
  `logmap-matcher-4.0.jar`.

## Quickstart

All `make` commands run inside `docker/`.

```bash
cd docker
# 1. Build LogMap locally into .build/logmap (jar + java-dependencies + parameters.txt)
make build

# 2. Run against a demo pair under $KG_TESTDATA/_snippets/logmap
make test
```

The test target expects these files (names overridable via `ONTO1`,
`ONTO2`, `REFERENCE`):

```
cmt.owl
ekaw.owl
cmt-ekaw.rdf
```

Results land under `target/`: the mapping files, `logmap_stdout.log` and
— because a reference is given — `evaluation.csv`.

### Using your own data

```bash
make test \
  ONTO1=path/to/source.owl \
  ONTO2=path/to/target.owl \
  REFERENCE=path/to/reference.rdf \
  OUTPUT_DIR=out/my_run \
  CONFIG=my_config.conf
```

Or directly:

```bash
LOGMAP_HOME=.build/logmap bash wrapper/run_logmap.sh source.owl target.owl out/my_run my_config.conf
```

Omit the reference to run in MATCHER mode; with a reference (OAEI RDF
alignment format) the runner uses EVALUATION mode and writes
`evaluation.csv` (`precision,recall,f1`).

## Makefile targets

| Target                | Effect                                                                                                |
|-----------------------|-------------------------------------------------------------------------------------------------------|
| `make build`          | Downloads the pinned LogMap sources, runs `mvn package`, assembles `$(LOGMAP_HOME)`.                  |
| `make test`           | Runs `run_logmap.sh` on `$(ONTO1)`, `$(ONTO2)`, `$(REFERENCE)` with `$(CONFIG)`.                      |
| `make clean`          | Removes `target/` and `.build/`.                                                                      |
| `make docker_build`   | Builds the `kgt/logmap` Docker image.                                                                 |
| `make docker_test`    | Copies the demo data into `target/data` and runs a test pass inside the container.                    |
| `make docker_help`    | Shows example invocations for the Docker image.                                                       |

All paths (`KG_TESTDATA`, `LOGMAP_HOME`, `OUTPUT_DIR`, `CONFIG`, ...) can
be overridden on invocation, e.g. `make test CONFIG=other.conf`.

## Docker

```bash
make docker_build
make docker_help
docker run --rm -v $(pwd)/data:/data kgt/logmap \
  bash run_logmap.sh /data/source.owl /data/target.owl /data/out config-example.conf
```

## Verified LogMap quirks worth knowing about

All documented in full in `CONFIG_REFERENCE.md`:

- **Silent failures:** the CLI catches all exceptions and prints its usage
  text, and exits with `0`. The runner checks for the usage text and for
  missing output files and fails with exit code `1`.
- **Silent parameter typos:** LogMap parses booleans with
  `Boolean.valueOf` and swallows exceptions while reading
  `parameters.txt`. The runner validates every value by type before
  starting the JVM.
- **Ignored `reverse_labels` line:** the shipped `parameters.txt` uses `=`
  instead of `|` there, so LogMap never reads it. The runner writes the
  key in the correct format.
- **Output path concatenation:** output files are named
  `<output_path><name>`, so the output path needs a trailing slash. The
  runner adds it.
- **Decimal separator:** EVALUATION scores are printed with the JVM's
  default locale; the runner forces `en_US`.
