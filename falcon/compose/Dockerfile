# Basis-Image
FROM python:3.8

# Arbeitsverzeichnis setzen
WORKDIR /app

# Notwendige Pakete installieren
RUN apt-get update && apt-get install -y \
    pkg-config \
    python3-openssl \
    wget unzip && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g elasticdump

RUN git clone https://github.com/SDM-TIB/falcon2.0.git /app/falcon2.0
WORKDIR /app/falcon2.0
RUN pip install -r requirements.txt && python3 -m spacy download en_core_web_sm

# Elasticsearch Host setzen
ENV ES_HOST=http://localhost:9200

# Elasticsearch-Endpunkte anpassen
RUN find /app/falcon2.0 -type f -name "*.py" -exec sed -i \
    -e "s|Elasticsearch(\['http://node1.research.tib.eu:9200/'\])|Elasticsearch(['http://elasticsearch:9200/'])|g" \
    -e 's|http://node1.research.tib.eu:4001/sparql|https://dbpedia.org/sparql/|g' \
    -e 's|http://node3.research.tib.eu:4010/sparql|https://query.wikidata.org/|g' \
    {} +

# Elasticsearch-Änderungen für doc_type (Kompatibilität)
RUN find /app/falcon2.0 -type f -name "*.py" -exec sed -i -E \
    "s/(es\.search\(.*)doc_type=[^,)]*,?\s*(.*\))/\1\2/g" {} +
RUN find /app/falcon2.0 -type f -name "*.py" -exec sed -i -E \
    "s/(es\.index\(.*)doc_type=[^,)]*,?\s*(.*\))/\1\2/g" {} +
RUN sed -i -e 's/doc_type=docType, //g' /app/falcon2.0/Elastic/searchIndex.py

# Fehlerhafte Exception-Handling-Zeilen entfernen
RUN sed -i \
    -e '/^    except:/d' \
    -e '/^    #raise/d' \
    -e '/^    print("error")/d' \
    -e '/^    try:$/d' /app/falcon2.0/main.py

WORKDIR /app
