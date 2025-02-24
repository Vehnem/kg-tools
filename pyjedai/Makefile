INSTALL_DIR := $(CURDIR)/bin
VENV_DIR := $(INSTALL_DIR)/.venv

.PHONY: all install start_openrefine fix-pd-np download testDownsampling test_data_profiling test_data_exploration test_overlap_blocking clean

all: install start_openrefine fix-pd-np download test_downsampling test_data_profiling test_data_exploration test_overlap_blocking
install:
	mkdir -p $(INSTALL_DIR)
	python3 -m venv $(VENV_DIR)
	. $(VENV_DIR)/bin/activate && pip install pyjedai

download:
	wget -P $(INSTALL_DIR) https://dbs.uni-leipzig.de/files/datasets/Abt-Buy.zip
	unzip $(INSTALL_DIR)/Abt-Buy.zip -d $(INSTALL_DIR)
	rm $(INSTALL_DIR)/Abt-Buy.zip

test_downsampling:
	$(VENV_DIR)/bin/python3 downsampling.py

test_data_profiling:
	$(VENV_DIR)/bin/python3 data_profiling.py

test_data_exploration:
	$(VENV_DIR)/bin/python3 data_exploration.py

test_overlap_blocking:
	$(VENV_DIR)/bin/python3 blocking/overlap_blocking.py

test_bestlearning_matcher:
	$(VENV_DIR)/bin/python3 matching/bestlearning_matcher.py


clean:
	rm -rf $(INSTALL_DIR) $(OUTPUT_DIR)
