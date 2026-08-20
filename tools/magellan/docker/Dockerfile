FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        python3-tk \
        wget \
        unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir "setuptools<69" \
    && pip install --no-cache-dir -r requirements.txt

COPY wrapper/run_magellan.py .
COPY wrapper/magellan.sh .
COPY config-example.yaml .
RUN chmod +x magellan.sh

ENTRYPOINT []
CMD ["python3", "run_magellan.py", "--help"]
