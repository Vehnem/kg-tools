INSTALL_DIR := $(CURDIR)/bin
OUTPUT_DIR := $(CURDIR)/target
KG_TESTDATA ?= $(HOME)/kg-testdata
FALCON_DIR := $(KG_TESTDATA)/_snippets/falcon
ES_HOST := http://localhost:9200
VENV_DIR := $(INSTALL_DIR)/.venv

.PHONY: all install update elasticsearch test clean

all: install update elasticsearch test
install:
	mkdir -p $(INSTALL_DIR)
	python3 -m venv $(VENV_DIR)
	. $(VENV_DIR)/bin/activate && git clone https://github.com/SDM-TIB/falcon2.0.git $(INSTALL_DIR)/falcon2.0
	. $(VENV_DIR)/bin/activate && pip install -r requirements.txt && python3 -m spacy download en_core_web_sm

update:
	# Replace ElasticSearch-Endpoint
	find $(INSTALL_DIR) -type f -name "*.py" -exec sed -i "s|Elasticsearch(\['http://node1.research.tib.eu:9200/'\])|Elasticsearch(['http://localhost:9200/'])|g" {} +

	# Remove doc_type Parameter from es.search and es.index
	find $(INSTALL_DIR) -type f -name "*.py" -exec sed -i -E \
	    "s/(es\.search\(.*)doc_type=[^,)]*,?\s*(.*\))/\1\2/g" {} +
	find $(INSTALL_DIR) -type f -name "*.py" -exec sed -i -E \
	    "s/(es\.index\(.*)doc_type=[^,)]*,?\s*(.*\))/\1\2/g" {} +

elasticsearch:
	wget -P $(INSTALL_DIR) https://figshare.com/ndownloader/files/20168714 -O $(INSTALL_DIR)/wikidata_dump.zip && \
	unzip -o $(INSTALL_DIR)/wikidata_dump.zip -d $(INSTALL_DIR) && \
	rm $(INSTALL_DIR)/wikidata_dump.zip
	. $(VENV_DIR)/bin/activate && elasticdump --output=$(ES_HOST)/wikidataentityindex/ --input=$(INSTALL_DIR)/wikidataentity.json --type=data --limit=5000
	. $(VENV_DIR)/bin/activate && elasticdump --output=$(ES_HOST)/wikidatapropertyindex/ --input=$(INSTALL_DIR)/wikidataproperty.json --type=data --limit=5000

test:
	mkdir -p $(OUTPUT_DIR)
	. $(VENV_DIR)/bin/activate && cd $(INSTALL_DIR)/falcon2.0/ && python3 main.py
clean:
	rm -rf $(INSTALL_DIR) $(OUTPUT_DIR)
