FROM adoptopenjdk/openjdk8:jre

RUN apt update
RUN apt install -y zip

WORKDIR /opt

RUN curl -L https://nlp.stanford.edu/software/stanford-corenlp-4.5.8.zip -o corenlp.zip
RUN unzip corenlp.zip && rm corenlp.zip

WORKDIR /opt/stanford-corenlp-4.5.8

COPY wrapper/ .

