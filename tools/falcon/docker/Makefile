INSTALL_DIR := $(CURDIR)/bin
ES_HOST := http://localhost:9200
VENV_DIR := .venv

.PHONY: all install update elasticsearch test clean docker_build docker_falconinit docker_falconrun

all: install update elasticsearch test
install:
	mkdir -p $(INSTALL_DIR)
	git clone https://github.com/SDM-TIB/falcon2.0.git $(INSTALL_DIR)/falcon2.0
	pip install -r requirements.txt && python3 -m spacy download en_core_web_sm

update:
	# Replace ElasticSearch-Endpoint
	find $(INSTALL_DIR)/falcon2.0 -type f -name "*.py" -exec sed -i "s|Elasticsearch(\['http://node1.research.tib.eu:9200/'\])|Elasticsearch(['http://localhost:9200/'])|g" {} +
	# Replace SPARQL Endpoints
	find $(INSTALL_DIR)/falcon2.0 -type f -exec sed -i \
		-e 's|http://node1.research.tib.eu:4001/sparql|https://dbpedia.org/sparql/|g' \
		-e 's|http://node3.research.tib.eu:4010/sparql|https://query.wikidata.org/|g' {} +
	# Remove doc_type Parameter from es.search and es.index
	find $(INSTALL_DIR)/falcon2.0 -type f -name "*.py" -exec sed -i -E \
	    "s/(es\.search\(.*)doc_type=[^,)]*,?\s*(.*\))/\1\2/g" {} +
	find $(INSTALL_DIR)/falcon2.0 -type f -name "*.py" -exec sed -i -E \
	    "s/(es\.index\(.*)doc_type=[^,)]*,?\s*(.*\))/\1\2/g" {} +
	sed -i \
		-e 's/doc_type=docType, //g' $(INSTALL_DIR)/falcon2.0/Elastic/searchIndex.py
	# Remove try catch block
	sed -i \
		-e '/^    except:/d' \
		-e '/^    #raise/d' \
		-e '/^    print("error")/d' \
		-e '/^    try:$$/d' $(INSTALL_DIR)/falcon2.0/main.py

elasticsearch:
#	wget -P $(INSTALL_DIR) https://figshare.com/ndownloader/files/20168714 -O $(INSTALL_DIR)/wikidata_dump.zip && \
#	unzip -o $(INSTALL_DIR)/wikidata_dump.zip -d $(INSTALL_DIR) && \
#	rm $(INSTALL_DIR)/wikidata_dump.zip
	elasticdump --output=$(ES_HOST)/wikidataentityindex/ --input=$(INSTALL_DIR)/wikidataentity.json --type=data --limit=5000
	elasticdump --output=$(ES_HOST)/wikidatapropertyindex/ --input=$(INSTALL_DIR)/wikidatapropertyindex.json --type=data --limit=5000

test:
	cd $(INSTALL_DIR)/falcon2.0/ && python3 main.py

clean:
	rm -rf $(INSTALL_DIR) $(VENV_DIR)

docker_build:
	cd compose && \
	docker compose build

docker_falconinit:
	cd compose && \
	docker compose run falconinit

docker_falconrun:
	cd compose && \
	docker compose run falconcli

docker_all: docker_build docker_falconinit docker_falconrun

