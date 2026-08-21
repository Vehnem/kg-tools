.PHONY: all install test clean create_outputdir docker_build docker_test docker_help

IMAGE_NAME  ?= kgt/splink
VENV_DIR    ?= $(CURDIR)/.venv
OUTPUT_DIR  ?= $(CURDIR)/target
CONFIG      ?= $(CURDIR)/config-example.yaml

KG_TESTDATA ?= $(HOME)/kg-testdata
MAGELLAN_DIR ?= $(KG_TESTDATA)/_snippets/magellan

all: install test

install:
	python3 -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -r requirements.txt

test: create_outputdir
	$(VENV_DIR)/bin/python wrapper/run_splink.py --input $(MAGELLAN_DIR)/acm_demo.csv --input2 $(MAGELLAN_DIR)/dblp_demo.csv --output $(OUTPUT_DIR)/predictions.csv --config $(CONFIG)

clean:
	rm -rf $(VENV_DIR) $(OUTPUT_DIR)

create_outputdir:
	mkdir -p $(OUTPUT_DIR)

docker_build:
	docker build -t $(IMAGE_NAME) .

docker_test: create_outputdir
	cp -r $(MAGELLAN_DIR) $(OUTPUT_DIR)/data; \
	docker run -v $(OUTPUT_DIR):/splink-data --rm $(IMAGE_NAME) bash splink.sh /splink-data/data/acm_demo.csv /splink-data/data/dblp_demo.csv /splink-data/predictions.csv config-example.yaml

docker_help:
	@echo "Example usage of Splink Docker image"
	@echo "=== Usage 1: dedupe a single file ==="
	@echo "docker run --rm -v \$$(pwd)/data:/data $(IMAGE_NAME) --input /data/input.csv --output /data/output.csv --config config-example.yaml"
	@echo "=== Usage 2: link two files ==="
	@echo "docker run --rm -v \$$(pwd)/data:/data $(IMAGE_NAME) --input /data/left.csv --input2 /data/right.csv --output /data/output.csv --config config-example.yaml"
	@echo "=== Usage 3: override the match-probability threshold ==="
	@echo "docker run --rm -v \$$(pwd)/data:/data $(IMAGE_NAME) --input /data/input.csv --output /data/output.csv --config config-example.yaml --threshold 0.8"