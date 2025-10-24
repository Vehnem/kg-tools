INSTALL_DIR := $(CURDIR)/bin

.PHONY: download test clean

all: download test

download:
	@wget -P $(INSTALL_DIR) https://nlp.stanford.edu/software/stanford-corenlp-4.5.8.zip
	@unzip $(INSTALL_DIR)/stanford-corenlp-4.5.8.zip -d $(INSTALL_DIR)
	@rm $(INSTALL_DIR)/stanford-corenlp-4.5.8.zip

test:
	cd $(INSTALL_DIR)/stanford-corenlp-4.5.8 && \
	java -mx1g -cp "*" edu.stanford.nlp.naturalli.OpenIE

clean:
	rm -rf $(INSTALL_DIR)

docker_build:
	docker build -t kgt/corenlp .

docker_help:
	echo "Example usage of CoreNLP Docker"; \
	echo "=== Usage 1 ==="; \
	echo "docker run --rm kgt/corenlp bash corenlp.sh $$input_path $$output_file"; \
	echo "=== Usage 2 ==="; \
	echo "docker run --rm kgt/corenlp bash kbp.sh $$input_path $$output_file"; \
	echo "=== Usage 3 ==="; \
	echo "docker run --rm kgt/corenlp bash openie.sh $$input_path $$output_file";


docker_test:
	#docker run --rm
	#docker run --rm -v /data:/data kgt/corenlp java -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLP -annotators tokenize,pos,lemma,ner,parse,coref,kbp -file /data/results/foundation-eval/sources/text/Angela_Merkel.txt  -outputFormat json
	echo "Skip for now"
	#docker run --rm -v /data:/data kgt/corenlp java -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLP -annotators tokenize,ssplit,pos,lemma,depparse,natlog,openie -file /data/results/foundation-eval/sources/text/Angela_Merkel.txt  -outputFormat json
