.PHONY: all clean docker_build docker_test docker_help create_outputdir


OUTPUT_DIR ?= $(CURDIR)/target
CONFIG     ?= config-smoke.yaml
BENCHMARK  ?= MED_BBK_9K

all: docker_test

create_outputdir:
	mkdir -p $(OUTPUT_DIR)

clean:
	rm -rf $(OUTPUT_DIR)

docker_build:
	docker build -t kgt/ontoea .

docker_test: create_outputdir
	docker run --rm -v $(OUTPUT_DIR):/ontoea-out -v /home/theo/PycharmProjects/kg-tools/tools/ontoea/kgpipe/tests/fixtures/benchmark:/tmp/bench kgt/ontoea bash -c \
	   "bash ontoea.sh /tmp/bench /ontoea-out $(CONFIG)"

docker_help:
	@echo "Example usage of OntoEA Docker"
	@echo "=== Usage 1: your own benchmark folder (see CONFIG_REFERENCE.md section 1) ==="
	@echo "docker run --rm -v <benchmark_dir>:/data/benchmark -v <output_dir>:/out kgt/ontoea bash ontoea.sh /data/benchmark /out config-example.yaml"
	@echo "=== Usage 2: your own config ==="
	@echo "docker run --rm -v <benchmark_dir>:/data/benchmark -v <output_dir>:/out -v <config.yaml>:/cfg/config.yaml kgt/ontoea bash ontoea.sh /data/benchmark /out /cfg/config.yaml"
	@echo "=== Usage 3: a benchmark shipped in the image (MED_BBK_9K, EN_FR_15K_V1, ...) ==="
	@echo "make docker_test BENCHMARK=EN_FR_15K_V1 CONFIG=config-example.yaml"
