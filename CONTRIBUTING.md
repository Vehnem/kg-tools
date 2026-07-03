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
python _scripts/validate_catalog.py
python _scripts/gen_readme.py
```

6. If CI should build your image, set `ci.docker_build: true` in `tool.yaml` and run:

```bash
python _scripts/gen_ci.py
```

## `tool.yaml` guidelines

- **Do not** duplicate KGpipe `input_spec` / `output_spec` — those live in KGpipe `kgpipe_tasks`.
- Use `kgpipe.task_refs` only as documentation links to existing KGpipe task names.
- Set `execution.docker.image` to the image name **without** tag (e.g. `kgt/paris`).
- Pick `kind` and `categories` from [catalog/categories.yaml](catalog/categories.yaml).

## Docker image naming

Use the `kgt/<tool-id>` convention so KGpipe wrappers can reference images consistently:

```bash
docker build -t kgt/<tool-id> .
```

## Test data

Prefer fixtures from [kg-testdata](https://github.com/Vehnem/kg-testdata). Document paths in `tool.yaml` `testdata` and in your README.

## Pull request checklist

- [ ] `tool.yaml` passes `python _scripts/validate_catalog.py`
- [ ] `README.md` updated for the tool (and root README via `gen_readme.py`)
- [ ] Upstream URL and license noted
- [ ] `make -C tools/<id>/docker docker_build` succeeds (if docker tool)
- [ ] `kgpipe.task_refs` added when a KGpipe wrapper exists (documentation only)

## Catalog maintenance scripts

| Script | Purpose |
|--------|---------|
| `_scripts/validate_catalog.py` | Validate all manifests against JSON schema |
| `_scripts/gen_readme.py` | Regenerate root README catalog tables |
| `_scripts/gen_ci.py` | Regenerate GitHub Actions docker matrix |
