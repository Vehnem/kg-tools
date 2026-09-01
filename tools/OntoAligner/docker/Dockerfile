FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY wrapper/run_ontoaligner.py .
COPY wrapper/ontoaligner.sh .
COPY example-config.yaml .

RUN mkdir -p /results
ENV OUTPUT_DIR=/results
