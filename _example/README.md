# Example Tool Dummy

For other information see spreadsheet.
- Input Format Support
- Ouput...

### Install

Goal: is to build it with and without docker .

1. Download
2. Configure, or install requirements (pip install -r requirements.txt)
3. Maybe apt-get packages

### Run

1. if CLI post a CLI example param, with data from kg-testdata/_snippets/

```bash
./mytool.sh -i kg-testdata/_snippets/mytool/input -option1 optionValue1 > output.txt
```

2. if code / language package
make a small example script, e.g., for python create an tool.py

3. if webserver
make a script that sends example requests to web server (curl)

### Wrapper

TODO: requires good structured description of the tool

application.yaml
- entry point


---



```
.
├── app.py            // tool wrapper in python with http API
├── Dockerfile        // docker file, can be generalized
├── Makefile          // setup code and deploy
├── README.md         // this readme
├── requirements.txt  // wrapper python dependecies
└── tool.sh           // the tool to wrap
```

Run `make build` to build the Docker image
Run `make run` to run the Docker container

And Test
```
curl localhost:$PORT 
```
