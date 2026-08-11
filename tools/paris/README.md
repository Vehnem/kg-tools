# PARIS Pipeline

Configurable ontology/knowledge-base alignment using
[PARIS](https://github.com/dig-team/PARIS) (Probabilistic Alignment of
Relations, Instances, and Schema), driven by an ini-style `settings.ini` file.

## Files

| File                    | Purpose                                                                                                                    |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------|
| `wrapper/paris.sh`      | Shell wrapper around `java -jar paris.jar`; merges a `settings.ini` with the input/output paths given on the command line. |
| `example-settings.ini`  | Example settings file with every field PARIS supports (verified against the PARIS source code).                            |
| `SETTINGS_REFERENCE.md` | Full reference of every `settings.ini` field, valid values, and defaults.                                                  |
| `Makefile`              | Setup (jar download) and test run via `make`.                                                                              |

## Requirements

- A Java runtime environment (> 1.6).
- A machine with a lot of RAM (PARIS loads both knowledge bases fully
  into memory; large KBs can require tens of GB).
- `wget` (only for `make download`).
- Input knowledge bases in N-Triples format (`.nt`), not N3 or Turtle.

## Quickstart

```bash
make download
make test
```

Results (TSV alignment files plus a run log) land under `target/` by
default.

### Using your own data

```bash
make test SETTINGS=my_settings.ini
```

Or directly without `make`:

```bash
bash paris_wrapper.sh settings.ini.example path/to/kb1.nt path/to/kb2.nt output/
```

`paris.sh` copies the given `settings.ini`, then appends
`factstore1`, `factstore2`, `resultTSV`, and `home` derived from the three
positional path arguments — any values for those four keys already
present in the settings file are overridden.

By default the wrapper picks the first `*.jar` file in the current
directory. Set `PARIS_JAR=/path/to/paris.jar` to override this.

## Configuration

Every PARIS parameter lives in `settings.ini` — no code changes needed.
See `SETTINGS_REFERENCE.md` for the full field list, including two important
gotchas verified directly from the PARIS source:


## Output

PARIS writes its results into the output folder after each iteration,
one set of files per iteration `n`:

| File                    | Contents                                                       |
|-------------------------|----------------------------------------------------------------|
| `n_eqv.tsv`             | Equalities found after iteration `n`.                          |
| `n_superrelations1.tsv` | Relations of KB1 that are super-relations of relations in KB2. |
| `n_superrelations2.tsv` | Relations of KB2 that are super-relations of relations in KB1. |
| `n_superclasses1.tsv`   | Superclasses of KB1 (last iteration only).                     |
| `n_superclasses2.tsv`   | Superclasses of KB2 (last iteration only).                     |

Each file contains the first item (instance, class, or relation), the
aligned second item, and a probabilistic confidence score.

## Makefile targets

| Target              | Effect                                                                  |
|---------------------|-------------------------------------------------------------------------|
| `make download`     | Downloads `paris_0_3.jar` into `bin/`.                                  |
| `make test`         | Runs `paris.sh` on the bundled `person11.nt`/`person12.nt` sample data. |
| `make clean`        | Removes `bin/` and `target/`.                                           |
| `make docker_build` | Builds the `kgt/paris` Docker image.                                    |
| `make docker_test`  | Runs a smoke test inside the Docker container.                          |
| `make docker_help`  | Shows example invocations for the Docker image.                         |

All paths (`INSTALL_DIR`, `OUTPUT_DIR`, `KG_TESTDATA`, `SETTINGS`, ...) can
be overridden on invocation, e.g. `make test SETTINGS=other.ini`.

## Docker

```bash
make docker_build
make docker_help
docker run --rm kgt/paris bash paris.sh settings.ini input1.nt input2.nt output/
```