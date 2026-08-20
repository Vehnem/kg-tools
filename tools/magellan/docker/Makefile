.PHONY: all venv test clean docker_build docker_test docker_help create_outputdir


KG_TESTDATA  ?= $(HOME)/kg-testdata
VENV_DIR     ?= $(CURDIR)/.venv
OUTPUT_DIR   ?= $(CURDIR)/target

CONFIG       ?= $(CURDIR)/config-example.yaml

MAGELLAN_DIR ?= $(KG_TESTDATA)/_snippets/magellan

PYTHON       ?= $(VENV_DIR)/bin/python3
PIP          ?= $(VENV_DIR)/bin/pip

all: test

venv:
	python3.11 -m venv $(VENV_DIR)
	$(PIP) install --no-cache-dir "setuptools<69" \
    && $(PIP) install --no-cache-dir -r requirements.txt

test: create_outputdir
	. $(VENV_DIR)/bin/activate && cd wrapper && \
	bash magellan.sh $(MAGELLAN_DIR) $(OUTPUT_DIR) $(CONFIG)

create_outputdir:
	mkdir -p $(OUTPUT_DIR)

clean:
	rm -rf $(OUTPUT_DIR) $(VENV_DIR)

docker_build:
	docker build -t kgt/magellan .

docker_test: create_outputdir
	cp -r $(MAGELLAN_DIR) $(OUTPUT_DIR)/data
	docker run --rm -v $(OUTPUT_DIR):/magellan-data kgt/magellan \
	   bash magellan.sh /magellan-data/data /magellan-data config-example.yaml

docker_help:
	@echo "Example usage of Magellan Docker"
	@echo "=== Usage 1: shell wrapper ==="
	@echo "docker run --rm kgt/magellan bash magellan.sh <input_dir> <output_dir> <config.yaml>"
	@echo "=== Usage 2: python script directly ==="
	@echo "docker run --rm kgt/magellan python3 label_candidates.py --input <input_dir> --output <output_dir> \
	--config <config.yaml> [--sample-size N] [--seed 42]"

