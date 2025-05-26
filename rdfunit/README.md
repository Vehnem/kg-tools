Build Dockerfile:
```
docker build -t kgt/rdfunit .
```

Run Image:
```
docker run --rm \
  -v $(pwd)/data:/data \
  -v $(pwd)/output:/output \
  kgt/rdfunit \
  /data/kg.ttl \
  /data/ontology.ttl \
  /output
```