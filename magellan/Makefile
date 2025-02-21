INSTALL_DIR := $(CURDIR)/bin
VENV := $(INSTALL_DIR)/.venv

.PHONY: all install start_openrefine fix-pd-np download testDownsampling test_data_profiling test_data_exploration test_overlap_blocking clean

all: install start_openrefine fix-pd-np download test_downsampling test_data_profiling test_data_exploration test_overlap_blocking
install:
	mkdir -p $(INSTALL_DIR)
	python3 -m venv $(VENV_DIR)
	. $(VENV_DIR)/bin/activate && pip install -U numpy scipy py_entitymatching pyqt5 xgboost pandastable ydata-profiling
	wget -P $(INSTALL_DIR) https://github.com/OpenRefine/OpenRefine/releases/download/3.9.0/openrefine-linux-3.9.0.tar.gz
	tar xzf openrefine-linux-3.9.0.tar.gz
	rm openrefine-linux-3.9.0.tar.gz

start_openrefine:
	cd openrefine-3.9.0
	./refine

fix-pd-np:
	sed -i 's/pd.np/np/g' $(VENV)/lib/python3.11/site-packages/py_entitymatching/matcher/matcherutils.py

download:
	wget -P $(INSTALL_DIR) http://pages.cs.wisc.edu/~anhai/data/falcon_data/citations/citeseer.csv
	wget -P $(INSTALL_DIR) http://pages.cs.wisc.edu/~anhai/data/falcon_data/citations/dblp.csv
	wget -P $(INSTALL_DIR) https://raw.githubusercontent.com/anhaidgroup/py_entitymatching/refs/heads/master/notebooks/vldb_demo/acm_demo.csv
	wget -P $(INSTALL_DIR) https://raw.githubusercontent.com/anhaidgroup/py_entitymatching/refs/heads/master/notebooks/vldb_demo/dblp_demo.csv
	wget -P $(INSTALL_DIR) https://raw.githubusercontent.com/anhaidgroup/py_entitymatching/refs/heads/master/notebooks/vldb_demo/labeled_data_demo.csv

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
