.PHONY: all venv download test clean docker_build docker_test docker_help create_outputdir create_checkpointdir

INSTALL_DIR ?= $(CURDIR)/bin
KG_TESTDATA ?= $(HOME)/kg-testdata
VENV_DIR ?= $(CURDIR)/.venv
OUTPUT_DIR ?= $(CURDIR)/target

CONFIG ?= $(CURDIR)/config-example.yaml

DITTO_REPO ?= $(INSTALL_DIR)/ditto
DITTO_REF ?= master

OUTPUT_JSONL ?= $(OUTPUT_DIR)/matched.jsonl

CHECKPOINT_DIR ?= $(CURDIR)/checkpoints-docker

# cpu (default) index, or a cuXXX index (e.g. cu121) - see
# install_ditto_deps.sh. A cuXXX index additionally requires a matching
# CUDA toolkit / nvcc already present on this machine.
TORCH_INDEX_URL ?= https://download.pytorch.org/whl/cpu
APEX_EXTENSIONS ?= --cpp_ext

PYTHON        ?= $(VENV_DIR)/bin/python3
PIP           ?= $(VENV_DIR)/bin/pip

all: download test

venv:
	/home/theo/.pyenv/versions/3.7.7/bin/python -m venv $(VENV_DIR)
	$(PIP) install pyyaml

download: venv
	mkdir -p $(INSTALL_DIR)
	git clone --depth 1 https://github.com/megagonlabs/ditto.git $(DITTO_REPO)
	. $(VENV_DIR)/bin/activate && \
	TORCH_INDEX_URL=$(TORCH_INDEX_URL) APEX_EXTENSIONS="$(APEX_EXTENSIONS)" \
	bash $(CURDIR)/install_ditto_deps.sh $(DITTO_REPO)

test: create_outputdir
	. $(VENV_DIR)/bin/activate && cd wrapper && \
	cp "$(CONFIG)" "$(CONFIG).orig" && \
	trap '[ -f "$(CONFIG).orig" ] && mv "$(CONFIG).orig" "$(CONFIG)"' EXIT && \
	sed -i 's/^mode: match/mode: train/' "$(CONFIG)" && \
	python run_ditto.py --config "$(CONFIG)" && \
	sed -i 's/^mode: train/mode: match/' "$(CONFIG)" && \
	bash ditto.sh \
	$(DITTO_REPO)/input/input_small.jsonl \
	$(OUTPUT_JSONL) \
	$(CONFIG) && \
	mv "$(CONFIG).orig" "$(CONFIG)"

create_outputdir:
	mkdir -p $(OUTPUT_DIR)

create_checkpointdir:
	mkdir -p $(CHECKPOINT_DIR)

clean:
	rm -rf $(INSTALL_DIR) $(OUTPUT_DIR) $(VENV_DIR)

docker_build:
	docker build \
	--build-arg DITTO_REF=$(DITTO_REF) \
	--build-arg TORCH_INDEX_URL=$(TORCH_INDEX_URL) \
	--build-arg APEX_EXTENSIONS="$(APEX_EXTENSIONS)" \
	-t kgt/ditto .

docker_test: create_outputdir create_checkpointdir
	docker run --rm --gpus all \
	  -v $(abspath $(OUTPUT_DIR)):/wrapper/output \
	  -v $(abspath $(CHECKPOINT_DIR)):/wrapper/checkpoints \
	  -v $(abspath $(CONFIG)):/wrapper/config-example.yaml:ro \
	  kgt/ditto \
	  -c 'set -e; \
		  cp /wrapper/config-example.yaml config-example-copy.yaml; \
		  sed -i "s/^mode: match/mode: train/" config-example-copy.yaml; \
		  sed -i "s#ditto_repo: \".*\"#ditto_repo: \"ditto\"#" config-example-copy.yaml; \
		  python run_ditto.py --config config-example-copy.yaml; \
		  sed -i "s/^mode: train/mode: match/" config-example-copy.yaml; \
		  bash ditto.sh ditto/input/input_small.jsonl output/matched.jsonl config-example-copy.yaml'

docker_help:
	@echo "Example usage of Ditto Docker"
	@echo "Ditto is already included in the image - only the datasets need to be mounted."
	@echo "=== Usage 1: shell wrapper ==="
	@echo "docker run --rm --gpus all -v <input-dir>:/ditto-data/input:ro -v <output-dir>:/ditto-data/output kgt/ditto \\"
	@echo "   bash ditto.sh /ditto-data/input/<input.jsonl> /ditto-data/output/<output.jsonl> <config.yaml>"
	@echo "=== Usage 2: python script directly ==="
	@echo "docker run --rm --gpus all -v <input-dir>:/ditto-data/input:ro -v <output-dir>:/ditto-data/output kgt/ditto \\"
	@echo "   python run_ditto.py --input /ditto-data/input/<input.jsonl> --output /ditto-data/output/<output.jsonl> --config <config.yaml> [--dry-run]"
	@echo "=== GPU build (requires a CUDA-enabled base image with nvcc) ==="
	@echo "make docker_build TORCH_INDEX_URL=https://download.pytorch.org/whl/cu121 APEX_EXTENSIONS=\"--cpp_ext --cuda_ext\""