Example Request:

```bash
curl -X POST \
  -F "file=@authors1.csv" -F "file_flag=" \
  -F "file=@authors2.csv" -F "file_flag=" \
  http://localhost:port/run
```
