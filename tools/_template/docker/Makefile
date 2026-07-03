.PHONY: docker_build docker_test docker_help

docker_build:
	mkdir -p bin
	cp tool.sh bin/
	docker build -t kgt/example .

docker_test:
	echo "Add a docker_test target for your tool"

docker_help:
	@echo "docker run --rm kgt/example bash tool.sh <args>"
