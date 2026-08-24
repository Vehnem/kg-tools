# Contributing to kg-tools

Thank you for contributing to the kg-tools catalog.

## Adding a new tool

1. Copy `tools/_template/` to `tools/<id>/` (use lowercase id with hyphens).
2. Create `tools/<id>/tool.yaml` following the [JSON schema](catalog/schema/tool.schema.json).
3. Add a `tools/<id>/README.md` with install/run examples.
4. For Docker tools, put build context in `tools/<id>/docker/` with:
   - `Dockerfile`
   - `Makefile` with targets: `docker_build`, `docker_test`, `docker_help`
5. Validate locally:

```bash
pip install -r _scripts/requirements.txt
python _scripts/manage.py validate
python _scripts/manage.py generate readme
python _scripts/manage.py generate pages
```

6. If CI should build your image, set `ci.docker_build: true` in `tool.yaml` and run:

```bash
python _scripts/manage.py generate ci
```

## `tool.yaml` guidelines

- **Do not** duplicate KGpipe `input_spec` / `output_spec` — those live in KGpipe `kgpipe_tasks`.
- Use `kgpipe.task_refs` only as documentation links to existing KGpipe task names.
- Set `execution.docker.image` to the image name **without** tag (e.g. `kgt/paris`).
- Pick `kind` and `categories` from [catalog/categories.yaml](catalog/categories.yaml).
- `description` is shown in [tools/README.md](tools/README.md) and the GitHub Pages catalog.

## Docker image naming

Use the `kgt/<tool-id>` convention so KGpipe wrappers can reference images consistently:

```bash
docker build -t kgt/<tool-id> .
```

## Test data

Prefer fixtures from [kg-testdata](https://github.com/Vehnem/kg-testdata). Document paths in `tool.yaml` `testdata` and in your README.

## KGpipe task tests

A pytest case is YAML at `tools/<id>/kgpipe/tests/<name>.yaml` with `task`,
`inputs`, `outputs`, and optional `config` (the three objects a `KgTask`
function receives). See
[catalog/schema/kgpipe_task_test.schema.json](catalog/schema/kgpipe_task_test.schema.json)
and the PyJedAI example
`tools/pyjedai/kgpipe/tests/jedai_syntactic_matching.yaml`.

These tests are **not** run in CI: they need Docker wrappers and can take a long
time. Run them locally, commit `catalog/reports/kgpipe-tasks.json`, then
regenerate Pages:

```bash
pip install pytest
python _scripts/manage.py kgpipe-test
python _scripts/manage.py generate pages
```

The Pages catalog has a second table that marks which tasks have a pytest case
and the last collected report outcome.

## Pull request checklist

- [ ] `tool.yaml` passes `python _scripts/manage.py validate`
- [ ] `README.md` updated for the tool (and `tools/README.md` / `docs/index.md` via `gen_readme.py` and `gen_pages.py`)
- [ ] Upstream URL and license noted
- [ ] `make -C tools/<id>/docker docker_build` succeeds (if docker tool)
- [ ] `kgpipe.task_refs` added when a KGpipe wrapper exists (documentation only)

## Catalog maintenance

Use `python _scripts/manage.py check` to run the fast validation checks locally.
Docker builds and tests are available as `manage.py build` and `manage.py test`.
See [_scripts/README.md](_scripts/README.md) for the complete command and script
reference.
