INSTALL_DIR := $(CURDIR)/bin
OUTPUT_DIR := $(CURDIR)/target
KG_TESTDATA ?= $(HOME)/papers/kg-testdata
PARIS_DIR := $(KG_TESTDATA)/_snippets/paris/

.PHONY: all download test clean

all: download test

download:
	mkdir -p $(INSTALL_DIR); \
	wget https://github.com/dig-team/PARIS/releases/download/v0.3/paris_0_3.jar -P $(INSTALL_DIR); \

test:
	mkdir -p $(OUTPUT_DIR); \
	cd $(INSTALL_DIR); \
	mkdir -p output; \
	cp $(PARIS_DIR)/person11.nt .; \
	cp $(PARIS_DIR)/person12.nt .; \
	java -jar *.jar person11.nt person12.nt output; \
	mv run*.txt $(OUTPUT_DIR); \
	mv output $(OUTPUT_DIR)

clean:
	rm -rf $(INSTALL_DIR) $(OUTPUT_DIR)

docker_build:
	docker build -t kgt/paris .

docker_help:
	docker run --rm kgt/paris java -jar paris.jar
