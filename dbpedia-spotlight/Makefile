

.cloned:
	git clone https://github.com/dbpedia-spotlight/spotlight-docker.git bin
	touch $@

docker_build: .cloned
	cp spotlight.sh bin/
	cp dockerfile bin/
	@cd bin && docker build -t kgt/spotlight .
