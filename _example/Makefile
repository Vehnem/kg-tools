build:
	mkdir -p bin;
	cp tool.sh bin/;
	docker build -t local/kg-tool/example .;

run:
	docker run -d -p 5000 local/kg-tool/example;

all: build run
