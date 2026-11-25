.PHONY: all build test clean docker_build docker_test docker_help create_outputdir


KG_TESTDATA   ?= $(HOME)/kg-testdata
OUTPUT_DIR    ?= $(CURDIR)/target
BUILD_DIR     ?= $(CURDIR)/.build
LOGMAP_HOME   ?= $(BUILD_DIR)/logmap
LOGMAP_COMMIT ?= a031fa9889e139fd5ab9e8c7415c8113f9c285ee

CONFIG        ?= $(CURDIR)/config-example.conf

LOGMAP_DIR    ?= $(KG_TESTDATA)/_snippets/logmap
ONTO1         ?= $(LOGMAP_DIR)/cmt.owl
ONTO2         ?= $(LOGMAP_DIR)/ekaw.owl
REFERENCE     ?= $(LOGMAP_DIR)/cmt-ekaw.rdf

all: test

build:
	mkdir -p $(BUILD_DIR)/src $(LOGMAP_HOME)
	curl -fsSL https://github.com/ernestojimenezruiz/logmap-matcher/archive/$(LOGMAP_COMMIT).tar.gz \
	  | tar -xz --strip-components=1 -C $(BUILD_DIR)/src
	cd $(BUILD_DIR)/src && mvn -B -DskipTests package
	cp $(BUILD_DIR)/src/target/logmap-matcher-4.0.jar $(LOGMAP_HOME)/logmap-matcher.jar
	rm -rf $(LOGMAP_HOME)/java-dependencies
	cp -r $(BUILD_DIR)/src/target/java-dependencies $(LOGMAP_HOME)/java-dependencies
	cp $(BUILD_DIR)/src/parameters.txt $(LOGMAP_HOME)/parameters.txt

test: create_outputdir
	cd wrapper && LOGMAP_HOME=$(LOGMAP_HOME) \
	bash run_logmap.sh $(ONTO1) $(ONTO2) $(OUTPUT_DIR) $(CONFIG) $(REFERENCE)

create_outputdir:
	mkdir -p $(OUTPUT_DIR)

clean:
	rm -rf $(OUTPUT_DIR) $(BUILD_DIR)

docker_build:
	docker build -t kgt/logmap .

docker_test: create_outputdir
	cp -r $(LOGMAP_DIR) $(OUTPUT_DIR)/data
	docker run --rm -v $(OUTPUT_DIR):/logmap-data kgt/logmap \
	   bash run_logmap.sh /logmap-data/data/cmt.owl /logmap-data/data/ekaw.owl /logmap-data config-example.conf /logmap-data/data/cmt-ekaw.rdf

docker_help:
	@echo "Example usage of LogMap Docker"
	@echo "=== Usage 1: matching only ==="
	@echo "docker run --rm -v <host_dir>:/data kgt/logmap bash run_logmap.sh /data/<onto1.owl> /data/<onto2.owl> /data/out config-example.conf"
	@echo "=== Usage 2: matching + evaluation against an OAEI RDF reference alignment ==="
	@echo "docker run --rm -v <host_dir>:/data kgt/logmap bash run_logmap.sh /data/<onto1.owl> /data/<onto2.owl> /data/out config-example.conf /data/<reference.rdf>"
