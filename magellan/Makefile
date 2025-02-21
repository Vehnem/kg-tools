INSTALL_DIR := $(CURDIR)/bin
VENV := .venv

.PHONY: all install download testDownsampling clean

all: install testDownsampling
install:
	mkdir -p $(INSTALL_DIR)
	python3 -m venv $(VENV_DIR)
	. $(VENV_DIR)/bin/activate && pip install -U numpy scipy py_entitymatching pyqt5 xgboost pandastable ydata-profiling
	wget -P $(INSTALL_DIR) https://github.com/OpenRefine/OpenRefine/releases/download/3.9.0/openrefine-linux-3.9.0.tar.gz
	tar xzf openrefine-linux-3.9.0.tar.gz
	rm openrefine-linux-3.9.0.tar.gz
	cd openrefine-3.9.0
	./refine

download:
	wget -P $(INSTALL_DIR) http://pages.cs.wisc.edu/~anhai/data/falcon_data/citations/citeseer.csv
	wget -P $(INSTALL_DIR) http://pages.cs.wisc.edu/~anhai/data/falcon_data/citations/dblp.csv

testDownsampling:
	$(VENV_DIR)/bin/python3 downsampling.py

clean:
	rm -rf $(INSTALL_DIR) $(OUTPUT_DIR)
