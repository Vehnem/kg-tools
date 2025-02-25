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
