INSTALL_DIR := $(CURDIR)/bin
KG_TESTDATA ?= $(HOME)/kg-testdata
VAL_DIR := $(KG_TESTDATA)/_snippets/valentine/
VENV_DIR := $(CURDIR)/.venv

.PHONY: all install test clean

all: install test

install:
	python3 -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install valentine

test:
	mkdir -p $(INSTALL_DIR); \
	cp $(VAL_DIR)/authors1.csv $(INSTALL_DIR)/; \
	cp $(VAL_DIR)/authors2.csv $(INSTALL_DIR)/
	$(VENV_DIR)/bin/python valentine_example.py $(INSTALL_DIR)/authors1.csv $(INSTALL_DIR)/authors2.csv

clean:
	rm -rf $(INSTALL_DIR) $(VENV_DIR)

docker_build:
	docker build -t kgt/valentine .

docker_help:
	echo "Example usage of Valentine Docker"
	echo "=== Usage 1 ==="
	echo "docker run --rm kgt/valentine bash valentine.sh $input_path1 $input_path2 $output_file"
	echo "=== Usage 2 ==="
	echo "docker run --rm kgt/valentine python valentine_example.py $input_path1 $input_path2 $output_file"

