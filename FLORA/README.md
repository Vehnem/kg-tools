# Paris Quickstart

## Requires
Tested with Python 3.10

## Test
Test with Makefile
```bash
make
```
It will run multiple Alignments - can stop after first one

## Run
### With flora.sh locally
```bash
bash wrapper/flora.sh path/to/kb1 path/to/kb2 path/to/outputfolder
```

### With Docker
```bash
make docker_build

make docker_help #for test run
docker run --rm kgt/flora bash flora.sh path/to/kb1 path/to/kb2 path/to/outputfolder
```

### TODO
Accept training data \
Accept embeddings
