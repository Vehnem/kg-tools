INSTALL_DIR := $(CURDIR)/bin
OUTPUT_DIR := $(CURDIR)/target
KG_TESTDATA ?= $(HOME)/kg-testdata
AM_DIR := $(KG_TESTDATA)/_snippets/agreementmaker/

.PHONY: all download test clean

all: download test

download:
	mkdir -p $(INSTALL_DIR); \
	wget https://github.com/AgreementMakerLight/AML-Project/releases/download/v3.2/AML_v3.2.zip -P $(INSTALL_DIR); \
	cd $(INSTALL_DIR); \
	unzip AML_v3.2.zip; \
	rm AML_v3.2.zip

test:
	mkdir -p $(OUTPUT_DIR); \
	cp $(AM_DIR)/source.rdf $(INSTALL_DIR)/AML_v3.2/; \
	cp $(AM_DIR)/target.rdf $(INSTALL_DIR)/AML_v3.2/; \
	java -jar $(INSTALL_DIR)/AML_v3.2/*.jar -a -s $(INSTALL_DIR)/AML_v3.2/source.rdf -t $(INSTALL_DIR)/AML_v3.2/target.rdf -o $(OUTPUT_DIR)/output.rdf

clean:
	rm -rf $(INSTALL_DIR) $(OUTPUT_DIR)
