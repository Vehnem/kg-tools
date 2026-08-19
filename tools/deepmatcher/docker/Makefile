.PHONY: all venv download test clean docker_build docker_test docker_help


INSTALL_DIR ?= $(CURDIR)/bin
KG_TESTDATA ?= $(HOME)/kg-testdata
VENV_DIR ?= $(CURDIR)/.venv
OUTPUT_DIR ?= $(CURDIR)/target

CONFIG ?= $(CURDIR)/config-example.yaml

DM_DIR ?= $(KG_TESTDATA)/_snippets/deepmatcher
UNLABELED_CSV ?= $(DM_DIR)/test_unlabeled.csv

BEST_MODEL    ?= $(OUTPUT_DIR)/best_model.pth
OUTPUT_CSV    ?= $(OUTPUT_DIR)/predictions.csv

PYTHON        ?= $(VENV_DIR)/bin/python3
PIP           ?= $(VENV_DIR)/bin/pip

all: download test

venv:
	python3.8 -m venv $(VENV_DIR)
	$(PIP) install torch==1.9.0 torchtext==0.10.0 deepmatcher pyyaml

download:
	mkdir -p $(INSTALL_DIR)
	git clone https://github.com/anhaidgroup/deepmatcher.git $(INSTALL_DIR)

test: create_outputdir
	. $(VENV_DIR)/bin/activate && cd wrapper && \
	bash deepmatcher.sh \
		$(DM_DIR) \
		test_train.csv \
		test_valid.csv \
		test_test.csv \
		$(BEST_MODEL) \
		$(UNLABELED_CSV) \
		$(OUTPUT_CSV) \
		$(CONFIG)

create_outputdir:
	mkdir -p $(OUTPUT_DIR)

clean:
	rm -rf $(INSTALL_DIR) $(OUTPUT_DIR) $(VENV_DIR)

docker_build:
	docker build -t kgt/deepmatcher .

docker_test: create_outputdir
	cp -r $(DM_DIR) $(OUTPUT_DIR)/data; \
	docker run --rm -v $(OUTPUT_DIR):/dm-data kgt/deepmatcher \
		bash deepmatcher.sh \
		/dm-data/data test_train.csv test_valid.csv test_test.csv \
		/dm-data/best_model.pth /dm-data/test_unlabeled.csv \
		/dm-data/predictions.csv config-example.yaml

docker_help:
	@echo "Example usage of DeepMatcher Docker"
	@echo "=== Usage 1: shell wrapper ==="
	@echo "docker run --rm kgt/deepmatcher bash deepmatcher.sh <data_dir> <train.csv> <validation.csv> <test.csv> <best_model.pth> <unlabeled.csv> <predictions.csv> [config.yaml]"
	@echo "=== Usage 2: python script directly ==="
	@echo "docker run --rm kgt/deepmatcher python run_deepmatcher.py --data_directory <data_dir> --train_csv <train.csv> --validation_csv <validation.csv> --test_csv <test.csv> --best_model <best_model.pth> --unlabeled_csv <unlabeled.csv> --output <predictions.csv> --config <config.yaml>"