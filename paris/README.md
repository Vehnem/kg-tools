Example Request:

```bash
curl -X POST \
  -F "flag=shared" \
  -F "file=@restaurant1.nt" -F "file_flag=" \
  -F "file=@restaurant2.nt" -F "file_flag=" \
  http://localhost:port/run
```
