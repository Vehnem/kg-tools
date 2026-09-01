.PHONY: all install test clean docker_build docker_test docker_help

IMAGE_NAME   ?= kgt/ontoaligner
VENV_DIR     := $(CURDIR)/.venv
OUTPUT_DIR   := $(CURDIR)/results
CONFIG       ?= $(CURDIR)/example-config.yaml
TESTDATA_DIR ?= $(HOME)/kg-testdata/_snippets/ontoaligner
SOURCE       ?= $(TESTDATA_DIR)/source.owl
TARGET       ?= $(TESTDATA_DIR)/target.owl
METHOD       ?=

all: install test

install:
	python3 -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -r requirements.txt

test:
	@if [ ! -x "$(VENV_DIR)/bin/python" ]; then \
	   echo "No virtualenv found in $(VENV_DIR) -- run 'make install' first." >&2; \
	   exit 1; \
	fi
	mkdir -p $(OUTPUT_DIR)
	cd wrapper && \
	PATH="$(VENV_DIR)/bin:$$PATH" bash ontoaligner.sh \
		$(SOURCE) \
		$(TARGET) \
		$(OUTPUT_DIR) \
		$(CONFIG) \
		$(METHOD)

clean:
	rm -rf $(VENV_DIR) $(OUTPUT_DIR)

docker_build:
	docker build -t $(IMAGE_NAME) .

docker_test:
	docker run --rm \
		-v $(TESTDATA_DIR):/data:ro \
		-v $(OUTPUT_DIR):/results \
		$(IMAGE_NAME) \
		sh ontoaligner.sh \
		/data/source.owl \
		/data/target.owl \
		/results \
		/app/config-example.yaml

docker_help:
	@echo "Example usage of the OntoAligner Docker image"
	@echo "(the image has no ENTRYPOINT/CMD -- always call: sh ontoaligner.sh <source> <target> <output_dir> <config> [method])"
	@echo "=== Usage 1: align two ontologies with the bundled example config ==="
	@echo "docker run --rm -v \$$(pwd)/data:/data -v \$$(pwd)/results:/results $(IMAGE_NAME) sh ontoaligner.sh /data/source.owl /data/target.owl /results /app/config-example.yaml"
	@echo "=== Usage 2: use your own config file ==="
	@echo "docker run --rm -v \$$(pwd)/data:/data -v \$$(pwd)/results:/results $(IMAGE_NAME) sh ontoaligner.sh /data/source.owl /data/target.owl /results /data/my_config.yaml"
	@echo "=== Usage 3: evaluate against a reference alignment (set output.evaluate: true and output.reference in the config) ==="
	@echo "docker run --rm -v \$$(pwd)/data:/data -v \$$(pwd)/results:/results $(IMAGE_NAME) sh ontoaligner.sh /data/source.owl /data/target.owl /results /data/my_config.yaml"
	@echo "=== Usage 4: switch method on the fly (e.g. retrieval instead of lightweight) ==="
	@echo "docker run --rm -v \$$(pwd)/data:/data -v \$$(pwd)/results:/results $(IMAGE_NAME) sh ontoaligner.sh /data/source.owl /data/target.owl /results /app/config-example.yaml retrieval"