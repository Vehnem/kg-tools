.PHONY: all download test clean docker_build docker_test docker_help

INSTALL_DIR  := $(CURDIR)/bin
OUTPUT_DIR   := $(CURDIR)/target
KG_TESTDATA  ?= $(HOME)/papers/kg-testdata
PARIS_DIR    := $(KG_TESTDATA)/_snippets/paris
SETTINGS     ?= settings.ini.example
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
	cp paris_wrapper.sh $(INSTALL_DIR)/
	cd $(INSTALL_DIR) && bash paris_wrapper.sh settings.ini person11.nt person12.nt $(OUTPUT_DIR)

clean:
	rm -rf $(INSTALL_DIR) $(OUTPUT_DIR)

docker_build:
	docker build -t kgt/paris .

docker_test:
	docker run --rm kgt/paris bash -c 'java -jar *.jar; status=$$?; if [ "$$status" -eq 63 ]; then echo "Smoke test OK: jar runs, exit code 63 as expected for no-args invocation."; else echo "Smoke test FAILED: unexpected exit code $$status" >&2; exit 1; fi'

docker_help:
	@echo "Example usage of Paris Docker"
	@echo "=== Usage 1 ==="
	@echo "docker run --rm kgt/paris bash paris_wrapper.sh settings.ini input_path1 input_path2 output_path"
	@echo "=== Usage 2 ==="
	@echo "docker run --rm kgt/paris java -jar paris.jar input_path1 input_path2 output_path"