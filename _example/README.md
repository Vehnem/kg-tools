# Example Tool Dummy

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
