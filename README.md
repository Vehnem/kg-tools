# kg-tools — Knowledge Graph Integration Tool Catalog

> A curated collection of tools for knowledge graph data integration: Dockerized CLIs, utilities, and visualization assets.

## Quick start

```bash
git clone https://github.com/vehnem/kg-tools.git
cd kg-tools
```

Each dockerized tool lives under `tools/<id>/docker/` with `make docker_build`, `make docker_test`, and `make docker_help`.

Validate the catalog:

```bash
pip install -r _scripts/requirements.txt
python _scripts/validate_catalog.py
```

## Tool catalog

<!-- CATALOG-START -->
### DatasetUtility

| Tool | Kind | Status | Docker image | KGpipe task refs |
|------|------|--------|--------------|------------------|
| [Dedup](tools/dedup/README.md) | dataset_utility | experimental | — | — |

### EntityLinking

| Tool | Kind | Status | Docker image | KGpipe task refs |
|------|------|--------|--------------|------------------|
| [DBpedia Spotlight](tools/dbpedia-spotlight/README.md) | docker_cli | maintained | `kgt/dbpedia-spotlight:latest` | `dbpedia_spotlight_ner_nel`, `dbpedia_spotlight_exchange` |
| [FALCON](tools/falcon/README.md) | docker_api | experimental | `kgt/falcon:latest` | `falcon_ner_nel_rl`, `falcon_exchange` |
| [REL](tools/rel/README.md) | docker_cli | experimental | `kgt/rel:latest` | — |

### EntityResolution

| Tool | Kind | Status | Docker image | KGpipe task refs |
|------|------|--------|--------------|------------------|
| [Dedup](tools/dedup/README.md) | dataset_utility | experimental | — | — |
| [DeepMatcher](tools/deepmatcher/README.md) | python_package | experimental | — | — |
| [FLORA](tools/flora/README.md) | docker_cli | experimental | `kgt/flora:latest` | — |
| [JedAI](tools/jedai/README.md) | python_package | deprecated | — | — |
| [Magellan](tools/magellan/README.md) | python_package | experimental | — | — |
| [PARIS](tools/paris/README.md) | docker_cli | maintained | `kgt/paris:latest` | `paris_entity_matching`, `paris_exchange` |
| [PyJedAI](tools/pyjedai/README.md) | docker_cli | maintained | `kgt/pyjedai:latest` | `pyjedai_entity_matching`, `pyjedai_entity_matching_v2` |

### InformationExtraction

| Tool | Kind | Status | Docker image | KGpipe task refs |
|------|------|--------|--------------|------------------|
| [Stanford CoreNLP](tools/corenlp/README.md) | docker_cli | maintained | `kgt/corenlp:latest` | `corenlp_openie_extraction`, `corenlp_exchange`, `corenlp_kbp_extraction` |
| [REBEL](tools/rebel/README.md) | docker_cli | experimental | `kgt/rebel:latest` | `rebel_extraction` |
| [Stanford OpenIE](tools/stanford-openie/README.md) | docker_cli | deprecated | `kgt/stanford-openie:latest` | — |

### ReasoningValidation

| Tool | Kind | Status | Docker image | KGpipe task refs |
|------|------|--------|--------------|------------------|
| [Pellet](tools/pellet/README.md) | docker_cli | maintained | `kgt/pellet:latest` | — |
| [RDFUnit](tools/rdfunit/README.md) | docker_cli | experimental | `kgt/rdfunit:latest` | — |

### SchemaAlignment

| Tool | Kind | Status | Docker image | KGpipe task refs |
|------|------|--------|--------------|------------------|
| [AgreementMakerLight](tools/agreementmaker/README.md) | docker_cli | maintained | `kgt/agreementmaker:latest` | `agreementmaker_ontology_matching` |
| [LIMES](tools/limes/README.md) | visualization, docker_cli | experimental | `kgt/limes:latest` | — |
| [PARIS](tools/paris/README.md) | docker_cli | maintained | `kgt/paris:latest` | `paris_entity_matching`, `paris_exchange` |
| [Valentine](tools/valentine/README.md) | docker_cli | maintained | `kgt/valentine:latest` | `valentine_csv_matching`, `valentine_csv_matching_v2` |

### StructureTransformation

| Tool | Kind | Status | Docker image | KGpipe task refs |
|------|------|--------|--------------|------------------|
| [Karma](tools/karma/README.md) | python_package | experimental | — | — |
| [RMLMapper](tools/rmlmapper/README.md) | docker_cli | experimental | `kgt/rmlmapper:latest` | — |

### Visualization

| Tool | Kind | Status | Docker image | KGpipe task refs |
|------|------|--------|--------------|------------------|
| [LIMES](tools/limes/README.md) | visualization, docker_cli | experimental | `kgt/limes:latest` | — |
<!-- CATALOG-END -->

## Repository layout

```
kg-tools/
  catalog/           # JSON schema and category taxonomy
  tools/<id>/        # One directory per tool
    tool.yaml        # Machine-readable catalog entry
    README.md        # Usage documentation
    docker/          # Docker build context (when applicable)
  _scripts/          # validate_catalog.py, gen_readme.py, gen_ci.py
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
