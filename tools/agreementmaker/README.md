Example Request:

```bash
curl -X POST \
  -F "flag=-a" \
  -F "file=@source.rdf" -F "file_flag=-s" \
  -F "file=@target.rdf" -F "file_flag=-t" \
  http://localhost:port/run
```

