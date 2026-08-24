If you want to run PyJedAI with VectorBasedMatching locally 
please replace the matching.py and utils.py from your PyJedAI pip installation (.venv/lib/python3.14/site-packages/pyjedai/matching.py)-(.venv/lib/python3.14/site-packages/pyjedai/utils.py)
with the matching.py and utils.py in [./docker/fixes/](docker/fixes)
Build Dockerfile

```
docker build -f pyjedai/Dockerfile -t kgtool/pyjedai .
```