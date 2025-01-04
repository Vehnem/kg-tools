FROM eclipse-temurin

RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN wget https://nlp.stanford.edu/software/stanford-corenlp-4.5.8.zip

RUN unzip stanford-corenlp-4.5.8.zip && rm stanford-corenlp-4.5.8.zip

WORKDIR /opt/stanford-corenlp-4.5.8

ENTRYPOINT ["java", "-mx1g", "-cp", "*", "edu.stanford.nlp.naturalli.OpenIE"]

CMD []

