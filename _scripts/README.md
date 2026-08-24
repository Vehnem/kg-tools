# Maintenance scripts

This directory contains repository-maintenance commands, data conversion helpers,
and older Docker utilities. From the repository root, run contributor commands
through the lightweight management CLI:

```bash
pip install -r _scripts/requirements.txt
python _scripts/manage.py --help
```

The CLI is intentionally local to the repository: it does not need to be
installed and adds no dependencies beyond those already used by the scripts.

## Common commands

```bash
# Validate every tools/*/tool.yaml against the schema and repository layout
python _scripts/manage.py validate

# Run the fast checks used by validation CI
python _scripts/manage.py check

# Build or test all tools enabled by their tool.yaml CI flags
python _scripts/manage.py build
python _scripts/manage.py test

# Limit a Docker operation to one or more tool ids
python _scripts/manage.py build paris valentine
python _scripts/manage.py test paris

# Refresh generated files
python _scripts/manage.py generate readme
python _scripts/manage.py generate pages
python _scripts/manage.py generate ci
python _scripts/manage.py generate all

# Run KGpipe task pytest cases locally (not CI) and write catalog/reports/kgpipe-tasks.json
python _scripts/manage.py kgpipe-test
```

`build` and `test` invoke the corresponding Make target below each selected
tool's `docker/` directory. They require Docker and Make and can take
considerably longer than `check`. Passing explicit tool ids runs those tools
regardless of their CI flags.

## Script reference

| Path | Purpose |
| --- | --- |
| `manage.py` | Stable contributor-facing command dispatcher |
| `validate_catalog.py` | Validate manifests against `catalog/schema/tool.schema.json` and check their directory layout |
| `catalog_util.py` | Shared manifest loading and wrapper/KGpipe helpers used by the generators |
| `kgpipe_catalog.py` | Discover KGpipe tasks, pytest cases, and collected reports |
| `kgpipe_harness.py` | Execute one task case with input/output maps and optional config |
| `gen_readme.py` | Generate the catalog listings in `tools/README.md`; `--check` only compares them |
| `gen_pages.py` | Generate the searchable GitHub Pages table in `docs/index.md`; `--check` only compares it |
| `gen_ci.py` | Generate `.github/workflows/docker-matrix.yml` from manifest CI flags |
| `build` | Build selected Docker tools, or every tool with `ci.docker_build: true` |
| `test` | Test selected Docker tools, or every tool with `ci.docker_test: true` |
| `migrate_repo.py` | One-time repository migration retained for history; not part of normal maintenance |
| `_data-util/` | Standalone RDF/CSV conversion utilities with their own README |
| `_tool-wrapper/` | Experimental HTTP tool wrapper with its own README |
| `_viz/` | Standalone catalog visualization pages with their own README |

`gen_ci.sh` is a deprecated compatibility wrapper for `gen_ci.py`.
`create_docker_images.sh` and `run_docker_containers.sh` predate the current
`tools/<id>/docker/` layout and are kept only as legacy utilities; do not use
them for catalog CI or routine testing.

## GitHub Pages

The searchable catalog is a [Just the Docs](https://just-the-docs.github.io/just-the-docs/)
Jekyll site in `docs/`, deployed by `.github/workflows/pages.yml`. Enable it once
in the repository: Settings → Pages → Source → GitHub Actions.

Local preview needs [Bundler](https://bundler.io/) (`bundle` is not part of a
default Ruby install):

```bash
gem install bundler --user-install
export PATH="$(ruby -e 'puts Gem.user_dir')/bin:$PATH"
```

Then generate the catalog page and serve it:

```bash
python _scripts/manage.py generate pages
cd docs
bundle config set --local path vendor/bundle
bundle install
bundle exec jekyll serve
```

## KGpipe task tests

Task pytest cases are YAML under `tools/<id>/kgpipe/tests/`. They are not part of
`manage.py check` or GitHub Actions. Install KGpipe and pytest, then:

```bash
pip install -r _scripts/requirements-kgpipe-test.txt
python _scripts/manage.py kgpipe-test
python _scripts/manage.py generate pages
```

That writes `catalog/reports/kgpipe-tasks.json` for the Pages task table.

## Adding a maintenance command

Keep domain logic in a focused script that can still run directly. Add a thin
subcommand to `manage.py` only when contributors need the operation regularly.
Commands should resolve paths relative to the repository, return a non-zero
status on failure, and avoid changing generated files when running checks.
