# kg-tools — Knowledge Graph Integration Tool Catalog

> A curated collection of tools for knowledge graph data integration: Dockerized CLIs, utilities, and visualization assets.

## Quick start

```bash
git clone https://github.com/vehnem/kg-tools.git
cd kg-tools
```

Each dockerized tool lives under `tools/<id>/docker/` with `make docker_build`, `make docker_test`, and `make docker_help`.

Browse the catalog in [tools/README.md](tools/README.md), or the searchable table on [GitHub Pages](https://vehnem.github.io/kg-tools/).

Validate the catalog:

```bash
pip install -r _scripts/requirements.txt
python _scripts/manage.py check
```

## Repository layout

```
kg-tools/
  catalog/           # JSON schema, taxonomy, and collected KGpipe test reports
  tools/README.md    # Generated catalog index
  tools/<id>/        # One directory per tool
    tool.yaml        # Machine-readable catalog entry
    README.md        # Usage documentation
    docker/          # Docker build context (when applicable)
    kgpipe/          # Optional local KgTask definitions and pytest cases
  docs/              # GitHub Pages site (Just the Docs)
  _scripts/          # Maintenance CLI and supporting scripts (see _scripts/README.md)
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

Repository maintenance commands are documented in [_scripts/README.md](_scripts/README.md).

## License

MIT — see [LICENSE](LICENSE).
