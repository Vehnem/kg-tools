Example Get Request:

docker build -f DockerfileAirflow -t kgt:corenlp .

```bash
curl "http://localhost:port/run?input=Paula%20is%20a%20girl%20&flags=-format%20ollie'
```

Example Post Request:
```bash
curl -X POST \
  -F "input=Paula%20is%20a%20girl" \
  -F "flag=-format ollie" \
  http://localhost:port/run
```