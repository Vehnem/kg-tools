.PHONY: all venv download test clean docker_build docker_test docker_help

INSTALL_DIR   ?= deepmatcher
VENV_DIR      ?= .venv
OUTPUT_DIR    ?= output
CONFIG        ?= deepmatcher_config.example.yaml
DATA_DIR      ?= $(INSTALL_DIR)/test/test_datasets
UNLABELED_CSV ?= $(DATA_DIR)/test_unlabeled.csv
BEST_MODEL    ?= $(OUTPUT_DIR)/best_model.pth
OUTPUT_CSV    ?= $(OUTPUT_DIR)/predictions.csv
PYTHON        ?= $(VENV_DIR)/bin/python3
PIP           ?= $(VENV_DIR)/bin/pip

all: download test

venv:
	python3 -m venv $(VENV_DIR)
	$(PIP) install --upgrade pip
	$(PIP) install deepmatcher pyyaml

download: venv
	mkdir -p $(INSTALL_DIR)
	git clone https://github.com/anhaidgroup/deepmatcher.git $(INSTALL_DIR)

test: $(OUTPUT_DIR)
	$(PYTHON) run_deepmatcher.py \
		--data_directory $(DATA_DIR) \
		--train_csv test_train.csv \
		--validation_csv test_valid.csv \
		--test_csv test_test.csv \
		--best_model $(BEST_MODEL) \
		--unlabeled_csv $(UNLABELED_CSV) \
		--output $(OUTPUT_CSV) \
		--config $(CONFIG)

$(OUTPUT_DIR):
	mkdir -p $(OUTPUT_DIR)

clean:
	rm -rf $(INSTALL_DIR) $(OUTPUT_DIR) $(VENV_DIR)

docker_build:
	docker build -t kgt/deepmatcher .

docker_test:
	docker run --rm kgt/deepmatcher \
		bash deepmatcher.sh \
		deepmatcher/test/test_datasets test_train.csv test_valid.csv test_test.csv \
		best_model.pth deepmatcher/test/test_datasets/test_unlabeled.csv \
		predictions.csv config-example.yaml

docker_help:
	@echo "Example usage of DeepMatcher Docker"
	@echo "=== Usage 1: shell wrapper ==="
	@echo "docker run --rm kgt/deepmatcher bash deepmatcher.sh <data_dir> <train.csv> <validation.csv> <test.csv> <best_model.pth> <unlabeled.csv> <predictions.csv> [config.yaml]"
	@echo "=== Usage 2: python script directly ==="
	@echo "docker run --rm kgt/deepmatcher python run_deepmatcher.py --data_directory <data_dir> --train_csv <train.csv> --validation_csv <validation.csv> --test_csv <test.csv> --best_model <best_model.pth> --unlabeled_csv <unlabeled.csv> --output <predictions.csv> --config <config.yaml>"