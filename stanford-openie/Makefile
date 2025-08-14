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

docker_test:
	#docker run --rm
	#docker run --rm -v /data:/data kgtool/corenlp java -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLP -annotators tokenize,pos,lemma,ner,parse,coref,kbp -file /data/results/foundation-eval/sources/text/Angela_Merkel.txt  -outputFormat json
	docker run --rm -v /data:/data kgtool/corenlp java -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLP -annotators tokenize,ssplit,pos,lemma,depparse,natlog,openie -file /data/results/foundation-eval/sources/text/Angela_Merkel.txt  -outputFormat json
