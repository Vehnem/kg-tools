# OntoAligner Wrapper

Registry-based CLI wrapper around [OntoAligner](https://github.com/sciknoworg/OntoAligner), covering all four
method families exposed via `OntoAlignerPipeline`: `lightweight`, `retrieval`, `llm`, `rag`.

## Usage

```bash
bash ontoaligner.sh <source.owl> <target.owl> <output_dir> <config.yaml> [method]
```

- `source.owl` / `target.owl` — the two ontologies to align
- `output_dir` — where alignment results are written
- `config.yaml` — method configuration (see `testdata/example-config.yaml` for a minimal example)
- `method` — optional, overrides the method set in the config (`lightweight`, `retrieval`, `llm`, `rag`)

### Docker

```bash
docker run --rm \
  -v $(pwd)/data:/data:ro \
  -v $(pwd)/results:/results \
  kgt/ontoaligner \
  sh ontoaligner.sh /data/source.owl /data/target.owl /results /app/example-config.yaml
```

### Makefile

```bash
make install test          # local venv run
make docker_build docker_test   # containerized run
make docker_help           # more usage examples
```

Test data (`testdata/source.owl`, `testdata/target.owl`) is included for a quick smoke test.

## Notes

- Five additional aligner types (Graph Embedding, PropMatch, FLORA, OLaLa, EnsembleLeaning, Reranking) are not
  reachable through `OntoAlignerPipeline` and are documented separately.
- `example-config.yaml` is a minimal placeholder — verify field names against the config schema actually read
  by `run_ontoaligner.py` before relying on it.