INSTALL_DIR := $(CURDIR)/bin

.PHONY: download test clean

all: download test

TESTDATA_URL = https://github.com/Vehnem/kg-testdata.git

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
	@echo "▶ Running CoreNLP test (clone testdata inside container)..."
	@docker run --rm kgt/corenlp bash -c "\
		set -e; \
		git clone $(TESTDATA_URL) /data; \
		if [ ! -f /data/_snippets/corenlp/Angela_Merkel.txt ]; then \
			echo 'File not found: /data/_snippets/corenlp/Angela_Merkel.txt'; \
			exit 1; \
		fi; \
		bash openie.sh /data/_snippets/corenlp/Angela_Merkel.txt /data; \
		if [ ! -f /data/Angela_Merkel.txt.json ]; then \
			echo 'Error: No output file produced.'; \
			exit 1; \
		fi; \
		if [ ! -s /data/Angela_Merkel.txt.json ]; then \
			echo 'Error: Output file is empty.'; \
			exit 1; \
		fi;"