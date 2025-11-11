FROM adoptopenjdk/openjdk8:jre

RUN apt-get update &&  \
    apt-get install -y --no-install-recommends git zip && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN curl -L https://nlp.stanford.edu/software/stanford-corenlp-4.5.8.zip -o corenlp.zip
RUN unzip corenlp.zip && rm corenlp.zip

WORKDIR /opt/stanford-corenlp-4.5.8

COPY wrapper/ .

