# Simplest Way to run py_entitymatching
### Requirements
- Python 3.10

### Installation Instruction

Install requirements
```
pip install -U numpy scipy py_entitymatching pyqt5 xgboost pandastable ydata-profiling
```

Install OpenRefine

```
wget -P $(INSTALL_DIR) https://github.com/OpenRefine/OpenRefine/releases/download/3.9.0/openrefine-linux-3.9.0.tar.gz
tar xzf openrefine-linux-3.9.0.tar.gz
rm openrefine-linux-3.9.0.tar.gz
```

Start OpenRefine
```
cd openrefine-3.9.0
./refine
```

Download Test Data
```
wget -P $(INSTALL_DIR) http://pages.cs.wisc.edu/~anhai/data/falcon_data/citations/citeseer.csv
wget -P $(INSTALL_DIR) http://pages.cs.wisc.edu/~anhai/data/falcon_data/citations/dblp.csv
```
Run Tests
```
python dataprofiling.py
```
