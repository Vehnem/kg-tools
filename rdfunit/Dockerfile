FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y git maven openjdk-8-jdk wget unzip && \
    rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/AKSW/RDFUnit.git /RDFUnit && \
    cd /RDFUnit && \
    mvn -pl rdfunit-validate -am clean install -DskipTests

WORKDIR /RDFUnit

COPY wrapper/rdfunit.sh /RDFUnit/run-rdfunit.sh
RUN chmod +x /RDFUnit/run-rdfunit.sh

ENTRYPOINT ["/RDFUnit/run-rdfunit.sh"]
