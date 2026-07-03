.PHONY: all download test clean

all: download test

download:
	git clone https://github.com/dig-team/FLORA.git; \
	cp main.py FLORA/src/; \
	cd FLORA; \
	pip install -r requirements.txt

test:
	cd FLORA/src; \
	bash run.sh

clean:
	rm -rf FLORA

docker_build:
	docker build -t kgt/flora .

docker_help:
	docker run --rm kgt/flora bash -c "cd FLORA/src && bash run.sh"

