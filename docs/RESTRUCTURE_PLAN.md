# kg-tools restructure — work checklist

Living document for the catalog restructure (kg-tools only; KGpipe unchanged).

## Phase 1 — Foundation

- [x] `catalog/schema/tool.schema.json`
- [x] `catalog/categories.yaml`
- [x] `CONTRIBUTING.md`, `LICENSE`
- [x] `tools/_template/` from `_example`
- [x] `_scripts/validate_catalog.py`
- [x] `.github/workflows/validate.yml`

## Phase 2 — Pilot migration

- [x] `tools/paris/` with `docker/` and `tool.yaml`
- [x] `tools/corenlp/` with `docker/` and `tool.yaml`
- [x] `tools/valentine/` with `docker/` and `tool.yaml`

## Phase 3 — Bulk migration and CI

- [x] Migrate remaining tools to `tools/<id>/`
- [x] `_scripts/gen_ci.py` + `.github/workflows/docker-matrix.yml`
- [x] `_scripts/gen_readme.py` for README catalog tables
- [x] Update `_scripts/build` and `_scripts/test` for new layout
- [ ] Optional: publish images to GHCR

## Phase 4 — Optional polish

- [ ] `catalog/index.yaml` curated lists (featured, moviekg-set)
- [ ] Fork-friendly docs in README
- [ ] Remove legacy `_example/` after contributors adopt `_template`

## Notes

- `kgpipe.task_refs` in `tool.yaml` are documentation links only.
- Docker image names stay `kgt/<id>:latest` for KGpipe compatibility.
- Regenerate CI workflow after changing `ci.docker_build` flags:

```bash
python _scripts/gen_ci.py
python _scripts/gen_readme.py
```
