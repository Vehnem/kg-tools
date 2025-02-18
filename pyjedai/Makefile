INSTALL_DIR := $(CURDIR)/bin
VENV_DIR := $(INSTALL_DIR)/.venv

.PHONY: install download test_cleanclean clean

all: install download test_cleanclean
install:
	mkdir -p $(INSTALL_DIR)
	python3 -m venv $(VENV_DIR)
	. $(VENV_DIR)/bin/activate && pip install pyjedai

download:
	wget -P $(INSTALL_DIR) https://dbs.uni-leipzig.de/files/datasets/Abt-Buy.zip
	unzip $(INSTALL_DIR)/Abt-Buy.zip -d $(INSTALL_DIR)
	rm $(INSTALL_DIR)/Abt-Buy.zip

test_cleanclean:
	$(VENV_DIR)/bin/python3 cleanclean.py

clean:
	rm -rf $(INSTALL_DIR) $(OUTPUT_DIR)
