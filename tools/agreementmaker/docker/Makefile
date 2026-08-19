INSTALL_DIR := $(CURDIR)/bin
OUTPUT_DIR := $(CURDIR)/target
KG_TESTDATA ?= $(HOME)/kg-testdata
AM_DIR := $(KG_TESTDATA)/_snippets/agreementmaker
AML_JAR_NAME := AgreementMakerLight.jar

.PHONY: all download test clean docker_build docker_test docker_help

all: download test

download:
	mkdir -p $(INSTALL_DIR); \
	wget https://github.com/AgreementMakerLight/AML-Project/releases/download/v3.2/AML_v3.2.zip -P $(INSTALL_DIR); \
	cd $(INSTALL_DIR); \
	unzip AML_v3.2.zip; \
	rm AML_v3.2.zip; \
	cp $(CURDIR)/wrapper/agreementmaker.sh $(INSTALL_DIR)/AML_v3.2/

test:
	mkdir -p $(OUTPUT_DIR); \
	cp $(AM_DIR)/source.rdf $(INSTALL_DIR)/AML_v3.2/; \
	cp $(AM_DIR)/target.rdf $(INSTALL_DIR)/AML_v3.2/; \
	cp $(CURDIR)/example-settings.ini $(INSTALL_DIR)/AML_v3.2/settings.ini; \
	AML_JAR=$(INSTALL_DIR)/AML_v3.2/$(AML_JAR_NAME) \
	bash $(INSTALL_DIR)/AML_v3.2/agreementmaker.sh \
		$(INSTALL_DIR)/AML_v3.2/settings.ini \
		$(INSTALL_DIR)/AML_v3.2/source.rdf \
		$(INSTALL_DIR)/AML_v3.2/target.rdf \
		$(OUTPUT_DIR)/output.rdf

clean:
	rm -rf $(INSTALL_DIR) $(OUTPUT_DIR)

docker_build:
	docker build -t kgt/agreementmaker .

docker_test:
	mkdir -p $(OUTPUT_DIR); \
	cp $(AM_DIR)/source.rdf $(OUTPUT_DIR)/; \
	cp $(AM_DIR)/target.rdf $(OUTPUT_DIR)/; \
	cp $(CURDIR)/example-settings.ini $(OUTPUT_DIR)/settings.ini; \
	docker run --rm -v $(OUTPUT_DIR):/data kgt/agreementmaker:latest \
		bash agreementmaker.sh /data/settings.ini /data/source.rdf /data/target.rdf /data/output2.rdf

docker_help:
	echo "Example usage of AgreementMaker Docker"; \
	echo "=== Usage 1: auto mode ==="; \
	echo "docker run --rm -v \$$(pwd):/data kgt/agreementmaker bash agreementmaker.sh /data/settings.ini /data/source.owl /data/target.owl /data/output.rdf"; \
	echo "=== Usage 2: repair mode (mit Referenz-Alignment) ==="; \
	echo "docker run --rm -v \$$(pwd):/data kgt/agreementmaker bash agreementmaker.sh /data/settings.ini /data/source.owl /data/target.owl /data/output.rdf /data/input.rdf"