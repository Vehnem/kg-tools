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

docker_build:
	docker build -t kgt/agreementmaker:latest .

docker_help:
	echo "Example usage of AgreementMaker Docker"
	echo "=== Usage 1 ==="
	echo "docker run --rm kgt/agreementmaker bash agreementmaker.sh $input_path1 $input_path2 $output_file"
	echo "=== Usage 2 ==="
	echo "docker run --rm kgt/agreementmaker java -jar AgreementMakerLight.jar -a -s $input_path1 -t $input_path2 -o $output_file"

docker_test:
	docker run --rm -v $(OUTPUT_DIR):/data kgt/agreementmaker:latest java -jar AgreementMakerLight.jar -a -s /data/source.rdf -t /data/target.rdf -o /data/output2.rdf # java -jar *.jar -h
