If you want to run PyJedAI with VectorBasedMatching locally 
please replace the matching.py from your PyJedAI pip installation (.venv/lib/python3.14/site-packages/pyjedai/matching.py)
with the matching.py in [./fixes/matching.py](./fixes/matching.py)
Build Dockerfile

```
docker build -f pyjedai/Dockerfile -t kgtool/pyjedai .
```