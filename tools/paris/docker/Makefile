.PHONY: all download test clean docker_build docker_test docker_help

INSTALL_DIR  := $(CURDIR)/bin
OUTPUT_DIR   := $(CURDIR)/target
KG_TESTDATA  ?= $(HOME)/kg-testdata
PARIS_DIR    := $(KG_TESTDATA)/_snippets/paris
SETTINGS     ?= $(CURDIR)/settings-example.ini
JAR_URL      ?= https://github.com/dig-team/PARIS/releases/download/v0.3/paris_0_3.jar

all: download test

download:
	mkdir -p $(INSTALL_DIR)
	wget -q -N $(JAR_URL) -P $(INSTALL_DIR)

test:
	@JAR=$$(ls $(INSTALL_DIR)/*.jar 2>/dev/null | head -n1); \
	if [ -z "$$JAR" ]; then \
		echo "No PARIS jar found in $(INSTALL_DIR) -- run 'make download' first." >&2; \
		exit 1; \
	fi
	mkdir -p $(OUTPUT_DIR)
	cp "$(PARIS_DIR)/person11.nt" $(INSTALL_DIR)/
	cp "$(PARIS_DIR)/person12.nt" $(INSTALL_DIR)/
	cp "$(SETTINGS)" $(INSTALL_DIR)/settings.ini
	cp wrapper/paris.sh $(INSTALL_DIR)/
	cd $(INSTALL_DIR) && bash paris.sh settings.ini person11.nt person12.nt $(OUTPUT_DIR)

clean:
	rm -rf $(INSTALL_DIR) $(OUTPUT_DIR)

docker_build:
	docker build -t kgt/paris .

docker_test: create_outputdir
	mkdir -p $(OUTPUT_DIR)/data
	cp $(PARIS_DIR)/person11.nt $(OUTPUT_DIR)/data; \
	cp $(PARIS_DIR)/person12.nt $(OUTPUT_DIR)/data; \
	cp $(SETTINGS) $(OUTPUT_DIR)/data/settings.ini; \
	docker run --rm -v $(OUTPUT_DIR):/output kgt/paris:latest \
		bash paris.sh /output/data/settings.ini /output/data/person11.nt /output/data/person12.nt /output

create_outputdir:
	mkdir -p $(OUTPUT_DIR)

docker_help:
	@echo "Example usage of Paris Docker"
	@echo "=== Usage 1 ==="
	@echo "docker run --rm kgt/paris bash paris_wrapper.sh settings.ini input_path1 input_path2 output_path"
	@echo "=== Usage 2 ==="
	@echo "docker run --rm kgt/paris java -jar paris.jar input_path1 input_path2 output_path"