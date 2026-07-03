# Example Tool (template)

Copy this directory to `tools/<your-tool-id>/` and customize.

## Docker

```bash
make -C docker docker_build
make -C docker docker_help
make -C docker docker_test
```

## Layout

```
tools/<id>/
  tool.yaml
  README.md
  docker/
    Dockerfile
    Makefile
    tool.sh
```

See [CONTRIBUTING.md](../../CONTRIBUTING.md).
